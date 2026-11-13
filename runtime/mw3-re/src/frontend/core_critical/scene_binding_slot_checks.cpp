#include "renderer/vk_scene.hpp"

#include <cstdio>
#include <stdexcept>

namespace cc_mw3_re::checks {

void check_scene_binding_slots() {
  const auto require = [](bool condition, const char *message) {
    if (!condition)
      throw std::runtime_error(message);
  };
  mw34::vkscene::Scene scene{};
  scene.textures.push_back(
      {7, 11, 2, 3, mw34::vkscene::TexFormat::rgba8888, {}, {}});
  require(scene.texture_slot_matches(0, 7, 11, 2, 3),
          "Scene slot validator rejected matching metadata");
  require(!scene.texture_slot_matches(0, 8, 11, 2, 3),
          "Scene slot validator accepted an in-range wrong key");
  require(!scene.texture_slot_matches(0, 7, 12, 2, 3),
          "Scene slot validator accepted a stale version");
  require(!scene.texture_slot_matches(0, 7, 11, 4, 3) &&
              !scene.texture_slot_matches(0, 7, 11, 2, 4),
          "Scene slot validator accepted wrong dimensions");
  require(!scene.texture_slot_matches(1, 7, 11, 2, 3),
          "Scene slot validator accepted an out-of-range slot");
  std::fprintf(stderr, "scene-bindings: slot controls=6\n");
}

} // namespace cc_mw3_re::checks
