// Supplementary finite negative controls; successful numeric paths are separate.
#define main positive_control_probe_main
#include "control_probe_positive.cpp"
#undef main
#include <thread>

static void denial(unsigned kind) {
    Isolation isolation;
    setup(0x7f, 4, 1);
    State state, other;
    std::memset(&state, 0xa5, sizeof(state));
    std::memset(&other, 0x5a, sizeof(other));
    state.x87.fxsave.cwd.flat = 0x7f;
    Context context{&state, GetCurrentThreadId()};
    context.memory.fill(0x96);
    if (kind == 1) context.thread ^= 1;
    if (kind == 2) state.x87.fxsave.cwd.flat = 0x3f;
    if (kind == 3) state.x87.fxsave.cwd.flat = 0x7e;
    if (kind == 4) state.x87.fxsave.cwd.flat = 0x37f;
    std::uint16_t supplied = kind == 5 ? 0 : 0x37f;
    std::memcpy(context.memory.data() + 5, &supplied, 2);
    const auto saved = state;
    const auto saved_other = other;
    const auto saved_memory = context.memory;
    Hardware before, after;
    snapshot(before);
    bool refused = false;
    try {
        if (kind == 0) mw34_hypot_store_cw(&other, 0x20001001, &context);
        else if (kind == 5) mw34_hypot_load_cw(&state, 0x20001005, &context);
        else if (kind == 6) mw34_hypot_load_cw(&state, 0xffffffff, &context);
        else if (kind == 7) mw34_hypot_store_cw(&state, 0x2000100b, &context);
        else mw34_hypot_wait(&state, &context);
    } catch (const std::runtime_error &) {
        refused = true;
    }
    snapshot(after);
    need(refused, "Unsupported context/operand/CW must refuse before mutation");
    need(std::memcmp(&state, &saved, sizeof(state)) == 0 &&
         std::memcmp(&other, &saved_other, sizeof(other)) == 0 && context.memory == saved_memory,
         "Denied operation conserves complete State and memory backings");
    std::cerr << "DENIAL kind=" << kind << " ENV_before=";
    for (auto byte : before.env) std::cerr << std::hex << unsigned(byte) << ',';
    std::cerr << " ENV_after=";
    for (auto byte : after.env) std::cerr << std::hex << unsigned(byte) << ',';
    std::cerr << std::dec << '\n';
    same_x87(before, after, 0x7f);
    // Restore only authored invalid unit inputs, then retry a fresh valid load.
    context.thread = GetCurrentThreadId();
    state.x87.fxsave.cwd.flat = 0x7f;
    supplied = 0x37f;
    std::memcpy(context.memory.data() + 5, &supplied, 2);
    const auto retry_before = state;
    need(mw34_hypot_load_cw(&state, 0x20001005, &context) == &context, "Valid retry returns exact context");
    auto expected = retry_before;
    expected.x87.fxsave.cwd.flat = 0x37f;
    need(std::memcmp(&state, &expected, sizeof(state)) == 0, "Valid retry changes only State CW");
    snapshot(after);
    same_x87(before, after, 0x37f);
}
static void real_other_thread() {
    State state;
    std::memset(&state, 0xa5, sizeof(state));
    state.x87.fxsave.cwd.flat = 0x7f;
    Context context{&state, GetCurrentThreadId()};
    context.memory.fill(0x96);
    const auto saved = state;
    const auto memory_before = context.memory;
    bool refused = false;
    std::thread worker([&] {
        try { mw34_hypot_wait(&state, &context); }
        catch (const std::runtime_error &) { refused = true; }
    });
    worker.join();
    need(refused && context.admissions == 0 && context.reads == 0 && context.writes == 0,
         "Actual different-thread context refuses before any operand access");
    need(std::memcmp(&state, &saved, sizeof(state)) == 0 && context.memory == memory_before,
         "Actual different-thread refusal retains whole guest backings");
}
int main() {
    try {
        for (unsigned kind = 0; kind < 8; ++kind) denial(kind);
        real_other_thread();
        std::cout << "{\"passed\":true,\"denials\":9,\"valid_retries\":8,\"initializer_credit\":0}\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
