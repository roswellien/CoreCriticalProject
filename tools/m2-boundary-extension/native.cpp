#include "context.hpp"
#include <iostream>
#include <mmsystem.h>
using namespace m2_boundary_extension;
static_assert(sizeof(void *) == 8 && sizeof(State) == 3504);
extern "C" {
void *mw34_block_10000000(State *, std::uint32_t, void *);
void *mw34_block_1000000f(State *, std::uint32_t, void *);
void *mw34_block_10000020(State *, std::uint32_t, void *);
void *mw34_block_1000002d(State *, std::uint32_t, void *);
void *mw34_block_10000200(State *, std::uint32_t, void *);
void *mw34_block_10000300(State *, std::uint32_t, void *);
void *mw34_block_10000400(State *, std::uint32_t, void *);
void *mw34_block_10000500(State *, std::uint32_t, void *);
std::uint32_t __remill_read_memory_32(void *c, std::uint32_t a) {
    return static_cast<Context *>(c)->memory.load<std::uint32_t>({a});
}
void *__remill_write_memory_32(void *c, std::uint32_t a, std::uint32_t v) {
    static_cast<Context *>(c)->memory.store<std::uint32_t>({a}, v);
    return c;
}
void *__remill_function_call(State *s, std::uint32_t a, void *c) {
    return static_cast<Context *>(c)->call(s, a);
}
void *sub_10000200(State *s, std::uint32_t a, void *c) {
    if (a != code_base + 0x200)
        throw std::runtime_error("Direct edge changed");
    return static_cast<Context *>(c)->call(s, a);
}
void *__remill_function_return(State *s, std::uint32_t a, void *c) {
    return static_cast<Context *>(c)->returned(s, a);
}
void *__remill_missing_block(State *s, std::uint32_t a, void *c) {
    return static_cast<Context *>(c)->continuation(s, a);
}
}
static std::uint32_t deterministic_timer(const void *cookie) {
    if (!cookie) throw std::runtime_error("Missing deterministic timer cookie");
    return *static_cast<const std::uint32_t *>(cookie);
}
static std::uint32_t live_timer(const void *) { return timeGetTime(); }
// Both deterministic and real providers pass through this selected guest bridge.
// Trace/scratch writes mirror the independently executed original x86 test thunk.
static void *timer_bridge(State *s, std::uint32_t, void *token) {
    auto &c = *static_cast<Context *>(token);
    auto sp = s->gpr.rsp.dword;
    auto ret = c.memory.load<std::uint32_t>({sp});
    ++c.bridge_calls;
    c.memory.store<std::uint32_t>({sp - 4}, s->gpr.rax.dword);
    c.memory.store<std::uint32_t>({data_base + 0x48}, ret);
    c.memory.store<std::uint32_t>({data_base + 0x4c}, sp);
    c.memory.store<std::uint32_t>({data_base + 0x60}, c.memory.load<std::uint32_t>({data_base + 0x60}) + 1);
    c.memory.store<std::uint32_t>({data_base + 0x64}, c.memory.load<std::uint32_t>({data_base + 0x64}) + 1);
    s->gpr.rax.dword = c.read_timer();
    s->gpr.rsp.dword = sp + 4;
    s->gpr.rip.dword = ret;
    return c.returned(s, ret);
}
static void register_routes(Context &c) {
    c.add(code_base, {mw34_block_10000000, nullptr, true, 0});
    c.add(code_base + 0xf, {mw34_block_1000000f, nullptr, true, 0});
    c.add(code_base + 0x20, {mw34_block_10000020, nullptr, true, 0});
    c.add(code_base + 0x2d, {mw34_block_1000002d, nullptr, true, 0});
    c.add(code_base + 0x200, {mw34_block_10000200, nullptr, false, 4});
    c.add(code_base + 0x300, {mw34_block_10000300, timer_bridge, false, 0});
    c.add(code_base + 0x400, {mw34_block_10000400, nullptr, false, 0});
    c.add(code_base + 0x500, {mw34_block_10000500, nullptr, false, 0});
}
static void *route_original(State *s, std::uint32_t pc, void *c) {
    return static_cast<Context *>(c)->route(s, pc, true);
}
static unsigned controls() {
    unsigned passed = 0;
    auto reject = [&](auto operation) {
        try {
            operation();
        } catch (const std::exception &) {
            ++passed;
            return;
        }
        throw std::runtime_error("A context negative control was accepted");
    };
    Context c;
    register_routes(c);
    const std::uint32_t controlled_tick = 0x12345678;
    c.timer_provider("deterministic-uint32", deterministic_timer, &controlled_tick);
    c.memory.map({stack_base}, page, mw34::Permissions::read | mw34::Permissions::write);
    c.memory.map({data_base}, page, mw34::Permissions::read | mw34::Permissions::write);
    State s{};
    s.gpr.rsp.dword = stack_base + 64;
    s.gpr.rip.dword = 0xdeadbeef;
    reject([&] { c.route(&s, 0xdeadbeef); });
    reject([&] { c.freeze(std::string(64, '0')); });
    reject([&] { c.select(code_base + 0x300, route_original); });
    reject([&] { c.add(0xdeadbeef, {mw34_block_10000200, nullptr, false, 0}); });
    c.select(code_base + 0x200, route_original);
    c.freeze(fixture_hash);
    reject([&] { c.route(&s, 0xdeadbeef); });
    reject([&] { c.route(&s, code_base); });
    reject([&] { c.add(code_base, {mw34_block_10000000, nullptr, true, 0}); });
    reject([&] { c.timer_provider("WINMM.timeGetTime", live_timer, nullptr); });
    s.gpr.rip.dword = code_base + 0x300;
    c.memory.store<std::uint32_t>({s.gpr.rsp.dword}, 0xdeadbeef);
    reject([&] { c.call(&s, code_base + 0x300); });
    c.memory.store<std::uint32_t>({s.gpr.rsp.dword}, code_base + 0xf);
    reject([&] { c.call(&s, code_base + 0x300); });
    reject([&] { (void)c.memory.load<std::uint32_t>({0xfffffffe}); });
    reject([&] { (void)c.memory.load<std::uint32_t>({0x22000000}); });
    std::array<std::byte, page> before{}, after{};
    c.memory.read({data_base}, before);
    c.memory.protect({data_base}, mw34::Permissions::read);
    reject([&] { c.memory.store<std::uint32_t>({data_base + 8}, 0xdeadbeef); });
    c.memory.read({data_base}, after);
    if (before != after)
        throw std::runtime_error("Rejected IAT write changed a global byte");
    c.memory.protect({data_base}, mw34::Permissions::read | mw34::Permissions::write);
    s.gpr.rip.dword = code_base + 0x300;
    c.frames.push_back({code_base + 0x300, code_base + 0x20, stack_base + 64, 0});
    reject([&] { c.returned(&s, code_base + 0x300); });
    c.frames.clear();
    s.gpr.rip.dword = code_base + 0x20;
    c.frames.push_back({code_base + 0x300, code_base + 0x20, stack_base + 64, 0});
    reject([&] { c.returned(&s, code_base + 0x20); });
    c.frames.clear();
    s.gpr.rip.dword = sentinel;
    reject([&] { c.continuation(&s, sentinel); });
    // A replacement must explicitly route to its original, never reselect itself.
    // Both direct and indirect entry shims reach Context::call, hence this table.
    reject([&] { c.select(code_base + 0x400, route_original); });
    for (bool direct : {true, false}) {
        s.gpr.rip.dword = code_base + 0x200;
        s.gpr.rsp.dword = stack_base + 64;
        s.gpr.rax.dword = 0x12345678;
        s.gpr.rcx.dword = 0x76543210;
        c.memory.store<std::uint32_t>({stack_base + 64}, code_base + 0xf);
        c.memory.store<std::uint32_t>({stack_base + 68}, 0x12345678);
        s.gpr.rax.dword = 0xa5a5f00d;
        auto *token = direct ? sub_10000200(&s, code_base + 0x200, &c)
                             : __remill_function_call(&s, code_base + 0x200, &c);
        if (token != &c || s.gpr.rax.dword != 0x88888888 || s.gpr.rsp.dword != stack_base + 72 ||
            !c.frames.empty())
            throw std::runtime_error(
                "Shared direct/indirect original route recursed or changed ABI");
        ++passed;
    }
    if (c.replacement_calls != 2)
        throw std::runtime_error("Direct/indirect replacement selection differs");
    ++passed;
    for (int mode = 0; mode < 4; ++mode) {
        Context provider;
        register_routes(provider);
        if (mode == 0) reject([&] { provider.freeze(fixture_hash); });
        if (mode == 1) reject([&] { provider.timer_provider("unknown", deterministic_timer, &controlled_tick); });
        if (mode == 2) reject([&] { provider.timer_provider("deterministic-uint32", nullptr, &controlled_tick); });
        if (mode == 3) reject([&] { (void)provider.read_timer(); });
    }
    Context provider;
    register_routes(provider);
    provider.timer_provider("deterministic-uint32", deterministic_timer, &controlled_tick);
    reject([&] { provider.timer_provider("deterministic-uint32", deterministic_timer, &controlled_tick); });
    provider.freeze(fixture_hash);
    if (provider.read_timer() != controlled_tick || provider.provider_calls != 1)
        throw std::runtime_error("Provider callback/count control failed");
    ++passed;
    Context selected;
    register_routes(selected);
    selected.timer_provider("deterministic-uint32", deterministic_timer, &controlled_tick);
    selected.memory.map({stack_base}, page, mw34::Permissions::read | mw34::Permissions::write);
    selected.memory.map({data_base}, page, mw34::Permissions::read | mw34::Permissions::write);
    selected.memory.store<std::uint32_t>({data_base + 16}, 0xdeadbeef);
    selected.memory.store<std::uint32_t>({stack_base + 64}, code_base + 0x20);
    selected.freeze(fixture_hash);
    State selected_state{};
    selected_state.gpr.rip.dword = code_base + 0x300;
    selected_state.gpr.rsp.dword = stack_base + 64;
    if (selected.call(&selected_state, code_base + 0x300) != &selected ||
        selected_state.gpr.rax.dword != controlled_tick || selected.provider_calls != 1 ||
        selected.bridge_calls != 1 || selected.returns != 1 || !selected.frames.empty())
        throw std::runtime_error("Selected bridge did not consume the registered provider");
    ++passed;
    return passed;
}
static Result run(const Request &q, bool live = false) {
    if (live && ((q.state.flags & 0x400U) || q.timer != 0))
        throw std::runtime_error("Live provider requires DF0 and zero unused timer input");
    auto b = initial(q, true);
    Context c;
    c.outer_esp = q.state.registers[4];
    register_routes(c);
    c.timer_provider(live ? "WINMM.timeGetTime" : "deterministic-uint32",
                     live ? live_timer : deterministic_timer, live ? nullptr : &q.timer);
    c.freeze(fixture_hash);
    c.memory.map({stack_base}, page, mw34::Permissions::read | mw34::Permissions::write);
    c.memory.map({data_base}, page, mw34::Permissions::read | mw34::Permissions::write);
    c.memory.write({stack_base}, std::as_bytes(std::span{b}.first(page)));
    c.memory.write({data_base}, std::as_bytes(std::span{b}.subspan(page)));
    State s{};
    // Logical guest FP/SIMD storage is carried through the compiled integer
    // chain. This does not execute, compare or validate floating instructions.
    auto pattern = [&](auto &field, std::uint32_t salt) {
        auto bytes = std::as_writable_bytes(std::span{&field, 1});
        for (std::size_t i = 0; i < bytes.size(); ++i)
            bytes[i] = std::byte((i * 29 + q.seed + salt) & 255);
    };
    pattern(s.vec, 1);
    pattern(s.mmx, 2);
    pattern(s.x87, 3);
    pattern(s.sw, 4);
    for (unsigned i = 0; i < 8; ++i) {
        std::array<std::uint8_t, 10> value{};
        std::uint64_t significand = 0x8000000000000000ULL + (std::uint64_t(i) << 55);
        std::uint16_t exponent = 0x3fff + (i & 1);
        std::memcpy(value.data(), &significand, 8);
        std::memcpy(value.data() + 8, &exponent, 2);
        std::memcpy(&s.st.elems[i].val, value.data(), 10);
        std::memcpy(&s.x87.fxsave.st[i].st, value.data(), 10);
    }
    constexpr std::uint16_t controls_words[] = {0x007f, 0x047f, 0x087f, 0x0c7f, 0x027f, 0x067f,
                                                0x0a7f, 0x0e7f, 0x037f, 0x077f, 0x0b7f, 0x0f7f};
    s.x87.fxsave.cwd.flat = controls_words[(q.seed >> 3) % 12];
    s.x87.fxsave.swd.flat = static_cast<std::uint16_t>(((q.seed & 7) << 11) | 0x21);
    s.x87.fxsave.ftw.flat = static_cast<std::uint8_t>((q.seed >> 8) | 3);
    s.sw.ie = 1;
    s.sw.pe = 1;
    s.sw.c1 = 1;
    s.sw.sf = 0;
    s.sw.de = 0;
    s.sw.ze = 0;
    s.sw.oe = 0;
    s.sw.ue = 0;
    std::vector<std::byte> before_fp;
    auto gather = [&]() {
        std::vector<std::byte> bytes;
        for (auto field : {std::as_bytes(std::span{&s.vec, 1}), std::as_bytes(std::span{&s.st, 1}),
                           std::as_bytes(std::span{&s.mmx, 1}), std::as_bytes(std::span{&s.sw, 1}),
                           std::as_bytes(std::span{&s.x87, 1})})
            bytes.insert(bytes.end(), field.begin(), field.end());
        return bytes;
    };
    before_fp = gather();
    s.gpr.rax.dword = q.state.registers[0];
    s.gpr.rcx.dword = q.state.registers[1];
    s.gpr.rdx.dword = q.state.registers[2];
    s.gpr.rbx.dword = q.state.registers[3];
    s.gpr.rsp.dword = q.state.registers[4];
    s.gpr.rbp.dword = q.state.registers[5];
    s.gpr.rsi.dword = q.state.registers[6];
    s.gpr.rdi.dword = q.state.registers[7];
    s.gpr.rip.dword = q.state.eip;
    s.rflag.flat = q.state.flags;
    s.aflag.cf = (q.state.flags >> 0) & 1;
    s.aflag.pf = (q.state.flags >> 2) & 1;
    s.aflag.af = (q.state.flags >> 4) & 1;
    s.aflag.zf = (q.state.flags >> 6) & 1;
    s.aflag.sf = (q.state.flags >> 7) & 1;
    s.aflag.df = (q.state.flags >> 10) & 1;
    s.aflag.of = (q.state.flags >> 11) & 1;
    if (c.route(&s, code_base) != &c || !c.final_return || !c.frames.empty() || c.calls != 3 ||
        c.returns != 4 || c.provider_calls != 1 || c.bridge_calls != 1)
        throw std::runtime_error("Unexpected termination");
    if (before_fp != gather())
        throw std::runtime_error("Integer/API chain changed logical guest FP/SIMD storage");
    Result r{};
    const std::uint32_t regs[] = {s.gpr.rax.dword, s.gpr.rcx.dword, s.gpr.rdx.dword,
                                  s.gpr.rbx.dword, s.gpr.rsp.dword, s.gpr.rbp.dword,
                                  s.gpr.rsi.dword, s.gpr.rdi.dword};
    std::memcpy(r.state.registers, regs, 32);
    r.state.flags = (s.aflag.cf << 0) | (s.aflag.pf << 2) | (s.aflag.af << 4) | (s.aflag.zf << 6) |
                    (s.aflag.sf << 7) | (s.aflag.df << 10) | (s.aflag.of << 11);
    r.state.eip = s.gpr.rip.dword;
    r.calls = c.calls;
    r.returns = c.returns;
    r.provider_calls = c.provider_calls;
    r.bridge_calls = c.bridge_calls;
    r.provider_return = c.provider_return;
    c.memory.read({stack_base}, std::as_writable_bytes(std::span{r.memory}.first(page)));
    c.memory.read({data_base}, std::as_writable_bytes(std::span{r.memory}.subspan(page)));
    return r;
}
int main(int argc, char **argv) {
    try {
        if (argc == 2 && std::string(argv[1]) == "--check-context") {
            std::cout << "Context controls passed: " << controls() << '\n';
            return 0;
        }
        if (argc == 2 && std::string(argv[1]) == "--check-unknown-call") {
            Request q{};
            q.state.eip = code_base;
            q.state.flags = 0x202;
            q.state.registers[4] = stack_base + 64;
            q.choice = 2;
            (void)run(q); // Trusted negative probe reaches the actual generated indirect CALL.
            throw std::runtime_error("Unknown target unexpectedly returned");
        }
        if (argc == 2 && std::string(argv[1]) == "--check-state-preservation") {
            for (std::uint32_t mode = 0; mode < 12; ++mode)
                for (std::uint32_t top = 0; top < 8; ++top) {
                    Request q{};
                    q.state.eip = code_base;
                    q.state.flags = 0x202 | ((top & 1) << 10);
                    q.state.registers[4] = stack_base + 128;
                    q.state.registers[1] = 0x88776655;
                    q.argument = 0x12345678;
                    q.global = 0xaabbccdd;
                    q.timer = 0xfedcba98;
                    q.choice = top & 1;
                    q.seed = (mode << 3) | top;
                    run(q);
                }
            std::cout << "Logical guest FP/SIMD preservation checks passed: 96\n";
            return 0;
        }
        const bool live = argc == 5 && std::string(argv[1]) == "--live-timer";
        if (argc != (live ? 5 : 4))
            throw std::runtime_error("native [--live-timer] input output fixture");
        code(argv[live ? 4 : 3]);
        std::ifstream in(argv[live ? 2 : 1], std::ios::binary);
        const auto matrix = requests(in, live);
        std::vector<Result> results;
        results.reserve(matrix.size());
        for (const auto &q : matrix) {
            results.push_back(run(q, live));
            if (live && results.size() != matrix.size()) Sleep(40);
        }
        std::ofstream out(argv[live ? 3 : 2], std::ios::binary | std::ios::trunc);
        write(out, output(static_cast<std::uint32_t>(results.size())));
        for (const auto &r : results) write(out, r);
        if (live) {
            std::cout << "{\"provider\":\"WINMM.timeGetTime\",\"module_path\":\"" << live_module_path()
                      << "\",\"pointer_bits\":64,\"live_context_cases\":8,\"provider_calls\":8,"
                         "\"bridge_calls\":8,\"guest_iat_target\":" << code_base + 0x300 << "}\n";
        } else std::cout << "Native x64 cases: " << results.size() << '\n';
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
