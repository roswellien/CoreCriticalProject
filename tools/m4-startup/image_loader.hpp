#pragma once

#include "memory/guest_memory.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <span>
#include <stdexcept>
#include <string>
#include <vector>

namespace mw34::m4 {

class ImageError : public std::runtime_error {
  public:
    using std::runtime_error::runtime_error;
};

struct ImageLimits {
    std::uint64_t max_file_bytes = 64U * 1024U * 1024U;
    std::uint64_t max_image_bytes = 128U * 1024U * 1024U;
    std::uint32_t max_sections = 96;
    std::uint32_t max_import_descriptors = 256;
    std::uint32_t max_import_symbols = 8192;
    std::uint32_t max_name_bytes = 4096;
};

struct DataDirectory {
    std::uint32_t rva{};
    std::uint32_t size{};
};

struct ImageRegion {
    std::string name;
    GuestAddress start;
    std::uint32_t size{};
    Permissions permissions = Permissions::none;
};

struct ImageSection {
    std::string name;
    std::uint32_t virtual_address{};
    std::uint32_t virtual_size{};
    std::uint32_t raw_offset{};
    std::uint32_t raw_size{};
    std::uint32_t mapped_size{};
    std::uint32_t characteristics{};
    Permissions permissions = Permissions::none;
};

struct ImportSymbol {
    std::string library;
    std::optional<std::string> name;
    std::optional<std::uint16_t> ordinal;
    std::uint16_t hint{};
    std::uint32_t lookup_rva{};
    std::uint32_t iat_rva{};
    std::uint32_t original_iat_value{};
    Permissions iat_permissions = Permissions::none;
};

struct ImageMetadata {
    std::uint32_t image_base{};
    std::uint32_t image_size{};
    std::uint32_t size_of_headers{};
    std::uint32_t entry_point_rva{};
    GuestAddress entry_point;
    std::uint32_t section_alignment{};
    std::uint32_t file_alignment{};
    std::uint16_t subsystem{};
    std::uint16_t characteristics{};
    std::uint16_t dll_characteristics{};
    std::array<DataDirectory, 16> directories{};
    std::vector<ImageSection> sections;
    std::vector<ImageRegion> mapped_regions;
    std::vector<ImportSymbol> imports;
    std::uint32_t import_library_count{};
};

struct LoadedImage {
    ImageMetadata metadata;
    GuestMemory memory;
};

// This loads data into owned GuestMemory only. No original x86 bytes are run,
// no host address is reserved, and no import is resolved or replaced.
// All structural and import checks finish before any mapping is published in
// the returned object. Structural rejection throws ImageError without changing
// other memory; allocation failures likewise cannot publish a partial image.
[[nodiscard]] LoadedImage load_pe32(std::span<const std::byte> file,
                                   const ImageLimits &limits = {});

} // namespace mw34::m4
