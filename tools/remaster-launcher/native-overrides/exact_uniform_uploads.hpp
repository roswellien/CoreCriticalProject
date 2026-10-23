#pragma once

#include "exact_uniform_runs.hpp"
#include <cstddef>
#include <cstdlib>

namespace mw34::submission {

inline bool uniform_upload_reuse_enabled() {
    static const bool enabled = [] {
        const char* value = std::getenv("MW34_UNIFORM_UPLOAD_REUSE");
        if (!value || !*value || !std::strcmp(value, "0")) return false;
        if (!std::strcmp(value, "1")) return true;
        throw std::runtime_error("MW34_UNIFORM_UPLOAD_REUSE must be 0 or 1");
    }();
    return enabled;
}

// One instance per scene, under the scene's existing fence. A run ID identifies
// complete byte equality in ordinary CPU memory, never a read of upload memory.
// Keep the original allocation/range guards: run count cannot exceed draw count.
template<class Uniform> class ExactUniformUploads {
    ExactUniformRuns<Uniform> runs;
    bool reuse;
    std::uint32_t uploaded{};

  public:
    std::uint64_t values{}, writes{};

    explicit ExactUniformUploads(bool enabled) : reuse(enabled) {}

    std::uint32_t offset(std::uint32_t identity, std::size_t draw, std::size_t stride) const {
        if (!identity || identity > uploaded)
            throw std::runtime_error("Lighting uniform was not uploaded in this scene");
        const std::size_t slot = reuse ? identity - 1 : draw;
        if (stride < sizeof(Uniform) || slot > std::numeric_limits<std::uint32_t>::max() / stride)
            throw std::runtime_error("Lighting uniform dynamic offset outside range");
        return std::uint32_t(slot * stride);
    }

    std::uint32_t capture(const Uniform& value, std::size_t draw, std::size_t stride, void* mapped) {
        const auto identity = runs.identify(value);
        ++values;
        if (!reuse || identity != uploaded) {
            // Allocation and alignment were validated by the renderer before capture.
            // Publish the identity only after its complete bytes reach the mapped slot.
            const std::size_t slot = reuse ? identity - 1 : draw;
            std::memcpy(static_cast<unsigned char*>(mapped) + slot * stride, &value, sizeof(value));
            ++writes;
            uploaded = identity;
        }
        return identity;
    }
};

} // namespace mw34::submission
