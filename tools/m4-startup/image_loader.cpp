#include "image_loader.hpp"

#include <algorithm>
#include <limits>
#include <set>
#include <utility>

namespace mw34::m4 {
namespace {

constexpr std::uint64_t page_size = 4096;
constexpr std::uint32_t execute_flag = 0x20000000U;
constexpr std::uint32_t read_flag = 0x40000000U;
constexpr std::uint32_t write_flag = 0x80000000U;

[[noreturn]] void fail(const char *message) { throw ImageError(message); }

bool has(Permissions permissions, Permissions bit) {
    return (static_cast<std::uint8_t>(permissions) & static_cast<std::uint8_t>(bit)) != 0;
}

std::uint64_t round_up(std::uint64_t value, std::uint64_t alignment) {
    return (value + alignment - 1U) / alignment * alignment;
}

bool power_of_two(std::uint32_t value) { return value && !(value & (value - 1U)); }

struct Range {
    std::uint64_t begin;
    std::uint64_t end;
};

bool overlaps(Range left, Range right) {
    return left.begin < right.end && right.begin < left.end;
}

void add_disjoint(std::vector<Range> &ranges, Range range, const char *message) {
    if (std::any_of(ranges.begin(), ranges.end(), [range](Range other) {
            return overlaps(range, other);
        })) {
        fail(message);
    }
    ranges.push_back(range);
}

class Parser {
  public:
    Parser(std::span<const std::byte> file, const ImageLimits &limits)
        : file_(file), limits_(limits) {}

    ImageMetadata parse() {
        if (!limits_.max_file_bytes || !limits_.max_image_bytes || !limits_.max_sections ||
            !limits_.max_import_descriptors || !limits_.max_import_symbols ||
            !limits_.max_name_bytes) {
            fail("Image limits must be nonzero");
        }
        const ImageLimits hard_limits;
        if (limits_.max_file_bytes > hard_limits.max_file_bytes ||
            limits_.max_image_bytes > hard_limits.max_image_bytes ||
            limits_.max_sections > hard_limits.max_sections ||
            limits_.max_import_descriptors > hard_limits.max_import_descriptors ||
            limits_.max_import_symbols > hard_limits.max_import_symbols ||
            limits_.max_name_bytes > hard_limits.max_name_bytes) {
            fail("Configured limits may tighten but must not expand the bounded subset");
        }
        if (file_.size() > limits_.max_file_bytes) {
            fail("PE file exceeds the configured file limit");
        }
        if (u16(0) != 0x5a4dU) {
            fail("Missing DOS MZ signature");
        }
        const auto pe = std::uint64_t{u32(0x3c)};
        if (pe < 0x40 || u32(pe) != 0x00004550U) {
            fail("Invalid PE signature or header offset");
        }
        const auto coff = pe + 4;
        if (u16(coff) != 0x14cU) {
            fail("Only PE32 i386 images are supported");
        }
        const auto section_count = u16(coff + 2);
        if (!section_count || section_count > limits_.max_sections) {
            fail("Invalid or excessive section count");
        }
        const auto optional_size = u16(coff + 16);
        metadata_.characteristics = u16(coff + 18);
        if (!(metadata_.characteristics & 0x0002U) ||
            !(metadata_.characteristics & 0x0001U) ||
            (metadata_.characteristics & 0x2000U)) {
            fail("Expected a fixed-base executable with relocations stripped");
        }
        const auto optional = coff + 20;
        bytes(optional, optional_size);
        if (optional_size < 96 || u16(optional) != 0x10bU) {
            fail("Expected a complete PE32 optional header");
        }
        metadata_.entry_point_rva = u32(optional + 16);
        metadata_.image_base = u32(optional + 28);
        metadata_.section_alignment = u32(optional + 32);
        metadata_.file_alignment = u32(optional + 36);
        metadata_.image_size = u32(optional + 56);
        metadata_.size_of_headers = u32(optional + 60);
        metadata_.subsystem = u16(optional + 68);
        metadata_.dll_characteristics = u16(optional + 70);
        if (metadata_.dll_characteristics & 0x40U) {
            fail("Dynamic-base images are outside the fixed-base subset");
        }
        if (metadata_.subsystem != 2 && metadata_.subsystem != 3) {
            fail("Only Windows GUI or console executable subsystems are supported");
        }
        if (!metadata_.image_base || metadata_.image_base % 65536U ||
            !metadata_.image_size || metadata_.image_size > limits_.max_image_bytes ||
            std::uint64_t{metadata_.image_base} + metadata_.image_size >
                GuestMemory::address_space_size) {
            fail("Invalid, overflowing, or excessive fixed guest image extent");
        }
        const auto section_alignment = metadata_.section_alignment;
        const auto file_alignment = metadata_.file_alignment;
        if (!power_of_two(section_alignment) || section_alignment < page_size ||
            section_alignment > 65536U || !power_of_two(file_alignment) ||
            file_alignment < 512U || file_alignment > 65536U ||
            file_alignment > section_alignment || metadata_.image_size % section_alignment) {
            fail("Unsupported or inconsistent image alignment");
        }
        const auto header_size = metadata_.size_of_headers;
        if (!header_size || header_size % file_alignment || header_size > file_.size() ||
            header_size > metadata_.image_size) {
            fail("Invalid SizeOfHeaders");
        }
        const auto directory_count = u32(optional + 92);
        if (directory_count > 16 || std::uint64_t{directory_count} * 8U + 96U > optional_size) {
            fail("Invalid or truncated data directory table");
        }
        for (std::uint32_t index = 0; index < directory_count; ++index) {
            auto &directory = metadata_.directories[index];
            directory = {u32(optional + 96 + index * 8U),
                         u32(optional + 100 + index * 8U)};
            if ((directory.rva == 0) != (directory.size == 0)) {
                fail("Incomplete data directory");
            }
            if (directory.rva && index != 1 && index != 2 && index != 12) {
                fail("Nonempty directory is outside the imports/resources/IAT subset");
            }
        }
        const auto section_table = optional + optional_size;
        if (section_table + std::uint64_t{section_count} * 40U > header_size) {
            fail("Section table exceeds SizeOfHeaders");
        }
        const auto mapped_header_size = round_up(header_size, page_size);
        std::vector<Range> raw_ranges{{0, header_size}};
        std::vector<Range> mapped_ranges{{0, mapped_header_size}};
        std::uint64_t maximum_end = mapped_header_size;
        metadata_.mapped_regions.push_back({"headers", {metadata_.image_base},
            static_cast<std::uint32_t>(mapped_header_size), Permissions::read});
        for (std::uint32_t index = 0; index < section_count; ++index) {
            const auto record = section_table + index * 40U;
            ImageSection section;
            for (const auto byte : bytes(record, 8)) {
                const auto character = std::to_integer<unsigned char>(byte);
                if (!character) {
                    break;
                }
                if (character < 0x20 || character > 0x7e) {
                    fail("Non-ASCII section name");
                }
                section.name.push_back(static_cast<char>(character));
            }
            section.virtual_size = u32(record + 8);
            section.virtual_address = u32(record + 12);
            section.raw_size = u32(record + 16);
            section.raw_offset = u32(record + 20);
            section.characteristics = u32(record + 36);
            const auto extent = std::uint64_t{std::max(section.virtual_size, section.raw_size)};
            if (!extent || section.virtual_address % section_alignment ||
                section.virtual_address < mapped_header_size ||
                std::uint64_t{section.virtual_address} + extent > metadata_.image_size) {
                fail("Invalid section virtual extent or alignment");
            }
            if (section.raw_size) {
                if (!section.raw_offset || section.raw_offset % file_alignment ||
                    section.raw_size % file_alignment) {
                    fail("Invalid section file alignment");
                }
                bytes(section.raw_offset, section.raw_size);
                add_disjoint(raw_ranges,
                    {section.raw_offset, std::uint64_t{section.raw_offset} + section.raw_size},
                    "Overlapping section file ranges");
            } else if (section.raw_offset && section.raw_offset % file_alignment) {
                fail("Invalid uninitialized section file offset alignment");
            }
            const auto mapped_size = round_up(extent, page_size);
            const auto end = std::uint64_t{section.virtual_address} + mapped_size;
            if (end > metadata_.image_size || mapped_size > UINT32_MAX) {
                fail("Page-rounded section exceeds SizeOfImage");
            }
            add_disjoint(mapped_ranges, {section.virtual_address, end},
                         "Overlapping page-rounded section mappings");
            maximum_end = std::max(maximum_end, end);
            section.mapped_size = static_cast<std::uint32_t>(mapped_size);
            if (section.characteristics & read_flag) {
                section.permissions = section.permissions | Permissions::read;
            }
            if (section.characteristics & write_flag) {
                section.permissions = section.permissions | Permissions::write;
            }
            if (section.characteristics & execute_flag) {
                section.permissions = section.permissions | Permissions::execute;
            }
            if (has(section.permissions, Permissions::write) &&
                has(section.permissions, Permissions::execute)) {
                fail("Writable executable sections are rejected");
            }
            metadata_.mapped_regions.push_back({section.name,
                {static_cast<std::uint32_t>(metadata_.image_base + section.virtual_address)},
                section.mapped_size, section.permissions});
            metadata_.sections.push_back(std::move(section));
        }
        if (round_up(maximum_end, section_alignment) != metadata_.image_size) {
            fail("SizeOfImage disagrees with the rounded section extent");
        }
        const auto *entry_section = containing_section(metadata_.entry_point_rva, 1);
        if (!metadata_.entry_point_rva || !entry_section ||
            !has(entry_section->permissions, Permissions::execute) ||
            !has(entry_section->permissions, Permissions::read)) {
            fail("Entry point must lie in a readable executable section extent");
        }
        // The entry byte must come from the file, not a zero-fill tail or page padding.
        rva_bytes(metadata_.entry_point_rva, 1);
        metadata_.entry_point = {metadata_.image_base + metadata_.entry_point_rva};
        for (const auto &directory : metadata_.directories) {
            if (directory.rva) {
                if (directory.rva % 4U) {
                    fail("Supported directory RVA must be four-byte aligned");
                }
                rva_bytes(directory.rva, directory.size);
            }
        }
        parse_imports();
        return std::move(metadata_);
    }

  private:
    std::span<const std::byte> bytes(std::uint64_t offset, std::uint64_t size) const {
        if (offset > file_.size() || size > file_.size() - offset) {
            fail("Truncated PE file range");
        }
        return file_.subspan(static_cast<std::size_t>(offset), static_cast<std::size_t>(size));
    }

    std::uint16_t u16(std::uint64_t offset) const {
        const auto data = bytes(offset, 2);
        return static_cast<std::uint16_t>(std::to_integer<std::uint16_t>(data[0]) |
            (std::to_integer<std::uint16_t>(data[1]) << 8U));
    }

    std::uint32_t u32(std::uint64_t offset) const {
        const auto data = bytes(offset, 4);
        std::uint32_t value{};
        for (std::uint32_t index = 0; index != 4; ++index) {
            value |= std::to_integer<std::uint32_t>(data[index]) << (8U * index);
        }
        return value;
    }

    const ImageSection *containing_section(std::uint64_t rva, std::uint64_t size) const {
        for (const auto &section : metadata_.sections) {
            const auto extent = std::uint64_t{std::max(section.virtual_size, section.raw_size)};
            if (rva >= section.virtual_address && rva - section.virtual_address < extent &&
                size <= extent - (rva - section.virtual_address)) {
                return &section;
            }
        }
        return nullptr;
    }

    std::uint64_t file_offset(std::uint64_t rva, std::uint64_t size) const {
        if (!size || rva >= metadata_.image_size || size > metadata_.image_size - rva) {
            fail("Metadata RVA range exceeds the image");
        }
        if (rva < metadata_.size_of_headers && size <= metadata_.size_of_headers - rva) {
            return rva;
        }
        const auto *section = containing_section(rva, size);
        if (!section || !has(section->permissions, Permissions::read)) {
            fail("Metadata RVA is not in a readable section or header");
        }
        const auto delta = rva - section->virtual_address;
        if (delta >= section->raw_size || size > section->raw_size - delta) {
            fail("Metadata RVA has no contiguous file backing");
        }
        return std::uint64_t{section->raw_offset} + delta;
    }

    std::span<const std::byte> rva_bytes(std::uint64_t rva, std::uint64_t size) const {
        return bytes(file_offset(rva, size), size);
    }

    std::uint32_t rva_u32(std::uint64_t rva) const { return u32(file_offset(rva, 4)); }

    std::pair<std::string, Range> string_at(std::uint64_t rva) const {
        std::string value;
        for (std::uint32_t index = 0; index < limits_.max_name_bytes; ++index) {
            // Checking the whole prefix prevents strings from crossing into a
            // second mapping or from treating zero-fill as a terminator.
            const auto prefix = rva_bytes(rva, std::uint64_t{index} + 1U);
            const auto byte = std::to_integer<unsigned char>(prefix.back());
            if (!byte) {
                if (value.empty()) {
                    fail("Empty imported metadata name");
                }
                return {std::move(value), {rva, rva + index + 1U}};
            }
            if (byte < 0x21 || byte > 0x7e) {
                fail("Imported metadata name contains a nonprintable ASCII character");
            }
            value.push_back(static_cast<char>(byte));
        }
        fail("Unterminated or excessive imported metadata name");
    }

    void parse_imports() {
        const auto directory = metadata_.directories[1];
        const auto declared_iat = metadata_.directories[12];
        if (!directory.rva) {
            if (declared_iat.rva) {
                fail("IAT directory exists without import descriptors");
            }
            return;
        }
        if (directory.size < 20 || directory.size % 20U ||
            directory.size / 20U > limits_.max_import_descriptors + std::uint64_t{1}) {
            fail("Invalid or excessive import descriptor directory extent");
        }
        if (declared_iat.rva && declared_iat.size % 4U) {
            fail("IAT directory extent must contain whole DWORD slots");
        }
        std::vector<Range> metadata_ranges{{directory.rva,
            std::uint64_t{directory.rva} + directory.size}};
        std::vector<Range> iat_ranges;
        std::vector<Range> lookup_ranges;
        bool terminated = false;
        for (std::uint32_t descriptor = 0; descriptor < directory.size / 20U; ++descriptor) {
            const auto rva = std::uint64_t{directory.rva} + descriptor * 20U;
            const auto lookup = rva_u32(rva);
            const auto timestamp = rva_u32(rva + 4);
            const auto chain = rva_u32(rva + 8);
            const auto name_rva = rva_u32(rva + 12);
            const auto iat = rva_u32(rva + 16);
            if (!(lookup || timestamp || chain || name_rva || iat)) {
                terminated = true;
                // No hidden descriptors after the sentinel are admitted.
                for (const auto byte : rva_bytes(rva, directory.rva + directory.size - rva)) {
                    if (byte != std::byte{}) {
                        fail("Nonzero import directory data follows its terminator");
                    }
                }
                break;
            }
            if (descriptor >= limits_.max_import_descriptors || !name_rva || !iat ||
                iat % 4U || (lookup && lookup % 4U)) {
                fail("Invalid import descriptor name or thunk alignment");
            }
            if (timestamp || chain) {
                fail("Bound or forwarded import descriptors are unsupported");
            }
            auto [library, library_range] = string_at(name_rva);
            if (library.find_first_of("/\\:") != std::string::npos) {
                fail("Imported library name must be a basename");
            }
            metadata_ranges.push_back(library_range);
            const auto lookup_start = lookup ? lookup : iat;
            bool thunk_terminated = false;
            std::uint64_t table_size = 0;
            for (std::uint32_t index = 0; index <= limits_.max_import_symbols; ++index) {
                const auto lookup_rva = std::uint64_t{lookup_start} + index * 4ULL;
                const auto iat_rva = std::uint64_t{iat} + index * 4ULL;
                const auto value = rva_u32(lookup_rva);
                const auto original_iat_value = rva_u32(iat_rva);
                const auto *iat_section = containing_section(iat_rva, 4);
                if (!iat_section || has(iat_section->permissions, Permissions::execute)) {
                    fail("IAT slot must lie in a readable nonexecutable section");
                }
                if (declared_iat.rva &&
                    (iat_rva < declared_iat.rva || iat_rva + 4U >
                        std::uint64_t{declared_iat.rva} + declared_iat.size)) {
                    fail("Import IAT slot lies outside the declared IAT directory");
                }
                if (original_iat_value != value) {
                    fail("IAT contains bound or divergent values rather than unresolved imports");
                }
                table_size += 4U;
                if (!value) {
                    thunk_terminated = true;
                    break;
                }
                if (metadata_.imports.size() >= limits_.max_import_symbols) {
                    fail("Excessive import symbol count");
                }
                ImportSymbol symbol;
                symbol.library = library;
                symbol.lookup_rva = static_cast<std::uint32_t>(lookup_rva);
                symbol.iat_rva = static_cast<std::uint32_t>(iat_rva);
                symbol.original_iat_value = original_iat_value;
                symbol.iat_permissions = iat_section->permissions;
                if (value & 0x80000000U) {
                    if (value & 0x7fff0000U || !(value & 0xffffU)) {
                        fail("Invalid reserved bits or zero ordinal import");
                    }
                    symbol.ordinal = static_cast<std::uint16_t>(value & 0xffffU);
                } else {
                    symbol.hint = u16(file_offset(value, 2));
                    auto [name, name_range] = string_at(std::uint64_t{value} + 2U);
                    name_range.begin = value;
                    metadata_ranges.push_back(name_range);
                    symbol.name = std::move(name);
                }
                metadata_.imports.push_back(std::move(symbol));
            }
            if (!thunk_terminated) {
                fail("Unterminated import thunk table");
            }
            const Range lookup_range{lookup_start, std::uint64_t{lookup_start} + table_size};
            const Range iat_range{iat, std::uint64_t{iat} + table_size};
            add_disjoint(iat_ranges, iat_range, "Overlapping import IAT tables");
            lookup_ranges.push_back(lookup_range);
            ++metadata_.import_library_count;
        }
        if (!terminated) {
            fail("Unterminated import descriptor directory");
        }
        // Future IAT routing may replace DWORD slots. Prove those locations cannot
        // overwrite names, descriptors, or another lookup table. A single table
        // used as both its own lookup and IAT is admitted as an explicit PE case.
        for (std::size_t index = 0; index < iat_ranges.size(); ++index) {
            for (const auto range : metadata_ranges) {
                if (overlaps(iat_ranges[index], range)) {
                    fail("IAT aliases import descriptor or name metadata");
                }
            }
            for (std::size_t other = 0; other < lookup_ranges.size(); ++other) {
                const auto iat = iat_ranges[index];
                const auto lookup = lookup_ranges[other];
                const bool same_own_table = index == other && iat.begin == lookup.begin &&
                                           iat.end == lookup.end;
                if (!same_own_table && overlaps(iat, lookup)) {
                    fail("IAT aliases a distinct import lookup table");
                }
            }
        }
    }

    std::span<const std::byte> file_;
    const ImageLimits &limits_;
    ImageMetadata metadata_;
};

} // namespace

LoadedImage load_pe32(std::span<const std::byte> file, const ImageLimits &limits) {
    LoadedImage result;
    result.metadata = Parser(file, limits).parse();
    // Parsing above admits every initialized span, zero tail, directory and
    // import before this private backing is allocated. Initialization temporarily
    // grants writes only to data owned by this not-yet-published result.
    for (const auto &region : result.metadata.mapped_regions) {
        result.memory.map(region.start, region.size, Permissions::read | Permissions::write);
    }
    result.memory.write({result.metadata.image_base},
                        file.first(result.metadata.size_of_headers));
    for (const auto &section : result.metadata.sections) {
        if (section.raw_size) {
            result.memory.write({result.metadata.image_base + section.virtual_address},
                file.subspan(section.raw_offset, section.raw_size));
        }
    }
    for (const auto &region : result.metadata.mapped_regions) {
        result.memory.protect(region.start, region.permissions);
    }
    return result;
}

} // namespace mw34::m4
