// Normal typed pointer ABI; actual ten-byte FCOS, no C++ long double.
#include <remill/Arch/X86/Runtime/State.h>
#include <cstdint>
struct Raw80 {std::uint8_t bytes[10];};
extern "C" void mw34_cosine_primitive_admit();
extern "C" void mw34_actual_fcos_status_raw80(State *state,const Raw80 *input,Raw80 *output){
    mw34_cosine_primitive_admit();
    std::uint16_t status;
    // Capture FCOS condition flags before the transport store changes C1.
    __asm__ volatile("fldt %2\n\tfcos\n\tfnstsw %0\n\tfstpt %1"
      :"=m"(status),"=m"(*output):"m"(*input):"memory","st");
    state->sw.c2=(status>>10)&1;
}
