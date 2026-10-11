#pragma once
#include "D:/Projects/MW34Recomp/tools/m4-strings-review/fixture_hooks_v2.hpp"
namespace mw34_vtable_controls {
using mw34_onexit_review::check;
inline unsigned selected{},hits{},mutation_hits{},trigger_point{},trigger_PC{};
struct Snapshot {
 std::vector<std::array<std::uint64_t,32>>calls;
 std::vector<std::array<std::uint64_t,16>>stores;
 std::array<std::uint64_t,8>read{},vptr{};
 std::array<std::uint64_t,16>store{};unsigned active{};
};
template<class A>void copy_span(A&dst,std::span<const std::byte>b){check(b.size()==sizeof(dst),"Exact real private probe span");std::memcpy(&dst,b.data(),b.size());}
inline void snapshot_sink(std::string_view name,std::span<const std::byte>b,void*context){
 auto&s=*static_cast<Snapshot*>(context);
 if(name=="vtable-call-witnesses.bin"){check(b.size()%256==0,"Whole actual call witness rows");s.calls.resize(b.size()/256);std::memcpy(s.calls.data(),b.data(),b.size());}
 if(name=="vtable-source-stores.bin"){check(b.size()%128==0,"Whole actual store rows");s.stores.resize(b.size()/128);std::memcpy(s.stores.data(),b.data(),b.size());}
 if(name=="vtable-read-probe.bin")copy_span(s.read,b);
 if(name=="vtable-instance-vptr.bin")copy_span(s.vptr,b);
 if(name=="vtable-store-probe.bin")copy_span(s.store,b);
 if(name=="vtable-active.bin")copy_span(s.active,b);
}
template<class Session>Snapshot snapshot(Session&s){Snapshot x;s.dump(&snapshot_sink,&x);return x;}
inline Snapshot trigger{};
inline std::array<std::byte,3504>trigger_state{};
inline std::array<std::byte,512>trigger_fx{};
inline std::array<std::byte,40>trigger_cpu{};
inline std::array<std::byte,28>trigger_env{};
inline std::array<std::byte,4096>trigger_stack{};
inline std::array<unsigned,5>trigger_tib{};
inline std::array<unsigned,3>trigger_record{};
inline std::array<std::uint64_t,32>trigger_frame{};
inline std::vector<std::byte>private_before,private_after;
inline std::string private_name;
inline std::array<std::uint64_t,8>actual_intervention{};
template<class Runtime>void game_change(Runtime&r,unsigned address,unsigned value){
 for(const auto&g:r.image_metadata().mapped_regions)if(address>=g.start.value&&std::uint64_t{address}+4<=std::uint64_t{g.start.value}+g.size){
  actual_intervention={1,address,r.memory().template load<unsigned>({address}),value,g.start.value,unsigned(g.permissions),0,0};
  r.memory().protect(g.start,mw34::Permissions::read|mw34::Permissions::write);
  r.memory().template store<unsigned>({address},value);r.memory().protect(g.start,g.permissions);
  actual_intervention[6]=r.memory().template load<unsigned>({address});return;
 }throw std::runtime_error("Exact admitted game mutation region missing");
}
inline void mutate_private(std::string_view name,std::span<const std::byte>b,void*){
 const char*wanted=selected==11?"vtable-call-witnesses.bin":selected==12?"vtable-instance-vptr.bin":selected==13?"vtable-source-stores.bin":selected==14?"vtable-read-probe.bin":selected==15?"vtable-store-probe.bin":"vtable-active.bin";
 if(name!=wanted)return;
 private_name=std::string(name);private_before.assign(b.begin(),b.end());
 if(selected==16){check(b.size()==4,"Exact nonconst actual active DWORD");auto*w=reinterpret_cast<unsigned*>(const_cast<std::byte*>(b.data()));w[0]^=1;}
 else{check(b.size()>=64,"Actual nonconst actual private vector/probe");auto*w=reinterpret_cast<std::uint64_t*>(const_cast<std::byte*>(b.data()));const auto index=selected==11?b.size()/8-32+6:selected==12?4:selected==13?b.size()/8-16+6:selected==14?5:6;w[index]^=1;}
 private_after.assign(b.begin(),b.end());++mutation_hits;
}
template<class Session>void observe(Session&s,unsigned point){
 if(!selected||hits)return;
 auto&r=s.runtime();auto*state=reinterpret_cast<State*>(r.remill_state().data());const auto pc=state->gpr.rip.dword;
 constexpr unsigned points[]{0,110,110,110,110,114,115,114,114,111,110,111,111,115,110,114,112,110,111,112,113,114,115,80,82,83,81};
 if(point!=points[selected])return;
 auto x=snapshot(s);
 const auto root=point>=110?(point<=111?x.read[1]:point<=113?(x.calls.empty()?0:x.calls.back()[2]):x.store[2]):(s.fs_witnesses().empty()?0:s.fs_witnesses().back()[2]);
 unsigned wanted_root=0x40f0e0,wanted_pc{};
 if(selected==1||selected==11||selected==14||selected==16||selected==17||selected==18||selected==19||selected==20)wanted_pc=0x59fbab;
 if(selected==2){wanted_root=0x4795f0;wanted_pc=0x59fdc5;}
 if(selected==3||selected==9||selected==10){wanted_root=0x4795f0;wanted_pc=0x59ff6e;}
 if(selected==4||selected==12){wanted_root=0x4795f0;wanted_pc=0x59ff64;}
 if(selected==5||selected==6||selected==13||selected==15||selected==21||selected==22)wanted_pc=0x59fba5;
 if(selected==7)wanted_pc=0x40f138;
 if(selected==8){wanted_root=0x47f5f0;wanted_pc=0x40e824;}
 if(selected>=23)wanted_root=0x47f5f0;
 // At113 the source PC is the genuine CALL return rather than original CALL PC.
 if(selected==20)wanted_pc=0x59fbb1;
 if(selected==16||selected==19)wanted_pc=0x40e820;
 if(root!=wanted_root||(wanted_pc&&pc!=wanted_pc))return;
 ++hits;trigger_point=point;trigger_PC=pc;trigger=std::move(x);
 std::copy(r.remill_state().begin(),r.remill_state().end(),trigger_state.begin());std::copy(r.fx().begin(),r.fx().end(),trigger_fx.begin());std::memcpy(trigger_cpu.data(),&r.cpu(),40);trigger_env=mw34::m4_nmx_integration::view(*state).env;
 r.memory().read({0x20001000},trigger_stack);const auto base=r.fs_base().value;
 trigger_tib={base,r.memory().template load<unsigned>({base}),r.memory().template load<unsigned>({base+4}),r.memory().template load<unsigned>({base+8}),r.memory().template load<unsigned>({base+0x18})};
 if(!s.fs_witnesses().empty()){trigger_frame=s.fs_witnesses().back();if(trigger_frame[9])r.memory().read({unsigned(trigger_frame[9])},std::as_writable_bytes(std::span(trigger_record)));}
 if(selected<=3){const auto slot=selected==1?0x5cfd14U:selected==2?0x5bc100U:0x5bc0fcU;const auto old=r.memory().template load<unsigned>({slot});game_change(r,slot,old^4);return;}
 if(selected==4){game_change(r,0x608ae0,0x5bc0e0^4);return;}
 if(selected==5||selected==6||selected==7||selected==8){r.memory().protect({0x5e0000},mw34::Permissions::read);actual_intervention={2,0x5e0000,0,0,0x5e0000,1,0,0};return;}
 if(selected==9){const auto argument=state->gpr.rsp.dword;const auto old=r.memory().template load<unsigned>({argument});r.memory().template store<unsigned>({argument},1);actual_intervention={3,argument,old,1,state->gpr.rsp.dword,0,r.memory().template load<unsigned>({argument}),0};return;}
 if(selected==10){const auto old=state->gpr.rdx.dword;state->gpr.rdx.dword^=4;const auto offset=reinterpret_cast<const std::byte*>(&state->gpr.rdx.dword)-reinterpret_cast<const std::byte*>(state);actual_intervention={4,std::uint64_t(offset),old,state->gpr.rdx.dword,0,0,0,0};return;}
 if(selected>=11&&selected<=16){s.dump(&mutate_private,nullptr);check(mutation_hits==1,"Exactly one actual private backing witness mutation");return;}
 if(selected==25){r.memory().protect({base},mw34::Permissions::read);actual_intervention={2,base,0,0,base,1,0,0};return;}
 if(selected==26){const auto a=unsigned(trigger_frame[9])+4;const auto old=r.memory().template load<unsigned>({a});r.memory().template store<unsigned>({a},old^4);actual_intervention={3,a,old,old^4,0,0,r.memory().template load<unsigned>({a}),0};return;}
 throw std::runtime_error("Independent deliberate finite-vtable source boundary observer failure");
}
}
