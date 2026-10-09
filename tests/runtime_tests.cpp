#include "memory/guest_memory.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <exception>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const char *message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

template <typename Action> void expect_invalid(Action action) {
    try {
        action();
    } catch (const std::invalid_argument &) {
        return;
    }
    throw std::runtime_error("Expected invalid_argument");
}

template <typename Action> void expect_fault(mw34::MemoryFaultReason reason, Action action) {
    try {
        action();
    } catch (const mw34::MemoryFault &fault) {
        require(fault.reason() == reason, "Wrong memory fault reason");
        return;
    }
    throw std::runtime_error("Expected MemoryFault");
}

void test_scalars() {
    mw34::GuestMemory memory;
    constexpr auto rw = mw34::Permissions::read | mw34::Permissions::write;
    memory.map({0x1000}, 32, rw);
    require(memory.load<std::uint32_t>({0x1000}) == 0, "Mappings must start zeroed");

    // A deliberately unaligned scalar must have the same byte order on every host.
    memory.store<std::uint32_t>({0x1001}, 0x12345678);
    std::array<std::byte, 4> bytes{};
    memory.read({0x1001}, bytes);
    require(bytes == std::array{std::byte{0x78}, std::byte{0x56}, std::byte{0x34}, std::byte{0x12}},
            "Stores must encode little-endian bytes");
    require(memory.load<std::uint16_t>({0x1002}) == 0x3456, "Unaligned word decode");
    require(memory.load<std::uint8_t>({0x1004}) == 0x12, "Byte decode");

    memory.store<std::uint64_t>({0x1007}, 0xfedcba9876543210ULL);
    require(memory.load<std::uint64_t>({0x1007}) == 0xfedcba9876543210ULL,
            "Unaligned 64-bit decode");
    const std::array source{std::byte{0xff}, std::byte{0x80}};
    memory.write({0x101e}, source);
    require(memory.load<std::uint16_t>({0x101e}) == 0x80ff, "Final bytes in region");
}

void test_bounds() {
    mw34::GuestMemory memory;
    constexpr auto rw = mw34::Permissions::read | mw34::Permissions::write;
    memory.map({0xfffffffc}, 4, rw);
    memory.store<std::uint32_t>({0xfffffffc}, 0x12345678);
    require(memory.load<std::uint8_t>({0xffffffff}) == 0x12, "Top guest byte must be accessible");
    expect_fault(mw34::MemoryFaultReason::address_overflow,
                 [&] { memory.store<std::uint16_t>({0xffffffff}, 0xffff); });
    require(memory.load<std::uint32_t>({0xfffffffc}) == 0x12345678,
            "Overflowing store must not partially write");

    memory.map({0x1000}, 4, rw);
    memory.map({0x1004}, 4, rw);
    memory.store<std::uint32_t>({0x1000}, 0x11223344);
    expect_fault(mw34::MemoryFaultReason::unmapped,
                 [&] { memory.store<std::uint32_t>({0x1002}, 0xffffffff); });
    require(memory.load<std::uint32_t>({0x1000}) == 0x11223344,
            "Cross-region store must not partially write");
    expect_fault(mw34::MemoryFaultReason::unmapped,
                 [&] { (void)memory.load<std::uint8_t>({0x1008}); });
    expect_fault(mw34::MemoryFaultReason::unmapped,
                 [&] { (void)memory.load<std::uint8_t>({0xfff}); });
    expect_fault(mw34::MemoryFaultReason::unmapped, [&] { (void)memory.load<std::uint8_t>({0}); });

    // Empty transfer semantics are explicit, even at an unmapped address.
    memory.read({0}, {});
    memory.write({0xffffffff}, {});
    require(mw34::GuestAddress{0xffffffff}.wrapping_add(1).value == 0,
            "Guest arithmetic must wrap modulo 2^32");
}

void test_mapping() {
    mw34::GuestMemory memory;
    constexpr auto rw = mw34::Permissions::read | mw34::Permissions::write;
    expect_invalid([&] { memory.map({0x1000}, 0, rw); });
    expect_invalid([&] { memory.map({0xffffffff}, 2, rw); });
    expect_invalid([&] { memory.map({1}, std::numeric_limits<std::uint64_t>::max(), rw); });
    expect_invalid([&] { memory.map({0x1000}, 4, static_cast<mw34::Permissions>(8)); });
    memory.map({0x1000}, 16, rw);
    expect_invalid([&] { memory.map({0x1000}, 16, rw); });
    expect_invalid([&] { memory.map({0x1008}, 16, rw); });
    expect_invalid([&] { memory.map({0xfff}, 2, rw); });
    expect_invalid([&] { memory.map({0xff0}, 48, rw); });
    expect_invalid([&] { memory.unmap({0x1001}); });
    expect_invalid([&] { memory.protect({0x1001}, mw34::Permissions::read); });
    memory.store<std::uint32_t>({0x1000}, 0xffffffff);
    memory.unmap({0x1000});
    expect_fault(mw34::MemoryFaultReason::unmapped,
                 [&] { (void)memory.load<std::uint32_t>({0x1000}); });
    memory.map({0x1000}, 16, rw);
    require(memory.load<std::uint32_t>({0x1000}) == 0,
            "Remapping must allocate fresh zeroed bytes");

    // Address zero is usable only when explicitly mapped by the caller.
    memory.map({0}, 1, rw);
    memory.store<std::uint8_t>({0}, 7);
    require(memory.load<std::uint8_t>({0}) == 7, "Explicit mapping at address zero");
}

void test_permissions() {
    mw34::GuestMemory memory;
    memory.map({0x2000}, 8, mw34::Permissions::write);
    memory.store<std::uint32_t>({0x2000}, 0x12345678);
    expect_fault(mw34::MemoryFaultReason::permission_denied,
                 [&] { (void)memory.load<std::uint32_t>({0x2000}); });
    memory.protect({0x2000}, mw34::Permissions::read | mw34::Permissions::execute);
    require(memory.load<std::uint32_t>({0x2000}) == 0x12345678, "Protect must preserve data");
    expect_fault(mw34::MemoryFaultReason::permission_denied,
                 [&] { memory.store<std::uint32_t>({0x2000}, 0); });
    require(memory.load<std::uint32_t>({0x2000}) == 0x12345678,
            "Denied store must not modify data");
    memory.protect({0x2000}, mw34::Permissions::execute);
    expect_fault(mw34::MemoryFaultReason::permission_denied,
                 [&] { (void)memory.load<std::uint8_t>({0x2000}); });
    memory.protect({0x2000}, mw34::Permissions::none);
    expect_fault(mw34::MemoryFaultReason::permission_denied,
                 [&] { memory.store<std::uint8_t>({0x2000}, 0); });
}

} // namespace

int main() {
    try {
        test_scalars();
        test_bounds();
        test_mapping();
        test_permissions();
        std::cout << "Guest memory tests passed\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "Guest memory tests failed: " << error.what() << '\n';
        return 1;
    } catch (...) {
        std::cerr << "Guest memory tests failed with an unknown exception\n";
        return 1;
    }
}
