#pragma once
#include "D:/Projects/MW34Recomp/tools/m4-strings-review/fixture_hooks_v2.hpp"
namespace mw34_lockit_controls {
using mw34_onexit_review::check;
inline unsigned selected{},hits{},mutation_hits{},trigger_point{},trigger_PC{};
struct Snapshot{std::vector<std::array<std::uint64_t,16>>calls;};
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
inline CRITICAL_SECTION*restore_resource{};
inline std::array<std::byte,40>resource_before{},resource_after{};
inline void snapshot_sink(std::string_view name,std::span<const std::byte>b,void*context){if(name=="lockit-calls.bin"){auto&s=*static_cast<Snapshot*>(context);check(b.size()%128==0,"Whole real Lockit CALL witnesses");s.calls.resize(b.size()/128);std::memcpy(s.calls.data(),b.data(),b.size());}}
template<class Session>Snapshot snapshot(Session&s){Snapshot x;s.dump(&snapshot_sink,&x);return x;}
inline void mutate_private(std::string_view name,std::span<const std::byte>b,void*){
 const char*wanted=selected==8?"lockit-calls.bin":selected==9?"lockit-imports.bin":selected==10?"lockit-source-CS.bin":"lockit-native-images.bin";
 if(name!=wanted)return;check(!b.empty(),"Actual Lockit private witness present");private_name=std::string(name);private_before.assign(b.begin(),b.end());
 const auto offset=selected==8?6*8:selected==9?4*8:selected==10?4:12;check(offset<b.size(),"Actual private mutation byte exists");const_cast<std::byte*>(b.data())[offset]^=std::byte{1};private_after.assign(b.begin(),b.end());++mutation_hits;
}
inline void mutate_actual(std::string_view name,std::span<const std::byte>b,void*){
 if(name!="locale-critical-sections.bin")return;check(b.size()%128==0,"Whole actual CS owner records");
 for(std::size_t offset=0;offset<b.size();offset+=128){std::array<std::uint64_t,16>row{};std::memcpy(row.data(),b.data()+offset,128);if(row[1]!=0x78145640)continue;check(row[8]&&!row[9]&&row[11]==40&&row[5]==1,"Actual held Lockit native resource40 present");restore_resource=reinterpret_cast<CRITICAL_SECTION*>(row[10]);std::memcpy(resource_before.data(),restore_resource,40);restore_resource->RecursionCount^=1;std::memcpy(resource_after.data(),restore_resource,40);actual_intervention={6,row[10]+12,1,0,40,0,0,0};++mutation_hits;return;}
}
inline void restore_actual(){if(restore_resource){std::memcpy(restore_resource,resource_before.data(),40);restore_resource=nullptr;}}
template<class Runtime>void change(Runtime&r,unsigned address,unsigned value){
 const unsigned page=address&~4095U;const auto old=r.memory().template load<unsigned>({address});
 unsigned permissions=address>=0x78000000?(address==0x7810a290?5:3):1;
 for(const auto&g:r.image_metadata().mapped_regions)if(address>=g.start.value&&std::uint64_t(address)+4<=g.start.value+g.size){permissions=unsigned(g.permissions);break;}
 r.memory().protect({page},mw34::Permissions::read|mw34::Permissions::write);r.memory().template store<unsigned>({address},value);r.memory().protect({page},static_cast<mw34::Permissions>(permissions));actual_intervention={1,address,old,value,page,permissions,r.memory().template load<unsigned>({address}),0};
}
template<class Session>void observe(Session&s,unsigned point){
 if(!selected||hits)return;auto&r=s.runtime();auto*state=reinterpret_cast<State*>(r.remill_state().data());const auto pc=state->gpr.rip.dword;
 const bool after=selected==11||selected==12;
 if(point!=(after?41U:40U)||pc!=0x7810a30b)return;
 ++hits;trigger_point=point;trigger_PC=pc;trigger=snapshot(s);check(trigger.calls.size()==1&&trigger.calls[0][2]==0x411010,"Exact first new root source CALL prefix");
 std::copy(r.remill_state().begin(),r.remill_state().end(),trigger_state.begin());std::copy(r.fx().begin(),r.fx().end(),trigger_fx.begin());std::memcpy(trigger_cpu.data(),&r.cpu(),40);trigger_env=mw34::m4_nmx_integration::view(*state).env;r.memory().read({0x20001000},trigger_stack);
 const auto base=r.fs_base().value;trigger_tib={base,r.memory().template load<unsigned>({base}),r.memory().template load<unsigned>({base+4}),r.memory().template load<unsigned>({base+8}),r.memory().template load<unsigned>({base+0x18})};
 if(!s.fs_witnesses().empty()){trigger_frame=s.fs_witnesses().back();if(trigger_frame[9])r.memory().read({unsigned(trigger_frame[9])},std::as_writable_bytes(std::span(trigger_record)));}
 if(selected<=3){change(r,0x78145658,selected==1?0:selected==2?1:3);return;}
 if(selected==4){change(r,0x78145640,r.memory().template load<unsigned>({0x78145640})^1);return;}
 if(selected==5){change(r,0x5bb4f8,r.memory().template load<unsigned>({0x5bb4f8})^4);return;}
 if(selected==6){change(r,0x78146198,r.memory().template load<unsigned>({0x78146198})^4);return;}
 if(selected==7){change(r,0x7810a290,r.memory().template load<unsigned>({0x7810a290})^1);return;}
 if(selected>=8&&selected<=11){s.dump(&mutate_private,nullptr);check(mutation_hits==1,"One actual Lockit private witness mutation");return;}
 if(selected==12){s.dump(&mutate_actual,nullptr);check(mutation_hits==1&&restore_resource,"One actual native40 mutation before observer guard; restore after refusal before cleanup");return;}
 if(selected==13){r.fx()[0]^=std::byte{1};actual_intervention={4,0,0,1,512,0,0,0};return;}
 if(selected==14){r.memory().protect({0x78145000},mw34::Permissions::read);actual_intervention={2,0x78145000,0,0,0x78145000,1,0,0};return;}
 if(selected==15){const auto address=state->gpr.rsp.dword+4;const auto old=r.memory().template load<unsigned>({address});r.memory().template store<unsigned>({address},old^4);actual_intervention={3,address,old,old^4,state->gpr.rsp.dword,0,r.memory().template load<unsigned>({address}),0};return;}
 throw std::runtime_error("Unknown actual Lockit source control");
}
}
