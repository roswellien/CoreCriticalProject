#pragma once
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <array>
// clang-format off
#include <windows.h>
#include <bcrypt.h>
// clang-format on
#include <cstdint>
#include <cstring>
#include <fstream>
#include <span>
#include <stdexcept>
#include <string>
#include <vector>

namespace m2_boundary_extension {
constexpr std::uint32_t code_base = 0x10000000, sentinel = code_base + 0x100;
constexpr std::uint32_t stack_base = 0x20001000, data_base = 0x21001000;
constexpr std::uint32_t flags_mask = 0xcd5;
constexpr std::size_t page = 4096;
constexpr const char *fixture_hash =
    "61b236a2a8402d96c48a28340203ae08f1351cf7b3f095ab4b4b817e38e6c667";
struct Cpu {
    std::uint32_t registers[8], flags, eip;
};
struct Request {
    Cpu state;
    std::uint32_t argument, global, timer, choice, seed;
};
struct Result {
    Cpu state;
    std::uint32_t status, calls, returns, provider_calls, bridge_calls, provider_return;
    std::array<std::uint8_t, 8192> memory;
};
struct Header {
    char magic[8];
    std::uint32_t version, count, size, pointer_bits;
};
static_assert(sizeof(Cpu) == 40 && sizeof(Request) == 60 && sizeof(Result) == 8256 &&
              sizeof(Header) == 24);
template <class T> T read(std::istream &in) {
    T result{};
    if (!in.read(reinterpret_cast<char *>(&result), sizeof(result)))
        throw std::runtime_error("Truncated input");
    return result;
}
template <class T> void write(std::ostream &out, const T &v) {
    if (!out.write(reinterpret_cast<const char *>(&v), sizeof(v)))
        throw std::runtime_error("Output failed");
}
inline Header header(std::istream &in) {
    auto h = read<Header>(in);
    if (std::memcmp(h.magic, "MW34BEXQ", 8) || h.version != 1 || h.size != sizeof(Request) ||
        h.pointer_bits != 32 || !h.count || h.count > 100000)
        throw std::runtime_error("Invalid M2 header");
    return h;
}
inline Header output(std::uint32_t count) {
    Header h{};
    std::memcpy(h.magic, "MW34BEXR", 8);
    h.version = 1;
    h.count = count;
    h.size = sizeof(Result);
    h.pointer_bits = sizeof(void *) * 8;
    return h;
}
inline void validate(const Request &q, bool admit_unknown = false) {
    auto esp = q.state.registers[4];
    if (q.state.eip != code_base || esp < stack_base + 32 || esp > stack_base + page - 16 ||
        (q.state.flags & ~(flags_mask | 0x202U)) || (q.state.flags & 0x202U) != 0x202U ||
        (!admit_unknown && q.choice > 1))
        throw std::runtime_error("Unsafe entry/frame/selector");
}
inline std::array<std::uint8_t, 8192> initial(const Request &q, bool admit_unknown = false) {
    validate(q, admit_unknown);
    std::array<std::uint8_t, 8192> b{};
    for (std::size_t i = 0; i < b.size(); ++i)
        b[i] = static_cast<std::uint8_t>(i * 37 + q.seed);
    auto store = [&](std::size_t off, std::uint32_t v) { std::memcpy(b.data() + off, &v, 4); };
    store(q.state.registers[4] - stack_base, sentinel);
    store(q.state.registers[4] - stack_base + 4, q.argument);
    store(page, q.global);
    store(page + 8, code_base + 0x300);
    store(page + 12, q.choice == 0   ? code_base + 0x400
                     : q.choice == 1 ? code_base + 0x500
                                     : 0xdeadbeef);
    store(page + 16, q.timer);
    store(page + 0x60, 0);
    store(page + 0x64, 0);
    return b;
}
inline void end(std::istream &in) {
    if (in.peek() != std::char_traits<char>::eof())
        throw std::runtime_error("Trailing input");
}
inline std::vector<Request> requests(std::istream &in, bool live = false) {
    const auto h = header(in);
    if (live && h.count != 8) throw std::runtime_error("Live matrix requires eight records");
    std::vector<Request> result;
    result.reserve(h.count);
    for (std::uint32_t i = 0; i < h.count; ++i) {
        auto q = read<Request>(in);
        validate(q);
        if (live && ((q.state.flags & 0x400U) || q.timer != 0))
            throw std::runtime_error("Live provider requires DF0 and zero unused timer input");
        result.push_back(q);
    }
    end(in);
    return result;
}
inline std::string live_module_path() {
    const auto module = GetModuleHandleA("winmm.dll");
    std::array<char, 32768> declared{}, system{}, wow64{};
    if (!module || !GetModuleFileNameA(module, declared.data(), static_cast<DWORD>(declared.size())))
        throw std::runtime_error("Live provider module path unavailable");
    std::string result(declared.data());
    BOOL redirected{};
    if (!IsWow64Process(GetCurrentProcess(), &redirected))
        throw std::runtime_error("Provider architecture unavailable");
    if (redirected) {
        if (!GetSystemDirectoryA(system.data(), static_cast<UINT>(system.size())) ||
            !GetSystemWow64DirectoryA(wow64.data(), static_cast<UINT>(wow64.size())))
            throw std::runtime_error("WOW64 provider directory unavailable");
        const auto split = result.find_last_of("\\/");
        if (split != std::string::npos && !_stricmp(result.substr(0, split).c_str(), system.data()))
            result = std::string(wow64.data()) + result.substr(split);
    }
    for (auto &ch : result) if (ch == '\\') ch = '/';
    return result;
}
inline std::vector<std::uint8_t> code(const char *path) {
    std::ifstream in(path, std::ios::binary);
    std::vector<std::uint8_t> b((std::istreambuf_iterator<char>(in)), {});
    constexpr std::array<std::uint8_t, 32> expected{0x61, 0xb2, 0x36, 0xa2, 0xa8, 0x40, 0x2d, 0x96,
                                                    0xc4, 0x8a, 0x28, 0x34, 0x02, 0x03, 0xae, 0x08,
                                                    0xf1, 0x35, 0x1c, 0xf7, 0xb3, 0xf0, 0x95, 0xab,
                                                    0x4b, 0x4b, 0x81, 0x7e, 0x38, 0xe6, 0xc6, 0x67};
    BCRYPT_ALG_HANDLE alg{};
    BCRYPT_HASH_HANDLE hash{};
    std::array<std::uint8_t, 32> actual{};
    bool okay = BCryptOpenAlgorithmProvider(&alg, BCRYPT_SHA256_ALGORITHM, nullptr, 0) >= 0 &&
                BCryptCreateHash(alg, &hash, nullptr, 0, nullptr, 0, 0) >= 0 &&
                BCryptHashData(hash, b.data(), static_cast<ULONG>(b.size()), 0) >= 0 &&
                BCryptFinishHash(hash, actual.data(), 32, 0) >= 0;
    if (hash)
        BCryptDestroyHash(hash);
    if (alg)
        BCryptCloseAlgorithmProvider(alg, 0);
    if (!okay || b.size() != 0x521 || actual != expected)
        throw std::runtime_error("Fixture identity mismatch");
    return b;
}
} // namespace m2_boundary_extension
