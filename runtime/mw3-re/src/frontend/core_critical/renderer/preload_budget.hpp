#pragma once

#include <algorithm>
#include <cstddef>
#include <cstdint>

namespace mw34::vkscene {

// Optional mission and first-world preload must leave enough device-local VRAM
// for lazy draws, swapchain/render-target recreation, and concurrent local
// processes (such as a local model server occupying ~6.9 GiB on a 16 GiB GPU).
// We reserve max(25% of the current process heapBudget, 1536 MiB) per
// device-local heap. All quantities below are in bytes and owned by the
// renderer instance on the producer/worker thread that serializes Vulkan calls.
inline constexpr std::uint64_t kMinimumPreloadHeadroomBytes =
    1536ULL * 1024ULL * 1024ULL;

constexpr std::uint64_t
preload_headroom_bytes(std::uint64_t heap_budget_bytes) noexcept {
  const std::uint64_t quarter_budget_bytes = heap_budget_bytes / 4ULL;
  return quarter_budget_bytes > kMinimumPreloadHeadroomBytes
             ? quarter_budget_bytes
             : kMinimumPreloadHeadroomBytes;
}

constexpr std::uint64_t
preload_usable_bytes(std::uint64_t heap_budget_bytes) noexcept {
  const std::uint64_t headroom_bytes = preload_headroom_bytes(heap_budget_bytes);
  return heap_budget_bytes > headroom_bytes
             ? (heap_budget_bytes - headroom_bytes)
             : 0ULL;
}

struct PreloadBudgetDecision {
  bool admitted{};
  std::uint64_t heap_budget_bytes{};
  std::uint64_t heap_usage_bytes{};
  std::uint64_t headroom_bytes{};
  std::uint64_t usable_bytes{};
  std::uint64_t requested_bytes{};
};

constexpr PreloadBudgetDecision
evaluate_preload_budget(std::uint64_t heap_budget_bytes,
                        std::uint64_t heap_usage_bytes,
                        std::uint64_t requested_bytes) noexcept {
  const std::uint64_t headroom_bytes = preload_headroom_bytes(heap_budget_bytes);
  const std::uint64_t usable_bytes =
      heap_budget_bytes > headroom_bytes ? (heap_budget_bytes - headroom_bytes)
                                         : 0ULL;
  const bool admitted = heap_usage_bytes <= usable_bytes &&
                        requested_bytes <= (usable_bytes - heap_usage_bytes);
  return {admitted,        heap_budget_bytes, heap_usage_bytes,
          headroom_bytes,  usable_bytes,      requested_bytes};
}

enum class PreloadStopReason {
  none,
  budget_denied,
  out_of_device_memory,
  out_of_host_memory,
  allocation_failed,
  oversized_upload
};

constexpr const char *
preload_stop_reason_name(PreloadStopReason reason) noexcept {
  switch (reason) {
  case PreloadStopReason::none:
    return "none";
  case PreloadStopReason::budget_denied:
    return "budget_denied";
  case PreloadStopReason::out_of_device_memory:
    return "out_of_device_memory";
  case PreloadStopReason::out_of_host_memory:
    return "out_of_host_memory";
  case PreloadStopReason::allocation_failed:
    return "allocation_failed";
  case PreloadStopReason::oversized_upload:
    return "oversized_upload";
  }
  return "unknown";
}

struct PreloadStopInfo {
  PreloadStopReason reason{PreloadStopReason::none};
  std::int32_t vk_result{};
  unsigned heap_index{};
  std::uint64_t requested_bytes{};
  std::uint64_t heap_usage_bytes{};
  std::uint64_t heap_budget_bytes{};
  std::uint64_t headroom_bytes{};
  std::uint64_t tracked_heap_bytes{};
};

// Test-only C++ fault and budget-cap injection configuration. Default-inactive
// in production builds; never driven by environment variables or owner settings.
struct PreloadFaultInjection {
  bool override_budget{};
  std::uint64_t synthetic_heap_budget_bytes{};
  std::uint64_t synthetic_base_usage_bytes{};
  std::size_t fail_on_allocation_attempt{};
  // Numeric VkResult is kept here so platform users of frame_renderer.hpp
  // do not acquire a Vulkan SDK dependency. The backend converts at its boundary.
  std::int32_t injected_result{-2};
  // Play-time faults (#496), outside the preload: the next N model buffer
  // allocations, or the next N texture image allocations, fail with
  // injected_result, one after another.
  std::size_t fail_next_play_model_allocations{};
  std::size_t fail_next_play_texture_allocations{};
};

} // namespace mw34::vkscene
