// Honest unary-atan baseline, raw80 pointer ABI and actual x87 instructions.
#include <cstdint>
#include <remill/Arch/X86/Runtime/State.h>
struct Raw80 {std::uint8_t bytes[10];};
extern "C" void mw34_atan_primitive_admit(unsigned op);
extern "C" void mw34_actual_fatan_raw80(const Raw80 *input,Raw80 *output){
 mw34_atan_primitive_admit(0);__asm__ volatile("fldt %1\n\tfld1\n\tfpatan\n\tfstpt %0":"=m"(*output):"m"(*input):"memory","st","st(1)");
}
extern "C" void mw34_actual_fcos_raw80(const Raw80 *input,Raw80 *output){
 mw34_atan_primitive_admit(1);__asm__ volatile("fldt %1\n\tfcos\n\tfstpt %0":"=m"(*output):"m"(*input):"memory","st");
}
extern "C" void mw34_actual_fpatan_raw80(State *,const Raw80 *y,const Raw80 *x,Raw80 *output){
 mw34_atan_primitive_admit(0);__asm__ volatile("fldt %1\n\tfldt %2\n\tfpatan\n\tfstpt %0":"=m"(*output):"m"(*y),"m"(*x):"memory","st","st(1)");
}
extern "C" void mw34_actual_fcos_status_raw80(State *state,const Raw80 *input,Raw80 *output){
 mw34_atan_primitive_admit(1);std::uint16_t status;
 __asm__ volatile("fldt %2\n\tfcos\n\tfnstsw %0\n\tfstpt %1":"=m"(status),"=m"(*output):"m"(*input):"memory","st");state->sw.c2=(status>>10)&1;
}
