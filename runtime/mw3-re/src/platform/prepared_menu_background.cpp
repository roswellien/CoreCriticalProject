#include "platform/prepared_menu_background.h"

#include <algorithm>
#include <cmath>
#include <cstring>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <thread>

#include "gamez/zimage/zimg_library.h"
#include "gamez/zrender/zrndr_blit.h"

namespace platform {
namespace {
uint32_t word(const uint8_t* bytes) {
  return uint32_t(bytes[0]) | uint32_t(bytes[1]) << 8 | uint32_t(bytes[2]) << 16 |
         uint32_t(bytes[3]) << 24;
}

float channel(uint16_t pixel, int index, bool rgb565) {
  if (index == 0) return float((pixel >> (rgb565 ? 11 : 10)) & 31) * (255.f / 31);
  if (index == 1)
    return float((pixel >> 5) & (rgb565 ? 63 : 31)) * (255.f / (rgb565 ? 63 : 31));
  return float(pixel & 31) * (255.f / 31);
}

uint32_t pack(uint8_t red, uint8_t green, uint8_t blue) {
  return 0xff000000u | uint32_t(red) | uint32_t(green) << 8 | uint32_t(blue) << 16;
}

uint32_t sample(const MenuBackgroundImage& image, double x, double y) {
  x -= std::floor(x / image.width) * image.width;
  y -= std::floor(y / image.height) * image.height;
  const unsigned x0 = unsigned(x), y0 = unsigned(y);
  const unsigned x1 = (x0 + 1) % image.width, y1 = (y0 + 1) % image.height;
  const float tx = float(x - x0), ty = float(y - y0);
  uint8_t channels[3]{};
  for (unsigned c = 0; c < 3; ++c) {
    const auto at = [&](unsigned px, unsigned py) {
      return float(image.rgb[(size_t(py) * image.width + px) * 3 + c]);
    };
    const float top = at(x0, y0) * (1 - tx) + at(x1, y0) * tx;
    const float bottom = at(x0, y1) * (1 - tx) + at(x1, y1) * tx;
    channels[c] = uint8_t(std::clamp(top * (1 - ty) + bottom * ty + .5f, 0.f, 255.f));
  }
  return pack(channels[0], channels[1], channels[2]);
}
}  // namespace

MenuBackgroundImage load_menu_background(const std::filesystem::path& path) {
  std::ifstream input(path, std::ios::binary | std::ios::ate);
  if (!input) throw std::runtime_error("Menu HD background unavailable: " + path.string());
  const auto length = static_cast<std::streamoff>(input.tellg());
  if (length < 24) throw std::runtime_error("Menu HD background header is truncated");
  input.seekg(0);
  uint8_t header[24]{};
  if (!input.read(reinterpret_cast<char*>(header), sizeof header) ||
      std::memcmp(header, "MWHDBG1\0", 8) != 0)
    throw std::runtime_error("Menu HD background requires MWHDBG1");
  MenuBackgroundImage image;
  image.width = word(header + 8);
  image.height = word(header + 12);
  image.source_width = word(header + 16);
  image.source_height = word(header + 20);
  const uint64_t pixels = uint64_t(image.width) * image.height;
  const uint64_t bytes = pixels * 3;
  if (!image.width || !image.height || !image.source_width || !image.source_height ||
      std::max({image.width, image.height, image.source_width, image.source_height}) > 16384 ||
      image.width * uint64_t(image.source_height) != image.height * uint64_t(image.source_width) ||
      bytes > 512ull * 1024 * 1024 || uint64_t(length) != 24 + bytes ||
      bytes > std::numeric_limits<size_t>::max())
    throw std::runtime_error("Menu HD background dimensions or byte length are invalid");
  image.rgb.resize(static_cast<size_t>(bytes));
  if (!input.read(reinterpret_cast<char*>(image.rgb.data()), static_cast<std::streamsize>(bytes)))
    throw std::runtime_error("Menu HD background payload is truncated");
  return image;
}

bool compose_menu_background(const MenuBackgroundImage& image, const zimg::Texture* source,
                             const std::vector<zrndr::MenuBackgroundBlit>& blits,
                             const uint16_t* pixels, int width, int height, int pitch,
                             bool rgb565, unsigned output_width, unsigned output_height,
                             std::vector<uint32_t>* output) {
  if (!output || !pixels || !source || source->palette || source->alpha || !source->pixels ||
      source->width != int(image.source_width) || source->height != int(image.source_height) ||
      source->width_again < source->width ||
      width <= 0 || height <= 0 || pitch < int64_t(width) * 2 || output_width < unsigned(width) ||
      output_height < unsigned(height) || output_width == 0 || output_height == 0 ||
      uint64_t(output_width) * output_height > 16ull * 1024 * 1024 || blits.empty())
    return false;

  struct SourcePixel { int x{-1}, y{-1}; };
  std::vector<SourcePixel> source_at(size_t(width) * height);
  for (const auto& blit : blits) {
    for (int row = 0; row < blit.height; ++row) {
      const int y = blit.destination_y + row;
      if (y < 0 || y >= height || blit.source_y + row < 0 || blit.source_y + row >= source->height)
        continue;
      for (int column = 0; column < blit.width; ++column) {
        const int x = blit.destination_x + column;
        const int sx = blit.source_x + column;
        if (x >= 0 && x < width && sx >= 0 && sx < source->width)
          source_at[size_t(y) * width + x] = {sx, blit.source_y + row};
      }
    }
  }
  const auto* frame = reinterpret_cast<const uint16_t*>(reinterpret_cast<const uint8_t*>(pixels));
  const auto* original = static_cast<const uint16_t*>(source->pixels);
  const int pitch_pixels = pitch / 2;
  const size_t frame_pixels = size_t(width) * height;
  std::vector<uint8_t> kind(frame_pixels);
  std::vector<float> actual(frame_pixels * 3), expected(frame_pixels * 3), added(frame_pixels * 3),
      gain(frame_pixels * 3, 1.f);
  for (int y = 0; y < height; ++y) {
    for (int x = 0; x < width; ++x) {
      const size_t at = size_t(y) * width + x;
      const auto position = source_at[at];
      if (position.x < 0 || position.y < 0) continue;
      const uint16_t rendered = frame[y * pitch_pixels + x];
      const uint16_t background = original[size_t(position.y) * source->width_again + position.x];
      float ratio[3]{};
      bool background_pixel = rendered == background;
      for (int channel_index = 0; channel_index < 3; ++channel_index) {
        actual[at * 3 + channel_index] = channel(rendered, channel_index, rgb565);
        expected[at * 3 + channel_index] = channel(background, channel_index, rgb565);
        ratio[channel_index] = (actual[at * 3 + channel_index] + 8.f) /
                               (expected[at * 3 + channel_index] + 8.f);
      }
      if (!background_pixel) {
        const float minimum = std::min({ratio[0], ratio[1], ratio[2]});
        const float maximum = std::max({ratio[0], ratio[1], ratio[2]});
        background_pixel = minimum > .12f && maximum < 2.5f && maximum <= minimum * 1.45f;
      }
      if (background_pixel) {
        kind[at] = 1;
        continue;
      }
      const float red_delta = actual[at * 3] - expected[at * 3];
      const float green_delta = actual[at * 3 + 1] - expected[at * 3 + 1];
      const float blue_delta = actual[at * 3 + 2] - expected[at * 3 + 2];
      if (green_delta > 6.f && red_delta > -10.f && blue_delta > -10.f &&
          red_delta < green_delta * .6f && blue_delta < green_delta * .6f) {
        kind[at] = 2;
        added[at * 3] = red_delta;
        added[at * 3 + 1] = green_delta;
        added[at * 3 + 2] = blue_delta;
      }
    }
  }
  for (int y = 0; y < height; ++y) {
    for (int x = 0; x < width; ++x) {
      const size_t at = size_t(y) * width + x;
      if (kind[at] != 1) continue;
      float sum_actual[3]{}, sum_expected[3]{};
      for (int dy = -2; dy <= 2; ++dy) {
        const int yy = y + dy;
        if (yy < 0 || yy >= height) continue;
        for (int dx = -2; dx <= 2; ++dx) {
          const int xx = x + dx;
          if (xx < 0 || xx >= width) continue;
          const size_t neighbor = size_t(yy) * width + xx;
          if (kind[neighbor] != 1) continue;
          for (int channel_index = 0; channel_index < 3; ++channel_index) {
            sum_actual[channel_index] += actual[neighbor * 3 + channel_index];
            sum_expected[channel_index] += expected[neighbor * 3 + channel_index];
          }
        }
      }
      for (int channel_index = 0; channel_index < 3; ++channel_index)
        gain[at * 3 + channel_index] = (sum_actual[channel_index] + 4.f) /
                                       (sum_expected[channel_index] + 4.f);
    }
  }

  output->resize(size_t(output_width) * output_height);
  auto render_rows = [&](unsigned first_row, unsigned last_row) {
    for (unsigned oy = first_row; oy < last_row; ++oy) {
      const double fy = (double(oy) + .5) * height / output_height;
      const int y = std::min(height - 1, int(fy));
      const double sub_y = fy - y;
      for (unsigned ox = 0; ox < output_width; ++ox) {
        const double fx = (double(ox) + .5) * width / output_width;
        const int x = std::min(width - 1, int(fx));
        const size_t at = size_t(y) * width + x;
        const uint16_t pixel = frame[y * pitch_pixels + x];
        const auto position = source_at[at];
        if (position.x >= 0 && kind[at] != 0) {
          const double hy = (position.y + sub_y) * double(image.height) / image.source_height;
          const double sub_x = fx - x;
          const double sx = (position.x + sub_x) * double(image.width) / image.source_width;
          const uint32_t color = sample(image, sx, hy);
          uint8_t channels[3] = {uint8_t(color), uint8_t(color >> 8), uint8_t(color >> 16)};
          for (int channel_index = 0; channel_index < 3; ++channel_index) {
            const float correction = kind[at] == 1 ? gain[at * 3 + channel_index] : 1.f;
            channels[channel_index] = uint8_t(std::clamp(
                channels[channel_index] * correction + added[at * 3 + channel_index] + .5f, 0.f,
                255.f));
          }
          (*output)[size_t(oy) * output_width + ox] = pack(channels[0], channels[1], channels[2]);
        } else {
          (*output)[size_t(oy) * output_width + ox] = pack(
              uint8_t(channel(pixel, 0, rgb565) + .5f),
              uint8_t(channel(pixel, 1, rgb565) + .5f),
              uint8_t(channel(pixel, 2, rgb565) + .5f));
        }
      }
    }
  };
  const unsigned thread_count =
      std::min(8u, std::max(1u, std::thread::hardware_concurrency()));
  if (output_height < 128 || thread_count == 1) {
    render_rows(0, output_height);
  } else {
    std::vector<std::thread> workers;
    workers.reserve(thread_count);
    for (unsigned index = 0; index < thread_count; ++index)
      workers.emplace_back(render_rows, output_height * index / thread_count,
                           output_height * (index + 1) / thread_count);
    for (auto& worker : workers) worker.join();
  }
  return true;
}
}  // namespace platform
