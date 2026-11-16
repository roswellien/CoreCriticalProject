// Producer-owned fixture values. No native objects or scene-local indices survive here.
#pragma once
#include "effect_light_ranking.hpp"
#include "native_fixture_geometry.hpp"
#include <memory>
#include <limits>

namespace mw34::native_fixtures {
enum class ObservationStatus { admitted, unknown_material, vehicle_pending, unsupported_mapping };

// Value-only source receipt; weak revision owns no native object. This receipt
// stays on the producer and is never copied into Scene or a worker packet.
struct Dependency {
  std::uint64_t life{}, source_revision{}, transform_revision{};
};
using Matrix = std::array<float, 12>; // Native row-vector affine layout.
inline constexpr Matrix identity_matrix{1,0,0,0,1,0,0,0,1,0,0,0};
struct SourceProof {
  std::uint64_t life{}, pool_epoch{}, load_epoch{}, owner_root{}, healthy_root{};
  std::uint64_t texture_epoch{}, texture_version{};
  std::uint32_t polygon{};
  bool retainable{};
  int texture{-1};
  std::vector<Dependency> dependencies;
  std::weak_ptr<const int> model_revision;
  std::weak_ptr<const int> material_revision;
  bool material_bound{};
  Matrix owner_world = identity_matrix;
};
inline Point transform_point(const Matrix& matrix, const Point& point, bool direction = false) {
  Point result{};
  for (unsigned row = 0; row < 3; ++row)
    result[row] = float(double(point[0])*matrix[row] + double(point[1])*matrix[row+3] +
        double(point[2])*matrix[row+6] + (direction ? 0. : matrix[row+9]));
  return result;
}
inline bool rigid_matrix(const Matrix& matrix) {
  for(float value:matrix) if(!std::isfinite(value)) return false;
  for(unsigned first=0;first<3;++first)
    for(unsigned second=first;second<3;++second) {
      double dot=0;
      for(unsigned component=0;component<3;++component)
        dot+=double(matrix[first*3+component])*matrix[second*3+component];
      if(std::abs(dot-(first==second ? 1. : 0.))>1e-4) return false;
    }
  const double determinant=double(matrix[0])*(double(matrix[4])*matrix[8]-double(matrix[5])*matrix[7])-
      double(matrix[3])*(double(matrix[1])*matrix[8]-double(matrix[2])*matrix[7])+
      double(matrix[6])*(double(matrix[1])*matrix[5]-double(matrix[2])*matrix[4]);
  return determinant>0;
}
inline std::optional<Matrix> inverse_matrix(const Matrix& matrix) {
  for (float value : matrix) if (!std::isfinite(value)) return std::nullopt;
  const double a=matrix[0], b=matrix[3], c=matrix[6];
  const double d=matrix[1], e=matrix[4], f=matrix[7];
  const double g=matrix[2], h=matrix[5], i=matrix[8];
  const double determinant=a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g);
  if (!std::isfinite(determinant) || std::abs(determinant)<1e-12) return std::nullopt;
  Matrix result{};
  const std::array<double,9> inverse{(e*i-f*h)/determinant,(f*g-d*i)/determinant,
      (d*h-e*g)/determinant,(c*h-b*i)/determinant,(a*i-c*g)/determinant,
      (b*g-a*h)/determinant,(b*f-c*e)/determinant,(c*d-a*f)/determinant,
      (a*e-b*d)/determinant};
  for (unsigned component=0;component<9;++component) result[component]=float(inverse[component]);
  const auto translation=transform_point(result, {-matrix[9],-matrix[10],-matrix[11]}, true);
  for(unsigned component=0;component<3;++component) result[component+9]=translation[component];
  for(float value:result) if(!std::isfinite(value)) return std::nullopt;
  return result;
}
// compose(first, second) applies first and then second, matching native Mat34.
inline Matrix compose_matrix(const Matrix& first, const Matrix& second) {
  Matrix result{};
  for(unsigned axis=0;axis<3;++axis) {
    const auto vector=transform_point(second,{first[axis*3],first[axis*3+1],first[axis*3+2]},true);
    std::copy(vector.begin(),vector.end(),result.begin()+axis*3);
  }
  const auto translation=transform_point(second,{first[9],first[10],first[11]});
  std::copy(translation.begin(),translation.end(),result.begin()+9);
  return result;
}

struct Observation {
  materials::SurfaceKey key;
  float intensity{};
  std::vector<Region> regions;
  std::vector<RegionLight> physical_lights;
  std::shared_ptr<const SourceProof> proof;
};
struct ObservationResult {
  ObservationStatus status{ObservationStatus::unknown_material};
  std::shared_ptr<const Observation> value;
};

// Rectangles describe one authenticated atlas tile. The shader repeats UVs,
// so accepting a crossing/repeated tile without matching its physical islands
// would make visible and physical emission disagree. Report it explicitly.
inline ObservationResult observe_source(const materials::SurfaceKey &key,
                                        const std::vector<UvPoint> &triangles,
                                        Winding winding = Winding::original,
                                        bool separate_triangles = false,
                                        std::optional<Point> vehicle_forward = std::nullopt) {
  const auto *definition = match(key);
  if (!definition)
    return {};
  if (definition->classification == Classification::vehicle_headlamp && !vehicle_forward)
    return {ObservationStatus::vehicle_pending, {}};
  if (triangles.empty())
    return {ObservationStatus::admitted, {}};
  if (triangles.size() % 3 || triangles.size() > maximum_triangles * 3)
    detail::reject("Fixture source: invalid triangle count");
  for (const auto &point : triangles)
    if (!std::isfinite(point.u) || !std::isfinite(point.v) || point.u < 0 || point.u > 1 ||
        point.v < 0 || point.v > 1)
      return {ObservationStatus::unsupported_mapping, {}};
  auto observation = std::make_shared<Observation>();
  observation->key = key;
  observation->intensity = definition->intensity;
  observation->regions = definition->emission_regions;
  bool overlapping = false;
  const auto append = [&](const Projection &projection) {
    overlapping = overlapping || !projection.anchors.empty();
    observation->physical_lights.insert(observation->physical_lights.end(),
                                        projection.physical_lights.begin(),
                                        projection.physical_lights.end());
  };
  if (separate_triangles) {
    // Prepared batches can contain separate copies of the same atlas window.
    // Each triangle supplies its own affine map; the view deduplicates shared
    // diagonal halves using owned light values rather than native identities.
    for (std::size_t first = 0; first < triangles.size(); first += 3)
      append(project_fixture(*definition,
          {triangles[first], triangles[first + 1], triangles[first + 2]}, winding, vehicle_forward));
  } else {
    append(project_fixture(*definition, triangles, winding, vehicle_forward));
  }
  return {ObservationStatus::admitted, overlapping ? observation : nullptr};
}

// One view's bounded selection, including packet splits. Persistent receipts
// are revalidated by the producer before their owned lights enter this set.
class VisibleSources {
  struct Entry {
    materials::SurfaceKey key;
    RegionLight source;
    effects::Candidate candidate;
  };
  std::vector<Entry> values_;
  effects::Point eye_{};
  std::uint64_t next_source_{1};
  void compact() {
    std::vector<effects::Candidate> candidates;
    for (const auto& entry : values_) candidates.push_back(entry.candidate);
    const auto ranked = effects::rank_frame_lights(candidates, eye_, 64, 16);
    std::vector<Entry> selected;
    std::vector<bool> used(values_.size(), false);
    const auto count = std::size_t(ranked.params[0]);
    for (std::size_t index=0;index<count;++index) {
      const auto& light=ranked.lights[index];
      for(std::size_t source=0;source<values_.size();++source) {
        if(used[source] || values_[source].candidate.light.start!=light.start ||
           values_[source].candidate.light.end!=light.end ||
           values_[source].candidate.light.color!=light.color) continue;
        selected.push_back(values_[source]);
        used[source]=true;
        break;
      }
    }
    values_=std::move(selected);
  }
public:
  static constexpr std::size_t maximum_sources = 384;
  void clear() { values_.clear(); next_source_=1; }
  void set_eye(effects::Point eye) { eye_=eye; }
  void observe(const Observation &observation) {
    for (const auto &source : observation.physical_lights) {
      const auto &light = source.light;
      const auto same = [&](const Entry &entry) {
        // Affine interpolation of two halves can round the same anchor by a
        // few float ULPs. Only the same exact material/island and coincident
        // world light may collapse; separate instances retain separate lamps.
        if (!(entry.key == observation.key) || entry.source.region != source.region ||
            entry.source.light.start[3] != light.start[3] ||
            entry.source.light.end[3] != light.end[3] || entry.source.light.color != light.color)
          return false;
        const auto coincident = [](float first, float second) {
          const double scale = std::max({1., std::abs(double(first)), std::abs(double(second))});
          const double tolerance = std::max(1e-5,
              4. * std::numeric_limits<float>::epsilon() * scale);
          return std::abs(double(first) - second) <= tolerance;
        };
        for (unsigned component = 0; component < 3; ++component)
          if (!coincident(entry.source.light.start[component], light.start[component]) ||
              !coincident(entry.source.light.end[component], light.end[component]))
            return false;
        return true;
      };
      if (std::find_if(values_.begin(), values_.end(), same) != values_.end())
        continue;
      if (values_.size() == maximum_sources) compact();
      effects::Candidate candidate{};
      candidate.source = (1ULL << 62) + next_source_++;
      candidate.light = light;
      values_.push_back({observation.key, source, candidate});
    }
  }
  std::vector<effects::Candidate> candidates() const {
    std::vector<effects::Candidate> result;
    result.reserve(values_.size());
    for (const auto &value : values_)
      result.push_back(value.candidate);
    return result;
  }
};
} // namespace mw34::native_fixtures
