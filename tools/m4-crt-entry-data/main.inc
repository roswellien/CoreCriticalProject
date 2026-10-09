#include "observations.hpp"
struct alignas(16) Boundary {std::array<std::byte,512>fx;std::array<std::byte,28>env;};
struct Job {fd::Registry*writer{};Context*entry_context{};bool ok{},denied{};unsigned fault_reason{},fault_pc{},fault_target{};};
extern "C" bool data_boundary_call(Job*,Boundary*,Boundary*,const Boundary*);
extern "C" bool data_boundary_initialize(Job*j) noexcept {
 try {if(j->writer){j->ok=j->writer->initialize();return j->ok;}j->entry_context->invoke();j->ok=true;return true;}
 catch(const Fault&f){j->denied=true;j->fault_reason=static_cast<unsigned>(f.reason());j->fault_pc=f.site().value;j->fault_target=f.target().value;return false;}
 catch(...){j->denied=true;j->fault_reason=0xffffffffU;return false;}
}
namespace {
void restore_host(const Boundary&c){__asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(c.fx),"m"(c.env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
void boundary(Job&j,const std::filesystem::path&row,const char*name,unsigned scenario){
 Boundary saved{},before{},after{};__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(saved.fx),"=m"(saved.env)::"memory");restore_host(saved);
 auto seeded=saved;for(unsigned i=6;i<16;++i)for(unsigned k=0;k<16;++k)seeded.fx[160+16*i+k]=std::byte(static_cast<unsigned char>(i*31+k*17+scenario+1));
 (void)data_boundary_call(&j,&before,&after,&seeded);restore_host(saved);
 raw_output(row/(std::string(name)+"-host-before.bin"),before);raw_output(row/(std::string(name)+"-host-after.bin"),after);
 require(before.env==after.env,"Direct caller complete ENV28 retained");
 require(std::equal(before.fx.begin(),before.fx.begin()+5,after.fx.begin())&&std::equal(before.fx.begin()+24,before.fx.begin()+28,after.fx.begin()+24),"Direct caller CW/SW/FTW/MXCSR retained");
 for(unsigned i=0;i<8;++i)require(std::equal(before.fx.begin()+32+16*i,before.fx.begin()+42+16*i,after.fx.begin()+32+16*i),"Direct caller physical raw80 retained");
 for(unsigned i=6;i<16;++i)require(std::equal(before.fx.begin()+160+16*i,before.fx.begin()+176+16*i,after.fx.begin()+160+16*i),"Direct caller ABI XMM6..15 retained");
}
void calls_output(const std::filesystem::path&p,const Runtime&r){std::ofstream f(p);f<<"[";for(unsigned i=0;i<r.calls().size();++i){const auto&v=r.calls()[i];if(i)f<<",";f<<"{\"site\":"<<v.site.value<<",\"target\":"<<v.target.value<<",\"return_pc\":"<<v.return_pc.value<<",\"import\":"<<(v.import?"true":"false")<<",\"completed\":"<<(v.completed?"true":"false")<<"}";}f<<"]\n";require(bool(f),"Call capture complete");}
void mutation(Runtime&r,unsigned address,unsigned value){r.memory().protect({address&~4095U},Permissions::read|Permissions::write);r.memory().store<unsigned>({address},value);}
}
int main(int argc,char**argv){try{
 require(argc==7,"Composition: exact-game exact-entry-object exact-provider exact-pack before-inputs fresh-directory");
 auto image=fd::readfile(argv[1],2384384),object=read_file(argv[2]),provider=fd::readfile(argv[3],266293),pack=fd::readfile(argv[4],28740),inputs=fd::readfile(argv[5],211128);
 require(m4::sha256(image)==m4::admitted_image_hash&&m4::sha256(object)==MW34_ENTRY_OBJECT_SHA,"Exact admitted game and literal entry object");
 require(inputs.size()==211128&&m4::sha256(inputs)==MW34_REPLAY_INPUT_SHA&&std::memcmp(inputs.data(),"MW4FRIN1",8)==0,"Exact original BEFORE pack; no AFTER execution input");
 const std::filesystem::path directory=argv[6];require(!std::filesystem::exists(directory)&&std::filesystem::create_directory(directory),"Fresh output directory required");auto worker=read_file(argv[0]);
 for(unsigned scenario=0;scenario<36;++scenario){const auto mode=scenario<24?0:scenario-23;
  Input in{};std::memcpy(&in,inputs.data()+24+(scenario<24?scenario:0)*sizeof(Input),sizeof(Input));require(in.cpu.esp==fd::entry_esp&&in.cpu.eip==fd::writer,"Actual BEFORE source projection");
  auto row=directory/("row-"+std::to_string(scenario));require(std::filesystem::create_directory(row),"Fresh scenario");raw_output(row/"input.bin",in);
  Policy policy;policy.stack_low={0x20001000};policy.stack_bytes=4096;policy.heap_bytes=4096;auto r=Runtime::from_admitted_image(image,policy);
  m4_crt::Session crt(r,provider,{Domain::admitted_game,m4::sha256(worker),"09a6018bb2cd3a6daf79786ee0bd2485b25f6b8c78740a352989019a2511e42a"});seed(r,in);
  fd::Registry fdiv(r);require(fdiv.admit(provider,pack)&&!fdiv.ready(),"Admitted source data is uninitialized");
  if(mode==1){require(!fdiv.resolve_data({fd::game_iat}),"File zero cannot become initialized data before actual writer");}
  if(mode==2){reinterpret_cast<State*>(r.remill_state().data())->x87.fxsave.cwd.flat^=0x100;}
  if(mode==3){r.memory().protect({0x78037000},Permissions::read);}
  snapshot(r,row,"writer-before");std::array<std::byte,3504>before{};std::array<std::byte,512>fx{};std::array<std::byte,9*4096>memory{};
  std::copy(r.remill_state().begin(),r.remill_state().end(),before.begin());std::copy(r.fx().begin(),r.fx().end(),fx.begin());pages(r,memory);
  Job writer_job;writer_job.writer=&fdiv;SetLastError(0xaabb0000U+scenario);boundary(writer_job,row,"writer",scenario);
  auto receipt=writer_receipt(r,fdiv,in,before,fx,memory,writer_job.ok);raw_output(row/"writer-record.bin",receipt);snapshot(r,row,"writer-after");
  if(mode<=3&&mode){require(!writer_job.ok&&!fdiv.ready()&&fdiv.first_fault()&&fdiv.lookups().empty(),"Early causal writer fault before actual APIs");
   const auto f=*fdiv.first_fault();const auto old_state=std::array<std::byte,3504>{};auto state_copy=old_state;std::copy(r.remill_state().begin(),r.remill_state().end(),state_copy.begin());auto fx_copy=fx;std::copy(r.fx().begin(),r.fx().end(),fx_copy.begin());const auto event_count=fdiv.events().size();
   require(!fdiv.initialize()&&!fdiv.resolve_data({fd::game_iat})&&!fdiv.admit(provider,pack),"Required FDIV fault terminal on retry");require(std::equal(state_copy.begin(),state_copy.end(),r.remill_state().begin())&&std::equal(fx_copy.begin(),fx_copy.end(),r.fx().begin())&&event_count==fdiv.events().size()&&f.pc==fdiv.first_fault()->pc&&f.address==fdiv.first_fault()->address,"Writer failed prefix retained");snapshot(r,row,"retry-after");
   std::ofstream result(row/"result.json");result<<"{\"passed\":true,\"scenario\":"<<scenario<<",\"control\":"<<mode<<",\"writer_complete\":false,\"entry_executed\":false,\"fault_reason\":"<<static_cast<unsigned>(f.reason)<<",\"fault_site\":"<<f.pc<<",\"fault_target\":"<<f.address<<",\"poisoned_retry\":true,\"whole_M4_complete\":false}\n";require(bool(result),"Fault result output");continue;
  }
  require(writer_job.ok&&fdiv.ready()&&fdiv.lookups().size()==3,"Actual native writer and real OS query completed");
  const auto carried=*reinterpret_cast<State*>(r.remill_state().data());const auto carried_fx=fx;auto fx_after=carried_fx;std::copy(r.fx().begin(),r.fx().end(),fx_after.begin());
  Context context(r,fdiv,m4::sha256(object));require(!std::memcmp(&carried,r.remill_state().data(),3504)&&std::equal(fx_after.begin(),fx_after.end(),r.fx().begin()),"Context borrows full State and distinct FX without reseed");
  r.cpu().esp=frame+4;r.cpu().eip=Runtime::external_return;r.freeze_registry();
  if(mode==4)mutation(r,fd::writer,0);
  if(mode==5)mutation(r,fd::module_iat,0);
  if(mode==6)r.memory().store<unsigned>({fd::global},fdiv.lookups()[2].raw_result^1);
  if(mode==7)mutation(r,entry,0);
  if(mode==8)r.memory().store<unsigned>({fd::game_iat},fdiv.original_game_word()^1);
  if(mode==9)r.memory().store<unsigned>({0x5bb5a4},0);
  if(mode==10)r.memory().protect({0x20001000},Permissions::read);
  if(mode==11)r.memory().protect({0x9a1000},Permissions::read);
  if(mode==12)r.memory().protect({m4_crt::Session::provider_app_type},Permissions::read);
  snapshot(r,row,"entry-before-invoke");Job entry_job;entry_job.entry_context=&context;boundary(entry_job,row,"entry",scenario);
  snapshot(r,row,"entry-after-fault");fresh_output(row/"entry-events.bin",{reinterpret_cast<const std::byte*>(context.events().data()),context.events().size()*sizeof(Event)});
  fresh_output(row/"data-routes.bin",{reinterpret_cast<const std::byte*>(context.data_routes().data()),context.data_routes().size()*sizeof(Context::DataRoute)});calls_output(row/"calls.json",r);
  require(entry_job.denied&&r.poisoned(),"Required unresolved or causal dependency terminal");
  if(!mode){require(entry_job.fault_reason==static_cast<unsigned>(FaultReason::unresolved_import)&&entry_job.fault_pc==0x5ac428&&entry_job.fault_target==0x5bb50c,"Next actual named CRT dependency");
   require(context.data_routes().size()==1&&context.data_routes()[0].value==fdiv.lookups()[2].raw_result&&r.memory().load<unsigned>({0x9a17e4})==fdiv.lookups()[2].raw_result,"Actual queried BOOL carried through compiled source load and game store");
   require(r.calls().size()==5&&!r.calls()[0].completed,"Actual root remains incomplete");for(unsigned i=1;i<5;++i)require(r.calls()[i].completed,"Three services plus literal translated RET leaf completed");
   const auto chain=r.seh_chain();require(chain.size()==1&&chain[0].frame.value==frame-20&&chain[0].previous.value==0xffffffff&&chain[0].handler.value==0x5ac586,"Actual source exception frame; dispatch unimplemented");
  } else require(entry_job.fault_pc!=0x5ac428||entry_job.fault_target!=0x5bb50c,"Causal mutation must stop before clean next dependency");
  const auto state_copy=context.state();auto retry_fx=fx;std::copy(r.fx().begin(),r.fx().end(),retry_fx.begin());const auto event_count=context.events().size(),route_count=context.data_routes().size(),call_count=r.calls().size();bool retry{};
  try{context.invoke();}catch(const Fault&f){retry=f.reason()==FaultReason::poisoned;}
  require(retry&&!std::memcmp(&state_copy,&context.state(),3504)&&std::equal(retry_fx.begin(),retry_fx.end(),r.fx().begin())&&event_count==context.events().size()&&route_count==context.data_routes().size()&&call_count==r.calls().size(),"Poisoned Runtime retry retains complete State/FX/events/routes/calls");snapshot(r,row,"retry-after");
  std::ofstream result(row/"result.json");result<<"{\"passed\":true,\"scenario\":"<<scenario<<",\"control\":"<<mode<<",\"writer_complete\":true,\"entry_executed\":true,\"source_events\":"<<event_count<<",\"writer_events\":"<<fdiv.events().size()<<",\"actual_query_BOOL\":"<<fdiv.lookups()[2].raw_result<<",\"fault_reason\":"<<entry_job.fault_reason<<",\"fault_site\":"<<entry_job.fault_pc<<",\"fault_target\":"<<entry_job.fault_target<<",\"data_routes\":"<<route_count<<",\"State_reseed_after_writer\":false,\"outer_ESP_EIP_transition_explicit\":true,\"poisoned_retry\":true,\"SEH_dispatch\":false,\"host_direct_boundary\":true,\"volatile_XMM0_5_equality_claimed\":false,\"full_CRT\":false,\"whole_M4_complete\":false}\n";require(bool(result),"Result output");
  std::cout<<"scenario "<<scenario<<" control="<<mode<<" query="<<fdiv.lookups()[2].raw_result<<" events="<<event_count<<" fault="<<entry_job.fault_pc<<" target="<<entry_job.fault_target<<'\n';
 }
 fresh_output(directory/"COMPLETE",{reinterpret_cast<const std::byte*>("COMPLETE"),8});return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
