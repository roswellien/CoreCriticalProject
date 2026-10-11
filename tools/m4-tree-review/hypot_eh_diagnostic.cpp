// Diagnostic only: exact metadata observations, no refusal acceptance credit.
#define main positive_control_probe_main
#include "D:/Projects/MW34Recomp/reports/m4-hypot-native/control-preparation-r1/control_probe.cpp"
#undef main
#include <iomanip>
#include <vector>

__attribute__((noinline)) static void throw_one() {
    throw std::runtime_error("Independent noinline host exception baseline");
}
__attribute__((noinline)) static void throw_two() { throw_one(); }
__attribute__((noinline)) static void throw_three() { throw_two(); }
__attribute__((noinline)) static void initial(Hardware &out) {
    setup(0x7f, 4, 1);
    snapshot(out);
}
static void restore(const Hardware &image) {
    __asm__ volatile("fxrstor64 %0\n\tfldenv %1" :: "m"(image.fx), "m"(image.env)
       : "memory", "st", "st(1)", "st(2)", "st(3)", "st(4)", "st(5)", "st(6)", "st(7)",
         "xmm0", "xmm1", "xmm2", "xmm3", "xmm4", "xmm5", "xmm6", "xmm7",
         "xmm8", "xmm9", "xmm10", "xmm11", "xmm12", "xmm13", "xmm14", "xmm15");
}
struct Row {
    const char *kind;
    Hardware before, after, immediately_restored;
    bool refused{}, state_equal{}, memory_equal{};
};
__attribute__((noinline)) static Row diagnostic(unsigned kind) {
    Isolation isolation;
    Row row{};
    row.kind = kind == 0 ? "same_frame_host_EH" : kind == 1 ? "one_noinline_host_EH" :
               kind == 2 ? "three_noinline_host_EH" : "actual_kind0_store_denial";
    State state, other;
    std::memset(&state, 0xa5, sizeof(state));
    std::memset(&other, 0x5a, sizeof(other));
    state.x87.fxsave.cwd.flat = 0x7f;
    Context context{&state, GetCurrentThreadId()};
    context.memory.fill(0x96);
    const auto before_state = state, before_other = other;
    const auto before_memory = context.memory;
    initial(row.before);
    try {
        if (kind == 0) throw std::runtime_error("Independent same-frame host exception baseline");
        else if (kind == 1) throw_one();
        else if (kind == 2) throw_three();
        else mw34_hypot_store_cw(&other, 0x20001001, &context);
    } catch (const std::runtime_error &) {
        row.refused = true;
    }
    snapshot(row.after);
    row.state_equal = std::memcmp(&state, &before_state, sizeof(State)) == 0 &&
                      std::memcmp(&other, &before_other, sizeof(State)) == 0;
    row.memory_equal = context.memory == before_memory;
    // Actual restoration is captured before any helper, comparison or output.
    restore(row.before);
    snapshot(row.immediately_restored);
    return row;
}
static std::string hex(const std::uint8_t *p, std::size_t n) {
    std::string out;
    constexpr char alphabet[] = "0123456789abcdef";
    out.reserve(n*2);
    for (std::size_t i=0; i<n; ++i) {
        out += alphabet[p[i]>>4]; out += alphabet[p[i]&15];
    }
    return out;
}
static void hardware(const Hardware &image) {
    std::cout << "{\"FX512_hex\":\"" << hex(image.fx.data(), image.fx.size())
              << "\",\"ENV28_hex\":\"" << hex(image.env.data(), image.env.size()) << "\"}";
}
int main() {
    try {
        std::array<Row,4> rows{};
        for (unsigned i=0; i<rows.size(); ++i) rows[i] = diagnostic(i);
        std::cout << "{\"diagnostic_only\":true,\"initializer_credit\":0,\"rows\":[";
        for (unsigned i=0; i<rows.size(); ++i) {
            need(rows[i].refused && rows[i].state_equal && rows[i].memory_equal,
                 "Actual exception and whole guest backing diagnostic conservation");
            if (i) std::cout << ',';
            std::cout << "{\"kind\":\"" << rows[i].kind << "\",\"refused\":true,"
                      << "\"two_State_backings_equal\":true,\"operand12_equal\":true,\"before\":";
            hardware(rows[i].before);
            std::cout << ",\"after\":"; hardware(rows[i].after);
            std::cout << ",\"immediately_restored\":"; hardware(rows[i].immediately_restored);
            std::cout << '}';
        }
        std::cout << "]}\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n'; return 1;
    }
}
