// Separate authored raw80 stack/state gate; no game instructions are admitted.
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
#if MW34_X87_FIXTURE_KIND < 0 || MW34_X87_FIXTURE_KIND > 3
#error "MW34_X87_FIXTURE_KIND must be 0..3 (push/pop/exchange/free)"
#endif
namespace mw34::x87_state {
inline constexpr unsigned fixture_kind = MW34_X87_FIXTURE_KIND;
inline constexpr std::array<const char *, 4> kind_names{"push", "pop", "exchange", "free"};
inline constexpr const char *kind_name = kind_names[fixture_kind];
inline constexpr std::array<std::array<std::uint8_t, 3>, 4> identities{
    {{0xdb, 0x29, 0xc3}, {0xdb, 0x3a, 0xc3}, {0xd9, 0xc9, 0xc3}, {0xdd, 0xc1, 0xc3}}};
inline constexpr auto code_identity = identities[fixture_kind];
inline constexpr std::uint32_t case_count = 3456, code_base = 0x10000000,
                               return_sentinel = 0x10000100, stack_base = 0x20000000,
                               memory_base = 0x20001000;
inline constexpr std::size_t memory_size = 4096, input_size = 10, output_size = 10;
inline constexpr std::uint32_t observed_flags = 0xcd5;
inline constexpr std::uint16_t observed_status = fixture_kind == 3 ? 0x38ff : 0x3aff;
using Raw80 = std::array<std::uint8_t, 10>;
constexpr Raw80 raw80(std::uint64_t significand, std::uint16_t exponent) {
    Raw80 value{};
    for (unsigned i = 0; i < 8; ++i)
        value[i] = static_cast<std::uint8_t>(significand >> (8 * i));
    value[8] = static_cast<std::uint8_t>(exponent);
    value[9] = static_cast<std::uint8_t>(exponent >> 8);
    return value;
}
inline constexpr std::array<std::array<Raw80, 8>, 2> patterns{
    {{raw80(0x8000000000000001ULL, 0x3fff), raw80(0x9000000000000003ULL, 0xbfff),
      raw80(0xa000000000000005ULL, 0x4000), raw80(0xb000000000000007ULL, 0xc000),
      raw80(0xc000000000000009ULL, 0x4001), raw80(0xd00000000000000bULL, 0xc001),
      raw80(0xe00000000000000dULL, 0x3ffe), raw80(0xf00000000000000fULL, 0xbffe)},
     {raw80(0, 0), raw80(0, 0x8000), raw80(0x8000000000000000ULL, 0x7fff),
      raw80(0x8000000000000000ULL, 0xffff), raw80(0xc000000000001234ULL, 0x7fff),
      raw80(0xc000000000004321ULL, 0xffff), raw80(0xd000000000005678ULL, 0x7fff),
      raw80(0xe00000000000abcdULL, 0xffff)}}};
inline constexpr std::array<Raw80, 2> input_patterns{raw80(0x8000000000000055ULL, 0x4002),
                                                     raw80(0xc00000000000beefULL, 0x7fff)};
struct CpuState {
    std::uint32_t registers[8], flags, eip;
};
struct Request {
    CpuState state;
    std::uint32_t cw, memory_seed, initial_top, physical_ftw, initial_sw, pattern_id;
    std::array<Raw80, 8> logical_slots;
    Raw80 input_raw80;
    std::uint16_t reserved;
};
struct Result {
    CpuState state;
    std::uint32_t status;
    std::array<std::uint8_t, memory_size> memory;
    std::uint32_t cw_before, cw_after, sw_before, sw_after, ftw_before, ftw_after, full_tag_before,
        full_tag_after;
    std::array<Raw80, 8> logical_before, logical_after;
    std::array<std::uint8_t, 512> fx_before, fx_after;
    std::array<std::uint8_t, 28> env_before, env_after;
    std::uint32_t host_restored;
};
struct Header {
    char magic[8];
    std::uint32_t version, count, record_size, pointer_bits;
};
static_assert(sizeof(CpuState) == 40 && sizeof(Request) == 156 && sizeof(Result) == 5416 &&
              sizeof(Header) == 24);
static_assert(offsetof(Request, logical_slots) == 64 && offsetof(Request, input_raw80) == 144 &&
              offsetof(Request, reserved) == 154);
static_assert(offsetof(Result, cw_before) == 4140 && offsetof(Result, logical_before) == 4172 &&
              offsetof(Result, fx_before) == 4332 && offsetof(Result, env_before) == 5356 &&
              offsetof(Result, host_restored) == 5412);
template <class T> T read_record(std::istream &stream) {
    T value{};
    if (!stream.read(reinterpret_cast<char *>(&value), sizeof(value)))
        throw std::runtime_error("Truncated x87 state request");
    return value;
}
template <class T> void write_record(std::ostream &stream, const T &value) {
    if (!stream.write(reinterpret_cast<const char *>(&value), sizeof(value)))
        throw std::runtime_error("Failed x87 state output");
}
inline Header input_header(std::istream &stream) {
    auto h = read_record<Header>(stream);
    if (std::memcmp(h.magic, "MW34REQ1", 8) || h.version != 1 || h.count != case_count ||
        h.record_size != sizeof(Request) || h.pointer_bits != 32)
        throw std::runtime_error("State probe requires3456 admitted v1 x86 requests");
    return h;
}
inline Header output_header(std::uint32_t count, std::uint32_t bits) {
    if (count != case_count || (bits != 32 && bits != 64))
        throw std::runtime_error("Invalid x87 state output count/width");
    Header h{};
    std::memcpy(h.magic, "MW34RES1", 8);
    h.version = 1;
    h.count = count;
    h.record_size = sizeof(Result);
    h.pointer_bits = bits;
    return h;
}
inline void require_end(std::istream &stream) {
    if (stream.peek() != std::char_traits<char>::eof())
        throw std::runtime_error("Trailing x87 state request bytes");
}
inline bool matches_fixture(const std::vector<std::uint8_t> &code) {
    return code.size() == code_identity.size() &&
           std::equal(code.begin(), code.end(), code_identity.begin());
}
inline bool legal_control_word(std::uint32_t value) {
    return !(value & ~0x0f7fU) && (value & 0xffU) == 0x7f && ((value >> 8) & 3) != 1;
}
inline bool overlaps(std::uint64_t a, std::uint64_t n, std::uint64_t b, std::uint64_t m) {
    return a < b + m && b < a + n;
}
inline bool safe_span(std::uint32_t address, std::size_t size, std::uint32_t esp) {
    return address >= memory_base &&
           std::uint64_t{address} + size <= std::uint64_t{memory_base} + memory_size &&
           !overlaps(address, size, esp, 12);
}
inline std::uint8_t logical_occupancy(std::uint32_t top, std::uint32_t physical) {
    std::uint8_t logical{};
    for (unsigned i = 0; i < 8; ++i)
        if (physical & (1U << ((top + i) & 7)))
            logical |= static_cast<std::uint8_t>(1U << i);
    return logical;
}
inline bool legal_seed(std::uint32_t logical, std::uint32_t sw) {
    if (sw == 0) {
        if (logical == 2)
            return true;
        for (unsigned depth = 0; depth <= 8; ++depth)
            if (logical == ((1U << depth) - 1))
                return true;
        return false;
    }
    return (sw == 0x22 || sw == 0x241) &&
           (logical == 0 || logical == 1 || logical == 2 || logical == 255);
}
inline bool canonical_admitted(const Raw80 &v) {
    std::uint64_t sig{};
    for (unsigned i = 0; i < 8; ++i)
        sig |= std::uint64_t{v[i]} << (8 * i);
    auto exp = (std::uint16_t{v[8]} | (std::uint16_t{v[9]} << 8)) & 0x7fff;
    if (exp == 0)
        return sig == 0;
    if (!(sig >> 63))
        return false;
    if (exp == 0x7fff)
        return sig == 0x8000000000000000ULL || (sig & (1ULL << 62));
    return true;
}
inline void validate_request(const Request &q) {
    auto esp = q.state.registers[4], input = q.state.registers[1], output = q.state.registers[2];
    if (q.state.eip != code_base || esp < memory_base + 16 ||
        esp > memory_base + memory_size - 16 || (q.state.flags & ~(observed_flags | 0x202U)) ||
        (q.state.flags & 0x202U) != 0x202U)
        throw std::runtime_error("Invalid x87 state entry/register flags");
    if (!safe_span(input, input_size, esp) || !safe_span(output, output_size, esp) ||
        overlaps(input, input_size, output, output_size))
        throw std::runtime_error("Invalid raw80 input/output span or overlap");
    if (!legal_control_word(q.cw))
        throw std::runtime_error("Unmasked or unsupported x87 control word");
    if (q.initial_top > 7 || q.physical_ftw > 255 || q.reserved || q.pattern_id > 1 ||
        !legal_seed(logical_occupancy(q.initial_top, q.physical_ftw), q.initial_sw))
        throw std::runtime_error("Unadmitted TOP/physical occupancy/sticky seed");
    for (const auto &v : q.logical_slots)
        if (!canonical_admitted(v))
            throw std::runtime_error("Unadmitted raw80 encoding");
    if (!canonical_admitted(q.input_raw80) || q.logical_slots != patterns[q.pattern_id] ||
        q.input_raw80 != input_patterns[q.pattern_id])
        throw std::runtime_error("Raw80 values differ from authored admitted patterns");
}
inline std::vector<Request> read_requests(std::istream &stream) {
    auto h = input_header(stream);
    std::vector<Request> requests;
    requests.reserve(h.count);
    std::set<std::tuple<std::uint32_t, std::uint32_t, std::uint32_t, std::uint32_t, std::uint32_t>>
        seen;
    for (std::uint32_t i = 0; i < h.count; ++i) {
        auto q = read_record<Request>(stream);
        validate_request(q);
        if (!seen.emplace(q.cw, q.initial_top, q.physical_ftw, q.initial_sw, q.pattern_id).second)
            throw std::runtime_error("Duplicate x87 state semantic request");
        requests.push_back(q);
    }
    require_end(stream);
    return requests;
}
inline std::array<std::uint8_t, memory_size> initial_memory(const Request &q) {
    std::array<std::uint8_t, memory_size> b{};
    for (std::size_t i = 0; i < b.size(); ++i)
        b[i] = static_cast<std::uint8_t>(i * 37 + q.memory_seed);
    const std::array<std::uint32_t, 3> frame{return_sentinel, q.cw, q.memory_seed};
    std::memcpy(b.data() + q.state.registers[4] - memory_base, frame.data(), 12);
    std::memcpy(b.data() + q.state.registers[1] - memory_base, q.input_raw80.data(), 10);
    return b;
}
} // namespace mw34::x87_state
