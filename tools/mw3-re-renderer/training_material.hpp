#pragma once

#include <array>
#include <memory>
#include <string>
#include <string_view>
#include <vector>

#include "frontend/sdl/sdl_render3d.h"

namespace mw34::vkscene {
struct ModelInstance;
}

namespace cc_mw3_re {

struct TrainingMaterial {
    explicit TrainingMaterial(const sdlfe::CoreCriticalOptions &options);

    std::string node, texture;
    uint64_t albedo_hash{};
    unsigned normal_width{}, normal_height{};
    std::vector<uint32_t> normal_pixels;
    bool enabled{}, probe{};
};

std::string_view node_name(const platform::ModelSurface &surface);
std::string_view texture_name(const platform::ModelSurface &surface);

std::shared_ptr<const mw34::vkscene::ModelInstance>
model_for_draw(const platform::ModelSurface &surface, platform::Primitive primitive,
               const platform::TLVertex *vertices, int count, const std::array<int, 4> &viewport,
               unsigned width, unsigned height);

} // namespace cc_mw3_re
