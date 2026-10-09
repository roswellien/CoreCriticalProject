#pragma once
#include "protocol.hpp"
#include "memory/guest_memory.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <thread>
#include <csetjmp>
extern "C" void *mw34_setter_entry(State*,std::uint32_t,void*);
extern "C" void *mw34_consumer_entry(State*,std::uint32_t,void*);
namespace mw34::m3_subsystem {
class Context{
 using Entry=void*(*)(State*,std::uint32_t,void*);Entry set_fn{},consumer_fn{};bool frozen{},active{},escape_ready{};std::thread::id owner;std::jmp_buf escape;
 std::uint32_t pc{},frame{};
 void fault(){failed=true;if(active&&escape_ready&&owner==std::this_thread::get_id())std::longjmp(escape,1);}
 bool admitted(){if(!active||failed||owner!=std::this_thread::get_id()){fault();return false;}return true;}
 bool stack_span(std::uint32_t a,unsigned w)const{const auto start=pc==setter?frame:frame-24;const auto end=pc==setter?std::uint64_t{frame}+12:std::uint64_t{frame}+4;return a>=start&&std::uint64_t{a}+w<=end;}
 bool buffer_span(std::uint32_t a,unsigned w)const{return a>=buffer_base&&std::uint64_t{a}+w<=buffer_base+8192;}
 bool global_span(std::uint32_t a,unsigned w)const{return w==4&&a>=global_base+0x1e4&&a<global_base+0x1f8&&(a-(global_base+0x1e4))%4==0;}
 void log(std::uint32_t a,std::uint32_t v,unsigned w,bool write){if(trace_count==max_events){fault();return;}events[trace_count++]={a,v,w,write?1U:0U};}
 public:
 mw34::GuestMemory memory;bool failed{},complete{};std::uint32_t returns{},trace_count{},selected_setter{},selected_consumer{};std::array<Event,max_events>events{};
 Context(const Request&q,const std::array<std::vector<std::uint8_t>,2>&codes){validate_request(q);require(codes[0].size()==43&&sha256(codes[0])==setter_hash&&codes[1].size()==119&&sha256(codes[1])==consumer_hash,"Context exact code identities failed");
  for(unsigned i=0;i<2;++i){const auto page=i?0x55a000U:0x558000U,at=i?consumer:setter;memory.map({page},4096,mw34::Permissions::read|mw34::Permissions::write);memory.write({at},std::as_bytes(std::span{codes[i]}));memory.protect({page},mw34::Permissions::read|mw34::Permissions::execute);}
  memory.map({stack_base},4096,mw34::Permissions::read|mw34::Permissions::write);memory.map({global_base},4096,mw34::Permissions::read|mw34::Permissions::write);memory.map({buffer_base},8192,mw34::Permissions::read|mw34::Permissions::write);
  const auto b=initial_memory(q);memory.write({stack_base},std::as_bytes(std::span{b.data(),4096}));memory.write({global_base},std::as_bytes(std::span{b.data()+4096,4096}));memory.write({buffer_base},std::as_bytes(std::span{b.data()+8192,8192}));
 }
 void select(Entry a,Entry b){require(!frozen&&!set_fn&&!consumer_fn&&a==&mw34_setter_entry&&b==&mw34_consumer_entry,"Frozen/conflicting/unadmitted selection");set_fn=a;consumer_fn=b;}
 void freeze(std::string_view image){require(!frozen&&set_fn&&consumer_fn&&image==image_hash,"Incomplete/frozen/wrong-image registry");frozen=true;}
 void prepare(const Step&s){require(frozen&&!active&&!failed,"Unfrozen/active/faulted caller preparation");validate_step(s);const std::uint32_t data[]{sentinel,s.arg_a,s.arg_b};memory.write({s.state.registers[4]},std::as_bytes(std::span{data,s.state.eip==setter?3U:1U}));}
 void*enter(State&s,std::uint32_t target){require(frozen&&!active&&!failed&&(target==setter||target==consumer)&&s.gpr.rip.dword==target,"Unfrozen/reentrant/faulted/wrong entry route");
  pc=target;frame=s.gpr.rsp.dword;active=true;owner=std::this_thread::get_id();returns=trace_count=0;complete=false;events.fill({});
  // Failure-only nonlocal exit crosses the pure LLVM body, never a live C++
  // bridge object/catch. The caller's FpuScope remains outside this region.
  void*token=this;escape_ready=true;
  if(setjmp(escape)==0)token=(target==setter?set_fn:consumer_fn)(&s,target,this);
  else token=this;
  escape_ready=false;if(target==setter)++selected_setter;else ++selected_consumer;active=false;
  if(token!=this||failed||!complete||returns!=1)failed=true;
  if(target==setter&&trace_count!=8)failed=true;return token;
 }
 template<unsigned Width>std::uint32_t read(std::uint32_t a){if(!admitted())return 0;
  if constexpr(Width==2){if(pc!=consumer||!buffer_span(a,2)){fault();return 0;}}
  else if(!stack_span(a,4)||(pc==setter&&a!=frame&&a!=frame+4&&a!=frame+8)){if(pc!=consumer||!global_span(a,4)){fault();return 0;}}
  if(trace_count==max_events){fault();return 0;}std::uint32_t value{};bool ok{};
  try{value=Width==2?memory.load<std::uint16_t>({a}):memory.load<std::uint32_t>({a});ok=true;}catch(const std::exception&){}
  if(!ok){fault();return 0;}log(a,value,Width,false);return value;
 }
 template<unsigned Width>void write(std::uint32_t a,std::uint32_t v){if(!admitted())return;
  if constexpr(Width==2){if(pc!=consumer||!buffer_span(a,2)){fault();return;}}
  else if(pc==setter?!global_span(a,4):(!stack_span(a,4)||a>=frame||(frame-a)%4)){fault();return;}
  if(trace_count==max_events){fault();return;}bool ok{};
  try{if constexpr(Width==2)memory.store<std::uint16_t>({a},static_cast<std::uint16_t>(v));else memory.store<std::uint32_t>({a},v);ok=true;}catch(const std::exception&){}
  if(!ok){fault();return;}log(a,Width==2?v&0xffff:v,Width,true);
 }
 void*returned(State&s,std::uint32_t target){if(!admitted())return this;const auto cleanup=pc==setter?12:4;if(returns||target!=sentinel||s.gpr.rip.dword!=sentinel||std::uint64_t{frame}+cleanup!=s.gpr.rsp.dword){fault();return this;}++returns;complete=true;return this;}
 void capture(std::array<std::uint8_t,memory_size>&b)const{memory.read({stack_base},std::as_writable_bytes(std::span{b.data(),4096}));memory.read({global_base},std::as_writable_bytes(std::span{b.data()+4096,4096}));memory.read({buffer_base},std::as_writable_bytes(std::span{b.data()+8192,8192}));}
};
}
