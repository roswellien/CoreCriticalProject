#pragma once

#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <optional>
#include <stdexcept>

namespace mw34::submission {
inline bool scene_uniform_base_enabled() {
    static const bool enabled = [] {
        const char* value = std::getenv("MW34_UNIFORM_BASE_REUSE");
        if (!value || !*value || !std::strcmp(value, "0")) return false;
        if (!std::strcmp(value, "1")) return true;
        throw std::runtime_error("MW34_UNIFORM_BASE_REUSE must be 0 or 1");
    }();
    return enabled;
}

// The pinned sun::uniform function depends on the scene's Settings plus the
// copied normal matrix. Cache only its scene-wide fields; later per-draw edits
// affect the returned copy. A new scene owns a fresh instance, built lazily
// after the caller's original normal validation.
template<class Uniform> class SceneUniformBase {
    bool enabled;
    std::optional<Uniform> base;
  public:
    std::uint64_t builds{}, hits{};
    explicit SceneUniformBase(bool reuse) : enabled(reuse) {}
    template<class Normal, class Build> Uniform capture(const Normal& normal, Build build) {
        if (!enabled) { ++builds; return build(); }
        if (!base) { base = build(); ++builds; }
        else ++hits;
        Uniform result = *base;
        result.normal = normal;
        return result;
    }
};
} // namespace mw34::submission
