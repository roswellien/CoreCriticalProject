// Video memory and device fault reporting for playtest reports (#521), kept
// apart from vk_scene.hpp so the renderer only calls in. Everything here is
// printed on stderr beside the existing "video memory full" line.
#pragma once

#include "frontend/sdl/game_health.h"
#include "platform/vk_loader.hpp"

#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

namespace mw34::vkscene {

// The table printed once per session at the first failed play allocation:
// one line per heap, DXVK-style.
inline void print_memory_table(std::FILE* out, const std::vector<sdlfe::HeapFigures>& heaps) {
  constexpr double mib = 1024.0 * 1024.0;
  for (const auto& heap : heaps) {
    const double size = double(heap.size_bytes) / mib, used = double(heap.used_bytes) / mib;
    const int local = heap.device_local ? 1 : 0;
    if (heap.driver_figures)
      std::fprintf(out,
                   "mw3: memory table heap=%u size_mib=%.0f used_mib=%.0f budget_mib=%.0f "
                   "device_local=%d\n",
                   heap.index, size, used, double(heap.budget_bytes) / mib, local);
    else
      std::fprintf(out,
                   "mw3: memory table heap=%u size_mib=%.0f used_mib=%.0f budget_mib=n/a "
                   "device_local=%d\n",
                   heap.index, size, used, local);
  }
  std::fflush(out);
}

#ifdef VK_EXT_DEVICE_FAULT_EXTENSION_NAME
using DeviceFaultInfoFn = PFN_vkGetDeviceFaultInfoEXT;
#else
using DeviceFaultInfoFn = void*;  // older Vulkan headers: the report says "not supported"
#endif

// After VK_ERROR_DEVICE_LOST: what the driver says went wrong, from
// VK_EXT_device_fault. Runs on a failing device, so it is bounded (at most
// 32 detail lines), never throws, and writes no vendor binary dump.
inline void print_device_fault(std::FILE* out, VkDevice device, DeviceFaultInfoFn get_fault_info) noexcept {
  try {
#ifdef VK_EXT_DEVICE_FAULT_EXTENSION_NAME
    if (!device || !get_fault_info) {
      std::fprintf(out, "mw3: device fault: not supported\n");
      std::fflush(out);
      return;
    }
    VkDeviceFaultCountsEXT counts{};
    counts.sType = VK_STRUCTURE_TYPE_DEVICE_FAULT_COUNTS_EXT;
    VkResult r = get_fault_info(device, &counts, nullptr);
    if (r != VK_SUCCESS && r != VK_INCOMPLETE) {
      std::fprintf(out, "mw3: device fault: query failed (%d)\n", int(r));
      std::fflush(out);
      return;
    }
    constexpr std::uint32_t kMaxDetail = 32;
    std::vector<VkDeviceFaultAddressInfoEXT> addresses(std::min(counts.addressInfoCount, kMaxDetail));
    std::vector<VkDeviceFaultVendorInfoEXT> vendor(std::min(counts.vendorInfoCount, kMaxDetail));
    counts.addressInfoCount = std::uint32_t(addresses.size());
    counts.vendorInfoCount = std::uint32_t(vendor.size());
    counts.vendorBinarySize = 0;  // the vendor binary dump is not written
    VkDeviceFaultInfoEXT info{};
    info.sType = VK_STRUCTURE_TYPE_DEVICE_FAULT_INFO_EXT;
    info.pAddressInfos = addresses.empty() ? nullptr : addresses.data();
    info.pVendorInfos = vendor.empty() ? nullptr : vendor.data();
    r = get_fault_info(device, &counts, &info);
    if (r != VK_SUCCESS && r != VK_INCOMPLETE) {
      std::fprintf(out, "mw3: device fault: query failed (%d)\n", int(r));
      std::fflush(out);
      return;
    }
    const std::string description(info.description, strnlen(info.description, VK_MAX_DESCRIPTION_SIZE));
    std::fprintf(out, "mw3: device fault: %s; %u addresses, %u vendor faults%s\n", description.c_str(),
                 counts.addressInfoCount, counts.vendorInfoCount, r == VK_INCOMPLETE ? " (incomplete)" : "");
    unsigned printed = 0;
    for (std::uint32_t i = 0; i < counts.addressInfoCount && printed < kMaxDetail; ++i, ++printed)
      std::fprintf(out, "mw3: device fault address type=%d address=0x%016llx precision=%llu\n",
                   int(addresses[i].addressType), (unsigned long long)addresses[i].reportedAddress,
                   (unsigned long long)addresses[i].addressPrecision);
    for (std::uint32_t i = 0; i < counts.vendorInfoCount && printed < kMaxDetail; ++i, ++printed) {
      const std::string text(vendor[i].description, strnlen(vendor[i].description, VK_MAX_DESCRIPTION_SIZE));
      std::fprintf(out, "mw3: device fault vendor code=0x%llx data=0x%llx %s\n",
                   (unsigned long long)vendor[i].vendorFaultCode, (unsigned long long)vendor[i].vendorFaultData,
                   text.c_str());
    }
#else
    (void)device, (void)get_fault_info;
    std::fprintf(out, "mw3: device fault: not supported\n");
#endif
    std::fflush(out);
  } catch (...) {
    std::fprintf(out, "mw3: device fault: query failed (exception)\n");
    std::fflush(out);
  }
}

}  // namespace mw34::vkscene
