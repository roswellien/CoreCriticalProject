// Explicit owned ten-byte pointer ABI; actual x87 instructions only.
#include <cstdint>
#include <remill/Arch/X86/Runtime/State.h>
struct Raw80 {std::uint8_t bytes[10];};
extern "C" void mw34_sincos_primitive_admit(unsigned operation);
extern "C" void mw34_actual_fcos_raw80(const Raw80 *input,Raw80 *output){
 mw34_sincos_primitive_admit(0);__asm__ volatile("fldt %1\n\tfcos\n\tfstpt %0":"=m"(*output):"m"(*input):"memory","st");
}
extern "C" void mw34_actual_fsin_raw80(const Raw80 *input,Raw80 *output){
 mw34_sincos_primitive_admit(1);__asm__ volatile("fldt %1\n\tfsin\n\tfstpt %0":"=m"(*output):"m"(*input):"memory","st");
}
extern "C" void mw34_actual_fcos_status_raw80(State *state,const Raw80 *input,Raw80 *output){
 mw34_sincos_primitive_admit(0);std::uint16_t status;
 __asm__ volatile("fldt %2\n\tfcos\n\tfnstsw %0\n\tfstpt %1":"=m"(status),"=m"(*output):"m"(*input):"memory","st");state->sw.c2=(status>>10)&1;
}
extern "C" void mw34_actual_fsin_status_raw80(State *state,const Raw80 *input,Raw80 *output){
 mw34_sincos_primitive_admit(1);std::uint16_t status;
 __asm__ volatile("fldt %2\n\tfsin\n\tfnstsw %0\n\tfstpt %1":"=m"(status),"=m"(*output):"m"(*input):"memory","st");state->sw.c2=(status>>10)&1;
}
