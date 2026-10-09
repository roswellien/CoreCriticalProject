#pragma once
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <bcrypt.h>
#include "spec.hpp"
#include <algorithm>
#include <array>
#include <bit>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <span>
#include <sstream>
#include <stdexcept>
#include <vector>
namespace mw34::spi {
constexpr std::uint32_t entry=0x482cf0,object=0x608f88,output=object+24,frame=0x20001800,broker=0x482ff0,call=0x482cdd,resume=0x482ce3,iat=0x5bb6dc;
constexpr std::array<std::uint32_t,3> observed_pages{0x5e6000,0x608000,0x20001000};
constexpr std::array<std::uint16_t,12> controls{0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f};
constexpr unsigned cases=144;
inline void require(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
template<class T>T word(const void*p){T v;std::memcpy(&v,p,sizeof(v));return v;}
inline std::vector<std::uint8_t> read(const char*p,std::size_t limit){std::ifstream f(p,std::ios::binary|std::ios::ate);require(bool(f),"Input unavailable");auto n=f.tellg();require(n>=0&&std::uint64_t(n)<=limit,"Input extent rejected");std::vector<std::uint8_t>b(static_cast<std::size_t>(n));f.seekg(0);f.read(reinterpret_cast<char*>(b.data()),b.size());require(bool(f),"Input read failed");return b;}
inline std::string sha(std::span<const std::uint8_t>b){BCRYPT_ALG_HANDLE a{};BCRYPT_HASH_HANDLE h{};require(!BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,nullptr,0),"SHA provider");struct Cleanup{BCRYPT_ALG_HANDLE a;BCRYPT_HASH_HANDLE&h;~Cleanup(){if(h)BCryptDestroyHash(h);BCryptCloseAlgorithmProvider(a,0);}}c{a,h};require(!BCryptCreateHash(a,&h,nullptr,0,nullptr,0,0)&&b.size()<=0xffffffffULL&&!BCryptHashData(h,const_cast<PUCHAR>(b.data()),ULONG(b.size()),0),"SHA update");std::array<std::uint8_t,32>d{};require(!BCryptFinishHash(h,d.data(),32,0),"SHA final");std::ostringstream s;s<<std::hex<<std::setfill('0');for(auto x:d)s<<std::setw(2)<<unsigned(x);return s.str();}
inline void provider(bool native){
    auto module=GetModuleHandleW(L"user32.dll");if(!module)module=LoadLibraryExW(L"user32.dll",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);require(module!=nullptr,"Loaded system USER32 unavailable");std::array<wchar_t,32768>path{};auto n=GetModuleFileNameW(module,path.data(),path.size());require(n&&n<path.size(),"Loaded provider path truncated");
    std::ifstream f(std::filesystem::path(path.data()),std::ios::binary);require(bool(f),"Loaded provider file unavailable");const std::vector<std::uint8_t>b((std::istreambuf_iterator<char>(f)),{});
    require(sha(b)==(native?provider64_sha:provider32_sha),"Loaded USER32 identity changed");
    std::wcout<<L"Loaded USER32 path="<<path.data()<<L" base="<<reinterpret_cast<std::uintptr_t>(module)<<L" architecture="<<(native?64:32)<<L"\n";
}
inline std::vector<std::uint8_t> admit(const char*pp,const char*ip){auto image=read(ip,2384384);require(image.size()==2384384&&sha(image)==image_sha,"Exact image identity required");auto pack=read(pp,20532);require(pack.size()==20532&&sha(pack)==pack_sha&&std::memcmp(pack.data(),"MW4SPIP1",8)==0&&word<std::uint32_t>(pack.data()+8)==5,"Exact private pack required");return pack;}
#pragma pack(push,1)
struct Cpu {std::array<std::uint32_t,8>gpr;std::uint32_t flags,pc;};
struct Service {Cpu before,after;std::array<std::uint8_t,512>fx_before,fx_after;std::array<std::uint8_t,28>env_before,env_after;std::array<std::uint8_t,16>rect_before,rect_after;std::uint32_t called,BOOL_value,guest_cleanup,provider_ESP_before,provider_ESP_after;};
struct Event {std::uint32_t pc,address,value,width,operation;};
struct Record {
    std::uint32_t id,repeat,cw,top,variant,status,host_restored,native,service_defined_cpu;
    Cpu before,after;
    std::array<std::uint8_t,512>fx_before,fx_after,host_before,host_after;
    std::array<std::uint8_t,28>env_before,env_after,host_env_before,host_env_after;
    std::array<std::uint8_t,12288>memory_before,memory_after;
    std::array<std::uint8_t,3504>state_before,state_after;
    Service service;
    std::uint32_t event_count,completed;
    std::array<Event,64>events;
};
struct Header {char magic[8];std::uint32_t version,count,record_bytes,observed_pages;};
#pragma pack(pop)
static_assert(sizeof(Cpu)==40&&sizeof(RECT)==16&&sizeof(LONG)==4);
static_assert(sizeof(Service)==1212&&sizeof(Record)==36360);
inline Cpu initial(unsigned v){return {{0x13579bdfU+v,0x2468ace0U+v,0x81726354U+v,0x10293847U+v,frame,0x92837465U+v,0x56473829U+v,0xaabbccddU+v},v==1?0xad7U:v==2?0x293U:0x202U,entry};}
inline std::array<std::uint8_t,512> initialfx(unsigned cw,unsigned top,unsigned v){std::array<std::uint8_t,512>fx{};const std::uint16_t c=cw,s=top<<11;const std::uint32_t m=0x1f80;std::memcpy(fx.data(),&c,2);std::memcpy(fx.data()+2,&s,2);std::memcpy(fx.data()+24,&m,4);for(unsigned i=0;i<128;++i)fx[160+i]=static_cast<std::uint8_t>(i*13+v*17);return fx;}
inline std::array<std::uint8_t,4096> pagefixture(unsigned page,unsigned v){std::array<std::uint8_t,4096>b{};if(page==1&&v)for(unsigned i=0;i<b.size();++i)b[i]=static_cast<std::uint8_t>(i*37+v*71+(i>>8)*5);if(page==2)b.fill(0xa5);return b;}
inline bool hostequal(const Record&r,bool native){bool ok=!std::memcmp(r.host_before.data(),r.host_after.data(),5)&&!std::memcmp(r.host_before.data()+24,r.host_after.data()+24,4)&&r.host_env_before==r.host_env_after;for(unsigned i=0;i<8;++i)ok=ok&&!std::memcmp(r.host_before.data()+32+i*16,r.host_after.data()+32+i*16,10);return ok&&!std::memcmp(r.host_before.data()+160,r.host_after.data()+160,native?256:128);}
class Output {std::filesystem::path dst,stage;HANDLE h{INVALID_HANDLE_VALUE};bool owns{};public:explicit Output(const char*p):dst(p),stage(dst.string()+".spi-stage-"+std::to_string(GetCurrentProcessId())){require(!std::filesystem::exists(dst),"Fresh output required");h=CreateFileW(stage.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);require(h!=INVALID_HANDLE_VALUE,"Fresh owned stage required");owns=true;}~Output(){if(h!=INVALID_HANDLE_VALUE)CloseHandle(h);if(owns)DeleteFileW(stage.c_str());}void write(const void*p,unsigned n){DWORD done{};require(WriteFile(h,p,n,&done,nullptr)&&done==n,"Output write failed");}void commit(){require(FlushFileBuffers(h)&&CloseHandle(h),"Output flush/close failed");h=INVALID_HANDLE_VALUE;require(MoveFileExW(stage.c_str(),dst.c_str(),MOVEFILE_WRITE_THROUGH),"Output commit failed");owns=false;}};
}
