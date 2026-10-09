#include "memory/guest_memory.hpp"
#include "protocol.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <fstream>
#include <iostream>

using namespace mw34::x87_state;
static_assert(sizeof(void *) == 8 && sizeof(State) == 3504);
static_assert(__builtin_offsetof(State, st) + 6 == 2486);
static_assert(__builtin_offsetof(State, x87) == 2768);
extern "C" void *mw34_lifted_entry(State *, std::uint32_t, void *);
static unsigned returns{}, reads80{}, writes80{}, clears{}, tests{};
static bool failed{};

struct FpuScope {
    struct alignas(16) Image { std::uint8_t bytes[512]; } saved{};
    explicit FpuScope(std::uint16_t cw) {
        __asm__ volatile("fxsave64 %0\n\tfninit\n\tfldcw %1"
                         : "=m"(saved) : "m"(cw) : "memory", "st", "st(1)", "st(2)",
                           "st(3)", "st(4)", "st(5)", "st(6)", "st(7)");
        const std::uint32_t mxcsr = 0x1f80;
        __asm__ volatile("ldmxcsr %0" : : "m"(mxcsr) : "memory");
    }
    static void restore(const Image &image) {
        __asm__ volatile("fxrstor64 %0" : : "m"(image) : "memory", "st", "st(1)",
                         "st(2)", "st(3)", "st(4)", "st(5)", "st(6)", "st(7)",
                         "xmm0", "xmm1", "xmm2", "xmm3", "xmm4", "xmm5", "xmm6", "xmm7",
                         "xmm8", "xmm9", "xmm10", "xmm11", "xmm12", "xmm13", "xmm14", "xmm15");
    }
    bool restored_image_matches() {
        Image after{};
        __asm__ volatile("fxrstor64 %1\n\tfxsave64 %0" : "=m"(after) : "m"(saved)
                         : "memory", "st", "st(1)", "st(2)", "st(3)", "st(4)",
                           "st(5)", "st(6)", "st(7)", "xmm0", "xmm1", "xmm2", "xmm3",
                           "xmm4", "xmm5", "xmm6", "xmm7", "xmm8", "xmm9", "xmm10",
                           "xmm11", "xmm12", "xmm13", "xmm14", "xmm15");
        return std::memcmp(saved.bytes, after.bytes, 512) == 0;
    }
    ~FpuScope() { restore(saved); }
    FpuScope(const FpuScope &) = delete;
};

extern "C" void *__remill_read_memory_f80(void *token, std::uint32_t address, void *out) {
    try {
        auto &memory = *static_cast<mw34::GuestMemory *>(token);
        memory.read({address}, std::span{static_cast<std::byte *>(out), 10});
        ++reads80;
    } catch (const std::exception &) { failed = true; std::memset(out, 0, 10); }
    return token;
}
extern "C" void *__remill_write_memory_f80(void *token, std::uint32_t address, const void *in) {
    try {
        auto &memory = *static_cast<mw34::GuestMemory *>(token);
        memory.write({address}, std::span{static_cast<const std::byte *>(in), 10});
        ++writes80;
    } catch (const std::exception &) { failed = true; }
    return token;
}
extern "C" std::uint32_t __remill_read_memory_32(void *token, std::uint32_t address) {
    try { return static_cast<mw34::GuestMemory *>(token)->load<std::uint32_t>({address}); }
    catch (const std::exception &) { failed = true; return 0; }
}
extern "C" void __remill_fpu_exception_clear(std::int32_t mask) {
    if (mask != 127) failed = true;
    __asm__ volatile("fnclex" : : : "memory");
    ++clears;
}
extern "C" std::int32_t __remill_fpu_exception_test(std::int32_t mask) {
    if (mask != 127) failed = true;
    std::uint16_t sw{};
    __asm__ volatile("fnstsw %0" : "=m"(sw) : : "memory");
    ++tests;
    return sw & 127;
}
extern "C" void *__remill_function_return(State *state, std::uint32_t address, void *token) {
    if (address != return_sentinel || state->gpr.rip.dword != return_sentinel) failed = true;
    ++returns;
    return token;
}

static std::uint16_t status(const State &s) {
    return (s.x87.fxsave.swd.flat & 0x3880) | (s.sw.ie << 0) | (s.sw.de << 1) |
           (s.sw.ze << 2) | (s.sw.oe << 3) | (s.sw.ue << 4) | (s.sw.pe << 5) |
           (s.sw.sf << 6) | (s.sw.c0 << 8) | (s.sw.c1 << 9) | (s.sw.c2 << 10) | (s.sw.c3 << 14);
}
static std::uint16_t full_tags(std::uint16_t sw, std::uint8_t ftw,
                               const std::array<Raw80, 8> &slots) {
    std::uint16_t result{};
    auto top = (sw >> 11) & 7;
    for (unsigned logical = 0; logical < 8; ++logical) {
        unsigned physical = (top + logical) & 7, tag = 3;
        if (ftw & (1U << physical)) {
            const auto &value = slots[logical];
            std::uint64_t sig{};
            std::memcpy(&sig, value.data(), 8);
            auto exp = (std::uint16_t{value[8]} | (std::uint16_t{value[9]} << 8)) & 0x7fff;
            tag = !exp && !sig ? 1 : (!exp || exp == 0x7fff || !(sig >> 63)) ? 2 : 0;
        }
        result |= static_cast<std::uint16_t>(tag << (2 * physical));
    }
    return result;
}
static void capture(const State &s, Result &r, bool before) {
    auto &cw = before ? r.cw_before : r.cw_after;
    auto &sw = before ? r.sw_before : r.sw_after;
    auto &ftw = before ? r.ftw_before : r.ftw_after;
    auto &tag = before ? r.full_tag_before : r.full_tag_after;
    auto &values = before ? r.logical_before : r.logical_after;
    auto &fx = before ? r.fx_before : r.fx_after;
    auto &env = before ? r.env_before : r.env_after;
    cw = s.x87.fxsave.cwd.flat;
    sw = status(s);
    ftw = s.x87.fxsave.ftw.flat;
    for (unsigned i = 0; i < 8; ++i)
        std::memcpy(values[i].data(), &s.st.elems[i].val, 10);
    tag = full_tags(static_cast<std::uint16_t>(sw), static_cast<std::uint8_t>(ftw), values);
    // Serialized observation of actual Remill fields. Native raw fields are not
    // hardware FXSAVE/FNSTENV captures, nor an expected-result computation.
    std::memcpy(fx.data(), &s.x87, 512);
    auto put16 = [](auto &bytes, unsigned offset, std::uint16_t value) {
        std::memcpy(bytes.data() + offset, &value, 2);
    };
    put16(fx, 0, static_cast<std::uint16_t>(cw));
    put16(fx, 2, static_cast<std::uint16_t>(sw));
    fx[4] = static_cast<std::uint8_t>(ftw);
    for (unsigned i = 0; i < 8; ++i)
        std::memcpy(fx.data() + 32 + i * 16, values[i].data(), 10);
    put16(env, 0, static_cast<std::uint16_t>(cw));
    put16(env, 4, static_cast<std::uint16_t>(sw));
    put16(env, 8, static_cast<std::uint16_t>(tag));
}

static Result run_native(const Request &q) {
    auto initial = initial_memory(q);
    mw34::GuestMemory memory;
    memory.map({memory_base}, memory_size, mw34::Permissions::read | mw34::Permissions::write);
    memory.write({memory_base}, std::as_bytes(std::span{initial}));
    State s{};
    s.gpr.rax.dword = q.state.registers[0]; s.gpr.rcx.dword = q.state.registers[1];
    s.gpr.rdx.dword = q.state.registers[2]; s.gpr.rbx.dword = q.state.registers[3];
    s.gpr.rsp.dword = q.state.registers[4]; s.gpr.rbp.dword = q.state.registers[5];
    s.gpr.rsi.dword = q.state.registers[6]; s.gpr.rdi.dword = q.state.registers[7];
    s.gpr.rip.dword = q.state.eip; s.rflag.flat = q.state.flags;
    s.aflag.cf = (q.state.flags >> 0) & 1; s.aflag.pf = (q.state.flags >> 2) & 1;
    s.aflag.af = (q.state.flags >> 4) & 1; s.aflag.zf = (q.state.flags >> 6) & 1;
    s.aflag.sf = (q.state.flags >> 7) & 1; s.aflag.df = (q.state.flags >> 10) & 1;
    s.aflag.of = (q.state.flags >> 11) & 1;
    s.x87.fxsave.cwd.flat = static_cast<std::uint16_t>(q.cw);
    s.x87.fxsave.swd.flat = static_cast<std::uint16_t>((q.initial_top << 11) | q.initial_sw);
    s.x87.fxsave.ftw.flat = static_cast<std::uint8_t>(q.physical_ftw);
    s.sw.ie = (q.initial_sw >> 0) & 1; s.sw.de = (q.initial_sw >> 1) & 1;
    s.sw.ze = (q.initial_sw >> 2) & 1; s.sw.oe = (q.initial_sw >> 3) & 1;
    s.sw.ue = (q.initial_sw >> 4) & 1; s.sw.pe = (q.initial_sw >> 5) & 1;
    s.sw.sf = (q.initial_sw >> 6) & 1; s.sw.c1 = (q.initial_sw >> 9) & 1;
    for (unsigned i = 0; i < 8; ++i) std::memcpy(&s.st.elems[i].val, q.logical_slots[i].data(), 10);
    Result result{};
    capture(s, result, true);
    returns = reads80 = writes80 = clears = tests = 0; failed = false;
    {
        FpuScope host(static_cast<std::uint16_t>(q.cw));
        if (mw34_lifted_entry(&s, code_base, &memory) != &memory || returns != 1 || failed ||
            reads80 != unsigned(fixture_kind == 0) || writes80 != unsigned(fixture_kind == 1) ||
            clears != unsigned(fixture_kind == 1) || tests != unsigned(fixture_kind == 1))
            throw std::runtime_error("Unreviewed native state bridge sequence or termination");
        capture(s, result, false);
        result.host_restored = host.restored_image_matches();
    }
    if (!result.host_restored) throw std::runtime_error("Native host FXSAVE64 restoration mismatch");
    const std::uint32_t registers[] = {s.gpr.rax.dword, s.gpr.rcx.dword, s.gpr.rdx.dword,
        s.gpr.rbx.dword, s.gpr.rsp.dword, s.gpr.rbp.dword, s.gpr.rsi.dword, s.gpr.rdi.dword};
    std::memcpy(result.state.registers, registers, 32);
    result.state.flags = (s.aflag.cf << 0) | (s.aflag.pf << 2) | (s.aflag.af << 4) |
        (s.aflag.zf << 6) | (s.aflag.sf << 7) | (s.aflag.df << 10) | (s.aflag.of << 11);
    result.state.eip = s.gpr.rip.dword;
    memory.read({memory_base}, std::as_writable_bytes(std::span{result.memory}));
    return result;
}

static Request probe_request(unsigned pc, unsigned rc, unsigned pattern = 0) {
    Request q{};
    q.state.registers[1] = memory_base + 65;
    q.state.registers[2] = memory_base + 257;
    q.state.registers[4] = memory_base + 2048;
    q.state.flags = 0x202;
    q.state.eip = code_base;
    q.cw = 0x7f | (pc << 8) | (rc << 10);
    q.memory_seed = 0x3434;
    q.initial_top = 7;
    q.physical_ftw = 255;
    q.initial_sw = 0x22;
    q.pattern_id = pattern;
    q.logical_slots = patterns[pattern];
    q.input_raw80 = input_patterns[pattern];
    validate_request(q);
    return q;
}

static void check_memory_bridges() {
    mw34::GuestMemory memory;
    memory.map({memory_base}, 16, mw34::Permissions::read | mw34::Permissions::write);
    const auto value = raw80(0x8000000000000001ULL, 0xbfff);
    failed = false;
    __remill_write_memory_f80(&memory, memory_base + 1, value.data());
    if (failed) throw std::runtime_error("Unaligned raw80 write failed");
    std::array<std::uint8_t, 12> buffer{};
    buffer.fill(0xcc);
    __remill_read_memory_f80(&memory, memory_base + 1, buffer.data() + 1);
    if (failed || buffer.front() != 0xcc || buffer.back() != 0xcc ||
        std::memcmp(buffer.data() + 1, value.data(), 10))
        throw std::runtime_error("Exact unaligned raw80 read/canaries failed");
    for (auto address : {memory_base - 1, memory_base + 7, 0xffffffffU}) {
        std::array<std::byte, 16> before{}, after{};
        memory.read({memory_base}, before);
        failed = false;
        __remill_write_memory_f80(&memory, address, value.data());
        memory.read({memory_base}, after);
        if (!failed || before != after) throw std::runtime_error("Invalid raw80 write was not atomic");
        buffer.fill(0xcc); failed = false;
        __remill_read_memory_f80(&memory, address, buffer.data() + 1);
        if (!failed || buffer.front() != 0xcc || buffer.back() != 0xcc ||
            std::any_of(buffer.begin() + 1, buffer.end() - 1, [](auto byte) { return byte != 0; }))
            throw std::runtime_error("Invalid raw80 read/canaries failed");
    }
    memory.protect({memory_base}, mw34::Permissions::read);
    failed = false;
    __remill_write_memory_f80(&memory, memory_base + 1, value.data());
    if (!failed) throw std::runtime_error("Read-only raw80 write admitted");
    failed = false;
    __remill_read_memory_f80(&memory, memory_base + 1, buffer.data() + 1);
    if (failed || std::memcmp(buffer.data() + 1, value.data(), 10))
        throw std::runtime_error("Read-only raw80 read failed");
    memory.protect({memory_base}, mw34::Permissions::none);
    failed = false;
    __remill_write_memory_f80(&memory, memory_base + 1, value.data());
    if (!failed) throw std::runtime_error("No-access raw80 write admitted");
    failed = false;
    __remill_read_memory_f80(&memory, memory_base + 1, buffer.data() + 1);
    if (!failed) throw std::runtime_error("No-access raw80 read admitted");
    std::cout << "State memory bridges: 12 checks passed\n";
}

static void check_environment() {
    FpuScope restore_outer(0x037f);
    __asm__ volatile("fld1\n\tfldpi\n\tfaddp" : : : "memory");
    FpuScope::Image before{}, after{};
    __asm__ volatile("fxsave64 %0" : "=m"(before) : : "memory");
    std::uint16_t seed_sw{};
    std::memcpy(&seed_sw, before.bytes + 2, 2);
    if (!(seed_sw & 0x20) || !before.bytes[4]) throw std::runtime_error("Host seed must be nonempty/inexact");
    auto same_active = [&](const FpuScope::Image &image) {
        if (std::memcmp(before.bytes, image.bytes, 5) || std::memcmp(before.bytes + 24, image.bytes + 24, 4))
            return false;
        for (unsigned i = 0; i < 8; ++i)
            if (std::memcmp(before.bytes + 32 + 16 * i, image.bytes + 32 + 16 * i, 10)) return false;
        return true;
    };
    for (unsigned pc : {0U, 2U, 3U}) for (unsigned rc = 0; rc < 4; ++rc) {
        const auto q = probe_request(pc, rc);
        const auto result = run_native(q);
        __asm__ volatile("fxsave64 %0" : "=m"(after) : : "memory");
        if (result.cw_after != q.cw || !same_active(after) || std::memcmp(before.bytes + 6, after.bytes + 6, 18))
            throw std::runtime_error("Host x87 state/pointers/MXCSR changed on normal return");
    }
    try { FpuScope unwind(0x0c7f); throw std::runtime_error("authored state unwind"); }
    catch (const std::runtime_error &) {}
    __asm__ volatile("fxsave64 %0" : "=m"(after) : : "memory");
    if (!same_active(after)) throw std::runtime_error("Active FP state changed through C++ unwinding");
    FpuScope::Image control{};
    FpuScope::restore(before);
    try { throw std::runtime_error("unwrapped state control"); }
    catch (const std::runtime_error &) {}
    __asm__ volatile("fxsave64 %0" : "=m"(control) : : "memory");
    // This controls Windows EH metadata changes; it does not implement guest SEH.
    if (!same_active(control) || std::memcmp(after.bytes + 6, control.bytes + 6, 18))
        throw std::runtime_error("Windows EH control does not explain pointer metadata");
    FpuScope::Image synthetic = before, seeded{}, returned{};
    const std::uint16_t pending_cw = 0x037e, pending_sw = seed_sw | 0x0081;
    const std::uint64_t high_ip = 0x00007ff62aef1000ULL, high_dp = 0x00007ff62aef3220ULL;
    std::memcpy(synthetic.bytes, &pending_cw, 2); std::memcpy(synthetic.bytes + 2, &pending_sw, 2);
    std::memcpy(synthetic.bytes + 8, &high_ip, 8); std::memcpy(synthetic.bytes + 16, &high_dp, 8);
    FpuScope::restore(synthetic);
    __asm__ volatile("fxsave64 %0" : "=m"(seeded) : : "memory");
    { FpuScope inner(0x037f); __asm__ volatile("fld1\n\tfldpi\n\tfaddp" : : : "memory"); }
    __asm__ volatile("fxsave64 %0\n\tfninit" : "=m"(returned) : : "memory", "st", "st(1)",
                     "st(2)", "st(3)", "st(4)", "st(5)", "st(6)", "st(7)");
    if (std::memcmp(seeded.bytes, returned.bytes, 5) || std::memcmp(seeded.bytes + 6, returned.bytes + 6, 22) ||
        std::memcmp(seeded.bytes + 8, &high_ip, 8) || std::memcmp(seeded.bytes + 16, &high_dp, 8))
        throw std::runtime_error("Pending host exception/full64 pointers were not restored");
    for (unsigned i = 0; i < 8; ++i)
        if (std::memcmp(seeded.bytes + 32 + 16 * i, returned.bytes + 32 + 16 * i, 10))
            throw std::runtime_error("Pending host raw80 payloads were not restored");
    std::cout << "State FP environment: 15 checks passed\n";
}

static void check_mxcsr_isolation() {
    FpuScope restore_outer(0x037f);
    unsigned count{};
    for (unsigned pc : {0U, 2U, 3U}) for (unsigned rc = 0; rc < 4; ++rc) for (unsigned pattern = 0; pattern < 2; ++pattern) {
        const auto q = probe_request(pc, rc, pattern);
        const std::uint32_t baseline_mxcsr = 0x1f80;
        __asm__ volatile("ldmxcsr %0" : : "m"(baseline_mxcsr) : "memory");
        const auto baseline = run_native(q);
        for (unsigned controls = 0; controls < 4; ++controls) for (unsigned host_rc = 0; host_rc < 4; ++host_rc) {
            const std::uint32_t mxcsr = 0x1f80 | host_rc << 13 | ((controls & 1) ? 0x40 : 0) | ((controls & 2) ? 0x8000 : 0);
            __asm__ volatile("ldmxcsr %0" : : "m"(mxcsr) : "memory");
            const auto actual = run_native(q);
            std::uint32_t restored{};
            __asm__ volatile("stmxcsr %0" : "=m"(restored) : : "memory");
            if (restored != mxcsr || std::memcmp(&baseline, &actual, sizeof(Result)))
                throw std::runtime_error("Host MXCSR affected raw80 state or was not restored");
            ++count;
        }
    }
    if (count != 384) throw std::runtime_error("Incomplete raw80 MXCSR isolation matrix");
    std::cout << "State MXCSR isolation: 384 checks passed\n";
}

int main(int argc, char **argv) {
    try {
        if (argc == 2 && std::string{argv[1]} == "--check-memory-bridges") { check_memory_bridges(); return 0; }
        if (argc == 2 && std::string{argv[1]} == "--check-fp-environment") { check_environment(); return 0; }
        if (argc == 2 && std::string{argv[1]} == "--check-mxcsr-isolation") { check_mxcsr_isolation(); return 0; }
        if (argc != 4) throw std::runtime_error("native input output fixture");
        std::ifstream code(argv[3], std::ios::binary);
        std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(code)), {});
        if (!matches_fixture(bytes)) throw std::runtime_error("Unadmitted state fixture bytes");
        std::ifstream input(argv[1], std::ios::binary);
        auto requests = read_requests(input);
        std::ofstream output(argv[2], std::ios::binary | std::ios::trunc);
        write_record(output, output_header(static_cast<std::uint32_t>(requests.size()), 64));
        for (const auto &q : requests) write_record(output, run_native(q));
        std::cout << "Native state cases: " << requests.size() << '\n';
        return 0;
    } catch (const std::exception &e) { std::cerr << e.what() << '\n'; return 1; }
}
