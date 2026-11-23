#include "platform/prepared_menu_background.h"

#include <algorithm>
#include <atomic>
#include <condition_variable>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <exception>
#include <fstream>
#include <functional>
#include <limits>
#include <mutex>
#include <stdexcept>
#include <thread>

#include "gamez/zimage/zimg_library.h"
#include "gamez/zrender/zrndr_blit.h"

namespace platform {
namespace detail {
struct MenuBackgroundWorkers::Impl {
  explicit Impl(unsigned requested_worker_count, WorkerWakeupHook worker_wakeup_hook,
                void* worker_wakeup_context)
      : worker_wakeup_hook(worker_wakeup_hook), worker_wakeup_context(worker_wakeup_context) {
    const unsigned available = std::max(1u, std::thread::hardware_concurrency());
    const unsigned count = requested_worker_count == 0
                              ? std::min(7u, available - 1)
                              : std::min(7u, requested_worker_count);
    try {
      for (unsigned index = 0; index < count; ++index)
        workers.emplace_back([this, index] { worker_loop(index); });
    } catch (...) {
      stop_workers();
      throw;
    }
  }

  ~Impl() { stop_workers(); }

  unsigned thread_count() const { return static_cast<unsigned>(workers.size()) + 1; }

  void run(unsigned row_count, const std::function<void(unsigned, unsigned)>& render_rows) {
    if (workers.empty() || row_count < 128) {
      render_rows(0, row_count);
      return;
    }
    {
      std::lock_guard<std::mutex> lock(mutex);
      task = &render_rows;
      rows = row_count;
      remaining = workers.size();
      first_exception = nullptr;
      ++generation;
    }
    ready.notify_all();

    std::exception_ptr caller_failure;
    try {
      render_rows(0, row_count / thread_count());
    } catch (...) {
      caller_failure = std::current_exception();
    }

    std::exception_ptr wait_failure;
    std::exception_ptr failure;
    for (;;) {
      try {
        std::unique_lock<std::mutex> lock(mutex);
        try {
          finished.wait(lock, [this] { return remaining == 0; });
        } catch (...) {
          if (!wait_failure) wait_failure = std::current_exception();
          continue;
        }
        failure = first_exception ? first_exception : caller_failure;
        if (!failure) failure = wait_failure;
        first_exception = nullptr;
        task = nullptr;
        break;
      } catch (...) {
        if (!wait_failure) wait_failure = std::current_exception();
      }
    }
    if (failure) std::rethrow_exception(failure);
  }

 private:
  void stop_workers() {
    {
      std::lock_guard<std::mutex> lock(mutex);
      stopping = true;
      ++generation;
    }
    ready.notify_all();
    for (auto& worker : workers)
      if (worker.joinable()) worker.join();
  }

  void worker_loop(unsigned index) {
    size_t seen_generation = 0;
    for (;;) {
      const std::function<void(unsigned, unsigned)>* current_task = nullptr;
      unsigned first_row = 0, last_row = 0;
      std::exception_ptr failure;
      bool observed_generation = false;
      try {
        std::unique_lock<std::mutex> lock(mutex);
        ready.wait(lock, [this, seen_generation] {
          return stopping || generation != seen_generation;
        });
        if (stopping) return;
        // Once this worker observes a generation, it must account for it even
        // if the test hook or a later operation in this block throws.
        seen_generation = generation;
        observed_generation = true;
        if (worker_wakeup_hook) worker_wakeup_hook(worker_wakeup_context);
        current_task = task;
        const std::uint64_t row_total = rows;
        const std::uint64_t partition_count = workers.size() + 1;
        first_row = static_cast<unsigned>(row_total * (index + 1) / partition_count);
        last_row = static_cast<unsigned>(row_total * (index + 2) / partition_count);
      } catch (...) {
        failure = std::current_exception();
      }
      if (!observed_generation) continue;
      if (!failure && current_task) {
        try {
          (*current_task)(first_row, last_row);
        } catch (...) {
          failure = std::current_exception();
        }
      }

      // A mutex acquisition can itself fail. Retry accounting until it can be
      // committed; otherwise this observed generation would strand run().
      for (;;) {
        try {
          std::lock_guard<std::mutex> lock(mutex);
          if (failure && !first_exception) first_exception = failure;
          if (--remaining == 0) finished.notify_one();
          break;
        } catch (...) {
          if (!failure) failure = std::current_exception();
        }
      }
    }
  }

  std::vector<std::thread> workers;
  std::mutex mutex;
  std::condition_variable ready, finished;
  const std::function<void(unsigned, unsigned)>* task = nullptr;
  std::exception_ptr first_exception;
  unsigned rows = 0;
  size_t remaining = 0, generation = 0;
  bool stopping = false;
  WorkerWakeupHook worker_wakeup_hook = nullptr;
  void* worker_wakeup_context = nullptr;
};

MenuBackgroundWorkers::MenuBackgroundWorkers(unsigned worker_count,
                                             WorkerWakeupHook worker_wakeup_hook,
                                             void* worker_wakeup_context)
    : impl_(std::make_unique<Impl>(worker_count, worker_wakeup_hook,
                                   worker_wakeup_context)) {}
MenuBackgroundWorkers::~MenuBackgroundWorkers() = default;
void MenuBackgroundWorkers::run(
    unsigned row_count, const std::function<void(unsigned, unsigned)>& render_rows) {
  impl_->run(row_count, render_rows);
}
unsigned MenuBackgroundWorkers::thread_count() const { return impl_->thread_count(); }
}  // namespace detail

namespace {
uint32_t word(const uint8_t* bytes) {
  return uint32_t(bytes[0]) | uint32_t(bytes[1]) << 8 | uint32_t(bytes[2]) << 16 |
         uint32_t(bytes[3]) << 24;
}

// The 5- or 6-bit code of one RGB555/RGB565 channel (0 red, 1 green, 2 blue).
unsigned channel_code(uint16_t pixel, int index, bool rgb565) {
  if (index == 0) return (pixel >> (rgb565 ? 11 : 10)) & 31;
  if (index == 1) return (pixel >> 5) & (rgb565 ? 63 : 31);
  return pixel & 31;
}

// 255 over the channel's largest code: a code times this is its 8-bit value.
float channel_scale(int index, bool rgb565) {
  return index == 1 && rgb565 ? 255.f / 63 : 255.f / 31;
}

float channel(uint16_t pixel, int index, bool rgb565) {
  return float(channel_code(pixel, index, rgb565)) * channel_scale(index, rgb565);
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

struct ComposeScratch {
  std::vector<SourcePixel> source_at;
  // 0 native artwork, 1 background (possibly tinted), 2 background with added light.
  std::vector<uint8_t> kind;
  std::vector<float> added, gain;
  // Per background pixel, the channel codes of the rendered and the original pixel (zero
  // elsewhere), and their sums over five columns. The 5x5 gain then needs five additions per
  // pixel instead of 25, in exact integers, so it no longer dominates every menu frame.
  std::vector<uint8_t> codes;
  std::vector<uint16_t> row_sums;
  std::unique_ptr<detail::MenuBackgroundWorkers> workers;
  // A one-off composition (no retained scratch) runs on the caller's thread rather than
  // starting a worker pool for a single frame.
  bool inline_only = false;

  void run(unsigned rows, const std::function<void(unsigned, unsigned)>& render_rows) {
    if (inline_only) {
      render_rows(0, rows);
      return;
    }
    if (!workers) workers = std::make_unique<detail::MenuBackgroundWorkers>();
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

bool valid_menu_inputs(const MenuBackgroundImage& image, const zimg::Texture* source,
                       const std::vector<zrndr::MenuBackgroundBlit>& blits,
                       const uint16_t* pixels, int width, int height, int pitch,
                       unsigned output_width, unsigned output_height) {
    // Empty blits are checked before the source is read: after a menu closes, the registered
    // source pointer can be stale (#375), and an empty blit list is the signal that no menu
    // background is live, so nothing may dereference the source in that case.
    return !blits.empty() && pixels && source && !source->palette && !source->alpha &&
           source->pixels &&
           image.width && image.height && image.source_width && image.source_height &&
           std::max({image.width, image.height, image.source_width, image.source_height}) <=
               16384 &&
           uint64_t(image.width) * image.source_height ==
               uint64_t(image.height) * image.source_width &&
           uint64_t(image.width) * image.height * 3 == image.rgb.size() && source->width > 0 &&
           source->width <= 16384 && source->height == int(image.source_height) &&
           source->width_again >= source->width && width > 0 && height > 0 &&
           pitch >= int64_t(width) * 2 && pitch % 2 == 0 &&
           uint64_t(width) * height <= 16ull * 1024 * 1024 && output_width && output_height &&
           uint64_t(output_width) * output_height <= 16ull * 1024 * 1024;
}
}  // namespace

MenuBackgroundOutputSize menu_background_output_size(int frame_width, int frame_height,
                                                     int window_width, int window_height,
                                                     unsigned maximum_height) {
  if (frame_width <= 0 || frame_height <= 0 || window_width <= 0 || window_height <= 0)
    return {};
  const double fit_scale = std::min({double(window_width) / frame_width,
                                     double(window_height) / frame_height, 4.5});
  const double cap_scale = maximum_height == 0 ? fit_scale
                                                : double(maximum_height) / frame_height;
  const double compose_scale = std::min(fit_scale, cap_scale);
  return {std::max(1u, unsigned(std::lround(frame_width * compose_scale))),
          std::max(1u, unsigned(std::lround(frame_height * compose_scale))), fit_scale,
          compose_scale};
}

MenuBackgroundLayerRect menu_background_layer_rect(int frame_width, int frame_height) {
  return {0.f, 0.f, float(frame_width), float(frame_height)};
}

MenuBackgroundLayerRect menu_background_cover_rect(int frame_width, int frame_height,
                                                    int output_width, int output_height) {
  if (frame_width <= 0 || frame_height <= 0 || output_width <= 0 || output_height <= 0)
    throw std::invalid_argument("Menu cover requires positive frame and output dimensions");
  const double scale = std::max(double(output_width) / frame_width,
                                double(output_height) / frame_height);
  const double covered_width = frame_width * scale;
  const double covered_height = frame_height * scale;
  return {float((output_width - covered_width) * .5),
          float((output_height - covered_height) * .5),
          float(covered_width), float(covered_height)};
}

MenuBackgroundUvRect menu_background_uv_rect(const MenuBackgroundImage &image, int64_t source_x,
                                             int64_t source_y, int frame_width, int frame_height,
                                             unsigned game_width, unsigned game_height,
                                             unsigned texture_width, unsigned texture_height) {
    if (!image.width || !image.height || !image.source_width || !image.source_height ||
        frame_width <= 0 || frame_height <= 0)
        throw std::invalid_argument(
            "Menu UV rectangle requires positive image and frame dimensions");
    const auto wrap = [](int64_t value, unsigned extent) {
        const int64_t remainder = value % int64_t(extent);
        return remainder < 0 ? remainder + extent : remainder;
    };
    if (!game_width)
        game_width = image.source_width;
    if (!game_height)
        game_height = image.source_height;
    // ScrollImage advances at 60 original-game pixels/s on the 1280-wide basis.
    // Scale BOTH origin and span by master_width/game_width: 60 becomes 90 on a
    // 1920-wide master, with the same on-screen speed and a 1920-pixel wrap period.
    if (!texture_width)
        texture_width = image.width;
    if (!texture_height)
        texture_height = image.height;
    const double u0 = double(wrap(source_x, game_width)) / game_width + .5 / texture_width;
    const double v0 = double(wrap(source_y, game_height)) / game_height + .5 / texture_height;
    return {float(u0), float(v0), float(u0 + double(frame_width) / game_width),
            float(v0 + double(frame_height) / game_height)};
}

unsigned menu_background_upload_height(int window_height, int display_height,
                                       unsigned image_height) {
    // Twice the displayed height: a 480-high menu views half a 960-high source canvas. A zero or
    // unknown window (minimised, or not yet sized at startup) must not shrink the texture for the
    // whole session, so use the display's height, and failing that keep the full image.
    if (window_height > 0)
        return unsigned(window_height) * 2;
    if (display_height > 0)
        return unsigned(display_height) * 2;
    return image_height;
}

MenuBackgroundImage menu_background_upload_image(const MenuBackgroundImage &image,
                                                 unsigned maximum_height) {
    if (!maximum_height || !image.width || !image.height ||
        uint64_t(image.width) * image.height * 3 != image.rgb.size())
        throw std::invalid_argument("Menu upload requires a valid image and height limit");
    if (image.height <= maximum_height)
        return image;
    MenuBackgroundImage filtered;
    filtered.height = maximum_height;
    filtered.width = std::max(1u, unsigned(uint64_t(image.width) * maximum_height / image.height));
    filtered.source_width = image.source_width;
    filtered.source_height = image.source_height;
    filtered.rgb.resize(size_t(filtered.width) * filtered.height * 3);
    // Integer overlap weights average each complete source footprint, including
    // fractional edge texels; point sampling here would retain the shimmer.
    const uint64_t total_weight = uint64_t(image.width) * image.height;
    for (unsigned y = 0; y < filtered.height; ++y) {
        const uint64_t top = uint64_t(y) * image.height;
        const uint64_t bottom = top + image.height;
        for (unsigned x = 0; x < filtered.width; ++x) {
            const uint64_t left = uint64_t(x) * image.width;
            const uint64_t right = left + image.width;
            uint64_t sums[3]{};
            for (unsigned source_y = unsigned(top / filtered.height);
                 uint64_t(source_y) * filtered.height < bottom; ++source_y) {
                const uint64_t row_weight =
                    std::min(bottom, uint64_t(source_y + 1) * filtered.height) -
                    std::max(top, uint64_t(source_y) * filtered.height);
                for (unsigned source_x = unsigned(left / filtered.width);
                     uint64_t(source_x) * filtered.width < right; ++source_x) {
                    const uint64_t weight =
                        row_weight * (std::min(right, uint64_t(source_x + 1) * filtered.width) -
                                      std::max(left, uint64_t(source_x) * filtered.width));
                    for (unsigned channel_index = 0; channel_index < 3; ++channel_index)
                        sums[channel_index] +=
                            image.rgb[(size_t(source_y) * image.width + source_x) * 3 +
                                      channel_index] *
                            weight;
                }
            }
            for (unsigned channel_index = 0; channel_index < 3; ++channel_index)
                filtered.rgb[(size_t(y) * filtered.width + x) * 3 + channel_index] =
                    uint8_t((sums[channel_index] + total_weight / 2) / total_weight);
        }
    }
    return filtered;
}

const char* menu_background_gpu_status_name(MenuBackgroundGpuStatus status) {
  switch (status) {
    case MenuBackgroundGpuStatus::kReady: return "ready";
    case MenuBackgroundGpuStatus::kMapping: return "nonuniform-source-mapping";
    case MenuBackgroundGpuStatus::kGain: return "gain-not-finite-or-above-4";
    case MenuBackgroundGpuStatus::kAdded: return "added-light-not-finite-or-beyond-255";
  }
  throw std::invalid_argument("Unknown menu GPU status");
}

MenuBackgroundUvRect menu_background_extend_uv(const MenuBackgroundUvRect& uv,
                                               const MenuBackgroundLayerRect& frame_rectangle,
                                               const MenuBackgroundLayerRect& cover_rectangle) {
  const auto valid_rectangle = [](const MenuBackgroundLayerRect& rectangle) {
    return std::isfinite(rectangle.x) && std::isfinite(rectangle.y) &&
           std::isfinite(rectangle.width) && std::isfinite(rectangle.height) &&
           rectangle.width > 0 && rectangle.height > 0;
  };
  if (!valid_rectangle(frame_rectangle) || !valid_rectangle(cover_rectangle) ||
      !std::isfinite(uv.u0) || !std::isfinite(uv.v0) ||
      !std::isfinite(uv.u1) || !std::isfinite(uv.v1))
    throw std::invalid_argument("Menu background extension requires finite UVs and positive rectangles");
  const double du = double(uv.u1) - uv.u0, dv = double(uv.v1) - uv.v0;
  const double left = double(cover_rectangle.x) - frame_rectangle.x;
  const double top = double(cover_rectangle.y) - frame_rectangle.y;
  return {float(uv.u0 + du * left / frame_rectangle.width),
          float(uv.v0 + dv * top / frame_rectangle.height),
          float(uv.u0 + du * (left + cover_rectangle.width) / frame_rectangle.width),
          float(uv.v0 + dv * (top + cover_rectangle.height) / frame_rectangle.height)};
}

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

namespace {
// Records, for each frame pixel, the background texel a recorded blit put there. Later blits
// overwrite earlier ones, as the native draw order does.
void map_source_pixels(const std::vector<zrndr::MenuBackgroundBlit>& blits,
                       const zimg::Texture& source, int width, int height,
                       std::vector<SourcePixel>* source_at) {
  source_at->assign(size_t(width) * height, {});
  for (const auto& blit : blits) {
    const int64_t first_row = std::max({int64_t(0), -int64_t(blit.destination_y),
                                        -int64_t(blit.source_y)});
    const int64_t last_row = std::min({int64_t(blit.height),
                                       int64_t(height) - blit.destination_y,
                                       int64_t(source.height) - blit.source_y});
    const int64_t first_column = std::max({int64_t(0), -int64_t(blit.destination_x),
                                           -int64_t(blit.source_x)});
    const int64_t last_column = std::min({int64_t(blit.width),
                                          int64_t(width) - blit.destination_x,
                                          int64_t(source.width) - blit.source_x});
    for (int64_t row = first_row; row < last_row; ++row) {
      const int y = int(blit.destination_y + row);
      SourcePixel* destination_row = source_at->data() + size_t(y) * width;
      for (int64_t column = first_column; column < last_column; ++column) {
        const int x = int(blit.destination_x + column);
        destination_row[x] = {int(blit.source_x + column), int(blit.source_y + row)};
      }
    }
  }
}

// One 8-bit UNORM map value; callers have already checked the value lies in [0, 1].
uint8_t unorm(float value) { return uint8_t(value * 255.f + .5f); }

// The GPU pass values of one gain (see MenuBackgroundGpuMap): attenuate * (1 + boost) *
// (1 + boost_high) == gain for every gain in [0, kMenuBackgroundMaximumGain].
struct GainFactors {
  float attenuate, boost, boost_high;
};
GainFactors split_gain(float gain) {
  GainFactors factors{std::min(gain, 1.f), 0.f, 0.f};
  if (gain > 1.f) factors.boost = std::min(gain, 2.f) - 1.f;
  if (gain > 2.f) factors.boost_high = gain * .5f - 1.f;
  return factors;
}
}  // namespace

static bool compose_menu_background_impl(const MenuBackgroundImage& image, const zimg::Texture* source,
                             const std::vector<zrndr::MenuBackgroundBlit>& blits,
                             const uint16_t* pixels, int width, int height, int pitch,
                             bool rgb565, unsigned output_width, unsigned output_height,
                             std::vector<uint32_t>* output, ComposeScratch* scratch,
                             MenuBackgroundGpuLayers* layers = nullptr,
                             unsigned bound_texture_width = 0, unsigned bound_texture_height = 0) {
  if ((!output && !layers) || !valid_menu_inputs(image, source, blits, pixels, width, height,
                                               pitch, output_width, output_height))
    return false;

  ComposeScratch local_scratch;
  local_scratch.inline_only = true;
  ComposeScratch& work = scratch ? *scratch : local_scratch;
  auto& source_at = work.source_at;
  auto& kind = work.kind;
  auto& added = work.added;
  auto& gain = work.gain;
  auto& codes = work.codes;
  auto& row_sums = work.row_sums;
  map_source_pixels(blits, *source, width, height, &source_at);
  const auto* frame = reinterpret_cast<const uint16_t*>(reinterpret_cast<const uint8_t*>(pixels));
  const auto* original = static_cast<const uint16_t*>(source->pixels);
  const int pitch_pixels = pitch / 2;
  const size_t frame_pixels = size_t(width) * height;
  kind.resize(frame_pixels);
  added.resize(frame_pixels * 3);
  gain.resize(frame_pixels * 3);
  codes.resize(frame_pixels * 6);
  row_sums.resize(frame_pixels * 6);

  // Classification: every pixel depends only on its own rendered and original values, so rows
  // run in parallel. The thresholds are unchanged from the serial version.
  work.run(unsigned(height), [&](unsigned first_row, unsigned last_row) {
    for (unsigned y = first_row; y < last_row; ++y) {
      for (int x = 0; x < width; ++x) {
        const size_t at = size_t(y) * width + x;
        kind[at] = 0;
        for (int channel_index = 0; channel_index < 3; ++channel_index) {
          added[at * 3 + channel_index] = 0.f;
          gain[at * 3 + channel_index] = 1.f;
        }
        std::fill_n(codes.begin() + at * 6, 6, uint8_t(0));
        const auto position = source_at[at];
        if (position.x < 0 || position.y < 0) continue;
        const uint16_t rendered = frame[size_t(y) * pitch_pixels + x];
        const uint16_t background =
            original[size_t(position.y) * source->width_again + position.x];
        float actual[3]{}, expected[3]{}, ratio[3]{};
        bool background_pixel = rendered == background;
        for (int channel_index = 0; channel_index < 3; ++channel_index) {
          actual[channel_index] = channel(rendered, channel_index, rgb565);
          expected[channel_index] = channel(background, channel_index, rgb565);
          ratio[channel_index] = (actual[channel_index] + 8.f) / (expected[channel_index] + 8.f);
        }
        if (!background_pixel) {
          const float minimum = std::min({ratio[0], ratio[1], ratio[2]});
          const float maximum = std::max({ratio[0], ratio[1], ratio[2]});
          background_pixel = minimum > .12f && maximum < 2.5f && maximum <= minimum * 1.45f;
        }
        if (background_pixel) {
          kind[at] = 1;
          for (int channel_index = 0; channel_index < 3; ++channel_index) {
            codes[at * 6 + channel_index] = uint8_t(channel_code(rendered, channel_index, rgb565));
            codes[at * 6 + 3 + channel_index] =
                uint8_t(channel_code(background, channel_index, rgb565));
          }
          continue;
        }
        const float red_delta = actual[0] - expected[0];
        const float green_delta = actual[1] - expected[1];
        const float blue_delta = actual[2] - expected[2];
        if (green_delta > 6.f && red_delta > -10.f && blue_delta > -10.f &&
            red_delta < green_delta * .6f && blue_delta < green_delta * .6f) {
          kind[at] = 2;
          added[at * 3] = red_delta;
          added[at * 3 + 1] = green_delta;
          added[at * 3 + 2] = blue_delta;
        }
      }
    }
  });
  // The gain of a background pixel is the ratio of the rendered to the original light over the
  // background pixels of its 5x5 neighbourhood. Codes are summed as integers, five columns then
  // five rows; non-background pixels hold zero codes and so add nothing.
  work.run(unsigned(height), [&](unsigned first_row, unsigned last_row) {
    for (unsigned y = first_row; y < last_row; ++y) {
      for (int x = 0; x < width; ++x) {
        const size_t at = size_t(y) * width + x;
        const int first_column = std::max(0, x - 2), last_column = std::min(width - 1, x + 2);
        for (int value = 0; value < 6; ++value) {
          unsigned sum = 0;
          for (int column = first_column; column <= last_column; ++column)
            sum += codes[(size_t(y) * width + column) * 6 + value];
          row_sums[at * 6 + value] = uint16_t(sum);
        }
      }
    }
  });
  work.run(unsigned(height), [&](unsigned first_row, unsigned last_row) {
    for (unsigned y = first_row; y < last_row; ++y) {
      const int first_neighbour_row = std::max(0, int(y) - 2);
      const int last_neighbour_row = std::min(height - 1, int(y) + 2);
      for (int x = 0; x < width; ++x) {
        const size_t at = size_t(y) * width + x;
        if (kind[at] != 1) continue;
        unsigned sums[6]{};
        for (int row = first_neighbour_row; row <= last_neighbour_row; ++row)
          for (int value = 0; value < 6; ++value)
            sums[value] += row_sums[(size_t(row) * width + x) * 6 + value];
        for (int channel_index = 0; channel_index < 3; ++channel_index) {
          const float scale = channel_scale(channel_index, rgb565);
          const float sum_actual = float(sums[channel_index]) * scale;
          const float sum_expected = float(sums[3 + channel_index]) * scale;
          // Near-black background makes this ratio of tiny sums meaningless (an original code 0
          // shown as code 1 gives about 52), so both paths limit it to what the GPU passes hold.
          gain[at * 3 + channel_index] =
              std::min((sum_actual + 4.f) / (sum_expected + 4.f), kMenuBackgroundMaximumGain);
        }
      }
    }
  });

  if (layers) {
    bool maps_changed = layers->status != MenuBackgroundGpuStatus::kReady;
    for (const auto& map : layers->maps) maps_changed = maps_changed || map.size() != frame_pixels;
    layers->status = MenuBackgroundGpuStatus::kMapping;
    // All recorded pieces must be one affine rectangle modulo the image, including overlap
    // order. Otherwise a single repeating quad cannot reproduce the CPU source_at map.
    const SourcePixel* first_mapped = std::find_if(
        source_at.data(), source_at.data() + frame_pixels,
        [](const SourcePixel& position) { return position.x >= 0; });
    if (first_mapped == source_at.data() + frame_pixels) return true;
    const size_t first_index = size_t(first_mapped - source_at.data());
    const int origin_x = first_mapped->x - int(first_index % width);
    const int origin_y = first_mapped->y - int(first_index / width);
    std::atomic<bool> nonuniform{false};
    work.run(unsigned(height), [&](unsigned first_row, unsigned last_row) {
      for (unsigned y = first_row; y < last_row && !nonuniform.load(std::memory_order_relaxed);
           ++y) {
        for (int x = 0; x < width; ++x) {
          const auto position = source_at[size_t(y) * width + x];
          if (position.x < 0) continue;
          if ((int64_t(position.x) - x - origin_x) % source->width != 0 ||
              (int64_t(position.y) - int64_t(y) - origin_y) % source->height != 0) {
            nonuniform.store(true, std::memory_order_relaxed);
            break;
          }
        }
      }
    });
    if (nonuniform.load()) return true;
    layers->uv = menu_background_uv_rect(image, origin_x, origin_y, width, height,
                                         unsigned(source->width), unsigned(source->height),
                                         bound_texture_width, bound_texture_height);
    for (auto& map : layers->maps) map.resize(frame_pixels);
    // Bit i of a mask stands for map i. Rows report which maps changed and which are needed
    // once per row block, not per pixel.
    std::atomic<unsigned> changed_maps{0}, used_maps{1u << kMenuGpuOverlay};
    std::atomic<bool> gain_unrepresentable{false}, added_unrepresentable{false};
    work.run(unsigned(height), [&](unsigned first_row, unsigned last_row) {
      unsigned block_changed = 0, block_used = 0;
      bool block_gain_error = false, block_added_error = false;
      for (unsigned y = first_row; y < last_row; ++y) {
        for (int x = 0; x < width; ++x) {
          const size_t at = size_t(y) * width + x;
          const uint16_t pixel = frame[size_t(y) * pitch_pixels + x];
          uint8_t attenuate[3]{255, 255, 255}, boost[3]{}, boost_high[3]{};
          uint8_t add[3]{}, subtract[3]{};
          for (int c = 0; c < 3; ++c) {
            if (kind[at] == 1) {
              const float factor = gain[at * 3 + c];
              if (!std::isfinite(factor) || factor < 0.f || factor > kMenuBackgroundMaximumGain) {
                block_gain_error = true;
                continue;
              }
              const GainFactors split = split_gain(factor);
              attenuate[c] = unorm(split.attenuate);
              boost[c] = unorm(split.boost);
              boost_high[c] = unorm(split.boost_high);
            }
            if (kind[at] == 2) {
              const float delta = added[at * 3 + c];
              if (!std::isfinite(delta) || std::fabs(delta) > 255.f) {
                block_added_error = true;
                continue;
              }
              if (delta >= 0.f)
                add[c] = uint8_t(delta + .5f);
              else
                subtract[c] = uint8_t(-delta + .5f);
            }
          }
          // The overlay alone carries alpha (opaque native artwork). The other maps keep alpha
          // so their passes leave the opaque destination's alpha unchanged: one for the
          // multiply, zero for the additive passes.
          uint32_t values[kMenuGpuMapCount]{};
          values[kMenuGpuAttenuate] = pack(attenuate[0], attenuate[1], attenuate[2]);
          values[kMenuGpuBoost] = pack(boost[0], boost[1], boost[2]) & 0x00ffffffu;
          values[kMenuGpuBoostHigh] = pack(boost_high[0], boost_high[1], boost_high[2]) &
                                      0x00ffffffu;
          values[kMenuGpuAdd] = pack(add[0], add[1], add[2]) & 0x00ffffffu;
          values[kMenuGpuSubtract] = pack(subtract[0], subtract[1], subtract[2]) & 0x00ffffffu;
          values[kMenuGpuOverlay] =
              kind[at] == 0 ? pack(uint8_t(channel(pixel, 0, rgb565) + .5f),
                                   uint8_t(channel(pixel, 1, rgb565) + .5f),
                                   uint8_t(channel(pixel, 2, rgb565) + .5f))
                            : 0;
          for (unsigned map = 0; map < kMenuGpuMapCount; ++map) {
            uint32_t& stored = layers->maps[map][at];
            if (stored != values[map]) block_changed |= 1u << map;
            stored = values[map];
          }
          if (values[kMenuGpuAttenuate] != 0xffffffffu) block_used |= 1u << kMenuGpuAttenuate;
          for (unsigned map : {kMenuGpuBoost, kMenuGpuBoostHigh, kMenuGpuAdd, kMenuGpuSubtract})
            if (values[map] != 0) block_used |= 1u << map;
        }
      }
      changed_maps.fetch_or(block_changed, std::memory_order_relaxed);
      used_maps.fetch_or(block_used, std::memory_order_relaxed);
      if (block_gain_error) gain_unrepresentable.store(true, std::memory_order_relaxed);
      if (block_added_error) added_unrepresentable.store(true, std::memory_order_relaxed);
    });
    if (gain_unrepresentable.load()) {
      layers->status = MenuBackgroundGpuStatus::kGain;
      return true;
    }
    if (added_unrepresentable.load()) {
      layers->status = MenuBackgroundGpuStatus::kAdded;
      return true;
    }
    const unsigned changed = changed_maps.load();
    const unsigned used = used_maps.load();
    for (unsigned map = 0; map < kMenuGpuMapCount; ++map) {
      layers->used[map] = (used >> map) & 1u;
      if (maps_changed || ((changed >> map) & 1u)) {
        if (layers->map_revisions[map] == std::numeric_limits<uint64_t>::max())
          throw std::overflow_error("Menu GPU map revision exhausted");
        ++layers->map_revisions[map];
      }
    }
    if (maps_changed || changed != 0) {
      if (layers->revision == std::numeric_limits<uint64_t>::max())
        throw std::overflow_error("Menu GPU map revision exhausted");
      ++layers->revision;
    }
    layers->status = MenuBackgroundGpuStatus::kReady;
    return true;
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
        const uint16_t pixel = frame[size_t(y) * pitch_pixels + x];
        const auto position = source_at[at];
        if (position.x >= 0 && kind[at] != 0) {
            const double hy = (position.y + sub_y) * double(image.height) / source->height;
            const double sub_x = fx - x;
            const double sx = (position.x + sub_x) * double(image.width) / source->width;
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

PreparedMenuTextureAction prepared_menu_texture_action(bool cache_hit, bool texture_exists,
                                                       int texture_width, int texture_height,
                                                       unsigned output_width,
                                                       unsigned output_height) {
  if (!texture_exists || texture_width != int(output_width) ||
      texture_height != int(output_height))
    return PreparedMenuTextureAction::kCreate;
  return cache_hit ? PreparedMenuTextureAction::kReuse : PreparedMenuTextureAction::kUpdate;
}

struct PreparedMenuBackgroundComposer::Impl {
  ComposeScratch scratch;
  std::vector<uint16_t> previous_frame;
  std::vector<zrndr::MenuBackgroundBlit> previous_blits;
  const MenuBackgroundImage* previous_image = nullptr;
  std::vector<uint32_t>* previous_output = nullptr;
  MenuBackgroundGpuLayers* previous_layers = nullptr;
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
  return prepare(image, source, blits, pixels, width, height, pitch, rgb565,
                 output_width, output_height, output, nullptr, cache_hit);
}

bool PreparedMenuBackgroundComposer::prepare_gpu(
    const MenuBackgroundImage& image, const zimg::Texture* source,
    const std::vector<zrndr::MenuBackgroundBlit>& blits, const uint16_t* pixels, int width,
    int height, int pitch, bool rgb565, MenuBackgroundGpuLayers* layers, bool* cache_hit) {
  return prepare(image, source, blits, pixels, width, height, pitch, rgb565,
                 unsigned(std::max(0, width)), unsigned(std::max(0, height)),
                 nullptr, layers, cache_hit);
}

bool PreparedMenuBackgroundComposer::prepare(
    const MenuBackgroundImage& image, const zimg::Texture* source,
    const std::vector<zrndr::MenuBackgroundBlit>& blits, const uint16_t* pixels, int width,
    int height, int pitch, bool rgb565, unsigned output_width, unsigned output_height,
    std::vector<uint32_t>* output, MenuBackgroundGpuLayers* layers, bool* cache_hit) {
  if (cache_hit) *cache_hit = false;
  if ((!output && !layers) || !valid_menu_inputs(image, source, blits, pixels, width, height,
                                               pitch, output_width, output_height)) {
    invalidate_cache();
    return false;
  }
  // Scrolling changes blits and native pixels, so classification currently
  // misses this whole-frame cache on each scrolling frame, even with UV-only uploads.
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
                   state.previous_layers == layers &&
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
                                    output_width, output_height, output, &impl_->scratch, layers,
                                    bound_texture_width_, bound_texture_height_)) {
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
  updated.previous_layers = layers;
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
void PreparedMenuBackgroundComposer::set_bound_texture_size(unsigned width, unsigned height) {
  if (width == bound_texture_width_ && height == bound_texture_height_) return;
  bound_texture_width_ = width;
  bound_texture_height_ = height;
  impl_->valid = false;  // the cached layers carry UVs computed for the old texture size
}
unsigned PreparedMenuBackgroundComposer::thread_count() const {
  return impl_->scratch.thread_count();
}
}  // namespace platform
