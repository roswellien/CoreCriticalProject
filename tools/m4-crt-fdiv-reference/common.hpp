// Authored reference capture schema. No provider instruction byte literals.
#pragma once
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <array>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <vector>
#include "../m4-crt/probe_common.hpp"
#include "../m4-crt/probe_io.hpp"
#include "../m4-crt-fdiv/host_services.hpp"
namespace mw34::m4_fdiv_reference {
using mw34::m4_crt_probe::Cpu;
using mw34::m4_crt_probe::need;
inline constexpr std::array<unsigned,7> page_addresses{
    0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000};
inline constexpr std::array<unsigned,7> page_permissions{5,5,5,1,1,1,3};
inline constexpr std::array<unsigned,3> return_pcs{0x780042ae,0x780042c2,0x780042ce};
inline constexpr unsigned maximum_stack=1024*1024,records=48,maximum_debug_events=8;
#pragma pack(push,1)
struct HostRegion {std::uint64_t base,bytes,allocation;unsigned state,type,protect,allocation_protect;};
struct ApiIdentity {std::uint64_t address,named,owner,owner_named;HostRegion region;char sha[64];wchar_t path[1024];};
struct ModuleIdentity {std::uint64_t handle;HostRegion region;char sha[64];wchar_t path[1024];};
struct DebugEvent {unsigned ordinal,thread_id;EXCEPTION_RECORD exception;CONTEXT before,continued;};
struct Tags {
    unsigned id,repeat,debug,cw,status,debug_count,debug_unexpected;
    unsigned stack_base,stack_bytes,writer_sp,limit_before,base_before,limit_after,base_after;
    unsigned thread_id,teb,worker_base,context_bytes,stack_pages_before,stack_pages_after;
    unsigned source_api_module,source_api_proc,expected_module,expected_feature;
    unsigned snapshot_complete,restore_checkpoint,entry_complete;
};
struct Record {
    Tags tags;
    Cpu before,after;
    std::array<std::uint8_t,512> fx_before,fx_after,host_before,host_after;
    std::array<std::uint8_t,28> env_before,env_after,host_env_before,host_env_after;
    std::array<std::uint8_t,7*4096> pages_before,pages_after;
    std::array<DebugEvent,maximum_debug_events> debug_events;
    std::array<ApiIdentity,3> api_before,api_after;
    ModuleIdentity module_before,module_after;
    CONTEXT suspended_before,suspended_admitted;
    std::array<HostRegion,7> source_regions_before,source_regions_after;
    HostRegion excluded_guard_before,excluded_guard_after;
};
#pragma pack(pop)
static_assert(sizeof(void*)==4&&sizeof(EXCEPTION_RECORD)==80&&sizeof(CONTEXT)==716);
static_assert(sizeof(HostRegion)==40&&sizeof(ApiIdentity)==2184&&sizeof(ModuleIdentity)==2160);
static_assert(sizeof(DebugEvent)==1520&&sizeof(Tags)==108&&sizeof(Record)==91348);
inline HostRegion region(unsigned address){auto v=m4_crt_fdiv::region(address);return {v.base,v.bytes,v.allocation,v.state,v.type,v.protect,v.allocation_protect};}
inline ApiIdentity identity(const m4_crt_fdiv::HostIdentity&v){
    need(v.path.size()<1024&&v.sha.size()==64,"Bounded original API identity");ApiIdentity r{};
    r.address=v.address;r.named=v.named;r.owner=v.owner;r.owner_named=v.owner_named;
    r.region={v.region.base,v.region.bytes,v.region.allocation,v.region.state,v.region.type,v.region.protect,v.region.allocation_protect};
    std::memcpy(r.sha,v.sha.data(),64);std::memcpy(r.path,v.path.data(),v.path.size()*sizeof(wchar_t));return r;
}
inline ModuleIdentity identity(const m4_crt_fdiv::ModuleIdentity&v){
    need(v.path.size()<1024&&v.sha.size()==64,"Bounded original module identity");ModuleIdentity r{};r.handle=v.handle;
    r.region={v.region.base,v.region.bytes,v.region.allocation,v.region.state,v.region.type,v.region.protect,v.region.allocation_protect};
    std::memcpy(r.sha,v.sha.data(),64);std::memcpy(r.path,v.path.data(),v.path.size()*sizeof(wchar_t));return r;
}
// CREATE_NEW owns the actual output atomically. A failure retains its complete
// observed prefix; only a successful complete gate writes the terminal marker.
struct Output {
    HANDLE handle{INVALID_HANDLE_VALUE};
    explicit Output(const char*path){handle=CreateFileW(std::filesystem::path(path).c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);need(handle!=INVALID_HANDLE_VALUE,"Fresh original reference output required");}
    ~Output(){if(handle!=INVALID_HANDLE_VALUE)CloseHandle(handle);}
    void write(const void*data,std::size_t n){DWORD done{};need(n<=0xffffffffULL&&WriteFile(handle,data,static_cast<DWORD>(n),&done,nullptr)&&done==n,"Original observed output write failed");}
    void finish(){write("COMPLETE",8);need(FlushFileBuffers(handle)!=0,"Original output flush failed");}
};
}
