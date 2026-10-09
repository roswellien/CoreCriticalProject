// Actual compiled provider definitions; original AFTER fields are never read.
#include "native_context.hpp"
#include "probe_io.hpp"
#include "probe_spec.hpp"
#include "replay_spec.hpp"
#include <iostream>
using namespace mw34;using namespace mw34::m4_crt_probe;namespace cf=mw34::m4_crt_control;
extern "C" void*sub_780042e1(State*,std::uint32_t,void*);
extern "C" void*sub_780042f7(State*,std::uint32_t,void*);
namespace {
template<class T>T get(const std::uint8_t*p){T v{};std::memcpy(&v,p,sizeof(v));return v;}
Cpu cpu(const State&s){return {s.gpr.rax.dword,s.gpr.rcx.dword,s.gpr.rdx.dword,s.gpr.rbx.dword,s.gpr.rsp.dword,s.gpr.rbp.dword,s.gpr.rsi.dword,s.gpr.rdi.dword,static_cast<std::uint32_t>((s.rflag.flat&~0xcd5ULL)|(s.aflag.cf<<0)|(s.aflag.pf<<2)|(s.aflag.af<<4)|(s.aflag.zf<<6)|(s.aflag.sf<<7)|(s.aflag.df<<10)|(s.aflag.of<<11)),s.gpr.rip.dword};}
void initialize(State&s,const Cpu&c,const std::uint8_t*fx,const std::uint8_t*env,unsigned seed){
 auto*b=reinterpret_cast<std::uint8_t*>(&s);for(unsigned i=0;i<3504;++i)b[i]=static_cast<std::uint8_t>(i*13+seed+7);s.addr.ds_base.dword=s.addr.ss_base.dword=0;s.addr.fs_base.dword=0x7ffde000;
 s.gpr.rax.dword=c.eax;s.gpr.rcx.dword=c.ecx;s.gpr.rdx.dword=c.edx;s.gpr.rbx.dword=c.ebx;s.gpr.rsp.dword=c.esp;s.gpr.rbp.dword=c.ebp;s.gpr.rsi.dword=c.esi;s.gpr.rdi.dword=c.edi;s.gpr.rip.dword=c.pc;s.rflag.flat=c.flags;
 s.aflag.cf=(c.flags>>0)&1;s.aflag.pf=(c.flags>>2)&1;s.aflag.af=(c.flags>>4)&1;s.aflag.zf=(c.flags>>6)&1;s.aflag.sf=(c.flags>>7)&1;s.aflag.df=(c.flags>>10)&1;s.aflag.of=(c.flags>>11)&1;
 std::memset(&s.sw,0,sizeof(s.sw));std::memcpy(&s.x87,fx,512);auto&f=s.x87.fxsave;f.ip=get<std::uint32_t>(env+12);f.cs.flat=get<std::uint16_t>(env+16);f.fop=get<std::uint16_t>(env+18);f.dp=get<std::uint32_t>(env+20);f.ds.flat=get<std::uint16_t>(env+24);
 for(unsigned i=0;i<8;++i){std::memcpy(&s.st.elems[i].val,fx+32+16*i,10);std::memcpy(&s.vec[i],fx+160+16*i,16);}
}
std::array<std::uint8_t,28>legacy(const State&s,const std::uint8_t*reserved){std::array<std::uint8_t,28>r{};std::memcpy(r.data(),reserved,28);const auto&f=s.x87.fxsave;put16(r.data(),f.cwd.flat);put16(r.data()+4,f.swd.flat);need(f.ftw.flat==0,"Native empty physical tags required");put16(r.data()+8,0xffff);put32(r.data()+12,f.ip);put16(r.data()+16,f.cs.flat);put16(r.data()+18,f.fop);put32(r.data()+20,f.dp);put16(r.data()+24,f.ds.flat);return r;}
struct HostScope{
 struct alignas(16) Image{std::uint8_t bytes[512];};Image before{},after{};std::uint8_t env[28]{},env_after[28]{};
 HostScope(){__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(before),"=m"(env)::"memory");}
 void restore(){__asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(before),"m"(env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
 void capture(){restore();__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(after),"=m"(env_after)::"memory");}
 ~HostScope(){restore();}
};
}
int main(int argc,char**argv){try{
 if(argc==2&&std::string(argv[1])=="--check-hash"){hash_controls();std::cout<<"2 SHA controls passed\n";return 0;}
 need(argc==4,"CRT control native: exact-pack actual-original fresh-output");const auto pack=read(argv[1],8220);need(pack.size()==8220&&digest(pack)==cf::pack_sha,"Pack identity rejected");const auto original=read(argv[2],34128408);need(original.size()==34128408&&digest(original)==cf::original_sha,"Actual original input identity rejected");need(std::memcmp(original.data(),"MW4CFC01",8)==0,"Actual original version rejected");const std::uint32_t expected[]{1,cf::records,cf::original_stride,4096};need(std::memcmp(original.data()+8,expected,16)==0,"Actual original header rejected");
 GuestMemory memory;memory.map(GuestAddress{0x20001000},4096,Permissions::read|Permissions::write);for(unsigned i=0;i<2;++i){const unsigned offset=12+i*4104;const auto base=get<std::uint32_t>(pack.data()+offset);need(base==(i?0x78011000U:0x78004000U),"Native actual code page layout");memory.map(GuestAddress{base},4096,Permissions::read|Permissions::write);memory.write(GuestAddress{base},std::as_bytes(std::span(pack.data()+offset+8,4096)));memory.protect(GuestAddress{base},Permissions::read|Permissions::execute);}
 Output out(argv[3]);out.write("MW4CFN01",8);const std::uint32_t header[]{1,cf::records,17596,3504};out.write(header,16);
 for(unsigned i=0;i<cf::records;++i){
  const auto*r=original.data()+24+i*cf::original_stride;const auto entry=get<std::uint32_t>(r+4);need(entry<2,"Actual original selected entry");const auto before_cpu=get<Cpu>(r+24);need(before_cpu.pc==cf::entries[entry],"Actual original input PC");const auto*before_fx=r+104;const auto*before_env=r+2152;const auto*before_mem=r+2264;
  memory.write(GuestAddress{0x20001000},std::as_bytes(std::span(before_mem,4096)));State state{};initialize(state,before_cpu,before_fx,before_env,i);std::array<std::byte,512>fx{};std::memcpy(fx.data(),before_fx,512);cf::Context context(memory,state,fx);std::array<std::byte,3504>s0{},s1{};std::memcpy(s0.data(),&state,3504);const auto actual_before=cpu(state);const auto f0=fx;const auto e0=legacy(state,before_env);Cpu after_cpu{};std::array<std::byte,4096>after_mem{};std::array<std::uint8_t,512>h0{},h1{};std::array<std::uint8_t,28>he0{},he1{};
  {
   HostScope host;
   if(setjmp(context.boundary)==0){auto*result=(entry?sub_780042f7:sub_780042e1)(&state,before_cpu.pc,&context);if(result!=&context||context.depth)context.deny("Compiled provider result/frame closure rejected");}
   need(!context.failed,context.reason?context.reason:"Required compiled execution fault");after_cpu=cpu(state);std::memcpy(s1.data(),&state,3504);memory.read(GuestAddress{0x20001000},after_mem);host.capture();std::memcpy(h0.data(),host.before.bytes,512);std::memcpy(h1.data(),host.after.bytes,512);std::memcpy(he0.data(),host.env,28);std::memcpy(he1.data(),host.env_after,28);
  }
  const auto e1=legacy(state,before_env);need(h0==h1&&he0==he1,"Full captured native host restoration failed");out.write(r,24);out.write(&actual_before,40);out.write(&after_cpu,40);out.write(f0.data(),512);out.write(fx.data(),512);out.write(e0.data(),28);out.write(e1.data(),28);out.write(s0.data(),3504);out.write(s1.data(),3504);out.write(before_mem,4096);out.write(after_mem.data(),4096);out.write(&context.count,4);out.write(context.events.data(),128);out.write(h0.data(),512);out.write(h1.data(),512);out.write(he0.data(),28);out.write(he1.data(),28);
 }
 out.commit();std::cout<<"3264 actual native complete CRT control records captured; integration pending\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
