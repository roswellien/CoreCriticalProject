#include "protocol.hpp"
#include <iostream>
#include <mmsystem.h>
using namespace m2_boundary_extension;
static_assert(sizeof(void *) == 4);
extern "C" {
Cpu m2_input{}, m2_output{};
std::uint32_t m2_host_esp{};
std::uint32_t m2_guest_api_esp{}, m2_live_provider_calls{};
void m2_enter();
void m2_capture();
void m2_live_bridge();
std::uint32_t m2_timer_read() {
    ++m2_live_provider_calls;
    return timeGetTime();
}
}
static std::uint32_t run() {
    __try {
        m2_enter();
        return 0;
    } __except (EXCEPTION_EXECUTE_HANDLER) {
        return 1;
    }
}
struct Map {
    void *p{};
    Map() = default;
    Map(const Map &) = delete;
    Map &operator=(const Map &) = delete;
    Map(Map &&other) noexcept : p(other.p) { other.p = nullptr; }
    ~Map() {
        if (p)
            VirtualFree(p, 0, MEM_RELEASE);
    }
};
static Map map(std::uint32_t addr, std::size_t size) {
    Map m;
    m.p = VirtualAlloc(reinterpret_cast<void *>(addr), size, MEM_RESERVE | MEM_COMMIT,
                       PAGE_READWRITE);
    if (m.p != reinterpret_cast<void *>(addr))
        throw std::runtime_error("Required authored address unavailable");
    return m;
}
int main(int argc, char **argv) {
    try {
        SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
        const bool live = argc == 5 && std::string(argv[1]) == "--live-timer";
        if (argc != (live ? 5 : 4))
            throw std::runtime_error("reference [--live-timer] input output fixture");
        auto b = code(argv[live ? 4 : 3]);
        std::ifstream in(argv[live ? 2 : 1], std::ios::binary);
        const auto matrix = requests(in, live);
        if (b.size() != 0x521)
            throw std::runtime_error("Fixture size mismatch");
        auto exec = map(code_base, page), stack = map(0x20000000, 8192),
             data = map(0x21000000, 8192);
        std::memcpy(exec.p, b.data(), b.size());
        auto *stub = static_cast<std::uint8_t *>(exec.p) + 0x100;
        stub[0] = 0xe9;
        auto delta = static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(&m2_capture) -
                                                (sentinel + 5));
        std::memcpy(stub + 1, &delta, 4);
        DWORD old{};
        if (!VirtualProtect(exec.p, page, PAGE_EXECUTE_READ, &old) ||
            !FlushInstructionCache(GetCurrentProcess(), exec.p, page))
            throw std::runtime_error("Code protect failed");
        std::vector<Result> results;
        results.reserve(matrix.size());
        for (const auto &q : matrix) {
            auto bytes = initial(q);
            if (live) {
                const auto target = static_cast<std::uint32_t>(reinterpret_cast<std::uintptr_t>(&m2_live_bridge));
                std::memcpy(bytes.data() + page + 8, &target, 4);
            }
            std::memcpy(reinterpret_cast<void *>(stack_base), bytes.data(), page);
            std::memcpy(reinterpret_cast<void *>(data_base), bytes.data() + page, page);
            m2_input = q.state;
            m2_output = {};
            m2_live_provider_calls = 0;
            Result r{};
            r.status = run();
            if (r.status)
                throw std::runtime_error("Original hardware fault");
            r.state = m2_output;
            r.state.flags &= flags_mask;
            std::memcpy(r.memory.data(), reinterpret_cast<void *>(stack_base), page);
            std::memcpy(r.memory.data() + page, reinterpret_cast<void *>(data_base), page);
            r.calls = 3;
            r.returns = 4;
            std::memcpy(&r.provider_calls, r.memory.data() + page + 0x60, 4);
            std::memcpy(&r.bridge_calls, r.memory.data() + page + 0x64, 4);
            r.provider_return = r.state.registers[2];
            if (r.provider_calls != 1 || r.bridge_calls != 1 ||
                (live && m2_live_provider_calls != 1))
                throw std::runtime_error("Original provider/bridge count mismatch");
            results.push_back(r);
            if (live && results.size() != matrix.size()) Sleep(40);
        }
        std::ofstream out(argv[live ? 3 : 2], std::ios::binary | std::ios::trunc);
        write(out, output(static_cast<std::uint32_t>(results.size())));
        for (const auto &r : results) write(out, r);
        if (live) {
            const auto executable = reinterpret_cast<std::uintptr_t>(GetModuleHandleA(nullptr));
            const auto *dos = reinterpret_cast<const IMAGE_DOS_HEADER *>(executable);
            const auto *nt = reinterpret_cast<const IMAGE_NT_HEADERS32 *>(executable + dos->e_lfanew);
            const auto target = reinterpret_cast<std::uintptr_t>(&m2_live_bridge);
            std::cout << "{\"provider\":\"WINMM.timeGetTime\",\"module_path\":\"" << live_module_path()
                      << "\",\"pointer_bits\":32,\"live_context_cases\":8,\"provider_calls\":8,"
                         "\"bridge_calls\":8,\"guest_iat_target\":" << target
                      << ",\"executable_base\":" << executable << ",\"shim_rva\":" << target - executable
                      << ",\"image_size\":" << nt->OptionalHeader.SizeOfImage << "}\n";
        } else std::cout << "Original x86 cases: " << results.size() << '\n';
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
