#include "protocol.hpp"

#include <iostream>
#include <vector>

using namespace mw34::experiment;
static_assert(sizeof(void *) == 4, "Reference worker must execute as x86");
extern "C" {
CpuState mw_input{};
CpuState mw_output{};
std::uint32_t mw_host_esp = 0;
std::uint32_t mw_entry = code_base;
void mw_enter_guest();
void mw_capture_guest();
}

// No C++ unwinding crosses guest execution. SEH catches hardware faults.
static std::uint32_t run_guest() {
    __try {
        mw_enter_guest();
        return 0;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return 1;
    }
}
struct Mapping {
    void *address;
    ~Mapping() {
        if (address)
            VirtualFree(address, 0, MEM_RELEASE);
    }
};
int main(int argc, char **argv) {
    try {
        SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
        if (argc != 4)
            throw std::runtime_error("Usage: reference input output fixture");
        std::ifstream fixture(argv[3], std::ios::binary);
        std::vector<std::uint8_t> code((std::istreambuf_iterator<char>(fixture)), {});
        const auto kind = identify_fixture(code);
        // The capture stub has its own page at the authored fixture address.
        // The real helper retains its original PC in a separate committed page.
        Mapping executable{VirtualAlloc(reinterpret_cast<void *>(code_base), 4096,
                                        MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE)};
        if (executable.address != reinterpret_cast<void *>(code_base)) {
            throw std::runtime_error("Required code address unavailable");
        }
        Mapping original{};
        void *guest_code = executable.address;
        if (kind == FixtureKind::mw3_helper) {
            original.address = VirtualAlloc(reinterpret_cast<void *>(helper_reservation), 65536,
                                            MEM_RESERVE, PAGE_NOACCESS);
            guest_code = reinterpret_cast<void *>(helper_page);
            if (original.address != reinterpret_cast<void *>(helper_reservation) ||
                VirtualAlloc(guest_code, 4096, MEM_COMMIT, PAGE_READWRITE) != guest_code) {
                throw std::runtime_error("Required original helper page unavailable");
            }
            std::memcpy(static_cast<std::uint8_t *>(guest_code) + (helper_entry - helper_page),
                        code.data(), code.size());
        } else {
            std::memcpy(guest_code, code.data(), code.size());
        }
        mw_entry = entry_address(kind);
        // Fixed guest return sentinel jumps to capture without changing flags/registers.
        auto *stub = static_cast<std::uint8_t *>(executable.address) + 0x100;
        stub[0] = 0xe9;
        const auto destination = reinterpret_cast<std::uintptr_t>(&mw_capture_guest);
        const auto displacement = static_cast<std::uint32_t>(destination - (return_sentinel + 5));
        std::memcpy(stub + 1, &displacement, sizeof(displacement));
        DWORD old_protection = 0;
        if (!VirtualProtect(executable.address, 4096, PAGE_EXECUTE_READ, &old_protection) ||
            !FlushInstructionCache(GetCurrentProcess(), executable.address, 4096)) {
            throw std::runtime_error("Code protection/flush failed");
        }
        if (kind == FixtureKind::mw3_helper &&
            (!VirtualProtect(guest_code, 4096, PAGE_EXECUTE_READ, &old_protection) ||
             !FlushInstructionCache(GetCurrentProcess(), guest_code, 4096))) {
            throw std::runtime_error("Helper protection/flush failed");
        }
        Mapping stack{VirtualAlloc(reinterpret_cast<void *>(stack_reservation), 3 * 4096,
                                   MEM_RESERVE, PAGE_NOACCESS)};
        auto *memory = reinterpret_cast<void *>(memory_base);
        if (stack.address != reinterpret_cast<void *>(stack_reservation) ||
            VirtualAlloc(memory, memory_size, MEM_COMMIT, PAGE_READWRITE) != memory) {
            throw std::runtime_error("Required guarded stack unavailable");
        }
        std::ifstream input(argv[1], std::ios::binary);
        const auto header = input_header(input);
        std::ofstream output(argv[2], std::ios::binary | std::ios::trunc);
        write_record(output, output_header(header.count));
        for (std::uint32_t index = 0; index < header.count; ++index) {
            const auto request = read_record<Request>(input);
            const auto bytes = initial_memory(request, kind);
            std::memcpy(memory, bytes.data(), bytes.size());
            mw_input = request.state;
            mw_output = {};
            Result result{};
            result.status = run_guest();
            result.state = mw_output;
            result.state.flags &= observed_flags;
            std::memcpy(result.memory.data(), memory, memory_size);
            write_record(output, result);
            if (result.status)
                throw std::runtime_error("Guest hardware fault; run failed");
        }
        require_end(input);
        std::cout << "Executed " << header.count << " x86 cases\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
