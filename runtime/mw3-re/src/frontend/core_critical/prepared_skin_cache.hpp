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
    explicit PreparedSkinCache(std::size_t budget = 1024ULL * 1024 * 1024) : budget_(budget) {}

    static std::string normalize_key(const std::string &path) {
        return std::filesystem::absolute(std::filesystem::u8path(path))
            .lexically_normal().generic_string();
    }

    std::shared_ptr<const platform::prepared::Textures>
    resolve(const std::string &path, const platform::prepared::Mesh &mesh) {
        return resolve_normalized(normalize_key(path), mesh);
    }

    std::shared_ptr<const platform::prepared::Textures>
    resolve_normalized(const std::string &normalized_key,
                       const platform::prepared::Mesh &mesh) {
        if (failed_.count(normalized_key))
            throw std::runtime_error("Prepared skin previously failed to load");
        auto found = entries_.find(normalized_key);
        if (found != entries_.end()) {
            platform::prepared::validate_bindings(mesh, *found->second.textures);
            found->second.used = ++clock_;
            return found->second.textures;
        }
        std::shared_ptr<platform::prepared::Textures> textures;
        try {
            std::ifstream input(std::filesystem::u8path(normalized_key), std::ios::binary);
            if (!input)
                throw std::runtime_error("Cannot open prepared skin texture payload");
            textures = std::make_shared<platform::prepared::Textures>(
                platform::prepared::read_textures(input));
            ++loads_;
        } catch (...) {
            if (failed_.size() < 512)
                failed_.insert(normalized_key);
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
            ++evictions_;
        }
        entries_.emplace(normalized_key, Entry{textures, bytes, ++clock_});
        bytes_ += bytes;
        return textures;
    }

    void clear() { entries_.clear(); failed_.clear(); bytes_ = 0; }
    // Checks only: a tiny budget forces eviction between two draws of one scene.
    void set_budget(std::size_t budget) { budget_ = budget; }
    std::size_t budget() const { return budget_; }
    std::size_t bytes() const { return bytes_; }
    // Loads and evictions are cumulative counters across clear().
    std::size_t loads() const { return loads_; }
    std::size_t evictions() const { return evictions_; }

  private:
    struct Entry {
        std::shared_ptr<const platform::prepared::Textures> textures;
        std::size_t bytes{};
        std::uint64_t used{};
    };
    std::size_t budget_, bytes_{}, loads_{}, evictions_{};
    std::uint64_t clock_{};
    std::map<std::string, Entry> entries_;
    std::set<std::string> failed_;
};

} // namespace cc_mw3_re
