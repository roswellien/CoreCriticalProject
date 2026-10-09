#include "admission.hpp"
#include "image_loader.hpp"

#include <iostream>
#include <sstream>

static_assert(sizeof(void *) == 8, "M4 native host must be Windows x64");

namespace {

std::string json_string(const std::string &value) {
    constexpr char hex[] = "0123456789abcdef";
    std::string result = "\"";
    for (const unsigned char byte : value) {
        if (byte == '"' || byte == '\\') {
            result += '\\';
            result += static_cast<char>(byte);
        } else if (byte < 32 || byte >= 127) {
            result += "\\u00";
            result += hex[byte >> 4];
            result += hex[byte & 15];
        } else {
            result += static_cast<char>(byte);
        }
    }
    result += '"';
    return result;
}

void write_image_report(const mw34::m4::LoadedImage &image, const std::string &file_hash) {
    const auto &metadata = image.metadata;
    std::ostringstream report;
    report << "{\"schema_version\":1,\"status\":\"image_mapped_startup_not_executed\","
           << "\"native_pointer_bits\":64,\"guest_pointer_bits\":32,"
           << "\"image_sha256\":" << json_string(file_hash)
           << ",\"image_base\":" << metadata.image_base
           << ",\"image_size\":" << metadata.image_size
           << ",\"size_of_headers\":" << metadata.size_of_headers
           << ",\"entry_point\":" << metadata.entry_point.value
           << ",\"entry_point_rva\":" << metadata.entry_point_rva
           << ",\"section_alignment\":" << metadata.section_alignment
           << ",\"file_alignment\":" << metadata.file_alignment
           << ",\"import_library_count\":" << metadata.import_library_count
           << ",\"unresolved_import_count\":" << metadata.imports.size()
           << ",\"original_x86_executed\":false,\"import_resolution_performed\":false,"
           << "\"native_startup_implemented\":false,\"regions\":[";
    bool first = true;
    for (const auto &region : metadata.mapped_regions) {
        std::vector<std::byte> actual(region.size);
        image.memory.read(region.start, actual);
        if (!first) {
            report << ',';
        }
        first = false;
        report << "{\"name\":" << json_string(region.name)
               << ",\"address\":" << region.start.value << ",\"size\":" << region.size
               << ",\"permissions\":" << unsigned(region.permissions)
               << ",\"actual_mapped_sha256\":" << json_string(mw34::m4::sha256(actual)) << '}';
    }
    report << "],\"imports\":[";
    first = true;
    for (const auto &symbol : metadata.imports) {
        const auto actual = image.memory.load<std::uint32_t>(
            mw34::GuestAddress{metadata.image_base + symbol.iat_rva});
        mw34::m4::require_admission(actual == symbol.original_iat_value,
                                  "Mapped IAT bytes differ from admitted original");
        if (!first) {
            report << ',';
        }
        first = false;
        report << "{\"library\":" << json_string(symbol.library)
               << ",\"iat_rva\":" << symbol.iat_rva
               << ",\"lookup_rva\":" << symbol.lookup_rva
               << ",\"hint\":" << symbol.hint
               << ",\"original_iat_value\":" << actual
               << ",\"iat_permissions\":" << unsigned(symbol.iat_permissions);
        if (symbol.name) {
            report << ",\"name\":" << json_string(*symbol.name);
        }
        if (symbol.ordinal) {
            report << ",\"ordinal\":" << *symbol.ordinal;
        }
        report << '}';
    }
    report << "],\"iat_values_preserved\":true}\n";
    std::cout << report.str();
}

} // namespace

int main(int argc, char **argv) {
    try {
        if (argc == 2 && std::string(argv[1]) == "--help") {
            std::cout << "Usage: mw34_m4_startup_host --inspect-image IMAGE | --image IMAGE | --check-admission\n";
            return 0;
        }
        if (argc == 2 && std::string(argv[1]) == "--check-admission") {
            const auto checks = mw34::m4::admission_controls();
            std::cout << "{\"passed\":true,\"admission_controls\":" << checks
                      << ",\"native_pointer_bits\":64,\"original_x86_executed\":false}\n";
            return 0;
        }
        if (argc != 3 || (std::string(argv[1]) != "--inspect-image" &&
                          std::string(argv[1]) != "--image")) {
            std::cerr << "M4 host rejected: expected exactly --inspect-image IMAGE or --image IMAGE\n";
            return 64;
        }
        const auto bytes = mw34::m4::read_image(argv[2]);
        mw34::m4::admit_image(bytes);
        const auto image = mw34::m4::load_pe32(bytes);
        mw34::m4::require_admission(image.metadata.image_base == 0x400000 &&
                                      image.metadata.entry_point.value == 0x5ac3a0 &&
                                      image.metadata.image_size == 0x5f5000 &&
                                      image.metadata.sections.size() == 4 &&
                                      image.metadata.import_library_count == 18 &&
                                      image.metadata.imports.size() == 474,
                                  "Admitted M4 structural profile differs");
        if (std::string(argv[1]) == "--inspect-image") {
            write_image_report(image, mw34::m4::admitted_image_hash);
            return 0;
        }
        // Execute permission is guest metadata. It does not authorize casting
        // guest bytes to a host function or calling the original entry.
        std::cerr << "{\"status\":\"unresolved_native_startup\",\"guest_pc\":"
                  << image.metadata.entry_point.value
                  << ",\"image_mapping_complete\":true,\"original_x86_executed\":false,"
                  << "\"reason\":\"CRT SEH startup, initializer routing and MFC application services require reviewed native implementations\"}\n";
        return 3;
    } catch (const std::exception &error) {
        std::cerr << "M4 host rejected: " << error.what() << '\n';
        return 1;
    }
}
