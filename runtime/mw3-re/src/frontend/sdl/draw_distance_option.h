#pragma once

#include <charconv>
#include <system_error>
#include <string_view>

#include "gamez/zclass/visual_distance.h"

namespace sdlfe {

inline bool parse_draw_distance(const char* text, unsigned* distance) {
  if (!text || !distance) return false;
  const std::string_view value{text};
  if (value.empty() || value.front() == '0') return false;
  unsigned parsed_distance = 0;
  const auto result = std::from_chars(value.data(), value.data() + value.size(), parsed_distance);
  if (result.ec != std::errc{} || result.ptr != value.data() + value.size() ||
      !zcls::is_supported_view_distance(parsed_distance)) return false;
  *distance = parsed_distance;
  return true;
}

}  // namespace sdlfe
