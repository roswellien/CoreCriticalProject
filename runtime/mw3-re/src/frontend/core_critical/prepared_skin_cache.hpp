#pragma once

#include "platform/prepared_visuals.h"

#include <filesystem>
#include <fstream>
#include <map>
#include <set>

namespace cc_mw3_re {

// Only requested liveries are decoded. Draws retain shared ownership while the
// LRU bounds otherwise retained RGB565 planes; a single oversized set is kept
// to avoid rereading it for every batch. GPU slots observe the same ownership.
class PreparedSkinCache {
  public:
    explicit PreparedSkinCache(std::size_t budget = 256 * 1024 * 1024) : budget_(budget) {}

    std::shared_ptr<const platform::prepared::Textures>
    resolve(const std::string &path, const platform::prepared::Mesh &mesh) {
        const auto key = std::filesystem::absolute(std::filesystem::u8path(path))
                             .lexically_normal().generic_string();
        if (failed_.count(key))
            throw std::runtime_error("Prepared skin previously failed to load");
        auto found = entries_.find(key);
        if (found != entries_.end()) {
            platform::prepared::validate_bindings(mesh, *found->second.textures);
            found->second.used = ++clock_;
            return found->second.textures;
        }
        std::shared_ptr<platform::prepared::Textures> textures;
        try {
            std::ifstream input(std::filesystem::u8path(key), std::ios::binary);
            if (!input)
                throw std::runtime_error("Cannot open prepared skin texture payload");
            textures = std::make_shared<platform::prepared::Textures>(
                platform::prepared::read_textures(input));
            ++loads_;
        } catch (...) {
            if (failed_.size() < 512)
                failed_.insert(key);
            throw;
        }
        // A valid payload incompatible with one LOD must not poison another.
        platform::prepared::validate_bindings(mesh, *textures);
        std::size_t bytes = textures->bindings.size() * sizeof(std::uint32_t);
        for (const auto &image : textures->images)
            bytes += image.pixels.size() * sizeof(std::uint16_t);
        while (!entries_.empty() && (bytes > budget_ || bytes_ > budget_ - bytes)) {
            const auto oldest = std::min_element(entries_.begin(), entries_.end(),
                [](const auto &a, const auto &b) { return a.second.used < b.second.used; });
            bytes_ -= oldest->second.bytes;
            entries_.erase(oldest);
        }
        entries_.emplace(key, Entry{textures, bytes, ++clock_});
        bytes_ += bytes;
        return textures;
    }

    void clear() { entries_.clear(); failed_.clear(); bytes_ = 0; }
    std::size_t bytes() const { return bytes_; }
    std::size_t loads() const { return loads_; }

  private:
    struct Entry {
        std::shared_ptr<const platform::prepared::Textures> textures;
        std::size_t bytes{};
        std::uint64_t used{};
    };
    std::size_t budget_, bytes_{}, loads_{};
    std::uint64_t clock_{};
    std::map<std::string, Entry> entries_;
    std::set<std::string> failed_;
};

} // namespace cc_mw3_re
