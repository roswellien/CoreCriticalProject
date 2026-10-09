// Separate hardware stack/state reference; original admitted instructions only.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include "protocol.hpp"
#include <fstream>
#include <iostream>
#include <windows.h>
using namespace mw34::x87_state;
static_assert(sizeof(void *) == 4);
extern "C" {
CpuState mw_input{}, mw_output{};
std::uint32_t mw_host_esp{}, mw_entry = code_base;
alignas(16) std::uint8_t mw_guest_seed[512]{}, mw_guest_before[512]{}, mw_guest_after[512]{},
    mw_host_fp[512]{}, mw_restored_fp[512]{};
std::uint8_t mw_env_before[28]{}, mw_env_after[28]{};
void mw_enter_guest();
void mw_capture_guest();
void mw_restore_host_fp();
}
static std::uint32_t run_guest() {
    __try {
        mw_enter_guest();
        return 0;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        mw_restore_host_fp();
        return 1;
    }
}
struct Mapping {
    void *address{};
    ~Mapping() {
        if (address)
            VirtualFree(address, 0, MEM_RELEASE);
    }
};
static std::uint16_t word(const std::uint8_t *bytes, unsigned offset) {
    return static_cast<std::uint16_t>(bytes[offset] | (std::uint16_t{bytes[offset + 1]} << 8));
}
static void seed(const Request &q) {
    std::memset(mw_guest_seed, 0, 512);
    auto put16 = [&](unsigned offset, std::uint16_t value) {
        std::memcpy(mw_guest_seed + offset, &value, 2);
    };
    put16(0, static_cast<std::uint16_t>(q.cw));
    put16(2, static_cast<std::uint16_t>((q.initial_top << 11) | q.initial_sw));
    mw_guest_seed[4] = static_cast<std::uint8_t>(q.physical_ftw);
    std::uint32_t mxcsr = 0x1f80, mask = 0x0000ffff;
    std::memcpy(mw_guest_seed + 24, &mxcsr, 4);
    std::memcpy(mw_guest_seed + 28, &mask, 4);
    for (unsigned i = 0; i < 8; ++i)
        std::memcpy(mw_guest_seed + 32 + 16 * i, q.logical_slots[i].data(), 10);
    // A distinct valid SSE byte pattern tests preservation at the actual host boundary.
    for (unsigned i = 160; i < 288; ++i)
        mw_guest_seed[i] = static_cast<std::uint8_t>(i * 29 + q.memory_seed);
}
int main(int argc, char **argv) {
    try {
        SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
        if (argc != 4)
            throw std::runtime_error("Usage: state_reference input output authored_fixture");
        std::ifstream fixture(argv[3], std::ios::binary);
        std::vector<std::uint8_t> code((std::istreambuf_iterator<char>(fixture)), {});
        if (!matches_fixture(code))
            throw std::runtime_error("Unknown authored state profile/fixture identity");
        std::ifstream input(argv[1], std::ios::binary);
        const auto requests = read_requests(input);
        Mapping executable{VirtualAlloc(reinterpret_cast<void *>(code_base), 4096,
                                        MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE)};
        if (executable.address != reinterpret_cast<void *>(code_base))
            throw std::runtime_error("Required authored code VA unavailable");
        std::memcpy(executable.address, code.data(), code.size());
        auto *stub = static_cast<std::uint8_t *>(executable.address) + 0x100;
        stub[0] = 0xe9;
        auto displacement = static_cast<std::uint32_t>(
            reinterpret_cast<std::uintptr_t>(&mw_capture_guest) - (return_sentinel + 5));
        std::memcpy(stub + 1, &displacement, 4);
        DWORD old{};
        if (!VirtualProtect(executable.address, 4096, PAGE_EXECUTE_READ, &old) ||
            !FlushInstructionCache(GetCurrentProcess(), executable.address, 4096))
            throw std::runtime_error("Code protect/flush failed");
        Mapping stack{VirtualAlloc(reinterpret_cast<void *>(stack_base), 3 * 4096, MEM_RESERVE,
                                   PAGE_NOACCESS)};
        auto *memory = reinterpret_cast<void *>(memory_base);
        if (stack.address != reinterpret_cast<void *>(stack_base) ||
            VirtualAlloc(memory, memory_size, MEM_COMMIT, PAGE_READWRITE) != memory)
            throw std::runtime_error("Required guarded state page unavailable");
        std::ofstream output(argv[2], std::ios::binary | std::ios::trunc);
        write_record(output, output_header(static_cast<std::uint32_t>(requests.size()), 32));
        for (const auto &q : requests) {
            auto initial = initial_memory(q);
            std::memcpy(memory, initial.data(), initial.size());
            mw_input = q.state;
            mw_output = {};
            seed(q);
            std::memset(mw_host_fp, 0, 512);
            std::memset(mw_restored_fp, 0, 512);
            std::memset(mw_guest_before, 0, 512);
            std::memset(mw_guest_after, 0, 512);
            std::memset(mw_env_before, 0, 28);
            std::memset(mw_env_after, 0, 28);
            Result r{};
            r.status = run_guest();
            if (r.status)
                throw std::runtime_error("Admitted masked original state instruction faulted");
            if (std::memcmp(mw_host_fp, mw_restored_fp, 512))
                throw std::runtime_error("Original host FP/SSE/MXCSR restore failed");
            r.host_restored = 1;
            r.state = mw_output;
            r.state.flags &= observed_flags;
            std::memcpy(r.memory.data(), memory, memory_size);
            r.cw_before = word(mw_guest_before, 0);
            r.cw_after = word(mw_guest_after, 0);
            r.sw_before = word(mw_guest_before, 2);
            r.sw_after = word(mw_guest_after, 2);
            r.ftw_before = mw_guest_before[4];
            r.ftw_after = mw_guest_after[4];
            r.full_tag_before = word(mw_env_before, 8);
            r.full_tag_after = word(mw_env_after, 8);
            for (unsigned i = 0; i < 8; ++i) {
                std::memcpy(r.logical_before[i].data(), mw_guest_before + 32 + 16 * i, 10);
                std::memcpy(r.logical_after[i].data(), mw_guest_after + 32 + 16 * i, 10);
            }
            std::memcpy(r.fx_before.data(), mw_guest_before, 512);
            std::memcpy(r.fx_after.data(), mw_guest_after, 512);
            std::memcpy(r.env_before.data(), mw_env_before, 28);
            std::memcpy(r.env_after.data(), mw_env_after, 28);
            write_record(output, r);
        }
        std::cout << "Executed " << requests.size() << " original x86 " << kind_name
                  << " state cases; full host FXSAVE restored\n";
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
