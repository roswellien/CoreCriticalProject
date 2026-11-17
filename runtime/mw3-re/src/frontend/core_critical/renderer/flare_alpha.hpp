#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string_view>
#include <vector>

namespace mw34::flare {

inline const char *generated_field(bool generated) {
  return generated ? "generated=yes" : "generated=no";
}

inline bool is_texture(std::string_view name) {
  if (name.size() != 7 || name[0] != 'l' || name[1] != 'f' ||
      name[2] != 'l' || name[3] != 'a' || name[4] != 'r' ||
      name[5] != 'e')
    return false;
  const char digit = name[6];
  return digit >= '1' && digit <= '4';
}

inline double cubic(double a, double b, double c, double d, double t) {
  return b + 0.5 * t * (c - a + t * (2.0 * a - 5.0 * b + 4.0 * c - d +
                                      t * (3.0 * (b - c) + d - a)));
}

inline double sample_grid(const std::vector<double> &values, unsigned width,
                          unsigned height, double x, double y) {
  const int x0 = int(std::floor(x));
  const int y0 = int(std::floor(y));
  const double tx = x - x0;
  const double ty = y - y0;
  auto value = [&](int sx, int sy) {
    sx = std::clamp(sx, 0, int(width) - 1);
    sy = std::clamp(sy, 0, int(height) - 1);
    return values[std::size_t(sy) * width + unsigned(sx)];
  };
  std::array<double, 4> rows{};
  for (int row = -1; row <= 2; ++row)
    rows[std::size_t(row + 1)] =
        cubic(value(x0 - 1, y0 + row), value(x0, y0 + row),
              value(x0 + 1, y0 + row), value(x0 + 2, y0 + row), tx);
  return std::clamp(cubic(rows[0], rows[1], rows[2], rows[3], ty), 0.0, 255.0);
}

inline std::vector<std::uint8_t> generate_rgba(std::string_view name,
                                               unsigned width, unsigned height,
                                               const std::uint8_t *rgba) {
  if (!is_texture(name))
    throw std::invalid_argument("Alpha generation requested for a non-flare texture");
  if (!rgba || !width || !height ||
      std::size_t(width) > SIZE_MAX / height / 4)
    throw std::invalid_argument("Invalid flare RGBA source");

  const std::size_t pixel_count = std::size_t(width) * height;
  std::vector<std::uint8_t> result(rgba, rgba + pixel_count * 4);
  if (name[6] == '1') {
    // lflare1's authored star rays are not radial. Average each nearest-sampled
    // 64x64 source cell, then reconstruct that authored shape with Catmull-Rom.
    unsigned source_width = width;
    unsigned source_height = height;
    if (width >= 64 && height >= 64 && width % 64 == 0 && height % 64 == 0) {
      source_width = 64;
      source_height = 64;
    }
    std::vector<double> source(std::size_t(source_width) * source_height);
    unsigned peak = 0;
    for (unsigned sy = 0; sy < source_height; ++sy) {
      for (unsigned sx = 0; sx < source_width; ++sx) {
        const unsigned x_begin = sx * width / source_width;
        const unsigned x_end = (sx + 1) * width / source_width;
        const unsigned y_begin = sy * height / source_height;
        const unsigned y_end = (sy + 1) * height / source_height;
        std::uint64_t sum = 0;
        std::uint64_t count = 0;
        for (unsigned y = y_begin; y < y_end; ++y)
          for (unsigned x = x_begin; x < x_end; ++x) {
            sum += rgba[(std::size_t(y) * width + x) * 4 + 3];
            peak = std::max(peak, unsigned(rgba[(std::size_t(y) * width + x) * 4 + 3]));
            ++count;
          }
        source[std::size_t(sy) * source_width + sx] =
            count ? double(sum) / double(count) : 0.0;
      }
    }
    if (source_width == width && source_height == height) {
      // Stock 64x64 originals have no blown-up block cells to interpolate;
      // apply a light one-texel filter so their star edges are still softened.
      const auto original = source;
      for (unsigned y = 0; y < source_height; ++y)
        for (unsigned x = 0; x < source_width; ++x) {
          auto value = [&](int sx, int sy) {
            sx = std::clamp(sx, 0, int(source_width) - 1);
            sy = std::clamp(sy, 0, int(source_height) - 1);
            return original[std::size_t(sy) * source_width + unsigned(sx)];
          };
          source[std::size_t(y) * source_width + x] =
              (4.0 * value(int(x), int(y)) + 2.0 * value(int(x) - 1, int(y)) +
               2.0 * value(int(x) + 1, int(y)) +
               2.0 * value(int(x), int(y) - 1) +
               2.0 * value(int(x), int(y) + 1) +
               value(int(x) - 1, int(y) - 1) +
               value(int(x) + 1, int(y) - 1) +
               value(int(x) - 1, int(y) + 1) +
               value(int(x) + 1, int(y) + 1)) /
              16.0;
        }
    }
    for (unsigned y = 0; y < height; ++y)
      for (unsigned x = 0; x < width; ++x) {
        const double source_x = (double(x) + 0.5) * source_width / width - 0.5;
        const double source_y = (double(y) + 0.5) * source_height / height - 0.5;
        result[(std::size_t(y) * width + x) * 4 + 3] =
            std::uint8_t(std::lround(sample_grid(source, source_width,
                                                 source_height, source_x,
                                                 source_y)));
      }
    unsigned generated_peak = 0;
    for (std::size_t i = 3; i < result.size(); i += 4)
      generated_peak = std::max(generated_peak, unsigned(result[i]));
    if (generated_peak && peak)
      for (std::size_t i = 3; i < result.size(); i += 4)
        result[i] = std::uint8_t(std::min(
            255U, unsigned(result[i]) * peak / generated_peak));
    return result;
  }

  // The rings and glow are radially symmetric. Fit their original azimuthal
  // mean, then interpolate and supersample at the upload size to smooth edges.
  const double radial_extent = std::sqrt(
      double(width) * width + double(height) * height) /
      double(std::min(width, height));
  const unsigned bins = std::max(
      32U, std::min(unsigned(std::ceil(std::min(width, height) *
                                       radial_extent / 2.0)),
                     2048U));
  std::vector<std::uint64_t> sums(bins);
  std::vector<std::uint32_t> counts(bins);
  unsigned peak = 0;
  const double radius_scale = 2.0 / double(std::min(width, height));
  const double radial_bin_scale = double(bins) / radial_extent;
  for (unsigned y = 0; y < height; ++y) {
    for (unsigned x = 0; x < width; ++x) {
      const unsigned alpha = rgba[(std::size_t(y) * width + x) * 4 + 3];
      peak = std::max(peak, alpha);
      const double dx = (double(x) + 0.5 - double(width) / 2.0) * radius_scale;
      const double dy = (double(y) + 0.5 - double(height) / 2.0) * radius_scale;
      const unsigned bin = std::min(
          bins - 1, unsigned(std::sqrt(dx * dx + dy * dy) * radial_bin_scale));
      sums[bin] += alpha;
      ++counts[bin];
    }
  }
  std::vector<double> profile(bins);
  for (unsigned i = 0; i < bins; ++i)
    if (counts[i])
      profile[i] = double(sums[i]) / counts[i];
  for (unsigned i = 1; i < bins; ++i)
    if (!counts[i])
      profile[i] = profile[i - 1];
  double profile_peak = *std::max_element(profile.begin(), profile.end());
  if (profile_peak > 0.0)
    for (double &value : profile)
      value = std::clamp(value * double(peak) / profile_peak, 0.0, 255.0);

  auto sample_profile = [&](double radius) {
    const double index = radius * radial_bin_scale;
    const unsigned low = std::min(unsigned(index), bins - 1);
    const unsigned high = std::min(low + 1, bins - 1);
    const double fraction = index - std::floor(index);
    return profile[low] * (1.0 - fraction) + profile[high] * fraction;
  };
  constexpr unsigned samples_per_axis = 4;
  constexpr double sample_count = samples_per_axis * samples_per_axis;
  for (unsigned y = 0; y < height; ++y) {
    for (unsigned x = 0; x < width; ++x) {
      double alpha = 0.0;
      for (unsigned sy = 0; sy < samples_per_axis; ++sy)
        for (unsigned sx = 0; sx < samples_per_axis; ++sx) {
          const double dx = (double(x) + (double(sx) + 0.5) / samples_per_axis -
                             double(width) / 2.0) * radius_scale;
          const double dy = (double(y) + (double(sy) + 0.5) / samples_per_axis -
                             double(height) / 2.0) * radius_scale;
          alpha += sample_profile(std::sqrt(dx * dx + dy * dy));
        }
      result[(std::size_t(y) * width + x) * 4 + 3] =
          std::uint8_t(std::clamp(std::lround(alpha / sample_count), 0L, 255L));
    }
  }
  unsigned generated_peak = 0;
  for (std::size_t i = 3; i < result.size(); i += 4)
    generated_peak = std::max(generated_peak, unsigned(result[i]));
  if (generated_peak && peak)
    for (std::size_t i = 3; i < result.size(); i += 4)
      result[i] = std::uint8_t(std::min(
          255U, unsigned(result[i]) * peak / generated_peak));
  return result;
}

} // namespace mw34::flare
