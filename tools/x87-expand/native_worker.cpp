#include "memory/guest_memory.hpp"
#include "protocol.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <bit>
#include <fstream>
#include <iostream>
#include <string>

using namespace mw34::x87_expand;
static_assert(sizeof(void *) == 8 && sizeof(State) == 3504);
extern "C" void *mw34_lifted_entry(State *, std::uint32_t, void *);
static unsigned return_count{}, clear_count{}, test_count{}, undefined_count{}, rounding_count{};
static bool bridge_failed{};

// Preserve x87 state including full64-bit instruction/data pointers and MXCSR.
// Declare restored vector/stack registers as clobbered so Clang preserves its
// live values and the Windows ABI's nonvolatile vector registers explicitly.
// No C++ long double crosses the Windows ABI (it is binary64 on this platform).
struct FpuScope {
    struct alignas(16) Image { std::uint8_t bytes[512]; } saved{};
    explicit FpuScope(std::uint16_t cw) {
        __asm__ volatile("fxsave64 %0\n\tfninit\n\tfldcw %1"
                         : "=m"(saved) : "m"(cw) : "memory", "st", "st(1)", "st(2)",
                           "st(3)", "st(4)", "st(5)", "st(6)", "st(7)");
    }
    static void restore(const Image &image) {
        __asm__ volatile("fxrstor64 %0" : : "m"(image) : "memory", "st", "st(1)",
                         "st(2)", "st(3)", "st(4)", "st(5)", "st(6)", "st(7)",
                         "xmm0", "xmm1", "xmm2", "xmm3", "xmm4", "xmm5", "xmm6", "xmm7",
                         "xmm8", "xmm9", "xmm10", "xmm11", "xmm12", "xmm13", "xmm14", "xmm15");
    }
    ~FpuScope() { restore(saved); }
    FpuScope(const FpuScope &) = delete;
};

extern "C" void __mw34_x87_nearbyint80(const void *input, void *output) {
    if (!input || !output || input == output) { bridge_failed = true; return; }
    FpuScope::Image entry{};
    __asm__ volatile("fxsave64 %0" : "=m"(entry) : : "memory");
    struct Raw80 { std::uint8_t bytes[10]; } operand{}, rounded{};
    std::memcpy(operand.bytes, input, 10);
    std::uint16_t cw{};
    std::memcpy(&cw, entry.bytes, 2);
    if (!legal_control_word(cw)) { bridge_failed = true; return; }
    {
        FpuScope preserve(cw);
        __asm__ volatile("fldt %1\n\tfrndint\n\tfstpt %0"
                         : "=m"(rounded) : "m"(operand) : "memory", "st", "st(1)",
                           "st(2)", "st(3)", "st(4)", "st(5)", "st(6)", "st(7)");
    }
    std::memcpy(output, rounded.bytes, 10);
    ++rounding_count;
}

extern "C" void __remill_fpu_exception_clear(std::int32_t mask) {
    if (mask != 127) bridge_failed = true;
    __asm__ volatile("fnclex" : : : "memory");
    ++clear_count;
}
extern "C" std::int32_t __remill_fpu_exception_test(std::int32_t mask) {
    if (mask != 127) bridge_failed = true;
    std::uint16_t sw{};
    __asm__ volatile("fnstsw %0" : "=m"(sw) : : "memory");
    ++test_count;
    return sw & 0x7f;
}
extern "C" std::uint8_t __remill_undefined_8() {
    // The exact reviewed IR writes only excluded C0/C2/C3 slots, never reads them.
    ++undefined_count;
    return 0;
}
extern "C" double __remill_read_memory_f64(void *memory, std::uint32_t address) {
    try { return std::bit_cast<double>(static_cast<mw34::GuestMemory *>(memory)->load<std::uint64_t>({address})); }
    catch (const std::exception &) { bridge_failed = true; return 0; }
}
extern "C" void *__remill_write_memory_f64(void *memory, std::uint32_t address, double value) {
    try { static_cast<mw34::GuestMemory *>(memory)->store<std::uint64_t>({address}, std::bit_cast<std::uint64_t>(value)); }
    catch (const std::exception &) { bridge_failed = true; }
    return memory;
}
extern "C" void *__remill_write_memory_32(void *memory, std::uint32_t address, std::uint32_t value) {
    try { static_cast<mw34::GuestMemory *>(memory)->store<std::uint32_t>({address}, value); }
    catch (const std::exception &) { bridge_failed = true; }
    return memory;
}
extern "C" std::uint32_t __remill_read_memory_32(void *memory, std::uint32_t address) {
    try { return static_cast<mw34::GuestMemory *>(memory)->load<std::uint32_t>({address}); }
    catch (const std::exception &) { bridge_failed = true; return 0; }
}
extern "C" void *__remill_function_return(State *state, std::uint32_t address, void *memory) {
    if (address != return_sentinel || state->gpr.rip.dword != return_sentinel) bridge_failed = true;
    ++return_count;
    return memory;
}

static Result run_native(const Request &request) {
    const auto initial = initial_memory(request);
    mw34::GuestMemory memory;
    memory.map({memory_base}, memory_size, mw34::Permissions::read | mw34::Permissions::write);
    memory.write({memory_base}, std::as_bytes(std::span{initial}));
    State state{};
    state.gpr.rax.dword = request.state.registers[0];
    state.gpr.rcx.dword = request.state.registers[1];
    state.gpr.rdx.dword = request.state.registers[2];
    state.gpr.rbx.dword = request.state.registers[3];
    state.gpr.rsp.dword = request.state.registers[4];
    state.gpr.rbp.dword = request.state.registers[5];
    state.gpr.rsi.dword = request.state.registers[6];
    state.gpr.rdi.dword = request.state.registers[7];
    state.gpr.rip.dword = request.state.eip;
    state.rflag.flat = request.state.flags;
    state.aflag.cf = (request.state.flags >> 0) & 1;
    state.aflag.pf = (request.state.flags >> 2) & 1;
    state.aflag.af = (request.state.flags >> 4) & 1;
    state.aflag.zf = (request.state.flags >> 6) & 1;
    state.aflag.sf = (request.state.flags >> 7) & 1;
    state.aflag.df = (request.state.flags >> 10) & 1;
    state.aflag.of = (request.state.flags >> 11) & 1;
    state.x87.fxsave.cwd.flat = static_cast<std::uint16_t>(request.cw);
    Result result{};
    result.cw_before = state.x87.fxsave.cwd.flat;
    return_count = clear_count = test_count = undefined_count = rounding_count = 0;
    bridge_failed = false;
    {
        FpuScope environment(result.cw_before);
        std::uint16_t actual_cw{};
        __asm__ volatile("fnstcw %0" : "=m"(actual_cw) : : "memory");
        if (actual_cw != result.cw_before) throw std::runtime_error("Host x87 control setup differs");
        if (mw34_lifted_entry(&state, code_base, &memory) != &memory || return_count != 1 ||
            clear_count != (fixture_kind == 0 ? 4U : 1U) || test_count != (fixture_kind == 0 ? 4U : 1U) ||
            undefined_count != (fixture_kind == 0 ? 3U : 0U) || rounding_count != (fixture_kind == 0 ? 0U : 1U) || bridge_failed)
            throw std::runtime_error("Unexpected native termination or FP/memory bridge sequence");
        __asm__ volatile("fnstcw %0" : "=m"(actual_cw) : : "memory");
        if (actual_cw != result.cw_before) throw std::runtime_error("Native entry changed host x87 control");
    }
    const std::array<std::uint32_t, 8> registers{
        state.gpr.rax.dword, state.gpr.rcx.dword, state.gpr.rdx.dword, state.gpr.rbx.dword,
        state.gpr.rsp.dword, state.gpr.rbp.dword, state.gpr.rsi.dword, state.gpr.rdi.dword};
    std::memcpy(result.state.registers, registers.data(), sizeof(registers));
    result.state.flags = (state.aflag.cf << 0) | (state.aflag.pf << 2) | (state.aflag.af << 4) |
                         (state.aflag.zf << 6) | (state.aflag.sf << 7) | (state.aflag.df << 10) | (state.aflag.of << 11);
    result.state.eip = state.gpr.rip.dword;
    result.cw_after = state.x87.fxsave.cwd.flat;
    // Remill stores exceptions in separate byte flags, TOP in the FXSAVE word.
    result.sw_after = (state.x87.fxsave.swd.flat & 0x3800) |
        (state.sw.ie << 0) | (state.sw.de << 1) | (state.sw.ze << 2) | (state.sw.oe << 3) |
        (state.sw.ue << 4) | (state.sw.pe << 5) | (state.sw.sf << 6) |
        (state.sw.c0 << 8) | (state.sw.c1 << 9) | (state.sw.c2 << 10) | (state.sw.c3 << 14);
    // Final occupancy is observed only. Remill's general per-instruction tag
    // bookkeeping is outside this clean-stack push/pop fixture's admitted scope.
    result.tag_after = state.x87.fxsave.ftw.flat;
    memory.read({memory_base}, std::as_writable_bytes(std::span{result.memory}));
    return result;
}

static void check_bridges() {
    mw34::GuestMemory memory;
    memory.map({memory_base}, 16, mw34::Permissions::read | mw34::Permissions::write);
    bridge_failed = false;
    const auto bits = 0xbff0000000000000ULL;
    __remill_write_memory_f64(&memory, memory_base + 1, std::bit_cast<double>(bits));
    if (bridge_failed || std::bit_cast<std::uint64_t>(__remill_read_memory_f64(&memory, memory_base + 1)) != bits)
        throw std::runtime_error("Unaligned floating bridge failed");
    __remill_write_memory_32(&memory, memory_base + 3, 0x87654321U);
    if (bridge_failed || __remill_read_memory_32(&memory, memory_base + 3) != 0x87654321U)
        throw std::runtime_error("Unaligned integer bridge failed");
    std::array<std::byte, 16> word_before{}, word_after{};
    memory.read({memory_base}, word_before);
    bridge_failed = false;
    __remill_write_memory_32(&memory, memory_base + 13, 0xffffffffU);
    memory.read({memory_base}, word_after);
    if (!bridge_failed || word_before != word_after) throw std::runtime_error("Invalid word write admitted");
    bridge_failed = false;
    __remill_read_memory_32(&memory, memory_base + 13);
    if (!bridge_failed) throw std::runtime_error("Invalid word read admitted");
    for (auto address : {memory_base - 1, memory_base + 9, 0xffffffffU}) {
        std::array<std::byte, 16> before{}, after{};
        memory.read({memory_base}, before);
        bridge_failed = false;
        __remill_write_memory_f64(&memory, address, 1.0);
        memory.read({memory_base}, after);
        if (!bridge_failed || before != after) throw std::runtime_error("Invalid floating write admitted");
        bridge_failed = false;
        __remill_read_memory_f64(&memory, address);
        if (!bridge_failed) throw std::runtime_error("Invalid floating read admitted");
    }
    memory.protect({memory_base}, mw34::Permissions::read);
    bridge_failed = false;
    __remill_write_memory_f64(&memory, memory_base, 1.0);
    if (!bridge_failed) throw std::runtime_error("Read-only floating write admitted");
    bridge_failed = false;
    __remill_write_memory_32(&memory, memory_base, 0xffffffffU);
    if (!bridge_failed) throw std::runtime_error("Read-only word write admitted");
    std::cout << "Expansion memory bridges: twelve checks passed\n";
}

static void check_environment() {
    // Seed a nonempty x87 stack and sticky precision exception, then ensure the
    // inner guest scope restores host control/status/tags/register bytes/MXCSR.
    FpuScope restore_outer(0x037f);
    __asm__ volatile("fld1\n\tfldpi\n\tfaddp" : : : "memory");
    FpuScope::Image before{}, after{};
    __asm__ volatile("fxsave64 %0" : "=m"(before) : : "memory");
    std::uint16_t saved_sw{};
    std::memcpy(&saved_sw, before.bytes + 2, 2);
    if (!(saved_sw & 0x20) || !before.bytes[4]) {
        throw std::runtime_error("Host FP environment seed is not inexact/nonempty");
    }
    const auto same_registers = [&](const FpuScope::Image &image) {
        for (unsigned i = 0; i < 8; ++i)
            if (std::memcmp(before.bytes + 32 + i * 16, image.bytes + 32 + i * 16, 10)) return false;
        return true;
    };
    const auto same_active = [&](const FpuScope::Image &image) {
        return !std::memcmp(before.bytes, image.bytes, 5) &&
               !std::memcmp(before.bytes + 24, image.bytes + 24, 4) && same_registers(image);
    };
    unsigned count{};
    for (auto pc : {0, 2, 3}) for (auto rc : {0, 1, 2, 3}) {
        Request request{};
        request.state.registers[1] = memory_base + 65;
        request.state.registers[2] = memory_base + 257;
        request.state.registers[4] = memory_base + 2048;
        request.state.flags = 0x202;
        request.state.eip = code_base;
        request.cw = 0x7f | (pc << 8) | (rc << 10);
        request.base_bits = 0x3ff0000000000000ULL;
        request.increment_bits = fixture_kind == 0 ? 0x3c90000000000000ULL : 0; // 2^-54
        validate_request(request);
        const auto result = run_native(request);
        if (result.cw_after != request.cw) throw std::runtime_error("Guest control changed in environment check");
        __asm__ volatile("fxsave64 %0" : "=m"(after) : : "memory");
        if (!same_active(after) || std::memcmp(before.bytes + 6, after.bytes + 6, 18))
            throw std::runtime_error("Native FP environment was not restored");
        ++count;
    }
    try { FpuScope unwind(0x0c7f); throw std::runtime_error("authored unwind"); }
    catch (const std::runtime_error &) {}
    __asm__ volatile("fxsave64 %0" : "=m"(after) : : "memory");
    // Windows exception dispatch clears x87 instruction/data-pointer metadata.
    // Verify this against an unwrapped throw instead of attributing it to our
    // scope. Normal-return checks include full64-bit FIP/FDP and the opcode.
    if (!same_active(after))
        throw std::runtime_error("Active native FP state differs after unwinding");
    FpuScope::Image control{};
    FpuScope::restore(before);
    try { throw std::runtime_error("unwrapped control"); }
    catch (const std::runtime_error &) {}
    __asm__ volatile("fxsave64 %0" : "=m"(control) : : "memory");
    if (!same_active(control) || std::memcmp(after.bytes + 6, control.bytes + 6, 18))
        throw std::runtime_error("Unwrapped exception does not explain metadata difference");
    // This CPU zeroes pointers in masked FXSAVE images. A pending host exception
    // keeps synthetic full64-bit pointer metadata observable. Use no waiting
    // instruction until FNINIT clears it; guest scope resets it before entry.
    FpuScope::Image synthetic = before, seeded{}, returned{};
    const std::uint16_t pending_cw = 0x037e;
    const std::uint16_t pending_sw = saved_sw | 0x0081;
    const std::uint64_t high_ip = 0x00007ff62aef1000ULL, high_dp = 0x00007ff62aef3220ULL;
    std::memcpy(synthetic.bytes, &pending_cw, 2);
    std::memcpy(synthetic.bytes + 2, &pending_sw, 2);
    std::memcpy(synthetic.bytes + 8, &high_ip, 8);
    std::memcpy(synthetic.bytes + 16, &high_dp, 8);
    FpuScope::restore(synthetic);
    __asm__ volatile("fxsave64 %0" : "=m"(seeded) : : "memory");
    { FpuScope inner(0x037f); __asm__ volatile("fld1\n\tfldpi\n\tfaddp" : : : "memory"); }
    __asm__ volatile("fxsave64 %0\n\tfninit" : "=m"(returned) : : "memory", "st", "st(1)",
                     "st(2)", "st(3)", "st(4)", "st(5)", "st(6)", "st(7)");
    if (std::memcmp(seeded.bytes, returned.bytes, 5) ||
        std::memcmp(seeded.bytes + 6, returned.bytes + 6, 22) ||
        std::memcmp(seeded.bytes + 8, &high_ip, 8) || std::memcmp(seeded.bytes + 16, &high_dp, 8))
        throw std::runtime_error("Pending host exception/pointer state was not restored");
    for (unsigned i = 0; i < 8; ++i)
        if (std::memcmp(seeded.bytes + 32 + i * 16, returned.bytes + 32 + i * 16, 10))
            throw std::runtime_error("Pending host FP register state was not restored");
    std::cout << "Numeric FP environment: " << count + 3
              << " checks passed (12 normal restores, active-state unwind, EH control, full64-bit pending pointers)\n";
}

static void check_rounding_bridge() {
    unsigned count{};
    for (auto pc : {0, 2, 3}) for (auto rc : {0, 1, 2, 3}) for (unsigned sign : {0U, 1U}) {
        const auto cw = static_cast<std::uint16_t>(0x7f | (pc << 8) | (rc << 10));
        FpuScope restore(cw);
        __asm__ volatile("fld1\n\tfldpi\n\tfaddp" : : : "memory", "st", "st(1)", "st(2)",
                         "st(3)", "st(4)", "st(5)", "st(6)", "st(7)");
        std::array<std::uint8_t, 12> input{}, output{};
        input.fill(0xa5); output.fill(0x5a);
        const std::uint64_t significand = 0xc000000000000000ULL; // +/-1.5 exactly.
        const auto exponent = static_cast<std::uint16_t>(0x3fff | (sign << 15));
        std::memcpy(input.data() + 1, &significand, 8);
        std::memcpy(input.data() + 9, &exponent, 2);
        const auto preserved_input = input;
        FpuScope::Image before{}, after{};
        __asm__ volatile("fxsave64 %0" : "=m"(before) : : "memory");
        bridge_failed = false; rounding_count = 0;
        __mw34_x87_nearbyint80(input.data() + 1, output.data() + 1);
        __asm__ volatile("fxsave64 %0" : "=m"(after) : : "memory");
        const auto magnitude = (rc == 0 || (rc == 1 && sign) || (rc == 2 && !sign)) ? 2U : 1U;
        const std::uint64_t wanted_significand = 0x8000000000000000ULL;
        const auto wanted_exponent = static_cast<std::uint16_t>((magnitude == 2 ? 0x4000 : 0x3fff) | (sign << 15));
        if (bridge_failed || rounding_count != 1 || input != preserved_input || output[0] != 0x5a || output[11] != 0x5a ||
            std::memcmp(output.data() + 1, &wanted_significand, 8) || std::memcmp(output.data() + 9, &wanted_exponent, 2))
            throw std::runtime_error("80-bit rounding, sign, extent or call count differs");
        if (std::memcmp(before.bytes, after.bytes, 5) || std::memcmp(before.bytes + 6, after.bytes + 6, 22))
            throw std::runtime_error("Rounding bridge changed the host FP environment");
        for (unsigned i = 0; i < 8; ++i)
            if (std::memcmp(before.bytes + 32 + 16 * i, after.bytes + 32 + 16 * i, 10))
                throw std::runtime_error("Rounding bridge changed a host FP register");
        ++count;
    }
    std::cout << "80-bit pointer rounding bridge: " << count << " signed PC/RC cases passed\n";
}

int main(int argc, char **argv) {
    try {
        if (argc == 2 && std::string{argv[1]} == "--check-memory-bridges") { check_bridges(); return 0; }
        if (argc == 2 && std::string{argv[1]} == "--check-fp-environment") { check_environment(); return 0; }
        if (argc == 2 && std::string{argv[1]} == "--check-rounding-bridge") { check_rounding_bridge(); return 0; }
        if (argc != 4) throw std::runtime_error("Usage: native input output fixture");
        std::ifstream fixture(argv[3], std::ios::binary);
        std::vector<std::uint8_t> code((std::istreambuf_iterator<char>(fixture)), {});
        if (!matches_fixture(code)) throw std::runtime_error("Authored code identity differs");
        std::ifstream input(argv[1], std::ios::binary);
        const auto requests = read_requests(input);
        std::ofstream output(argv[2], std::ios::binary | std::ios::trunc);
        write_record(output, output_header(static_cast<std::uint32_t>(requests.size()), 64));
        for (const auto &request : requests) write_record(output, run_native(request));
        std::cout << "Executed " << requests.size() << " native x64 spill/conversion cases\n";
        return 0;
    } catch (const std::exception &error) { std::cerr << error.what() << '\n'; return 1; }
}
