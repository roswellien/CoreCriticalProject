// Value-only original-UV placement. No scene traversal or native pose queries.
#pragma once
#include "effect_lighting.hpp"
#include "native_fixture_catalog.hpp"
#include <algorithm>
#include <cmath>
#include <optional>
#include <stdexcept>
#include <vector>

namespace mw34::native_fixtures {
struct UvPoint {
  Point position;
  float u, v;
};
enum class Topology { fan, strip };
enum class Winding { original, reversed_submission };
inline constexpr std::size_t maximum_polygon_corners = 64;
inline constexpr std::size_t maximum_triangles = 4096;

struct RegionAnchor {
  std::size_t region;
  Point position, normal;
};
struct RegionLight {
  std::size_t region;
  effects::Light light;
};
struct Projection {
  std::vector<RegionAnchor> anchors;
  std::vector<RegionLight> physical_lights;
};

namespace detail {
inline void reject(const char *message) { throw std::invalid_argument(message); }
inline bool bounded(float value) {
  return std::isfinite(value) && std::abs(value) <= 1000000.f;
}
inline void validate_point(const UvPoint &point) {
  for (float component : point.position)
    if (!bounded(component))
      reject("Fixture geometry: invalid world position");
  if (!bounded(point.u) || !bounded(point.v))
    reject("Fixture geometry: invalid UV");
}
inline Point unit_direction(const Point &direction) {
  double length_squared = 0;
  for (float component : direction) {
    if (!bounded(component))
      reject("Fixture geometry: invalid direction");
    length_squared += double(component) * component;
  }
  const double length = std::sqrt(length_squared);
  if (length <= 1e-6)
    reject("Fixture geometry: degenerate direction");
  return {float(direction[0] / length), float(direction[1] / length),
          float(direction[2] / length)};
}
inline void validate_color(const Point &color) {
  for (float component : color)
    if (!std::isfinite(component) || component < 0)
      reject("Fixture definition: invalid color");
}

// A triangle clipped by four half planes has at most seven corners. Keep
// clipping storage fixed rather than allocating from input-dependent bounds.
struct Uv {
  double u, v;
};
struct UvPolygon {
  std::array<Uv, 8> points{};
  std::size_t count{};
  void append(Uv point) {
    if (count == points.size())
      reject("Fixture geometry: clipping capacity exceeded");
    points[count++] = point;
  }
};
inline double edge_distance(const Uv &point, const Region &region, unsigned edge) {
  switch (edge) {
  case 0: return point.u - region[0];
  case 1: return region[2] - point.u;
  case 2: return point.v - region[1];
  default: return region[3] - point.v;
  }
}
inline double overlap_area(const UvPoint &a, const UvPoint &b, const UvPoint &c,
                           const Region &region) {
  UvPolygon polygon;
  polygon.append({a.u, a.v});
  polygon.append({b.u, b.v});
  polygon.append({c.u, c.v});
  for (unsigned edge = 0; edge < 4 && polygon.count; ++edge) {
    UvPolygon clipped;
    auto previous = polygon.points[polygon.count - 1];
    double previous_distance = edge_distance(previous, region, edge);
    for (std::size_t index = 0; index < polygon.count; ++index) {
      const auto current = polygon.points[index];
      const double current_distance = edge_distance(current, region, edge);
      if ((previous_distance >= 0) != (current_distance >= 0)) {
        const double fraction = previous_distance / (previous_distance - current_distance);
        clipped.append({previous.u + fraction * (current.u - previous.u),
                        previous.v + fraction * (current.v - previous.v)});
      }
      if (current_distance >= 0)
        clipped.append(current);
      previous = current;
      previous_distance = current_distance;
    }
    polygon = clipped;
  }
  if (polygon.count < 3)
    return 0;
  double area = 0;
  for (std::size_t index = 0; index < polygon.count; ++index) {
    const auto &a = polygon.points[index];
    const auto &b = polygon.points[(index + 1) % polygon.count];
    area += a.u * b.v - b.u * a.v;
  }
  return std::abs(area);
}

struct Triangle {
  const UvPoint *a, *b, *c; // Borrowed only inside the current pure call.
  double determinant;
  Point normal;
};
inline Triangle triangle(const UvPoint &a, const UvPoint &b, const UvPoint &c,
                         Winding winding) {
  const double determinant = (double(b.u) - a.u) * (double(c.v) - a.v) -
                             (double(b.v) - a.v) * (double(c.u) - a.u);
  if (std::abs(determinant) < 1e-12)
    reject("Fixture geometry: degenerate UV mapping");
  std::array<double, 3> edge_b{}, edge_c{};
  for (unsigned component = 0; component < 3; ++component) {
    edge_b[component] = double(b.position[component]) - a.position[component];
    edge_c[component] = double(c.position[component]) - a.position[component];
  }
  const std::array<double, 3> cross{
      edge_b[1] * edge_c[2] - edge_b[2] * edge_c[1],
      edge_b[2] * edge_c[0] - edge_b[0] * edge_c[2],
      edge_b[0] * edge_c[1] - edge_b[1] * edge_c[0]};
  const double length = std::sqrt(cross[0] * cross[0] + cross[1] * cross[1] +
                                  cross[2] * cross[2]);
  if (length <= 1e-6)
    reject("Fixture geometry: degenerate world triangle");
  const double sign = winding == Winding::original ? 1. : -1.;
  Point normal{};
  for (unsigned component = 0; component < 3; ++component)
    normal[component] = float(sign * cross[component] / length);
  return {&a, &b, &c, determinant, normal};
}

inline Point anchor(const Triangle &triangle, const Region &region, float offset) {
  const auto &a = *triangle.a;
  const auto &b = *triangle.b;
  const auto &c = *triangle.c;
  const double du = (double(region[0]) + region[2]) * .5 - a.u;
  const double dv = (double(region[1]) + region[3]) * .5 - a.v;
  const double weight_b = (du * (double(c.v) - a.v) - dv * (double(c.u) - a.u)) /
                           triangle.determinant;
  const double weight_c = ((double(b.u) - a.u) * dv - (double(b.v) - a.v) * du) /
                           triangle.determinant;
  Point position{};
  for (unsigned component = 0; component < 3; ++component) {
    // Extrapolate the authored rectangle center even when clipping removes it.
    // The visible-fragment centroid is not a stable physical source position.
    const double value = a.position[component] +
                         weight_b * (double(b.position[component]) - a.position[component]) +
                         weight_c * (double(c.position[component]) - a.position[component]) +
                         double(triangle.normal[component]) * offset;
    if (!std::isfinite(value) || std::abs(value) > 1000000.)
      reject("Fixture geometry: UV anchor outside supported world");
    position[component] = float(value);
  }
  return position;
}
} // namespace detail

inline void validate_definition(const Definition &definition) {
  if (!definition.name || !definition.width || !definition.height ||
      definition.width > 4096 || definition.height > 4096 || definition.format < 1 ||
      definition.format > 3 || !definition.hash || !detail::bounded(definition.radius) ||
      definition.radius < 0 || !detail::bounded(definition.intensity) ||
      definition.intensity < 0 || !detail::bounded(definition.normal_offset) ||
      definition.normal_offset < 0 || definition.emission_regions.empty() ||
      definition.emission_regions.size() > maximum_regions ||
      definition.emission_radii.size() > definition.emission_regions.size() ||
      definition.emission_colors.size() > definition.emission_regions.size())
    detail::reject("Fixture definition: invalid scalar or region bounds");
  detail::validate_color(definition.color);
  for (const auto &region : definition.emission_regions) {
    for (float coordinate : region)
      if (!std::isfinite(coordinate) || coordinate < 0 || coordinate > 1)
        detail::reject("Fixture definition: invalid emission region");
    if (region[0] >= region[2] || region[1] >= region[3])
      detail::reject("Fixture definition: empty emission region");
  }
  for (float radius : definition.emission_radii)
    if (!detail::bounded(radius) || radius < 0)
      detail::reject("Fixture definition: invalid region radius");
  for (const auto &color : definition.emission_colors)
    detail::validate_color(color);
  if (definition.classification != Classification::scenery &&
      definition.classification != Classification::vehicle_headlamp)
    detail::reject("Fixture definition: unsupported classification");
}

// The caller supplies original corner order. Registered GPU resources have
// reversed submission winding and must say so explicitly when projected below.
inline std::vector<UvPoint> triangulate_polygon(const std::vector<UvPoint> &polygon,
                                               Topology topology = Topology::fan) {
  if (polygon.size() < 3 || polygon.size() > maximum_polygon_corners)
    detail::reject("Fixture geometry: polygon corner limit exceeded");
  if (topology != Topology::fan && topology != Topology::strip)
    detail::reject("Fixture geometry: unsupported topology");
  for (const auto &point : polygon)
    detail::validate_point(point);
  std::vector<UvPoint> triangles;
  triangles.reserve((polygon.size() - 2) * 3);
  for (std::size_t index = 2; index < polygon.size(); ++index) {
    if (topology == Topology::fan) {
      triangles.insert(triangles.end(), {polygon[0], polygon[index - 1], polygon[index]});
    } else {
      const auto first = index - 2;
      triangles.insert(triangles.end(),
                       {polygon[first + (first & 1)], polygon[first + 1 - (first & 1)],
                        polygon[index]});
    }
  }
  return triangles;
}

// Each UV window produces at most one anchor from the largest overlapping
// triangle, matching the maintained source-UV repair. Repeated atlas tiles are
// not expanded here; callers must authenticate their original UV mapping.
// Vehicle activation/ownership is the producer's prerequisite. A vehicle call
// additionally requires its owned world-forward value; it cannot become an
// anonymous point light when that proof is absent.
inline Projection project_fixture(const Definition &definition,
                                  const std::vector<UvPoint> &vertices,
                                  Winding winding = Winding::original,
                                  std::optional<Point> vehicle_forward = std::nullopt) {
  validate_definition(definition);
  if (vertices.size() % 3 || vertices.size() > maximum_triangles * 3)
    detail::reject("Fixture geometry: triangle count outside supported range");
  if (winding != Winding::original && winding != Winding::reversed_submission)
    detail::reject("Fixture geometry: unsupported winding");
  const bool vehicle = definition.classification == Classification::vehicle_headlamp;
  if (vehicle != bool(vehicle_forward))
    detail::reject("Fixture geometry: vehicle direction proof mismatch");
  Point forward{};
  if (vehicle_forward)
    forward = detail::unit_direction(*vehicle_forward);
  for (const auto &point : vertices)
    detail::validate_point(point);
  std::vector<detail::Triangle> triangles;
  triangles.reserve(vertices.size() / 3);
  for (std::size_t index = 0; index < vertices.size(); index += 3)
    triangles.push_back(detail::triangle(vertices[index], vertices[index + 1], vertices[index + 2],
                                         winding));
  Projection result;
  result.anchors.reserve(definition.emission_regions.size());
  result.physical_lights.reserve(definition.emission_regions.size());
  for (std::size_t region_index = 0; region_index < definition.emission_regions.size();
       ++region_index) {
    const auto &region = definition.emission_regions[region_index];
    const detail::Triangle *best_triangle = nullptr;
    double best_area = 0;
    for (const auto &triangle : triangles) {
      const double area = detail::overlap_area(*triangle.a, *triangle.b, *triangle.c, region);
      if (area <= best_area || area < 1e-10)
        continue;
      best_area = area;
      best_triangle = &triangle;
    }
    if (!best_triangle)
      continue;
    const auto &normal = best_triangle->normal;
    if (vehicle && normal[0] * forward[0] + normal[1] * forward[1] +
                       normal[2] * forward[2] < .5f)
      continue;
    const auto position = detail::anchor(*best_triangle, region, definition.normal_offset);
    result.anchors.push_back({region_index, position, normal});
    const float radius = region_index < definition.emission_radii.size()
                             ? definition.emission_radii[region_index] : definition.radius;
    if (definition.emission_only || radius <= 0 || definition.intensity <= 0)
      continue;
    const auto color = region_index < definition.emission_colors.size()
                           ? definition.emission_colors[region_index] : definition.color;
    effects::Light light{};
    light.start = {position[0], position[1], position[2], radius};
    const bool spot = vehicle || definition.is_spot;
    const auto direction = vehicle ? forward : normal;
    light.end = spot ? std::array<float, 4>{direction[0], direction[1], direction[2], 2.f}
                     : std::array<float, 4>{position[0], position[1], position[2], 0.f};
    light.color = {color[0], color[1], color[2], definition.intensity};
    result.physical_lights.push_back({region_index, light});
  }
  return result;
}
} // namespace mw34::native_fixtures
