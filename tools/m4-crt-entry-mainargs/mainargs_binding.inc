struct MainargsBinding{
 mg::Context context;unsigned control{};
 void(*extra_before)(mg::Context&,unsigned){};void(*extra_access)(mg::Context&,unsigned){};void(*extra_event)(mg::Context&,unsigned){};void(*extra_after)(mg::Context&){};
 MainargsBinding(Runtime&r,std::span<const std::byte>provider,unsigned mode):context(r,provider),control(mode){}
};
thread_local MainargsBinding*mainargs_binding{};
void mainargs_checkpoint(Runtime&,const char*);
extern "C" unsigned __remill_read_memory_32(void*,unsigned) noexcept(false);
void mainargs_change(mg::Context&c,unsigned address,unsigned value){const auto page=address&~4095U;c.runtime.memory().protect({page},Permissions::read|Permissions::write);c.runtime.memory().store<unsigned>({address},value);if(page==0x7800b000)c.runtime.memory().protect({page},Permissions::read|Permissions::execute);}
void mainargs_before(mg::Context&c,unsigned target){require(mainargs_binding&& &mainargs_binding->context==&c,"Exact mainargs projected observer owner");mainargs_checkpoint(c.runtime,target==mg::entry?"mainargs-projected":"mainargs-builder-projected");const auto mode=mainargs_binding->control;
 if(target==mg::entry){if(mode==49)mainargs_change(c,mg::entry,0);if(mode==51)mainargs_change(c,mg::slot,c.raw^1);if(mode==53)c.runtime.memory().protect({0x78037000},Permissions::read);if(mode==54)c.runtime.memory().protect({0x20001000},Permissions::read);if(mode==56)c.runtime.memory().store<unsigned>({c.startup_ptr},0x13579bdf);if(mode==57)c.runtime.memory().store<unsigned>({c.frame+16},1);if(mode==59)throw std::runtime_error("Authored mainargs projected observer exception");}
 else{if(mode==50)mainargs_change(c,mg::builder,0);if(mode==52)mainargs_change(c,mg::import_slot,c.provider_raw^1);if(mode==58)(void)__remill_read_memory_32(&c.runtime,mg::import_slot);if(mode==60)c.runtime.memory().protect({0x20001000},Permissions::read);}
 if(mainargs_binding->extra_before)mainargs_binding->extra_before(c,target);
}
void mainargs_access(mg::Context&c,unsigned count){require(mainargs_binding&& &mainargs_binding->context==&c,"Exact mainargs access observer owner");if(mainargs_binding->control==55&&count==6&&c.accesses[count-1].pc==mg::internal_call)c.runtime.memory().store<unsigned>({c.frame-8},mg::internal_return^1);if(mainargs_binding->extra_access)mainargs_binding->extra_access(c,count);}
void mainargs_event(mg::Context&c,unsigned count){require(mainargs_binding&& &mainargs_binding->context==&c,"Exact mainargs route observer owner");if(mainargs_binding->extra_event)mainargs_binding->extra_event(c,count);}
} // enclosing composition anonymous namespace
namespace mw34::m4_crt_entry_mainargs {
void Context::nested(State*s,unsigned target,void*p){guard();if(p!=this||s!=&state||target!=builder||stage!=1||state.gpr.rip.dword!=builder||state.gpr.rsp.dword!=frame-8||access_count!=6||accesses[5].pc!=internal_call||accesses[5].address!=frame-8||accesses[5].value!=internal_return||!accesses[5].write||runtime.memory().load<unsigned>({frame-8})!=internal_return)deny("Actual mainargs E8 internal return frame rejected",frame-8,internal_call);
 event(2,internal_call,builder,internal_return);mainargs_checkpoint(runtime,"mainargs-builder-before");stage=2;++boundary_depth;
 try{if(test_before_execute)test_before_execute(*this,builder);source_identity();event(3,builder,frame-8,internal_return);(void)mw34_mainargs_normal_argv_body(&state,builder,this);deny("Unexpected complete ordinary argv builder return",builder);}
 catch(...){--boundary_depth;mainargs_checkpoint(runtime,"mainargs-builder-after");throw;}
}
}
namespace {
void mainargs_adapter(Runtime&r){require(mainargs_binding&& &mainargs_binding->context.runtime==&r&&!mg::owner&&!nt::owner&&!ci::owner&&!mn::owner,"Exact exclusive mainargs service owner");auto&c=mainargs_binding->context;
 mainargs_checkpoint(r,"mainargs-before");project(c.state,r.cpu());c.frame=r.cpu().esp;c.ret=r.memory().load<unsigned>({c.frame});c.argc_ptr=r.memory().load<unsigned>({c.frame+4});c.argv_ptr=r.memory().load<unsigned>({c.frame+8});c.env_ptr=r.memory().load<unsigned>({c.frame+12});c.wildcard=r.memory().load<unsigned>({c.frame+16});c.startup_ptr=r.memory().load<unsigned>({c.frame+20});c.startup_value=r.memory().load<unsigned>({c.startup_ptr});c.loaded_startup=c.startup_value;c.nonvolatile={c.state.gpr.rbx.dword,c.state.gpr.rbp.dword,c.state.gpr.rsi.dword,c.state.gpr.rdi.dword};c.used=true;c.active=true;c.stage=1;c.boundary_depth=1;mg::owner=&c;c.state.gpr.rip.dword=mg::entry;c.test_before_execute=&mainargs_before;c.test_after_access=&mainargs_access;c.test_after_event=&mainargs_event;
 try{require(r.cpu().eip==mg::slot&&c.frame==0x20001860&&c.ret==mg::return_pc&&c.argc_ptr==0x2000189c&&c.argv_ptr==0x2000188c&&c.env_ptr==0x20001898&&c.wildcard==0&&c.startup_ptr==0x20001890&&c.startup_value==0,"Exact actual zero wildcard/startupinfo mainargs frame");if(c.test_before_execute)c.test_before_execute(c,mg::entry);c.source_identity();c.event(1,mg::entry,c.frame,c.ret);(void)mg::mw34_mainargs_mainargs_body(&c.state,mg::entry,&c);c.deny("Unexpected complete __getmainargs return",mg::entry);}
 catch(const mg::BridgeAbort&){c.active=false;c.boundary_depth=0;mg::owner=nullptr;if(mainargs_binding->extra_after)mainargs_binding->extra_after(c);mainargs_checkpoint(r,"mainargs-after");throw std::runtime_error(c.reason?c.reason:"Required compiled mainargs fault");}
 catch(...){c.first("Required mainargs observer or host fault");c.active=false;c.boundary_depth=0;mg::owner=nullptr;if(mainargs_binding->extra_after)mainargs_binding->extra_after(c);mainargs_checkpoint(r,"mainargs-after");throw;}
}
