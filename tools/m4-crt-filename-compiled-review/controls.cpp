// Independently authored fixtures on the complete production composition.
// Exclude only CLI main; preserve all Contexts, adapters and typed dispatch.
#define MW34_CRT_FILENAME_NO_MAIN
#include "composition.cpp"
namespace {
unsigned review_checks{},review_scenarios{},review_malformed{};
std::string review_failure;
void review_need(bool ok,const char*why){++review_checks;if(!ok){review_failure=std::string(why)+" in independent scenario "+std::to_string(review_scenarios);throw std::runtime_error(review_failure);}}
std::vector<std::byte>review_game,review_provider,review_pack,review_inputs,review_object,review_worker;
std::filesystem::path review_directory;
template<class T>void review_put(std::byte*p,T v){std::memcpy(p,&v,sizeof(v));}
template<class T>T review_get(const std::byte*p){T v{};std::memcpy(&v,p,sizeof(v));return v;}
void review_boundary(Job&job,const std::filesystem::path&row,const char*name,unsigned scenario){
 Boundary saved{};__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(saved.fx),"=m"(saved.env)::"memory");restore_host(saved);
 auto seeded=saved;const unsigned top=scenario%2?3U:7U;const unsigned depths[]{0,1,3,7};const unsigned depth=depths[scenario%4];const auto sw=static_cast<unsigned short>((top<<11)|0x20);unsigned ftw{},tag=0xffff;
 for(unsigned i=0;i<depth;++i){const auto physical=(top+i)&7;ftw|=1U<<physical;tag&=~(3U<<(2*physical));}
 review_put<unsigned short>(seeded.fx.data(),0xa7f);review_put<unsigned short>(seeded.fx.data()+2,sw);seeded.fx[4]=std::byte(ftw);review_put<unsigned>(seeded.fx.data()+24,0x1fa0);
 for(unsigned i=0;i<8;++i){review_put<std::uint64_t>(seeded.fx.data()+32+16*i,0x8000000000000000ULL+i*0x0101010101010101ULL);review_put<unsigned short>(seeded.fx.data()+40+16*i,static_cast<unsigned short>(0x3fff+i));}
 review_put<unsigned short>(seeded.env.data(),0xa7f);review_put<unsigned short>(seeded.env.data()+4,sw);review_put<unsigned short>(seeded.env.data()+8,static_cast<unsigned short>(tag));
 review_put<unsigned>(seeded.env.data()+12,0x11223344);review_put<unsigned short>(seeded.env.data()+16,0x23);review_put<unsigned short>(seeded.env.data()+18,0x11d);review_put<unsigned>(seeded.env.data()+20,0x55667788);review_put<unsigned short>(seeded.env.data()+24,0x2b);
 restore_host(seeded);try{boundary(job,row,name,scenario);}catch(...){restore_host(saved);throw;}restore_host(saved);
 const auto actual=read_file((row/(std::string(name)+"-host-before.bin")).string().c_str());review_need(actual.size()==544&&!std::memcmp(actual.data()+524,seeded.env.data()+12,14),"Actual direct hardware BEFORE retains complete nonzero legacy metadata");
}
std::array<std::byte,16*4096>review_pages(Runtime&r){std::array<std::byte,16*4096>b{};for(unsigned i=0;i<composition_pages.size();++i)r.memory().read({composition_pages[i]},std::span{b}.subspan(i*4096,4096));return b;}
std::array<unsigned,23>review_status(const mg::Context&c){return {c.raw,c.provider_raw,c.frame,c.ret,c.argc_ptr,c.argv_ptr,c.env_ptr,c.wildcard,c.startup_ptr,c.startup_value,c.loaded_startup,c.access_count,c.event_count,c.boundary_depth,c.stage,c.fault_pc,c.fault_address,unsigned(c.used),unsigned(c.active),unsigned(c.failed),unsigned(c.reached_import),0,0};}
bool review_calls(const std::vector<CallRecord>&a,const std::vector<CallRecord>&b){if(a.size()!=b.size())return false;for(unsigned i=0;i<a.size();++i)if(a[i].site!=b[i].site||a[i].target!=b[i].target||a[i].return_pc!=b[i].return_pc||a[i].import!=b[i].import||a[i].completed!=b[i].completed||a[i].name!=b[i].name)return false;return true;}
struct ReviewFixture;thread_local ReviewFixture*review_fixture{};
void review_before(mg::Context&,unsigned);void review_access(mg::Context&,unsigned);void review_event(mg::Context&,unsigned);void review_after(mg::Context&);void review_filename(fn::Binding&,unsigned);
struct ReviewFixture {
 Runtime r;std::unique_ptr<m4_crt::Session>crt;std::unique_ptr<fd::Registry>fdiv;std::unique_ptr<MatherrBinding>matherr;std::unique_ptr<ControlBinding>control;std::unique_ptr<InitermBinding>initterm;std::unique_ptr<MainargsBinding>mainargs;std::unique_ptr<Context>entry_context;std::unique_ptr<fn::Binding>filename,stale_filename;std::unique_ptr<mg::Context>stale_context;
 std::filesystem::path row;unsigned mode{},trigger_count{};Job last_job{};std::array<std::byte,3504>pre_api_state{};std::array<std::byte,512>pre_api_fx{};std::array<unsigned,3>outputs_before{};std::array<std::byte,260>module_before{};
 explicit ReviewFixture(unsigned which=0,unsigned index=0):r([&]{Policy p;p.stack_low={0x20001000};p.stack_bytes=4096;p.heap_bytes=4096;return Runtime::from_admitted_image(review_game,p);}()),mode(which){
  ++review_scenarios;row=review_directory/("case-"+std::to_string(review_scenarios));review_need(std::filesystem::create_directory(row),"Fresh actual independent row");checkpoint_directory=row;
  crt=std::make_unique<m4_crt::Session>(r,review_provider,m4_crt::Proof{Domain::admitted_game,m4::sha256(review_worker),"09a6018bb2cd3a6daf79786ee0bd2485b25f6b8c78740a352989019a2511e42a"});
  Input in{};std::memcpy(&in,review_inputs.data()+24+index*sizeof(Input),sizeof(in));seed(r,in);
  for(auto address:matherr_pages){const auto page=provider_raw_page(review_provider,address);r.memory().map({address},4096,Permissions::read|Permissions::write);r.memory().write({address},page);if(address==matherr_pages[0])r.memory().protect({address},Permissions::read|Permissions::execute);}
  {const auto page=provider_raw_page(review_provider,0x78001000);r.memory().map({0x78001000},4096,Permissions::read|Permissions::write);r.memory().write({0x78001000},page);r.memory().protect({0x78001000},Permissions::read|Permissions::execute);}
  fdiv=std::make_unique<fd::Registry>(r);review_need(fdiv->admit(review_provider,review_pack),"Exact source FDIV admission");Job writer;writer.writer=fdiv.get();review_boundary(writer,row,"writer",review_scenarios);review_need(writer.ok&&fdiv->ready(),"Actual source producer completes before same-State entry");
  auto state=std::array<std::byte,3504>{};std::copy(r.remill_state().begin(),r.remill_state().end(),state.begin());auto fx=std::array<std::byte,512>{};std::copy(r.fx().begin(),r.fx().end(),fx.begin());
  matherr=std::make_unique<MatherrBinding>(r,review_provider,0);control=std::make_unique<ControlBinding>(r,0);initterm=std::make_unique<InitermBinding>(r,review_game,review_provider,0);mainargs=std::make_unique<MainargsBinding>(r,review_provider,0);entry_context=std::make_unique<Context>(r,*fdiv,m4::sha256(review_object));
  review_need(std::equal(state.begin(),state.end(),r.remill_state().begin())&&std::equal(fx.begin(),fx.end(),r.fx().begin()),"All Contexts borrow every persistent State/FX byte without reseed");
  filename=std::make_unique<fn::Binding>(mainargs->context,0,0xc1100000U+review_scenarios);filename->extra=&review_filename;stale_context=std::make_unique<mg::Context>(r,review_provider);stale_filename=std::make_unique<fn::Binding>(*stale_context);
  mainargs->extra_before=&review_before;mainargs->extra_access=&review_access;mainargs->extra_event=&review_event;mainargs->extra_after=&review_after;
  r.register_service({{matherr->context.slot},{Abi::Cdecl,4,true},&matherr_adapter,"Independent actual game matherr",Domain::admitted_game,fd::provider_sha,"72dabe5c1616590b1fe624844914b6d21fab26cf8eb8ddc3d430de98f50adce4"});
  r.register_translation({{ci::wrapper},{Abi::Cdecl,0,true},&control_wrapper_adapter,"Independent actual game control wrapper",{Domain::admitted_game,m4::admitted_image_hash,19,"ae1fa42ecf74ee2fb8a6076d57a6d7cb51e91890df3a0b0e839f8a4f4063f4ac",MW34_CONTROL_OBJECT_SHA,"2ff6fb125e0abae0b125f0e00e430cf5e8e4a0ab3a22b1c1eb9fefcb65c8175a"}});
  r.register_service({{ci::slot},{Abi::Cdecl,8,true},&control_provider_adapter,"Independent actual staged control provider",Domain::admitted_game,fd::provider_sha,"b75abde48029efcdb8cb123c163c6bfb27a9b76dc62da014e620fca7c95bac56"});
  r.register_translation({{nt::thunk},{Abi::Cdecl,8,true},&initterm_thunk_adapter,"Independent actual first initterm thunk",{Domain::admitted_game,m4::admitted_image_hash,6,"86127a1a5240eff849fe402fc8517ae3ead7498476c8f17188afd36be6060947",MW34_ENTRY_OBJECT_SHA,MW34_INITTERM_SOURCE_SHA}});
  r.register_service({{mg::slot},{Abi::Cdecl,20,true},&mainargs_adapter,"Independent actual mainargs bounded provider prefix",Domain::admitted_game,fd::provider_sha,MW34_MAINARGS_RECOVERY_SHA});
  r.cpu().esp=frame+4;r.cpu().eip=Runtime::external_return;r.freeze_registry();
 }

 ~ReviewFixture(){fn::binding=nullptr;fn::admitted_binding=nullptr;review_fixture=nullptr;matherr_binding=nullptr;control_binding=nullptr;initterm_binding=nullptr;mainargs_binding=nullptr;mg::owner=nullptr;nt::owner=nullptr;ci::owner=nullptr;mn::owner=nullptr;owner=nullptr;}
 Job call(){Job job;job.entry_context=entry_context.get();review_fixture=this;matherr_binding=matherr.get();control_binding=control.get();initterm_binding=initterm.get();mainargs_binding=mainargs.get();fn::binding=filename.get();fn::admitted_binding=filename.get();review_boundary(job,row,"entry",review_scenarios);review_fixture=nullptr;matherr_binding=nullptr;control_binding=nullptr;initterm_binding=nullptr;mainargs_binding=nullptr;fn::binding=nullptr;fn::admitted_binding=nullptr;
  if(!review_failure.empty())throw std::runtime_error(review_failure);
  review_need(job.denied&&r.poisoned(),"Actual required dependency or compiled fault terminally poisons root");review_need(!fn::binding&&!fn::admitted_binding&&!filename->active&&!mg::owner&&!nt::owner&&!ci::owner&&!mn::owner&&!owner&&!matherr->context.active&&!control->context.active&&!control->context.boundary_depth&&!initterm->context.active&&!initterm->context.boundary_depth&&!mainargs->context.active&&!mainargs->context.boundary_depth,"Every typed owner and C++ boundary clears after root catch");review_need(fn::outer_error_before==fn::outer_error_after,"Outer actual caller LastError retained through call/catch");if(filename->used)review_need(filename->caller_error==filename->restored_error,"Actual filename service caller LastError restored on every exit");last_job=job;
  snapshot(r,row,"independent-after");calls_output(row/"calls.json",r);auto&c=mainargs->context;raw_output(row/"mainargs-events.bin",c.events);raw_output(row/"mainargs-accesses.bin",c.accesses);raw_output(row/"mainargs-status.bin",review_status(c));raw_output(row/"mainargs-mode.bin",mode);
  std::array<unsigned,3>fault{job.fault_reason,job.fault_pc,job.fault_target};raw_output(row/"job-fault.bin",fault);std::ofstream why(row/"mainargs-reason.txt");why<<(c.reason?c.reason:"")<<'\n';review_need(bool(why),"Actual first typed diagnostic retained");raw_output(row/"filename-witness.bin",filename->witness);raw_output(row/"actual-filename-witness.bin",filename->actual_witness());std::array<unsigned,22>fs{mode,filename->frame,filename->result,filename->last_error,filename->caller_error,filename->restored_error,filename->stage,filename->hook_count,filename->fault_pc,filename->fault_address,unsigned(filename->used),unsigned(filename->active),unsigned(filename->api_called),unsigned(filename->stored),unsigned(filename->returned),unsigned(filename->stopped),unsigned(filename->failed),fn::outer_error_before,fn::outer_error_after,fn::commandline,fn::stop_pc,filename->incoming_error};raw_output(row/"filename-status.bin",fs);if(filename->api_called){raw_output(row/"filename-api-before.bin",api(filename->api_before));raw_output(row/"filename-api-after.bin",api(filename->api_after));raw_output(row/"filename-module-before.bin",module(filename->module_before));raw_output(row/"filename-module-after.bin",module(filename->module_after));}return job;
 }
 void retry(){auto&c=mainargs->context;auto state=c.state;auto fx=std::array<std::byte,512>{};std::copy(r.fx().begin(),r.fx().end(),fx.begin());const auto pages=review_pages(r);const auto status=review_status(c);std::array<std::byte,sizeof(fn::Binding)>filename_status{};std::memcpy(filename_status.data(),filename.get(),filename_status.size());const auto events=c.events;const auto accesses=c.accesses;const auto nv=c.nonvolatile;const auto thread=c.thread;const auto*why=c.reason;const auto calls=r.calls();const auto outerevents=entry_context->events();const auto routes=entry_context->data_routes();auto beforecpu=r.cpu();const auto ce=control->context.events;const auto ca=control->context.accesses;const auto ne=initterm->context.events;const auto na=initterm->context.accesses;bool denied{};
  try{entry_context->invoke();}catch(const Fault&f){denied=f.reason()==FaultReason::poisoned;}
  review_need(denied&&!std::memcmp(&state,&c.state,3504)&&std::equal(fx.begin(),fx.end(),r.fx().begin())&&pages==review_pages(r)&&!std::memcmp(&beforecpu,&r.cpu(),sizeof(beforecpu)),"Poisoned retry cannot alter full State/FX/16 pages/runtime CPU");
  review_need(status==review_status(c)&&why==c.reason&&thread==c.thread&&nv==c.nonvolatile&&!std::memcmp(events.data(),c.events.data(),sizeof(events))&&!std::memcmp(accesses.data(),c.accesses.data(),sizeof(accesses))&&review_calls(calls,r.calls())&&outerevents.size()==entry_context->events().size()&&!std::memcmp(outerevents.data(),entry_context->events().data(),outerevents.size()*sizeof(Event))&&routes.size()==entry_context->data_routes().size()&&!std::memcmp(routes.data(),entry_context->data_routes().data(),routes.size()*sizeof(Context::DataRoute)),"Retry preserves complete partial source records/POD first fault/nonvolatile identity and all Runtime/outer ledgers");
  review_need(!std::memcmp(ce.data(),control->context.events.data(),sizeof(ce))&&!std::memcmp(ca.data(),control->context.accesses.data(),sizeof(ca))&&!std::memcmp(ne.data(),initterm->context.events.data(),sizeof(ne))&&!std::memcmp(na.data(),initterm->context.accesses.data(),sizeof(na)),"Retry preserves prior frozen control and initterm records too");review_need(!std::memcmp(filename_status.data(),filename.get(),filename_status.size()),"Poisoned retry retains complete public/private filename witness/progress/return State and FX");
 }

 void verify(bool clean){auto&c=mainargs->context;auto&n=*filename;
  std::array<std::byte,260>b{};r.memory().read({fn::buffer},b);
  review_need(c.access_count==16&&matherr->context.complete&&control->context.complete&&initterm->context.complete,"Exact actual prior composition and sixteen source memory accesses retained");
  review_need(r.calls().size()==11&&!r.calls()[0].completed&&!r.calls()[10].completed,"Root/mainargs incomplete; no fabricated generic provider call frame");for(unsigned i=1;i<10;++i)review_need(r.calls()[i].completed,"Prior actual Runtime routes complete");
  review_need(r.cpu().eip==mg::slot&&r.cpu().esp==c.frame,"Runtime CPU remains at actual outer mainargs slot/frame throughout internal service");
  if(n.api_called){review_need(n.actual_witness().capacity==260&&n.actual_witness().incoming_error==n.incoming_error,"Actual native API witness binds literal capacity and explicit error input");review_need(n.api_before==n.api_after&&n.module_before==n.module_after,"Actual measured API/module identities stable");}
  if(n.stage>=3)review_need(b==n.actual_witness().after||(mode==19),"Stored entire buffer derives from immutable actual API result including tail");else review_need(b==module_before,"No guest buffer publication before successful whole transfer");
  if(clean){review_need(last_job.fault_reason==unsigned(FaultReason::unresolved_translation)&&last_job.fault_pc==fn::stop_pc&&last_job.fault_target==fn::commandline,"Actual compiled MOV read refuses initialized commandline dependency before load");review_need(n.api_called&&n.stored&&n.returned&&n.stopped&&!n.failed&&c.event_count==6,"Service completes real API/store/RET before typed required read stop");review_need(c.state.gpr.rax.dword==n.actual_witness().result&&c.state.gpr.rsp.dword==c.frame-28&&c.state.gpr.rip.dword==fn::stop_pc,"Actual DWORD API result and stdcall ESP+16 return published");review_need(c.events[4].kind==5&&c.events[4].pc==fn::stop_pc&&c.events[4].value==n.actual_witness().result&&c.events[5].kind==6&&c.events[5].address==fn::commandline,"Real return and refused source-read routes retained");std::array<unsigned,3>outputs{r.memory().load<unsigned>({c.argc_ptr}),r.memory().load<unsigned>({c.argv_ptr}),r.memory().load<unsigned>({c.env_ptr})};review_need(outputs==outputs_before,"Argument/environment outputs remain exactly unchanged");}
  else review_need(last_job.fault_pc!=fn::stop_pc||last_job.fault_target!=fn::commandline,"Independent causal mutation cannot receive clean required stop credit");
  retry();
 }
};
void review_before(mg::Context&c,unsigned target){if(target==mg::entry){auto&f=*review_fixture;std::array<std::byte,260>buffer_seed{};for(unsigned n=0;n<260;++n)buffer_seed[n]=std::byte((n*29+review_scenarios*7)&255);c.runtime.memory().write({fn::buffer},buffer_seed);f.outputs_before={c.runtime.memory().load<unsigned>({c.argc_ptr}),c.runtime.memory().load<unsigned>({c.argv_ptr}),c.runtime.memory().load<unsigned>({c.env_ptr})};c.runtime.memory().read({fn::buffer},f.module_before);}}
void review_access(mg::Context&,unsigned){}
void review_event(mg::Context&,unsigned){}
void review_after(mg::Context&c){if(review_fixture&&review_fixture->mode==29){review_need(!mg::owner&&!c.active&&!c.boundary_depth,"All current Context ownership closed before terminal observer");throw std::runtime_error("Independent outer terminal observer failure");}}
void review_oracle(fn::Binding&n){fn::LastErrorBoundary errors;InvocationHostBoundary fp;
 const auto procedure=GetProcAddress(GetModuleHandleW(L"kernel32.dll"),"GetModuleFileNameA");std::array<std::byte,260>b=n.actual_witness().before;SetLastError(n.actual_witness().incoming_error);const auto result=GetModuleFileNameA(nullptr,reinterpret_cast<char*>(b.data()),260);const auto error=GetLastError();
 review_need(procedure!=nullptr&&result==n.actual_witness().result&&error==n.actual_witness().last_error&&b==n.actual_witness().after,"Second independent actual OS call matches complete260-byte witness/result/immediate error");
}
void review_side(fn::Binding&n,unsigned variant){auto&f=*review_fixture;auto&c=n.context;std::array<std::byte,sizeof(fn::Binding)>sb{};std::array<std::byte,sizeof(mg::Context)>sc{};std::memcpy(sb.data(),f.stale_filename.get(),sb.size());std::memcpy(sc.data(),f.stale_context.get(),sc.size());const auto state=c.state;std::array<std::byte,512>fx{};std::copy(f.r.fx().begin(),f.r.fx().end(),fx.begin());const auto pages=review_pages(f.r);const auto events=c.events;const auto accesses=c.accesses;bool denied{};
 auto*published=fn::binding;auto*admitted=fn::admitted_binding;
 try{if(variant==22||variant==25)fn::binding=f.stale_filename.get();if(variant==23)fn::binding=reinterpret_cast<fn::Binding*>(std::uintptr_t{1});if(variant==24)fn::admitted_binding=f.stale_filename.get();if(variant==31)fn::binding=nullptr;
 if(variant==25)(void)__remill_read_memory_32(&c,fn::commandline);else if(variant==26)f.stale_filename->invoke(&c.state,c.provider_raw,&c);else if(variant==27){for(void*wrong:{static_cast<void*>(nullptr),reinterpret_cast<void*>(std::uintptr_t{1}),static_cast<void*>(f.entry_context.get()),static_cast<void*>(&f.matherr->context),static_cast<void*>(&f.control->context),static_cast<void*>(&f.initterm->context),static_cast<void*>(f.stale_context.get())}){bool refused{};try{(void)__remill_function_call(&c.state,c.provider_raw,wrong);}catch(const mg::BridgeAbort&){refused=true;}review_need(refused,"Every opaque null/arbitrary/outer/prior/stale token refuses through actual current global filename call bridge");++review_malformed;}throw mg::BridgeAbort{};}else if(variant==28)n.closure(reinterpret_cast<State*>(std::uintptr_t{1}),c.provider_raw);else (void)__remill_function_call(&c.state,c.provider_raw,&c);
 }catch(const mg::BridgeAbort&){denied=true;}catch(const Fault&){denied=true;}catch(const std::exception&){denied=true;}
 fn::binding=published;fn::admitted_binding=admitted;
 review_need(denied&&c.failed&&!std::memcmp(sb.data(),f.stale_filename.get(),sb.size())&&!std::memcmp(sc.data(),f.stale_context.get(),sc.size()),"Current owner refusal leaves stale side Binding/Context byte-for-byte untouched");review_need(!std::memcmp(&state,&c.state,sizeof(State))&&std::equal(fx.begin(),fx.end(),f.r.fx().begin())&&pages==review_pages(f.r)&&!std::memcmp(events.data(),c.events.data(),sizeof(events))&&!std::memcmp(accesses.data(),c.accesses.data(),sizeof(accesses)),"Malformed filename side/opaque token refuses before guest bytes or source progress effects");if(variant!=27)++review_malformed;throw mg::BridgeAbort{};
}
void review_filename(fn::Binding&n,unsigned point){auto&f=*review_fixture;auto&c=n.context;
 if(point==1){std::memcpy(f.pre_api_state.data(),&c.state,sizeof(State));std::copy(f.r.fx().begin(),f.r.fx().end(),f.pre_api_fx.begin());}
 if(point==2)review_oracle(n);
 if(f.mode==1&&point==1)throw std::runtime_error("Independent before API observer");
 if(f.mode==2&&point==2)throw std::runtime_error("Independent after API observer");
 if(f.mode==3&&point==3)throw std::runtime_error("Independent after buffer observer");
 if(f.mode==4&&point==4)throw std::runtime_error("Independent after RET observer");
 if(f.mode==5&&point==5)throw std::runtime_error("Independent before refused read observer");
 if(f.mode==6&&point==2)n.witness.after[259]^=std::byte{1};
 if(f.mode==7&&point==2)++n.result;
 if(f.mode==8&&point==3)n.witness.before[259]^=std::byte{1};
 if(f.mode==9&&point==5)c.state.rflag.flat^=0x100;
 if(f.mode==10&&point==5)c.runtime.fx()[24]^=std::byte{0x20};
 if((f.mode==11&&point==1)||(f.mode==12&&point==2))n.frame+=4;
 if(f.mode==13&&point==2)n.stored=true;
 if(f.mode==14&&point==2)n.returned=true;
 if(f.mode==15&&point==2)n.active=false;
 if(f.mode==16&&point==3)c.state.gpr.rsp.dword+=4;
 if(f.mode==17&&point==2)c.runtime.memory().store<unsigned>({n.frame},mg::import_return^1);
 if(f.mode==18&&point==2)c.runtime.memory().protect({fn::buffer&~4095U},Permissions::read);
 if(f.mode==19&&point==3){std::array<std::byte,260>b{};c.runtime.memory().read({fn::buffer},b);b[259]^=std::byte{1};c.runtime.memory().write({fn::buffer},b);}
 if(f.mode==20&&point==5)c.runtime.memory().store<unsigned>({fn::commandline},0xa55aa55a);
 if(f.mode==21&&point==4)mainargs_change(c,fn::stop_pc,0);
 if(((f.mode>=22&&f.mode<=24)||f.mode==26||f.mode==27||f.mode==28||f.mode==31)&&point==1)review_side(n,f.mode);
 if(f.mode==25&&point==5)review_side(n,25);
 if(f.mode==30&&point==2)c.runtime.fx()[2]^=std::byte{0x20};
 if(f.mode==32&&point==1)n.stored=true;
 if(f.mode==33&&point==1)n.returned=true;
 if(f.mode==34&&point==1)n.active=false;
 if(f.mode==35&&point==5)n.stopped=true;
}
void review_negative(unsigned mode){ReviewFixture f(mode);const auto job=f.call();auto&n=*f.filename;auto&c=n.context;
 if(mode==20){review_need(f.r.memory().load<unsigned>({fn::commandline})==0xa55aa55a&&c.state.gpr.rax.dword==n.actual_witness().result,"Required source read refuses even nonzero commandline data before loading EAX");f.verify(true);return;}
 review_need(!n.stopped||mode==29||mode==35,"Every independent mutation terminates before required-read success");
 const bool api_expected=mode!=1&&mode!=11&&mode!=22&&mode!=23&&mode!=24&&mode!=26&&mode!=27&&mode!=28&&mode!=31&&mode!=32&&mode!=33&&mode!=34;
 review_need(n.api_called==api_expected,"Actual API invocation ordering matches independent causal point");
 const bool buffer_expected=(mode==3||mode==4||mode==5||mode==8||mode==9||mode==10||mode==16||mode==19||mode==21||mode==25||mode==29||mode==35);
 std::array<std::byte,260>buffer{};f.r.memory().read({fn::buffer},buffer);review_need(buffer_expected?(buffer==n.actual_witness().after||mode==19):buffer==f.module_before,"Whole guest buffer effects retain exact checked-transfer fault ordering");
 const bool ret_expected=(mode==4||mode==5||mode==9||mode==10||mode==21||mode==25||mode==29||mode==35);
 if(ret_expected)review_need(c.state.gpr.rip.dword==fn::stop_pc&&c.state.gpr.rsp.dword==c.frame-28&&c.state.gpr.rax.dword==n.actual_witness().result,"Real completed stdcall return survives later observer/closure fault");else if(mode!=16)review_need(c.state.gpr.rsp.dword==c.frame-44&&c.state.gpr.rip.dword==c.provider_raw,"Fault before RET preserves actual source CALL target/frame");
 if(mode==18)f.r.memory().protect({fn::buffer&~4095U},Permissions::read|Permissions::write);
 f.verify(false);
}
thread_local unsigned review_capacity{};
void review_unit(){fn::LastErrorBoundary error;InvocationHostBoundary fp;const auto procedure=GetProcAddress(GetModuleHandleW(L"kernel32.dll"),"GetModuleFileNameA");std::array<std::byte,260>seed{};for(unsigned n=0;n<260;++n)seed[n]=std::byte((n*47+3)&255);auto actual=fn::native_filename(review_capacity,0xface0246,seed,procedure);std::array<std::byte,260>oracle=seed;SetLastError(0xface0246);const auto result=GetModuleFileNameA(nullptr,reinterpret_cast<char*>(oracle.data()),review_capacity);const auto last=GetLastError();review_need(actual.result==result&&actual.last_error==last&&actual.after==oracle&&actual.before==seed,"Independent exact actualAPI capacity/result/error/full-buffer comparison");review_need(std::equal(actual.after.begin()+review_capacity,actual.after.end(),seed.begin()+review_capacity),"Actual API preserves bytes outside declared scratch capacity");if(review_capacity&&review_capacity<260)review_need(actual.result==review_capacity&&actual.last_error==ERROR_INSUFFICIENT_BUFFER&&actual.after[review_capacity-1]==std::byte{},"Measured modern host truncation DWORD/error/NUL is retained");raw_output(review_fixture->row/"unit-witness.bin",actual);}
void review_run(){for(unsigned index:{0U,5U,11U,12U,17U,23U}){ReviewFixture f(0,index);f.call();f.verify(true);}for(unsigned mode=1;mode<=35;++mode)review_negative(mode);for(unsigned size:{0U,1U,8U,260U}){ReviewFixture f(100+size);review_fixture=&f;review_capacity=size;Job job;job.unit=&review_unit;review_boundary(job,f.row,"entry",review_scenarios);review_fixture=nullptr;review_need(job.ok&&!job.denied&&fn::outer_error_before==fn::outer_error_after,"Isolated actual API capacity unit retains enclosing caller and host hardware");}}
}
int main(int argc,char**argv){try{
 review_need(argc==7,"Exact game entryobject provider FDIVpack originalBEFORE freshout");review_game=read_file(argv[1]);review_object=read_file(argv[2]);review_provider=read_file(argv[3]);review_pack=read_file(argv[4]);review_inputs=read_file(argv[5]);review_worker=read_file(argv[0]);review_directory=argv[6];
 review_need(m4::sha256(review_game)==m4::admitted_image_hash&&m4::sha256(review_provider)==fd::provider_sha&&m4::sha256(review_object)==MW34_ENTRY_OBJECT_SHA&&m4::sha256(review_inputs)==MW34_REPLAY_INPUT_SHA,"Exact original-BEFORE and linked literal source identities");review_need(!std::filesystem::exists(review_directory)&&std::filesystem::create_directory(review_directory),"Fresh independent execution directory");review_run();
 std::ofstream f(review_directory/"controls.json");f<<"{\"passed\":true,\"checks\":"<<review_checks<<",\"scenarios\":"<<review_scenarios<<",\"malformed_token_denials\":"<<review_malformed<<",\"ordinary_game_launched\":false,\"original_executed\":false,\"whole_M4_complete\":false}\n";review_need(bool(f),"Independent actual report complete");std::cout<<review_checks<<" independent compiled checks / "<<review_scenarios<<" scenarios passed\n";return 0;
}catch(const std::exception&e){fn::binding=nullptr;fn::admitted_binding=nullptr;review_fixture=nullptr;matherr_binding=nullptr;control_binding=nullptr;initterm_binding=nullptr;mainargs_binding=nullptr;mg::owner=nullptr;nt::owner=nullptr;ci::owner=nullptr;mn::owner=nullptr;owner=nullptr;std::cerr<<e.what()<<'\n';return 1;}}
