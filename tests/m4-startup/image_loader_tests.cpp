#include "image_loader.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

constexpr std::uint32_t base = 0x400000;
constexpr std::size_t optional = 0x98;
constexpr std::size_t text_section = 0x178;
constexpr std::size_t data_section = text_section + 40;
using Bytes = std::vector<std::byte>;
std::uint32_t checks{};

void require(bool condition, const char *message) {
    ++checks;
    if (!condition) {
        throw std::runtime_error(message);
    }
}

void put16(Bytes &bytes, std::size_t offset, std::uint16_t value) {
    bytes.at(offset) = static_cast<std::byte>(value & 0xffU);
    bytes.at(offset + 1) = static_cast<std::byte>(value >> 8U);
}

void put32(Bytes &bytes, std::size_t offset, std::uint32_t value) {
    for (std::uint32_t index = 0; index < 4; ++index) {
        bytes.at(offset + index) = static_cast<std::byte>((value >> (index * 8U)) & 0xffU);
    }
}

void put_string(Bytes &bytes, std::size_t offset, std::string_view value) {
    for (const char character : value) {
        bytes.at(offset++) = static_cast<std::byte>(static_cast<unsigned char>(character));
    }
    bytes.at(offset) = std::byte{};
}

std::size_t idata_offset(std::uint32_t rva) { return 0x400U + rva - 0x3000U; }

Bytes fixture() {
    Bytes bytes(0x600);
    put16(bytes, 0, 0x5a4d);
    put32(bytes, 0x3c, 0x80);
    put32(bytes, 0x80, 0x4550);
    put16(bytes, 0x84, 0x14c);
    put16(bytes, 0x86, 2);
    put16(bytes, 0x94, 224);
    put16(bytes, 0x96, 0x103);
    put16(bytes, optional, 0x10b);
    put32(bytes, optional + 16, 0x1000);
    put32(bytes, optional + 28, base);
    put32(bytes, optional + 32, 0x1000);
    put32(bytes, optional + 36, 0x200);
    put32(bytes, optional + 56, 0x4000);
    put32(bytes, optional + 60, 0x200);
    put16(bytes, optional + 68, 2);
    put32(bytes, optional + 92, 16);
    put32(bytes, optional + 104, 0x3000);
    put32(bytes, optional + 108, 40);
    put32(bytes, optional + 192, 0x3060);
    put32(bytes, optional + 196, 12);
    put_string(bytes, text_section, ".text");
    put32(bytes, text_section + 8, 0x20);
    put32(bytes, text_section + 12, 0x1000);
    put32(bytes, text_section + 16, 0x200);
    put32(bytes, text_section + 20, 0x200);
    put32(bytes, text_section + 36, 0x60000020);
    put_string(bytes, data_section, ".idata");
    put32(bytes, data_section + 8, 0x300);
    put32(bytes, data_section + 12, 0x3000);
    put32(bytes, data_section + 16, 0x200);
    put32(bytes, data_section + 20, 0x400);
    put32(bytes, data_section + 36, 0x40000040);
    for (std::size_t index = 0; index < 0x200; ++index) {
        bytes[0x200 + index] = static_cast<std::byte>((index * 37U + 0x90U) & 0xffU);
    }
    put32(bytes, idata_offset(0x3000), 0x3040);
    put32(bytes, idata_offset(0x300c), 0x3080);
    put32(bytes, idata_offset(0x3010), 0x3060);
    put32(bytes, idata_offset(0x3040), 0x30a0);
    put32(bytes, idata_offset(0x3044), 0x80000007);
    put32(bytes, idata_offset(0x3060), 0x30a0);
    put32(bytes, idata_offset(0x3064), 0x80000007);
    put_string(bytes, idata_offset(0x3080), "SYNTHETIC.dll");
    put16(bytes, idata_offset(0x30a0), 0x12);
    put_string(bytes, idata_offset(0x30a2), "AuthorDefinedImport");
    return bytes;
}

void expect_image_error(const char *label, const std::function<void(Bytes &)> &change,
                        const char *expected_text = nullptr) {
    auto bytes = fixture();
    change(bytes);
    try {
        const auto unexpected = mw34::m4::load_pe32(bytes);
        (void)unexpected;
    } catch (const mw34::m4::ImageError &error) {
        if (expected_text && std::string(error.what()).find(expected_text) == std::string::npos) {
            throw std::runtime_error(std::string(label) + ": wrong rejection: " + error.what());
        }
        ++checks;
        return;
    }
    throw std::runtime_error(std::string(label) + ": expected ImageError");
}

template <typename Action>
void expect_fault(mw34::MemoryFaultReason expected, Action action) {
    try {
        action();
    } catch (const mw34::MemoryFault &fault) {
        require(fault.reason() == expected, "Wrong mapped-memory fault reason");
        return;
    }
    throw std::runtime_error("Expected mapped-memory access failure");
}

void valid_mapping() {
    auto bytes = fixture();
    auto loaded = mw34::m4::load_pe32(bytes);
    const auto &metadata = loaded.metadata;
    require(metadata.image_base == base && metadata.image_size == 0x4000,
            "Preferred guest image base and extent");
    require(metadata.entry_point.value == base + 0x1000, "Entry guest address");
    require(metadata.sections.size() == 2 && metadata.mapped_regions.size() == 3,
            "Header and rounded sections are separate mappings");
    require(metadata.sections[0].mapped_size == 4096 &&
            metadata.sections[1].mapped_size == 4096, "Section page rounding");
    std::array<std::byte, 0x200> header{};
    loaded.memory.read({base}, header);
    require(std::equal(header.begin(), header.end(), bytes.begin()), "Mapped header bytes");
    std::array<std::byte, 0x200> text{};
    loaded.memory.read({base + 0x1000}, text);
    require(std::equal(text.begin(), text.end(), bytes.begin() + 0x200),
            "Raw section data includes file padding beyond VirtualSize");
    require(loaded.memory.load<std::uint8_t>({base + 0x11ff}) ==
            std::to_integer<std::uint8_t>(bytes[0x3ff]), "Last raw padded byte");
    require(loaded.memory.load<std::uint8_t>({base + 0x1200}) == 0,
            "Section page padding starts zero");
    require(loaded.memory.load<std::uint8_t>({base + 0x3200}) == 0 &&
            loaded.memory.load<std::uint8_t>({base + 0x32ff}) == 0,
            "Uninitialized virtual section tail is zero");
    require(loaded.memory.load<std::uint8_t>({base + 0x33ff}) == 0 &&
            loaded.memory.load<std::uint8_t>({base + 0x3fff}) == 0,
            "Tail page padding is zero");
    require(loaded.memory.load<std::uint8_t>({base + 0x200}) == 0 &&
            loaded.memory.load<std::uint8_t>({base + 0xfff}) == 0,
            "Header page padding is zero");
    expect_fault(mw34::MemoryFaultReason::unmapped, [&] {
        (void)loaded.memory.load<std::uint8_t>({base + 0x2000});
    });
    expect_fault(mw34::MemoryFaultReason::unmapped, [&] {
        (void)loaded.memory.load<std::uint8_t>({base + 0x4000});
    });
    expect_fault(mw34::MemoryFaultReason::unmapped, [&] {
        (void)loaded.memory.load<std::uint32_t>({base + 0x1ffe});
    });
    expect_fault(mw34::MemoryFaultReason::address_overflow, [&] {
        (void)loaded.memory.load<std::uint32_t>({0xfffffffeU});
    });
    for (const auto address : {base, base + 0x1000, base + 0x3060}) {
        expect_fault(mw34::MemoryFaultReason::permission_denied, [&] {
            loaded.memory.store<std::uint32_t>({address}, 0xfeedface);
        });
    }
    require(metadata.imports.size() == 2 && metadata.import_library_count == 1,
            "Actual unresolved import count");
    const auto &named = metadata.imports[0];
    require(named.library == "SYNTHETIC.dll" && named.name == "AuthorDefinedImport" &&
            !named.ordinal && named.hint == 0x12 && named.lookup_rva == 0x3040 &&
            named.iat_rva == 0x3060 && named.original_iat_value == 0x30a0,
            "Named unresolved import metadata");
    const auto &ordinal = metadata.imports[1];
    require(!ordinal.name && ordinal.ordinal == 7 && ordinal.original_iat_value == 0x80000007,
            "Ordinal unresolved import metadata");
    require(named.iat_permissions == mw34::Permissions::read,
            "Read-only IAT retained without a routing write");
    require(loaded.memory.load<std::uint32_t>({base + 0x3060}) == 0x30a0 &&
            loaded.memory.load<std::uint32_t>({base + 0x3064}) == 0x80000007,
            "No host pointer or fake success is written to the IAT");
    bytes.assign(bytes.size(), std::byte{0xff});
    require(loaded.memory.load<std::uint16_t>({base}) == 0x5a4d,
            "Mapped bytes own storage independently of input lifetime");
}

void valid_variants() {
    auto bytes = fixture();
    put32(bytes, data_section + 36, 0xc0000040);
    auto writable = mw34::m4::load_pe32(bytes);
    writable.memory.store<std::uint32_t>({base + 0x3200}, 0x12345678);
    require(writable.memory.load<std::uint32_t>({base + 0x3200}) == 0x12345678,
            "Declared writable zero tail permits data writes");
    put32(bytes, idata_offset(0x3000), 0);
    auto fallback = mw34::m4::load_pe32(bytes);
    require(fallback.metadata.imports[0].lookup_rva == 0x3060,
            "Zero OriginalFirstThunk uses the unresolved IAT as lookup");
    put32(bytes, idata_offset(0x3000), 0x3060);
    const auto identical = mw34::m4::load_pe32(bytes);
    require(identical.metadata.imports.size() == 2,
            "Explicit identical lookup/IAT table admitted");
    bytes = fixture();
    for (const auto offset : {optional + 104, optional + 108, optional + 192, optional + 196}) {
        put32(bytes, offset, 0);
    }
    auto no_imports = mw34::m4::load_pe32(bytes);
    require(no_imports.metadata.imports.empty(), "Import-free bounded image");
    put32(bytes, data_section + 8, 0x1100);
    put32(bytes, data_section + 16, 0);
    put32(bytes, data_section + 20, 0);
    put32(bytes, optional + 56, 0x5000);
    auto uninitialized = mw34::m4::load_pe32(bytes);
    require(uninitialized.metadata.sections[1].mapped_size == 0x2000 &&
            uninitialized.memory.load<std::uint8_t>({base + 0x4000}) == 0,
            "Entirely uninitialized section has zero owned pages");
    bytes = fixture();
    put32(bytes, optional + 28, 0xffff0000U);
    auto high_base = mw34::m4::load_pe32(bytes);
    require(high_base.metadata.entry_point.value == 0xffff1000U &&
            high_base.memory.load<std::uint16_t>({0xffff0000U}) == 0x5a4d,
            "High guest image base needs no corresponding host mapping");
    bytes = fixture();
    put32(bytes, optional + 112, 0x3100);
    put32(bytes, optional + 116, 0x20);
    const auto resources = mw34::m4::load_pe32(bytes);
    require(resources.metadata.directories[2].size == 0x20,
            "Resource directory span recorded without executing or traversing it");
}

void invalid_headers() {
    expect_image_error("empty", [](Bytes &b) { b.clear(); }, "Truncated");
    expect_image_error("truncated DOS", [](Bytes &b) { b.resize(0x3f); }, "Truncated");
    expect_image_error("MZ", [](Bytes &b) { put16(b, 0, 0); }, "DOS");
    expect_image_error("early PE", [](Bytes &b) { put32(b, 0x3c, 0x20); }, "header offset");
    expect_image_error("overflow PE", [](Bytes &b) { put32(b, 0x3c, UINT32_MAX); }, "Truncated");
    expect_image_error("PE signature", [](Bytes &b) { put32(b, 0x80, 0); }, "signature");
    expect_image_error("x64", [](Bytes &b) { put16(b, 0x84, 0x8664); }, "i386");
    expect_image_error("no sections", [](Bytes &b) { put16(b, 0x86, 0); }, "section count");
    expect_image_error("many sections", [](Bytes &b) { put16(b, 0x86, 97); }, "section count");
    expect_image_error("DLL", [](Bytes &b) { put16(b, 0x96, 0x2103); }, "executable");
    expect_image_error("relocs not stripped", [](Bytes &b) { put16(b, 0x96, 0x102); }, "fixed-base");
    expect_image_error("short optional", [](Bytes &b) { put16(b, 0x94, 94); }, "optional header");
    expect_image_error("PE32+", [](Bytes &b) { put16(b, optional, 0x20b); }, "PE32");
    expect_image_error("dynamic base", [](Bytes &b) { put16(b, optional + 70, 0x40); }, "Dynamic-base");
    expect_image_error("unknown subsystem", [](Bytes &b) { put16(b, optional + 68, 1); }, "subsystems");
    expect_image_error("base unaligned", [](Bytes &b) { put32(b, optional + 28, base + 1); }, "image extent");
    expect_image_error("base zero", [](Bytes &b) { put32(b, optional + 28, 0); }, "image extent");
    expect_image_error("base overflow", [](Bytes &b) { put32(b, optional + 28, 0xffff0000U); put32(b, optional + 56, 0x20000); }, "image extent");
    expect_image_error("image limit", [](Bytes &b) { put32(b, optional + 56, 0x10000000); }, "image extent");
    expect_image_error("image zero", [](Bytes &b) { put32(b, optional + 56, 0); }, "image extent");
    expect_image_error("section alignment", [](Bytes &b) { put32(b, optional + 32, 0x800); }, "alignment");
    expect_image_error("odd section alignment", [](Bytes &b) { put32(b, optional + 32, 0x3000); }, "alignment");
    expect_image_error("file alignment", [](Bytes &b) { put32(b, optional + 36, 0x100); }, "alignment");
    expect_image_error("image alignment", [](Bytes &b) { put32(b, optional + 56, 0x4001); }, "alignment");
    expect_image_error("header alignment", [](Bytes &b) { put32(b, optional + 60, 0x201); }, "SizeOfHeaders");
    expect_image_error("headers too large", [](Bytes &b) { put32(b, optional + 60, 0x800); }, "SizeOfHeaders");
    expect_image_error("table too large", [](Bytes &b) { put16(b, 0x86, 4); }, "Section table");
    expect_image_error("directory count", [](Bytes &b) { put32(b, optional + 92, 17); }, "directory table");
    expect_image_error("truncated dirs", [](Bytes &b) { put16(b, 0x94, 96); }, "directory table");
    expect_image_error("incomplete dir", [](Bytes &b) { put32(b, optional + 108, 0); }, "Incomplete");
    for (const auto directory : {0U, 3U, 4U, 5U, 6U, 7U, 8U, 9U, 10U, 11U, 13U, 14U, 15U}) {
        expect_image_error("unsupported directory", [directory](Bytes &b) {
            put32(b, optional + 96 + directory * 8U, 0x3100);
            put32(b, optional + 100 + directory * 8U, 4);
        }, "outside");
    }
}

void invalid_sections() {
    expect_image_error("unaligned VA", [](Bytes &b) { put32(b, data_section + 12, 0x3001); }, "virtual extent");
    expect_image_error("header overlap", [](Bytes &b) { put32(b, text_section + 12, 0); }, "virtual extent");
    expect_image_error("section overlap", [](Bytes &b) { put32(b, data_section + 12, 0x1000); }, "Overlapping page");
    expect_image_error("rounded overlap", [](Bytes &b) { put32(b, text_section + 8, 0x2001); }, "Overlapping page");
    expect_image_error("empty section", [](Bytes &b) { put32(b, text_section + 8, 0); put32(b, text_section + 16, 0); }, "virtual extent");
    expect_image_error("huge virtual tail", [](Bytes &b) { put32(b, data_section + 8, UINT32_MAX); }, "virtual extent");
    expect_image_error("unaligned raw offset", [](Bytes &b) { put32(b, data_section + 20, 0x401); }, "file alignment");
    expect_image_error("unaligned raw size", [](Bytes &b) { put32(b, data_section + 16, 0x201); }, "file alignment");
    expect_image_error("raw overlap", [](Bytes &b) { put32(b, data_section + 20, 0x200); }, "Overlapping section file");
    expect_image_error("raw header overlap", [](Bytes &b) { put32(b, text_section + 20, 0); }, "file alignment");
    expect_image_error("truncated raw", [](Bytes &b) { b.resize(0x5ff); }, "Truncated");
    expect_image_error("raw arithmetic", [](Bytes &b) { put32(b, data_section + 20, 0xfffffe00U); }, "Truncated");
    expect_image_error("writable executable", [](Bytes &b) { put32(b, text_section + 36, 0xe0000020); }, "Writable executable");
    expect_image_error("bad image extent", [](Bytes &b) { put32(b, optional + 56, 0x5000); }, "rounded section");
    expect_image_error("non-ASCII section", [](Bytes &b) { b[text_section] = std::byte{0xff}; }, "section name");
    expect_image_error("entry gap", [](Bytes &b) { put32(b, optional + 16, 0x2000); }, "Entry point");
    expect_image_error("entry data", [](Bytes &b) { put32(b, optional + 16, 0x3000); }, "Entry point");
    expect_image_error("entry zero", [](Bytes &b) { put32(b, optional + 16, 0); }, "Entry point");
    expect_image_error("entry zero tail", [](Bytes &b) { put32(b, text_section + 8, 0x300); put32(b, optional + 16, 0x1200); }, "file backing");
    expect_image_error("entry page padding", [](Bytes &b) { put32(b, optional + 16, 0x1300); }, "Entry point");
}

void invalid_imports() {
    expect_image_error("directory gap", [](Bytes &b) { put32(b, optional + 104, 0x2000); }, "readable");
    expect_image_error("directory zero tail", [](Bytes &b) { put32(b, optional + 104, 0x3200); }, "file backing");
    expect_image_error("directory spans raw boundary", [](Bytes &b) { put32(b, optional + 104, 0x31fc); }, "file backing");
    expect_image_error("directory overflow", [](Bytes &b) { put32(b, optional + 104, 0xfffffffcU); }, "exceeds");
    expect_image_error("directory unaligned", [](Bytes &b) { put32(b, optional + 104, 0x3001); }, "aligned");
    expect_image_error("descriptor size", [](Bytes &b) { put32(b, optional + 108, 39); }, "descriptor directory extent");
    expect_image_error("descriptor no terminator", [](Bytes &b) { put32(b, optional + 108, 20); }, "Unterminated import descriptor");
    expect_image_error("hidden after terminator", [](Bytes &b) { put32(b, optional + 108, 60); put32(b, idata_offset(0x3028), 0x1234); }, "follows its terminator");
    expect_image_error("missing DLL", [](Bytes &b) { put32(b, idata_offset(0x300c), 0); }, "descriptor name");
    expect_image_error("missing IAT", [](Bytes &b) { put32(b, idata_offset(0x3010), 0); }, "descriptor name");
    expect_image_error("bound timestamp", [](Bytes &b) { put32(b, idata_offset(0x3004), 1); }, "Bound");
    expect_image_error("forwarder chain", [](Bytes &b) { put32(b, idata_offset(0x3008), 1); }, "forwarded");
    expect_image_error("empty DLL", [](Bytes &b) { b[idata_offset(0x3080)] = std::byte{}; }, "Empty");
    expect_image_error("DLL path", [](Bytes &b) { put_string(b, idata_offset(0x3080), "a/b.dll"); }, "basename");
    expect_image_error("DLL non-ASCII", [](Bytes &b) { b[idata_offset(0x3080)] = std::byte{0xff}; }, "ASCII");
    expect_image_error("unterminated name", [](Bytes &b) { put32(b, idata_offset(0x300c), 0x31fc); std::fill(b.begin() + 0x5fc, b.end(), std::byte{'A'}); }, "file backing");
    expect_image_error("lookup unaligned", [](Bytes &b) { put32(b, idata_offset(0x3000), 0x3041); }, "alignment");
    expect_image_error("IAT unaligned", [](Bytes &b) { put32(b, idata_offset(0x3010), 0x3061); }, "alignment");
    expect_image_error("lookup overflow", [](Bytes &b) { put32(b, idata_offset(0x3000), 0xfffffffcU); }, "exceeds");
    expect_image_error("IAT zero tail", [](Bytes &b) { put32(b, idata_offset(0x3010), 0x3200); }, "file backing");
    expect_image_error("IAT divergent", [](Bytes &b) { put32(b, idata_offset(0x3060), 0x12345678); }, "divergent");
    expect_image_error("IAT nonzero terminator", [](Bytes &b) { put32(b, idata_offset(0x3068), 0x12345678); }, "divergent");
    expect_image_error("IAT outside directory", [](Bytes &b) { put32(b, optional + 196, 8); }, "declared IAT");
    expect_image_error("IAT fractional slots", [](Bytes &b) { put32(b, optional + 196, 11); }, "whole DWORD");
    expect_image_error("ordinal reserved bits", [](Bytes &b) { put32(b, idata_offset(0x3044), 0x80010007); put32(b, idata_offset(0x3064), 0x80010007); }, "ordinal");
    expect_image_error("ordinal zero", [](Bytes &b) { put32(b, idata_offset(0x3044), 0x80000000); put32(b, idata_offset(0x3064), 0x80000000); }, "ordinal");
    expect_image_error("name zero tail", [](Bytes &b) { put32(b, idata_offset(0x3040), 0x3200); put32(b, idata_offset(0x3060), 0x3200); }, "file backing");
    expect_image_error("empty symbol", [](Bytes &b) { b[idata_offset(0x30a2)] = std::byte{}; }, "Empty");
    expect_image_error("no imports with IAT", [](Bytes &b) { put32(b, optional + 104, 0); put32(b, optional + 108, 0); }, "without import");
    expect_image_error("IAT executable", [](Bytes &b) {
        put32(b, optional + 192, 0);
        put32(b, optional + 196, 0);
        put32(b, idata_offset(0x3010), 0x1100);
        put32(b, 0x300, 0x30a0); put32(b, 0x304, 0x80000007); put32(b, 0x308, 0);
    }, "nonexecutable");
    expect_image_error("IAT header", [](Bytes &b) {
        put32(b, optional + 192, 0); put32(b, optional + 196, 0);
        put32(b, idata_offset(0x3010), 0x40);
        put32(b, 0x40, 0x30a0); put32(b, 0x44, 0x80000007); put32(b, 0x48, 0);
    }, "nonexecutable");
    expect_image_error("IAT name alias", [](Bytes &b) {
        put32(b, optional + 192, 0); put32(b, optional + 196, 0);
        put32(b, idata_offset(0x3000), 0x3080); put32(b, idata_offset(0x3010), 0x3080);
        put32(b, idata_offset(0x3080), 0x80002121); put32(b, idata_offset(0x3084), 0);
    }, "aliases");
    expect_image_error("duplicate IAT tables", [](Bytes &b) {
        put32(b, optional + 108, 60);
        put32(b, idata_offset(0x3014), 0x3040);
        put32(b, idata_offset(0x3020), 0x3080);
        put32(b, idata_offset(0x3024), 0x3060);
    }, "Overlapping import IAT");
    expect_image_error("distinct lookup overlap", [](Bytes &b) {
        put32(b, optional + 192, 0); put32(b, optional + 196, 0);
        put32(b, optional + 108, 60);
        put32(b, idata_offset(0x3014), 0x3060);
        put32(b, idata_offset(0x3020), 0x3080);
        put32(b, idata_offset(0x3024), 0x3040);
    }, "distinct import lookup");
}

void configured_limits_and_staging() {
    const auto bytes = fixture();
    for (const auto setting : {0U, 1U, 2U, 3U, 4U, 5U, 6U}) {
        auto limits = mw34::m4::ImageLimits{};
        switch (setting) {
        case 0: limits.max_file_bytes = bytes.size() - 1; break;
        case 1: limits.max_image_bytes = 0x3000; break;
        case 2: limits.max_sections = 1; break;
        case 3: limits.max_import_symbols = 1; break;
        case 4: limits.max_name_bytes = 3; break;
        case 5: limits.max_name_bytes = 0; break;
        case 6: limits.max_import_symbols = UINT32_MAX; break;
        }
        bool rejected = false;
        try {
            const auto unexpected = mw34::m4::load_pe32(bytes, limits);
            (void)unexpected;
        } catch (const mw34::m4::ImageError &) {
            rejected = true;
        }
        require(rejected, "Configured admission limit is enforced");
    }
    auto valid = mw34::m4::load_pe32(bytes);
    auto invalid = fixture();
    put32(invalid, idata_offset(0x3060), 0xfacefeed);
    bool rejected = false;
    try {
        // Assignment publishes only a fully validated return object.
        valid = mw34::m4::load_pe32(invalid);
    } catch (const mw34::m4::ImageError &) {
        rejected = true;
    }
    require(rejected && valid.memory.load<std::uint32_t>({base + 0x3060}) == 0x30a0,
            "Late malformed import does not publish or corrupt previous mapping");
}

} // namespace

int main() {
    try {
        valid_mapping();
        valid_variants();
        invalid_headers();
        invalid_sections();
        invalid_imports();
        configured_limits_and_staging();
        std::cout << "{\"passed\":true,\"checks\":" << checks
                  << ",\"original_code_executed\":false,\"fixture\":\"authored PE32\"}\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "M4 loader tests failed: " << error.what() << '\n';
        return 1;
    }
}
