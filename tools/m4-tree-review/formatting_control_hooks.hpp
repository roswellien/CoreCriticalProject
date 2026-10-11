#pragma once
namespace mw34_tree_controls {
using Q=std::uint64_t;
inline unsigned selected{},hits{},mutations{},point_id{},pc_id{},owner{},generation{},base{};
inline std::array<Q,16>intervention{};
inline std::vector<std::pair<std::string,std::vector<std::byte>>>trigger;
inline std::vector<std::byte>private_before,private_after;
inline std::string private_name;
inline std::array<std::byte,40>resource_before{},resource_after{};
inline void restore_actual(){}
inline void collect(std::string_view n,std::span<const std::byte>b,void*){trigger.emplace_back(std::string(n),std::vector<std::byte>(b.begin(),b.end()));}
inline void status(std::string_view n,std::span<const std::byte>b,void*){if(n=="formatting-status.bin"){std::array<unsigned,10>r{};need(b.size()==40,"Current exact formatter status");std::memcpy(r.data(),b.data(),40);base=r[3];owner=r[4];generation=r[5];}}
inline unsigned foreign{};
inline void foreign_owner(std::string_view n,std::span<const std::byte>b,void*){if(n!="locale-allocations.bin")return;for(std::size_t p=0;p<b.size();p+=128){std::array<Q,16>r{};std::memcpy(r.data(),b.data()+p,128);if(r[1]!=owner&&r[6]==1&&r[8]&&r[9])foreign=unsigned(r[1]);}}
inline void private_mutation(std::string_view n,std::span<const std::byte>b,void*){
 const char*wanted=selected==5?"formatting-calls.bin":selected==6?"formatting-owned.bin":selected==7?"formatting-publications.bin":"formatting-dispatches.bin";
 if(n!=wanted)return;need(!b.empty(),"Actual live formatter private vector");private_name=std::string(n);private_before.assign(b.begin(),b.end());
 const unsigned at=selected==5?13*8:selected==6?9*8:selected==7?5*8:6*8;need(at<b.size(),"Actual current typed formatter private field");
 const_cast<std::byte*>(b.data())[at]^=std::byte{1};private_after.assign(b.begin(),b.end());++mutations;intervention={2,at,b.size(),owner,generation,selected,0,0,0,0,0,0,0,0,0,0};
}
template<class Runtime>void change(Runtime&r,unsigned a,unsigned v,unsigned width=4){
 const auto page=a&~4095U;unsigned perms=3;for(const auto&g:r.image_metadata().mapped_regions)if(a>=g.start.value&&Q(a)+width<=g.start.value+g.size){perms=unsigned(g.permissions);break;}
 const auto old=width==1?r.memory().template load<unsigned char>({a}):r.memory().template load<unsigned>({a});r.memory().protect({page},Permissions::read|Permissions::write);
 if(width==1)r.memory().template store<unsigned char>({a},v);else r.memory().template store<unsigned>({a},v);r.memory().protect({page},static_cast<Permissions>(perms));
 intervention={4,a,old,v,width,page,perms,owner,generation,0,0,0,0,0,0,0};++mutations;
}
template<class Session>void observe(Session&s,unsigned point){
 if(!selected||hits)return;auto&r=s.runtime();auto*state=reinterpret_cast<State*>(r.remill_state().data());const auto pc=state->gpr.rip.dword;
 const unsigned wanted=(selected<=4||selected==6||selected==11)?90:(selected==8||selected==9)?89:88;
 if(point!=wanted)return;if(point==90&&pc!=0x7801042a)return;if(point==89&&pc!=0x7800fcef)return;
 s.dump(&status,nullptr);need(owner&&generation&&base,"Actual active first formatter allocation");++hits;point_id=point;pc_id=pc;
 s.dump(&collect,nullptr);trigger.emplace_back("State.bin",std::vector<std::byte>(r.remill_state().begin(),r.remill_state().end()));trigger.emplace_back("FX.bin",std::vector<std::byte>(r.fx().begin(),r.fx().end()));
 trigger.emplace_back("CPU.bin",std::vector<std::byte>(reinterpret_cast<const std::byte*>(&r.cpu()),reinterpret_cast<const std::byte*>(&r.cpu())+40));
 for(auto a:mw34_tree_fixture::current_pages){std::vector<std::byte>b(4096);r.memory().read({a},b);trigger.emplace_back("whole-page-"+std::to_string(a)+".bin",std::move(b));}
 if(selected<=4){
  unsigned address{};const auto old=state->gpr.rdx.dword;const auto prior_eax=state->gpr.rax.dword;unsigned value=prior_eax&255;
  if(selected==1){s.dump(&foreign_owner,nullptr);need(foreign,"Actual live foreign registry allocation");address=foreign;}
  if(selected==2)address=owner+8; // First source request is8, actual capacity16.
  if(selected==3)address=owner+4096; // Actual unmapped successor, not a fabricated allocation.
  if(selected==4){address=owner+1;value^=0x80;state->gpr.rax.dword=(prior_eax&~255U)|value;}
  state->gpr.rdx.dword=address;intervention={1,old,address,value,prior_eax,owner,generation,selected,pc,1,0,0,0,0,0,0};++mutations;
  (void)m4_onexit::write(s.token(),address,value,1);throw std::runtime_error("Unexpected admitted formatter counterfactual source byte");
 }
 if(selected>=5&&selected<=8){s.dump(&private_mutation,nullptr);need(mutations==1,"Exactly one actual private formatter vector mutation");return;}
 if(selected==9){const auto old=state->gpr.rax.dword;state->gpr.rax.dword=2;const auto address=0x780103fa+8;intervention={7,old,2,address,pc,owner,generation,0,0,0,0,0,0,0,0,0};++mutations;(void)m4_onexit::read(s.token(),address,4);throw std::runtime_error("Unexpected admitted formatter table branch");}
 if(selected==10){change(r,0x5bb658,r.memory().template load<unsigned>({0x5bb658})^4);return;}
 if(selected==11){r.memory().protect({owner&~4095U},Permissions::read);intervention={6,owner&~4095U,owner,generation,0,0,0,0,0,0,0,0,0,0,0,0};++mutations;return;}
 if(selected==12){r.fx()[0]^=std::byte{1};intervention={5,0,512,owner,generation,0,0,0,0,0,0,0,0,0,0,0};++mutations;return;}
 if(selected==13){change(r,base-8,r.memory().template load<unsigned>({base-8})^1);return;}
 throw std::runtime_error("Unknown formatter control scenario");
}
inline void reset(unsigned n){selected=n;hits=mutations=point_id=pc_id=owner=generation=base=foreign=0;intervention={};trigger.clear();private_before.clear();private_after.clear();private_name.clear();resource_before={};resource_after={};}
}
