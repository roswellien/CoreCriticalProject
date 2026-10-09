// Bounded native research: literal translated CRT entry to its first missing
// service. This is not startup admission or a native game launcher.
#include "runtime.hpp"
#include "admission.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <thread>
using namespace mw34;
namespace {
using namespace m4_runtime;
constexpr unsigned entry=0x5ac3a0,frame=0x20001900,slot=0x5bb5a4;
extern "C" void *sub_5ac3a0(State*,unsigned,void*) noexcept(false);
void require(bool b,const char *reason){if(!b)throw std::runtime_error(reason);}
std::vector<std::byte> read_file(const char *name){std::ifstream f(name,std::ios::binary|std::ios::ate);require(bool(f),"Input open failed");auto size=f.tellg();require(size>0&&size<64*1024*1024,"Bounded input size");std::vector<std::byte>b(static_cast<std::size_t>(size));f.seekg(0);f.read(reinterpret_cast<char*>(b.data()),static_cast<std::streamsize>(b.size()));require(bool(f),"Complete input read");return b;}
void output(const std::string&path,std::span<const std::byte>b){std::ofstream f(path,std::ios::binary);require(bool(f),"Fresh output open failed");f.write(reinterpret_cast<const char*>(b.data()),static_cast<std::streamsize>(b.size()));require(bool(f),"Complete output write");}
Cpu32 cpu(const State&s){return {s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword,static_cast<unsigned>((s.rflag.flat&~0xcd5ULL)|(s.aflag.cf<<0)|(s.aflag.pf<<2)|(s.aflag.af<<4)|(s.aflag.zf<<6)|(s.aflag.sf<<7)|(s.aflag.df<<10)|(s.aflag.of<<11)),s.gpr.rip.dword};}
void project(State&s,const Cpu32&c){s.gpr.rax.dword=c.eax;s.gpr.rcx.dword=c.ecx;s.gpr.rdx.dword=c.edx;s.gpr.rbx.dword=c.ebx;s.gpr.rsp.dword=c.esp;s.gpr.rbp.dword=c.ebp;s.gpr.rsi.dword=c.esi;s.gpr.rdi.dword=c.edi;s.gpr.rip.dword=c.eip;s.rflag.flat=c.eflags;s.aflag.cf=(c.eflags>>0)&1;s.aflag.pf=(c.eflags>>2)&1;s.aflag.af=(c.eflags>>4)&1;s.aflag.zf=(c.eflags>>6)&1;s.aflag.sf=(c.eflags>>7)&1;s.aflag.df=(c.eflags>>10)&1;s.aflag.of=(c.eflags>>11)&1;}
struct Event{unsigned pc,address,value,width,write;};
class Context;
thread_local Context*owner{};
class Context {
 Runtime&r_;State&s_;std::thread::id thread_=std::this_thread::get_id();
 std::vector<Event>events_;bool running_{};
public:
 Context(Runtime&r,const std::string&native_sha):r_(r),s_(*std::construct_at(reinterpret_cast<State*>(r.remill_state().data()))){
  for(unsigned i=0;i<3504;++i)r.remill_state()[i]=std::byte(static_cast<unsigned char>(i*31+3));
  std::memset(&s_.addr,0,sizeof(s_.addr));s_.addr.fs_base.dword=r.fs_base().value;s_.seg.cs.flat=0x23;s_.seg.ds.flat=s_.seg.ss.flat=0x2b;
  project(s_,{0x13579bdf,0x2468ace0,0x81726354,0x10293847,frame,0x92837465,0x56473829,0xaabbccdd,0x202,entry});
  std::memset(&s_.x87,0,sizeof(s_.x87));s_.x87.fxsave.cwd.flat=0x37f;s_.x87.fxsave.mxcsr.flat=0x1f80;s_.x87.fxsave.mxcsr_mask.flat=0x2ffff;
  s_.sw.ie=s_.sw.de=s_.sw.ze=s_.sw.oe=s_.sw.ue=s_.sw.pe=s_.sw.sf=s_.sw.c0=s_.sw.c1=s_.sw.c2=s_.sw.c3=0;
  r.cpu()=cpu(s_);r.cpu().esp+=4;r.cpu().eip=Runtime::external_return;
  std::memcpy(r.fx().data(),&s_.x87,512);r.mark_remill_seeded();
  r.register_translation({{entry},{Abi::Cdecl,0,true},&adapter,"Unaccepted complete CRT entry first-fault probe",{Domain::admitted_game,m4::admitted_image_hash,430,"30da37cdf0ae957fc87f6e0caf250b4a60e0e63767dea24935381791e60ad856",native_sha,"0c67cae86dad6468e082607ebe9d2b2504094829adb28e37b0c082d6e158d724"}});
 }
 static void adapter(Runtime&r){require(owner && &owner->r_==&r,"Entry owner absent");owner->run();}
 void guard(){require(owner==this&&running_&&thread_==std::this_thread::get_id(),"Stable serial entry ownership required");}
 void run(){require(!running_&&thread_==std::this_thread::get_id()&&r_.remill_seeded(),"Fresh serial entry required");std::vector<std::byte>source(430);r_.memory().read({entry},source);require(m4::sha256(source)=="30da37cdf0ae957fc87f6e0caf250b4a60e0e63767dea24935381791e60ad856","Current original entry identity");project(s_,r_.cpu());running_=true;try{(void)sub_5ac3a0(&s_,entry,this);throw std::runtime_error("Unexpected complete entry return");}catch(...){running_=false;throw;}}
 unsigned read(unsigned a,unsigned width){guard();require(width==4,"Only reached DWORD reads admitted");auto v=r_.memory().load<unsigned>({a});events_.push_back({s_.gpr.rip.dword,a,v,width,0});return v;}
 void write(unsigned a,unsigned v){guard();r_.memory().store<unsigned>({a},v);events_.push_back({s_.gpr.rip.dword,a,v,4,1});}
 void*call(State*s,unsigned target){guard();require(s==&s_&&events_.size()==15&&events_[13].pc==0x5ac3cf&&events_[13].address==slot&&events_[13].write==0&&events_[13].value==target&&events_[14].pc==0x5ac3cf&&events_[14].address==frame-144&&events_[14].value==0x5ac3d5,"Actual first source CALL/IAT/guest frame required");require(s_.gpr.rsp.dword==frame-144&&r_.memory().load<unsigned>({frame-144})==0x5ac3d5,"Literal first guest return frame");
  r_.cpu()=cpu(s_);r_.cpu().esp+=4;r_.cpu().eip=0x5ac3cf;
  r_.call_import({slot},{0x5ac3d5});throw std::runtime_error("Unexpected first missing-service completion");
 }
 void invoke(){require(!owner,"No nested entry owner");owner=this;try{r_.invoke({entry});}catch(...){owner=nullptr;throw;}owner=nullptr;}
 const auto&events()const{return events_;}State&state(){return s_;}
};
}
extern "C" unsigned __remill_read_memory_32(void*p,unsigned a) noexcept(false) {return static_cast<Context*>(p)->read(a,4);}
extern "C" unsigned char __remill_read_memory_8(void*,unsigned) noexcept(false) {throw std::runtime_error("Unreached required byte-read bridge");}
extern "C" void*__remill_write_memory_32(void*p,unsigned a,unsigned v) noexcept(false) {static_cast<Context*>(p)->write(a,v);return p;}
extern "C" void*__remill_function_call(State*s,unsigned a,void*p) noexcept(false) {return static_cast<Context*>(p)->call(s,a);}
extern "C" void*__remill_function_return(State*,unsigned,void*) noexcept(false) {throw std::runtime_error("Unreached required return bridge");}
extern "C" void*__remill_jump(State*,unsigned,void*) noexcept(false) {throw std::runtime_error("Unreached required jump bridge");}
extern "C" void*mw34_crte_direct(State*,unsigned,void*) noexcept(false) {throw std::runtime_error("Unreached required direct-call bridge");}
extern "C" void*mw34_crte_enter(State*s,unsigned a,void*p) noexcept(false) {auto*c=static_cast<Context*>(p);c->guard();require(s==&c->state()&&a==entry,"Only actual ordinary entry reached");return p;}
extern "C" unsigned char __remill_undefined_8() noexcept(false) {throw std::runtime_error("Unreached undefined flag representative");}
int main(int argc,char**argv){try{
 require(argc==4,"Usage: exact-image exact-entry-object fresh-output-directory");const auto image=read_file(argv[1]),object=read_file(argv[2]);require(m4::sha256(image)==m4::admitted_image_hash,"Exact game image");
 const std::filesystem::path directory=argv[3];require(!std::filesystem::exists(directory),"Fresh output required");std::filesystem::create_directory(directory);
 Policy policy;policy.stack_low={0x20001000};policy.stack_bytes=4096;policy.heap_bytes=4096;
 auto r=Runtime::from_admitted_image(image,policy);Context c(r,m4::sha256(object));r.freeze_registry();
 const std::array<unsigned,2>pages{0x20001000,0x5bb000};
 auto capture=[&](const char*tag){output((directory/(std::string(tag)+"-state.bin")).string(),r.remill_state());output((directory/(std::string(tag)+"-cpu.bin")).string(),{reinterpret_cast<const std::byte*>(&r.cpu()),sizeof(Cpu32)});output((directory/(std::string(tag)+"-fx.bin")).string(),r.fx());for(auto a:pages){std::array<std::byte,4096>data{};r.memory().read({a},data);output((directory/(std::string(tag)+"-page-"+std::to_string(a)+".bin")).string(),data);}for(auto [offset,size]:std::array<std::pair<unsigned,unsigned>,3>{{{0,4},{4,8},{0x18,4}}}){std::vector<std::byte>data(size);r.memory().read(r.fs_base().wrapping_add(offset),data);output((directory/(std::string(tag)+"-tib-"+std::to_string(offset)+".bin")).string(),data);}};
 capture("before");bool denied=false;FaultReason reason{};unsigned fault_pc{},fault_target{};std::string detail;
 try{c.invoke();}catch(const Fault&f){denied=true;reason=f.reason();fault_pc=f.site().value;fault_target=f.target().value;detail=f.what();}
 capture("after");require(denied&&reason==FaultReason::unresolved_import&&fault_pc==0x5ac3cf&&fault_target==slot&&r.poisoned(),"Exact first missing-service denial");
 require(r.calls().size()==1&&!r.calls()[0].completed&&r.calls()[0].target.value==entry,"Entered root incomplete ledger");
 const auto chain=r.seh_chain();require(chain.size()==1&&chain[0].frame.value==frame-20&&chain[0].previous.value==0xffffffff&&chain[0].handler.value==0x5ac586,"Actual translated FS exception-frame installation");
 output((directory/"events.bin").string(),{reinterpret_cast<const std::byte*>(c.events().data()),c.events().size()*sizeof(Event)});
 const auto state=c.state();const auto count=c.events().size();bool retry=false;try{c.invoke();}catch(const Fault&f){retry=f.reason()==FaultReason::poisoned;}
 require(retry&&std::memcmp(&state,&c.state(),3504)==0&&c.events().size()==count,"Poisoned entry retry leaves State/events unchanged");
 std::ofstream report(directory/"result.json");report<<"{\"passed\":true,\"scope\":\"Native complete-entry first missing-service research; original comparison and independent admission pending\",\"source_events\":"<<count<<",\"first_call_pc\":"<<fault_pc<<",\"missing_IAT\":"<<fault_target<<",\"SEH_frame\":"<<chain[0].frame.value<<",\"SEH_dispatch_implemented\":false,\"poisoned_retry_denied\":true,\"original_executed\":false,\"full_CRT\":false,\"whole_M4_complete\":false}\n";require(bool(report),"Result publication");
 std::cout<<"Translated entry reached its first required CRT service; explicit missing-service denial preserved\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}

