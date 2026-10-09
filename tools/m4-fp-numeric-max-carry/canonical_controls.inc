// Authored malformed-byte controls. No game or original process is executed.
#pragma pack(push,1)
struct FlagRecord{Record core;std::array<unsigned,16>control;std::array<std::byte,512>runtime_fx_before,runtime_fx_after;};
#pragma pack(pop)
static_assert(sizeof(FlagRecord)==47768);
static void canonical_controls(std::span<const std::byte>game,std::span<const std::byte>provider,const ni::Proof&p,const std::filesystem::path&dir){
 old::Output raw((dir/"canonical-controls.bin").string().c_str());old::Header header{};std::memcpy(header.magic,"MW4NMB01",8);header.version=1;header.count=132;header.stride=sizeof(FlagRecord);header.pages=4;raw.write(header);
 unsigned checks=0,index=0;std::ostringstream rows;
 auto check=[&](bool b,const char*m){++checks;need(b,m);};
 for(unsigned field=0;field<11;++field)for(unsigned bad:{2U,3U,255U})for(unsigned coherent:{0U,1U}){
  old::Tag t{0,0,ni::root,0x37f,field%2?7U:0U,1,0,0,0,0};Fixture f(game,provider,p,t);auto&c=*f.session;const State valid=f.s;
  const std::array<std::uint8_t*,11>flags{&f.s.sw.ie,&f.s.sw.de,&f.s.sw.ze,&f.s.sw.oe,&f.s.sw.ue,&f.s.sw.pe,&f.s.sw.sf,&f.s.sw.c0,&f.s.sw.c1,&f.s.sw.c2,&f.s.sw.c3};*flags[field]=static_cast<std::uint8_t>(bad);
  if(coherent){const auto malformed=ni::view(f.s);std::memcpy(f.r.fx().data(),malformed.fx.data(),512);}
  const unsigned scenario=index/2;ni::Fault first{};unsigned prior_step=0,prior_calls=0;
  for(unsigned retry=0;retry<2;++retry){
   if(retry){f.s=valid;auto v=ni::view(f.s);std::memcpy(f.r.fx().data(),v.fx.data(),512);f.r.cpu()=v.cpu;f.r.cpu().esp+=4;f.r.cpu().eip=0x410a80;f.r.memory().store<unsigned>({old::frame},0x410a80);}
   FlagRecord record{};auto&n=record.core;n.tag=t;n.sequence=scenario;n.phase=retry;n.before=ni::view(f.s);n.memory_before=f.memory();
   std::array<std::byte,512>runtime_before{};std::memcpy(runtime_before.data(),f.r.fx().data(),512);const auto calls_before=f.r.calls().size();
   const std::array<std::uint16_t,3>host_cws{0x7f,0x37f,0xb7f};Host host(host_cws[scenario%3]);const bool actual=c.invoke({ni::root},{0x410a80});host.capture();
   n.after=ni::view(f.s);n.checkpoint=c.checkpoint();n.memory_after=f.memory();n.host_before=host.before.b;n.host_after=host.after.b;n.host_env_before=host.env;n.host_env_after=host.env_after;n.events=c.events();
   const auto calls_after=f.r.calls().size();const auto fault=c.fault();record.runtime_fx_before=runtime_before;std::memcpy(record.runtime_fx_after.data(),f.r.fx().data(),512);const bool state_stable=n.before.state==n.after.state;const bool software_stable=record.runtime_fx_before==record.runtime_fx_after;const bool page_stable=n.memory_before==n.memory_after;
   const bool reason=std::string_view(fault.reason?fault.reason:"")=="Noncanonical FP shadow flag byte rejected";
   if(!retry){first=fault;prior_step=c.step();prior_calls=static_cast<unsigned>(calls_after);}
   const bool first_stable=fault.pc==first.pc&&fault.address==first.address&&fault.step==first.step&&fault.reason==first.reason;
   n.counts={c.step(),unsigned(c.complete()),unsigned(c.failed()),unsigned(f.r.poisoned()),unsigned(calls_after-calls_before),unsigned(ni::owner!=nullptr),unsigned(c.running()),0};
   if(calls_after>calls_before){const auto&v=f.r.calls()[calls_before];n.routes[0]=v.site.value;n.routes[1]=v.target.value;n.routes[2]=v.return_pc.value;n.routes[3]=v.import;n.routes[4]=v.completed;}
   record.control={field,bad,coherent,retry,unsigned(actual),0,fault.pc,fault.address,fault.step,unsigned(reason),unsigned(first_stable),unsigned(calls_before),unsigned(calls_after),unsigned(state_stable),unsigned(software_stable),unsigned(page_stable)};
   check(!actual&&c.failed()&&!c.complete()&&f.r.poisoned(),"Malformed/corrected poisoned invocation refuses completion");
   check(c.step()==0&&fault.pc==ni::root&&fault.address==0&&reason,"Canonical byte guard precedes status projection/guest body and retains exact first fault");
   check(state_stable&&software_stable&&page_stable,"Malformed/corrected poisoned call preserves whole State/softwareFX/pages");
   check(!c.running()&&ni::owner==nullptr,"Canonical denial cleans owner and running scope");
   check(first_stable&&c.step()==prior_step&&(retry?calls_after==prior_calls:calls_after==1),"First error/call/event records unchanged on corrected poison retry");
   raw.write(record);rows<<"{\"field\":"<<field<<",\"value\":"<<bad<<",\"coherent\":"<<coherent<<",\"retry\":"<<retry<<",\"actual\":"<<actual<<",\"step\":"<<c.step()<<",\"fault_pc\":"<<fault.pc<<",\"calls_before\":"<<calls_before<<",\"calls_after\":"<<calls_after<<"}"<<(index==131?"":",");++index;
  }
 }
 check(index==132,"Exact field x value x view coherence x retry schedule");raw.commit();
 const std::string text="{\"passed\":true,\"checks\":"+std::to_string(checks)+",\"malformed_scenarios\":66,\"corrected_poisoned_retries\":66,\"records\":132,\"record_bytes\":47768,\"numerical_host_capture\":\"Direct before/after before harness cleanup\",\"rows\":["+rows.str()+"],\"original_executed\":false}\n";old::Output report((dir/"canonical-controls.json").string().c_str());report.write(text.data(),text.size());report.commit();std::cout<<checks<<" canonical flag admission checks / 132 direct host observations passed\n";
}
