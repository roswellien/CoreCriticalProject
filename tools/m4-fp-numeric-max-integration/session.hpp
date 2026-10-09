// NEW native-only MSVCP50 registry. Shared r9 and standalone gate are unchanged.
#pragma once
#include "runtime.hpp"
#include "admission.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <array>
#include <algorithm>
#include <bit>
#include <cctype>
#include <cstring>
#include <thread>
#include <tuple>
#include <optional>
namespace mw34::m4_nmx_integration {
inline constexpr unsigned root=0x4c19f0,body=0x4c1a00,leaf=0x780c10f0,slot=0x5bb4fc,data=0x78115004,output=0x60b368;
inline constexpr char provider_sha[]="91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a";
inline constexpr char symbol[]="?max@?$numeric_limits@M@std@@SAMXZ";
inline constexpr std::array<unsigned,12>controls{0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f};
extern "C" void *mw34_nmx_entry_4c19f0(State*,unsigned,void*);
extern "C" void *mw34_nmx_entry_4c1a00(State*,unsigned,void*);
extern "C" void *mw34_nmx_entry_780c10f0(State*,unsigned,void*);
struct Proof{std::string native_sha,gate_sha;};
struct DataFixture{unsigned bits;}; // Explicit authored source-input substitution only.
struct Event{unsigned pc,address,value,width,write;};
struct Fault{unsigned pc,address,step;const char*reason;};
struct View{m4_runtime::Cpu32 cpu;std::array<std::byte,3504>state;std::array<std::byte,512>fx;std::array<std::byte,28>env;};
inline m4_runtime::Cpu32 cpu(const State&s){return {s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword,static_cast<unsigned>((s.rflag.flat&~0xcd5ULL)|(s.aflag.cf<<0)|(s.aflag.pf<<2)|(s.aflag.af<<4)|(s.aflag.zf<<6)|(s.aflag.sf<<7)|(s.aflag.df<<10)|(s.aflag.of<<11)),s.gpr.rip.dword};}
inline void project(State&s,const m4_runtime::Cpu32&c){s.gpr.rax.dword=c.eax;s.gpr.rcx.dword=c.ecx;s.gpr.rdx.dword=c.edx;s.gpr.rbx.dword=c.ebx;s.gpr.rsp.dword=c.esp;s.gpr.rbp.dword=c.ebp;s.gpr.rsi.dword=c.esi;s.gpr.rdi.dword=c.edi;s.gpr.rip.dword=c.eip;s.rflag.flat=c.eflags;s.aflag.cf=(c.eflags>>0)&1;s.aflag.pf=(c.eflags>>2)&1;s.aflag.af=(c.eflags>>4)&1;s.aflag.zf=(c.eflags>>6)&1;s.aflag.sf=(c.eflags>>7)&1;s.aflag.df=(c.eflags>>10)&1;s.aflag.of=(c.eflags>>11)&1;}
inline unsigned status(const State&s){return (s.x87.fxsave.swd.flat&0xb880)|(s.sw.ie<<0)|(s.sw.de<<1)|(s.sw.ze<<2)|(s.sw.oe<<3)|(s.sw.ue<<4)|(s.sw.pe<<5)|(s.sw.sf<<6)|(s.sw.c0<<8)|(s.sw.c1<<9)|(s.sw.c2<<10)|(s.sw.c3<<14);}
inline unsigned full_tag(const void*p){std::uint64_t m;std::uint16_t e;std::memcpy(&m,p,8);std::memcpy(&e,static_cast<const std::byte*>(p)+8,2);e&=0x7fff;return !e&&!m?1:e==0x7fff||!e||!(m>>63)?2:0;}
inline View view(const State&s){View v{};v.cpu=cpu(s);std::memcpy(v.state.data(),&s,3504);std::memcpy(v.fx.data(),&s.x87,512);const auto sw=static_cast<std::uint16_t>(status(s));std::memcpy(v.fx.data()+2,&sw,2);std::memset(v.fx.data()+6,0,18);unsigned tag=0xffff;const auto top=(sw>>11)&7;
 for(unsigned i=0;i<8;++i){std::memcpy(v.fx.data()+32+16*i,&s.st.elems[i].val,10);std::memcpy(v.fx.data()+160+16*i,&s.vec[i],16);auto phys=(top+i)&7;if(s.x87.fxsave.ftw.flat&(1<<phys))tag=(tag&~(3<<(2*phys)))|(full_tag(v.fx.data()+32+16*i)<<(2*phys));}
 auto put=[&](unsigned o,unsigned x){std::memcpy(v.env.data()+o,&x,4);};put(0,0xffff0000U|s.x87.fxsave.cwd.flat);put(4,0xffff0000U|sw);put(8,0xffff0000U|tag);put(12,s.x87.fxsave.ip);put(16,s.x87.fxsave.cs.flat|(unsigned{s.x87.fxsave.fop}<<16));put(20,s.x87.fxsave.dp);put(24,0xffff0000U|s.x87.fxsave.ds.flat);return v;}
struct BridgeAbort{};
class Session;
inline thread_local Session*owner{};
class Session {
 struct OwnedPages{GuestMemory&m;std::array<unsigned,2>pages{0x780c1000,0x78115000};std::array<bool,2>owns{};~OwnedPages(){for(unsigned i=2;i-->0;)if(owns[i])try{m.unmap({pages[i]});}catch(...){}}}owned_;
 m4_runtime::Runtime&r_;State&s_;unsigned raw_iat_{},data_word_=0x7f7fffff;std::thread::id thread_=std::this_thread::get_id();bool running_{},failed_{};Fault fault_{};
 unsigned frame_{},ret_{},level_{},step_{},clears_{},tests_{},returns_{},commits_{};bool complete_{};
 std::array<Event,22>events_{};View checkpoint_{};std::array<std::byte,4096>code_page_{},data_page_{};
 static void root_adapter(m4_runtime::Runtime&r){auto*c=owner;if(!c||&c->r_!=&r)throw std::runtime_error("Numeric-max live stable owner absent");c->enter_root();}
 static void body_adapter(m4_runtime::Runtime&r){auto*c=owner;if(!c||&c->r_!=&r)throw std::runtime_error("Numeric-max body owner absent");c->compiled_body();}
 static void service_adapter(m4_runtime::Runtime&r){auto*c=owner;if(!c||&c->r_!=&r)throw std::runtime_error("Numeric-max MSVCP50 owner absent");c->compiled_service();}
 void source_check(){std::array<std::byte,10>w{};std::array<std::byte,117>b{};std::array<std::byte,4096>p{},d{};r_.memory().read({root},w);r_.memory().read({body},b);r_.memory().read({0x780c1000},p);r_.memory().read({0x78115000},d);if(m4::sha256(w)!="1147d8ad778df578820c4be4a4719d35cc4a4c39e0d74043bfdbc57909a261cc"||m4::sha256(b)!="642aa130e093e1dc8e691b492ae650831cb9f60cf2428d2448e6c0a61fe1e3c5"||p!=code_page_||d!=data_page_||r_.memory().load<unsigned>({slot})!=raw_iat_)deny("Current game/MSVCP50/raw IAT identity changed");}
 void guard(){if(!running_||failed_||owner!=this||thread_!=std::this_thread::get_id())deny("Inactive/wrong owner/faulted numeric-max bridge");}
 Event wanted(unsigned i){const std::array<Event,22>e{{{0,frame_-4,0,4,1},{0,frame_-8,0,4,1},{0,frame_-12,0,4,1},{0,slot,0,4,0},{0,frame_-16,0,4,1},{0,data,0,4,0},{0,frame_-16,0,4,0},{0,output,0,4,1},{0,output+4,0,4,1},{0,output+8,0,4,1},{0,output+12,0,4,1},{0,output+16,0,4,1},{0,output+20,0,4,1},{0,output+24,0,4,1},{0,output+28,0,4,1},{0,output+32,0,4,1},{0,output+36,0,4,1},{0,output+40,0,4,1},{0,frame_-12,0,4,0},{0,frame_-8,0,4,0},{0,frame_-4,0,4,0},{0,frame_,0,4,0}}};if(i>=e.size())deny("Numeric-max event extent exceeded");return e[i];}
 void access(unsigned a,unsigned op){guard();auto e=wanted(step_);if(a!=e.address||op!=e.write)deny("Unexpected exact numeric-max access",a);}
 void log(unsigned a,unsigned v,unsigned op){events_[step_++]={s_.gpr.rip.dword,a,v,4,op};if(test_after_event)test_after_event(*this,step_);}
 void sync(){const auto v=view(s_);r_.cpu()=v.cpu;std::memcpy(r_.fx().data(),v.fx.data(),512);}
 void compiled_body(){guard();if(level_!=1||step_!=2||r_.cpu().eip!=body)deny("Direct body dispatcher domain rejected");project(s_,r_.cpu());auto token=mw34_nmx_entry_4c1a00(&s_,body,this);if(token!=this||level_!=0||step_!=20)deny("Complete compiled body did not return");sync();}
 void compiled_service(){guard();if(level_!=2||step_!=5||r_.cpu().eip!=slot)deny("MSVCP50 typed service domain rejected");project(s_,r_.cpu());s_.gpr.rip.dword=leaf;auto token=mw34_nmx_entry_780c10f0(&s_,leaf,this);if(token!=this||level_!=1||step_!=7)deny("Complete real provider leaf did not return");sync();}
 void admit_fp(){auto sw=status(s_),top=(sw>>11)&7;unsigned depth=0;const auto ftw=s_.x87.fxsave.ftw.flat;while(depth<8&&(ftw&(1<<((top+depth)&7))))++depth;unsigned expected=0;for(unsigned i=0;i<depth;++i)expected|=1<<((top+i)&7);
  const auto sticky=sw&~0x3800U;
  if(depth==8||(depth!=0&&depth!=1&&depth!=7)||ftw!=expected||(top!=0&&top!=7)||std::find(controls.begin(),controls.end(),s_.x87.fxsave.cwd.flat)==controls.end()||(sticky!=0&&sticky!=2&&sticky!=34)||s_.x87.fxsave.mxcsr.flat!=0x1f80||s_.addr.ds_base.dword||s_.addr.ss_base.dword||s_.addr.fs_base.dword!=r_.fs_base().value||s_.seg.cs.flat!=0x23||s_.seg.ds.flat!=0x2b||s_.seg.ss.flat!=0x2b)deny("Bounded coherent live-stack/CW/status/segments domain rejected");
  const auto v=view(s_);if(!std::equal(v.fx.begin(),v.fx.end(),r_.fx().begin()))deny("Persistent State and separate software FX disagree");
  // Only live values are constrained. Dead physical storage legitimately changes
  // after FLD/FSTP and must carry into subsequent invocations without reseeding.
  for(unsigned i=0;i<depth;++i){std::uint64_t m{};std::uint16_t e{};std::memcpy(&m,&s_.st.elems[i].val,8);std::memcpy(&e,reinterpret_cast<const std::byte*>(&s_.st.elems[i].val)+8,2);if(m!=(0x8000000000000000ULL+(std::uint64_t{i}<<56))||e!=(0x4000|(i%2?0x8000:0)))deny("Unmeasured live raw80 value rejected");}
 }
 void enter_root(){if(running_||failed_||r_.poisoned()||thread_!=std::this_thread::get_id()||!r_.remill_seeded())throw std::runtime_error("Numeric-max fresh serial root context rejected");project(s_,r_.cpu());frame_=s_.gpr.rsp.dword;ret_=r_.memory().load<unsigned>({frame_});if(s_.gpr.rip.dword!=root||frame_<r_.stack_low().value+16||std::uint64_t{frame_}+4>r_.stack_top().value)throw std::runtime_error("Numeric-max owned root frame rejected");
  level_=step_=clears_=tests_=returns_=commits_=0;complete_=false;events_={};checkpoint_={};running_=true;
  try{source_check();admit_fp();auto token=mw34_nmx_entry_4c19f0(&s_,root,this);if(token!=this||!complete_||level_||step_!=22||returns_!=3||clears_!=1||tests_!=1||commits_!=2)deny("Complete original wrapper/body/provider closure rejected");sync();}
  catch(const BridgeAbort&){running_=false;throw std::runtime_error(fault_.reason);}catch(...){running_=false;throw;}running_=false;
 }
public:
 void(*test_after_event)(Session&,unsigned){}; // Null for all positive/offline replay calls.
 Session(m4_runtime::Runtime&r,std::span<const std::byte>provider,const Proof&p,std::optional<DataFixture>fixture={}):owned_{r.memory()},r_(r),s_(*reinterpret_cast<State*>(r.remill_state().data())){
  if(r.domain()!=m4_runtime::Domain::admitted_game||provider.size()!=565760||m4::sha256(provider)!=provider_sha)throw std::invalid_argument("Exact MSVCP50 image ownership required");
  unsigned count=0;for(const auto&i:r.image_metadata().imports){auto library=i.library;std::transform(library.begin(),library.end(),library.begin(),[](unsigned char c){return static_cast<char>(std::tolower(c));});if(r.image_metadata().image_base+i.iat_rva==slot){if(library!="msvcp50.dll"||!i.name||*i.name!=symbol)throw std::invalid_argument("Actual MSVCP50 numeric_limits max game owner differs");raw_iat_=i.original_iat_value;++count;}}
  if(count!=1||r.memory().load<unsigned>({slot})!=raw_iat_)throw std::invalid_argument("Exact raw MSVCP50 owning IAT required");
  // File offsets/permissions/export1545 are independently recovered in preparation-r4.
  std::memcpy(code_page_.data(),provider.data()+0x1000,4096);std::memcpy(data_page_.data(),provider.data()+0x54c00,4096);
  if(fixture){constexpr std::array<unsigned,16>allowed{0x7f7fffff,0,0x80000000,1,0x80000001,0x007fffff,0x00800000,0x3f800000,0xbf800000,0x3eaaaaab,0xff7fffff,0x7f800000,0xff800000,0x7fc12345,0x7f812345,0xff812345};if(std::find(allowed.begin(),allowed.end(),fixture->bits)==allowed.end())throw std::invalid_argument("Unknown explicit provider source-input fixture");data_word_=fixture->bits;std::memcpy(data_page_.data()+4,&data_word_,4);}
  const auto leaf_source=std::span<const std::byte>{code_page_}.subspan(0xf0,7);unsigned operand{};std::memcpy(&operand,leaf_source.data()+2,4);
  if(m4::sha256(leaf_source)!="31d3ed84e61450051bfba7bc7265523bc3e687f3c7e1a1cb237ec08494ec3d1d"||leaf_source[0]!=std::byte{0xd9}||leaf_source[1]!=std::byte{0x05}||leaf_source[6]!=std::byte{0xc3}||operand!=data)throw std::invalid_argument("Actual provider source SHA/FLD-memory operand/RET extent differ");
  for(unsigned i=0;i<2;++i){r.memory().map({owned_.pages[i]},4096,Permissions::read|Permissions::write);owned_.owns[i]=true;r.memory().write({owned_.pages[i]},i?std::span<const std::byte>{data_page_}:std::span<const std::byte>{code_page_});r.memory().protect({owned_.pages[i]},i?Permissions::read:Permissions::read|Permissions::execute);}
  r.register_service({{slot},{m4_runtime::Abi::Cdecl,0,true},&service_adapter,"Exact MSVCP50 numeric_limits<float>::max x87 ST0 return",m4_runtime::Domain::admitted_game,provider_sha,p.gate_sha});
  for(auto [a,size,hash,callback]:std::array<std::tuple<unsigned,unsigned,const char*,m4_runtime::NativeEntry>,2>{{{root,10,"1147d8ad778df578820c4be4a4719d35cc4a4c39e0d74043bfdbc57909a261cc",&root_adapter},{body,117,"642aa130e093e1dc8e691b492ae650831cb9f60cf2428d2448e6c0a61fe1e3c5",&body_adapter}}})r.register_translation({{a},{m4_runtime::Abi::Cdecl,0,true},callback,"Exact connected numeric-max initializer",{m4_runtime::Domain::admitted_game,m4::admitted_image_hash,size,hash,p.native_sha,p.gate_sha}});
 }
 Session(const Session&)=delete;Session&operator=(const Session&)=delete;
 struct Borrow{Session&s;explicit Borrow(Session&v):s(v){if(owner||v.failed_||v.thread_!=std::this_thread::get_id())throw std::runtime_error("Numeric-max serial borrower rejected");owner=&v;}~Borrow(){owner=nullptr;}};
 [[noreturn]]void deny(const char*why,unsigned at=0){if(!failed_){failed_=true;fault_={s_.gpr.rip.dword,at,step_,why};}throw BridgeAbort{};}
 unsigned read(unsigned a){access(a,0);unsigned v{};try{v=r_.memory().load<unsigned>({a});}catch(...){deny("Checked numeric-max read fault",a);}if(a==data&&v!=data_word_)deny("Declared provider source input changed",a);log(a,v,0);return a==slot?slot:v;}
 void write(unsigned a,unsigned v){access(a,1);try{r_.memory().store<unsigned>({a},v);}catch(...){deny("Checked numeric-max write fault",a);}log(a,v,1);}
 void*dispatch_body(State*s,unsigned pc){guard();if(s!=&s_||pc!=body||level_||step_!=2||s_.gpr.rsp.dword!=frame_-8||r_.memory().load<unsigned>({frame_-8})!=0x4c19f8)deny("Actual wrapper direct CALL frame rejected");level_=1;sync();r_.cpu().esp+=4;r_.cpu().eip=0x4c19f3;r_.call_direct({body},{0x4c19f8});return this;}
 void*body_entry(State*s,unsigned pc){guard();if(s!=&s_||pc!=body||level_!=1||step_!=2||s_.gpr.rsp.dword!=frame_-8||s_.gpr.rbp.dword!=frame_-4)deny("Complete body actual entry rejected");return this;}
 void*call(State*s,unsigned pc){guard();if(s!=&s_||pc!=slot||level_!=1||step_!=5||s_.gpr.rsp.dword!=frame_-16||r_.memory().load<unsigned>({frame_-16})!=0x4c1a09)deny("Actual game MSVCP50 CALL frame rejected");level_=2;sync();r_.cpu().esp+=4;r_.cpu().eip=0x4c1a03;r_.call_import({slot},{0x4c1a09});return this;}
 void*returned(State*s,unsigned pc){guard();if(s!=&s_||s_.gpr.rip.dword!=pc)deny("Returned State/PC identity rejected");if(level_==2){if(pc!=0x4c1a09||s_.gpr.rsp.dword!=frame_-12||step_!=7)deny("Actual x87 ST0 provider return rejected");checkpoint_=view(s_);level_=1;}else if(level_==1){if(pc!=0x4c19f8||s_.gpr.rsp.dword!=frame_-4||step_!=20)deny("Actual complete body return rejected");level_=0;}else{source_check();if(complete_||pc!=ret_||s_.gpr.rsp.dword!=frame_+4||step_!=22)deny("Actual wrapper RET closure rejected");complete_=true;}++returns_;return this;}
 void clear(unsigned m){guard();if(m!=127||clears_||tests_)deny("Actual FPU clear boundary rejected");++clears_;__asm__ volatile("fnclex":::"memory");}
 unsigned test(unsigned m){guard();if(m!=127||clears_!=1||tests_)deny("Actual FPU test boundary rejected");++tests_;std::uint16_t sw;__asm__ volatile("fnstsw %0":"=m"(sw)::"memory");return sw&m;}
 void commit(State*s,bool push){guard();if(s!=&s_)deny("Physical tag State identity rejected");auto top=(s_.x87.fxsave.swd.flat>>11)&7;if(push){if(commits_||level_!=2||s_.gpr.rip.dword!=leaf||step_!=6||(s_.x87.fxsave.ftw.flat&(1<<top)))deny("Actual FLD physical tag commit rejected");s_.x87.fxsave.ftw.flat|=1<<top;}else{auto old=(top+7)&7;if(commits_!=1||level_!=1||s_.gpr.rip.dword!=0x4c1a09||step_!=8||!(s_.x87.fxsave.ftw.flat&(1<<old)))deny("Actual FSTP physical tag commit rejected");s_.x87.fxsave.ftw.flat&=~(1<<old);}++commits_;}
 auto fault()const{return fault_;}bool failed()const{return failed_;}bool running()const{return running_;}unsigned step()const{return step_;}bool complete()const{return complete_;}const auto&events()const{return events_;}const auto&checkpoint()const{return checkpoint_;}m4_runtime::Runtime&runtime(){return r_;}State&state(){return s_;}unsigned raw_iat()const{return raw_iat_;}
};
}
extern "C" unsigned mw34_nmx_read32(void*p,unsigned a){return static_cast<mw34::m4_nmx_integration::Session*>(p)->read(a);}
extern "C" void*mw34_nmx_write32(void*p,unsigned a,unsigned v){static_cast<mw34::m4_nmx_integration::Session*>(p)->write(a,v);return p;}
extern "C" float mw34_nmx_readf32(void*p,unsigned a){return std::bit_cast<float>(static_cast<mw34::m4_nmx_integration::Session*>(p)->read(a));}
extern "C" void*mw34_nmx_writef32(void*p,unsigned a,float v){static_cast<mw34::m4_nmx_integration::Session*>(p)->write(a,std::bit_cast<unsigned>(v));return p;}
extern "C" void*mw34_nmx_dispatch_body(State*s,unsigned pc,void*p){return static_cast<mw34::m4_nmx_integration::Session*>(p)->dispatch_body(s,pc);}
extern "C" void*mw34_nmx_body_entry(State*s,unsigned pc,void*p){return static_cast<mw34::m4_nmx_integration::Session*>(p)->body_entry(s,pc);}
extern "C" void*mw34_nmx_call(State*s,unsigned pc,void*p){return static_cast<mw34::m4_nmx_integration::Session*>(p)->call(s,pc);}
extern "C" void*mw34_nmx_return(State*s,unsigned pc,void*p){return static_cast<mw34::m4_nmx_integration::Session*>(p)->returned(s,pc);}
extern "C" void mw34_nmx_clear(unsigned m){auto*c=mw34::m4_nmx_integration::owner;if(!c)throw mw34::m4_nmx_integration::BridgeAbort{};c->clear(m);}
extern "C" unsigned mw34_nmx_test(unsigned m){auto*c=mw34::m4_nmx_integration::owner;if(!c)throw mw34::m4_nmx_integration::BridgeAbort{};return c->test(m);}
extern "C" void mw34_nmx_fld_commit(State*s,void*p){static_cast<mw34::m4_nmx_integration::Session*>(p)->commit(s,true);}
extern "C" void mw34_nmx_fstp_commit(State*s,void*p){static_cast<mw34::m4_nmx_integration::Session*>(p)->commit(s,false);}
