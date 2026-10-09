// Actual hardware store C1, same typed boundary as the reviewed first repair.
// Context validates mask, thread owner and clear/test order before State write.
#include <remill/Arch/X86/Runtime/State.h>
#include <cstdint>
extern "C" unsigned __remill_fpu_exception_test(unsigned);
extern "C" unsigned mw34_fp_store_exception_test(State *state,unsigned mask){
    const auto exceptions=__remill_fpu_exception_test(mask);
    std::uint16_t status;__asm__ volatile("fnstsw %0":"=m"(status)::"memory");
    state->sw.c1=(status>>9)&1;
    return exceptions;
}
