#pragma once

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#ifndef NOMINMAX
#define NOMINMAX
#endif
// BCrypt declarations require the Windows types first.
// clang-format off
#include <windows.h>
#include <bcrypt.h>
// clang-format on

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <span>
#include <stdexcept>
#include <string>

namespace mw34::experiment {
constexpr std::uint32_t code_base = 0x10000000;
constexpr std::uint32_t return_sentinel = code_base + 0x100;
constexpr std::uint32_t helper_entry = 0x00409ed0;
constexpr std::uint32_t helper_page = 0x00409000;
// Windows reservations use 64 KiB granularity; only helper_page is committed.
constexpr std::uint32_t helper_reservation = 0x00400000;
constexpr std::uint32_t stack_reservation = 0x20000000;
constexpr std::uint32_t memory_base = stack_reservation + 0x1000;
constexpr std::size_t memory_size = 4096;
constexpr std::uint32_t arithmetic_flags = 0x8d5;
constexpr std::uint32_t observed_flags = arithmetic_flags | 0x400;
enum class FixtureKind { add = 0, branch = 1, memory = 2, shift = 3, mw3_helper = 4 };
#ifndef MW34_FIXTURE_KIND
#define MW34_FIXTURE_KIND 0
#endif
constexpr auto compiled_fixture = static_cast<FixtureKind>(MW34_FIXTURE_KIND);
inline std::uint32_t entry_address(FixtureKind kind) {
    return kind == FixtureKind::mw3_helper ? helper_entry : code_base;
}
constexpr std::array<std::uint8_t, 9> add_bytes{0x8b, 0x44, 0x24, 0x04, 0x03,
                                                0x44, 0x24, 0x08, 0xc3};
constexpr std::array<std::uint8_t, 22> branch_bytes{0x8b, 0x44, 0x24, 0x04, 0x3b, 0x44, 0x24, 0x08,
                                                    0x7d, 0x07, 0x8b, 0x44, 0x24, 0x08, 0xb1, 0x11,
                                                    0xc3, 0x66, 0xb9, 0x33, 0x22, 0xc3};
constexpr std::array<std::uint8_t, 23> memory_bytes{0x8b, 0x44, 0x24, 0x04, 0x8b, 0x4c, 0x24, 0x08,
                                                    0x03, 0x08, 0x89, 0x08, 0x8b, 0x50, 0x04, 0x89,
                                                    0x50, 0x08, 0x89, 0xc8, 0xc2, 0x08, 0x00};
constexpr std::array<std::uint8_t, 12> shift_bytes{0x8b, 0x44, 0x24, 0x04, 0xc1, 0xe0,
                                                   0x05, 0x2b, 0x44, 0x24, 0x08, 0xc3};

inline bool matches_helper(std::span<const std::uint8_t> code) {
    if (code.size() != 22)
        return false;
    // Identity only. The copyrighted machine-code slice comes from the user's
    // private extraction and is never embedded in a public worker or fixture.
    constexpr std::array<std::uint8_t, 32> expected{0x56, 0x0c, 0x17, 0xc2, 0x10, 0xdd, 0x7f, 0xed,
                                                    0xd7, 0xde, 0x60, 0x1f, 0x42, 0x57, 0x0c, 0x2a,
                                                    0x04, 0x73, 0xfa, 0x71, 0x96, 0x2c, 0x13, 0xcf,
                                                    0xa8, 0x5a, 0x00, 0x55, 0x09, 0xa7, 0x7c, 0x65};
    struct HashHandles {
        BCRYPT_ALG_HANDLE algorithm{};
        BCRYPT_HASH_HANDLE hash{};
        ~HashHandles() {
            if (hash)
                BCryptDestroyHash(hash);
            if (algorithm)
                BCryptCloseAlgorithmProvider(algorithm, 0);
        }
    } handles;
    std::array<std::uint8_t, 32> actual{};
    if (BCryptOpenAlgorithmProvider(&handles.algorithm, BCRYPT_SHA256_ALGORITHM, nullptr, 0) < 0 ||
        BCryptCreateHash(handles.algorithm, &handles.hash, nullptr, 0, nullptr, 0, 0) < 0 ||
        BCryptHashData(handles.hash, const_cast<PUCHAR>(code.data()),
                       static_cast<ULONG>(code.size()), 0) < 0 ||
        BCryptFinishHash(handles.hash, actual.data(), static_cast<ULONG>(actual.size()), 0) < 0) {
        throw std::runtime_error("SHA256 helper identity admission failed");
    }
    return actual == expected;
}
inline std::span<const std::uint8_t> fixture_code(FixtureKind kind) {
    switch (kind) {
    case FixtureKind::add:
        return add_bytes;
    case FixtureKind::branch:
        return branch_bytes;
    case FixtureKind::memory:
        return memory_bytes;
    case FixtureKind::shift:
        return shift_bytes;
    case FixtureKind::mw3_helper:
        throw std::runtime_error("Private helper code must be supplied by file");
    }
    throw std::runtime_error("Unknown authored fixture kind");
}
inline bool matches_fixture(std::span<const std::uint8_t> code, FixtureKind kind) {
    if (kind == FixtureKind::mw3_helper)
        return matches_helper(code);
    const auto expected = fixture_code(kind);
    return code.size() == expected.size() && std::equal(code.begin(), code.end(), expected.begin());
}
inline FixtureKind identify_fixture(std::span<const std::uint8_t> code) {
    for (auto kind : {FixtureKind::add, FixtureKind::branch, FixtureKind::memory,
                      FixtureKind::shift, FixtureKind::mw3_helper}) {
        if (matches_fixture(code, kind))
            return kind;
    }
    throw std::runtime_error(
        "Code does not match any reviewed fixture identity or admitted private helper");
}

// Register order is EAX, ECX, EDX, EBX, ESP, EBP, ESI, EDI.
// This fixed, little-endian format is for Windows x86/x64 experiment workers.
struct CpuState {
    std::uint32_t registers[8];
    std::uint32_t flags;
    std::uint32_t eip;
};
struct Request {
    CpuState state;
    std::uint32_t a;
    std::uint32_t b;
    std::uint32_t memory_seed;
};
struct Result {
    CpuState state;
    std::uint32_t status; // 0 returned, 1 fault, 2 unsupported/harness failure.
    std::array<std::uint8_t, memory_size> memory;
};
struct Header {
    char magic[8];
    std::uint32_t version;
    std::uint32_t count;
    std::uint32_t record_size;
    std::uint32_t pointer_bits;
};
static_assert(sizeof(CpuState) == 40 && offsetof(CpuState, flags) == 32);
static_assert(sizeof(Request) == 52 && sizeof(Result) == 4140 && sizeof(Header) == 24);

template <class T> T read_record(std::istream &input) {
    T value{};
    if (!input.read(reinterpret_cast<char *>(&value), sizeof(value))) {
        throw std::runtime_error("Truncated experiment input");
    }
    return value;
}
template <class T> void write_record(std::ostream &output, const T &value) {
    if (!output.write(reinterpret_cast<const char *>(&value), sizeof(value))) {
        throw std::runtime_error("Failed writing experiment output");
    }
}
inline void validate_request(const Request &request, FixtureKind kind = FixtureKind::add) {
    const auto esp = request.state.registers[4];
    if (request.state.eip != entry_address(kind) || esp < memory_base + 16 ||
        esp > memory_base + memory_size - 16 ||
        (request.state.flags & ~(observed_flags | 0x202U)) != 0 ||
        (request.state.flags & 0x202U) != 0x202U) {
        throw std::runtime_error("Invalid entry state or unsafe flags");
    }
    if (kind == FixtureKind::memory) {
        const std::uint64_t start = request.a;
        const auto end = start + 12;
        if (start < memory_base || end > memory_base + memory_size ||
            (start < std::uint64_t{esp} + 12 && end > esp)) {
            throw std::runtime_error("Invalid buffer extent or overlap with return frame");
        }
    }
}
inline std::array<std::uint8_t, memory_size> initial_memory(const Request &request,
                                                            FixtureKind kind = FixtureKind::add) {
    validate_request(request, kind);
    std::array<std::uint8_t, memory_size> bytes{};
    for (std::size_t i = 0; i < bytes.size(); ++i) {
        bytes[i] = static_cast<std::uint8_t>((i * 37 + request.memory_seed) & 0xff);
    }
    const std::array<std::uint32_t, 3> frame{return_sentinel, request.a, request.b};
    std::memcpy(bytes.data() + (request.state.registers[4] - memory_base), frame.data(),
                sizeof(frame));
    if (kind == FixtureKind::memory) {
        // EDX supplies initialized buffer[0], ESI supplies buffer[1]. The third
        // word retains the page pattern until the original/lifted code writes it.
        const std::array<std::uint32_t, 2> data{request.state.registers[2],
                                                request.state.registers[6]};
        std::memcpy(bytes.data() + (request.a - memory_base), data.data(), sizeof(data));
    }
    return bytes;
}
inline Header input_header(std::istream &input) {
    auto header = read_record<Header>(input);
    if (std::memcmp(header.magic, "MW34REQ1", 8) || header.version != 1 ||
        header.record_size != sizeof(Request) || header.pointer_bits != 32 || header.count == 0 ||
        header.count > 100000) {
        throw std::runtime_error("Unsupported experiment header");
    }
    return header;
}
inline Header output_header(std::uint32_t count) {
    Header header{};
    std::memcpy(header.magic, "MW34RES1", 8);
    header.version = 1;
    header.count = count;
    header.record_size = sizeof(Result);
    header.pointer_bits = sizeof(void *) * 8;
    return header;
}
inline void require_end(std::istream &input) {
    if (input.peek() != std::char_traits<char>::eof()) {
        throw std::runtime_error("Unexpected trailing input");
    }
}
} // namespace mw34::experiment
