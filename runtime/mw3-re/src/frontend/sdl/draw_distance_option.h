#pragma once

#include <string_view>

namespace sdlfe {

inline bool parse_draw_distance(const char* text, unsigned* distance) {
  if (!text || !distance) return false;
  const std::string_view value{text};
  if (value == "800") *distance = 800;
  else if (value == "1200") *distance = 1200;
  else if (value == "1600") *distance = 1600;
  else return false;
  return true;
}

}  // namespace sdlfe
