// Isolated, project-authored x87 arithmetic reference. No game code is admitted.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>

#include "protocol.hpp"

#include <fstream>
#include <iostream>

namespace mw34::x87_arithmetic {
struct Mapping {
    void *address{};
    ~Mapping() {
        if (address)
            VirtualFree(address, 0, MEM_RELEASE);
    }
};
} // namespace mw34::x87_arithmetic

using namespace mw34::x87_arithmetic;
static_assert(sizeof(void *) == 4);
extern "C" {
CpuState mw_input{}, mw_output{};
std::uint32_t mw_host_esp{}, mw_entry = code_base;
std::uint16_t mw_entry_cw{};
alignas(16) std::uint8_t mw_host_fp[512]{}, mw_restored_fp[512]{}, mw_guest_before[512]{},
    mw_guest_after[512]{};
void mw_enter_guest();
void mw_capture_guest();
void mw_restore_host_fp();
}

// No C++ unwinding crosses the hardware guest call.
static std::uint32_t run_guest() {
    __try {
        mw_enter_guest();
        return 0;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        mw_restore_host_fp();
        return 1;
    }
}

int main(int argc, char **argv) {
    try {
        SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
        if (argc != 4)
            throw std::runtime_error("Usage: x87_reference input output authored_fixture");
        std::ifstream fixture(argv[3], std::ios::binary);
        std::vector<std::uint8_t> code((std::istreambuf_iterator<char>(fixture)), {});
        if (!matches_fixture(code))
            throw std::runtime_error("Code differs from authored expansion fixture identity");
        std::ifstream input(argv[1], std::ios::binary);
        const auto requests = read_requests(input);
        Mapping executable{VirtualAlloc(reinterpret_cast<void *>(code_base), 4096,
                                        MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE)};
        if (executable.address != reinterpret_cast<void *>(code_base))
            throw std::runtime_error("Required authored code address unavailable");
        std::memcpy(executable.address, code.data(), code.size());
        auto *stub = static_cast<std::uint8_t *>(executable.address) + 0x100;
        stub[0] = 0xe9;
        const auto destination = reinterpret_cast<std::uintptr_t>(&mw_capture_guest);
        const auto displacement = static_cast<std::uint32_t>(destination - (return_sentinel + 5));
        std::memcpy(stub + 1, &displacement, sizeof(displacement));
        DWORD old_protection{};
        if (!VirtualProtect(executable.address, 4096, PAGE_EXECUTE_READ, &old_protection) ||
            !FlushInstructionCache(GetCurrentProcess(), executable.address, 4096))
            throw std::runtime_error("Authored code protection or flush failed");
        Mapping stack{VirtualAlloc(reinterpret_cast<void *>(stack_base), 3 * 4096, MEM_RESERVE,
                                   PAGE_NOACCESS)};
        auto *memory = reinterpret_cast<void *>(memory_base);
        if (stack.address != reinterpret_cast<void *>(stack_base) ||
            VirtualAlloc(memory, memory_size, MEM_COMMIT, PAGE_READWRITE) != memory)
            throw std::runtime_error("Required guarded memory page unavailable");
        std::ofstream output(argv[2], std::ios::binary | std::ios::trunc);
        write_record(output, output_header(static_cast<std::uint32_t>(requests.size()), 32));
        for (const auto &request : requests) {
            const auto initial = initial_memory(request);
            std::memcpy(memory, initial.data(), initial.size());
            mw_input = request.state;
            mw_output = {};
            mw_entry_cw = static_cast<std::uint16_t>(request.cw);
            std::memset(mw_host_fp, 0, sizeof(mw_host_fp));
            std::memset(mw_restored_fp, 0, sizeof(mw_restored_fp));
            std::memset(mw_guest_before, 0, sizeof(mw_guest_before));
            std::memset(mw_guest_after, 0, sizeof(mw_guest_after));
            Result result{};
            result.status = run_guest();
            if (!result.status && std::memcmp(mw_host_fp, mw_restored_fp, sizeof(mw_host_fp)))
                throw std::runtime_error("Host FP/vector state restore check failed");
            result.state = mw_output;
            result.state.flags &= observed_flags;
            std::memcpy(&result.cw_before, mw_guest_before, sizeof(result.cw_before));
            std::memcpy(&result.cw_after, mw_guest_after, sizeof(result.cw_after));
            std::memcpy(&result.sw_before, mw_guest_before + 2, sizeof(result.sw_before));
            std::memcpy(&result.sw_after, mw_guest_after + 2, sizeof(result.sw_after));
            result.tag_before = mw_guest_before[4];
            result.tag_after = mw_guest_after[4];
            std::memcpy(result.memory.data(), memory, memory_size);
            write_record(output, result);
            if (result.status)
                throw std::runtime_error("Authored guest hardware fault; expansion probe failed");
        }
        std::cout << "Executed " << requests.size()
                  << " authored x86 " << kind_name << " cases; host FXSAVE state restored\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
