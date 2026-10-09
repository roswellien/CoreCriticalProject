} // composition anonymous namespace
namespace mw34::m4_crt_heap_init {
namespace {thread_local Binding*authority{};}
bool has_authority()noexcept{return authority!=nullptr;}
extern "C" unsigned __remill_read_memory_32(void*,unsigned)noexcept(false);
 unsigned original_import(std::span<const std::byte>b){
  if(m4::sha256(b)!="2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7")throw std::invalid_argument("Exact provider import source required");
  auto word=[&](unsigned p){if(std::uint64_t(p)+2>b.size())throw std::invalid_argument("Provider PE word bounds");unsigned short v{};std::memcpy(&v,b.data()+p,2);return v;};
  auto dword=[&](unsigned p){if(std::uint64_t(p)+4>b.size())throw std::invalid_argument("Provider PE DWORD bounds");unsigned v{};std::memcpy(&v,b.data()+p,4);return v;};
  const auto pe=dword(0x3c),opt=pe+24;if(dword(pe)!=0x4550||word(pe+4)!=0x14c||word(opt)!=0x10b||dword(opt+28)!=0x78000000)throw std::invalid_argument("Exact PE32 provider import authority");
  auto offset=[&](unsigned rva,unsigned size){unsigned matches{},result{};for(unsigned n=0;n<word(pe+6);++n){const auto p=opt+word(pe+20)+n*40,va=dword(p+12),rs=dword(p+16),rp=dword(p+20);if(rva>=va&&std::uint64_t(rva)+size<=std::uint64_t(va)+rs){result=rp+rva-va;++matches;}}if(matches!=1||std::uint64_t(result)+size>b.size())throw std::invalid_argument("Provider import raw RVA bounds");return result;};
  auto text=[&](unsigned rva){const auto p=offset(rva,1);std::string result;for(unsigned n=0;n<4096;++n){if(p+n>=b.size())throw std::invalid_argument("Provider name bounds");auto v=std::to_integer<unsigned char>(b[p+n]);if(!v)return result;result.push_back(static_cast<char>(v));}throw std::invalid_argument("Terminated provider import name required");};
  const auto directory=dword(opt+104),size=dword(opt+108);unsigned matches{},result{};bool terminal{};
  for(unsigned d=0;d<size/20;++d){const auto p=offset(directory+d*20,20),original=dword(p),name=dword(p+12),iat=dword(p+16);if(!(original||dword(p+4)||dword(p+8)||name||iat)){terminal=true;break;}const auto library=text(name);const auto lookup=original?original:iat;bool end{};
   for(unsigned n=0;n<8192;++n){const auto value=dword(offset(lookup+4*n,4));if(!value){end=true;break;}if(!(value&0x80000000U)&&text(value+2)=="HeapCreate"){if(library!="KERNEL32.dll"||0x78000000+iat+4*n!=mw34::m4_crt_heap_init::iat||word(offset(value,2))!=411)throw std::invalid_argument("Exact unique provider HeapCreate name/hint/slot");result=dword(offset(iat+4*n,4));++matches;}}
   if(!end)throw std::invalid_argument("Provider import thunk termination");
  }if(!terminal||matches!=1)throw std::invalid_argument("Exactly one named HeapCreate provider import");return result;
 }

Binding::Binding(mg::Context&c,std::span<const std::byte>provider,unsigned mode):runtime(c.runtime),state(c.state),parent(&c),control(mode),admitted_parent_(&c),admitted_control_(mode){
 m4_cmd_native::Provider p(provider);source_[0]=p.slice({fragment},7,0x60000000);source_[1]=p.slice({entry},77,0x60000000);
 if(m4::sha256(source_[0])!="67c33f8cdb056ef8c51db43178b7fec29b78f7da00d0d4b0c34fde166a0fc6f1"||m4::sha256(source_[1])!="72922b45de858dc84ab5a08a8626acf0fca8487bd1e1cba955a3c0afba30e6ba"||original_import(provider)!=raw_import||p.dword({iat})!=raw_import)throw std::invalid_argument("Exact heap initializer, literal source CALL and unique HeapCreate import required");
}
Binding*current(void*p,unsigned a){auto*known=authority;if(!known)throw std::invalid_argument("Heap initializer active authority absent");if(p!=known||owner!=known||binding!=known||admitted_binding!=known)known->deny("Exact current exclusive heap initializer token required",a);return known;}
void Binding::first(const char*w,unsigned a,unsigned pc){if(!failed){failed=true;reason=w;fault_pc=pc?pc:state.gpr.rip.dword;fault_address=a;}}
[[noreturn]]void Binding::deny(const char*w,unsigned a,unsigned pc){first(w,a,pc);admitted_parent_->first(reason,fault_address,fault_pc);throw mg::BridgeAbort{};}
void Binding::admit_current(){if(authority&&authority!=this)authority->deny("Stale heap initializer binding cannot use current authority",entry);if(binding!=this||admitted_binding!=this)deny("Exact admitted heap initializer side binding required",entry);if(parent!=admitted_parent_||&admitted_parent_->runtime!=&runtime||&admitted_parent_->state!=&state)deny("Heap initializer borrowed parent association required",entry);}
void Binding::guard(){admit_current();if(authority!=this||owner!=this||!active||failed||!started_||control!=admitted_control_||thread_!=std::this_thread::get_id()||depth<1||depth>2||frame!=admitted_frame_||parent_frame!=admitted_parent_frame_||mg::owner||pp::owner||ld::has_authority()||cm::producer_owner||nt::owner||ci::owner||mn::owner||parent->used||parent->active)deny("Exact active serial heap initializer authority and frame required",frame);if(!std::equal(entry_fx_.begin(),entry_fx_.end(),runtime.fx().begin()))deny("Heap initializer changed carried Runtime FX",entry);cm::outer_owner_guard(*admitted_parent_);}
void Binding::source_identity(){admit_current();admitted_parent_->source_identity();for(unsigned i=0;i<2;++i){const auto start=i?entry:fragment;std::vector<std::byte>actual(source_[i].size());bool bad{};try{runtime.memory().read({start},actual);bad=actual!=source_[i];}catch(...){bad=true;}if(bad)deny("Exact current heap initializer source identity",start);}unsigned value{};try{value=runtime.memory().load<unsigned>({iat});}catch(...){deny("Checked original HeapCreate IAT identity read",iat);}if(value!=raw_import)deny("Exact original named HeapCreate IAT identity required",iat);}
void Binding::event(unsigned k,unsigned pc,unsigned a,unsigned v){if(event_count==events.size())deny("Heap initializer event bound",a,pc);events[event_count++]={k,pc,a,v};}
void Binding::hook(unsigned point){stage=point;auto&memory=runtime.memory();
 if(point==1&&control==109){memory.protect({0x78001000},Permissions::read|Permissions::write);memory.store<unsigned>({fragment},0);memory.protect({0x78001000},Permissions::read|Permissions::execute);}
 if(point==1&&control==110)state.gpr.rsp.dword^=4;
 if(point==1&&control==111)memory.protect({0x20001000},Permissions::read);
 if(point==2&&control==112&&access_count==1)memory.protect({0x20001000},Permissions::read);
 if(point==2&&control==113&&access_count==2)memory.store<unsigned>({admitted_frame_},ret^1);
 if(point==2&&control==114&&access_count==3)memory.store<unsigned>({admitted_frame_+4},2);
 if(point==2&&control==115&&access_count==3)memory.store<unsigned>({iat},raw_import^1);
 if(point==2&&control==116&&access_count==3)(void)__remill_read_memory_32(parent,admitted_frame_+4);
 if(point==2&&control==117&&access_count==4)throw std::runtime_error("Authored heap initializer partial-access observer exception");
 if(point==3&&control==118){memory.protect({0x78003000},Permissions::read|Permissions::write);memory.store<unsigned>({api_site},0);memory.protect({0x78003000},Permissions::read|Permissions::execute);}
 if(point==3&&control==119)state.gpr.rax.dword^=1;
 if(point==4&&control==120)throw std::runtime_error("Authored heap initializer terminal observer exception");
 if(extra)extra(*this,point);
}
void Binding::stable_hook(unsigned point,bool terminal){const auto old_state=state;const auto old_cpu=runtime.cpu();std::array<std::byte,512>fx{};std::copy(runtime.fx().begin(),runtime.fx().end(),fx.begin());auto progress=[&](){return std::array<unsigned,15>{frame,parent_frame,access_count,event_count,undefined_count,depth,fault_pc,fault_address,unsigned(used),unsigned(active),unsigned(failed),unsigned(api_reached),caller_error,restored_error,unsigned(admitted_parent_->failed)};};const auto old_progress=progress();const auto old_accesses=accesses;const auto old_events=events;const auto old_undefined=undefined_sites;const auto old_reason=reason;const auto old_scheduler=scheduler;hook(point);admit_current();if(authority!=(terminal?nullptr:this)||owner!=(terminal?nullptr:this)||control!=admitted_control_||stage!=point||old_progress!=progress()||old_reason!=reason||old_scheduler!=scheduler||std::memcmp(&old_state,&state,sizeof(State))||std::memcmp(&old_cpu,&runtime.cpu(),sizeof(old_cpu))||!std::equal(fx.begin(),fx.end(),runtime.fx().begin())||std::memcmp(old_accesses.data(),accesses.data(),sizeof(accesses))||std::memcmp(old_events.data(),events.data(),sizeof(events))||old_undefined!=undefined_sites)deny("Heap initializer observer changed carried State/FX or lifecycle/ledger",entry);if(!terminal){guard();source_identity();}}
void Binding::record(unsigned a,unsigned v,unsigned write){if(access_count==accesses.size())deny("Heap initializer source access bound",a);accesses[access_count++]={state.gpr.rip.dword,a,v,4,write};stable_hook(2);}
unsigned Binding::read32(unsigned a){guard();source_identity();const auto pc=state.gpr.rip.dword;unsigned want_pc{},want_address{},expected{};switch(access_count){case 3:want_pc=0x780039c3;want_address=admitted_frame_+4;expected=1;break;case 6:want_pc=api_site;want_address=iat;expected=raw_import;break;default:deny("Heap initializer DWORD read outside bounded prefix",a);}if(pc!=want_pc||a!=want_address)deny("Exact heap initializer generated DWORD operand required",a);unsigned v{};try{v=runtime.memory().load<unsigned>({a});}catch(...){deny("Checked heap initializer DWORD read fault",a);}if(v!=expected)deny("Heap initializer source argument or loaded value changed",a);record(a,v,0);return v;}
void Binding::write32(unsigned a,unsigned v){guard();source_identity();const auto pc=state.gpr.rip.dword;unsigned want_pc{},want_address{},expected{};switch(access_count){
 case 0:want_pc=fragment;want_address=admitted_parent_frame_-4;expected=1;break;
 case 1:want_pc=site;want_address=admitted_frame_;expected=ret;break;
 case 2:want_pc=0x780039c1;want_address=admitted_frame_-4;break;
 case 4:want_pc=0x780039c7;want_address=admitted_frame_-8;expected=4096;break;
 case 5:want_pc=0x780039cf;want_address=admitted_frame_-12;break;
 case 7:want_pc=api_site;want_address=admitted_frame_-16;expected=api_ret;break;
 default:deny("Heap initializer DWORD store outside bounded prefix",a);
 }if(pc!=want_pc||a!=want_address||v!=expected)deny("Exact heap initializer generated PUSH/CALL store required",a);try{runtime.memory().store<unsigned>({a},v);}catch(...){deny("Checked heap initializer generated store fault",a);}record(a,v,1);
}
unsigned char Binding::undefined(){guard();source_identity();if(state.gpr.rip.dword!=entry||access_count!=2||undefined_count||depth!=2)deny("Exact source XOR undefined AF representative site required",entry);undefined_sites[undefined_count++]=entry;return 0;}
void*Binding::called(State*s,unsigned target,void*p){guard();source_identity();if(s!=&state||p!=this||state.gpr.rip.dword!=target||access_count==0)deny("Exact heap initializer CALL State/token required",target);const auto&w=accesses[access_count-1];
 if(target==entry){if(depth!=1||event_count!=1||access_count!=2||w.pc!=site||w.address!=admitted_frame_||w.value!=ret||!w.write||state.gpr.rsp.dword!=admitted_frame_||runtime.memory().load<unsigned>({admitted_frame_})!=ret||runtime.memory().load<unsigned>({admitted_frame_+4})!=1)deny("Actual heap initializer source CALL frame closure required",admitted_frame_,site);event(2,site,target,ret);depth=2;checkpoint(runtime,"heap-provider-before");(void)mw34_heap_init_provider_body(s,target,this);deny("Unexpected heap initializer return",target);}
 const auto&r=accesses[6];if(target!=raw_import||depth!=2||event_count!=2||access_count!=8||undefined_count!=1||r.pc!=api_site||r.address!=iat||r.value!=raw_import||r.write||w.pc!=api_site||w.address!=admitted_frame_-16||w.value!=api_ret||!w.write||state.gpr.rsp.dword!=admitted_frame_-16||state.gpr.rax.dword!=0||runtime.memory().load<unsigned>({admitted_frame_-16})!=api_ret||runtime.memory().load<unsigned>({admitted_frame_-12})!=0||runtime.memory().load<unsigned>({admitted_frame_-8})!=4096||runtime.memory().load<unsigned>({admitted_frame_-4})!=0)deny("Actual original HeapCreate argument/IAT/CALL closure required",iat,api_site);
 checkpoint(runtime,"heap-api-before");stable_hook(3);guard();source_identity();api_reached=true;event(3,api_site,iat,raw_import);first("Required KERNEL32.dll HeapCreate remains unresolved",iat,api_site);admitted_parent_->first(reason,fault_address,fault_pc);throw m4_runtime::Fault(m4_runtime::FaultReason::unresolved_import,{api_site},{iat},reason);
}
[[noreturn]]void Binding::unsupported(unsigned a,const char*w){guard();deny(w,a);}
[[noreturn]]void Binding::start(mg::Context&c){fn::LastErrorBoundary errors;InvocationHostBoundary host;if(authority&&authority!=this)authority->deny("Stale heap initializer direct binding cannot enter current authority",entry);if(&c!=admitted_parent_)deny("Heap initializer scheduler received stale parent Context",entry);admit_current();cm::outer_owner_guard(c);if(authority||owner||used||active||failed||started_||depth||access_count||event_count||undefined_count||control!=admitted_control_||mg::owner||pp::owner||ld::has_authority()||cm::producer_owner||nt::owner||ci::owner||mn::owner||c.used||c.active||runtime.cpu().eip!=mg::slot||runtime.cpu().esp!=0x20001860||state.gpr.rsp.dword!=runtime.cpu().esp)deny("Exact fresh explicit source-fragment bootstrap scheduling required",fragment);source_identity();
 parent_frame=runtime.cpu().esp;admitted_parent_frame_=parent_frame;frame=parent_frame-8;admitted_frame_=frame;caller_error=errors.saved;errors.restored=&restored_error;std::copy(runtime.fx().begin(),runtime.fx().end(),entry_fx_.begin());checkpoint(runtime,"heap-before");scheduler={1,state.gpr.rip.dword,state.gpr.rsp.dword,fragment,state.gpr.rsp.dword,0,runtime.cpu().eip,runtime.cpu().esp};
 state.gpr.rip.dword=fragment;used=true;started_=true;active=true;depth=1;authority=this;owner=this;struct Cleanup{Binding&b;~Cleanup()noexcept{b.active=false;b.depth=0;owner=nullptr;authority=nullptr;}}cleanup{*this};event(1,fragment,parent_frame,0);
 try{checkpoint(runtime,"heap-projected");stable_hook(1);guard();source_identity();(void)mw34_heap_init_fragment_body(&state,fragment,this);deny("Unexpected source fragment completion beyond HeapCreate frontier",fragment);}
 catch(const mg::BridgeAbort&){active=false;depth=0;owner=nullptr;authority=nullptr;checkpoint(runtime,"heap-after");stable_hook(4,true);throw std::runtime_error(reason?reason:"Required compiled heap initializer fault");}
 catch(...){first("Required heap initializer observer or host fault");admitted_parent_->first(reason,fault_address,fault_pc);active=false;depth=0;owner=nullptr;authority=nullptr;checkpoint(runtime,"heap-after");stable_hook(4,true);throw;}
}
}
namespace {
