#pragma once

#include "texture_source.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <map>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace mw34::vkscene {

// One resident texture as the texture memory line counts it (#518): where it
// came from, its base-level size, and the bytes its image (with mips) takes on
// the card. A row with zero width is a total for a whole source (the parallax
// height images); it counts toward that source and the overall total, but not
// toward the image count or the list of largest sizes.
struct TextureMemoryRow {
  TextureSource source{};
  unsigned width{}, height{};
  std::uint64_t bytes{};
  bool sixteen_bit{};
};

// The driver's own figures for device-local memory (VK_EXT_memory_budget),
// summed over the device-local heaps.
struct DriverFigures {
  std::uint64_t usage_bytes{}, budget_bytes{};
};

// Bytes as MiB with one decimal. Integer math, so the line reads the same
// whatever floating-point mode the game has set.
inline std::string mib_tenths(std::uint64_t bytes) {
  constexpr std::uint64_t mib = 1024ULL * 1024ULL;
  const std::uint64_t tenths = bytes * 10 / mib;
  return std::to_string(tenths / 10) + "." + std::to_string(tenths % 10);
}

// One log line saying how much video memory each kind of texture takes, how
// much of it is stored at 16 bits, and which sizes take the most. The tracked
// figure is everything the renderer allocated on device-local heaps; it is
// larger than the texture total because it also holds models, render targets
// and the unused tail of shared preload blocks.
inline std::string texture_memory_line(const char *reason,
                                       const std::vector<TextureMemoryRow> &rows,
                                       std::uint64_t tracked_bytes,
                                       const std::optional<DriverFigures> &driver) {
  constexpr std::size_t kSourceCount = 5;
  constexpr std::array<const char *, kSourceCount> kSourceNames{"guest", "skin", "normal",
                                                                "canvas", "height"};
  constexpr std::size_t kLargestSizes = 8;
  std::array<std::uint64_t, kSourceCount> source_bytes{};
  std::uint64_t total_bytes = 0, sixteen_bit_bytes = 0;
  std::size_t image_count = 0;
  struct SizeTotal {
    std::size_t count{};
    std::uint64_t bytes{};
  };
  std::map<std::pair<unsigned, unsigned>, SizeTotal> by_size;
  for (const auto &row : rows) {
    source_bytes.at(std::size_t(row.source)) += row.bytes;
    total_bytes += row.bytes;
    if (row.sixteen_bit)
      sixteen_bit_bytes += row.bytes;
    if (row.width == 0)
      continue;
    ++image_count;
    auto &size_total = by_size[{row.width, row.height}];
    ++size_total.count;
    size_total.bytes += row.bytes;
  }
  std::vector<std::pair<std::pair<unsigned, unsigned>, SizeTotal>> largest(by_size.begin(),
                                                                          by_size.end());
  // Most bytes first; equal totals by larger size, so the order never depends
  // on how the renderer's texture map happens to be laid out.
  std::sort(largest.begin(), largest.end(), [](const auto &left, const auto &right) {
    if (left.second.bytes != right.second.bytes)
      return left.second.bytes > right.second.bytes;
    return left.first > right.first;
  });
  if (largest.size() > kLargestSizes)
    largest.resize(kLargestSizes);

  std::string line = std::string("mw3: texture memory (") + reason + "): tracked " +
                     mib_tenths(tracked_bytes) + " MiB, ";
  if (driver)
    line += "driver usage " + mib_tenths(driver->usage_bytes) + " of budget " +
            mib_tenths(driver->budget_bytes) + " MiB; ";
  else
    line += "driver figures unavailable; ";
  line += "textures " + mib_tenths(total_bytes) + " MiB in " + std::to_string(image_count) +
          ", 16-bit " + mib_tenths(sixteen_bit_bytes) + " MiB; ";
  for (std::size_t source = 0; source < kSourceCount; ++source) {
    line += std::string(kSourceNames.at(source)) + " " + mib_tenths(source_bytes.at(source));
    line += source + 1 < kSourceCount ? ", " : " MiB; top:";
  }
  if (largest.empty())
    line += " none";
  for (std::size_t index = 0; index < largest.size(); ++index) {
    const auto &[size, size_total] = largest[index];
    line += std::string(index ? ", " : " ") + std::to_string(size.first) + "x" +
            std::to_string(size.second) + " n=" + std::to_string(size_total.count) + " " +
            mib_tenths(size_total.bytes) + " MiB";
  }
  return line;
}

} // namespace mw34::vkscene
