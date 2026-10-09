// Isolated authored FNSTCW protocol. No game code is admitted.
#pragma once

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <istream>
#include <ostream>
#include <set>
#include <stdexcept>
#include <vector>

namespace mw34::x87_probe {
inline constexpr std::uint32_t code_base = 0x10000000;
inline constexpr std::uint32_t return_sentinel = 0x10000100;
inline constexpr std::uint32_t stack_base = 0x20000000;
inline constexpr std::uint32_t memory_base = 0x20001000;
inline constexpr std::size_t memory_size = 4096;
inline constexpr std::uint32_t observed_flags = 0xcd5;
inline constexpr std::array<std::uint8_t, 3> code_identity{0xd9, 0x39, 0xc3};

struct CpuState {
    std::uint32_t registers[8]; // EAX, ECX, EDX, EBX, ESP, EBP, ESI, EDI.
    std::uint32_t flags;
    std::uint32_t eip;
};
struct Request {
    CpuState state;
    std::uint32_t a; // Entry CW, restricted to the twelve masked PC/RC modes.
    std::uint32_t b; // Unused stack argument, retained in the memory comparison.
    std::uint32_t memory_seed;
};
struct Result {
    CpuState state;
    std::uint32_t status;
    std::array<std::uint8_t, memory_size> memory;
    std::uint16_t cw_before;
    std::uint16_t cw_after;
};
struct Header {
    char magic[8];
    std::uint32_t version;
    std::uint32_t count;
    std::uint32_t record_size;
    std::uint32_t pointer_bits;
};
static_assert(sizeof(CpuState) == 40 && sizeof(Request) == 52);
static_assert(sizeof(Result) == 4144 && offsetof(Result, cw_before) == 4140);
static_assert(sizeof(Header) == 24);

template <class T> T read_record(std::istream &stream) {
    T value{};
    if (!stream.read(reinterpret_cast<char *>(&value), sizeof(value)))
        throw std::runtime_error("Truncated control probe input");
    return value;
}
template <class T> void write_record(std::ostream &stream, const T &value) {
    if (!stream.write(reinterpret_cast<const char *>(&value), sizeof(value)))
        throw std::runtime_error("Failed writing control probe result");
}
inline Header input_header(std::istream &stream) {
    const auto header = read_record<Header>(stream);
    if (std::memcmp(header.magic, "MW34REQ1", 8) || header.version != 1 || header.count != 12 ||
        header.record_size != sizeof(Request) || header.pointer_bits != 32)
        throw std::runtime_error("Control probe requires twelve v1 x86 requests");
    return header;
}
inline Header output_header(std::uint32_t pointer_bits) {
    if (pointer_bits != 32 && pointer_bits != 64)
        throw std::runtime_error("Invalid control probe worker pointer width");
    Header header{};
    std::memcpy(header.magic, "MW34RES1", 8);
    header.version = 1;
    header.count = 12;
    header.record_size = sizeof(Result);
    header.pointer_bits = pointer_bits;
    return header;
}
inline void require_end(std::istream &stream) {
    if (stream.peek() != std::char_traits<char>::eof())
        throw std::runtime_error("Unexpected trailing control probe input");
}
inline bool matches_fixture(const std::vector<std::uint8_t> &code) {
    return code.size() == code_identity.size() &&
           std::equal(code.begin(), code.end(), code_identity.begin());
}
inline void validate_request(const Request &request) {
    const auto esp = request.state.registers[4];
    const std::uint64_t target = request.state.registers[1];
    if (request.state.eip != code_base || esp < memory_base + 16 ||
        esp > memory_base + memory_size - 16 ||
        (request.state.flags & ~(observed_flags | 0x202U)) != 0 ||
        (request.state.flags & 0x202U) != 0x202U)
        throw std::runtime_error("Invalid entry state or unsafe integer flags");
    if (target < memory_base || target + 2 > memory_base + memory_size ||
        (target < std::uint64_t{esp} + 12 && target + 2 > esp))
        throw std::runtime_error("Invalid output word or overlap with return frame");
    const auto pc = (request.a >> 8) & 3;
    if ((request.a & ~0x0f7fU) || (request.a & 0xffU) != 0x7f || pc == 1)
        throw std::runtime_error("Control word is outside reviewed masked PC/RC modes");
}
inline std::vector<Request> read_requests(std::istream &stream) {
    const auto header = input_header(stream);
    std::vector<Request> requests;
    std::set<std::uint32_t> control_words;
    for (std::uint32_t index = 0; index < header.count; ++index) {
        auto request = read_record<Request>(stream);
        validate_request(request);
        if (!control_words.insert(request.a).second)
            throw std::runtime_error("Duplicate reviewed control word mode");
        requests.push_back(request);
    }
    require_end(stream);
    return requests;
}
inline std::array<std::uint8_t, memory_size> initial_memory(const Request &request) {
    std::array<std::uint8_t, memory_size> bytes{};
    for (std::size_t index = 0; index < memory_size; ++index)
        bytes[index] = static_cast<std::uint8_t>((index * 37 + request.memory_seed) & 0xff);
    const std::array<std::uint32_t, 3> frame{return_sentinel, request.a, request.b};
    std::memcpy(bytes.data() + (request.state.registers[4] - memory_base), frame.data(),
                sizeof(frame));
    return bytes;
}
} // namespace mw34::x87_probe
