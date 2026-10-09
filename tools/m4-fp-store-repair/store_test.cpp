// This normal host ABI is called only by the exact checked static FSTP site.
// Capture the hardware status; do not infer rounding from input/output values.
#include <remill/Arch/X86/Runtime/State.h>
#include <cstdint>
extern "C" unsigned __remill_fpu_exception_test(unsigned);
extern "C" unsigned mw34_fp_store_exception_test(State *state,unsigned mask){
    // The existing context bridge validates the active owner, mask and exact
    // clear/test ordering. Its bounded fault escape occurs before this store.
    const auto exceptions=__remill_fpu_exception_test(mask);
    std::uint16_t status;__asm__ volatile("fnstsw %0":"=m"(status)::"memory");
    state->sw.c1=(status>>9)&1;
    return exceptions;
}
