// Separate authored spill/conversion probes. No game instructions are admitted.
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
#include <string>
#include <tuple>
#include <vector>

#ifndef MW34_X87_FIXTURE_KIND
#define MW34_X87_FIXTURE_KIND 0
#endif

namespace mw34::x87_expand {
inline constexpr unsigned fixture_kind = MW34_X87_FIXTURE_KIND;
#if MW34_X87_FIXTURE_KIND == 0
inline constexpr const char *kind_name = "spill64";
inline constexpr std::uint32_t case_count = 240;
inline constexpr std::size_t input_size = 16, output_size = 16;
inline constexpr std::array<std::uint8_t, 16> code_identity{
    0xdd, 0x01, 0xdc, 0x41, 0x08, 0xdd, 0x5a, 0x08,
    0xdd, 0x42, 0x08, 0xdc, 0x21, 0xdd, 0x1a, 0xc3};
#elif MW34_X87_FIXTURE_KIND == 1
inline constexpr const char *kind_name = "fistp32";
inline constexpr std::uint32_t case_count = 384;
inline constexpr std::size_t input_size = 8, output_size = 4;
inline constexpr std::array<std::uint8_t, 5> code_identity{0xdd, 0x01, 0xdb, 0x1a, 0xc3};
#else
#error "MW34_X87_FIXTURE_KIND must be 0 (spill64) or 1 (fistp32)"
#endif
inline constexpr std::uint32_t code_base = 0x10000000;
inline constexpr std::uint32_t return_sentinel = 0x10000100;
inline constexpr std::uint32_t stack_base = 0x20000000;
inline constexpr std::uint32_t memory_base = 0x20001000;
inline constexpr std::size_t memory_size = 4096;
inline constexpr std::uint32_t observed_flags = 0xcd5;
inline constexpr std::uint16_t observed_status = 0x38ff;
inline constexpr std::array<unsigned, 5> increment_powers{30, 54, 24, 53, 64};
// Ordered exact binary64 encodings: signed zero; both signs of .25/.5/.75,
// 1/1.25/1.5/1.75/2/2.5/3.5/12345.5; then eight signed32-safe boundaries.
inline constexpr std::array<std::uint64_t, 32> conversion_vectors{
    0x0000000000000000ULL, 0x8000000000000000ULL,
    0x3fd0000000000000ULL, 0xbfd0000000000000ULL,
    0x3fe0000000000000ULL, 0xbfe0000000000000ULL,
    0x3fe8000000000000ULL, 0xbfe8000000000000ULL,
    0x3ff0000000000000ULL, 0xbff0000000000000ULL,
    0x3ff4000000000000ULL, 0xbff4000000000000ULL,
    0x3ff8000000000000ULL, 0xbff8000000000000ULL,
    0x3ffc000000000000ULL, 0xbffc000000000000ULL,
    0x4000000000000000ULL, 0xc000000000000000ULL,
    0x4004000000000000ULL, 0xc004000000000000ULL,
    0x400c000000000000ULL, 0xc00c000000000000ULL,
    0x40c81cc000000000ULL, 0xc0c81cc000000000ULL,
    0xc1e0000000000000ULL, 0x41dfffffffc00000ULL,
    0xc1dffffffff00000ULL, 0x41dfffffffb00000ULL,
    0xc1dfffffffe00000ULL, 0x41dfffffffa00000ULL,
    0xc1dfffffffd00000ULL, 0x41dfffffff900000ULL};

struct CpuState {
    std::uint32_t registers[8]; // EAX, ECX, EDX, EBX, ESP, EBP, ESI, EDI.
    std::uint32_t flags;
    std::uint32_t eip;
};
struct Request {
    CpuState state;
    std::uint32_t cw;
    std::uint32_t memory_seed;
    std::uint64_t base_bits;
    std::uint64_t increment_bits;
};
struct Result {
    CpuState state;
    std::uint32_t status;
    std::array<std::uint8_t, memory_size> memory;
    std::uint16_t cw_before;
    std::uint16_t cw_after;
    std::uint16_t sw_before;
    std::uint16_t sw_after;
    std::uint8_t tag_before;
    std::uint8_t tag_after;
    std::uint16_t reserved;
};
struct Header {
    char magic[8];
    std::uint32_t version;
    std::uint32_t count;
    std::uint32_t record_size;
    std::uint32_t pointer_bits;
};
static_assert(sizeof(CpuState) == 40 && sizeof(Request) == 64);
static_assert(offsetof(Request, base_bits) == 48 && offsetof(Request, increment_bits) == 56);
static_assert(sizeof(Result) == 4152 && offsetof(Result, cw_before) == 4140);
static_assert(offsetof(Result, sw_before) == 4144 && offsetof(Result, tag_before) == 4148);
static_assert(offsetof(Result, reserved) == 4150 && sizeof(Header) == 24);

template <class T> T read_record(std::istream &stream) {
    T value{};
    if (!stream.read(reinterpret_cast<char *>(&value), sizeof(value)))
        throw std::runtime_error("Truncated expansion probe input");
    return value;
}
template <class T> void write_record(std::ostream &stream, const T &value) {
    if (!stream.write(reinterpret_cast<const char *>(&value), sizeof(value)))
        throw std::runtime_error("Failed writing expansion probe result");
}
inline Header input_header(std::istream &stream) {
    const auto header = read_record<Header>(stream);
    if (std::memcmp(header.magic, "MW34REQ1", 8) || header.version != 1 ||
        header.count != case_count || header.record_size != sizeof(Request) ||
        header.pointer_bits != 32)
        throw std::runtime_error("Expansion probe requires " + std::to_string(case_count) +
                                 " v1 x86 requests");
    return header;
}
inline Header output_header(std::uint32_t count, std::uint32_t pointer_bits) {
    if (count != case_count || (pointer_bits != 32 && pointer_bits != 64))
        throw std::runtime_error("Invalid expansion probe output count or pointer width");
    Header header{};
    std::memcpy(header.magic, "MW34RES1", 8);
    header.version = 1;
    header.count = count;
    header.record_size = sizeof(Result);
    header.pointer_bits = pointer_bits;
    return header;
}
inline void require_end(std::istream &stream) {
    if (stream.peek() != std::char_traits<char>::eof())
        throw std::runtime_error("Unexpected trailing expansion probe input");
}
inline bool matches_fixture(const std::vector<std::uint8_t> &code) {
    return code.size() == code_identity.size() &&
           std::equal(code.begin(), code.end(), code_identity.begin());
}
inline bool legal_control_word(std::uint32_t value) {
    return !(value & ~0x0f7fU) && (value & 0xffU) == 0x7f && ((value >> 8) & 3) != 1;
}
inline bool legal_vector(std::uint64_t base, std::uint64_t increment) {
    if constexpr (fixture_kind == 1) {
        return increment == 0 &&
               std::find(conversion_vectors.begin(), conversion_vectors.end(), base) !=
                   conversion_vectors.end();
    } else {
        constexpr std::uint64_t magnitude_mask = 0x7fffffffffffffffULL;
        if ((base & magnitude_mask) != 0x3ff0000000000000ULL)
            return false;
        for (const auto power : increment_powers)
            if ((increment & magnitude_mask) == ((std::uint64_t{1023} - power) << 52))
                return true;
        return false;
    }
}
inline bool overlaps(std::uint64_t left, std::uint64_t left_size, std::uint64_t right,
                     std::uint64_t right_size) {
    return left < right + right_size && right < left + left_size;
}
inline bool safe_span(std::uint32_t value, std::size_t size, std::uint32_t esp) {
    const std::uint64_t address = value;
    return address >= memory_base && address + size <= memory_base + memory_size &&
           !overlaps(address, size, esp, 12);
}
inline void validate_request(const Request &request) {
    const auto esp = request.state.registers[4];
    const auto input = request.state.registers[1];
    const auto output = request.state.registers[2];
    if (request.state.eip != code_base || esp < memory_base + 16 ||
        esp > memory_base + memory_size - 16 ||
        (request.state.flags & ~(observed_flags | 0x202U)) != 0 ||
        (request.state.flags & 0x202U) != 0x202U)
        throw std::runtime_error("Invalid entry state or unsafe integer flags");
    if (!safe_span(input, input_size, esp))
        throw std::runtime_error("Invalid expansion input span or overlap with return frame");
    if (!safe_span(output, output_size, esp))
        throw std::runtime_error("Invalid expansion output span or overlap with return frame");
    if (overlaps(input, input_size, output, output_size))
        throw std::runtime_error("Expansion input and output spans overlap");
    if (!legal_control_word(request.cw))
        throw std::runtime_error("Control word is outside reviewed masked PC/RC modes");
    if (!legal_vector(request.base_bits, request.increment_bits))
        throw std::runtime_error("Expansion bits are outside reviewed exact input vectors");
}
inline std::vector<Request> read_requests(std::istream &stream) {
    const auto header = input_header(stream);
    std::vector<Request> requests;
    requests.reserve(header.count);
    std::set<std::tuple<std::uint32_t, std::uint64_t, std::uint64_t>> cases;
    for (std::uint32_t index = 0; index < header.count; ++index) {
        auto request = read_record<Request>(stream);
        validate_request(request);
        if (!cases.emplace(request.cw, request.base_bits, request.increment_bits).second)
            throw std::runtime_error("Duplicate reviewed expansion mode and vector");
        requests.push_back(request);
    }
    require_end(stream);
    return requests;
}
inline std::array<std::uint8_t, memory_size> initial_memory(const Request &request) {
    std::array<std::uint8_t, memory_size> bytes{};
    for (std::size_t index = 0; index < memory_size; ++index)
        bytes[index] = static_cast<std::uint8_t>((index * 37 + request.memory_seed) & 0xff);
    const std::array<std::uint32_t, 3> frame{return_sentinel, request.cw, request.memory_seed};
    std::memcpy(bytes.data() + (request.state.registers[4] - memory_base), frame.data(),
                sizeof(frame));
    const std::array<std::uint64_t, 2> input{request.base_bits, request.increment_bits};
    std::memcpy(bytes.data() + (request.state.registers[1] - memory_base), input.data(), input_size);
    return bytes;
}
} // namespace mw34::x87_expand
