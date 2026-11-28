#pragma once

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <istream>
#include <memory>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <vector>

namespace platform::prepared {

struct SkinCatalogRecord {
    std::string id, name, chassis;
    std::array<std::string, 2> textures;
};
using SkinCatalog = std::vector<SkinCatalogRecord>;

struct SkinTextureBinding {
    std::string chassis, path;
    std::uint32_t lod{}, index{};
};

inline bool skin_catalog_utf8(const std::string &value) {
    for (std::size_t i = 0; i < value.size();) {
        const auto first = static_cast<unsigned char>(value[i++]);
        if (first < 32 || first == 127) return false;
        if (first < 128) continue;
        unsigned count{}, code{}, minimum{};
        if (first >= 0xc2 && first <= 0xdf) count = 1, code = first & 31, minimum = 0x80;
        else if (first >= 0xe0 && first <= 0xef) count = 2, code = first & 15, minimum = 0x800;
        else if (first >= 0xf0 && first <= 0xf4) count = 3, code = first & 7, minimum = 0x10000;
        else return false;
        if (value.size() - i < count) return false;
        for (unsigned n = 0; n < count; ++n) {
            const auto next = static_cast<unsigned char>(value[i++]);
            if ((next & 0xc0) != 0x80) return false;
            code = (code << 6) | (next & 63);
        }
        if (code < minimum || code > 0x10ffff || (code >= 0xd800 && code <= 0xdfff)) return false;
    }
    return true;
}

// A separate compact index keeps the 18-chassis stock roster below Windows'
// command-line limit. It contains only validated metadata and absolute paths.
inline std::vector<SkinTextureBinding> read_skin_bindings(std::istream &input) {
    const auto number = [&]() {
        unsigned char bytes[4]{};
        if (!input.read(reinterpret_cast<char *>(bytes), 4))
            throw std::runtime_error("Truncated prepared skin binding index");
        return std::uint32_t(bytes[0]) | std::uint32_t(bytes[1]) << 8 |
               std::uint32_t(bytes[2]) << 16 | std::uint32_t(bytes[3]) << 24;
    };
    const auto text = [&](std::uint32_t limit) {
        const auto size = number();
        if (!size || size > limit)
            throw std::runtime_error("Invalid prepared skin binding string size");
        std::string result(size, '\0');
        if (!input.read(result.data(), size) || !skin_catalog_utf8(result))
            throw std::runtime_error("Invalid prepared skin binding text");
        return result;
    };
    char magic[8]{};
    if (!input.read(magic, 8) || std::string(magic, 8) != "BWSKIDX1")
        throw std::runtime_error("Unsupported prepared skin binding index");
    const auto count = number();
    if (count > 512)
        throw std::runtime_error("Too many prepared skin bindings");
    std::set<std::tuple<std::string, std::uint32_t, std::uint32_t>> identities;
    std::vector<SkinTextureBinding> result;
    for (std::uint32_t i = 0; i < count; ++i) {
        SkinTextureBinding binding;
        binding.chassis = text(32);
        binding.lod = number();
        binding.index = number();
        binding.path = text(4096);
        if (binding.chassis.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_") != std::string::npos ||
            binding.lod > 1 || binding.index < 1 || binding.index > 7 ||
            !std::filesystem::u8path(binding.path).is_absolute() ||
            !identities.emplace(binding.chassis, binding.lod, binding.index).second)
            throw std::runtime_error("Invalid or duplicate prepared skin binding");
        result.push_back(std::move(binding));
    }
    if (input.peek() != std::char_traits<char>::eof())
        throw std::runtime_error("Trailing prepared skin binding data");
    return result;
}

// Coordinator-resolved paths, never executable content. Stable ID order keeps
// the Lab's appended names and the renderer's numeric selections in agreement.
inline SkinCatalog read_skin_catalog(std::istream &input) {
    const auto number = [&]() {
        unsigned char bytes[4]{};
        if (!input.read(reinterpret_cast<char *>(bytes), 4))
            throw std::runtime_error("Truncated prepared skin catalog");
        return std::uint32_t(bytes[0]) | std::uint32_t(bytes[1]) << 8 |
               std::uint32_t(bytes[2]) << 16 | std::uint32_t(bytes[3]) << 24;
    };
    const auto text = [&]() {
        const auto size = number();
        if (!size || size > 4096)
            throw std::runtime_error("Invalid prepared skin catalog string size");
        std::string result(size, '\0');
        if (!input.read(result.data(), size) || !skin_catalog_utf8(result))
            throw std::runtime_error("Invalid prepared skin catalog text");
        return result;
    };
    char magic[8]{};
    if (!input.read(magic, 8) || std::string(magic, 8) != std::string("BWSKIN1\0", 8))
        throw std::runtime_error("Unsupported prepared skin catalog");
    const auto count = number();
    if (count > 128) throw std::runtime_error("Too many prepared catalog skins");
    SkinCatalog result;
    std::set<std::string> ids;
    for (std::uint32_t i = 0; i < count; ++i) {
        SkinCatalogRecord record{text(), text(), text(), {text(), text()}};
        if (!ids.insert(record.id).second || record.name.size() > 64 ||
            record.id.find(':') == std::string::npos ||
            record.id.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789._-:") != std::string::npos ||
            record.chassis.find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789._-:") != std::string::npos)
            throw std::runtime_error("Invalid or duplicate prepared skin identity");
        for (const auto &path : record.textures)
            if (!std::filesystem::u8path(path).is_absolute())
                throw std::runtime_error("Prepared skin catalog requires absolute texture paths");
        result.push_back(std::move(record));
    }
    if (input.peek() != std::char_traits<char>::eof())
        throw std::runtime_error("Trailing prepared skin catalog data");
    std::sort(result.begin(), result.end(), [](const auto &a, const auto &b) { return a.id < b.id; });
    return result;
}

inline std::shared_ptr<const SkinCatalog> &configured_skin_catalog() {
    static std::shared_ptr<const SkinCatalog> catalog = std::make_shared<const SkinCatalog>();
    return catalog;
}

// Configure at startup, before native definitions are loaded. Both the Lab and
// renderer consume this immutable table; no texture payload is decoded here.
inline void configure_skin_catalog(const std::string &path) {
    configured_skin_catalog() = std::make_shared<const SkinCatalog>();
    if (path.empty()) return;
    try {
        std::ifstream input(std::filesystem::u8path(path), std::ios::binary);
        if (!input) throw std::runtime_error("Cannot open prepared skin catalog");
        configured_skin_catalog() = std::make_shared<const SkinCatalog>(read_skin_catalog(input));
    } catch (const std::exception &error) {
        std::fprintf(stderr, "Prepared skin catalog fallback: %s; using primary/retail skins\n", error.what());
    }
}

// Catalogue identities are host-only and negative, separate from native skin
// rows (including explicit --cc-model-skin indices). A mech's saved selection
// remains its row in the Lab, even when it has fewer or more original skins.
// Reserve -1 for an invalid selection. Stable catalogue order gives both the
// Lab and renderer the same identity without knowing each other's row counts.
template <typename Visitor>
inline void for_each_model_skin(const SkinCatalog &catalog, std::string_view model_name,
                                Visitor &&visit) {
    for (std::size_t index = 0; index < catalog.size(); ++index) {
        const auto &skin = catalog[index];
        if (skin.chassis == model_name)
            visit(skin, -2 - static_cast<int32_t>(index));
    }
}

} // namespace platform::prepared
