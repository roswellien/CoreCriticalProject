// Independently authored fixtures on the complete production composition.
// Exclude only CLI main; preserve all Contexts, adapters and typed dispatch.
#define MW34_ENTRY_MAINARGS_NO_MAIN
#include "composition.cpp"
namespace {
unsigned review_checks{},review_scenarios{},review_malformed{};
void review_need(bool ok,const char*why){++review_checks;if(!ok)throw std::runtime_error(std::string(why)+" in independent scenario "+std::to_string(review_scenarios));}
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
void review_before(mg::Context&,unsigned);void review_access(mg::Context&,unsigned);void review_event(mg::Context&,unsigned);void review_after(mg::Context&);
struct ReviewFixture {
 Runtime r;std::unique_ptr<m4_crt::Session>crt;std::unique_ptr<fd::Registry>fdiv;std::unique_ptr<MatherrBinding>matherr;std::unique_ptr<ControlBinding>control;std::unique_ptr<InitermBinding>initterm;std::unique_ptr<MainargsBinding>mainargs;std::unique_ptr<Context>entry_context;
 std::filesystem::path row;unsigned mode{},trigger_count{};Job last_job{};std::array<unsigned,3>outputs_before{};std::array<std::byte,260>module_before{};
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
  mainargs->extra_before=&review_before;mainargs->extra_access=&review_access;mainargs->extra_event=&review_event;mainargs->extra_after=&review_after;
  r.register_service({{matherr->context.slot},{Abi::Cdecl,4,true},&matherr_adapter,"Independent actual game matherr",Domain::admitted_game,fd::provider_sha,"72dabe5c1616590b1fe624844914b6d21fab26cf8eb8ddc3d430de98f50adce4"});
  r.register_translation({{ci::wrapper},{Abi::Cdecl,0,true},&control_wrapper_adapter,"Independent actual game control wrapper",{Domain::admitted_game,m4::admitted_image_hash,19,"ae1fa42ecf74ee2fb8a6076d57a6d7cb51e91890df3a0b0e839f8a4f4063f4ac",MW34_CONTROL_OBJECT_SHA,"2ff6fb125e0abae0b125f0e00e430cf5e8e4a0ab3a22b1c1eb9fefcb65c8175a"}});
  r.register_service({{ci::slot},{Abi::Cdecl,8,true},&control_provider_adapter,"Independent actual staged control provider",Domain::admitted_game,fd::provider_sha,"b75abde48029efcdb8cb123c163c6bfb27a9b76dc62da014e620fca7c95bac56"});
  r.register_translation({{nt::thunk},{Abi::Cdecl,8,true},&initterm_thunk_adapter,"Independent actual first initterm thunk",{Domain::admitted_game,m4::admitted_image_hash,6,"86127a1a5240eff849fe402fc8517ae3ead7498476c8f17188afd36be6060947",MW34_ENTRY_OBJECT_SHA,MW34_INITTERM_SOURCE_SHA}});
  r.register_service({{mg::slot},{Abi::Cdecl,20,true},&mainargs_adapter,"Independent actual mainargs bounded provider prefix",Domain::admitted_game,fd::provider_sha,MW34_MAINARGS_RECOVERY_SHA});
  r.cpu().esp=frame+4;r.cpu().eip=Runtime::external_return;r.freeze_registry();
 }

 ~ReviewFixture(){review_fixture=nullptr;matherr_binding=nullptr;control_binding=nullptr;initterm_binding=nullptr;mainargs_binding=nullptr;mg::owner=nullptr;nt::owner=nullptr;ci::owner=nullptr;mn::owner=nullptr;owner=nullptr;}
 Job call(){Job job;job.entry_context=entry_context.get();review_fixture=this;matherr_binding=matherr.get();control_binding=control.get();initterm_binding=initterm.get();mainargs_binding=mainargs.get();review_boundary(job,row,"entry",review_scenarios);review_fixture=nullptr;matherr_binding=nullptr;control_binding=nullptr;initterm_binding=nullptr;mainargs_binding=nullptr;
  review_need(job.denied&&r.poisoned(),"Actual required dependency or compiled fault terminally poisons root");review_need(!mg::owner&&!nt::owner&&!ci::owner&&!mn::owner&&!owner&&!matherr->context.active&&!control->context.active&&!control->context.boundary_depth&&!initterm->context.active&&!initterm->context.boundary_depth&&!mainargs->context.active&&!mainargs->context.boundary_depth,"Every typed owner and C++ boundary clears after root catch");last_job=job;
  snapshot(r,row,"independent-after");calls_output(row/"calls.json",r);auto&c=mainargs->context;raw_output(row/"mainargs-events.bin",c.events);raw_output(row/"mainargs-accesses.bin",c.accesses);raw_output(row/"mainargs-status.bin",review_status(c));raw_output(row/"mainargs-mode.bin",mode);
  std::array<unsigned,3>fault{job.fault_reason,job.fault_pc,job.fault_target};raw_output(row/"job-fault.bin",fault);std::ofstream why(row/"mainargs-reason.txt");why<<(c.reason?c.reason:"")<<'\n';review_need(bool(why),"Actual first typed diagnostic retained");return job;
 }
 void retry(){auto&c=mainargs->context;auto state=c.state;auto fx=std::array<std::byte,512>{};std::copy(r.fx().begin(),r.fx().end(),fx.begin());const auto pages=review_pages(r);const auto status=review_status(c);const auto events=c.events;const auto accesses=c.accesses;const auto nv=c.nonvolatile;const auto thread=c.thread;const auto*why=c.reason;const auto calls=r.calls();const auto outerevents=entry_context->events();const auto routes=entry_context->data_routes();auto beforecpu=r.cpu();const auto ce=control->context.events;const auto ca=control->context.accesses;const auto ne=initterm->context.events;const auto na=initterm->context.accesses;bool denied{};
  try{entry_context->invoke();}catch(const Fault&f){denied=f.reason()==FaultReason::poisoned;}
  review_need(denied&&!std::memcmp(&state,&c.state,3504)&&std::equal(fx.begin(),fx.end(),r.fx().begin())&&pages==review_pages(r)&&!std::memcmp(&beforecpu,&r.cpu(),sizeof(beforecpu)),"Poisoned retry cannot alter full State/FX/16 pages/runtime CPU");
  review_need(status==review_status(c)&&why==c.reason&&thread==c.thread&&nv==c.nonvolatile&&!std::memcmp(events.data(),c.events.data(),sizeof(events))&&!std::memcmp(accesses.data(),c.accesses.data(),sizeof(accesses))&&review_calls(calls,r.calls())&&outerevents.size()==entry_context->events().size()&&!std::memcmp(outerevents.data(),entry_context->events().data(),outerevents.size()*sizeof(Event))&&routes.size()==entry_context->data_routes().size()&&!std::memcmp(routes.data(),entry_context->data_routes().data(),routes.size()*sizeof(Context::DataRoute)),"Retry preserves complete partial source records/POD first fault/nonvolatile identity and all Runtime/outer ledgers");
  review_need(!std::memcmp(ce.data(),control->context.events.data(),sizeof(ce))&&!std::memcmp(ca.data(),control->context.accesses.data(),sizeof(ca))&&!std::memcmp(ne.data(),initterm->context.events.data(),sizeof(ne))&&!std::memcmp(na.data(),initterm->context.accesses.data(),sizeof(na)),"Retry preserves prior frozen control and initterm records too");
 }
 void positive(){const auto job=call();auto&c=mainargs->context;
  review_need(job.fault_reason==static_cast<unsigned>(FaultReason::unresolved_import)&&job.fault_pc==mg::import_call&&job.fault_target==mg::import_slot,"Actual first ordinary builder CALL stops at unimplemented named GetModuleFileNameA");
  review_need(matherr->context.complete&&control->context.complete&&initterm->context.complete&&c.reached_import&&c.failed&&c.access_count==16&&c.event_count==4&&c.stage==2&&!c.active&&!c.boundary_depth,"Prior frozen bodies complete and both actual mainargs bodies retain exact16 accesses/4 routes");
  review_need(c.frame==0x20001860&&c.ret==mg::return_pc&&c.argc_ptr==0x2000189c&&c.argv_ptr==0x2000188c&&c.env_ptr==0x20001898&&!c.wildcard&&c.startup_ptr==0x20001890&&!c.startup_value&&!c.loaded_startup,"Actual four stack-owned pointers and zero wildcard/newmode are preserved");
  review_need(c.state.gpr.rip.dword==c.provider_raw&&c.state.gpr.rsp.dword==c.frame-44&&c.state.gpr.rbp.dword==c.frame-12&&c.fault_pc==mg::import_call&&c.fault_address==mg::import_slot,"Actual nested CALLs publish final target/stack while first fault retains source import identity");
  review_need(c.accesses[0].pc==mg::entry&&c.accesses[4].pc==0x7800ba6a&&c.accesses[4].address==mg::newmode&&c.accesses[5].pc==mg::internal_call&&c.accesses[5].value==mg::internal_return&&c.accesses[14].pc==mg::import_call&&!c.accesses[14].write&&c.accesses[15].pc==mg::import_call&&c.accesses[15].value==mg::import_return&&c.accesses[15].write,"Source startup-mode store, real internal return and provider CALL words are observed");
  std::array<unsigned,3>outputs{r.memory().load<unsigned>({c.argc_ptr}),r.memory().load<unsigned>({c.argv_ptr}),r.memory().load<unsigned>({c.env_ptr})};std::array<std::byte,260>module{};r.memory().read({0x7803b3f0},module);review_need(outputs==outputs_before&&module==module_before&&r.memory().load<unsigned>({0x78037174})==0,"Unresolved OS call produces no invented argc/argv/environment/module filename or commandline bytes");
  review_need(r.calls().size()==11&&!r.calls()[0].completed&&!r.calls()[10].completed,"Root and actual mainargs import remain incomplete");for(unsigned i=1;i<10;++i)review_need(r.calls()[i].completed,"Every prior actual reached child route is complete");review_need(r.calls()[10].site.value==0x5ac468&&r.calls()[10].target.value==mg::slot&&r.calls()[10].return_pc.value==mg::return_pc&&r.calls()[10].import,"Real source mainargs named CDECL call ledger");retry();
 }
};
void review_before(mg::Context&c,unsigned target){review_need(review_fixture&& &review_fixture->mainargs->context==&c,"Independent live observer exact typed mainargs owner");auto&f=*review_fixture;
 if(target==mg::entry){f.outputs_before={c.runtime.memory().load<unsigned>({c.argc_ptr}),c.runtime.memory().load<unsigned>({c.argv_ptr}),c.runtime.memory().load<unsigned>({c.env_ptr})};c.runtime.memory().read({0x7803b3f0},f.module_before);
  if(f.mode==1)throw std::runtime_error("Independent outer projected observer exception");
  if(f.mode==3)c.runtime.memory().protect({0x20001000},Permissions::read);
  if(f.mode==6)c.runtime.memory().protect({0x78037000},Permissions::read);
  if(f.mode==7)c.runtime.memory().store<unsigned>({c.frame+20},1);
  if(f.mode==8)c.runtime.memory().store<unsigned>({c.startup_ptr},0x13579bdf);
  if(f.mode==9)mainargs_change(c,mg::entry,0);
  if(f.mode==10)mainargs_change(c,mg::slot,c.raw^1);
  if(f.mode==11)c.runtime.memory().store<unsigned>({c.frame+16},1);
  if(f.mode==23)c.thread=std::thread::id{};
 }
 if(target==mg::builder){
  if(f.mode==2)throw std::runtime_error("Independent builder projected observer exception");
  if(f.mode==12)c.runtime.memory().protect({0x20001000},Permissions::read);
  if(f.mode==13)mainargs_change(c,mg::builder,0);
  if(f.mode==14)mainargs_change(c,mg::import_slot,c.provider_raw^1);
  if(f.mode==24)c.active=false;
 }
}
void review_access(mg::Context&c,unsigned count){auto&f=*review_fixture;const auto&v=c.accesses[count-1];
 const unsigned abort_pc=f.mode==4?mg::entry:f.mode==5?0x7800ba68U:f.mode==15?0x7800bbbfU:0U;if(abort_pc&&v.pc==abort_pc){++f.trigger_count;c.deny("Independent required access observer abort",v.address);}
 if(f.mode==16&&v.pc==mg::internal_call){c.runtime.memory().store<unsigned>({c.frame-8},mg::internal_return^1);++f.trigger_count;}
 if(f.mode==17&&v.pc==mg::import_call&&!v.write){c.runtime.memory().store<unsigned>({c.frame-32},259);++f.trigger_count;}
 if(f.mode==18&&v.pc==mg::import_call&&v.write){c.runtime.memory().store<unsigned>({c.frame-44},mg::import_return^1);++f.trigger_count;}
 if(f.mode==19&&v.pc==0x7800ba6a){c.access_count=64;++f.trigger_count;}
}
void review_event(mg::Context&c,unsigned count){auto&f=*review_fixture;const auto&v=c.events[count-1];if(f.mode==20&&v.kind==1){c.event_count=16;++f.trigger_count;}if(f.mode==25&&v.kind==4)throw std::runtime_error("Independent provider CALL route observer exception");}
void review_after(mg::Context&c){auto&f=*review_fixture;if(f.mode==21||f.mode==22){review_need(c.failed&&c.reached_import&&!mg::owner&&!c.active&&!c.boundary_depth,"Typed owner and boundaries close before terminal observer");review_need(c.fault_pc==mg::import_call&&c.fault_address==mg::import_slot,"Terminal observer sees original source API first fault");if(f.mode==21)throw std::runtime_error("Independent terminal after-observer exception");review_need(std::filesystem::create_directory(f.row/"mainargs-after"),"Fresh deliberately failing terminal checkpoint");}}
void review_negative(unsigned mode){ReviewFixture f(mode);const auto job=f.call();auto&c=f.mainargs->context;
 review_need(c.failed&&c.reason&&!c.active&&!c.boundary_depth&&!f.r.calls()[10].completed,"Required compiled or observer fault retains first typed diagnostic and incomplete service");
 if(mode==1)review_need(!c.access_count&&!c.event_count&&c.fault_pc==mg::entry&&std::string(c.reason)=="Required mainargs observer or host fault","Outer projected observer exception unwinds before guest access");
 if(mode==2)review_need(c.access_count==6&&c.event_count==2&&c.stage==2&&c.state.gpr.rip.dword==mg::builder&&c.state.gpr.rsp.dword==c.frame-8,"Builder observer exception retains real nested CALL frame and unwinds both boundaries");
 if(mode==3||mode==4)review_need(c.fault_pc==mg::entry&&c.fault_address==c.frame-4&&c.state.gpr.rsp.dword==c.frame&&c.access_count==(mode==3?0U:1U),"Real first outer PUSH checked fault preserves pre-publication ESP");
 if(mode==5)review_need(c.fault_pc==0x7800ba68&&c.fault_address==c.startup_ptr&&c.access_count==4&&c.state.gpr.rsp.dword==c.frame-4,"Real startup read abort preserves source prefix before mode store");
 if(mode==6)review_need(c.fault_pc==0x7800ba6a&&c.fault_address==mg::newmode&&c.access_count==4,"Actual startup-mode store denied by current guest write permission");
 if(mode==7)review_need(c.fault_pc==0x7800ba61&&c.fault_address==c.frame+20&&c.access_count==1,"Changed actual startup pointer denied before its bytes are interpreted");
 if(mode==8)review_need(c.fault_pc==0x7800ba6a&&c.fault_address==mg::newmode&&c.access_count==5&&c.runtime.memory().load<unsigned>({mg::newmode})==0x13579bdf,"Actual nonzero startup mode store occurs before unsupported-domain denial");
 if(mode==9||mode==10)review_need(c.fault_pc==mg::entry&&!c.access_count&&!c.event_count&&std::string(c.reason)=="Exact mainargs/provider source and game IAT identity","Hot source or game raw IAT identity refuses before first actual PUSH");
 if(mode==11)review_need(c.fault_pc==0x7800ba71&&c.fault_address==0x7800b3b4&&c.access_count==6&&c.event_count==2&&c.state.gpr.rsp.dword==c.frame-8&&c.state.gpr.rip.dword==0x7800b3b4&&std::string(c.reason)=="Required mainargs helper remains outside admitted prefix","Real nonzero wildcard branch writes actual returnBA76 then refuses unreviewed helper");
 if(mode==12)review_need(c.fault_pc==mg::builder&&c.fault_address==c.frame-12&&c.access_count==6&&c.state.gpr.rsp.dword==c.frame-8,"Actual first nested builder PUSH denial preserves its old ESP");
 if(mode==13)review_need(c.fault_pc==mg::builder&&c.access_count==6&&c.event_count==2&&std::string(c.reason)=="Exact mainargs/provider source and game IAT identity","Late builder code mutation refused before nested PUSH");
 if(mode==14)review_need(c.fault_pc==mg::import_call&&c.fault_address==mg::import_slot&&c.access_count==14&&c.state.gpr.rsp.dword==c.frame-40&&!c.reached_import,"Real provider raw IAT changed before read refuses before CALL return publication");
 if(mode==15)review_need(c.fault_pc==0x7800bbbf&&c.fault_address==c.frame-16&&c.access_count==8&&c.state.gpr.rsp.dword==c.frame-12,"Actual nested scratch PUSH abort retains pre-publication ESP");
 if(mode==16)review_need(c.fault_pc==mg::internal_call&&c.fault_address==c.frame-8&&c.access_count==6&&c.stage==1&&c.state.gpr.rip.dword==mg::builder,"Real internal CALL return corruption rejected before builder entry");
 if(mode==17||mode==18)review_need(c.fault_pc==mg::import_call&&c.fault_address==mg::import_slot&&c.access_count==16&&!c.reached_import&&c.state.gpr.rsp.dword==c.frame-44&&std::string(c.reason)=="Actual named GetModuleFileNameA argument/return words changed","Actual API CALL validates exact argument/return words after target and ESP publication");
 if(mode==19)review_need(c.fault_pc==mg::internal_call&&c.fault_address==c.frame-8&&c.access_count==64&&c.state.gpr.rsp.dword==c.frame-4&&std::string(c.reason)=="Mainargs access bound","Actual internal CALL writes return before record-bound denial and ESP publication");
 if(mode==20)review_need(c.fault_pc==mg::builder&&c.access_count==6&&c.event_count==16&&c.stage==1&&std::string(c.reason)=="Mainargs route bound","Real nested event bound fails after CALL publication before builder body");
 if(mode==21||mode==22)review_need(c.reached_import&&c.access_count==16&&c.event_count==4&&c.fault_pc==mg::import_call&&c.fault_address==mg::import_slot&&std::string(c.reason)=="Required KERNEL32.dll!GetModuleFileNameA remains unresolved","Terminal observer/checkpoint exceptions cannot replace original API POD first diagnostic");
 if(mode==23)review_need(c.fault_pc==mg::entry&&!c.access_count&&std::string(c.reason)=="Exact current active serial mainargs owner required","Foreign thread identity refuses before first guest PUSH");
 if(mode==24)review_need(c.fault_pc==mg::builder&&c.access_count==6&&std::string(c.reason)=="Exact current active serial mainargs owner required","Inactive nested owner refuses before first builder guest PUSH");
 if(mode==25)review_need(c.fault_pc==c.provider_raw&&c.access_count==16&&c.event_count==4&&!c.reached_import&&std::string(c.reason)=="Required mainargs observer or host fault","Real CALL route observer exception retains all source accesses while required API remains unexecuted");
 if(mode!=21&&mode!=22)review_need(job.fault_pc!=mg::import_call||job.fault_target!=mg::import_slot,"Independent causal control refuses before clean declared API-stop route");
 f.mainargs->extra_before=nullptr;f.mainargs->extra_access=nullptr;f.mainargs->extra_event=nullptr;f.mainargs->extra_after=nullptr;if(mode==3||mode==12)f.r.memory().protect({0x20001000},Permissions::read|Permissions::write);if(mode==6)f.r.memory().protect({0x78037000},Permissions::read|Permissions::write);f.retry();
}
void review_bad_tokens(){ReviewFixture f;auto&c=f.mainargs->context;mg::Context stale(f.r,review_provider);const auto state=c.state;auto fx=std::array<std::byte,512>{};std::copy(f.r.fx().begin(),f.r.fx().end(),fx.begin());const auto pages=review_pages(f.r);const auto cpu_before=f.r.cpu();const auto ac=c.accesses;const auto ev=c.events;
 auto invoke=[&](unsigned bridge,void*p){switch(bridge){case 0:(void)__remill_read_memory_32(p,mg::import_slot);break;case 1:(void)__remill_write_memory_32(p,frame,0x12345678);break;case 2:(void)__remill_function_return(&c.state,mg::return_pc,p);break;case 3:(void)__remill_jump(&c.state,c.provider_raw,p);break;case 4:(void)mw34_ci_enter(&c.state,ci::wrapper,p);break;case 5:(void)mw34_cf_enter(&c.state,ci::provider_entry,p);break;case 6:(void)mw34_cf_wait(&c.state,0x780042fc,p);break;case 7:(void)mw34_cf_store_cw(&c.state,frame,p);break;case 8:(void)mw34_cf_load_cw(&c.state,frame,p);break;case 9:(void)__remill_function_call(&c.state,c.provider_raw,p);break;case 10:(void)mw34_crte_direct(&c.state,nt::thunk,p);break;case 11:(void)mw34_crte_enter(&c.state,nt::thunk,p);break;case 12:(void)__remill_read_memory_8(p,1);break;case 13:(void)sub_7800bbbc(&c.state,mg::builder,p);break;case 14:(void)sub_7800b3b4(&c.state,0x7800b3b4,p);break;case 15:(void)sub_7800bc48(&c.state,0x7800bc48,p);break;case 16:(void)sub_780012b3(&c.state,0x780012b3,p);break;case 17:(void)sub_7800badb(&c.state,0x7800badb,p);break;case 18:(void)mw34_entry_initerm_undefined_8();break;case 19:(void)mw34_mainargs_normal_argv_undefined_8();break;case 20:(void)mw34_fdiv_entry_undefined_8();break;}};
 auto unchanged=[&]{return !std::memcmp(&state,&c.state,3504)&&std::equal(fx.begin(),fx.end(),f.r.fx().begin())&&pages==review_pages(f.r)&&cpu_before==f.r.cpu()&&!std::memcmp(ac.data(),c.accesses.data(),sizeof(ac))&&!std::memcmp(ev.data(),c.events.data(),sizeof(ev))&&!c.reached_import&&!c.used&&!c.active&&!c.boundary_depth&&!c.stage&&!c.access_count&&!c.event_count&&f.entry_context->events().empty();};
 owner=f.entry_context.get();mg::owner=&c;
 const char*first_reason{};unsigned first_pc{},first_addr{};
 auto denied=[&](unsigned bridge,void*p){bool rejected{};try{invoke(bridge,p);}catch(const mg::BridgeAbort&){rejected=true;}catch(const std::exception&){rejected=true;}review_need(rejected&&unchanged(),"Opaque null/arbitrary/stale/outer/prior owner token refuses before State/FX/page/progress interpretation");++review_malformed;if(c.failed&&!first_reason){first_reason=c.reason;first_pc=c.fault_pc;first_addr=c.fault_address;}if(first_reason)review_need(c.reason==first_reason&&c.fault_pc==first_pc&&c.fault_address==first_addr,"Every subsequent token denial preserves exact current-owner POD first diagnostic");};
 for(void*wrong:{static_cast<void*>(nullptr),reinterpret_cast<void*>(std::uintptr_t{1}),static_cast<void*>(f.entry_context.get()),static_cast<void*>(&f.matherr->context),static_cast<void*>(&f.control->context),static_cast<void*>(&f.initterm->context),static_cast<void*>(&stale)})for(unsigned bridge=0;bridge<21;++bridge)denied(bridge,wrong);
 for(unsigned conflict=0;conflict<3;++conflict){nt::owner=conflict==0?&f.initterm->context:nullptr;ci::owner=conflict==1?&f.control->context:nullptr;mn::owner=conflict==2?&f.matherr->context:nullptr;for(unsigned bridge=0;bridge<21;++bridge)denied(bridge,bridge==10?static_cast<void*>(f.entry_context.get()):static_cast<void*>(&c));}
 nt::owner=nullptr;mn::owner=nullptr;ci::owner=nullptr;mg::owner=nullptr;owner=nullptr;review_need(unchanged()&&c.failed&&first_reason,"Strict dispatch denials preserve all guest storage and terminal first typed fault");const auto job=f.call();review_need(!c.access_count&&!c.reached_import&&c.reason==first_reason&&c.fault_pc==first_pc&&c.fault_address==first_addr&&job.fault_pc!=mg::import_call,"Attempted actual use of failed Context cannot reach provider import or replace first fault");f.retry();
}
void review_run(){for(unsigned index:{0U,5U,11U,12U,17U,23U}){ReviewFixture f(0,index);f.positive();}for(unsigned mode=1;mode<=25;++mode)review_negative(mode);review_bad_tokens();}
}
int main(int argc,char**argv){try{
 review_need(argc==7,"Exact game entryobject provider FDIVpack originalBEFORE freshout");review_game=read_file(argv[1]);review_object=read_file(argv[2]);review_provider=read_file(argv[3]);review_pack=read_file(argv[4]);review_inputs=read_file(argv[5]);review_worker=read_file(argv[0]);review_directory=argv[6];
 review_need(m4::sha256(review_game)==m4::admitted_image_hash&&m4::sha256(review_provider)==fd::provider_sha&&m4::sha256(review_object)==MW34_ENTRY_OBJECT_SHA&&m4::sha256(review_inputs)==MW34_REPLAY_INPUT_SHA,"Exact original-BEFORE and linked literal source identities");review_need(!std::filesystem::exists(review_directory)&&std::filesystem::create_directory(review_directory),"Fresh independent execution directory");review_run();
 std::ofstream f(review_directory/"controls.json");f<<"{\"passed\":true,\"checks\":"<<review_checks<<",\"scenarios\":"<<review_scenarios<<",\"malformed_token_denials\":"<<review_malformed<<",\"ordinary_game_launched\":false,\"original_executed\":false,\"whole_M4_complete\":false}\n";review_need(bool(f),"Independent actual report complete");std::cout<<review_checks<<" independent compiled checks / "<<review_scenarios<<" scenarios passed\n";return 0;
}catch(const std::exception&e){review_fixture=nullptr;matherr_binding=nullptr;control_binding=nullptr;initterm_binding=nullptr;mainargs_binding=nullptr;mg::owner=nullptr;nt::owner=nullptr;ci::owner=nullptr;mn::owner=nullptr;owner=nullptr;std::cerr<<e.what()<<'\n';return 1;}}
