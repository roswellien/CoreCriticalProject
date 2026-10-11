#pragma once
namespace mw34_tree_controls {
using Q=std::uint64_t;
inline unsigned selected{},hits{},mutations{},point_id{},pc_id{};
inline std::array<Q,16>intervention{};
inline std::vector<std::pair<std::string,std::vector<std::byte>>>trigger;
inline std::vector<std::byte>private_before,private_after;
inline std::string private_name;
inline CRITICAL_SECTION*restore_resource{};
inline std::array<std::byte,40>resource_before{},resource_after{};
inline void collect(std::string_view n,std::span<const std::byte>b,void*){trigger.emplace_back(std::string(n),std::vector<std::byte>(b.begin(),b.end()));}
inline void mutate_private(std::string_view n,std::span<const std::byte>b,void*){
 const char*wanted=selected==5?"tree-lockit-held.bin":selected==6?"tree-lockit-contexts.bin":selected==7?"fs-active-records.bin":selected==8?"fs-owned-access-probe.bin":selected==9?"fs-owned-publications.bin":"lockit-imports.bin";
 if(n!=wanted)return;need(!b.empty(),"Live direct private vector to mutate");private_name=std::string(n);private_before.assign(b.begin(),b.end());
 const unsigned offset=selected==5?2*8:selected==6?7*8:selected==7?0:selected==8?11*8:selected==9?6*8:4*8;
 need(offset<b.size(),"Exact actual private mutation offset");const_cast<std::byte*>(b.data())[offset]^=std::byte{1};private_after.assign(b.begin(),b.end());++mutations;
 intervention={2,offset,b.size(),0,0,0,0,0,0,0,0,0,0,0,0,0};
}
inline void mutate_actual(std::string_view n,std::span<const std::byte>b,void*){
 if(n!="locale-critical-sections.bin")return;
 for(std::size_t k=0;k<b.size();k+=128){std::array<Q,16>r{};std::memcpy(r.data(),b.data()+k,128);if(r[1]!=0x78145640)continue;
  need(r[5]&&r[8]&&!r[9]&&r[11]==40,"Held actual native40 resource");restore_resource=reinterpret_cast<CRITICAL_SECTION*>(r[10]);std::memcpy(resource_before.data(),restore_resource,40);restore_resource->RecursionCount^=1;std::memcpy(resource_after.data(),restore_resource,40);intervention={3,r[10]+12,40,r[5],0,0,0,0,0,0,0,0,0,0,0,0};++mutations;return;}
}
inline void restore_actual(){if(restore_resource){std::memcpy(restore_resource,resource_before.data(),40);restore_resource=nullptr;}}
template<class Runtime>void change(Runtime&r,unsigned a,unsigned v){
 const auto page=a&~4095U,old=r.memory().template load<unsigned>({a});unsigned perms=a>=0x78000000?(a==0x7810a290?5:3):1;
 for(const auto&g:r.image_metadata().mapped_regions)if(a>=g.start.value&&Q(a)+4<=g.start.value+g.size){perms=unsigned(g.permissions);break;}
 r.memory().protect({page},Permissions::read|Permissions::write);r.memory().template store<unsigned>({a},v);r.memory().protect({page},static_cast<Permissions>(perms));intervention={4,a,old,v,page,perms,r.memory().template load<unsigned>({a}),0,0,0,0,0,0,0,0,0};++mutations;
}
inline unsigned foreign_alias{};
inline void find_foreign(std::string_view n,std::span<const std::byte>b,void*){if(n!="locale-allocations.bin")return;for(std::size_t k=0;k<b.size();k+=128){std::array<Q,16>r{};std::memcpy(r.data(),b.data()+k,128);if(r[6]==1&&r[8]&&r[9])foreign_alias=unsigned(r[1]);}}
template<class Session>void observe(Session&s,unsigned point){
 if(!selected||hits)return;auto&r=s.runtime();auto*state=reinterpret_cast<State*>(r.remill_state().data());const auto pc=state->gpr.rip.dword;
 const bool owner=selected<=4||selected==8||selected==9||selected==17;
 if(owner){if(point!=86||pc!=0x4bab44)return;if(selected==4&&s.mfc_witnesses().size()<4)return;if(selected==9&&s.mfc_witnesses().size()<4)return;}
 else if(point!=(selected==15?41U:40U)||pc!=0x7810a30b)return;
 if(selected==5){bool live{};s.dump(+[](std::string_view n,std::span<const std::byte>b,void*p){if(n=="tree-lockit-held.bin")*static_cast<bool*>(p)=!b.empty();},&live);if(!live)return;}
 ++hits;point_id=point;pc_id=pc;s.dump(&collect,nullptr);
 trigger.emplace_back("State.bin",std::vector<std::byte>(r.remill_state().begin(),r.remill_state().end()));trigger.emplace_back("FX.bin",std::vector<std::byte>(r.fx().begin(),r.fx().end()));trigger.emplace_back("CPU.bin",std::vector<std::byte>(reinterpret_cast<const std::byte*>(&r.cpu()),reinterpret_cast<const std::byte*>(&r.cpu())+40));
 for(auto a:mw34_tree_fixture::current_pages){std::vector<std::byte>b(4096);r.memory().read({a},b);trigger.emplace_back("whole-page-"+std::to_string(a)+".bin",std::move(b));}
 if(selected<=4){
  const auto old=state->gpr.rdi.dword;unsigned next{};
  if(selected==1){s.dump(&find_foreign,nullptr);need(foreign_alias,"Actual positive registry foreign owner");next=foreign_alias;}
  if(selected==2)next=old+20; // [EDI+4] reaches requested offset24, still inside capacity32.
  if(selected==3)next=r.memory().template load<unsigned>({0x60b314});
  if(selected==4){auto rows=s.mfc_witnesses();need(rows.size()>=4,"Two genuine repeated node occurrences");next=unsigned(rows[2][16]);}
  const auto a=next+4,before=r.memory().template load<unsigned>({a});intervention={1,old,next,a,before,state->gpr.rax.dword,4,pc,selected,0,0,0,0,0,0,0};++mutations;state->gpr.rdi.dword=next;
  // Public source memory service, using its actual current decoded operand.
  // Exact owner admission must refuse before this candidate store can commit.
  (void)m4_onexit::write(s.token(),a,state->gpr.rax.dword,4);throw std::runtime_error("Unexpected admitted counterfactual owner store");
 }
 if(selected>=5&&selected<=10){s.dump(&mutate_private,nullptr);need(mutations==1,"One actual direct private mutation");return;}
 if(selected==11){change(r,0x5bb4f8,r.memory().template load<unsigned>({0x5bb4f8})^4);return;}
 if(selected==12){change(r,0x7810a290,r.memory().template load<unsigned>({0x7810a290})^1);return;}
 if(selected==13){r.fx()[0]^=std::byte{1};intervention={5,0,512,0,0,0,0,0,0,0,0,0,0,0,0,0};++mutations;return;}
 if(selected==14){change(r,0x78145658,1);return;}
 if(selected==15){s.dump(&mutate_actual,nullptr);need(mutations==1&&restore_resource,"Actual resource mutation retained before refusal");return;}
 if(selected==16){change(r,0x78146198,r.memory().template load<unsigned>({0x78146198})^4);return;}
 if(selected==17){const auto probe=s.fs_owner_probe();const auto page=unsigned(probe[4])&~4095U;r.memory().protect({page},Permissions::read);intervention={6,page,1,probe[4],0,0,0,0,0,0,0,0,0,0,0,0};++mutations;return;}
 throw std::runtime_error("Unknown tree control");
}
inline void reset(unsigned n){selected=n;hits=mutations=point_id=pc_id=foreign_alias=0;intervention={};trigger.clear();private_before.clear();private_after.clear();private_name.clear();resource_before={};resource_after={};restore_resource=nullptr;}
}
