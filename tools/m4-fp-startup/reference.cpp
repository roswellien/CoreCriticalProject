// Private hardware observations of complete real startup FP roots. No native
// implementation or expected-value computation is present in this worker.
#include "probe_spec.hpp"
#include "original_broker.hpp"
#include <bcrypt.h>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <memory>
#include <sstream>
using namespace mw34::m4_fp;
static_assert(sizeof(void*)==4);
static void require(bool ok,const char *reason){if(!ok)throw std::runtime_error(reason);}
struct Cpu {std::uint32_t eax,ecx,edx,ebx,esp,ebp,esi,edi,flags,pc;};
static_assert(sizeof(Cpu)==40);
extern "C" {
Cpu fp_input{},fp_before{},fp_after{};
std::uint32_t fp_host_esp{};
alignas(16) std::uint8_t fp_guest_fx[512]{},fp_host_fx[512]{},fp_host_after[512]{};
alignas(16) std::uint8_t fp_fx_before[512]{},fp_fx_after[512]{};
std::uint8_t fp_env_before[28]{},fp_env_after[28]{},fp_host_env[28]{},fp_host_env_after[28]{};
void fp_enter();void fp_capture();void fp_restore();
}
static std::uint32_t execute(){__try{fp_enter();return 0;}__except(EXCEPTION_EXECUTE_HANDLER){fp_restore();return 1;}}
static std::string digest(const std::vector<std::uint8_t>&bytes){
    BCRYPT_ALG_HANDLE algorithm{};BCRYPT_HASH_HANDLE hash{};
    require(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)==0,"SHA provider failed");
    struct Close {BCRYPT_ALG_HANDLE a;BCRYPT_HASH_HANDLE &h;~Close(){if(h)BCryptDestroyHash(h);BCryptCloseAlgorithmProvider(a,0);}} close{algorithm,hash};
    require(BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0)==0,"SHA object failed");
    require(bytes.size()<=0xffffffffULL&&BCryptHashData(hash,const_cast<PUCHAR>(bytes.data()),static_cast<ULONG>(bytes.size()),0)==0,"SHA update failed");
    std::uint8_t result[32]{};require(BCryptFinishHash(hash,result,32,0)==0,"SHA final failed");
    std::ostringstream out;out<<std::hex<<std::setfill('0');for(auto value:result)out<<std::setw(2)<<unsigned(value);return out.str();
}
static std::vector<std::uint8_t> read(const char*path,std::size_t max){
    std::ifstream file(path,std::ios::binary|std::ios::ate);require(bool(file),"Input unavailable");
    const auto size=file.tellg();require(size>=0&&static_cast<std::uint64_t>(size)<=max,"Input extent rejected");
    std::vector<std::uint8_t> result(static_cast<std::size_t>(size));file.seekg(0);
    file.read(reinterpret_cast<char*>(result.data()),static_cast<std::streamsize>(result.size()));require(bool(file),"Input read failed");return result;
}
struct Region {
    void*base{};
    explicit Region(std::uint32_t address):base(mw34::original_broker::reserve_or_adopt(address)){}
    ~Region(){if(base)VirtualFree(base,0,MEM_RELEASE);}
    Region(const Region&)=delete;
};
struct Output {
    std::filesystem::path destination,stage;HANDLE handle{INVALID_HANDLE_VALUE};bool owns{};
    explicit Output(const char *path):destination(path),stage(destination.string()+".fp-stage-"+std::to_string(GetCurrentProcessId())){
        const auto attributes=GetFileAttributesW(destination.c_str());
        require(attributes==INVALID_FILE_ATTRIBUTES&&GetLastError()==ERROR_FILE_NOT_FOUND,"Output exists or cannot establish absence");
        handle=CreateFileW(stage.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);
        require(handle!=INVALID_HANDLE_VALUE,"Cannot own fresh staging file");owns=true;
    }
    ~Output(){if(handle!=INVALID_HANDLE_VALUE)CloseHandle(handle);if(owns)DeleteFileW(stage.c_str());}
    void write(const void*data,std::size_t size){DWORD written{};require(size<=0xffffffffULL&&WriteFile(handle,data,static_cast<DWORD>(size),&written,nullptr)&&written==size,"Output write failed");}
    void commit(){require(FlushFileBuffers(handle),"Output flush failed");require(CloseHandle(handle),"Output close failed");handle=INVALID_HANDLE_VALUE;
        require(MoveFileExW(stage.c_str(),destination.c_str(),MOVEFILE_WRITE_THROUGH),"Output commit failed");owns=false;}
};
static void protect(void*page,DWORD flags){DWORD previous{};require(VirtualProtect(page,4096,flags,&previous),"Page protect failed");}
int main(int argc,char**argv){try{
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    if(argc==2&&std::string(argv[1])=="--check-hash"){
        require(digest({})=="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","Empty SHA KAT failed");
        require(digest({'a','b','c'})=="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad","ABC SHA KAT failed");std::cout<<"2 SHA controls passed\n";return 0;}
    if(auto broker=mw34::original_broker::dispatch(argc,argv,4))return *broker;
    require(argc==4,"FP reference: exact-pages exact-image fresh-output");
    // One owner per reservation, even where multiple pages share a 64K base.
    std::vector<std::unique_ptr<Region>> regions;
    for(auto base:mw34::original_broker::bases)regions.push_back(std::make_unique<Region>(base));
    const auto image=read(argv[2],2384384);require(image.size()==2384384&&digest(image)=="95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf","Image identity rejected");
    const auto pack=read(argv[1],61572);require(pack.size()==61572&&digest(pack)==pack_sha,"Pack identity rejected");
    require(std::memcmp(pack.data(),"MW4FPK01",8)==0,"Pack version rejected");
    std::uint32_t count{};std::memcpy(&count,pack.data()+8,4);require(count==page_bases.size(),"Pack count rejected");
    std::array<void*,15> pages{};
    for(std::size_t i=0;i<pages.size();++i){
        const auto offset=12+i*4104;std::uint32_t base{},permission{};
        std::memcpy(&base,pack.data()+offset,4);std::memcpy(&permission,pack.data()+offset+4,4);
        require(base==page_bases[i]&&permission==page_permissions[i],"Pack page layout rejected");
        pages[i]=VirtualAlloc(reinterpret_cast<void*>(base),4096,MEM_COMMIT,PAGE_READWRITE);
        require(pages[i]==reinterpret_cast<void*>(base),"Exact page commit failed");
        std::memcpy(pages[i],pack.data()+offset+8,4096);
        protect(pages[i],permission==1?PAGE_EXECUTE_READ:permission==0?PAGE_READONLY:PAGE_READWRITE);
        if(permission==1)require(FlushInstructionCache(GetCurrentProcess(),pages[i],4096),"Code cache flush failed");
    }
    auto*capture=static_cast<std::uint8_t*>(VirtualAlloc(reinterpret_cast<void*>(0x10000000),4096,MEM_COMMIT,PAGE_READWRITE));
    require(capture==reinterpret_cast<void*>(0x10000000),"Capture commit failed");
    auto*stub=capture+0x100;stub[0]=0xe9;const auto delta=static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(&fp_capture)-0x10000105);
    std::memcpy(stub+1,&delta,4);protect(capture,PAGE_EXECUTE_READ);
    require(FlushInstructionCache(GetCurrentProcess(),capture,4096),"Capture cache flush failed");
    Output out(argv[3]);const std::uint32_t header[]{1,480,9,4096};out.write("MW4FPO01",8);out.write(header,sizeof(header));
    std::array<std::uint8_t,9*4096> memory_before{},memory_after{};
    const std::array<std::uint16_t,12> controls{0x007f,0x047f,0x087f,0x0c7f,0x027f,0x067f,0x0a7f,0x0e7f,0x037f,0x077f,0x0b7f,0x0f7f};
    for(unsigned repeat=0;repeat<2;++repeat)for(auto entry:entries)for(auto cw:controls)for(unsigned top:{0u,7u}){
        for(std::size_t i=6;i<pages.size();++i){if(page_permissions[i]==2)std::memcpy(pages[i],pack.data()+12+i*4104+8,4096);}
        const std::uint32_t sentinel=0x10000100;std::memcpy(reinterpret_cast<void*>(0x20001800),&sentinel,4);
        for(std::size_t i=6;i<pages.size();++i)std::memcpy(memory_before.data()+(i-6)*4096,pages[i],4096);
        fp_input={0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xaabbccdd,0x202,entry};
        std::memset(fp_guest_fx,0,512);std::memcpy(fp_guest_fx,&cw,2);
        const auto sw=static_cast<std::uint16_t>(top<<11);std::memcpy(fp_guest_fx+2,&sw,2);
        const std::uint32_t mxcsr=0x1f80;std::memcpy(fp_guest_fx+24,&mxcsr,4);
        fp_before={};fp_after={};const auto status=execute();
        require(!status,"Original FP execution faulted");
        require(fp_after.pc==sentinel&&fp_after.esp==fp_input.esp+4,"Original return contract failed");
        require(std::memcmp(fp_host_fx,fp_host_after,5)==0&&std::memcmp(fp_host_fx+24,fp_host_after+24,4)==0&&
                std::memcmp(fp_host_env,fp_host_env_after,28)==0,"Host FP environment restoration failed");
        for(unsigned i=0;i<8;++i)require(std::memcmp(fp_host_fx+32+i*16,fp_host_after+32+i*16,10)==0,"Host x87 storage restoration failed");
        require(std::memcmp(fp_host_fx+160,fp_host_after+160,128)==0,"Host XMM restoration failed");
        for(std::size_t i=6;i<pages.size();++i)std::memcpy(memory_after.data()+(i-6)*4096,pages[i],4096);
        const std::uint32_t tag[]{repeat,entry,cw,top,status};out.write(tag,sizeof(tag));out.write(&fp_before,sizeof(fp_before));out.write(&fp_after,sizeof(fp_after));
        for(auto snapshot:{fp_fx_before,fp_fx_after,fp_host_fx,fp_host_after})out.write(snapshot,512);
        for(auto snapshot:{fp_env_before,fp_env_after,fp_host_env,fp_host_env_after})out.write(snapshot,28);
        out.write(memory_before.data(),memory_before.size());out.write(memory_after.data(),memory_after.size());
    }
    // Read-only code and constants remain exactly pinned after all executions.
    for(std::size_t i=0;i<pages.size();++i)if(page_permissions[i]!=2)require(std::memcmp(pages[i],pack.data()+12+i*4104+8,4096)==0,"Protected page identity changed");
    out.commit();std::cout<<"480 actual original startup FP records captured; native equivalence remains open\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
