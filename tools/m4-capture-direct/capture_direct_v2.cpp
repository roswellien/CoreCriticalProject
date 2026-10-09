#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include "capture_direct.hpp"
#include <algorithm>
#include <array>
#include <chrono>
#include <charconv>
#include <exception>
#include <functional>
#include <limits>
#include <set>
#include <stdexcept>
#include <utility>
#include <type_traits>

extern "C" void mw34_capture_preserved_call(void(*)(void*) noexcept,void*) noexcept;
extern "C" void mw34_capture_save(void*) noexcept;
extern "C" void mw34_capture_restore(const void*) noexcept;
namespace mw34::capture_direct {
namespace {
namespace fs=std::filesystem;
using Digest=std::array<unsigned char,32>;
using Clock=std::chrono::steady_clock;
void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
void win(bool ok,const char* why){if(!ok)throw std::runtime_error(std::string(why)+" Windows error "+std::to_string(GetLastError()));}
struct ErrorScope {DWORD saved=GetLastError();~ErrorScope() noexcept{SetLastError(saved);}};
struct HardwareScope {alignas(16) std::array<unsigned char,544> saved{};HardwareScope() noexcept{mw34_capture_save(saved.data());}~HardwareScope() noexcept{mw34_capture_restore(saved.data());}};
template<class F> void preserved(F&& work){
    ErrorScope error;
    // Exception propagation/destruction occurs after the body callback. Restore
    // again during normal return/unwind after the exception_ptr is destroyed.
    HardwareScope hardware;
    struct Call {std::remove_reference_t<F>* body;std::exception_ptr failure;};
    Call call{&work,{}};
    mw34_capture_preserved_call([](void* raw) noexcept{auto& call=*static_cast<Call*>(raw);try{(*call.body)();}catch(...){call.failure=std::current_exception();}},&call);
    if(call.failure)std::rethrow_exception(call.failure);
}
struct File {
    HANDLE value=INVALID_HANDLE_VALUE;
    File()=default;File(const File&)=delete;File& operator=(const File&)=delete;
    File(File&& other) noexcept:value(std::exchange(other.value,INVALID_HANDLE_VALUE)){}
    File& operator=(File&& other) noexcept{close();value=std::exchange(other.value,INVALID_HANDLE_VALUE);return *this;}
    ~File() noexcept{close();}
    void close() noexcept{if(value!=INVALID_HANDLE_VALUE){CloseHandle(value);value=INVALID_HANDLE_VALUE;}}
};
struct Hash {
    BCRYPT_HASH_HANDLE handle=nullptr;
    std::vector<unsigned char> object;
    explicit Hash(BCRYPT_ALG_HANDLE algorithm){DWORD bytes=0,count=0;need(BCryptGetProperty(algorithm,BCRYPT_OBJECT_LENGTH,reinterpret_cast<PUCHAR>(&bytes),sizeof(bytes),&count,0)>=0&&count==sizeof(bytes),"BCrypt SHA object extent");object.resize(bytes);need(BCryptCreateHash(algorithm,&handle,object.data(),bytes,nullptr,0,0)>=0,"BCrypt SHA create");}
    ~Hash() noexcept{if(handle)BCryptDestroyHash(handle);}
    void add(const void* data,std::size_t bytes){auto p=static_cast<const unsigned char*>(data);while(bytes){auto step=static_cast<ULONG>(std::min<std::size_t>(bytes,1u<<20));need(BCryptHashData(handle,const_cast<PUCHAR>(p),step,0)>=0,"BCrypt SHA update");p+=step;bytes-=step;}}
    Digest finish(){Digest digest{};need(BCryptFinishHash(handle,digest.data(),static_cast<ULONG>(digest.size()),0)>=0,"BCrypt SHA finish");return digest;}
};
std::string hex(const Digest& value){static constexpr char digits[]="0123456789abcdef";std::string result(64,'0');for(std::size_t i=0;i<value.size();++i){result[2*i]=digits[value[i]>>4];result[2*i+1]=digits[value[i]&15];}return result;}
std::string name_key(std::string_view name){
    need(!name.empty()&&name.size()<=1024,"Logical name extent");
    std::string key(name);
    for(auto& c:key){unsigned char x=static_cast<unsigned char>(c);need(x>=32&&x<127&&c!='\\'&&std::string_view(":<>\"|?*").find(c)==std::string_view::npos,"Unsupported ASCII logical name");if(c>='A'&&c<='Z')c+=32;}
    for(std::size_t at=0;at<=name.size();){auto end=name.find('/',at);if(end==std::string_view::npos)end=name.size();auto part=name.substr(at,end-at);need(!part.empty()&&part!="."&&part!=".."&&part.back()!='.'&&part.back()!=' ',"Unsupported logical component");std::string stem(part.substr(0,part.find('.')));for(auto& c:stem)if(c>='a'&&c<='z')c-=32;need(stem!="CON"&&stem!="PRN"&&stem!="AUX"&&stem!="NUL"&&stem!="CLOCK$"&&!(stem.size()==4&&(stem.substr(0,3)=="COM"||stem.substr(0,3)=="LPT")&&stem[3]>='1'&&stem[3]<='9'),"Reserved logical component");if(end==name.size())break;at=end+1;}
    return key;
}
void check_ancestors(const fs::path& path){
    fs::path current;
    for(const auto& component:path){current/=component;DWORD attributes=GetFileAttributesW(current.c_str());if(attributes!=INVALID_FILE_ATTRIBUTES)need(!(attributes&FILE_ATTRIBUTE_REPARSE_POINT),"Reparse capture path unsupported");else need(GetLastError()==ERROR_FILE_NOT_FOUND||GetLastError()==ERROR_PATH_NOT_FOUND,"Capture ancestor query failed");}
}
fs::path clean(const fs::path& path){return fs::absolute(path).lexically_normal().make_preferred();}
bool beneath(const fs::path& child,const fs::path& root){auto a=child.wstring(),b=root.wstring();while(!b.empty()&&(b.back()==L'\\'||b.back()==L'/'))b.pop_back();return a.size()>b.size()&&a[b.size()]==L'\\'&&CompareStringOrdinal(a.data(),static_cast<int>(b.size()),b.data(),static_cast<int>(b.size()),TRUE)==CSTR_EQUAL;}
std::string number(std::uint64_t value){return std::to_string(value);}
std::string seconds(double value){char text[64];auto result=std::to_chars(text,text+sizeof(text),value,std::chars_format::general,17);need(result.ec==std::errc{},"Finite timing encoding");return {text,result.ptr};}
void little(std::vector<unsigned char>& out,std::uint64_t value,unsigned bytes){for(unsigned i=0;i<bytes;++i)out.push_back(static_cast<unsigned char>(value>>(8*i)));}
}

struct Writer::Impl {
    struct Entry {std::string name,digest;std::uint64_t spool_offset=0,size=0;};
    Options options;
    fs::path root,target,temporary;
    std::vector<fs::path> owned;
    File spool;
    fs::path spool_path;
    BCRYPT_ALG_HANDLE algorithm=nullptr;
    std::vector<Entry> entries;
    std::set<std::string> names;
    std::uint64_t spool_bytes=0,index_estimate=70,written=0;
    bool failed=false,finished=false,owns_temporary=false;
    Receipt receipt;
    explicit Impl(const fs::path& output,Options choice):options(std::move(choice)){
        try{
            need(options.files_per_part>0&&options.files_per_part<=max_files&&options.bytes_per_part>0&&options.bytes_per_part<=max_total&&options.index_bytes_per_part>=70&&options.index_bytes_per_part<=max_index,"Unchanged bounded capture limits");
            root=clean(options.reports_root.empty()?fs::current_path()/"reports":options.reports_root);target=clean(output);need(beneath(target,root),"Capture output must be a reports child");check_ancestors(root);check_ancestors(target);need(!fs::exists(target),"Fresh complete capture directory required");fs::create_directories(target.parent_path());check_ancestors(target.parent_path());
            need(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0,"System BCrypt SHA provider");
            bool created=false;
            for(unsigned attempt=0;attempt<8&&!created;++attempt){Digest token{};need(BCryptGenRandom(nullptr,token.data(),static_cast<ULONG>(token.size()),BCRYPT_USE_SYSTEM_PREFERRED_RNG)>=0,"Private capture name entropy");temporary=target.parent_path()/(L"."+target.filename().wstring()+L"."+fs::path(hex(token)).wstring()+L".partial");created=CreateDirectoryW(temporary.c_str(),nullptr)!=0;if(!created)need(GetLastError()==ERROR_ALREADY_EXISTS,"Private directory creation failed");}
            owns_temporary=created;need(created,"Private capture directory unavailable");receipt.directory=target;receipt.manifest=target/"transport.json";
        }catch(...){cleanup();throw;}
    }
    ~Impl() noexcept{cleanup();}
    void cleanup() noexcept{
        spool.close();
        if(!finished&&owns_temporary){
            // Only paths created by this instance; never recursively enumerate/delete.
            // If an ancestor was replaced/reparsed, abandon the private debris.
            try{need(clean(temporary)==temporary&&beneath(temporary,root)&&temporary.parent_path()==target.parent_path(),"Owned private cleanup target");check_ancestors(temporary);for(const auto& path:owned){need(path.parent_path()==temporary,"Owned private cleanup file");check_ancestors(path);DeleteFileW(path.c_str());}RemoveDirectoryW(temporary.c_str());}catch(...){}
        }
        if(algorithm){BCryptCloseAlgorithmProvider(algorithm,0);algorithm=nullptr;}
    }
    void alive(){need(!failed&&!finished,"Capture writer is poisoned or closed");}
    Digest digest(const void* p,std::size_t n){Hash hash(algorithm);hash.add(p,n);return hash.finish();}
    File create(const fs::path& path){File file;file.value=CreateFileW(path.c_str(),GENERIC_READ|GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);win(file.value!=INVALID_HANDLE_VALUE,"Fresh capture file creation");owned.push_back(path);return file;}
    void seek(File& file,std::uint64_t offset){LARGE_INTEGER value{};value.QuadPart=static_cast<LONGLONG>(offset);win(SetFilePointerEx(file.value,value,nullptr,FILE_BEGIN)!=0,"Capture seek");}
    void write(File& file,const void* p,std::size_t n){
        auto data=static_cast<const unsigned char*>(p);
        while(n){auto step=static_cast<DWORD>(std::min<std::size_t>(n,1u<<20));need(written<=options.fail_after_written_bytes&&step<=options.fail_after_written_bytes-written,"Declared transport failure injection");DWORD actual=0;win(WriteFile(file.value,data,step,&actual,nullptr)!=0&&actual==step,"Complete capture write");written+=step;data+=step;n-=step;}
    }
    void read(File& file,void* p,std::size_t n){auto data=static_cast<unsigned char*>(p);while(n){auto step=static_cast<DWORD>(std::min<std::size_t>(n,1u<<20));DWORD actual=0;win(ReadFile(file.value,data,step,&actual,nullptr)!=0&&actual==step,"Complete capture read");data+=step;n-=step;}}
    void append(std::string_view name,const void* data,std::size_t size){
        alive();auto key=name_key(name);need(size<=max_file&&(size==0||data!=nullptr),"Capture entry extent/pointer");need(!names.contains(key),"Duplicate normalized capture name");
        // Conservative canonical-index budget; exact index checked again at closure.
        const std::uint64_t index_cost=name.size()+140;
        need(index_cost+70<=options.index_bytes_per_part&&size<=options.bytes_per_part,"Entry fits unchanged part limits");
        if(!entries.empty()&&(entries.size()>=options.files_per_part||size>options.bytes_per_part-spool_bytes||index_cost>options.index_bytes_per_part-index_estimate))close_part();
        auto started=Clock::now();
        if(entries.empty()){spool_path=temporary/("part-"+number(receipt.parts.size()+1)+".spool");spool=create(spool_path);}
        Entry entry{std::string(name),hex(digest(data,size)),spool_bytes,size};
        names.insert(std::move(key));entries.push_back(std::move(entry));write(spool,data,size);spool_bytes+=size;index_estimate+=index_cost;
        ++receipt.logical_files;receipt.payload_bytes+=size;receipt.emit_seconds+=std::chrono::duration<double>(Clock::now()-started).count();
    }
    void close_part(){
        if(entries.empty())return;
        auto started=Clock::now();win(FlushFileBuffers(spool.value)!=0,"Flush compact spool");
        std::sort(entries.begin(),entries.end(),[](const Entry& a,const Entry& b){return a.name<b.name;});
        std::string index="{\"files\":[";std::uint64_t offset=0;
        for(std::size_t i=0;i<entries.size();++i){const auto& e=entries[i];if(i)index+=',';index+="{\"offset\":"+number(offset)+",\"path\":\""+e.name+"\",\"sha256\":\""+e.digest+"\",\"size\":"+number(e.size)+"}";offset+=e.size;}
        index+="],\"format\":\"mw34.capture.v1\",\"total_bytes\":"+number(offset)+"}";
        need(index.size()<=options.index_bytes_per_part&&offset==spool_bytes&&offset<=options.bytes_per_part&&entries.size()<=options.files_per_part,"Exact frozen canonical archive limits");
        auto index_digest=digest(index.data(),index.size());std::vector<unsigned char> header{'M','W','3','4','C','A','P','1'};little(header,index.size(),8);header.insert(header.end(),index_digest.begin(),index_digest.end());need(header.size()==48,"Exact frozen archive header");
        auto relative="part-"+number(receipt.parts.size()+1)+".mwb";auto path=temporary/relative;File archive=create(path);Hash whole(algorithm);write(archive,header.data(),header.size());whole.add(header.data(),header.size());write(archive,index.data(),index.size());whole.add(index.data(),index.size());
        std::vector<unsigned char> block(1u<<20);
        for(const auto& e:entries){seek(spool,e.spool_offset);Hash actual(algorithm);std::uint64_t remaining=e.size;while(remaining){auto step=static_cast<std::size_t>(std::min<std::uint64_t>(remaining,block.size()));read(spool,block.data(),step);actual.add(block.data(),step);write(archive,block.data(),step);whole.add(block.data(),step);remaining-=step;}need(hex(actual.finish())==e.digest,"Compact spool record changed before closure");}
        auto expected=hex(whole.finish());win(FlushFileBuffers(archive.value)!=0,"Flush finalized archive");
        // Reread complete written archive before publication using a fresh system hash.
        seek(archive,0);Hash check(algorithm);std::uint64_t remaining=header.size()+index.size()+offset;while(remaining){auto step=static_cast<std::size_t>(std::min<std::uint64_t>(remaining,block.size()));read(archive,block.data(),step);check.add(block.data(),step);remaining-=step;}need(hex(check.finish())==expected,"Written archive verification hash");
        LARGE_INTEGER extent{};win(GetFileSizeEx(archive.value,&extent)!=0,"Final archive extent");need(static_cast<std::uint64_t>(extent.QuadPart)==header.size()+index.size()+offset,"Final archive exact extent");archive.close();spool.close();win(DeleteFileW(spool_path.c_str())!=0,"Remove completed compact spool");
        receipt.parts.push_back({target/relative,expected,hex(index_digest),entries.size(),offset,static_cast<std::uint64_t>(extent.QuadPart),index.size()});entries.clear();spool_bytes=0;index_estimate=70;receipt.finalize_seconds+=std::chrono::duration<double>(Clock::now()-started).count();
    }
    void finish(){
        alive();need(receipt.logical_files>0,"Empty capture set refused");close_part();auto started=Clock::now();
        std::string manifest="{\"emit_seconds\":"+seconds(receipt.emit_seconds)+",\"finalize_parts_seconds\":"+seconds(receipt.finalize_seconds)+",\"format\":\"mw34.capture.direct.v1\",\"logical_files\":"+number(receipt.logical_files)+",\"native_executed\":false,\"parts\":[";
        for(std::size_t i=0;i<receipt.parts.size();++i){const auto& p=receipt.parts[i];if(i)manifest+=',';manifest+="{\"bundle\":\""+p.bundle.filename().string()+"\",\"bundle_bytes\":"+number(p.bundle_bytes)+",\"index_bytes\":"+number(p.index_bytes)+",\"index_sha256\":\""+p.index_sha256+"\",\"logical_files\":"+number(p.logical_files)+",\"payload_bytes\":"+number(p.payload_bytes)+",\"sha256\":\""+p.sha256+"\"}";}
        manifest+="],\"passed\":true,\"payload_bytes\":"+number(receipt.payload_bytes)+",\"transport_only\":true}";
        {File file=create(temporary/"transport.json");write(file,manifest.data(),manifest.size());win(FlushFileBuffers(file.value)!=0,"Flush complete transport manifest");}
        check_ancestors(target.parent_path());need(!fs::exists(target),"No-overwrite publication target");
        win(MoveFileExW(temporary.c_str(),target.c_str(),MOVEFILE_WRITE_THROUGH)!=0,"Atomic fresh whole-set publication");finished=true;
        receipt.finalize_seconds+=std::chrono::duration<double>(Clock::now()-started).count();
    }
};

Writer::Writer(const fs::path& path,Options options){preserved([&]{impl_=std::make_unique<Impl>(path,std::move(options));});}
void validate_ascii_name(std::string_view name){preserved([&]{(void)name_key(name);});}
Writer::~Writer() noexcept{try{preserved([&]{impl_.reset();});}catch(...) {}}
void Writer::append(std::string_view name,const void* p,std::size_t size){preserved([&]{try{impl_->append(name,p,size);}catch(...){impl_->failed=true;throw;}});}
void Writer::close_batch(){preserved([&]{try{impl_->alive();impl_->close_part();}catch(...){impl_->failed=true;throw;}});}
const Receipt& Writer::finish(){preserved([&]{try{impl_->finish();}catch(...){impl_->failed=true;throw;}});return impl_->receipt;}
}
