// Independent string input, ownership and partial-copy controls over frozen71.
#pragma once
#include "D:/Projects/MW34Recomp/tools/m4-crt-commandline-native/host_input.hpp"
namespace mw34_onexit_review {
using mw34::Permissions;
inline unsigned selected{},hits{},checks{},thread_checks{};
inline std::vector<unsigned>owned_guest_aliases;
inline mw34::m4_cmd_native::ApiIdentity cleanup_api_after;
inline std::array<std::uint64_t,32>trigger_string{};
inline std::array<std::uint64_t,5>trigger_copy{};
inline std::vector<std::byte>trigger_native_before;
inline void check(bool b,const char*why){++checks;if(!b)throw std::runtime_error(why);}
inline mw34::m4_cmd_native::ApiIdentity pressure_identity(const char*requested,std::uintptr_t target){
 using namespace mw34::m4_cmd_native;
 auto kernel=GetModuleHandleW(L"kernel32.dll");check(kernel,"Research pressure named kernel module");
 ApiIdentity a;a.target=target;a.named_target=reinterpret_cast<std::uintptr_t>(GetProcAddress(kernel,requested));
 check(a.named_target==target,"Research pressure imported and named API match");a.region=region(reinterpret_cast<void*>(target));a.owner=a.region.allocation;
 const char*alias=std::string_view(requested)=="HeapAlloc"?"RtlAllocateHeap":std::string_view(requested)=="HeapSize"?"RtlSizeHeap":requested;
 a.owner_named_target=reinterpret_cast<std::uintptr_t>(GetProcAddress(reinterpret_cast<HMODULE>(a.owner),alias));
 check(a.owner_named_target==target&&a.region.state==MEM_COMMIT&&a.region.type==MEM_IMAGE,
       "Research pressure executable actual owning API export");
 std::array<wchar_t,32768>path{};auto n=GetModuleFileNameW(reinterpret_cast<HMODULE>(a.owner),path.data(),path.size());
 check(n&&n<path.size(),"Research pressure physical owning module path");a.module_path.assign(path.data(),n);
 a.module_sha=mw34::m4::sha256(readfile(std::filesystem::path(a.module_path),16*1024*1024));return a;
}
inline void add_alias(unsigned address){if(address&&std::find(owned_guest_aliases.begin(),owned_guest_aliases.end(),address)==owned_guest_aliases.end())owned_guest_aliases.push_back(address);}
inline void receive(std::string_view name,std::span<const std::byte>bytes,void*){
 if(name=="locale-allocations.bin")for(std::size_t n=0;n+128<=bytes.size();n+=128){std::array<std::uint64_t,16>row{};std::memcpy(row.data(),bytes.data()+n,128);add_alias(unsigned(row[1]));}
}
template<class Session>void observe(Session&s,unsigned point){
 const auto rows=s.string_witnesses();if(rows.empty()||hits||!selected||selected==12)return;
 const std::array<unsigned,14>points{0,50,50,50,52,54,50,51,52,53,54,55,0,52};
 if(point!=points[selected])return;
 const auto w=rows.back();check(w[0]==1&&w[2]==0x4487e0&&w[4]&&w[7]==10,"First genuine Lab State duplicate control boundary");
 if(selected==5&&w[16]!=4)return;
 ++hits;trigger_string=w;trigger_copy=s.string_copy_probe();add_alias(unsigned(w[10]));
 if(w[11]&&w[13]){trigger_native_before.resize(w[13]);std::memcpy(trigger_native_before.data(),reinterpret_cast<const void*>(w[11]),w[13]);}
 auto&r=s.runtime();
 if(selected==1){r.memory().store<unsigned>({unsigned(w[5]+4)},0);return;}
 if(selected==2){const auto value=r.memory().load<unsigned char>({unsigned(w[4])});r.memory().store<unsigned char>({unsigned(w[4])},value^1);return;}
 if(selected==3){r.memory().protect({unsigned(w[4])&~4095U},Permissions::none);return;}
 if(selected==4||selected==5){r.memory().protect({unsigned(w[10])&~4095U},Permissions::read);return;}
 if(selected==13){check(w[11]&&w[13],"Actual privately owned full native allocation");auto*p=reinterpret_cast<unsigned char*>(w[11]);*p^=0x55;return;}
 throw std::runtime_error("Independent deliberate string boundary observer failure");
}
}
