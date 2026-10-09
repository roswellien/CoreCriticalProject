} // composition anonymous namespace
namespace mw34::m4_crt_locale_default {
namespace {thread_local Binding*authority{};}
bool has_authority()noexcept{return authority!=nullptr;}
extern "C" unsigned __remill_read_memory_32(void*,unsigned)noexcept(false);
Binding::Binding(mg::Context&c,std::span<const std::byte>provider,unsigned mode):runtime(c.runtime),state(c.state),parent(&c),control(mode),admitted_parent_(&c),admitted_control_(mode){
 m4_cmd_native::Provider p(provider);source_[0]=p.slice({entry},9,0x60000000);source_[1]=p.slice({setmbcp},169,0x60000000);source_[2]=p.slice({lock},91,0x60000000);
 if(m4::sha256(source_[0])!="1a41ce536222ffae17fc37752af3a3b00b2c9b95344a788e8cdd907b8399c51b"||m4::sha256(source_[1])!="32386ba7e0e07bd08b91f9a893b9c56342b8f03d704bafa5899cf65167c7d37d"||m4::sha256(source_[2])!="b66fcdb3d2bd6e9f657d964333cb5e2bbef8c230396e506bb92bfb85753279b4")throw std::invalid_argument("Exact genuine default locale bodies required");
}
Binding*current(void*p,unsigned a){auto*known=authority;if(!known)throw std::invalid_argument("Locale active authority absent");if(p!=known||owner!=known||binding!=known||admitted_binding!=known)known->deny("Exact current exclusive locale token required",a);return known;}
void Binding::first(const char*w,unsigned a,unsigned pc){if(!failed){failed=true;reason=w;fault_pc=pc?pc:state.gpr.rip.dword;fault_address=a;}}
[[noreturn]]void Binding::deny(const char*w,unsigned a,unsigned pc){first(w,a,pc);admitted_parent_->first(reason,fault_address,fault_pc);throw mg::BridgeAbort{};}
void Binding::admit_current(){if(authority&&authority!=this)authority->deny("Stale locale binding cannot use current authority",entry);if(binding!=this||admitted_binding!=this)deny("Exact admitted locale side binding required",entry);if(parent!=admitted_parent_||&admitted_parent_->runtime!=&runtime||&admitted_parent_->state!=&state)deny("Locale borrowed parent association required",entry);}
void Binding::guard(){admit_current();if(authority!=this||owner!=this||!active||failed||!started_||control!=admitted_control_||thread_!=std::this_thread::get_id()||depth<1||depth>3||frame!=admitted_frame_||parent_frame!=admitted_parent_frame_||mg::owner||pp::owner||cm::producer_owner||nt::owner||ci::owner||mn::owner||parent->used||parent->active)deny("Exact active serial locale authority and frame required",frame);if(!std::equal(entry_fx_.begin(),entry_fx_.end(),runtime.fx().begin()))deny("Locale changed carried Runtime FX",entry);cm::outer_owner_guard(*admitted_parent_);}
void Binding::source_identity(){admit_current();admitted_parent_->source_identity();for(unsigned i=0;i<3;++i){const auto start=i==0?entry:i==1?setmbcp:lock;std::vector<std::byte>actual(source_[i].size());bool bad{};try{runtime.memory().read({start},actual);bad=actual!=source_[i];}catch(...){bad=true;}if(bad)deny("Exact current locale source identity",start);}}
void Binding::event(unsigned k,unsigned pc,unsigned a,unsigned v){if(event_count==events.size())deny("Locale event bound",a,pc);events[event_count++]={k,pc,a,v};}
void Binding::hook(unsigned point){stage=point;auto&memory=runtime.memory();
 if(point==1&&control==97){memory.protect({0x78003000},Permissions::read|Permissions::write);memory.store<unsigned>({entry},0);memory.protect({0x78003000},Permissions::read|Permissions::execute);}
 if(point==1&&control==98)memory.store<unsigned>({admitted_frame_},m4_runtime::Runtime::external_return^1);
 if(point==1&&control==99)memory.protect({0x20001000},Permissions::read);
 if(point==2&&control==100&&access_count==1)memory.protect({0x20001000},Permissions::read);
 if(point==2&&control==101&&access_count==8)memory.store<unsigned>({admitted_frame_-56},lock_ret^1);
 if(point==2&&control==102&&access_count==9)memory.store<unsigned>({admitted_frame_-52},24);
 if(point==2&&control==103&&access_count==11)memory.store<unsigned>({lock_slot},1);
 if(point==2&&control==104&&access_count==11)(void)__remill_read_memory_32(parent,lock_slot);
 if(point==2&&control==105&&access_count==13)throw std::runtime_error("Authored locale partial-access observer exception");
 if(point==3&&control==106){memory.protect({0x78001000},Permissions::read|Permissions::write);memory.store<unsigned>({malloc_call},0);memory.protect({0x78001000},Permissions::read|Permissions::execute);}
 if(point==3&&control==107)state.gpr.rax.dword^=1;
 if(point==4&&control==108)throw std::runtime_error("Authored locale terminal observer exception");
 if(extra)extra(*this,point);
}
void Binding::stable_hook(unsigned point,bool terminal){const auto old_state=state;const auto old_cpu=runtime.cpu();std::array<std::byte,512>fx{};std::copy(runtime.fx().begin(),runtime.fx().end(),fx.begin());auto progress=[&](){return std::array<unsigned,14>{frame,parent_frame,access_count,event_count,depth,fault_pc,fault_address,unsigned(used),unsigned(active),unsigned(failed),unsigned(malloc_reached),caller_error,restored_error,unsigned(admitted_parent_->failed)};};const auto old_progress=progress();const auto old_accesses=accesses;const auto old_events=events;const auto old_reason=reason;const auto old_scheduler=scheduler;hook(point);admit_current();if(authority!=(terminal?nullptr:this)||owner!=(terminal?nullptr:this)||control!=admitted_control_||stage!=point||old_progress!=progress()||old_reason!=reason||old_scheduler!=scheduler||std::memcmp(&old_state,&state,sizeof(State))||std::memcmp(&old_cpu,&runtime.cpu(),sizeof(old_cpu))||!std::equal(fx.begin(),fx.end(),runtime.fx().begin())||std::memcmp(old_accesses.data(),accesses.data(),sizeof(accesses))||std::memcmp(old_events.data(),events.data(),sizeof(events)))deny("Locale observer changed carried State/FX or lifecycle/ledger",entry);if(!terminal){guard();source_identity();}}
void Binding::record(unsigned a,unsigned v,unsigned write){if(access_count==accesses.size())deny("Locale source access bound",a);accesses[access_count++]={state.gpr.rip.dword,a,v,4,write};stable_hook(2);}
unsigned Binding::read32(unsigned a){guard();source_identity();const auto pc=state.gpr.rip.dword;unsigned want_pc{},want_address{},expected{};switch(access_count){case 9:want_pc=0x78001058;want_address=admitted_frame_-52;expected=25;break;case 11:want_pc=0x7800105c;want_address=lock_slot;break;default:deny("Locale DWORD read outside bounded genuine prefix",a);}if(pc!=want_pc||a!=want_address)deny("Exact locale generated DWORD operand required",a);unsigned v{};try{v=runtime.memory().load<unsigned>({a});}catch(...){deny("Checked locale DWORD read fault",a);}if(v!=expected)deny("Locale source argument or uninitialized lock slot changed",a);record(a,v,0);return v;}
void Binding::write32(unsigned a,unsigned v){guard();source_identity();const auto pc=state.gpr.rip.dword;unsigned want_pc{},want_address{},expected{};switch(access_count){
 case 0:want_pc=entry;want_address=admitted_frame_-4;expected=0xfffffffd;break;
 case 1:want_pc=stub_call;want_address=admitted_frame_-8;expected=stub_ret;break;
 case 2:want_pc=setmbcp;want_address=admitted_frame_-12;expected=saved_[1];break;
 case 3:want_pc=0x78003de1;want_address=admitted_frame_-40;expected=saved_[0];break;
 case 4:want_pc=0x78003de2;want_address=admitted_frame_-44;expected=saved_[2];break;
 case 5:want_pc=0x78003de3;want_address=admitted_frame_-48;expected=saved_[3];break;
 case 6:want_pc=0x78003de4;want_address=admitted_frame_-52;expected=25;break;
 case 7:want_pc=lock_call;want_address=admitted_frame_-56;expected=lock_ret;break;
 case 8:want_pc=lock;want_address=admitted_frame_-60;expected=admitted_frame_-12;break;
 case 10:want_pc=0x7800105b;want_address=admitted_frame_-64;expected=saved_[2];break;
 case 12:want_pc=0x78001078;want_address=admitted_frame_-68;expected=saved_[3];break;
 case 13:want_pc=0x78001079;want_address=admitted_frame_-72;expected=24;break;
 case 14:want_pc=malloc_call;want_address=admitted_frame_-76;expected=malloc_ret;break;
 default:deny("Locale DWORD store outside bounded genuine prefix",a);
 }if(pc!=want_pc||a!=want_address||v!=expected)deny("Exact locale generated PUSH/CALL store required",a);try{runtime.memory().store<unsigned>({a},v);}catch(...){deny("Checked locale generated store fault",a);}record(a,v,1);
}
void*Binding::called(State*s,unsigned target,void*p){guard();source_identity();if(s!=&state||p!=this||state.gpr.rip.dword!=target||access_count==0)deny("Exact locale CALL State/token required",target);const auto&w=accesses[access_count-1];
 const auto site=target==setmbcp?stub_call:target==lock?lock_call:target==malloc_entry?malloc_call:0;const auto ret=target==setmbcp?stub_ret:target==lock?lock_ret:malloc_ret;const auto expected_count=target==setmbcp?2U:target==lock?8U:15U;const auto expected_frame=target==setmbcp?admitted_frame_-8:target==lock?admitted_frame_-56:admitted_frame_-76;
 if(!site||w.pc!=site||w.address!=expected_frame||w.value!=ret||!w.write||access_count!=expected_count||state.gpr.rsp.dword!=expected_frame||runtime.memory().load<unsigned>({expected_frame})!=ret)deny("Actual locale source CALL frame closure required",expected_frame,site);
 if(target==setmbcp){if(depth!=1||event_count!=1||runtime.memory().load<unsigned>({expected_frame+4})!=0xfffffffd)deny("Exact source default selector CALL required",expected_frame,site);event(2,site,target,ret);depth=2;checkpoint(runtime,"locale-setmbcp-before");(void)mw34_locale_default_setmbcp_body(s,target,this);deny("Unexpected default locale setmbcp return",target);}
 if(target==lock){if(depth!=2||event_count!=2||runtime.memory().load<unsigned>({expected_frame+4})!=25)deny("Exact source lock25 CALL required",expected_frame,site);event(3,site,target,ret);depth=3;checkpoint(runtime,"locale-lock-before");(void)mw34_locale_default_lock_body(s,target,this);deny("Unexpected default locale lock return",target);}
 if(depth!=3||event_count!=3||state.gpr.rax.dword!=25||state.gpr.rbp.dword!=admitted_frame_-60||state.gpr.rsi.dword!=lock_slot||state.gpr.rbx.dword!=saved_[0]||state.gpr.rdi.dword!=saved_[3]||runtime.memory().load<unsigned>({expected_frame+4})!=24||runtime.memory().load<unsigned>({lock_slot})!=0)deny("Exact genuine lock malloc frontier required",expected_frame,site);
 checkpoint(runtime,"locale-malloc-before");stable_hook(3);guard();source_identity();malloc_reached=true;event(4,site,target,ret);first("Required genuine CRT malloc for default locale lock remains unresolved",target,site);parent->first(reason,fault_address,fault_pc);throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_translation,{site},{target},reason);
}
[[noreturn]]void Binding::unsupported(unsigned a,const char*w){guard();deny(w,a);}
[[noreturn]]void Binding::start(mg::Context&c){fn::LastErrorBoundary errors;InvocationHostBoundary host;if(authority&&authority!=this)authority->deny("Stale locale direct binding cannot enter current authority",entry);if(&c!=admitted_parent_)deny("Locale scheduler received stale parent Context",entry);admit_current();cm::outer_owner_guard(c);if(authority||owner||used||active||failed||started_||depth||access_count||event_count||control!=admitted_control_||mg::owner||pp::owner||cm::producer_owner||nt::owner||ci::owner||mn::owner||c.used||c.active||runtime.cpu().eip!=mg::slot||runtime.cpu().esp!=0x20001860||state.gpr.rsp.dword!=runtime.cpu().esp)deny("Exact fresh explicit locale bootstrap scheduling required",entry);source_identity();
 parent_frame=runtime.cpu().esp;admitted_parent_frame_=parent_frame;frame=parent_frame-4;admitted_frame_=frame;caller_error=errors.saved;errors.restored=&restored_error;saved_={state.gpr.rbx.dword,state.gpr.rbp.dword,state.gpr.rsi.dword,state.gpr.rdi.dword};std::copy(runtime.fx().begin(),runtime.fx().end(),entry_fx_.begin());checkpoint(runtime,"locale-before");scheduler={1,state.gpr.rip.dword,state.gpr.rsp.dword,entry,frame,frame,m4_runtime::Runtime::external_return,0,runtime.cpu().eip,runtime.cpu().esp};
 try{runtime.memory().store<unsigned>({frame},m4_runtime::Runtime::external_return);}catch(...){deny("Checked explicit locale scheduler return-word store",frame,entry);}state.gpr.rsp.dword=frame;state.gpr.rip.dword=entry;used=true;started_=true;active=true;depth=1;authority=this;owner=this;struct Cleanup{Binding&b;~Cleanup()noexcept{b.active=false;b.depth=0;owner=nullptr;authority=nullptr;}}cleanup{*this};event(1,entry,frame,m4_runtime::Runtime::external_return);
 try{checkpoint(runtime,"locale-projected");stable_hook(1);guard();source_identity();if(runtime.memory().load<unsigned>({frame})!=m4_runtime::Runtime::external_return)deny("Explicit scheduler return word changed before locale stub",frame,entry);(void)mw34_locale_default_mbinit_body(&state,entry,this);deny("Unexpected genuine locale stub RET beyond allocator frontier",entry);}
 catch(const mg::BridgeAbort&){active=false;depth=0;owner=nullptr;authority=nullptr;checkpoint(runtime,"locale-after");stable_hook(4,true);throw std::runtime_error(reason?reason:"Required compiled locale fault");}
 catch(...){first("Required locale observer or host fault");parent->first(reason,fault_address,fault_pc);active=false;depth=0;owner=nullptr;authority=nullptr;checkpoint(runtime,"locale-after");stable_hook(4,true);throw;}
}
}
namespace {
