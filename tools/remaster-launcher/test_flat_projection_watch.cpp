#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <vector>
#include "native-overrides/projection_contract.hpp"
using U=std::uint32_t;
extern "C" U mw34_attach_watch_phi_body(void*,U,void*)noexcept(false);
extern "C" std::uint8_t mw34_attach_watch8_body(void*,U,void*)noexcept(false);
extern "C" std::uint16_t mw34_attach_watch16_body(void*,U,void*)noexcept(false);
extern "C" U mw34_attach_watch32_body(void*,U,void*)noexcept(false);
extern "C" std::uint64_t mw34_attach_watch64_body(void*,U,void*)noexcept(false);
extern "C" float mw34_attach_watchf32_body(void*,U,void*)noexcept(false);
extern "C" double mw34_attach_watchf64_body(void*,U,void*)noexcept(false);
extern "C" void mw34_attach_watch80_body(void*,U,void*)noexcept(false);
extern "C" void fixture_range(void*,void*,U,U,U)noexcept(false);
extern "C" void mw34_attach_watch_store_body(void*,U,void*,U)noexcept(false);
struct Event{U address,size,write;};
static std::vector<Event> events;
static std::vector<unsigned char> memory(0x731000);
static bool dirty=false,range_only=false,rewrite_read=false;
static unsigned expected=0,raw_reads=0,raw_writes=0;
static mw34::projection::Dirty omitted;
template<class T>T get(U a){T v;std::memcpy(&v,memory.data()+a,sizeof(v));return v;}
template<class T>void put(U a,T v){std::memcpy(memory.data()+a,&v,sizeof(v));}
static void require(bool x,const char* why){if(!x)throw std::runtime_error(why);}
extern "C" void mw34_projection_flat_access(void* state,void* token,U a,U size,U write)noexcept(false){
 events.push_back({a,size,write});
 if(range_only)return;
 U pc;std::memcpy(&pc,static_cast<unsigned char*>(state)+4,4);
 require(pc==(write?0x540994U:0x540985U),"Observer did not see the current noalias State PC");
 require(token==memory.data(),"Exact guest token was not forwarded");
 if(!write&&(dirty||omitted.any(a,size)))throw std::runtime_error("Retained dirty scratch read");
 if(!write&&rewrite_read){U v=99;std::memcpy(static_cast<unsigned char*>(token)+a,&v,4);}
 if(write&&size==4&&expected){U v;std::memcpy(&v,static_cast<unsigned char*>(token)+a,4);require(v==expected,"Write observer ran before store");}
 if(write&&size==10)require(raw_writes==1,"Raw80 write observer ran before bridge store");
 if(write)omitted.set(a,size,false);
}
extern "C" void* __remill_read_memory_f80(void* p,U a,void* out){
 require(!events.empty()&&events.back().write==0&&events.back().size==10,"Raw80 read was unobserved");
 std::memcpy(out,static_cast<unsigned char*>(p)+a,10);++raw_reads;return p;
}
extern "C" void* __remill_write_memory_f80(void* p,U a,const void* in){std::memcpy(static_cast<unsigned char*>(p)+a,in,10);++raw_writes;return p;}
int main(){
 try{
  constexpr U low=0x72f41c,high=0x73041c;std::array<U,2> state_words{7,0};auto*state=state_words.data();
  put<U>(0x1000,40);events.clear();expected=0;
  require(mw34_attach_watch_phi_body(state,0x1000,memory.data())==41&&events.empty(),"Outside access called observer");
  // State PC loads/stores remain separate from flat guest access observations.
  require(state_words[1]==0x540994U,"Noalias State store disappeared");
  put<U>(low,40);events.clear();expected=41;
  require(mw34_attach_watch_phi_body(state,low,memory.data())==41,"Guest value changed");
  require(events.size()==2&&events[0].write==0&&events[1].write==1,"Read/write ordering changed");
  rewrite_read=true;expected=100;put<U>(low,40);events.clear();
  require(mw34_attach_watch_phi_body(state,low,memory.data())==100,"Load moved before observer memory effects");rewrite_read=false;
  dirty=true;events.clear();bool caught=false;put<U>(low,40);
  try{mw34_attach_watch_phi_body(state,low,memory.data());}catch(const std::runtime_error&){caught=true;}
  require(caught&&get<U>(low)==40&&events.size()==1,"Observer did not unwind before read/store");dirty=false;expected=0;
  auto width=[&](auto fn,unsigned size){events.clear();fn(state,low,memory.data());require(events.size()==2&&events[0].size==size&&events[1].size==size&&events[0].write==0&&events[1].write==1,"Width observation failed");};
  width(mw34_attach_watch8_body,1);width(mw34_attach_watch16_body,2);width(mw34_attach_watch32_body,4);width(mw34_attach_watch64_body,8);
  width(mw34_attach_watchf32_body,4);width(mw34_attach_watchf64_body,8);width(mw34_attach_watch80_body,10);
  require(raw_reads==1&&raw_writes==1,"Raw80 bridge payload path changed");
  // Exercise the runtime byte tracker through optimized guest loads/stores.
  omitted.prefix(3);events.clear();caught=false;
  try{mw34_attach_watch32_body(state,low,memory.data());}catch(const std::runtime_error&){caught=true;}
  require(caught&&events.size()==1,"Actual omitted-coordinate read escaped watcher");
  mw34_attach_watch_store_body(state,low,memory.data(),123);
  require(!omitted.any(low,4)&&omitted.any(low+4,4),"Flat overwrite did not clear exactly its bytes");
  require(mw34_attach_watch32_body(state,low,memory.data())==123,"Overwritten coordinate stayed dirty");
  caught=false;try{mw34_attach_watch32_body(state,low+4,memory.data());}catch(const std::runtime_error&){caught=true;}
  require(caught,"Partial overwrite cleared adjacent omitted coordinate");
  omitted.set(low,mw34::projection::extent,false);
  range_only=true;
  struct Probe{U address,size;bool observed;};
  for(auto p:std::array<Probe,11>{{{low-4,4,false},{low-3,4,true},{low,1,true},{high-1,1,true},{high,1,false},{high-1,4,true},{low,0,false},{0xfffffffe,8,false},{0,0xffffffff,true},{0,1,false},{high,0xffffffff,false}}}){
   events.clear();fixture_range(state,memory.data(),p.address,p.size,0);require(events.size()==unsigned(p.observed),"Boundary/wrap overlap classification failed");
  }
  std::cout<<"Flat projection watch: widths1/2/4/8/raw80, outside fast path, State exclusion, PHI CFG, read/write ordering, dirty-read unwind and 11 overlap boundaries pass\n";
 }catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 1;}
}
