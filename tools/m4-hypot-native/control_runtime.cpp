// Finite, fully masked x87 control transfers. Source State owns the guest CW.
// The enclosing fixture owns hardware isolation and the memory/thread context.
#include <remill/Arch/X86/Runtime/State.h>
#include <cstdint>
#include <stdexcept>

extern "C" void mw34_hypot_control_admit(State *, void *);
extern "C" std::uint16_t mw34_hypot_read_memory_16(void *, std::uint32_t);
extern "C" void *mw34_hypot_write_memory_16(void *, std::uint32_t, std::uint16_t);

namespace {
constexpr std::uint16_t normalized(std::uint16_t word) {
    return (word & 0x1f3fU) | 0x40U;
}
void admit(State *state, void *context) {
    mw34_hypot_control_admit(state, context);
    const auto word = state->x87.fxsave.cwd.flat;
    if (word != normalized(word) || (word & 63U) != 63U)
        throw std::runtime_error("Unadmitted guest CW or pending exception domain");
    std::uint16_t actual;
    __asm__ volatile("fnstcw %0" : "=m"(actual) :: "memory");
    if (actual != word)
        throw std::runtime_error("Guest CW differs from isolated hardware CW");
}
}

extern "C" void *mw34_hypot_store_cw(State *state, std::uint32_t address, void *context) {
    admit(state, context);
    return mw34_hypot_write_memory_16(context, address, state->x87.fxsave.cwd.flat);
}

extern "C" void *mw34_hypot_load_cw(State *state, std::uint32_t address, void *context) {
    admit(state, context);
    const auto word = normalized(mw34_hypot_read_memory_16(context, address));
    if ((word & 63U) != 63U)
        throw std::runtime_error("Unmasked guest exceptions require a separate source domain");
    __asm__ volatile("fldcw %0" :: "m"(word) : "memory");
    state->x87.fxsave.cwd.flat = word;
    return context;
}

extern "C" void *mw34_hypot_wait(State *state, void *context) {
    admit(state, context);
    // FWAIT retains masked sticky flags and every occupied x87 stack register.
    __asm__ volatile("fwait" ::: "memory");
    return context;
}
