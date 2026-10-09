// Independent observer seed. This never changes the guest State or Runtime FX.
namespace {
unsigned review_checks{},review_hook_hits{},review_case{},review_thread_units{};
void review_check(bool okay,const char*why){++review_checks;require(okay,why);}
void review_seed(std::array<std::byte,512>&fx,std::array<std::byte,28>&env){
 struct alignas(16) H{std::array<std::byte,512>fx;std::array<std::byte,28>env;};H old{},rich{};
 __asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfldenv %1":"=m"(old.fx),"=m"(old.env)::"memory");
 unsigned mxcsr=0x5fa5;unsigned short cw=0xa7f;
 __asm__ volatile("fninit\n\tfld1\n\tfldpi\n\tfldz\n\tfld1\n\tfdivp\n\tfldcw %0\n\tldmxcsr %1"::"m"(cw),"m"(mxcsr):"memory","st","st(1)","st(2)","st(3)");
 __asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfldenv %1":"=m"(rich.fx),"=m"(rich.env)::"memory");
 __asm__ volatile("fxrstor64 %0\n\tfldenv %1"::"m"(old.fx),"m"(old.env):"memory","st","st(1)","st(2)","st(3)","st(4)","st(5)","st(6)","st(7)","xmm0","xmm1","xmm2","xmm3","xmm4","xmm5","xmm6","xmm7","xmm8","xmm9","xmm10","xmm11","xmm12","xmm13","xmm14","xmm15");
 fx=rich.fx;env=rich.env;
}
}
