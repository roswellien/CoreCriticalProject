struct InitermBinding{
 nt::Context context;unsigned control{};std::array<std::byte,4096>table{},provider_page{};
 void(*extra_before)(nt::Context&,unsigned){};void(*extra_access)(nt::Context&,unsigned){};void(*extra_event)(nt::Context&,unsigned){};void(*extra_after)(nt::Context&){};
 InitermBinding(Runtime&r,std::span<const std::byte>image,std::span<const std::byte>provider,unsigned mode):context(r),control(mode){
  r.memory().read({0x5e0000},table);require(std::equal(table.begin(),table.end(),image.begin()+1961472),"Already admitted complete literal game table page; no remap");r.memory().read({0x78001000},provider_page);
 }
};
thread_local InitermBinding*initterm_binding{};
void initterm_checkpoint(Runtime&,const char*);
void initterm_before(nt::Context&c,unsigned pc){
 require(initterm_binding&& &initterm_binding->context==&c,"Exact initterm observation owner");
 if(pc==nt::entry){initterm_checkpoint(c.runtime,"initterm-projected");const auto mode=initterm_binding->control;if(mode==41)c.runtime.memory().store<unsigned>({nt::begin},0x51e7b0);if(mode==42)c.runtime.memory().protect({0x20001000},Permissions::read);if(mode==46)throw std::runtime_error("Authored initterm observer exception");}
 else initterm_checkpoint(c.runtime,"initterm-thunk-projected");
 if(initterm_binding->extra_before)initterm_binding->extra_before(c,pc);
}
void initterm_access(nt::Context&c,unsigned count){
 require(initterm_binding&& &initterm_binding->context==&c,"Exact initterm access observer");const auto&v=c.accesses[count-1];const auto mode=initterm_binding->control;
 if(mode==43&&v.pc==0x780014f9)c.state.gpr.rsp.dword=0x20001ffc;
 if(mode==44&&v.pc==0x78001512)c.runtime.memory().store<unsigned>({c.frame},c.ret^1);
 if(mode==45&&v.pc==0x78001513)c.state.gpr.rsi.dword^=1;
 if(mode==48&&v.pc==0x78001502&&c.provider_step==3)c.runtime.memory().store<unsigned>({c.frame+8},nt::end+4);
 if(initterm_binding->extra_access)initterm_binding->extra_access(c,count);
}
void initterm_event(nt::Context&c,unsigned count){if(initterm_binding->extra_event)initterm_binding->extra_event(c,count);}
} // enclosing composition's anonymous namespace
namespace mw34::m4_crt_entry_initerm {
void Context::tail(State*s,unsigned target){
 guard();if(s!=&state||target!=raw||state.gpr.rip.dword!=target||runtime.memory().load<unsigned>({slot})!=raw||state.gpr.rsp.dword!=frame||runtime.memory().load<unsigned>({frame})!=ret)deny("Actual initterm import tail/raw IAT/frame rejected");
 source_identity();event(2,target,frame,ret);runtime.cpu()=m4_crt_control_integration::cpu_view(state);runtime.cpu().esp=frame+4;runtime.cpu().eip=thunk;
 bool bad{};try{runtime.call_import({slot},{ret});}catch(...){bad=true;}if(bad)deny("Required actual initterm provider route fault",slot);
 if(!provider_complete||runtime.cpu().eip!=ret||runtime.cpu().esp!=frame+4||state.gpr.rip.dword!=ret||state.gpr.rsp.dword!=frame+4)deny("Actual initterm typed tail closure");event(6,ret,frame+4,ret);
}
}
namespace {
void initterm_provider_adapter(Runtime&r){
 require(initterm_binding&&nt::owner==&initterm_binding->context&& &nt::owner->runtime==&r&&!ci::owner&&!mn::owner,"Exact nested initterm provider owner");auto&b=*initterm_binding;auto&c=b.context;
 initterm_checkpoint(r,"initterm-before");
 try{
  c.source_identity();std::array<std::byte,4096>table{},page{};r.memory().read({0x5e0000},table);r.memory().read({0x78001000},page);require(table==b.table&&page==b.provider_page,"Literal initterm owned source table and provider page intact");
  require(r.cpu().esp==c.frame&&r.cpu().eip==nt::slot&&r.memory().load<unsigned>({c.frame})==nt::return_pc,"Actual initterm imported call frame");
  project(c.state,r.cpu());c.state.gpr.rip.dword=nt::entry;++c.boundary_depth;
  try{if(c.test_before_execute)c.test_before_execute(c,nt::entry);c.event(3,nt::entry,c.frame,c.ret);auto*p=nt::sub_780014f8(&c.state,nt::entry,&c);require(p==&c&&c.provider_complete,"Actual provider compiled token and RET closure");}
  catch(const nt::BridgeAbort&){--c.boundary_depth;throw std::runtime_error(c.reason?c.reason:"Required compiled initterm fault");}
  catch(...){--c.boundary_depth;throw;}--c.boundary_depth;r.cpu()=cpu(c.state);initterm_checkpoint(r,"initterm-after");
 }catch(...){initterm_checkpoint(r,"initterm-after");throw;}
}
void initterm_thunk_adapter(Runtime&r){
 require(initterm_binding&& &initterm_binding->context.runtime==&r&&!nt::owner&&!ci::owner&&!mn::owner,"Exact exclusive initterm thunk owner");auto&c=initterm_binding->context;
 initterm_checkpoint(r,"initterm-thunk-before");
 project(c.state,r.cpu());c.frame=r.cpu().esp;c.ret=r.memory().load<unsigned>({c.frame});c.first=r.memory().load<unsigned>({c.frame+4});c.last=r.memory().load<unsigned>({c.frame+8});c.nonvolatile=c.nonvol();c.used=true;
 c.test_before_execute=&initterm_before;c.test_after_access=&initterm_access;c.test_after_event=&initterm_event;nt::owner=&c;c.active=true;++c.boundary_depth;
 try{
  require(c.ret==nt::return_pc&&c.first==nt::begin&&c.last==nt::end,"Only exact actual first initterm interval/frame admitted");c.source_identity();if(c.test_before_execute)c.test_before_execute(c,nt::thunk);auto*p=nt::sub_5ac598(&c.state,nt::thunk,&c);require(p==&c&&c.provider_complete,"Actual thunk and provider token completed");
  c.complete=true;--c.boundary_depth;c.active=false;r.cpu()=cpu(c.state);if(initterm_binding->extra_after)initterm_binding->extra_after(c);initterm_checkpoint(r,"initterm-thunk-after");nt::owner=nullptr;
 }catch(const nt::BridgeAbort&){if(c.boundary_depth)--c.boundary_depth;c.active=false;nt::owner=nullptr;initterm_checkpoint(r,"initterm-thunk-after");throw std::runtime_error(c.reason?c.reason:"Required compiled initterm fault");}
 catch(...){if(c.boundary_depth)--c.boundary_depth;c.active=false;nt::owner=nullptr;initterm_checkpoint(r,"initterm-thunk-after");throw;}
}
