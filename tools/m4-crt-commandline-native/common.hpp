#pragma once
#include "host_input.hpp"
#include "../m4-crt/probe_common.hpp"
#include <iostream>
namespace mw34::m4_cmd_native {
using Cpu=m4_crt_probe::Cpu;
constexpr unsigned cases=48;
constexpr std::array<unsigned,5> observed_pages{0x78001000,0x7802e000,0x78037000,0x5bb000,0x20001000};
#pragma pack(push,1)
struct ApiRecord {std::uint64_t target,named_target,owner,owner_named_target;HostRegion region;char sha[64];wchar_t path[1024];};
struct Record {
 std::uint32_t id,repeat,cw,top,native,status,host_restored,input_bytes,input_regions,data_address,data_value,events,capture;
 Cpu before,after,service_before,service_after;
 std::uint64_t host_pointer;
 ApiRecord api_before,api_after;
 std::array<std::uint8_t,512> fx_before,fx_after,host_before,host_after,service_fx_before,service_fx_after;
 std::array<std::uint8_t,28> env_before,env_after,host_env_before,host_env_after,service_env_before,service_env_after;
 std::array<std::uint8_t,20480> memory_before,memory_after;
 std::array<std::uint8_t,3504> state_before,state_after;
 std::array<std::uint32_t,5> route;
 std::array<std::uint32_t,160> event_data;
};
struct Header {char magic[8];std::uint32_t version,count,record_bytes,pages,supplied_bytes,observed_bytes;};
#pragma pack(pop)
static_assert(sizeof(Cpu)==40&&sizeof(HostRegion)==40);
inline ApiRecord api_record(const ApiIdentity&a){ApiRecord r{};r.target=a.target;r.named_target=a.named_target;r.owner=a.owner;r.owner_named_target=a.owner_named_target;r.region=a.region;require(a.module_sha.size()==64&&a.module_path.size()<1024,"Measured API serialization bounds");std::memcpy(r.sha,a.module_sha.data(),64);std::copy(a.module_path.begin(),a.module_path.end(),r.path);return r;}
inline std::string environment(const char*name){auto n=GetEnvironmentVariableA(name,nullptr,0);require(n&&n<=131072,"Task-local measurement input unavailable/bounded");std::string v(n,'\0');require(GetEnvironmentVariableA(name,v.data(),n)==n-1,"Task-local measurement input changed");v.pop_back();return v;}
inline bool hostequal(const Record&r,bool native){bool ok=!std::memcmp(r.host_before.data(),r.host_after.data(),5)&&!std::memcmp(r.host_before.data()+24,r.host_after.data()+24,4)&&r.host_env_before==r.host_env_after;for(unsigned i=0;i<8;++i)ok=ok&&!std::memcmp(r.host_before.data()+32+i*16,r.host_after.data()+32+i*16,10);return ok&&!std::memcmp(r.host_before.data()+160,r.host_after.data()+160,native?256:128);}
class Output {std::filesystem::path dst,stage;HANDLE handle{INVALID_HANDLE_VALUE};bool owns{};
public:explicit Output(const std::string&p):dst(p),stage(p+".cmd-stage-"+std::to_string(GetCurrentProcessId())){require(!std::filesystem::exists(dst),"Fresh command-line result required");handle=CreateFileW(stage.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);require(handle!=INVALID_HANDLE_VALUE,"Fresh owned command-line stage required");owns=true;}~Output(){if(handle!=INVALID_HANDLE_VALUE)CloseHandle(handle);if(owns)DeleteFileW(stage.c_str());}void write(const void*p,unsigned n){DWORD done{};require(WriteFile(handle,p,n,&done,nullptr)&&done==n,"Command-line output write failed");}void commit(){require(FlushFileBuffers(handle)&&CloseHandle(handle),"Command-line output flush/close failed");handle=INVALID_HANDLE_VALUE;require(MoveFileExW(stage.c_str(),dst.c_str(),MOVEFILE_WRITE_THROUGH),"Command-line result commit failed");owns=false;}};
inline void prefix(Output&o,bool native,const std::string&supplied,std::span<const std::byte>actual){Header h{};std::memcpy(h.magic,native?"MW4CMNN1":"MW4CMNO1",8);h.version=1;h.count=cases;h.record_bytes=sizeof(Record);h.pages=5;h.supplied_bytes=static_cast<unsigned>(supplied.size());h.observed_bytes=static_cast<unsigned>(actual.size());o.write(&h,sizeof(h));o.write(supplied.data(),h.supplied_bytes);o.write(actual.data(),h.observed_bytes);}
}
