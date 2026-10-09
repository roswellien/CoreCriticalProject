// Authored x87 control storage/load repair protocol. No game code is admitted.
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

#ifndef MW34_X87_FIXTURE_KIND
#define MW34_X87_FIXTURE_KIND 0
#endif
#if MW34_X87_FIXTURE_KIND != 0 && MW34_X87_FIXTURE_KIND != 1
#error Unsupported authored x87 repair fixture kind
#endif

namespace mw34::x87_repair {
inline constexpr std::uint32_t fixture_kind = MW34_X87_FIXTURE_KIND;
inline constexpr std::uint32_t case_count = fixture_kind == 0 ? 12 : 144;
inline constexpr std::uint32_t code_base = 0x10000000;
inline constexpr std::uint32_t return_sentinel = 0x10000100;
inline constexpr std::uint32_t stack_base = 0x20000000;
inline constexpr std::uint32_t memory_base = 0x20001000;
inline constexpr std::size_t memory_size = 4096;
inline constexpr std::uint32_t observed_flags = 0xcd5;
#if MW34_X87_FIXTURE_KIND == 0
inline constexpr std::array<std::uint8_t, 3> code_identity{0xd9, 0x39, 0xc3};
#else
inline constexpr std::array<std::uint8_t, 5> code_identity{0xd9, 0x29, 0xd9, 0x3a, 0xc3};
#endif

struct CpuState {
    std::uint32_t registers[8]; // EAX, ECX, EDX, EBX, ESP, EBP, ESI, EDI.
    std::uint32_t flags;
    std::uint32_t eip;
};
struct Request {
    CpuState state;
    std::uint32_t a; // Entry CW; only the twelve masked PC/RC modes are admitted.
    std::uint32_t b; // Loaded CW for kind 1; unused frame word for kind 0.
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
        throw std::runtime_error("Truncated control repair input");
    return value;
}
template <class T> void write_record(std::ostream &stream, const T &value) {
    if (!stream.write(reinterpret_cast<const char *>(&value), sizeof(value)))
        throw std::runtime_error("Failed writing control repair result");
}
inline Header input_header(std::istream &stream) {
    const auto header = read_record<Header>(stream);
    if (std::memcmp(header.magic, "MW34REQ1", 8) || header.version != 1 ||
        header.count != case_count || header.record_size != sizeof(Request) ||
        header.pointer_bits != 32)
        throw std::runtime_error("Control repair requires fixture-specific v1 x86 requests");
    return header;
}
inline Header output_header(std::uint32_t count, std::uint32_t pointer_bits) {
    if (count != case_count || (pointer_bits != 32 && pointer_bits != 64))
        throw std::runtime_error("Invalid control repair output count or pointer width");
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
        throw std::runtime_error("Unexpected trailing control repair input");
}
inline bool matches_fixture(const std::vector<std::uint8_t> &code) {
    return code.size() == code_identity.size() &&
           std::equal(code.begin(), code.end(), code_identity.begin());
}
inline bool legal_control_word(std::uint32_t value) {
    return !(value & ~0x0f7fU) && (value & 0xffU) == 0x7f && ((value >> 8) & 3) != 1;
}
inline bool safe_word(std::uint32_t value, std::uint32_t esp) {
    const std::uint64_t address = value;
    return address >= memory_base && address + 2 <= memory_base + memory_size &&
           !(address < std::uint64_t{esp} + 12 && address + 2 > esp);
}
inline void validate_request(const Request &request) {
    const auto esp = request.state.registers[4];
    const auto ecx = request.state.registers[1];
    const auto edx = request.state.registers[2];
    if (request.state.eip != code_base || esp < memory_base + 16 ||
        esp > memory_base + memory_size - 16 ||
        (request.state.flags & ~(observed_flags | 0x202U)) != 0 ||
        (request.state.flags & 0x202U) != 0x202U)
        throw std::runtime_error("Invalid entry state or unsafe integer flags");
    if constexpr (fixture_kind == 0) {
        if (!safe_word(ecx, esp))
            throw std::runtime_error("Invalid output word or overlap with return frame");
    } else {
        if (!safe_word(ecx, esp))
            throw std::runtime_error("Invalid input word or overlap with return frame");
        if (!safe_word(edx, esp))
            throw std::runtime_error("Invalid output word or overlap with return frame");
        if (std::uint64_t{ecx} < std::uint64_t{edx} + 2 &&
            std::uint64_t{edx} < std::uint64_t{ecx} + 2)
            throw std::runtime_error("Input and output words overlap");
    }
    if (!legal_control_word(request.a) || (fixture_kind == 1 && !legal_control_word(request.b)))
        throw std::runtime_error("Control word is outside reviewed masked PC/RC modes");
}
inline std::vector<Request> read_requests(std::istream &stream) {
    const auto header = input_header(stream);
    std::vector<Request> requests;
    requests.reserve(header.count);
    std::set<std::uint64_t> modes;
    for (std::uint32_t index = 0; index < header.count; ++index) {
        auto request = read_record<Request>(stream);
        validate_request(request);
        const auto identity = fixture_kind == 0 ? std::uint64_t{request.a}
                                                : (std::uint64_t{request.a} << 32) | request.b;
        if (!modes.insert(identity).second)
            throw std::runtime_error("Duplicate reviewed control word mode or transition");
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
    if constexpr (fixture_kind == 1) {
        const auto loaded_cw = static_cast<std::uint16_t>(request.b);
        std::memcpy(bytes.data() + (request.state.registers[1] - memory_base), &loaded_cw,
                    sizeof(loaded_cw));
    }
    return bytes;
}
} // namespace mw34::x87_repair
