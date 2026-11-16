#pragma once

#include "platform/render3d.h"
#include <array>
#include <cstddef>
#include <cstdint>

namespace cc_mw3_re {
class VulkanFrameRenderer;
namespace testing {

enum class ProducerViewStage {
  exchange, restore, append, local_packet, packet, backend_group, abandon, reset
};

// Owned observations of actual producer/backend storage. No observer, receiver,
// camera or legacy pointer is transported inside a Draw or worker packet.
struct ProducerViewObservation {
  ProducerViewStage stage{};
  ::platform::ProducerView view{};
  ::platform::TLVertex first_vertex{};
  std::array<float, 12> camera_world{};
  std::array<float, 6> projection{};
  std::array<float, 4> surface_eye{};
  std::uint64_t packet{};
  std::size_t scene_draws{}, pending_local_packets{};
  std::size_t upload_receipts{};
  unsigned first{}, count{}, logical_draws{};
  bool sun_tl{}, height_binding{}, combined{}, tl_combine{}, failed{};
};

class ProducerViewObserver {
public:
  virtual ~ProducerViewObserver() = default;
  // Producer may inject an exception; the central producer abandonment path
  // must handle it exactly like any other synchronous admission failure.
  virtual void producer(const ProducerViewObservation&) = 0;
  // Worker/backend writes only a test-owned preallocated bounded sink. Its
  // overflow must be retained and checked after drain, never silently ignored.
  virtual void backend(const ProducerViewObservation&) noexcept = 0;
};

// Installing/removing synchronizes with existing posted jobs. The observer must
// outlive the scoped installation. Unsupported renderers explicitly return false.
bool observe_producer_views(VulkanFrameRenderer&, ProducerViewObserver*);
} // namespace testing
} // namespace cc_mw3_re
