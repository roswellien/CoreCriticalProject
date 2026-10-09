// Independently authored fixtures on the complete production composition.
// Exclude only CLI main; preserve all Contexts, adapters and typed dispatch.
#define MW34_ENTRY_CONTROL_NO_MAIN
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
std::array<std::byte,14*4096>review_pages(Runtime&r){std::array<std::byte,14*4096>b{};for(unsigned i=0;i<composition_pages.size();++i)r.memory().read({composition_pages[i]},std::span{b}.subspan(i*4096,4096));return b;}
struct ReviewFixture;
thread_local ReviewFixture*review_fixture{};
void review_before(ci::Context&,unsigned);
void review_access(ci::Context&,unsigned);
void review_event(ci::Context&,unsigned);
void review_after(ci::Context&);
struct ReviewFixture {
 Runtime r;std::unique_ptr<m4_crt::Session>crt;std::unique_ptr<fd::Registry>fdiv;std::unique_ptr<MatherrBinding>matherr;std::unique_ptr<ControlBinding>control;std::unique_ptr<Context>entry_context;
 std::filesystem::path row;unsigned mode{},guest_word{},trigger_count{};std::uint16_t initial_cw{};Job last_job{};
 explicit ReviewFixture(unsigned which=0,unsigned index=0):r([&]{Policy p;p.stack_low={0x20001000};p.stack_bytes=4096;p.heap_bytes=4096;return Runtime::from_admitted_image(review_game,p);}()),mode(which){
  ++review_scenarios;row=review_directory/("case-"+std::to_string(review_scenarios));review_need(std::filesystem::create_directory(row),"Fresh actual independent row");checkpoint_directory=row;
  crt=std::make_unique<m4_crt::Session>(r,review_provider,m4_crt::Proof{Domain::admitted_game,m4::sha256(review_worker),"09a6018bb2cd3a6daf79786ee0bd2485b25f6b8c78740a352989019a2511e42a"});
  Input in{};std::memcpy(&in,review_inputs.data()+24+index*sizeof(Input),sizeof(in));seed(r,in);
  fdiv=std::make_unique<fd::Registry>(r);review_need(fdiv->admit(review_provider,review_pack),"Exact FDIV source admission");Job writer;writer.writer=fdiv.get();review_boundary(writer,row,"writer",review_scenarios);review_need(writer.ok&&fdiv->ready(),"Actual source producer finishes before same-State entry");
  for(auto address:matherr_pages){const auto page=provider_raw_page(review_provider,address);r.memory().map({address},4096,Permissions::read|Permissions::write);r.memory().write({address},page);if(address==matherr_pages[0])r.memory().protect({address},Permissions::read|Permissions::execute);}
  auto state=std::array<std::byte,3504>{};std::copy(r.remill_state().begin(),r.remill_state().end(),state.begin());auto fx=std::array<std::byte,512>{};std::copy(r.fx().begin(),r.fx().end(),fx.begin());
  matherr=std::make_unique<MatherrBinding>(r,review_provider,0);control=std::make_unique<ControlBinding>(r,0);entry_context=std::make_unique<Context>(r,*fdiv,m4::sha256(review_object));
  review_need(std::equal(state.begin(),state.end(),r.remill_state().begin())&&std::equal(fx.begin(),fx.end(),r.fx().begin()),"Both service Contexts borrow every State/FX byte without reseed");initial_cw=control->context.state.x87.fxsave.cwd.flat;
  control->extra_before=&review_before;control->extra_access=&review_access;control->extra_event=&review_event;control->extra_after=&review_after;
  r.register_service({{matherr->context.slot},{Abi::Cdecl,4,true},&matherr_adapter,"Independent actual game matherr",Domain::admitted_game,fd::provider_sha,"72dabe5c1616590b1fe624844914b6d21fab26cf8eb8ddc3d430de98f50adce4"});
  r.register_translation({{ci::wrapper},{Abi::Cdecl,0,true},&control_wrapper_adapter,"Independent actual game control wrapper",{Domain::admitted_game,m4::admitted_image_hash,19,"ae1fa42ecf74ee2fb8a6076d57a6d7cb51e91890df3a0b0e839f8a4f4063f4ac",MW34_CONTROL_OBJECT_SHA,"2ff6fb125e0abae0b125f0e00e430cf5e8e4a0ab3a22b1c1eb9fefcb65c8175a"}});
  r.register_service({{ci::slot},{Abi::Cdecl,8,true},&control_provider_adapter,"Independent actual staged control provider",Domain::admitted_game,fd::provider_sha,"b75abde48029efcdb8cb123c163c6bfb27a9b76dc62da014e620fca7c95bac56"});
  r.cpu().esp=frame+4;r.cpu().eip=Runtime::external_return;r.freeze_registry();
 }
 ~ReviewFixture(){review_fixture=nullptr;matherr_binding=nullptr;control_binding=nullptr;ci::owner=nullptr;mn::owner=nullptr;owner=nullptr;}
 Job call(){Job job;job.entry_context=entry_context.get();review_fixture=this;matherr_binding=matherr.get();control_binding=control.get();review_boundary(job,row,"entry",review_scenarios);review_fixture=nullptr;matherr_binding=nullptr;control_binding=nullptr;
  review_need(job.denied&&r.poisoned(),"Actual required next dependency or real compiled fault terminally poisons root");review_need(!ci::owner&&!mn::owner&&!owner&&!matherr->context.active&&!control->context.active&&!control->context.boundary_depth,"Every typed owner and C++ entered boundary clears after root catch");last_job=job;
  snapshot(r,row,"independent-after");calls_output(row/"calls.json",r);raw_output(row/"control-events.bin",control->context.events);raw_output(row/"control-accesses.bin",control->context.accesses);
  std::array<unsigned,12>status{mode,control->context.count,control->context.access_count,control->context.depth,control->context.boundary_depth,unsigned(control->context.active),unsigned(control->context.failed),unsigned(control->context.complete),control->context.fault_pc,control->context.fault_address,job.fault_pc,job.fault_target};raw_output(row/"control-status.bin",status);
  std::ofstream why(row/"control-reason.txt");why<<(control->context.reason?control->context.reason:"")<<'\n';review_need(bool(why),"First diagnostic retained in actual capture");return job;
 }
 void retry(){auto&c=control->context;auto state=c.state;auto fx=std::array<std::byte,512>{};std::copy(r.fx().begin(),r.fx().end(),fx.begin());const auto pages=review_pages(r);const auto frames=c.frames;const auto events=c.events;const auto accesses=c.accesses;const auto count=c.count,ac=c.access_count,depth=c.depth;const auto pc=c.fault_pc,addr=c.fault_address;const auto*why=c.reason;const auto calls=r.calls().size(),outerevents=entry_context->events().size();const auto cwfault=c.cw.fault();const auto cwaddr=c.cw.fault_address();auto beforecpu=r.cpu();bool denied{};
  try{entry_context->invoke();}catch(const Fault&f){denied=f.reason()==FaultReason::poisoned;}
  review_need(denied&&!std::memcmp(&state,&c.state,3504)&&std::equal(fx.begin(),fx.end(),r.fx().begin())&&pages==review_pages(r)&&!std::memcmp(&beforecpu,&r.cpu(),sizeof(beforecpu)),"Poisoned retry cannot alter full State/FX/14 pages/runtime CPU");
  review_need(count==c.count&&ac==c.access_count&&depth==c.depth&&pc==c.fault_pc&&addr==c.fault_address&&why==c.reason&&!std::memcmp(frames.data(),c.frames.data(),sizeof(frames))&&!std::memcmp(events.data(),c.events.data(),sizeof(events))&&!std::memcmp(accesses.data(),c.accesses.data(),sizeof(accesses))&&calls==r.calls().size()&&outerevents==entry_context->events().size()&&c.cw.fault()==cwfault&&c.cw.fault_address()==cwaddr,"Terminal retry preserves partial frames/accesses, first native/CW diagnostics and ledgers");
 }
 void positive(){const auto job=call();auto&c=control->context;
  review_need(job.fault_reason==static_cast<unsigned>(FaultReason::unresolved_translation)&&job.fault_pc==0x5ac440&&job.fault_target==0x5ac598,"Actual source continuation stops at next argv helper");
  review_need(matherr->context.complete&&c.complete&&!c.failed&&c.count==13&&!c.depth&&!c.boundary_depth,"Actual compiled matherr, wrapper and four provider bodies close all semantic frames");
  const auto expected=static_cast<unsigned short>(((guest_word?guest_word:initial_cw)&~0x300U)|0x200U);review_need(c.state.x87.fxsave.cwd.flat==expected&&review_get<unsigned short>(r.fx().data())==expected,"Actual wrapper selects PC53 and carries incoming CW bits in State and separate FX");
  review_need(r.calls().size()==8&&!r.calls()[0].completed,"Actual root remains incomplete after new completed wrapper and named control import");for(unsigned i=1;i<8;++i)review_need(r.calls()[i].completed,"Every actual reached child route completed");
  review_need(r.calls()[6].site.value==0x5ac431&&r.calls()[6].target.value==ci::wrapper&&r.calls()[6].return_pc.value==0x5ac436&&!r.calls()[6].import&&r.calls()[7].site.value==0x5ac5aa&&r.calls()[7].target.value==ci::slot&&r.calls()[7].return_pc.value==ci::provider_return&&r.calls()[7].import,"True game CALL and CDECL import call frames recorded");retry();
 }
};
void review_before(ci::Context&c,unsigned target){
 review_need(review_fixture&& &review_fixture->control->context==&c,"Independent live observer exact owner");auto&f=*review_fixture;const auto mode=f.mode;
 if(target==ci::wrapper){
  if(f.guest_word){c.state.x87.fxsave.cwd.flat=static_cast<unsigned short>(f.guest_word);review_put<unsigned short>(c.runtime.fx().data(),static_cast<unsigned short>(f.guest_word));}
  if(mode==1)throw std::runtime_error("Independent wrapper observation throw");
  if(mode==2)c.state.x87.fxsave.cwd.flat^=0x100;
  if(mode==3){c.state.x87.fxsave.swd.flat=1;c.runtime.fx()[2]=std::byte{1};}
  if(mode==4){c.state.x87.fxsave.ftw.flat=1;c.runtime.fx()[4]=std::byte{1};}
  if(mode==5)c.state.addr.ds_base.dword=4;
  if(mode==6)c.memory.store<unsigned>({c.state.gpr.rsp.dword},ci::outer_return^1);
 }
 if(target==ci::provider_entry){
  if(mode==9||mode==10){const auto a=mode==9?ci::provider_entry:0x7801129bU;auto old=c.memory.load<unsigned char>({a});c.memory.protect({a&~4095U},Permissions::read|Permissions::write);c.memory.store<unsigned char>({a},old^1);}
  if(mode==11)c.memory.protect({0x20001000},Permissions::read);
  if(mode==12)throw std::runtime_error("Independent nested provider observation throw");
 }
}
void review_access(ci::Context&c,unsigned count){auto&f=*review_fixture;const auto&v=c.accesses[count-1];
 if(f.mode==13&&v.pc==0x5ac5a5&&v.write){c.memory.store<unsigned>({v.address},v.value^1);++f.trigger_count;}
 if(f.mode==14&&v.pc==0x780042fd&&v.width==2&&v.write){review_put<unsigned short>(c.runtime.fx().data(),c.state.x87.fxsave.cwd.flat^0x100);++f.trigger_count;}
 if(f.mode==15&&v.pc==0x780042fd&&v.width==2&&v.write){c.memory.protect({0x20001000},Permissions::read);++f.trigger_count;}
 if(f.mode==16&&v.pc==0x78004324&&v.width==2&&!v.write){c.deny("Independent post-FLDCW required bridge denial",v.address);}
 if(f.mode==17&&v.address==ci::slot&&!v.write){c.memory.protect({ci::slot&~4095U},Permissions::read|Permissions::write);c.memory.store<unsigned>({ci::slot},v.value^1);++f.trigger_count;}
 if(f.mode==18&&count==1){c.access_count=256;++f.trigger_count;}
 if(f.mode==19&&v.pc==0x780042fd&&v.width==2&&v.write)c.deny("Independent post-FNSTCW required bridge denial",v.address);
}
void review_event(ci::Context&c,unsigned count){auto&f=*review_fixture;const auto&v=c.events[count-1];
 if(f.mode==7&&v.kind==1&&v.pc==ci::wrapper){c.memory.protect({0x20001000},Permissions::read);++f.trigger_count;}
 if(f.mode==20&&v.kind==5){c.memory.store<unsigned>({c.frames[0].esp},c.frames[0].return_pc^1);++f.trigger_count;}
 if(f.mode==21&&v.kind==5){c.state.gpr.rbx.dword^=1;++f.trigger_count;}
 if(f.mode==22&&v.kind==1&&v.pc==ci::wrapper){c.count=16;++f.trigger_count;}
 if(f.mode==23&&v.kind==1&&v.pc==ci::provider_entry){c.memory.store<unsigned>({c.frames[1].esp},c.frames[1].return_pc^1);++f.trigger_count;}
}
void review_after(ci::Context&c){auto&f=*review_fixture;if(f.mode==24){review_need(c.complete&&!c.active&&!c.boundary_depth,"Actual compiled closure finishes before after-observer failure");review_need(std::filesystem::create_directory(f.row/"control-after"),"Fresh independent deliberate catch-checkpoint failure");throw std::runtime_error("Independent control after-observer exception");}}
void review_negative(unsigned mode){ReviewFixture f(mode);const auto job=f.call();auto&c=f.control->context;
 review_need(job.fault_pc!=0x5ac440||job.fault_target!=0x5ac598,"Independent causal control stops before clean next dependency");review_need((mode==24?c.complete:!c.complete)&&!f.r.calls()[6].completed,"Actual wrapper ledger remains incomplete through required failure");
 if(mode==1)review_need(!c.failed&&!c.count&&!c.active&&!c.boundary_depth,"Wrapper observer exception unwinds before any game control instruction");
 else if(mode==12)review_need(c.failed&&c.count==3&&c.depth==1&&!c.active&&!c.boundary_depth&&c.fault_pc==ci::provider_entry&&std::string(c.reason)=="Required typed control import route fault","Nested provider observer exception closes both C++ boundaries and preserves outer required-route diagnostic");
 else if(mode==24)review_need(!c.failed&&!c.active&&!c.boundary_depth&&f.r.calls()[7].completed,"After-observer and catch-checkpoint exceptions leave control owner/boundaries clear and real provider complete");
 else review_need(c.failed&&c.reason,"Real generated bridge/frame denial retains first typed diagnostic");
 if(mode==2||mode==14)review_need(c.cw.fault()==m4_guest_cw::Fault::unsupported_state&&c.fault_pc==(mode==2?0x780042fdU:0x78004324U),"Actual FNSTCW/FLDCW incoherence rejects at exact source transfer");
 if(mode==3||mode==4)review_need(c.fault_pc==0x780042fc&&std::string(c.reason)=="Unsupported connected FWAIT pending/nonempty state","Real FWAIT source requires clean empty guest state");
 if(mode==7)review_need(c.fault_pc==0x5ac5a0&&c.fault_address==frame-144,"First actual wrapper PUSH fails at owned stack address");
 if(mode==9||mode==10)review_need(c.fault_pc==ci::provider_entry&&std::string(c.reason)=="Exact connected provider source identity changed","Exact hot/cold source identity checked before first provider guest access");
 if(mode==13)review_need(c.fault_pc==ci::thunk&&std::string(c.reason)=="Actual wrapper CALL/arguments/thunk frame rejected","Actual pushed argument corruption detected at compiled thunk entry");
 if(mode==16||mode==19)review_need(c.fault_pc==(mode==16?0x78004324U:0x780042fdU)&&c.fault_address&&c.depth==3,"Required bridge abort after real CW transfer retains exact nested source/operand and partial semantic frames");
 if(mode==20||mode==21||mode==23)review_need(std::string(c.reason)=="Actual connected RET/nonvolatile/cleanup rejected","Actual compiled RET closes source return and nonvolatile frame");
 if(mode==22)review_need(std::string(c.reason)=="Connected actual route ledger overflow","Actual typed route bound fails during later game thunk event");
 f.control->extra_before=nullptr;f.control->extra_access=nullptr;f.control->extra_event=nullptr;f.control->extra_after=nullptr;if(mode==7||mode==11||mode==15)f.r.memory().protect({0x20001000},Permissions::read|Permissions::write);f.retry();
}
void review_bad_tokens(){ReviewFixture f;auto&c=f.control->context;ci::Context stale(f.r,c.state);const auto state=c.state;auto fx=std::array<std::byte,512>{};std::copy(f.r.fx().begin(),f.r.fx().end(),fx.begin());const auto pages=review_pages(f.r);
 auto invoke=[&](unsigned bridge,void*p){switch(bridge){case 0:(void)__remill_read_memory_32(p,ci::slot);break;case 1:(void)__remill_write_memory_32(p,frame,0x12345678);break;case 2:(void)__remill_function_return(&c.state,ci::outer_return,p);break;case 3:(void)__remill_jump(&c.state,c.raw_iat,p);break;case 4:(void)mw34_ci_enter(&c.state,ci::wrapper,p);break;case 5:(void)mw34_cf_enter(&c.state,ci::provider_entry,p);break;case 6:(void)mw34_cf_wait(&c.state,0x780042fc,p);break;case 7:(void)mw34_cf_store_cw(&c.state,frame,p);break;case 8:(void)mw34_cf_load_cw(&c.state,frame,p);break;case 9:(void)__remill_function_call(&c.state,0x5bb50c,p);break;case 10:(void)mw34_crte_direct(&c.state,ci::wrapper,p);break;case 11:(void)mw34_crte_enter(&c.state,entry,p);break;}};
 owner=f.entry_context.get();ci::owner=&c;
 for(void*wrong:{static_cast<void*>(nullptr),reinterpret_cast<void*>(std::uintptr_t{1}),static_cast<void*>(f.entry_context.get()),static_cast<void*>(&f.matherr->context),static_cast<void*>(&stale)})for(unsigned bridge=0;bridge<12;++bridge){bool denied{};try{invoke(bridge,wrong);}catch(const std::exception&e){denied=std::string(e.what()).find("Exact ")==0;}review_need(denied,"Null/arbitrary/stale/outer/matherr token refused before typed interpretation");++review_malformed;review_need(!std::memcmp(&state,&c.state,3504)&&std::equal(fx.begin(),fx.end(),f.r.fx().begin())&&pages==review_pages(f.r)&&!c.failed&&!c.complete&&!c.active&&!c.depth&&!c.count&&!c.access_count&&f.entry_context->events().empty(),"Malformed nested dispatch changes no State/FX/page/progress/first fault");}
 mn::owner=&f.matherr->context;
 for(unsigned bridge=0;bridge<12;++bridge){bool denied{};try{invoke(bridge,bridge>=9?static_cast<void*>(f.entry_context.get()):static_cast<void*>(&c));}catch(const std::exception&e){denied=std::string(e.what()).find("Exact ")==0;}review_need(denied,"Conflicting current control/matherr nesting refuses even otherwise correct opaque token");++review_malformed;}
 mn::owner=nullptr;ci::owner=nullptr;owner=nullptr;review_need(!c.failed&&!c.count&&!c.access_count&&!std::memcmp(&state,&c.state,3504)&&pages==review_pages(f.r),"All unentered malformed token denials retain pristine service Context");f.positive();
}
void review_run(){for(unsigned index:{0U,5U,11U,12U,17U,23U}){ReviewFixture f(0,index);f.positive();}
 // These are native-only controlled CW fixtures after source FDIV, not
 // additional original hardware equivalence inputs.
 for(unsigned word:{0x37fU,0x27fU,0x77fU,0xa7fU,0xf7fU,0x67fU}){ReviewFixture f;f.guest_word=word;f.positive();}
 for(unsigned mode:{1U,2U,3U,4U,5U,6U,7U,9U,10U,11U,12U,13U,14U,15U,16U,17U,18U,19U,20U,21U,22U,23U,24U})review_negative(mode);
 review_bad_tokens();
}
}
int main(int argc,char**argv){try{
 review_need(argc==7,"Exact game entryobject provider FDIVpack originalBEFORE freshout");review_game=read_file(argv[1]);review_object=read_file(argv[2]);review_provider=read_file(argv[3]);review_pack=read_file(argv[4]);review_inputs=read_file(argv[5]);review_worker=read_file(argv[0]);review_directory=argv[6];
 review_need(m4::sha256(review_game)==m4::admitted_image_hash&&m4::sha256(review_provider)==fd::provider_sha&&m4::sha256(review_object)==MW34_ENTRY_OBJECT_SHA&&m4::sha256(review_inputs)==MW34_REPLAY_INPUT_SHA,"Exact original-BEFORE and actual linked entry source identity");review_need(!std::filesystem::exists(review_directory)&&std::filesystem::create_directory(review_directory),"Entirely fresh independent execution directory");review_run();
 std::ofstream f(review_directory/"controls.json");f<<"{\"passed\":true,\"checks\":"<<review_checks<<",\"scenarios\":"<<review_scenarios<<",\"malformed_token_denials\":"<<review_malformed<<",\"ordinary_game_launched\":false,\"original_executed\":false,\"whole_M4_complete\":false}\n";review_need(bool(f),"Independent actual report complete");std::cout<<review_checks<<" independent compiled checks / "<<review_scenarios<<" scenarios passed\n";return 0;
}catch(const std::exception&e){review_fixture=nullptr;matherr_binding=nullptr;control_binding=nullptr;ci::owner=nullptr;mn::owner=nullptr;owner=nullptr;std::cerr<<e.what()<<'\n';return 1;}}
