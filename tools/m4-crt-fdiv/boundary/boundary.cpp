// Direct authored AMD64 call-boundary capture; no original instructions execute.
#include "registry.hpp"
#include <iostream>
using namespace mw34;namespace fd=mw34::m4_crt_fdiv;
struct alignas(16) Capture{std::array<std::byte,512>fx;std::array<std::byte,28>env;};
static_assert(offsetof(Capture,env)==512);
extern "C" bool fd_boundary_call(fd::Registry*,Capture*,Capture*,const Capture*);
extern "C" bool fd_boundary_initialize(fd::Registry*r)noexcept{return r->initialize();}
namespace{
unsigned checks{};void check(bool v,const char*m){++checks;if(!v)throw std::runtime_error(m);}
void seed(m4_runtime::Runtime&r){State s{};s.gpr.rax.dword=0x13579bdf;s.gpr.rcx.dword=0x2468ace0;s.gpr.rdx.dword=0x81726354;s.gpr.rbx.dword=0x10293847;s.gpr.rsp.dword=fd::entry_esp;s.gpr.rbp.dword=0x92837465;s.gpr.rsi.dword=0x56473829;s.gpr.rdi.dword=0xaabbccdd;s.gpr.rip.dword=fd::writer;s.addr.fs_base.dword=r.fs_base().value;s.rflag.flat=0x202;s.x87.fxsave.cwd.flat=0x37f;s.x87.fxsave.mxcsr.flat=0x1f80;s.x87.fxsave.mxcsr_mask.flat=0x2ffff;std::memcpy(r.remill_state().data(),&s,3504);std::memcpy(r.fx().data(),&s.x87,512);r.mark_remill_seeded();r.memory().store<unsigned>({fd::entry_esp},fd::outer_return);}
void restore(const Capture&c){__asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(c.fx),"m"(c.env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");}
class Output{HANDLE h_;public:explicit Output(const char*p){h_=CreateFileA(p,GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);check(h_!=INVALID_HANDLE_VALUE,"Fresh private boundary output");}~Output(){if(h_!=INVALID_HANDLE_VALUE)CloseHandle(h_);}void write(const void*p,unsigned n){DWORD done{};check(WriteFile(h_,p,n,&done,nullptr)&&done==n,"Complete boundary raw write");}};
}
int main(int argc,char**argv){try{check(argc==5,"Boundary: exact game/provider/pack/fresh output");auto game=fd::readfile(argv[1],2384384),provider=fd::readfile(argv[2],266293),pack=fd::readfile(argv[3],28740);Output out(argv[4]);
 for(unsigned mode=0;mode<2;++mode){auto runtime=m4_runtime::Runtime::from_admitted_image(game);seed(runtime);fd::Registry registry(runtime);check(registry.admit(provider,pack),"Boundary exact literal admission");if(mode)runtime.memory().protect({0x78037000},Permissions::read);Capture host{},before{},after{};__asm__ volatile("fxsave64 %0\n\tfnstenv %1":"=m"(host.fx),"=m"(host.env)::"memory");restore(host);Capture seeded=host;for(unsigned i=6;i<16;++i)for(unsigned j=0;j<16;++j)seeded.fx[160+16*i+j]=std::byte(static_cast<unsigned char>(i*31+j*17+mode+1));auto ok=fd_boundary_call(&registry,&before,&after,&seeded);restore(host);
  check(ok==!mode,"Actual positive/fault registry return status");check(before.env==after.env,"Outside call complete legacy ENV28 preserved");check(std::equal(before.fx.begin(),before.fx.begin()+5,after.fx.begin())&&std::equal(before.fx.begin()+24,before.fx.begin()+28,after.fx.begin()+24),"Outside call x87 CW/SW/FTW and full MXCSR preserved");for(unsigned i=0;i<8;++i)check(std::equal(before.fx.begin()+32+16*i,before.fx.begin()+42+16*i,after.fx.begin()+32+16*i),"Outside call all physical raw80 storage preserved");for(unsigned i=6;i<16;++i)check(std::equal(before.fx.begin()+160+16*i,before.fx.begin()+176+16*i,after.fx.begin()+160+16*i),"Outside call each ABI nonvolatile XMM6..15 preserved");check(std::any_of(before.fx.begin()+256,before.fx.begin()+416,[](auto b){return b!=std::byte{};}),"Actual nonzero ABI SIMD sentinels reached boundary");out.write(&mode,4);out.write(&before,sizeof(before));out.write(&after,sizeof(after));
 }
 std::cout<<"{\"passed\":true,\"checks\":"<<checks<<",\"scenarios\":2,\"direct_assembly_boundary\":true,\"original_execution\":false,\"volatile_XMM0_5_equality_claimed\":false}\n";return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
