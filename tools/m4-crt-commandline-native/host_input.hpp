#pragma once
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include "provider.hpp"
#include <array>
#include <filesystem>
#include <fstream>
namespace mw34::m4_cmd_native {
struct HostRegion {std::uint64_t base,bytes,allocation;std::uint32_t state,type,protect,allocation_protect;friend bool operator==(const HostRegion&,const HostRegion&)=default;};
struct ApiIdentity {std::uint64_t target{},named_target{},owner{},owner_named_target{};HostRegion region{};std::wstring module_path;std::string module_sha;friend bool operator==(const ApiIdentity&,const ApiIdentity&)=default;};
inline HostRegion region(const void*p){MEMORY_BASIC_INFORMATION m{};require(VirtualQuery(p,&m,sizeof(m))==sizeof(m),"Actual host memory query unavailable");return {reinterpret_cast<std::uintptr_t>(m.BaseAddress),m.RegionSize,reinterpret_cast<std::uintptr_t>(m.AllocationBase),m.State,m.Type,m.Protect,m.AllocationProtect};}
inline std::vector<std::byte> readfile(const std::filesystem::path&p,std::uint64_t bound){std::ifstream f(p,std::ios::binary|std::ios::ate);require(bool(f),"Exact input file unavailable");auto n=f.tellg();require(n>=0&&std::uint64_t(n)<=bound,"Input file extent rejected");std::vector<std::byte>b(static_cast<std::size_t>(n));f.seekg(0);f.read(reinterpret_cast<char*>(b.data()),b.size());require(bool(f),"Input file read unavailable");return b;}
inline ApiIdentity api_identity(){
    ApiIdentity a;a.target=reinterpret_cast<std::uintptr_t>(&GetCommandLineA);auto kernel=GetModuleHandleW(L"kernel32.dll");require(kernel!=nullptr,"Loaded KERNEL32 missing");a.named_target=reinterpret_cast<std::uintptr_t>(GetProcAddress(kernel,"GetCommandLineA"));require(a.named_target==a.target,"Actual imported target differs from named KERNEL32 export");a.region=region(reinterpret_cast<const void*>(a.target));require(a.region.state==MEM_COMMIT&&a.region.type==MEM_IMAGE&&!(a.region.protect&(PAGE_GUARD|PAGE_NOACCESS))&&(a.region.protect&(PAGE_EXECUTE|PAGE_EXECUTE_READ|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY)),"Actual API target must be executable loaded image");a.owner=a.region.allocation;a.owner_named_target=reinterpret_cast<std::uintptr_t>(GetProcAddress(reinterpret_cast<HMODULE>(a.owner),"GetCommandLineA"));require(a.owner_named_target==a.target,"Actual loaded owner named export does not match target");std::array<wchar_t,32768>path{};auto n=GetModuleFileNameW(reinterpret_cast<HMODULE>(a.owner),path.data(),path.size());require(n&&n<path.size(),"Actual loaded target module path bound");a.module_path.assign(path.data(),n);a.module_sha=m4::sha256(readfile(std::filesystem::path(a.module_path),16*1024*1024));return a;
}
struct HostInput {std::uint64_t borrowed_pointer{};std::vector<std::byte>bytes;std::vector<HostRegion>regions;ApiIdentity before,after;};
inline HostInput own_host_input(){
    HostInput s;s.before=api_identity();const char*p=GetCommandLineA();require(p!=nullptr,"Actual command-line pointer null");s.borrowed_pointer=reinterpret_cast<std::uintptr_t>(p);std::uint64_t end{};
    for(unsigned i=0;i<131072;++i){require(s.borrowed_pointer<=UINTPTR_MAX-i,"Host borrowed pointer wrap");const auto at=s.borrowed_pointer+i;if(at>=end){auto m=region(reinterpret_cast<const void*>(at));require(m.state==MEM_COMMIT&&!(m.protect&(PAGE_GUARD|PAGE_NOACCESS))&&(m.protect&(PAGE_READONLY|PAGE_READWRITE|PAGE_WRITECOPY|PAGE_EXECUTE_READ|PAGE_EXECUTE_READWRITE|PAGE_EXECUTE_WRITECOPY))&&m.bytes<=UINT64_MAX-m.base,"Actual command line region unreadable");end=m.base+m.bytes;require(at>=m.base&&at<end,"Actual command-line region coverage");s.regions.push_back(m);}auto v=std::byte(static_cast<unsigned char>(p[i]));s.bytes.push_back(v);if(v==std::byte{}){s.after=api_identity();require(s.before==s.after,"API target identity changed across actual query");return s;}}
    throw std::invalid_argument("Actual command line terminator exceeds131072-byte bound");
}
}
