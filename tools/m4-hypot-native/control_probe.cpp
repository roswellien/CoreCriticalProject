// Hardware unit evidence only: no original AFTER values or numeric oracle.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <remill/Arch/X86/Runtime/State.h>
#include <array>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>

extern "C" void *mw34_hypot_store_cw(State *, std::uint32_t, void *);
extern "C" void *mw34_hypot_load_cw(State *, std::uint32_t, void *);
extern "C" void *mw34_hypot_wait(State *, void *);
static_assert(sizeof(State) == 3504 && sizeof(void *) == 8);
static void need(bool condition, const char *message) {
    if (!condition) throw std::runtime_error(message);
}
struct alignas(16) Hardware {
    std::array<std::uint8_t, 512> fx{};
    std::array<std::uint8_t, 28> env{};
};
static void snapshot(Hardware &out) {
    __asm__ volatile("fxsave64 %0\n\tfnstenv %1\n\tfxrstor64 %0\n\tfldenv %1"
        : "=m"(out.fx), "=m"(out.env) :: "memory");
}
struct Isolation {
    Hardware caller;
    Isolation() { snapshot(caller); }
    ~Isolation() {
        __asm__ volatile("fxrstor64 %0\n\tfldenv %1" :: "m"(caller.fx), "m"(caller.env)
            : "memory", "st", "st(1)", "st(2)", "st(3)", "st(4)", "st(5)", "st(6)", "st(7)",
              "xmm0", "xmm1", "xmm2", "xmm3", "xmm4", "xmm5", "xmm6", "xmm7",
              "xmm8", "xmm9", "xmm10", "xmm11", "xmm12", "xmm13", "xmm14", "xmm15");
    }
};
struct Context {
    State *state;
    DWORD thread;
    std::array<std::uint8_t, 12> memory{};
    unsigned reads{}, writes{}, admissions{};
};
extern "C" void mw34_hypot_control_admit(State *state, void *opaque) {
    auto *context = static_cast<Context *>(opaque);
    need(context && state && context->state == state && context->thread == GetCurrentThreadId(),
         "Exact active State/current-thread context required");
    ++context->admissions;
}
static Context &memory(void *opaque, std::uint32_t address) {
    auto &context = *static_cast<Context *>(opaque);
    need(context.thread == GetCurrentThreadId() && address >= 0x20001000 &&
         std::uint64_t{address} + 2 <= 0x2000100c, "Exact guest operand bounds required");
    return context;
}
extern "C" std::uint16_t mw34_hypot_read_memory_16(void *opaque, std::uint32_t address) {
    auto &context = memory(opaque, address);
    ++context.reads;
    std::uint16_t value;
    std::memcpy(&value, context.memory.data() + address - 0x20001000, 2);
    return value;
}
extern "C" void *mw34_hypot_write_memory_16(void *opaque, std::uint32_t address, std::uint16_t value) {
    auto &context = memory(opaque, address);
    ++context.writes;
    std::memcpy(context.memory.data() + address - 0x20001000, &value, 2);
    return opaque;
}
static void same_x87(const Hardware &before, const Hardware &after, std::uint16_t word) {
    auto expected = before;
    std::memcpy(expected.fx.data(), &word, 2);
    std::memcpy(expected.env.data(), &word, 2);
    need(std::memcmp(expected.fx.data(), after.fx.data(), 24) == 0,
         "Complete x87 FX header except the declared CW transfer");
    need(expected.env == after.env, "Complete legacy x87 environment except the declared CW transfer");
    for (unsigned i = 0; i < 8; ++i)
        need(std::memcmp(expected.fx.data() + 32 + i * 16, after.fx.data() + 32 + i * 16, 10) == 0,
             "Every occupied or empty hardware raw80 backing retained");
}
static void setup(std::uint16_t cw, unsigned occupied, unsigned sticky) {
    __asm__ volatile("fninit\n\tfldcw %0" :: "m"(cw) : "memory", "st", "st(1)", "st(2)",
                     "st(3)", "st(4)", "st(5)", "st(6)", "st(7)");
    for (unsigned i = 0; i < occupied; ++i)
        __asm__ volatile("fld1" ::: "memory", "st");
    if (sticky) {
        Hardware image;
        snapshot(image);
        std::uint16_t sw;
        std::memcpy(&sw, image.env.data() + 4, 2);
        sw |= 0x20; // Explicit authored masked PE unit input, never a game result.
        std::memcpy(image.env.data() + 4, &sw, 2);
        __asm__ volatile("fldenv %0" :: "m"(image.env) : "memory");
    }
}
static void probe(std::uint16_t before_word, std::uint16_t supplied, unsigned occupied, unsigned sticky) {
    Isolation isolation;
    setup(before_word, occupied, sticky);
    State state;
    std::memset(&state, 0xa5, sizeof(state));
    state.x87.fxsave.cwd.flat = before_word;
    Context context{&state, GetCurrentThreadId()};
    context.memory.fill(0x96);
    std::memcpy(context.memory.data() + 5, &supplied, 2);
    const State saved = state;
    const auto memory_before = context.memory;
    Hardware before, after;
    snapshot(before);
    need(mw34_hypot_store_cw(&state, 0x20001001, &context) == &context, "Store returns exact context");
    need(mw34_hypot_wait(&state, &context) == &context, "Wait returns exact context");
    snapshot(after);
    need(std::memcmp(&state, &saved, sizeof(state)) == 0, "Store and wait conserve whole State");
    auto expected_memory = memory_before;
    std::memcpy(expected_memory.data() + 1, &before_word, 2);
    need(context.memory == expected_memory, "Exactly two operand bytes published");
    same_x87(before, after, before_word);
    need(mw34_hypot_load_cw(&state, 0x20001005, &context) == &context, "Load returns exact context");
    snapshot(after);
    const auto normalized = static_cast<std::uint16_t>((supplied & 0x1f3fU) | 0x40U);
    auto expected_state = saved;
    expected_state.x87.fxsave.cwd.flat = normalized;
    need(std::memcmp(&state, &expected_state, sizeof(state)) == 0, "Exactly the State CW field changes");
    need(context.memory == expected_memory, "Load conserves whole source memory");
    same_x87(before, after, normalized);
    need(context.reads == 1 && context.writes == 1 && context.admissions == 3,
         "Exact source memory and active context events");
}
int main(int argc, char **argv) {
    try {
        need(argc == 2, "Six genuine BEFORE state inputs required");
        std::array<std::uint8_t, 6 * 580> genuine{};
        std::ifstream input(argv[1], std::ios::binary);
        input.read(reinterpret_cast<char *>(genuine.data()), genuine.size());
        need(input.gcount() == genuine.size() && input.peek() == EOF, "Exact bounded input extent");
        unsigned cases = 0;
        constexpr unsigned occupied_counts[]{0, 1, 4, 8};
        // Every precision encoding and rounding mode; reserved inputs normalize.
        for (unsigned sequence = 0; sequence < 6; ++sequence) {
            std::uint16_t before_word;
            std::memcpy(&before_word, genuine.data() + sequence * 580 + 40, 2);
            need((before_word & 63U) == 63U, "Original fixture has fully masked guest CW");
            for (auto occupied : occupied_counts)
                for (unsigned sticky = 0; sticky < 2; ++sticky)
                    for (unsigned precision = 0; precision < 4; ++precision)
                        for (unsigned rounding = 0; rounding < 4; ++rounding) {
                            probe(before_word, static_cast<std::uint16_t>(0xe03fU | precision << 8 | rounding << 10),
                                  occupied, sticky);
                            ++cases;
                        }
        }
        std::cout << "{\"passed\":true,\"hardware_cases\":" << cases
                  << ",\"masked_only\":true,\"original_AFTER_seed\":false,\"initializer_credit\":0}\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
