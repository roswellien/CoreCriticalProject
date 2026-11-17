#pragma once

#include "renderer/material_normals.hpp"
#include "renderer/surface_detail.hpp"

#include <limits>
#include <map>
#include <stdexcept>

namespace mw34::detail {

struct Binding {
  unsigned role{};
  int normal_index{-1};
};

using Bindings = std::map<mw34::materials::SurfaceKey, Binding>;

inline void register_catalog(Bindings &bindings,
                             const mw34::materials::SurfaceNormals &catalog,
                             unsigned role, std::size_t texture_base) {
  if (role < 1 || role > 3 || catalog.bindings.empty() ||
      texture_base > static_cast<std::size_t>(std::numeric_limits<int>::max()) ||
      catalog.pack.images.size() >
          static_cast<std::size_t>(std::numeric_limits<int>::max()) - texture_base)
    throw std::runtime_error("Invalid surface detail catalog role or size");

  for (const auto &[key, local_index] : catalog.bindings) {
    if (local_index == mw34::materials::no_normal ||
        local_index >= catalog.pack.images.size())
      throw std::runtime_error("Surface detail catalog has an empty image binding");
    const auto index = texture_base + local_index;
    if (index > static_cast<std::size_t>(std::numeric_limits<int>::max()) ||
        !bindings.emplace(key, Binding{role, static_cast<int>(index)}).second)
      throw std::runtime_error("Conflicting surface detail texture identity");
  }
}

inline const Binding *find_binding(
    const Bindings &bindings, const mw34::materials::SurfaceKey &key,
    const Settings &settings) {
  const auto found = bindings.find(key);
  return found != bindings.end() && enabled(found->second.role, settings)
             ? &found->second
             : nullptr;
}

} // namespace mw34::detail
