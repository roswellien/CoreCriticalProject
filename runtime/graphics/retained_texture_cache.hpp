#pragma once

#include <cstddef>
#include <cstdint>
#include <map>
#include <memory>
#include <utility>

namespace mw34::graphics {

// One producer manages the cache. Render jobs retain immutable textures, so an
// eviction can release unused recipes without invalidating an in-flight frame.
template <class Texture> class RetainedTextureCache {
  public:
    explicit RetainedTextureCache(std::size_t limit = 512) : limit_(limit) {}

    template <class Build> std::shared_ptr<const Texture> get(std::uint64_t key, Build &&build) {
        const auto found = textures_.find(key);
        if (found != textures_.end()) {
            return found->second;
        }
        if (textures_.size() > limit_) {
            textures_.clear();
        }
        auto texture = std::make_shared<const Texture>(std::forward<Build>(build)());
        textures_.emplace(key, texture);
        return texture;
    }

  private:
    std::size_t limit_;
    std::map<std::uint64_t, std::shared_ptr<const Texture>> textures_;
};

} // namespace mw34::graphics
