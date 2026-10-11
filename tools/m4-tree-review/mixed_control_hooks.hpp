#pragma once
namespace mw34_tree_controls {
using Q=std::uint64_t;
inline unsigned selected{},hits{},mutations{},point_id{},pc_id{},owner{},generation{},base{},foreign{},header_owner{},sentinel_owner{};
inline std::array<Q,16>intervention{};
inline std::vector<std::pair<std::string,std::vector<std::byte>>>trigger;
inline std::vector<std::byte>private_before,private_after;
inline std::string private_name;
inline std::array<std::byte,40>resource_before{},resource_after{};
inline void restore_actual(){}
inline void collect(std::string_view n,std::span<const std::byte>b,void*){trigger.emplace_back(std::string(n),std::vector<std::byte>(b.begin(),b.end()));}
inline void identity(std::string_view n,std::span<const std::byte>b,void*){
 if(n=="locale-allocations.bin")for(std::size_t p=0;p<b.size();p+=128){std::array<Q,16>r{};std::memcpy(r.data(),b.data()+p,128);if(r[6]==1&&r[8]&&r[9])foreign=unsigned(r[1]);}
 if(n=="mfc-witnesses.bin")for(std::size_t p=0;p<b.size();p+=256){std::array<Q,32>r{};std::memcpy(r.data(),b.data()+p,256);if(r[2]!=0x4e1ca0||!r[21])continue;if(r[4]==0x49cc8d){base=unsigned(r[16]);}if(r[4]==0x4e5325)header_owner=unsigned(r[16]);if(r[4]==0x4e535b)sentinel_owner=unsigned(r[16]);}
}
inline void private_mutation(std::string_view n,std::span<const std::byte>b,void*){
 const auto wanted=selected==6?"fs-owned-accesses.bin":"fs-owned-publications.bin";if(n!=wanted)return;
 need(!b.empty()&&b.size()%128==0,"Actual current mixed private witness");const unsigned at=(selected==6?11:6)*8;need(at<b.size(),"Full genuine mixed generation field");private_name=std::string(n);private_before.assign(b.begin(),b.end());const_cast<std::byte*>(b.data())[at]^=std::byte{1};private_after.assign(b.begin(),b.end());++mutations;intervention={2,at,b.size(),owner,generation,selected,0,0,0,0,0,0,0,0,0,0};
}
template<class Runtime>void change(Runtime&r,unsigned a,unsigned v){
 const unsigned old=r.memory().template load<unsigned>({a});const unsigned page=a&~4095U;unsigned perms=3;
 for(const auto&m:r.image_metadata().mapped_regions)if(a>=m.start.value&&Q(a)+4<=m.start.value+m.size){perms=unsigned(m.permissions);break;}
 r.memory().protect({page},Permissions::read|Permissions::write);r.memory().template store<unsigned>({a},v);r.memory().protect({page},static_cast<Permissions>(perms));intervention={4,a,old,v,4,page,perms,owner,generation,selected,0,0,0,0,0,0};++mutations;
}
template<class Session>void observe(Session&s,unsigned point){
 if(!selected||hits)return;auto&r=s.runtime();auto*state=reinterpret_cast<State*>(r.remill_state().data());const auto pc=state->gpr.rip.dword;
 const unsigned wanted=selected==6?87:86;const unsigned wanted_pc=selected<=2||selected==6?0x49cc95:selected==7?0x4e532a:0x4e5360;
 if(point!=wanted||pc!=wanted_pc)return;
 s.dump(&identity,nullptr);s.dump(&collect,nullptr);
 // Owner/probe comes from the actual current mixed source invocation.
 for(const auto&[n,b]:trigger)if(n=="fs-owned-access-probe.bin"){std::array<Q,16>q{};need(b.size()==128,"Whole current mixed source operand probe");std::memcpy(q.data(),b.data(),128);need(q[2]==0x4e1ca0&&q[3]==pc,"Exact mixed source operand");owner=unsigned(q[10]);generation=unsigned(q[11]);}
 need(owner&&generation&&base,"Measured current mixed owner occurrence");++hits;point_id=point;pc_id=pc;
 trigger.emplace_back("State.bin",std::vector<std::byte>(r.remill_state().begin(),r.remill_state().end()));trigger.emplace_back("FX.bin",std::vector<std::byte>(r.fx().begin(),r.fx().end()));trigger.emplace_back("CPU.bin",std::vector<std::byte>(reinterpret_cast<const std::byte*>(&r.cpu()),reinterpret_cast<const std::byte*>(&r.cpu())+40));
 for(auto a:mw34_tree_fixture::current_pages){std::vector<std::byte>b(4096);r.memory().read({a},b);trigger.emplace_back("whole-page-"+std::to_string(a)+".bin",std::move(b));}
 if(selected<=5){
  const auto old_eax=state->gpr.rax.dword,old_edi=state->gpr.rdi.dword;unsigned address{},value{};
  if(selected==1){need(foreign&&foreign!=owner,"Actual foreign live generic allocation");state->gpr.rax.dword=foreign;address=value=foreign;}
  if(selected==2){state->gpr.rax.dword=owner+12;address=value=owner+12;}
  if(selected==3){need(header_owner&&sentinel_owner&&owner==sentinel_owner,"Actual header/sentinel distinct current roles");state->gpr.rax.dword=header_owner;address=header_owner+4;value=old_edi;}
  if(selected==4){need(header_owner&&sentinel_owner&&old_edi==header_owner,"Actual source parent EDI");state->gpr.rdi.dword=sentinel_owner;address=owner+4;value=sentinel_owner;}
  if(selected==5){state->gpr.rip.dword=0x4e532a;address=owner+4;value=0;}
  intervention={1,address,value,old_eax,old_edi,owner,generation,selected,pc,state->gpr.rip.dword,4,header_owner,sentinel_owner,foreign,0,0};++mutations;
  (void)m4_onexit::write(s.token(),address,value,4);throw std::runtime_error("Unexpected admitted mixed source operand counterfactual");
 }
 if(selected==6||selected==7){s.dump(&private_mutation,nullptr);need(mutations==1,"Exactly one actual mixed private field bit");return;}
 if(selected==8){change(r,0x5bb4f4,r.memory().template load<unsigned>({0x5bb4f4})^4);return;}
 if(selected==9){const unsigned head=r.memory().template load<unsigned>({r.fs_base().value});need(head!=m4_runtime::Runtime::seh_end,"Actual active source FS record");change(r,head+4,r.memory().template load<unsigned>({head+4})^1);return;}
 throw std::runtime_error("Unknown mixed control scenario");
}
inline void reset(unsigned n){selected=n;hits=mutations=point_id=pc_id=owner=generation=base=foreign=header_owner=sentinel_owner=0;intervention={};trigger.clear();private_before.clear();private_after.clear();private_name.clear();resource_before={};resource_after={};}
}
