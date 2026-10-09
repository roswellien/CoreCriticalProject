// Independent compiled fixtures on the exact production composition and objects.
// Exclude only the CLI main; all production functions and typed dispatch persist.
#define MW34_ENTRY_MATHERR_NO_MAIN
#include "composition.cpp"
namespace {
unsigned review_checks{},review_scenarios{};
void review_need(bool ok,const char*why){++review_checks;if(!ok)throw std::runtime_error(std::string(why)+" in independent scenario "+std::to_string(review_scenarios));}
std::vector<std::byte> review_game,review_provider,review_pack,review_inputs,review_object,review_worker;
std::filesystem::path review_directory;
template<class T>void review_put(std::byte*p,T value){std::memcpy(p,&value,sizeof(value));}
void review_boundary(Job&job,const std::filesystem::path&row,const char*name,unsigned scenario){
 Boundary saved{};__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(saved.fx),"=m"(saved.env)::"memory");restore_host(saved);
 auto seeded=saved;const unsigned top=scenario%2?3U:7U;const unsigned depths[]={0,1,3,7};const unsigned depth=depths[scenario%4];const auto sw=static_cast<unsigned short>((top<<11)|0x20);unsigned ftw{},tag=0xffff;
 for(unsigned i=0;i<depth;++i){const auto physical=(top+i)&7;ftw|=1U<<physical;tag&=~(3U<<(2*physical));}
 review_put<unsigned short>(seeded.fx.data(),0xa7f);review_put<unsigned short>(seeded.fx.data()+2,sw);seeded.fx[4]=std::byte(ftw);review_put<unsigned>(seeded.fx.data()+24,0x1fa0);
 for(unsigned i=0;i<8;++i){review_put<std::uint64_t>(seeded.fx.data()+32+16*i,0x8000000000000000ULL+i*0x0101010101010101ULL);review_put<unsigned short>(seeded.fx.data()+40+16*i,static_cast<unsigned short>(0x3fff+i));}
 review_put<unsigned short>(seeded.env.data(),0xa7f);review_put<unsigned short>(seeded.env.data()+4,sw);review_put<unsigned short>(seeded.env.data()+8,static_cast<unsigned short>(tag));
 review_put<unsigned>(seeded.env.data()+12,0x11223344);review_put<unsigned short>(seeded.env.data()+16,0x23);review_put<unsigned short>(seeded.env.data()+18,0x11d);review_put<unsigned>(seeded.env.data()+20,0x55667788);review_put<unsigned short>(seeded.env.data()+24,0x2b);
 restore_host(seeded);try{boundary(job,row,name,scenario);}catch(...){restore_host(saved);throw;}restore_host(saved);
 const auto actual=read_file((row/(std::string(name)+"-host-before.bin")).string().c_str());review_need(actual.size()==544&&!std::memcmp(actual.data()+524,seeded.env.data()+12,14),"Direct hardware BEFORE retains deliberately nonzero complete legacy metadata");
}
struct ReviewFixture {
 Runtime r;std::unique_ptr<m4_crt::Session>crt;std::unique_ptr<fd::Registry>fdiv;
 std::unique_ptr<MatherrBinding>matherr;std::unique_ptr<Context>entry_context;std::filesystem::path row;
 explicit ReviewFixture(unsigned control=0,unsigned input_index=0):r([&]{Policy p;p.stack_low={0x20001000};p.stack_bytes=4096;p.heap_bytes=4096;return Runtime::from_admitted_image(review_game,p);}()){
  ++review_scenarios;row=review_directory/("case-"+std::to_string(review_scenarios));review_need(std::filesystem::create_directory(row),"Fresh independent row");checkpoint_directory=row;
  crt=std::make_unique<m4_crt::Session>(r,review_provider,m4_crt::Proof{Domain::admitted_game,m4::sha256(review_worker),"09a6018bb2cd3a6daf79786ee0bd2485b25f6b8c78740a352989019a2511e42a"});
  Input in{};std::memcpy(&in,review_inputs.data()+24+input_index*sizeof(Input),sizeof(in));seed(r,in);
  fdiv=std::make_unique<fd::Registry>(r);review_need(fdiv->admit(review_provider,review_pack),"Exact FDIV admission");Job j;j.writer=fdiv.get();review_boundary(j,row,"writer",review_scenarios);review_need(j.ok&&fdiv->ready(),"Actual producer executes before entry");
  for(auto address:matherr_pages){const auto page=provider_raw_page(review_provider,address);r.memory().map({address},4096,Permissions::read|Permissions::write);r.memory().write({address},page);if(address==matherr_pages[0])r.memory().protect({address},Permissions::read|Permissions::execute);}
  auto state=std::array<std::byte,3504>{};std::copy(r.remill_state().begin(),r.remill_state().end(),state.begin());auto fx=std::array<std::byte,512>{};std::copy(r.fx().begin(),r.fx().end(),fx.begin());
  matherr=std::make_unique<MatherrBinding>(r,review_provider,control);matherr_binding=matherr.get();
  review_need(std::equal(state.begin(),state.end(),r.remill_state().begin())&&std::equal(fx.begin(),fx.end(),r.fx().begin()),"Matherr constructor borrows full State/FX unchanged");
  r.register_service({{matherr->context.slot},{Abi::Cdecl,4,true},&matherr_adapter,"Independent compiled actual game matherr",Domain::admitted_game,fd::provider_sha,"72dabe5c1616590b1fe624844914b6d21fab26cf8eb8ddc3d430de98f50adce4"});
  entry_context=std::make_unique<Context>(r,*fdiv,m4::sha256(review_object));r.cpu().esp=frame+4;r.cpu().eip=Runtime::external_return;r.freeze_registry();
 }
 ~ReviewFixture(){matherr_binding=nullptr;mn::owner=nullptr;owner=nullptr;}
 Job call(){Job j;j.entry_context=entry_context.get();review_boundary(j,row,"entry",review_scenarios);review_need(j.denied&&r.poisoned(),"Actual required stop poisons bounded root");review_need(!mn::owner&&!owner&&!matherr->context.active,"Actual unwind clears active matherr and entry owners");return j;}
 void retry(){auto state=std::array<std::byte,3504>{};std::copy(r.remill_state().begin(),r.remill_state().end(),state.begin());auto fx=std::array<std::byte,512>{};std::copy(r.fx().begin(),r.fx().end(),fx.begin());const auto calls=r.calls().size(),events=entry_context->events().size();const auto step=matherr->context.step;const auto reason=matherr->context.reason;const auto pc=matherr->context.fault_pc,address=matherr->context.fault_address;bool denied{};
  try{entry_context->invoke();}catch(const Fault&f){denied=f.reason()==FaultReason::poisoned;}
  review_need(denied&&std::equal(state.begin(),state.end(),r.remill_state().begin())&&std::equal(fx.begin(),fx.end(),r.fx().begin()),"Poisoned retry cannot mutate full State/FX");
  review_need(calls==r.calls().size()&&events==entry_context->events().size()&&step==matherr->context.step&&reason==matherr->context.reason&&pc==matherr->context.fault_pc&&address==matherr->context.fault_address,"Poisoned retry retains first diagnostic and exact progress");
 }
};
void review_run(){
 for(unsigned index:{0U,5U,11U,12U,17U,23U}){ReviewFixture f(0,index);const auto j=f.call();auto&c=f.matherr->context;
  review_need(j.fault_reason==static_cast<unsigned>(FaultReason::unresolved_translation)&&j.fault_pc==0x5ac431&&j.fault_target==0x5ac5a0,"Next actual untranslated control wrapper boundary");
  review_need(c.used&&c.complete&&!c.failed&&c.step==5&&c.argument==0x51e7b0,"True compiled matherr leaf completed");
  review_need(f.r.memory().load<unsigned>({mn::zero_global})==0&&f.r.memory().load<unsigned>({mn::callback_global})==0x51e7b0,"Exact source global clear and guest callback storage");
  review_need(f.r.calls().size()==6&&!f.r.calls()[0].completed&&f.r.calls()[5].completed&&f.r.calls()[5].site.value==0x5ac428&&f.r.calls()[5].target.value==0x5bb50c&&f.r.calls()[5].return_pc.value==0x5ac42e,"Complete actual named import call with incomplete CRT root");f.retry();
 }
 for(unsigned which=0;which<2;++which){ReviewFixture f;f.r.memory().protect({which?0x7803b000U:0x78039000U},Permissions::read);const auto j=f.call();auto&c=f.matherr->context;
  review_need(c.used&&c.failed&&!c.complete&&c.step==(which?3U:2U),"Real compiled protected global stops exact counted prefix");
  review_need(c.fault_pc==(which?0x7800b39aU:0x7800b393U)&&c.fault_address==(which?mn::callback_global:mn::zero_global),"Exact first generated global write fault");
  review_need(j.fault_target==0x5bb50c&&!f.r.calls().back().completed,"Entered named matherr route incomplete on generated failure");
  f.r.memory().protect({which?0x7803b000U:0x78039000U},Permissions::read|Permissions::write);f.retry();
 }
 for(unsigned control:{18U,19U,20U,21U}){ReviewFixture f(control);f.call();auto&c=f.matherr->context;
  review_need(c.used&&c.failed&&!c.complete,"Actual generated return/bridge closure rejects corruption");
  review_need(c.step==(control==18?4U:control==21?4U:5U),"Actual corrupt closure stopped access count");f.matherr->control=0;f.retry();
 }
 {ReviewFixture f(24);const auto j=f.call();auto&c=f.matherr->context;review_need(c.used&&!c.active&&!c.complete&&c.step==0&&j.fault_target==0x5bb50c,"Before-execute observer exception unwinds typed Context and root without a guest instruction");f.matherr->control=0;f.retry();}
 for(unsigned which=0;which<2;++which){ReviewFixture f;const auto address=which?0x7803b0c4U:mn::entry;f.r.memory().protect({address&~4095U},Permissions::read|Permissions::write);f.r.memory().store<unsigned>({address},f.r.memory().load<unsigned>({address})^1);const auto j=f.call();
  review_need(!f.matherr->context.used&&f.matherr->context.step==0&&j.fault_target==0x5bb50c,"Current exact provider page mutation denied before compiled leaf");f.retry();
 }
 {ReviewFixture f;mutation(f.r,0x5bb50c,0);const auto j=f.call();review_need(j.fault_reason==static_cast<unsigned>(FaultReason::invalid_binding)&&j.fault_target==0x5bb50c&&!f.matherr->context.used,"Changed raw owning IAT rejected before service body");f.retry();}
 {ReviewFixture f;auto sb=std::array<std::byte,3504>{};std::copy(f.r.remill_state().begin(),f.r.remill_state().end(),sb.begin());auto fb=std::array<std::byte,512>{};std::copy(f.r.fx().begin(),f.r.fx().end(),fb.begin());auto&c=f.matherr->context;
  for(unsigned nested=0;nested<2;++nested){owner=f.entry_context.get();mn::owner=nested?&c:nullptr;
   for(void*wrong:{static_cast<void*>(nullptr),reinterpret_cast<void*>(std::uintptr_t{1}),static_cast<void*>(f.entry_context.get())}){
    if(!nested&&wrong==f.entry_context.get())continue;
    for(unsigned bridge=0;bridge<3;++bridge){bool denied{};try{if(bridge==0)(void)__remill_read_memory_32(wrong,mn::callback_global);if(bridge==1)(void)__remill_write_memory_32(wrong,mn::callback_global,0x12345678);if(bridge==2)(void)__remill_function_return(&c.state,0x5ac42e,wrong);}catch(const std::exception&e){const std::string expected=nested?(bridge==2?"Exact current matherr return token":"Exact current matherr memory token"):(bridge==2?"Exact active entry return token":"Exact active entry memory token");denied=e.what()==expected;}
     review_need(denied,"Null/arbitrary/cross-owner memory token denied before reinterpretation");review_need(std::equal(sb.begin(),sb.end(),f.r.remill_state().begin())&&std::equal(fb.begin(),fb.end(),f.r.fx().begin())&&f.entry_context->events().empty()&&!c.used&&!c.failed&&c.step==0&&f.r.memory().load<unsigned>({mn::callback_global})==0,"Malformed dispatch has no State/FX/access/Context/memory mutation");
    }
   }
  }
  mn::owner=nullptr;owner=nullptr;const auto j=f.call();review_need(c.complete&&j.fault_target==0x5ac5a0,"Correct serial owners remain usable after unentered malformed-token denials");f.retry();
 }
}
}
int main(int argc,char**argv){try{
 review_need(argc==7,"Independent exact game entryobject provider pack BEFOREinputs freshout");
 review_game=read_file(argv[1]);review_object=read_file(argv[2]);review_provider=read_file(argv[3]);review_pack=read_file(argv[4]);review_inputs=read_file(argv[5]);review_worker=read_file(argv[0]);review_directory=argv[6];
 review_need(m4::sha256(review_game)==m4::admitted_image_hash&&m4::sha256(review_provider)==fd::provider_sha&&m4::sha256(review_object)==MW34_ENTRY_OBJECT_SHA&&m4::sha256(review_inputs)==MW34_REPLAY_INPUT_SHA,"Exact original-BEFORE and frozen actual object inputs");review_need(!std::filesystem::exists(review_directory)&&std::filesystem::create_directory(review_directory),"Entirely fresh independent executions");review_run();
 std::ofstream f(review_directory/"controls.json");f<<"{\"passed\":true,\"checks\":"<<review_checks<<",\"scenarios\":"<<review_scenarios<<",\"ordinary_game_launched\":false,\"full_M4_complete\":false}\n";review_need(bool(f),"Independent report complete");std::cout<<review_checks<<" independent compiled checks / "<<review_scenarios<<" scenarios passed\n";return 0;
 }catch(const std::exception&e){matherr_binding=nullptr;mn::owner=nullptr;owner=nullptr;std::cerr<<e.what()<<'\n';return 1;}}
