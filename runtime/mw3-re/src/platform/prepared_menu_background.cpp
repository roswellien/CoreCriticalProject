#include "platform/prepared_menu_background.h"

#include <algorithm>
#include <condition_variable>
#include <cmath>
#include <cstring>
#include <fstream>
#include <functional>
#include <limits>
#include <mutex>
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

struct SourcePixel { int x{-1}, y{-1}; };

class MenuBackgroundWorkers {
 public:
  MenuBackgroundWorkers() {
    const unsigned available = std::max(1u, std::thread::hardware_concurrency());
    const unsigned count = std::min(7u, available - 1);
    try {
      for (unsigned index = 0; index < count; ++index)
        workers_.emplace_back([this, index] { worker_loop(index); });
    } catch (...) {
      stop_workers();
      throw;
    }
  }

  ~MenuBackgroundWorkers() { stop_workers(); }

  unsigned thread_count() const { return static_cast<unsigned>(workers_.size()) + 1; }

  void run(unsigned row_count, const std::function<void(unsigned, unsigned)>& render_rows) {
    if (workers_.empty() || row_count < 128) {
      render_rows(0, row_count);
      return;
    }
    {
      std::lock_guard<std::mutex> lock(mutex_);
      task_ = render_rows;
      row_count_ = row_count;
      remaining_ = workers_.size();
      ++generation_;
    }
    ready_.notify_all();
    render_rows(0, row_count / thread_count());
    std::unique_lock<std::mutex> lock(mutex_);
    finished_.wait(lock, [this] { return remaining_ == 0; });
    task_ = {};
  }

 private:
  void stop_workers() {
    {
      std::lock_guard<std::mutex> lock(mutex_);
      stopping_ = true;
      ++generation_;
    }
    ready_.notify_all();
    for (auto& worker : workers_)
      if (worker.joinable()) worker.join();
  }

  void worker_loop(unsigned index) {
    size_t seen_generation = 0;
    for (;;) {
      std::function<void(unsigned, unsigned)> task;
      unsigned first_row = 0, last_row = 0;
      {
        std::unique_lock<std::mutex> lock(mutex_);
        ready_.wait(lock, [this, seen_generation] {
          return stopping_ || generation_ != seen_generation;
        });
        if (stopping_) return;
        seen_generation = generation_;
        task = task_;
        first_row = row_count_ * (index + 1) / thread_count();
        last_row = row_count_ * (index + 2) / thread_count();
      }
      task(first_row, last_row);
      {
        std::lock_guard<std::mutex> lock(mutex_);
        if (--remaining_ == 0) finished_.notify_one();
      }
    }
  }

  std::vector<std::thread> workers_;
  std::mutex mutex_;
  std::condition_variable ready_, finished_;
  std::function<void(unsigned, unsigned)> task_;
  unsigned row_count_ = 0;
  size_t remaining_ = 0, generation_ = 0;
  bool stopping_ = false;
};

struct ComposeScratch {
  std::vector<SourcePixel> source_at;
  std::vector<uint8_t> kind;
  std::vector<float> actual, expected, added, gain;
  std::unique_ptr<MenuBackgroundWorkers> workers;

  void run(unsigned rows, const std::function<void(unsigned, unsigned)>& render_rows) {
    if (!workers) workers = std::make_unique<MenuBackgroundWorkers>();
    workers->run(rows, render_rows);
  }

  unsigned thread_count() const { return workers ? workers->thread_count() : 1; }
};

bool same_blits(const std::vector<zrndr::MenuBackgroundBlit>& left,
                const std::vector<zrndr::MenuBackgroundBlit>& right) {
  if (left.size() != right.size()) return false;
  for (size_t index = 0; index < left.size(); ++index) {
    const auto& a = left[index];
    const auto& b = right[index];
    if (a.destination_x != b.destination_x || a.destination_y != b.destination_y ||
        a.source_x != b.source_x || a.source_y != b.source_y || a.width != b.width ||
        a.height != b.height)
      return false;
  }
  return true;
}

bool same_frame(const uint16_t* pixels, int width, int height, int pitch,
                const std::vector<uint16_t>& previous) {
  if (previous.size() != size_t(width) * height) return false;
  const auto* bytes = reinterpret_cast<const uint8_t*>(pixels);
  for (int row = 0; row < height; ++row) {
    const auto* current = reinterpret_cast<const uint16_t*>(bytes + size_t(row) * pitch);
    if (std::memcmp(current, previous.data() + size_t(row) * width,
                    size_t(width) * sizeof(uint16_t)) != 0)
      return false;
  }
  return true;
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

static bool compose_menu_background_impl(const MenuBackgroundImage& image, const zimg::Texture* source,
                             const std::vector<zrndr::MenuBackgroundBlit>& blits,
                             const uint16_t* pixels, int width, int height, int pitch,
                             bool rgb565, unsigned output_width, unsigned output_height,
                             std::vector<uint32_t>* output, ComposeScratch* scratch) {
  if (!output || !pixels || !source || source->palette || source->alpha || !source->pixels ||
      source->width != int(image.source_width) || source->height != int(image.source_height) ||
      source->width_again < source->width ||
      width <= 0 || height <= 0 || pitch < int64_t(width) * 2 ||
      output_width == 0 || output_height == 0 ||
      uint64_t(output_width) * output_height > 16ull * 1024 * 1024 || blits.empty())
    return false;

  ComposeScratch local_scratch;
  ComposeScratch& work = scratch ? *scratch : local_scratch;
  auto& source_at = work.source_at;
  auto& kind = work.kind;
  auto& actual = work.actual;
  auto& expected = work.expected;
  auto& added = work.added;
  auto& gain = work.gain;
  source_at.assign(size_t(width) * height, {});
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
  kind.assign(frame_pixels, 0);
  actual.resize(frame_pixels * 3);
  expected.resize(frame_pixels * 3);
  added.assign(frame_pixels * 3, 0.f);
  gain.assign(frame_pixels * 3, 1.f);
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
  if (scratch) {
    work.run(output_height, render_rows);
  } else {
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
  }
  return true;
}

bool compose_menu_background(const MenuBackgroundImage& image, const zimg::Texture* source,
                             const std::vector<zrndr::MenuBackgroundBlit>& blits,
                             const uint16_t* pixels, int width, int height, int pitch,
                             bool rgb565, unsigned output_width, unsigned output_height,
                             std::vector<uint32_t>* output) {
  return compose_menu_background_impl(image, source, blits, pixels, width, height, pitch, rgb565,
                                      output_width, output_height, output, nullptr);
}

struct PreparedMenuBackgroundComposer::Impl {
  ComposeScratch scratch;
  std::vector<uint16_t> previous_frame;
  std::vector<zrndr::MenuBackgroundBlit> previous_blits;
  const MenuBackgroundImage* previous_image = nullptr;
  std::vector<uint32_t>* previous_output = nullptr;
  const uint8_t* previous_image_data = nullptr;
  const zimg::Texture* previous_source = nullptr;
  const void* previous_source_pixels = nullptr;
  unsigned previous_image_width = 0, previous_image_height = 0;
  unsigned previous_image_source_width = 0, previous_image_source_height = 0;
  unsigned previous_source_width = 0, previous_source_height = 0;
  size_t previous_image_rgb_size = 0;
  int previous_source_stride = 0;
  int previous_width = 0, previous_height = 0, previous_pitch = 0;
  bool previous_rgb565 = false, valid = false;
  unsigned previous_output_width = 0, previous_output_height = 0;
};

PreparedMenuBackgroundComposer::PreparedMenuBackgroundComposer()
    : impl_(std::make_unique<Impl>()) {}
PreparedMenuBackgroundComposer::~PreparedMenuBackgroundComposer() = default;

bool PreparedMenuBackgroundComposer::compose(
    const MenuBackgroundImage& image, const zimg::Texture* source,
    const std::vector<zrndr::MenuBackgroundBlit>& blits, const uint16_t* pixels, int width,
    int height, int pitch, bool rgb565, unsigned output_width, unsigned output_height,
    std::vector<uint32_t>* output, bool* cache_hit) {
  if (cache_hit) *cache_hit = false;
  if (!output || !pixels || !source || width <= 0 || height <= 0 || pitch < int64_t(width) * 2)
    return false;
  const auto& state = *impl_;
  const bool hit = state.valid && state.previous_image == &image &&
                   state.previous_image_data == image.rgb.data() &&
                   state.previous_image_width == image.width &&
                   state.previous_image_height == image.height &&
                   state.previous_image_source_width == image.source_width &&
                   state.previous_image_source_height == image.source_height &&
                   state.previous_image_rgb_size == image.rgb.size() &&
                   state.previous_source == source && state.previous_source_pixels == source->pixels &&
                   state.previous_source_width == unsigned(source->width) &&
                   state.previous_source_height == unsigned(source->height) &&
                   state.previous_source_stride == source->width_again &&
                   state.previous_output == output &&
                   state.previous_width == width && state.previous_height == height &&
                   state.previous_pitch == pitch && state.previous_rgb565 == rgb565 &&
                   state.previous_output_width == output_width &&
                   state.previous_output_height == output_height &&
                   same_blits(state.previous_blits, blits) &&
                   same_frame(pixels, width, height, pitch, state.previous_frame);
  if (hit) {
    if (cache_hit) *cache_hit = true;
    return true;
  }

  if (!compose_menu_background_impl(image, source, blits, pixels, width, height, pitch, rgb565,
                                    output_width, output_height, output, &impl_->scratch)) {
    invalidate_cache();
    return false;
  }
  auto& updated = *impl_;
  updated.previous_frame.resize(size_t(width) * height);
  const auto* bytes = reinterpret_cast<const uint8_t*>(pixels);
  for (int row = 0; row < height; ++row) {
    const auto* current = reinterpret_cast<const uint16_t*>(bytes + size_t(row) * pitch);
    std::memcpy(updated.previous_frame.data() + size_t(row) * width, current,
                size_t(width) * sizeof(uint16_t));
  }
  updated.previous_blits = blits;
  updated.previous_image = &image;
  updated.previous_output = output;
  updated.previous_image_data = image.rgb.data();
  updated.previous_image_width = image.width;
  updated.previous_image_height = image.height;
  updated.previous_image_source_width = image.source_width;
  updated.previous_image_source_height = image.source_height;
  updated.previous_image_rgb_size = image.rgb.size();
  updated.previous_source = source;
  updated.previous_source_pixels = source->pixels;
  updated.previous_source_width = unsigned(source->width);
  updated.previous_source_height = unsigned(source->height);
  updated.previous_source_stride = source->width_again;
  updated.previous_width = width;
  updated.previous_height = height;
  updated.previous_pitch = pitch;
  updated.previous_rgb565 = rgb565;
  updated.previous_output_width = output_width;
  updated.previous_output_height = output_height;
  updated.valid = true;
  return true;
}

void PreparedMenuBackgroundComposer::invalidate_cache() { impl_->valid = false; }
unsigned PreparedMenuBackgroundComposer::thread_count() const {
  return impl_->scratch.thread_count();
}
}  // namespace platform
