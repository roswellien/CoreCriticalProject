#pragma once
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <istream>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>

namespace mw34::materials {
inline constexpr std::uint32_t no_normal = 0xffffffffU;
// Process-wide choice, captured on first use. Changing the environment after
// materials have been initialized does not reload this switch or their pixels.
inline bool normal_maps_enabled() {
    static const bool enabled = [] {
        const char *value = std::getenv("MW34_NORMAL_MAPS");
        if (!value || !std::strcmp(value, "1"))
            return true;
        if (!std::strcmp(value, "0"))
            return false;
        throw std::runtime_error("MW34_NORMAL_MAPS must be 0 or 1");
    }();
    return enabled;
}
// FNV-1a over the entire byte sequence, shared with the Python sidecar writer.
// This is a format/content key, not a cryptographic publisher-admission check.
inline std::uint64_t normal_hash(const void *data, std::size_t size) {
    auto *bytes = static_cast<const unsigned char *>(data);
    std::uint64_t hash = 0xcbf29ce484222325ULL;
    for (std::size_t i = 0; i < size; ++i) {
        hash ^= bytes[i];
        hash *= 0x100000001b3ULL;
    }
    return hash;
}
// Owns decoded linear RGBA8 pixels. On the supported little-endian Windows host,
// each uint32_t stores the four source channel bytes without colour conversion.
struct NormalImage {
    std::string name;
    std::uint32_t width{}, height{};
    std::uint64_t hash{};
    std::vector<std::uint32_t> pixels;
};
struct NormalPack {
    // One image index per material batch, or no_normal for explicit absence.
    // Indices refer to this pack's images, never global renderer texture IDs.
    std::vector<std::uint32_t> bindings;
    std::vector<NormalImage> images;
};
// BWNRM2 is little-endian RGBA8, linear OpenGL tangent normals. Batch order is
// checked against the albedo material names. UINT32_MAX explicitly leaves a
// batch unperturbed (glass, constants or an intentionally absent map).
// BWNRM1 remains readable; its glass exception uses its material name, not slot 3.
inline NormalPack read_normals(std::istream &input, const std::vector<std::string> &materials) {
    // Read from the stream's current position; BWSNR2 places its BWNRM2 payload
    // immediately after a source-surface header. Counts and aggregate pixel bytes
    // are bounded before allocation. Truncation/trailing bytes fail visibly.
    auto fail = [] { throw std::runtime_error("Invalid normal-map sidecar"); };
    auto bytes = [&](void *out, std::size_t count) {
        if (!input.read(static_cast<char *>(out), std::streamsize(count)))
            fail();
    };
    auto u32 = [&] {
        unsigned char b[4];
        bytes(b, 4);
        return std::uint32_t(b[0]) | std::uint32_t(b[1]) << 8 | std::uint32_t(b[2]) << 16 |
               std::uint32_t(b[3]) << 24;
    };
    auto u64 = [&] {
        auto lo = u32();
        return std::uint64_t(lo) | std::uint64_t(u32()) << 32;
    };
    char magic[8];
    bytes(magic, 8);
    const bool version2 = std::memcmp(magic, "BWNRM2\0\0", 8) == 0;
    if (!version2 && std::memcmp(magic, "BWNRM1\0\0", 8))
        fail();
    const auto batches = u32(), count = u32();
    if (batches != materials.size() || batches > 256 || count > 64)
        fail();
    NormalPack pack;
    for (unsigned i = 0; i < batches; ++i) {
        const auto index = u32();
        if (index >= count && !(version2 && index == no_normal))
            fail();
        pack.bindings.push_back(index);
    }
    std::set<std::string> names;
    std::uint64_t total{};
    for (unsigned i = 0; i < count; ++i) {
        char name[32];
        bytes(name, 32);
        if (!name[0] || name[31])
            fail();
        NormalImage image;
        image.name = name;
        if (!names.insert(image.name).second)
            fail();
        image.width = u32();
        image.height = u32();
        image.hash = u64();
        if (!image.width || !image.height || image.width > 4096 || image.height > 4096)
            fail();
        const auto size = std::uint64_t(image.width) * image.height * 4;
        total += size;
        if (total > 256ULL * 1024 * 1024)
            fail();
        image.pixels.resize(std::size_t(size / 4));
        bytes(image.pixels.data(), std::size_t(size));
        if (version2 && normal_hash(image.pixels.data(), std::size_t(size)) != image.hash)
            fail();
        pack.images.push_back(std::move(image));
    }
    if (input.peek() != std::char_traits<char>::eof())
        fail();
    for (unsigned i = 0; i < batches; ++i) {
        auto &index = pack.bindings[i];
        if (index == no_normal)
            continue;
        const auto &name = pack.images[index].name;
        if (name != materials[i])
            fail();
        if (!version2 && (name == "Window" || name == "Glass"))
            index = no_normal;
    }
    return pack;
}
// Surface keys identify every source pixel, not a map name, allocation address
// or a short prefix that can alias unrelated textures on another mission.
struct SurfaceKey {
    std::uint32_t width{}, height{}, format{}; // 1 RGB565, 2 ARGB1555, 3 ARGB4444
    std::uint64_t hash{};
    bool operator<(const SurfaceKey &other) const {
        return std::tie(width, height, format, hash) <
               std::tie(other.width, other.height, other.format, other.hash);
    }
};
struct SurfaceNormals {
    NormalPack pack;
    std::map<SurfaceKey, std::uint32_t> bindings;
};
// Authored catalogs can span small pages while retaining the original single
// BWSNR2 sidecar contract. Enhanced host catalogs have a bounded 512 MiB
// aggregate budget (matching automatic world normals); each page stays within
// its original 256 MiB limit. Guest image/resource limits are unchanged.
inline constexpr std::uint64_t authored_normal_budget = 512ULL * 1024 * 1024;
inline std::vector<std::filesystem::path>
surface_normal_catalog_paths(const std::filesystem::path &path) {
    // Accept one binary sidecar or a bounded text list of pages. Resolve paths,
    // check sizes and reject filesystem aliases here; decoding each page remains
    // the caller's separate operation. No source pixels are loaded by this step.
    auto fail = [] { throw std::runtime_error("Invalid authored surface-normal catalog"); };
    std::ifstream input(path, std::ios::binary);
    if (!input)
        throw std::runtime_error("Configured surface normal sidecar is missing");
    char magic[8];
    if (!input.read(magic, 8))
        fail();
    if (!std::memcmp(magic, "BWSNR2\0\0", 8))
        return {path};
    if (std::memcmp(magic, "MW34SNA1", 8))
        fail();
    if (std::filesystem::file_size(path) > 4096)
        fail();
    if (input.peek() == '\r')
        input.get();
    if (input.get() != '\n')
        fail();
    std::vector<std::filesystem::path> paths;
    std::set<std::string> names;
    std::uint64_t total{};
    std::string line;
    while (std::getline(input, line)) {
        if (!line.empty() && line.back() == '\r')
            line.pop_back();
        const std::filesystem::path entry(line);
        const bool absolute = entry.is_absolute();
        if (line.empty() || line.size() > 512 || line == "." || line == ".." ||
            (!absolute &&
             line.find_first_not_of(
                 "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.") !=
                 std::string::npos) ||
            !names.insert(line).second || names.size() > 16)
            fail();
        // Local authored catalogs may explicitly register absolute pages. Relative
        // entries remain filename-only; traversal and duplicate file aliases fail.
        auto page = absolute ? entry : path.parent_path() / entry;
        if (!std::filesystem::is_regular_file(page))
            fail();
        for (const auto &previous : paths)
            if (std::filesystem::equivalent(previous, page))
                fail();
        const auto size = std::filesystem::file_size(page);
        total += size;
        if (size > 256ULL * 1024 * 1024 || total > authored_normal_budget)
            fail();
        paths.push_back(std::move(page));
    }
    if (!input.eof() || paths.empty())
        fail();
    return paths;
}
// Registration metadata is also used when perturbation is disabled. Keeping
// it separate lets geometric lighting remain on without loading normal pixels.
inline std::vector<std::pair<SurfaceKey, std::string>>
read_surface_normal_header(std::istream &input) {
    // Consume only source identities and material names, leaving the normal-pack
    // payload unread. Disabled perturbation can retain these geometric bindings
    // without allocating pixels; this alone does not validate the unread payload.
    auto fail = [] { throw std::runtime_error("Invalid surface-normal sidecar"); };
    auto bytes = [&](void *out, std::size_t count) {
        if (!input.read(static_cast<char *>(out), std::streamsize(count)))
            fail();
    };
    auto u32 = [&] {
        unsigned char b[4];
        bytes(b, 4);
        return std::uint32_t(b[0]) | std::uint32_t(b[1]) << 8 | std::uint32_t(b[2]) << 16 |
               std::uint32_t(b[3]) << 24;
    };
    char magic[8];
    bytes(magic, 8);
    if (std::memcmp(magic, "BWSNR2\0\0", 8))
        fail();
    const auto count = u32();
    if (!count || count > 256)
        fail();
    std::vector<std::pair<SurfaceKey, std::string>> header;
    std::set<SurfaceKey> unique;
    for (unsigned i = 0; i < count; ++i) {
        SurfaceKey key;
        key.width = u32();
        key.height = u32();
        key.format = u32();
        const auto lo = u32();
        key.hash = std::uint64_t(lo) | std::uint64_t(u32()) << 32;
        if (!key.width || !key.height || key.width > 4096 || key.height > 4096 || key.format < 1 ||
            key.format > 3 || !unique.insert(key).second)
            fail();
        char name[32];
        bytes(name, 32);
        if (!name[0] || name[31])
            fail();
        header.emplace_back(key, name);
    }
    return header;
}
inline SurfaceNormals read_surface_normals(std::istream &input) {
    // Header order becomes the expected material order for read_normals. This
    // joins original-surface keys to pack-local image indices, including no_normal.
    const auto header = read_surface_normal_header(input);
    std::vector<std::string> materials;
    for (const auto &entry : header)
        materials.push_back(entry.second);
    SurfaceNormals result;
    result.pack = read_normals(input, materials);
    for (std::size_t i = 0; i < header.size(); ++i)
        result.bindings.emplace(header[i].first, result.pack.bindings[i]);
    return result;
}
} // namespace mw34::materials
