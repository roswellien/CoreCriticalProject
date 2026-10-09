
namespace mw34::m4_onexit {
namespace {thread_local SessionImpl*session_owner{};}
struct Checkpoint {
 std::string name;std::array<std::byte,3504>state;std::array<std::byte,512>fx;std::array<std::byte,40>cpu,runtime_cpu;
 std::vector<std::pair<unsigned,std::vector<std::byte>>>pages;
};
struct SessionImpl {
 Session&self;m4_runtime::Runtime&r;State&s;std::thread::id thread=std::this_thread::get_id();
 std::vector<std::byte>provider;std::unique_ptr<mg::Context>parent;std::unique_ptr<lb::Binding>binding;
 bool bootstrapped{},running{},failed{},finished{};unsigned roots{};std::vector<Checkpoint>checkpoints;
 std::array<unsigned,4>exception_witness{1,0,0,0};std::array<char,4096>exception_message{};
 std::vector<std::array<unsigned,8>>projections;
 SessionImpl(Session&session,m4_runtime::Runtime&runtime,std::span<const std::byte>raw):self(session),r(runtime),s(*reinterpret_cast<State*>(runtime.remill_state().data())),provider(raw.begin(),raw.end()){
  require(r.remill_seeded()&&m4::sha256(provider)==fd::provider_sha,"Fresh persistent State and literal registry provider");
  for(const auto&p:lb::source_pages()){
   const auto original=provider_raw_page(provider,p.address);std::array<std::byte,4096>current{};bool absent{};
   try{r.memory().read({p.address},current);}catch(const MemoryFault&e){if(e.reason()!=MemoryFaultReason::unmapped)throw;absent=true;}
   if(absent){r.memory().map({p.address},4096,Permissions::read|Permissions::write);r.memory().write({p.address},original);r.memory().protect({p.address},static_cast<Permissions>(p.permissions));}
   else require(current==original,"Existing provider mapping must be the exact raw source input");
  }
  std::array<std::byte,4096>lower{};try{r.memory().read({0x20000000},lower);}catch(const MemoryFault&e){if(e.reason()!=MemoryFaultReason::unmapped)throw;r.memory().map({0x20000000},4096,Permissions::read|Permissions::write);}
  parent=std::make_unique<mg::Context>(r,provider);binding=std::make_unique<lb::Binding>(*parent,provider,0);binding->research_standalone_=true;binding->extra=&hook;
 }
 static void hook(lb::Binding&b,unsigned point){
  require(session_owner&&session_owner->binding.get()==&b,"Exact current standalone registry observer owner");auto&i=*session_owner;
  if(i.self.test_hook)i.self.test_hook(i.self,point);
 }
 void check(){if(thread!=std::this_thread::get_id()||running||failed||finished||session_owner||lb::has_authority())throw std::runtime_error("Fresh serial unpoisoned callback-registry boundary");}
 void activate(){
  session_owner=this;lb::binding=binding.get();lb::admitted_binding=binding.get();lb::owner=binding.get();lb::authority=binding.get();running=true;
  // The inherited caller_error authenticates the completed bootstrap query.
  // Each Session invocation has its own LastErrorBoundary for the current
  // caller; later entries must not rewrite that immutable historical witness.
  std::copy(r.fx().begin(),r.fx().end(),binding->entry_fx_.begin());
 }
 void pause()noexcept{running=false;lb::owner=nullptr;lb::authority=nullptr;lb::binding=nullptr;lb::admitted_binding=nullptr;session_owner=nullptr;}
 void remember_exception(const char*message,unsigned kind)noexcept{
  if(exception_witness[1])return;if(!message)message="Exception without diagnostic text";
  unsigned n{};while(n+1<exception_message.size()&&message[n]){exception_message[n]=message[n];++n;}
  exception_witness={1,kind,unsigned(message[n]!=0),n};
 }
 void poison()noexcept{
  // Capture the currently handled exception before rethrowing it to the caller.
  // Existing first-fault identity/reason remains authoritative when already set.
  try{if(auto current=std::current_exception())std::rethrow_exception(current);remember_exception("Registry fault without active exception",3);}
  catch(const std::exception&e){remember_exception(e.what(),1);}
  catch(...){remember_exception(binding->failed&&binding->reason?binding->reason:"Non-standard registry observer or host exception",2);}
  failed=true;if(!binding->failed)binding->first(exception_message.data());if(!binding->registry_growth_.empty())binding->registry_growth_.back()[21]=1;pause();
 }
 void fresh_external_pages(){
  // Caller-owned stack input changes only while this owner is paused; provider
  // and allocation pages retain their checked committed mirrors.
  for(auto&[address,bytes]:binding->expected_pages_)if(address<0x78000000&&address<0x31000000)r.memory().read({address},bytes);
  r.memory().read({0x20000000},binding->lower_expected_);r.memory().read({0x20001000},binding->upper_expected_);
 }
 void capture(std::string_view name){
  Checkpoint c;c.name=name;std::memcpy(c.state.data(),&s,sizeof(s));std::copy(r.fx().begin(),r.fx().end(),c.fx.begin());const auto projected=::cpu(s);std::memcpy(c.cpu.data(),&projected,sizeof(projected));std::memcpy(c.runtime_cpu.data(),&r.cpu(),sizeof(r.cpu()));
  for(const auto&p:lb::source_pages()){std::vector<std::byte>page(4096);r.memory().read({p.address},page);c.pages.emplace_back(p.address,std::move(page));}
  for(unsigned address:lb::registry_game_pages){std::vector<std::byte>page(4096);r.memory().read({address},page);c.pages.emplace_back(address,std::move(page));}
  for(unsigned address:std::array<unsigned,2>{0x20000000,0x20001000})c.pages.emplace_back(address,binding->guest_bytes(address,4096));
  for(auto&a:binding->owned_allocations_)if(a->mapped){auto bytes=binding->guest_bytes(a->guest,a->mapped_bytes);c.pages.emplace_back(a->guest,std::move(bytes));if(a->retired_guest)c.pages.emplace_back(a->retired_guest,binding->guest_bytes(a->retired_guest,a->mapped_bytes));}
  checkpoints.push_back(std::move(c));
 }
 void bootstrap(){
  check();if(bootstrapped)throw std::runtime_error("Registry bootstrap is single use");InvocationHostBoundary host;fn::LastErrorBoundary errors;
  const auto oldpc=s.gpr.rip.dword,oldsp=s.gpr.rsp.dword;const auto prior=r.cpu();
  projections.push_back({1,oldpc,oldsp,mg::slot,0x20001860,prior.eip,prior.esp,0});s.gpr.rip.dword=mg::slot;s.gpr.rsp.dword=0x20001860;r.cpu()=::cpu(s);
  session_owner=this;lb::binding=binding.get();lb::admitted_binding=binding.get();running=true;
  try{capture("registry-bootstrap-before");
   binding->start(*parent);require(binding->static_complete_&&binding->live_handle()&&binding->live_critical_sections()==4,"Actual source heap and four static critical sections established");
   binding->registry_root_=0x5ac3d8;s.gpr.rip.dword=0x5ac3d8;projections.push_back({3,mg::slot,0x20001860,0x5ac3d8,0x20001860,0,0,0});
   try{(void)lb::dispatch_body(0x5ac3d8,&s,binding.get());binding->deny("Actual sentinel source fragment must stop at 5AC3EC",0x5ac3ec);}catch(const lb::SentinelComplete&){}
   require(r.memory().load<unsigned>({0x9a17ec})==UINT32_MAX&&r.memory().load<unsigned>({0x9a17f0})==UINT32_MAX,"Actual original sentinel stores completed");binding->registry_root_=0;
   capture("registry-producer-before");binding->external_source_call(0x78004482,0xffffff90);capture("registry-producer-after");
   auto begin=r.memory().load<unsigned>({0x7803788c}),next=r.memory().load<unsigned>({0x78037888});require(begin&&begin==next&&binding->allocation_for(begin)&&binding->allocation_for(begin)->requested==128&&r.memory().load<unsigned>({begin})==0,"Genuine source producer published owned empty callback vector");
   s.gpr.rip.dword=oldpc;s.gpr.rsp.dword=oldsp;r.cpu()=::cpu(s);projections.push_back({2,0x7800184c,0x20001860,oldpc,oldsp,0,0,0});bootstrapped=true;capture("registry-bootstrap-returned");pause();
  }catch(...){r.cpu()=::cpu(s);poison();throw;}
 }
 void enter(unsigned root){
  check();if(!bootstrapped||!lb::registration_callback(root))throw std::runtime_error("Only an actual registered literal initializer root may enter");
  InvocationHostBoundary host;fn::LastErrorBoundary errors;::project(s,r.cpu());fresh_external_pages();activate();binding->registry_root_=root;
  const auto frame=s.gpr.rsp.dword,ret=r.memory().load<unsigned>({frame});
  try{
   if(r.cpu().eip!=root)binding->deny("Actual selected Runtime translation entry",root);capture("registry-root-"+std::to_string(roots)+"-before");
   binding->guard();binding->source_identity();binding->calls_.push_back({root,frame,ret,0,s.gpr.rbp.dword,s.gpr.rbx.dword,s.gpr.rsi.dword,s.gpr.rdi.dword,0});
   // Native scratch x87 executes constrained source operations with the carried
   // guest control word. Caller hardware is restored by the outer boundary.
   const auto control=s.x87.fxsave.cwd.flat;const auto mxcsr=s.x87.fxsave.mxcsr.flat;__asm__ volatile("fninit\n\tfldcw %0\n\tldmxcsr %1"::"m"(control),"m"(mxcsr):"memory");
   const auto result=lb::dispatch_body(root,&s,binding.get());binding->guard();binding->source_identity();
   require(result==binding.get()&&binding->calls_.empty()&&s.gpr.rsp.dword==frame+4&&s.gpr.rip.dword==ret,"Actual selected initializer RET consumes original committed Runtime frame");
   capture("registry-root-"+std::to_string(roots)+"-after");++roots;binding->registry_root_=0;r.cpu()=::cpu(s);pause();
  }catch(...){r.cpu()=::cpu(s);poison();throw;}
 }
 void replay(unsigned root,unsigned marker){
  check();if(!bootstrapped||!lb::registration_callback(root))throw std::runtime_error("Replay requires genuine initialized registry and original root");InvocationHostBoundary host;fn::LastErrorBoundary errors;
  ::project(s,r.cpu());fresh_external_pages();activate();binding->registry_root_=root;
  try{capture("registry-replay-"+std::to_string(roots)+"-before");binding->external_source_call(root,marker);capture("registry-replay-"+std::to_string(roots)+"-after");++roots;binding->registry_root_=0;r.cpu()=::cpu(s);pause();}catch(...){r.cpu()=::cpu(s);poison();throw;}
 }
 void finish(){
  if(thread!=std::this_thread::get_id())throw std::runtime_error("Registry finish requires its original owner thread");if(running)throw std::runtime_error("Registry cleanup cannot run during source or native API work");if(finished)return;
  InvocationHostBoundary host;fn::LastErrorBoundary errors;lb::binding=binding.get();lb::admitted_binding=binding.get();
  try{
   if(bootstrapped&&!failed){::project(s,r.cpu());fresh_external_pages();std::copy(r.fx().begin(),r.fx().end(),binding->entry_fx_.begin());session_owner=this;lb::owner=binding.get();lb::authority=binding.get();running=true;const auto begin=r.memory().load<unsigned>({0x7803788c});auto*a=binding->allocation_for(begin);if(!a)binding->deny("Registry cleanup requires its live source-published begin",begin);
    const auto oldpc=s.gpr.rip.dword,oldsp=s.gpr.rsp.dword;const auto sp=oldsp-4;r.memory().store<unsigned>({sp},begin);binding->expected_store(sp,&begin,4);binding->research_accesses_.push_back({oldpc,sp,begin,4,1});s.gpr.rsp.dword=sp;binding->external_source_call(lb::free_entry,0xffffff80);s.gpr.rsp.dword=oldsp;require(a->source_freed&&!a->native,"Genuine source free released registry allocation");r.cpu()=::cpu(s);pause();lb::binding=binding.get();lb::admitted_binding=binding.get();
   }
   binding->finish();finished=true;pause();
  }catch(...){pause();throw;}
 }
 void dump(Sink sink,void*user)const{
  binding->dump(sink,user);sink("registry-research-projections.bin",std::as_bytes(std::span(projections)),user);
  sink("registry-exception-witness.bin",std::as_bytes(std::span(exception_witness)),user);
  sink("registry-exception-message.bin",std::as_bytes(std::span(exception_message.data(),exception_witness[3])),user);
  const auto&b=*binding;
  sink("heap-create-witness.bin",std::as_bytes(std::span(b.witness)),user);
  sink("heap-create-registry.bin",std::as_bytes(std::span(b.registry)),user);
  sink("heap-query-witness.bin",std::as_bytes(std::span(b.query_witness)),user);
  sink("heap-query-input.bin",b.query_input,user);sink("heap-query-output.bin",b.query_output,user);
  sink("heap-source-accesses.bin",std::as_bytes(std::span(b.accesses)),user);
  sink("heap-api-accesses.bin",std::as_bytes(std::span(b.api_accesses)),user);
  sink("heap-events.bin",std::as_bytes(std::span(b.events)),user);
  sink("heap-undefined-sites.bin",std::as_bytes(std::span(b.undefined_sites)),user);
  sink("heap-query-output-accesses.bin",std::as_bytes(std::span(b.output_accesses)),user);
  sink("heap-scheduler.bin",std::as_bytes(std::span(b.scheduler)),user);
  lb::emit_identity(sink,user,"heap-create-api-before",b.create_before);lb::emit_identity(sink,user,"heap-create-api-after",b.create_after);
  lb::emit_identity(sink,user,"heap-query-api-before",b.query_before);lb::emit_identity(sink,user,"heap-query-api-after",b.query_after);
  lb::emit_identity(sink,user,"heap-destroy-api-before",b.destroy_before);lb::emit_identity(sink,user,"heap-destroy-api-after",b.destroy_after);
  for(std::size_t n=0;n<checkpoints.size();++n){const auto&c=checkpoints[n];const auto prefix="registry-checkpoint-"+std::to_string(n);sink(prefix+"-name.bin",std::as_bytes(std::span(c.name)),user);sink(prefix+"-state.bin",c.state,user);sink(prefix+"-fx.bin",c.fx,user);sink(prefix+"-cpu.bin",c.cpu,user);sink(prefix+"-runtime-cpu.bin",c.runtime_cpu,user);for(const auto&[a,b]:c.pages)sink(prefix+"-page-"+std::to_string(a)+".bin",b,user);}
 }
};
void registry_checkpoint(m4_runtime::Runtime&r,const char*name){if(session_owner&& &session_owner->r==&r)session_owner->capture(name);}
Session::Session(m4_runtime::Runtime&r,std::span<const std::byte>provider):impl_(std::make_unique<SessionImpl>(*this,r,provider)){}
Session::~Session()noexcept{if(impl_){try{impl_->finish();}catch(...){}if(session_owner==impl_.get())impl_->pause();}}
void Session::bootstrap(){impl_->bootstrap();}void Session::enter(unsigned root){impl_->enter(root);}void Session::replay(unsigned root,unsigned marker){impl_->replay(root,marker);}void Session::finish(){impl_->finish();}
void Session::dump(Sink sink,void*user)const{impl_->dump(sink,user);auto value=summary();sink("registry-summary.bin",std::as_bytes(std::span(value)),user);}
std::array<std::uint64_t,32>Session::summary()const noexcept{
 const auto&i=*impl_;const auto&b=*i.binding;unsigned begin{},next{},capacity{};if(i.bootstrapped){try{begin=i.r.memory().load<unsigned>({0x7803788c});next=i.r.memory().load<unsigned>({0x78037888});auto*a=const_cast<lb::Binding&>(b).allocation_for(begin);if(a)capacity=a->capacity;}catch(...){}}
 return {1,unsigned(i.bootstrapped),unsigned(i.running),unsigned(i.failed||b.failed),unsigned(i.finished),i.roots,begin,next,capacity,next>=begin?(next-begin)/4:0,b.live_allocations(),b.live_critical_sections(),b.native_apis_.size(),b.source_accesses_.size(),b.registry_growth_.size(),b.live_handle()?b.known_handle():0,b.fault_pc,b.fault_address,b.source_budget_,i.s.gpr.rip.dword,i.s.gpr.rsp.dword,b.research_accesses_.size(),i.checkpoints.size(),0,0,0,0,0,0,0,0,0};
}
std::span<const std::array<std::uint64_t,32>>Session::growth_witnesses()const noexcept{return impl_->binding->registry_growth_;}
void*Session::token()const noexcept{return impl_->binding.get();}m4_runtime::Runtime&Session::runtime()const noexcept{return impl_->r;}bool Session::live_handle()const noexcept{return impl_->binding->live_handle();}
bool active()noexcept{return session_owner&&session_owner->running&&lb::has_authority();}
std::uint64_t read(void*p,unsigned a,unsigned n){return n==4?lb::current(p,a)->read32(a):lb::current(p,a)->read(a,n);}
void*write(void*p,unsigned a,std::uint64_t v,unsigned n){if(n==4)lb::current(p,a)->write32(a,unsigned(v));else lb::current(p,a)->write(a,v,n);return p;}
void*called(void*p,State*s,unsigned a){return lb::current(p,a)->called(s,a,p);}void*returned(void*p,State*s,unsigned a){return lb::current(p,a)->returned(s,a,p);}void*missing(void*p,State*s,unsigned a){return lb::current(p,a)->missing(s,a,p);}unsigned char undefined(){return lb::current(lb::owner)->undefined();}
}
