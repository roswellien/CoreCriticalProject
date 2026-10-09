// Independent observation of Windows' passive image mapping of the exact game.
// No project PE parser/loader, game entry call, DLL loader, import fixup or writes.
#include "admission.hpp"

#include <algorithm>
#include <iostream>

namespace {

struct Handle {
    HANDLE value = INVALID_HANDLE_VALUE;
    ~Handle() {
        if (value && value != INVALID_HANDLE_VALUE) {
            CloseHandle(value);
        }
    }
};

struct View {
    const std::byte *value{};
    ~View() {
        if (value) {
            UnmapViewOfFile(value);
        }
    }
};

struct Region {
    std::uint32_t rva;
    std::uint32_t size;
};

// Literal admitted section/header extents reviewed independently from the PE.
constexpr std::array<Region, 5> regions{{{0, 0x1000}, {0x1000, 0x1ba000},
                                       {0x1bb000, 0x25000}, {0x1e0000, 0x3c2000},
                                       {0x5a2000, 0x53000}}};

void check_readable(const std::byte *start, std::size_t size) {
    std::size_t offset{};
    while (offset < size) {
        MEMORY_BASIC_INFORMATION info{};
        mw34::m4::require_admission(VirtualQuery(start + offset, &info, sizeof(info)) == sizeof(info),
                                    "Windows image region query failed");
        const auto protection = info.Protect & 0xffU;
        mw34::m4::require_admission(info.State == MEM_COMMIT && !(info.Protect & PAGE_GUARD) &&
                                      (protection == PAGE_READONLY || protection == PAGE_READWRITE ||
                                       protection == PAGE_WRITECOPY),
                                    "Passive Windows image region is unreadable or executable");
        const auto available = static_cast<const std::byte *>(info.BaseAddress) + info.RegionSize -
                               (start + offset);
        mw34::m4::require_admission(available > 0, "Invalid Windows image region extent");
        offset += (std::min)(static_cast<std::size_t>(available), size-offset);
    }
}

} // namespace

int main(int argc, char **argv) {
    try {
        mw34::m4::require_admission(argc == 2, "Expected exact admitted image path");
        // Deny writes and deletion while identity and passive view are measured.
        Handle file{CreateFileA(argv[1], GENERIC_READ, FILE_SHARE_READ, nullptr,
                                OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, nullptr)};
        mw34::m4::require_admission(file.value != INVALID_HANDLE_VALUE, "Windows image file open failed");
        const auto original = mw34::m4::read_image(argv[1]);
        mw34::m4::admit_image(original);
        Handle mapping{CreateFileMappingA(file.value, nullptr, PAGE_READONLY | SEC_IMAGE_NO_EXECUTE,
                                          0, 0, nullptr)};
        mw34::m4::require_admission(mapping.value != nullptr, "Passive Windows image mapping failed");
        View view{static_cast<const std::byte *>(MapViewOfFile(mapping.value, FILE_MAP_READ, 0, 0, 0))};
        mw34::m4::require_admission(view.value != nullptr, "Passive Windows image view failed");
        std::string output = "{\"schema_version\":1,\"source\":\"Windows_SEC_IMAGE_NO_EXECUTE\","
                             "\"original_x86_executed\":false,\"dll_loader_used\":false,\"imports_resolved\":false,"
                             "\"image_sha256\":\"" + std::string(mw34::m4::admitted_image_hash) + "\",\"regions\":[";
        for (std::size_t i = 0; i < regions.size(); ++i) {
            const auto &region = regions[i];
            check_readable(view.value+region.rva, region.size);
            if (i) {
                output += ',';
            }
            output += "{\"rva\":"+std::to_string(region.rva)+",\"size\":"+std::to_string(region.size)+
                      ",\"actual_mapped_sha256\":\""+
                      mw34::m4::sha256(std::span<const std::byte>{view.value+region.rva, region.size})+"\"}";
        }
        std::cout << output << "]}\n";
        return 0;
    } catch (const std::exception &error) {
        std::cerr << "Windows passive image probe rejected: " << error.what() << '\n';
        return 1;
    }
}
