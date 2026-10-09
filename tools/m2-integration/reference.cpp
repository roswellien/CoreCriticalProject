#include "protocol.hpp"
#include <iostream>
#include <mmsystem.h>
using namespace m2;
static_assert(sizeof(void *) == 4);
extern "C" {
Cpu m2_input{}, m2_output{};
std::uint32_t m2_host_esp{};
void m2_enter();
void m2_capture();
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
        if (argc == 2 && std::string(argv[1]) == "--live-timer") {
            auto a = timeGetTime();
            Sleep(20);
            auto b = timeGetTime();
            auto delta = std::uint32_t(b - a);
            if (!delta || delta > 10000)
                throw std::runtime_error("Implausible live timer span");
            std::cout << "{\"api\":\"WINMM.timeGetTime\",\"first\":" << a << ",\"second\":" << b
                      << ",\"delta_ms\":" << delta << ",\"pointer_bits\":32}\n";
            return 0;
        }
        SetErrorMode(SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX);
        if (argc != 4)
            throw std::runtime_error("reference input output fixture");
        auto b = code(argv[3]);
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
        std::ifstream in(argv[1], std::ios::binary);
        auto h = header(in);
        std::ofstream out(argv[2], std::ios::binary | std::ios::trunc);
        write(out, output(h.count));
        for (std::uint32_t i = 0; i < h.count; ++i) {
            auto q = read<Request>(in);
            auto bytes = initial(q);
            std::memcpy(reinterpret_cast<void *>(stack_base), bytes.data(), page);
            std::memcpy(reinterpret_cast<void *>(data_base), bytes.data() + page, page);
            m2_input = q.state;
            m2_output = {};
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
            write(out, r);
        }
        end(in);
        std::cout << "Original x86 cases: " << h.count << '\n';
        return 0;
    } catch (const std::exception &e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
