#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include "capture_shared.hpp"
#include <algorithm>
#include <array>
#include <charconv>
#include <chrono>
#include <fstream>
#include <iostream>
#include <limits>
#include <set>
#include <stdexcept>

namespace fs=std::filesystem;
namespace cd=mw34::capture_shared;
using Clock=std::chrono::steady_clock;
void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
std::uint64_t integer(std::string_view text){std::uint64_t n=0;auto r=std::from_chars(text.data(),text.data()+text.size(),n);need(r.ec==std::errc{}&&r.ptr==text.data()+text.size(),"Unsigned option integer");return n;}
void exact(std::istream& stream,void* data,std::size_t size){auto* p=static_cast<char*>(data);while(size){auto step=std::min<std::size_t>(size,1u<<20);stream.read(p,static_cast<std::streamsize>(step));need(static_cast<std::size_t>(stream.gcount())==step,"Truncated record input");p+=step;size-=step;}}
std::uint64_t little(std::istream& stream,unsigned width){std::array<unsigned char,8> b{};exact(stream,b.data(),width);std::uint64_t n=0;for(unsigned i=0;i<width;++i)n|=std::uint64_t(b[i])<<(i*8);return n;}
struct Input {
    std::ifstream stream;std::uint64_t count=0;
    explicit Input(const fs::path& path):stream(path,std::ios::binary){need(stream.is_open(),"Record input readable");char magic[8];exact(stream,magic,8);need(std::string_view(magic,8)=="MW34REC1","Record protocol magic");count=little(stream,4);need(count>0,"Nonempty record input");}
    template<class F> void each(F callback){for(std::uint64_t i=0;i<count;++i){auto names=little(stream,4),bytes=little(stream,8);need(names>0&&names<=1024&&bytes<=cd::max_file,"Bounded input record extents");std::string name(static_cast<std::size_t>(names),'\0');std::vector<unsigned char> data(static_cast<std::size_t>(bytes));exact(stream,name.data(),name.size());exact(stream,data.data(),data.size());callback(name,data,i+1);}need(stream.peek()==std::char_traits<char>::eof()&&!stream.bad(),"Exact EOF record protocol");}
};
void replay(const fs::path& input,const fs::path& output,cd::Options options,std::uint64_t close_every){
    auto start=Clock::now();Input records(input);cd::Writer writer(output,options);
    records.each([&](const auto& name,const auto& data,std::uint64_t ordinal){need(writer.try_append(name,data.data(),data.size()),"Checked append refused");if(close_every&&ordinal%close_every==0)need(writer.try_close_batch(),"Checked batch refused");});
    const auto* completed=writer.try_finish();need(completed!=nullptr,"Checked whole-set completion refused");const auto& r=*completed;double wall=std::chrono::duration<double>(Clock::now()-start).count();
    std::cout.precision(17);std::cout<<"{\"emit_seconds\":"<<r.emit_seconds<<",\"finalize_seconds\":"<<r.finalize_seconds<<",\"logical_files\":"<<r.logical_files<<",\"native_game_executed\":false,\"parts\":"<<r.parts.size()<<",\"passed\":true,\"payload_bytes\":"<<r.payload_bytes<<",\"unique_blobs\":"<<r.unique_blobs<<",\"unique_payload_bytes\":"<<r.unique_payload_bytes<<",\"transport_only\":true,\"wall_seconds\":"<<wall<<"}\n";
}
void ancestors(const fs::path& path){fs::path p;for(const auto& component:path){p/=component;DWORD a=GetFileAttributesW(p.c_str());if(a!=INVALID_FILE_ATTRIBUTES)need(!(a&FILE_ATTRIBUTE_REPARSE_POINT),"Benchmark ancestor reparse refused");else need(GetLastError()==ERROR_FILE_NOT_FOUND||GetLastError()==ERROR_PATH_NOT_FOUND,"Benchmark ancestor inaccessible");}}
bool beneath(const fs::path& a,const fs::path& b){auto x=a.wstring(),y=b.wstring();return x.size()>y.size()&&x[y.size()]==L'\\'&&CompareStringOrdinal(x.data(),static_cast<int>(y.size()),y.data(),static_cast<int>(y.size()),TRUE)==CSTR_EQUAL;}
void flat(const fs::path& input,const fs::path& output){
    // Controlled small same-input benchmark only. No production game uses this mode.
    auto start=Clock::now();auto root=(fs::current_path()/"reports").lexically_normal().make_preferred();auto target=fs::absolute(output).lexically_normal().make_preferred();need(beneath(target,root),"Benchmark output beneath reports");ancestors(target);need(!fs::exists(target),"Fresh benchmark output");
    Input records(input);need(records.count<=10000,"Flat benchmark has declared small bound");fs::create_directories(target.parent_path());auto private_path=target.parent_path()/(L"."+target.filename().wstring()+L".flat-"+std::to_wstring(GetCurrentProcessId()));need(!fs::exists(private_path),"Fresh private benchmark directory");need(CreateDirectoryW(private_path.c_str(),nullptr)!=0,"Benchmark directory creation");
    std::vector<fs::path> owned_files,owned_dirs{private_path};std::set<std::string> keys;std::uint64_t bytes=0;
    try{records.each([&](const auto& name,const auto& data,std::uint64_t){cd::validate_ascii_name(name);std::string key=name;for(auto& c:key)if(c>='A'&&c<='Z')c+=32;need(keys.insert(key).second,"Normalized benchmark duplicate");auto path=private_path/fs::path(name);need(beneath(path,private_path),"Owned benchmark file descendant");fs::path current=private_path;auto relative=path.parent_path().lexically_relative(private_path);for(const auto& component:relative){if(component==".")continue;current/=component;if(!fs::exists(current)){need(CreateDirectoryW(current.c_str(),nullptr)!=0,"Benchmark parent creation");owned_dirs.push_back(current);}ancestors(current);}need(!fs::exists(path),"Fresh benchmark file");std::ofstream stream(path,std::ios::binary|std::ios::out);need(stream.is_open(),"Benchmark file open");owned_files.push_back(path);if(!data.empty())stream.write(reinterpret_cast<const char*>(data.data()),static_cast<std::streamsize>(data.size()));stream.close();need(!stream.fail(),"Complete benchmark file write");bytes+=data.size();});
        ancestors(target.parent_path());need(!fs::exists(target),"No-overwrite benchmark publication");need(MoveFileExW(private_path.c_str(),target.c_str(),MOVEFILE_WRITE_THROUGH)!=0,"Whole-set benchmark publication");
    }catch(...){try{need(beneath(private_path,root),"Owned benchmark cleanup descendant");ancestors(private_path);for(const auto& p:owned_files){ancestors(p);DeleteFileW(p.c_str());}for(auto it=owned_dirs.rbegin();it!=owned_dirs.rend();++it){ancestors(*it);RemoveDirectoryW(it->c_str());}}catch(...){}throw;}
    double elapsed=std::chrono::duration<double>(Clock::now()-start).count();std::cout.precision(17);std::cout<<"{\"flat_benchmark_only\":true,\"logical_files\":"<<records.count<<",\"native_game_executed\":false,\"passed\":true,\"payload_bytes\":"<<bytes<<",\"wall_seconds\":"<<elapsed<<"}\n";
}
int main(int argc,char** argv){try{need(argc>=4,"Usage: driver replay|flat INPUT OUTPUT [--files-per-part N --bytes-per-part N --index-bytes-per-part N --close-every N --fail-after N]");cd::Options options;std::uint64_t close_every=0;for(int i=4;i<argc;i+=2){need(i+1<argc,"Option value required");auto value=integer(argv[i+1]);std::string_view key=argv[i];if(key=="--files-per-part")options.files_per_part=value;else if(key=="--bytes-per-part")options.bytes_per_part=value;else if(key=="--index-bytes-per-part")options.index_bytes_per_part=value;else if(key=="--close-every")close_every=value;else if(key=="--fail-after")options.fail_after_written_bytes=value;else if(key=="--force-key-collision"){need(value<=1,"Boolean collision fixture");options.force_hash_key_collision=value!=0;}else need(false,"Known driver option required");}std::string_view mode=argv[1];if(mode=="replay")replay(argv[2],argv[3],options,close_every);else if(mode=="flat"){need(argc==4,"Flat benchmark uses identical default workload");flat(argv[2],argv[3]);}else need(false,"Known driver mode required");return 0;}catch(const std::exception& e){std::cerr<<"Transport refusal: "<<e.what()<<'\n';return 2;}catch(...){std::cerr<<"Transport refusal: unknown failure\n";return 3;}}
