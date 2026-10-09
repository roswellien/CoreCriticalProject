// Independently authored fixtures on the complete production composition.
// Exclude only CLI main; preserve all Contexts, adapters and typed dispatch.
#define MW34_ENTRY_INITTERM_NO_MAIN
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
struct ReviewFixture;
thread_local ReviewFixture*review_fixture{};
void review_before(nt::Context&,unsigned);void review_access(nt::Context&,unsigned);void review_event(nt::Context&,unsigned);void review_after(nt::Context&);
struct ReviewFixture {
 Runtime r;std::unique_ptr<m4_crt::Session>crt;std::unique_ptr<fd::Registry>fdiv;std::unique_ptr<MatherrBinding>matherr;std::unique_ptr<ControlBinding>control;std::unique_ptr<InitermBinding>initterm;std::unique_ptr<Context>entry_context;
 std::filesystem::path row;unsigned mode{},trigger_count{};Job last_job{};
 explicit ReviewFixture(unsigned which=0,unsigned index=0):r([&]{Policy p;p.stack_low={0x20001000};p.stack_bytes=4096;p.heap_bytes=4096;return Runtime::from_admitted_image(review_game,p);}()),mode(which){
  ++review_scenarios;row=review_directory/("case-"+std::to_string(review_scenarios));review_need(std::filesystem::create_directory(row),"Fresh actual independent row");checkpoint_directory=row;
  crt=std::make_unique<m4_crt::Session>(r,review_provider,m4_crt::Proof{Domain::admitted_game,m4::sha256(review_worker),"09a6018bb2cd3a6daf79786ee0bd2485b25f6b8c78740a352989019a2511e42a"});
  Input in{};std::memcpy(&in,review_inputs.data()+24+index*sizeof(Input),sizeof(in));seed(r,in);
  for(auto address:matherr_pages){const auto page=provider_raw_page(review_provider,address);r.memory().map({address},4096,Permissions::read|Permissions::write);r.memory().write({address},page);if(address==matherr_pages[0])r.memory().protect({address},Permissions::read|Permissions::execute);}
  {const auto page=provider_raw_page(review_provider,0x78001000);r.memory().map({0x78001000},4096,Permissions::read|Permissions::write);r.memory().write({0x78001000},page);r.memory().protect({0x78001000},Permissions::read|Permissions::execute);}
  fdiv=std::make_unique<fd::Registry>(r);review_need(fdiv->admit(review_provider,review_pack),"Exact source FDIV admission");Job writer;writer.writer=fdiv.get();review_boundary(writer,row,"writer",review_scenarios);review_need(writer.ok&&fdiv->ready(),"Actual source producer completes before same-State entry");
  auto state=std::array<std::byte,3504>{};std::copy(r.remill_state().begin(),r.remill_state().end(),state.begin());auto fx=std::array<std::byte,512>{};std::copy(r.fx().begin(),r.fx().end(),fx.begin());
  matherr=std::make_unique<MatherrBinding>(r,review_provider,0);control=std::make_unique<ControlBinding>(r,0);initterm=std::make_unique<InitermBinding>(r,review_game,review_provider,0);entry_context=std::make_unique<Context>(r,*fdiv,m4::sha256(review_object));
  review_need(std::equal(state.begin(),state.end(),r.remill_state().begin())&&std::equal(fx.begin(),fx.end(),r.fx().begin()),"All Contexts borrow every persistent State/FX byte without reseed");
  initterm->extra_before=&review_before;initterm->extra_access=&review_access;initterm->extra_event=&review_event;initterm->extra_after=&review_after;
  r.register_service({{matherr->context.slot},{Abi::Cdecl,4,true},&matherr_adapter,"Independent actual game matherr",Domain::admitted_game,fd::provider_sha,"72dabe5c1616590b1fe624844914b6d21fab26cf8eb8ddc3d430de98f50adce4"});
  r.register_translation({{ci::wrapper},{Abi::Cdecl,0,true},&control_wrapper_adapter,"Independent actual game control wrapper",{Domain::admitted_game,m4::admitted_image_hash,19,"ae1fa42ecf74ee2fb8a6076d57a6d7cb51e91890df3a0b0e839f8a4f4063f4ac",MW34_CONTROL_OBJECT_SHA,"2ff6fb125e0abae0b125f0e00e430cf5e8e4a0ab3a22b1c1eb9fefcb65c8175a"}});
  r.register_service({{ci::slot},{Abi::Cdecl,8,true},&control_provider_adapter,"Independent actual staged control provider",Domain::admitted_game,fd::provider_sha,"b75abde48029efcdb8cb123c163c6bfb27a9b76dc62da014e620fca7c95bac56"});
  r.register_translation({{nt::thunk},{Abi::Cdecl,8,true},&initterm_thunk_adapter,"Independent actual first initterm thunk",{Domain::admitted_game,m4::admitted_image_hash,6,"86127a1a5240eff849fe402fc8517ae3ead7498476c8f17188afd36be6060947",MW34_ENTRY_OBJECT_SHA,MW34_INITTERM_SOURCE_SHA}});
  r.cpu().esp=frame+4;r.cpu().eip=Runtime::external_return;r.freeze_registry();
 }
 ~ReviewFixture(){review_fixture=nullptr;matherr_binding=nullptr;control_binding=nullptr;initterm_binding=nullptr;nt::owner=nullptr;ci::owner=nullptr;mn::owner=nullptr;owner=nullptr;}
 Job call(){Job job;job.entry_context=entry_context.get();review_fixture=this;matherr_binding=matherr.get();control_binding=control.get();initterm_binding=initterm.get();review_boundary(job,row,"entry",review_scenarios);review_fixture=nullptr;matherr_binding=nullptr;control_binding=nullptr;initterm_binding=nullptr;
  review_need(job.denied&&r.poisoned(),"Actual required dependency or compiled fault terminally poisons root");review_need(!nt::owner&&!ci::owner&&!mn::owner&&!owner&&!matherr->context.active&&!control->context.active&&!control->context.boundary_depth&&!initterm->context.active&&!initterm->context.boundary_depth,"Every typed owner and C++ boundary clears after root catch");last_job=job;
  snapshot(r,row,"independent-after");calls_output(row/"calls.json",r);auto&c=initterm->context;raw_output(row/"initterm-events.bin",c.events);raw_output(row/"initterm-accesses.bin",c.accesses);
  std::array<unsigned,18>status{mode,c.frame,c.ret,c.first,c.last,c.access_count,c.provider_step,c.event_count,c.boundary_depth,unsigned(c.active),unsigned(c.failed),unsigned(c.complete),unsigned(c.provider_complete),c.fault_pc,c.fault_address,job.fault_reason,job.fault_pc,job.fault_target};raw_output(row/"initterm-status.bin",status);
  fresh_output(row/"initterm-undefined.bin",{reinterpret_cast<const std::byte*>(c.undefined_sites.data()),c.undefined_sites.size()*sizeof(unsigned)});std::ofstream why(row/"initterm-reason.txt");why<<(c.reason?c.reason:"")<<'\n';review_need(bool(why),"Actual first typed diagnostic retained");return job;
 }
 void retry(){auto&c=initterm->context;auto state=c.state;auto fx=std::array<std::byte,512>{};std::copy(r.fx().begin(),r.fx().end(),fx.begin());const auto pages=review_pages(r);const auto events=c.events;const auto accesses=c.accesses;const auto undefined=c.undefined_sites;const auto nv=c.nonvolatile;
  const auto ac=c.access_count,step=c.provider_step,ec=c.event_count,pc=c.fault_pc,addr=c.fault_address;const auto*why=c.reason;const auto calls=r.calls().size(),outerevents=entry_context->events().size(),routes=entry_context->data_routes().size();auto beforecpu=r.cpu();bool denied{};
  try{entry_context->invoke();}catch(const Fault&f){denied=f.reason()==FaultReason::poisoned;}
  review_need(denied&&!std::memcmp(&state,&c.state,3504)&&std::equal(fx.begin(),fx.end(),r.fx().begin())&&pages==review_pages(r)&&!std::memcmp(&beforecpu,&r.cpu(),sizeof(beforecpu)),"Poisoned retry cannot alter full State/FX/16 pages/runtime CPU");
  review_need(ac==c.access_count&&step==c.provider_step&&ec==c.event_count&&pc==c.fault_pc&&addr==c.fault_address&&why==c.reason&&nv==c.nonvolatile&&undefined==c.undefined_sites&&!std::memcmp(events.data(),c.events.data(),sizeof(events))&&!std::memcmp(accesses.data(),c.accesses.data(),sizeof(accesses))&&calls==r.calls().size()&&outerevents==entry_context->events().size()&&routes==entry_context->data_routes().size()&&!c.active&&!c.boundary_depth,"Retry preserves partial source accesses/events, first diagnostic, ownership and ledgers");
 }
 void positive(){const auto job=call();auto&c=initterm->context;
  review_need(job.fault_reason==static_cast<unsigned>(FaultReason::unresolved_import)&&job.fault_pc==0x5ac468&&job.fault_target==0x5bb514,"Actual source continuation stops at next unresolved initializer-range import");
  review_need(matherr->context.complete&&control->context.complete&&c.complete&&c.provider_complete&&!c.failed&&c.access_count==8&&c.provider_step==7&&c.event_count==6&&!c.active&&!c.boundary_depth,"Actual compiled prior bodies, thunk and complete null-only provider close");
  review_need(c.frame==frame-148&&c.ret==nt::return_pc&&c.first==nt::begin&&c.last==nt::end&&c.undefined_sites==std::vector<unsigned>{0x7800150a},"Actual first null interval and sole TEST AF representative carried");
  review_need(c.accesses[0].pc==nt::thunk&&c.accesses[0].address==nt::slot&&c.accesses[1].pc==nt::entry&&c.accesses[1].address==c.frame-4&&c.accesses[1].write&&c.accesses[4].pc==0x78001508&&!c.accesses[4].value&&c.accesses[6].pc==0x78001512&&c.accesses[7].pc==0x78001513,"Actual generated thunk/PUSH/table/POP/RET bridge sequence");
  review_need(r.calls().size()==10&&!r.calls()[0].completed,"Actual root remains incomplete after new thunk/provider");for(unsigned i=1;i<10;++i)review_need(r.calls()[i].completed,"Every actual reached child route completed");
  review_need(r.calls()[8].site.value==0x5ac440&&r.calls()[8].target.value==nt::thunk&&r.calls()[8].return_pc.value==nt::return_pc&&!r.calls()[8].import&&r.calls()[9].site.value==nt::thunk&&r.calls()[9].target.value==nt::slot&&r.calls()[9].return_pc.value==nt::return_pc&&r.calls()[9].import,"Real game CALL, thunk tail and named CDECL import recorded");retry();
 }
};
void review_before(nt::Context&c,unsigned target){review_need(review_fixture&& &review_fixture->initterm->context==&c,"Independent live observer exact typed owner");auto&f=*review_fixture;
 if(target==nt::thunk){
  if(f.mode==1)throw std::runtime_error("Independent thunk observer exception");
  if(f.mode==4)mutation(c.runtime,nt::entry,0);
  if(f.mode==6)mutation(c.runtime,nt::thunk,0);
  if(f.mode==18)c.state.addr.ds_base.dword=4;
  if(f.mode==19)c.state.addr.ss_base.dword=4;
 }
 if(target==nt::entry){
  if(f.mode==2)throw std::runtime_error("Independent provider observer exception");
  if(f.mode==3)c.runtime.memory().protect({0x20001000},Permissions::read);
  if(f.mode==5)mutation(c.runtime,nt::entry,0);
  if(f.mode==11||f.mode==17)c.runtime.memory().store<unsigned>({nt::begin},0x51e7b0);
 }
}
void review_access(nt::Context&c,unsigned count){auto&f=*review_fixture;const auto&v=c.accesses[count-1];
 if(f.mode==7&&v.pc==nt::thunk){mutation(c.runtime,nt::slot,v.value^1);++f.trigger_count;}
 if(f.mode==8&&v.pc==0x780014f9){c.state.gpr.rsp.dword=0x20001ffc;++f.trigger_count;}
 if(f.mode==9&&v.pc==0x78001512){c.runtime.memory().store<unsigned>({c.frame},c.ret^1);++f.trigger_count;}
 if(f.mode==10&&v.pc==0x78001513){c.state.gpr.rsi.dword^=1;++f.trigger_count;}
 if(f.mode==12&&v.pc==0x78001502&&c.provider_step==3){c.runtime.memory().store<unsigned>({c.frame+8},nt::end+4);++f.trigger_count;}
 const unsigned denied_pc=f.mode==13?nt::entry:f.mode==14?0x780014f9U:f.mode==15?0x78001512U:f.mode==16?0x78001513U:f.mode==17?0x7800150eU:0U;
 if(denied_pc&&v.pc==denied_pc){++f.trigger_count;c.deny("Independent required access callback abort",v.address);}
 if(f.mode==21&&v.pc==nt::thunk){c.access_count=32;++f.trigger_count;}
}
void review_event(nt::Context&c,unsigned count){auto&f=*review_fixture;const auto&v=c.events[count-1];
 if(f.mode==20&&v.kind==1){c.event_count=16;++f.trigger_count;}
 if(f.mode==22&&v.kind==5){c.state.gpr.rsp.dword^=4;++f.trigger_count;}
 if(f.mode==24&&v.kind==4)throw std::runtime_error("Independent null-table observer exception");
}
void review_after(nt::Context&c){auto&f=*review_fixture;if(f.mode==23){review_need(c.complete&&c.provider_complete&&!c.active&&!c.boundary_depth,"Real thunk/provider close before after-observer exception");review_need(std::filesystem::create_directory(f.row/"initterm-thunk-after"),"Fresh independent deliberate catch-checkpoint failure");throw std::runtime_error("Independent initterm after-observer exception");}}
void review_negative(unsigned mode){ReviewFixture f(mode);const auto job=f.call();auto&c=f.initterm->context;
 review_need(job.fault_pc!=0x5ac468||job.fault_target!=0x5bb514,"Causal control refuses before clean next source dependency");review_need((mode==23?c.complete:!c.complete)&&!f.r.calls()[8].completed,"Actual thunk route remains incomplete through required failure");
 if(mode==1)review_need(!c.failed&&!c.access_count&&!c.event_count,"Before-thunk observer unwinds without guest access or POD diagnostic");
 else if(mode==23)review_need(!c.failed&&f.r.calls()[9].completed,"After-observer plus catch-checkpoint exceptions retain real completed provider");
 else review_need(c.failed&&c.reason,"Actual bridge or routed observer fault preserves first typed POD diagnostic");
 if(mode==2)review_need(c.fault_pc==nt::entry&&c.fault_address==nt::slot&&c.access_count==1&&c.event_count==2&&std::string(c.reason)=="Required actual initterm provider route fault","Provider observer exception unwinds both boundaries and retains routed diagnostic");
 if(mode==3)review_need(c.fault_pc==nt::entry&&c.fault_address==c.frame-4&&c.state.gpr.rsp.dword==c.frame&&c.access_count==1,"Failed actual first PUSH store preserves old pre-publication ESP");
 if(mode==4||mode==6)review_need(c.fault_pc==nt::thunk&&!c.access_count&&std::string(c.reason)=="Exact initterm thunk/provider source identity","Exact thunk/provider code identity rejects before compiled IAT read");
 if(mode==5)review_need(c.fault_pc==nt::return_pc&&c.access_count==8&&!c.provider_complete&&std::string(c.reason)=="Exact initterm thunk/provider source identity","Independent late provider byte mutation refuses actual RET identity closure");
 if(mode==7)review_need(c.fault_pc==c.raw&&c.access_count==1&&std::string(c.reason)=="Actual initterm import tail/raw IAT/frame rejected","Actual thunk IAT read then mutated slot denied at source tail");
 if(mode==8)review_need(c.fault_pc==0x78001502&&c.fault_address==(MW34_REVIEW_OPTIMIZED?c.frame+8:0x20002008U)&&c.access_count==3&&c.state.gpr.rsp.dword==0x20001ffc,"Actual MOV then changed-State CMP operand fails at exact source PC and optimizer-specific address");
 if(mode==9)review_need(c.fault_pc==0x78001513&&c.fault_address==c.frame&&c.state.gpr.rsp.dword==c.frame&&c.access_count==7,"Actual POP publishes ESP before subsequent RET-word read denial");
 if(mode==10)review_need(c.fault_pc==nt::return_pc&&c.access_count==8&&c.state.gpr.rsp.dword==c.frame+4&&std::string(c.reason)=="Actual initterm RET/nonvolatile/stack closure","Actual RET publishes return PC/ESP before nonvolatile closure denial");
 if(mode==11)review_need(c.fault_pc==0x7800150e&&c.fault_address==0x51e7b0&&c.state.gpr.rsp.dword==c.frame-8&&c.state.gpr.rip.dword==0x51e7b0&&f.r.memory().load<unsigned>({c.frame-8})==0x78001510&&std::string(c.reason)=="Required initterm callback remains unreviewed","Complete static nonnull CALL path writes return and publishes target then refuses before callback");
 if(mode==12)review_need(c.fault_pc==0x78001508&&c.fault_address==nt::begin+4&&c.access_count==6&&c.provider_step==5,"Mutated end reaches real ADD/CMP then refuses second table operand");
 if(mode>=13&&mode<=17){const unsigned pc=mode==13?nt::entry:mode==14?0x780014f9U:mode==15?0x78001512U:mode==16?0x78001513U:0x7800150eU;const unsigned esp=(mode==13||mode==15||mode==16)?c.frame:c.frame-4;review_need(c.fault_pc==pc&&c.state.gpr.rsp.dword==esp&&f.trigger_count==1&&std::string(c.reason)=="Independent required access callback abort","Actual checked bridge C++ abort preserves exact PUSH/CALL pre-publication or POP post-publication state");}
 if(mode==18||mode==19)review_need(c.fault_pc==nt::thunk&&!c.access_count&&std::string(c.reason)=="Initterm thunk State/segment identity","Typed thunk exact current segment identity refuses before first IAT read");
 if(mode==20)review_need(c.fault_pc==c.raw&&c.access_count==1&&c.event_count==16&&std::string(c.reason)=="Initterm route bound","Actual tail event bound fails without entering provider");
 if(mode==21)review_need(c.fault_pc==nt::entry&&c.fault_address==c.frame-4&&c.access_count==32&&c.state.gpr.rsp.dword==c.frame&&std::string(c.reason)=="Initterm access bound","Actual PUSH write commits memory then record bound refuses before ESP publication");
 if(mode==22)review_need(c.provider_complete&&c.fault_pc==nt::return_pc&&c.fault_address==nt::slot&&std::string(c.reason)=="Required actual initterm provider route fault","Post-RET observer ESP mutation fails real CDECL closure with typed first fault");
 if(mode==24)review_need(c.fault_pc==0x78001508&&c.access_count==5&&std::string(c.reason)=="Required actual initterm provider route fault","Entered table observer C++ exception unwinds both boundaries and retains exact source prefix");
 f.initterm->extra_before=nullptr;f.initterm->extra_access=nullptr;f.initterm->extra_event=nullptr;f.initterm->extra_after=nullptr;if(mode==3)f.r.memory().protect({0x20001000},Permissions::read|Permissions::write);f.retry();
}
void review_bad_tokens(){ReviewFixture f;auto&c=f.initterm->context;nt::Context stale(f.r);const auto state=c.state;auto fx=std::array<std::byte,512>{};std::copy(f.r.fx().begin(),f.r.fx().end(),fx.begin());const auto pages=review_pages(f.r);
 auto invoke=[&](unsigned bridge,void*p){switch(bridge){case 0:(void)__remill_read_memory_32(p,nt::slot);break;case 1:(void)__remill_write_memory_32(p,frame,0x12345678);break;case 2:(void)__remill_function_return(&c.state,nt::return_pc,p);break;case 3:(void)__remill_jump(&c.state,c.raw,p);break;case 4:(void)mw34_ci_enter(&c.state,ci::wrapper,p);break;case 5:(void)mw34_cf_enter(&c.state,ci::provider_entry,p);break;case 6:(void)mw34_cf_wait(&c.state,0x780042fc,p);break;case 7:(void)mw34_cf_store_cw(&c.state,frame,p);break;case 8:(void)mw34_cf_load_cw(&c.state,frame,p);break;case 9:(void)__remill_function_call(&c.state,0x51e7b0,p);break;case 10:(void)mw34_crte_direct(&c.state,nt::thunk,p);break;case 11:(void)mw34_crte_enter(&c.state,nt::thunk,p);break;}};
 auto unchanged=[&]{return !std::memcmp(&state,&c.state,3504)&&std::equal(fx.begin(),fx.end(),f.r.fx().begin())&&pages==review_pages(f.r)&&!c.failed&&!c.complete&&!c.active&&!c.boundary_depth&&!c.used&&!c.provider_step&&!c.event_count&&!c.access_count&&c.undefined_sites.empty()&&f.entry_context->events().empty();};
 owner=f.entry_context.get();nt::owner=&c;
 for(void*wrong:{static_cast<void*>(nullptr),reinterpret_cast<void*>(std::uintptr_t{1}),static_cast<void*>(f.entry_context.get()),static_cast<void*>(&f.matherr->context),static_cast<void*>(&f.control->context),static_cast<void*>(&stale)})for(unsigned bridge=0;bridge<12;++bridge){bool denied{};try{invoke(bridge,wrong);}catch(const std::exception&e){denied=std::string(e.what()).find("Exact ")==0;}review_need(denied,"Null/arbitrary/stale/outer/control/matherr token refuses before typed interpretation");++review_malformed;review_need(unchanged(),"Malformed nested dispatch preserves full State/FX/16 pages/progress/first fault");}
 for(unsigned conflict=0;conflict<2;++conflict){ci::owner=conflict?nullptr:&f.control->context;mn::owner=conflict?&f.matherr->context:nullptr;for(unsigned bridge=0;bridge<12;++bridge){bool denied{};try{invoke(bridge,bridge==10?static_cast<void*>(f.entry_context.get()):static_cast<void*>(&c));}catch(const std::exception&e){denied=std::string(e.what()).find("Exact ")==0;}review_need(denied&&unchanged(),"Conflicting current nested owner refuses even otherwise correct opaque token");++review_malformed;}}
 mn::owner=nullptr;ci::owner=nullptr;nt::owner=nullptr;owner=nullptr;review_need(unchanged(),"Unentered typed token denials retain pristine compiled provider context");f.positive();
}
void review_run(){for(unsigned index:{0U,5U,11U,12U,17U,23U}){ReviewFixture f(0,index);f.positive();}for(unsigned mode=1;mode<=24;++mode)review_negative(mode);review_bad_tokens();}
}
int main(int argc,char**argv){try{
 review_need(argc==7,"Exact game entryobject provider FDIVpack originalBEFORE freshout");review_game=read_file(argv[1]);review_object=read_file(argv[2]);review_provider=read_file(argv[3]);review_pack=read_file(argv[4]);review_inputs=read_file(argv[5]);review_worker=read_file(argv[0]);review_directory=argv[6];
 review_need(m4::sha256(review_game)==m4::admitted_image_hash&&m4::sha256(review_provider)==fd::provider_sha&&m4::sha256(review_object)==MW34_ENTRY_OBJECT_SHA&&m4::sha256(review_inputs)==MW34_REPLAY_INPUT_SHA,"Exact original-BEFORE and linked literal source identities");review_need(!std::filesystem::exists(review_directory)&&std::filesystem::create_directory(review_directory),"Fresh independent execution directory");review_run();
 std::ofstream f(review_directory/"controls.json");f<<"{\"passed\":true,\"checks\":"<<review_checks<<",\"scenarios\":"<<review_scenarios<<",\"malformed_token_denials\":"<<review_malformed<<",\"ordinary_game_launched\":false,\"original_executed\":false,\"whole_M4_complete\":false}\n";review_need(bool(f),"Independent actual report complete");std::cout<<review_checks<<" independent compiled checks / "<<review_scenarios<<" scenarios passed\n";return 0;
}catch(const std::exception&e){review_fixture=nullptr;matherr_binding=nullptr;control_binding=nullptr;initterm_binding=nullptr;nt::owner=nullptr;ci::owner=nullptr;mn::owner=nullptr;owner=nullptr;std::cerr<<e.what()<<'\n';return 1;}}
