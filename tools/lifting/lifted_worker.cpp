#include "memory/guest_memory.hpp"
#include "protocol.hpp"
#include <remill/Arch/X86/Runtime/State.h>

#include <iostream>
#include <vector>

using namespace mw34::experiment;
static_assert(sizeof(void *) == 8, "Lifted worker must be native x64");
static_assert(sizeof(State) == 3504);
static_assert(__builtin_offsetof(State, aflag) == 2064);
static_assert(__builtin_offsetof(State, gpr) == 2208);
static_assert(__builtin_offsetof(GPR, rax) == 8);
static_assert(__builtin_offsetof(GPR, rsp) == 104);
static_assert(__builtin_offsetof(GPR, rip) == 264);
extern "C" void *mw34_lifted_entry(State *, std::uint32_t, void *);
static unsigned return_count = 0;
static bool bridge_failed = false;

// Guest addresses stay uint32_t; host pointers are never synthesized from them.
extern "C" std::uint32_t __remill_read_memory_32(void *memory, std::uint32_t address) {
    try {
        return static_cast<mw34::GuestMemory *>(memory)->load<std::uint32_t>({address});
    } catch (const std::exception &) {
        bridge_failed = true;
        return 0;
    }
}
extern "C" void *__remill_write_memory_32(void *memory, std::uint32_t address,
                                          std::uint32_t value) {
    try {
        static_cast<mw34::GuestMemory *>(memory)->store<std::uint32_t>({address}, value);
    } catch (const std::exception &) {
        bridge_failed = true;
    }
    return memory;
}
extern "C" void *__remill_function_return(State *state, std::uint32_t address, void *memory) {
    if (address != return_sentinel || state->gpr.rip.dword != return_sentinel) {
        bridge_failed = true;
    }
    ++return_count;
    return memory;
}

// These probes test the actual host memory bridges' failure behavior. They do
// not supply instruction semantics or substitute for original x86 execution.
static void check_memory_bridges() {
    mw34::GuestMemory memory;
    memory.map({memory_base}, 12, mw34::Permissions::read | mw34::Permissions::write);
    memory.store<std::uint32_t>({memory_base + 1}, 0x12345678);
    bridge_failed = false;
    if (__remill_read_memory_32(&memory, memory_base + 1) != 0x12345678 || bridge_failed)
        throw std::runtime_error("Valid unaligned bridge read failed");
    __remill_write_memory_32(&memory, memory_base + 5, 0xaabbccdd);
    if (bridge_failed || memory.load<std::uint32_t>({memory_base + 5}) != 0xaabbccdd)
        throw std::runtime_error("Valid unaligned bridge write failed");
    for (auto address : {memory_base - 1, memory_base + 10, 0xfffffffeU}) {
        bridge_failed = false;
        __remill_read_memory_32(&memory, address);
        if (!bridge_failed)
            throw std::runtime_error("Invalid bridge read was accepted");
    }
    std::array<std::byte, 12> before{}, after{};
    memory.read({memory_base}, before);
    for (auto address : {memory_base - 1, memory_base + 10, 0xfffffffeU}) {
        bridge_failed = false;
        if (__remill_write_memory_32(&memory, address, 0xdeadbeef) != &memory || !bridge_failed)
            throw std::runtime_error("Invalid bridge write was accepted");
        memory.read({memory_base}, after);
        if (before != after)
            throw std::runtime_error("Failed bridge write changed memory");
    }
    memory.protect({memory_base}, mw34::Permissions::read);
    bridge_failed = false;
    __remill_write_memory_32(&memory, memory_base, 0xdeadbeef);
    memory.read({memory_base}, after);
    if (!bridge_failed || before != after)
        throw std::runtime_error("Bridge ignored read-only protection");
    std::cout << "Memory bridges: valid unaligned reads/writes and 7 failure probes passed\n";
}

static Result run_lifted(const Request &request) {
    const auto initial = initial_memory(request, compiled_fixture);
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
    return_count = 0;
    bridge_failed = false;
    if (mw34_lifted_entry(&state, entry_address(compiled_fixture), &memory) != &memory ||
        return_count != 1 || bridge_failed) {
        throw std::runtime_error("Unexpected lifted termination or memory token");
    }
    Result result{};
    const std::array<std::uint32_t, 8> registers{
        state.gpr.rax.dword, state.gpr.rcx.dword, state.gpr.rdx.dword, state.gpr.rbx.dword,
        state.gpr.rsp.dword, state.gpr.rbp.dword, state.gpr.rsi.dword, state.gpr.rdi.dword};
    std::memcpy(result.state.registers, registers.data(), sizeof(registers));
    result.state.flags = (state.aflag.cf << 0) | (state.aflag.pf << 2) | (state.aflag.af << 4) |
                         (state.aflag.zf << 6) | (state.aflag.sf << 7) | (state.aflag.df << 10) |
                         (state.aflag.of << 11);
    result.state.eip = state.gpr.rip.dword;
    memory.read({memory_base}, std::as_writable_bytes(std::span{result.memory}));
    return result;
}
int main(int argc, char **argv) {
    try {
        if (argc == 2 && std::string{argv[1]} == "--check-memory-bridges") {
            check_memory_bridges();
            return 0;
        }
        if (argc != 4)
            throw std::runtime_error("Usage: lifted input output fixture");
        std::ifstream fixture(argv[3], std::ios::binary);
        std::vector<std::uint8_t> code((std::istreambuf_iterator<char>(fixture)), {});
        if (!matches_fixture(code, compiled_fixture))
            throw std::runtime_error("Code does not match compiled authored fixture identity or "
                                     "admitted private helper");
        std::ifstream input(argv[1], std::ios::binary);
        const auto header = input_header(input);
        std::ofstream output(argv[2], std::ios::binary | std::ios::trunc);
        write_record(output, output_header(header.count));
        for (std::uint32_t index = 0; index < header.count; ++index) {
            const auto request = read_record<Request>(input);
            write_record(output, run_lifted(request));
        }
        require_end(input);
        std::cout << "Executed " << header.count << " native x64 lifted cases\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
