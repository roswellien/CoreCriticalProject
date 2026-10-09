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
#include <vector>

namespace m2 {
constexpr std::uint32_t code_base = 0x10000000, sentinel = code_base + 0x100;
constexpr std::uint32_t stack_base = 0x20001000, data_base = 0x21001000;
constexpr std::uint32_t flags_mask = 0xcd5;
constexpr std::size_t page = 4096;
constexpr const char *fixture_hash =
    "edc5e8b32eb6fd28b3520a36c6e65ab36fc11cc20136df284ed6851f40f1d6d4";
struct Cpu {
    std::uint32_t registers[8], flags, eip;
};
struct Request {
    Cpu state;
    std::uint32_t argument, global, timer, choice, seed;
};
struct Result {
    Cpu state;
    std::uint32_t status, calls, returns;
    std::array<std::uint8_t, 8192> memory;
};
struct Header {
    char magic[8];
    std::uint32_t version, count, size, pointer_bits;
};
static_assert(sizeof(Cpu) == 40 && sizeof(Request) == 60 && sizeof(Result) == 8244 &&
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
    if (std::memcmp(h.magic, "MW34M2Q1", 8) || h.version != 1 || h.size != sizeof(Request) ||
        h.pointer_bits != 32 || !h.count || h.count > 100000)
        throw std::runtime_error("Invalid M2 header");
    return h;
}
inline Header output(std::uint32_t count) {
    Header h{};
    std::memcpy(h.magic, "MW34M2R1", 8);
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
    return b;
}
inline void end(std::istream &in) {
    if (in.peek() != std::char_traits<char>::eof())
        throw std::runtime_error("Trailing input");
}
inline std::vector<std::uint8_t> code(const char *path) {
    std::ifstream in(path, std::ios::binary);
    std::vector<std::uint8_t> b((std::istreambuf_iterator<char>(in)), {});
    constexpr std::array<std::uint8_t, 32> expected{0xed, 0xc5, 0xe8, 0xb3, 0x2e, 0xb6, 0xfd, 0x28,
                                                    0xb3, 0x52, 0x0a, 0x36, 0xc6, 0xe6, 0x5a, 0xb3,
                                                    0x6f, 0xc1, 0x1c, 0xc2, 0x01, 0x36, 0xdf, 0x28,
                                                    0x4e, 0xd6, 0x85, 0x1f, 0x40, 0xf1, 0xd6, 0xd4};
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
} // namespace m2
