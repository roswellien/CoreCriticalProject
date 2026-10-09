#include "memory/guest_memory.hpp"
#include "control_protocol.hpp"
#include <remill/Arch/X86/Runtime/State.h>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

using namespace mw34::x87_repair;
static_assert(sizeof(void *) == 8 && sizeof(State) == 3504);
static_assert(__builtin_offsetof(State, x87) + __builtin_offsetof(FpuFXSAVE, cwd) == 2768);
extern "C" void *mw34_lifted_entry(State *, std::uint32_t, void *);
static unsigned return_count{};
static bool bridge_failed{};
static std::int32_t guest_rounding{};

static unsigned setter_count{};
extern "C" void __remill_fpu_set_rounding(std::int32_t value) {
    if (value < 0 || value > 3) { bridge_failed = true; return; }
    guest_rounding = value;
    ++setter_count;
}
extern "C" std::uint16_t __remill_read_memory_16(void *memory, std::uint32_t address) {
    try { return static_cast<mw34::GuestMemory *>(memory)->load<std::uint16_t>({address}); }
    catch (const std::exception &) { bridge_failed = true; return 0; }
}
extern "C" std::uint32_t __remill_read_memory_32(void *memory, std::uint32_t address) {
    try { return static_cast<mw34::GuestMemory *>(memory)->load<std::uint32_t>({address}); }
    catch (const std::exception &) { bridge_failed = true; return 0; }
}
extern "C" void *__remill_write_memory_16(void *memory, std::uint32_t address,
                                         std::uint16_t value) {
    try { static_cast<mw34::GuestMemory *>(memory)->store<std::uint16_t>({address}, value); }
    catch (const std::exception &) { bridge_failed = true; }
    return memory;
}
extern "C" void *__remill_function_return(State *state, std::uint32_t address, void *memory) {
    if (address != return_sentinel || state->gpr.rip.dword != return_sentinel)
        bridge_failed = true;
    ++return_count;
    return memory;
}

static Result run_native(const Request &request) {
    const auto initial = initial_memory(request);
    mw34::GuestMemory memory;
    memory.map({memory_base}, memory_size, mw34::Permissions::read | mw34::Permissions::write);
    memory.write({memory_base}, std::as_bytes(std::span{initial}));
    State state;
    std::memset(&state, 0, sizeof(state));
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
    state.x87.fxsave.cwd.flat = static_cast<std::uint16_t>(request.a);
    guest_rounding = (request.a >> 10) & 3;
    Result result{};
    result.cw_before = state.x87.fxsave.cwd.flat;
    return_count = 0;
    setter_count = 0;
    bridge_failed = false;
    if (mw34_lifted_entry(&state, code_base, &memory) != &memory ||
        return_count != 1 || bridge_failed)
        throw std::runtime_error("Unexpected native termination or failed memory bridge");
    const auto expected_rc = ((fixture_kind == 1 ? request.b : request.a) >> 10) & 3;
    if (setter_count != (fixture_kind == 1 ? 1U : 0U) || guest_rounding != expected_rc)
        throw std::runtime_error("Rounding setter call count or admitted RC differs");
    const std::array<std::uint32_t, 8> registers{
        state.gpr.rax.dword, state.gpr.rcx.dword, state.gpr.rdx.dword, state.gpr.rbx.dword,
        state.gpr.rsp.dword, state.gpr.rbp.dword, state.gpr.rsi.dword, state.gpr.rdi.dword};
    std::memcpy(result.state.registers, registers.data(), sizeof(registers));
    result.state.flags = (state.aflag.cf << 0) | (state.aflag.pf << 2) | (state.aflag.af << 4) |
                         (state.aflag.zf << 6) | (state.aflag.sf << 7) | (state.aflag.df << 10) |
                         (state.aflag.of << 11);
    result.state.eip = state.gpr.rip.dword;
    result.cw_after = state.x87.fxsave.cwd.flat;
    memory.read({memory_base}, std::as_writable_bytes(std::span{result.memory}));
    return result;
}

static void check_bridges() {
    mw34::GuestMemory memory;
    memory.map({memory_base}, 8, mw34::Permissions::read | mw34::Permissions::write);
    bridge_failed = false;
    __remill_write_memory_16(&memory, memory_base + 1, 0x1234);
    if (bridge_failed || memory.load<std::uint16_t>({memory_base + 1}) != 0x1234)
        throw std::runtime_error("Valid unaligned write failed");
    if (__remill_read_memory_16(&memory, memory_base + 1) != 0x1234 || bridge_failed)
        throw std::runtime_error("Valid unaligned read failed");
    for (auto address : {memory_base - 1, memory_base + 7, 0xffffffffU}) {
        std::array<std::byte, 8> before{}, after{};
        memory.read({memory_base}, before);
        bridge_failed = false;
        __remill_write_memory_16(&memory, address, 0xffff);
        memory.read({memory_base}, after);
        if (!bridge_failed || before != after)
            throw std::runtime_error("Invalid write accepted or changed memory");
    }
    for (auto address : {memory_base - 1, memory_base + 7, 0xffffffffU}) {
        bridge_failed = false;
        __remill_read_memory_16(&memory, address);
        if (!bridge_failed) throw std::runtime_error("Invalid word read accepted");
    }
    bridge_failed = false;
    __remill_read_memory_32(&memory, memory_base + 6);
    if (!bridge_failed) throw std::runtime_error("Invalid return read accepted");
    memory.protect({memory_base}, mw34::Permissions::read);
    bridge_failed = false;
    __remill_write_memory_16(&memory, memory_base, 0xffff);
    if (!bridge_failed) throw std::runtime_error("Read-only write accepted");
    for (std::int32_t rc = 0; rc < 4; ++rc) {
        setter_count = 0;
        bridge_failed = false;
        __remill_fpu_set_rounding(rc);
        if (guest_rounding != rc || setter_count != 1 || bridge_failed)
            throw std::runtime_error("Valid rounding setter failed");
    }
    setter_count = 0;
    bridge_failed = false;
    __remill_fpu_set_rounding(4);
    if (!bridge_failed || setter_count != 0 || guest_rounding != 3)
        throw std::runtime_error("Invalid rounding setter accepted");
    std::cout << "Control repair bridges: fifteen checks passed\n";
}

int main(int argc, char **argv) {
    try {
        if (argc == 2 && std::string{argv[1]} == "--check-memory-bridges") {
            check_bridges(); return 0;
        }
        if (argc != 4) throw std::runtime_error("Usage: native input output fixture");
        std::ifstream fixture(argv[3], std::ios::binary);
        std::vector<std::uint8_t> code((std::istreambuf_iterator<char>(fixture)), {});
        if (!matches_fixture(code)) throw std::runtime_error("Authored code identity differs");
        std::ifstream input(argv[1], std::ios::binary);
        const auto requests = read_requests(input);
        std::ofstream output(argv[2], std::ios::binary | std::ios::trunc);
        write_record(output, output_header(static_cast<std::uint32_t>(requests.size()), 64));
        for (const auto &request : requests) write_record(output, run_native(request));
        std::cout << "Executed " << requests.size() << " native x64 control-word repair cases\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n'; return 1;
    }
}
