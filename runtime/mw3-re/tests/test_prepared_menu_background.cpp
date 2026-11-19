#include "gamez/zimage/zimg_library.h"
#include "gamez/zrender/zrndr_blit.h"
#include "platform/prepared_menu_background.h"

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <condition_variable>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <exception>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

namespace {
void require(bool condition, const char* message);

template <typename Function>
void run_with_watchdog(const char* test_name, Function test) {
  std::mutex mutex;
  std::condition_variable finished;
  bool done = false;
  std::exception_ptr failure;
  std::thread test_thread([&] {
    try {
      test();
    } catch (...) {
      failure = std::current_exception();
    }
    {
      std::lock_guard<std::mutex> lock(mutex);
      done = true;
    }
    finished.notify_one();
  });

  std::unique_lock<std::mutex> lock(mutex);
  if (!finished.wait_for(lock, std::chrono::seconds(10), [&] { return done; })) {
    std::fprintf(stderr, "Timed out waiting for pool test: %s\n", test_name);
    std::fflush(stderr);
    std::_Exit(EXIT_FAILURE);
  }
  lock.unlock();
  test_thread.join();
  if (failure) std::rethrow_exception(failure);
}

struct WakeupFailure {
  std::atomic<bool> should_throw{true};
};

void fail_once_after_worker_wakeup(void* context) {
  auto* failure = static_cast<WakeupFailure*>(context);
  if (failure->should_throw.exchange(false, std::memory_order_relaxed))
    throw std::runtime_error("injected post-wakeup failure");
}

float reference_channel_value(uint16_t pixel, int index, bool rgb565) {
  if (index == 0) return float((pixel >> (rgb565 ? 11 : 10)) & 31) * (255.f / 31);
  if (index == 1)
    return float((pixel >> 5) & (rgb565 ? 63 : 31)) * (255.f / (rgb565 ? 63 : 31));
  return float(pixel & 31) * (255.f / 31);
}

uint16_t reference_rgb565(int red, int green, int blue) {
  const auto red_bits = unsigned(std::clamp(red, 0, 255) * 31 / 255);
  const auto green_bits = unsigned(std::clamp(green, 0, 255) * 63 / 255);
  const auto blue_bits = unsigned(std::clamp(blue, 0, 255) * 31 / 255);
  return uint16_t((red_bits << 11) | (green_bits << 5) | blue_bits);
}

uint32_t reference_pack(uint8_t red, uint8_t green, uint8_t blue) {
  return 0xff000000u | uint32_t(red) | uint32_t(green) << 8 | uint32_t(blue) << 16;
}

uint32_t reference_sample(const platform::MenuBackgroundImage& image, double x, double y) {
  x -= std::floor(x / image.width) * image.width;
  y -= std::floor(y / image.height) * image.height;
  const unsigned x0 = unsigned(x), y0 = unsigned(y);
  const unsigned x1 = (x0 + 1) % image.width, y1 = (y0 + 1) % image.height;
  const float tx = float(x - x0), ty = float(y - y0);
  uint8_t result[3]{};
  for (unsigned channel = 0; channel < 3; ++channel) {
    const auto pixel = [&](unsigned px, unsigned py) {
      return float(image.rgb[(size_t(py) * image.width + px) * 3 + channel]);
    };
    const float upper = pixel(x0, y0) * (1 - tx) + pixel(x1, y0) * tx;
    const float lower = pixel(x0, y1) * (1 - tx) + pixel(x1, y1) * tx;
    result[channel] = uint8_t(std::clamp(upper * (1 - ty) + lower * ty + .5f, 0.f, 255.f));
  }
  return reference_pack(result[0], result[1], result[2]);
}

std::vector<uint32_t> brute_force_compose(
    const platform::MenuBackgroundImage& image, const zimg::Texture& source,
    const std::vector<zrndr::MenuBackgroundBlit>& blits, const std::vector<uint16_t>& frame,
    unsigned output_width, unsigned output_height) {
  const int width = source.width;
  const int height = source.height;
  std::vector<int> source_x(size_t(width) * height, -1);
  std::vector<int> source_y(size_t(width) * height, -1);
  for (const auto& blit : blits) {
    for (int row = 0; row < blit.height; ++row) {
      const int destination_y = blit.destination_y + row;
      const int background_y = blit.source_y + row;
      if (destination_y < 0 || destination_y >= height || background_y < 0 ||
          background_y >= source.height)
        continue;
      for (int column = 0; column < blit.width; ++column) {
        const int destination_x = blit.destination_x + column;
        const int background_x = blit.source_x + column;
        if (destination_x >= 0 && destination_x < width && background_x >= 0 &&
            background_x < source.width) {
          const size_t index = size_t(destination_y) * width + destination_x;
          source_x[index] = background_x;
          source_y[index] = background_y;
        }
      }
    }
  }

  const size_t frame_size = size_t(width) * height;
  std::vector<uint8_t> type(frame_size, 0);
  std::vector<std::array<float, 3>> rendered(frame_size), background(frame_size),
      overlay(frame_size);
  std::vector<std::array<float, 3>> correction(frame_size, {1.f, 1.f, 1.f});
  const auto* background_pixels = static_cast<const uint16_t*>(source.pixels);
  for (int y = 0; y < height; ++y) {
    for (int x = 0; x < width; ++x) {
      const size_t index = size_t(y) * width + x;
      if (source_x[index] < 0 || source_y[index] < 0) continue;
      const uint16_t actual_pixel = frame[index];
      const uint16_t expected_pixel =
          background_pixels[size_t(source_y[index]) * source.width_again + source_x[index]];
      bool is_background = actual_pixel == expected_pixel;
      std::array<float, 3> ratio{};
      for (int channel = 0; channel < 3; ++channel) {
        rendered[index][channel] = reference_channel_value(actual_pixel, channel, true);
        background[index][channel] = reference_channel_value(expected_pixel, channel, true);
        ratio[channel] = (rendered[index][channel] + 8.f) / (background[index][channel] + 8.f);
      }
      if (!is_background) {
        const float minimum = std::min({ratio[0], ratio[1], ratio[2]});
        const float maximum = std::max({ratio[0], ratio[1], ratio[2]});
        is_background = minimum > .12f && maximum < 2.5f && maximum <= minimum * 1.45f;
      }
      if (is_background) {
        type[index] = 1;
        continue;
      }
      const float red_difference = rendered[index][0] - background[index][0];
      const float green_difference = rendered[index][1] - background[index][1];
      const float blue_difference = rendered[index][2] - background[index][2];
      if (green_difference > 6.f && red_difference > -10.f && blue_difference > -10.f &&
          red_difference < green_difference * .6f && blue_difference < green_difference * .6f) {
        type[index] = 2;
        for (int channel = 0; channel < 3; ++channel)
          overlay[index][channel] = rendered[index][channel] - background[index][channel];
      }
    }
  }

  for (int y = 0; y < height; ++y) {
    for (int x = 0; x < width; ++x) {
      const size_t index = size_t(y) * width + x;
      if (type[index] != 1) continue;
      std::array<float, 3> rendered_sum{}, background_sum{};
      for (int dy = -2; dy <= 2; ++dy) {
        const int neighbor_y = y + dy;
        if (neighbor_y < 0 || neighbor_y >= height) continue;
        for (int dx = -2; dx <= 2; ++dx) {
          const int neighbor_x = x + dx;
          if (neighbor_x < 0 || neighbor_x >= width) continue;
          const size_t neighbor = size_t(neighbor_y) * width + neighbor_x;
          if (type[neighbor] != 1) continue;
          for (int channel = 0; channel < 3; ++channel) {
            rendered_sum[channel] += rendered[neighbor][channel];
            background_sum[channel] += background[neighbor][channel];
          }
        }
      }
      for (int channel = 0; channel < 3; ++channel)
        correction[index][channel] =
            (rendered_sum[channel] + 4.f) / (background_sum[channel] + 4.f);
    }
  }
  require(std::find(type.begin(), type.end(), 2) != type.end(),
          "Reference fixture did not classify any added overlay pixels");
  if (output_width < unsigned(width) && output_height < unsigned(height)) {
    const size_t sampled_background = size_t(width) + 1;
    const size_t unsampled_neighbor = size_t(2) * width + 2;
    require(type[sampled_background] == 1 && type[unsampled_neighbor] == 1 &&
                std::abs(correction[sampled_background][0] - 1.f) > .01f,
            "Downscaled fixture lacks an unsampled background neighbor that affects sampled gain");
  }

  std::vector<uint32_t> result(size_t(output_width) * output_height);
  for (unsigned output_y = 0; output_y < output_height; ++output_y) {
    const double frame_y = (double(output_y) + .5) * height / output_height;
    const int y = std::min(height - 1, int(frame_y));
    const double sub_y = frame_y - y;
    for (unsigned output_x = 0; output_x < output_width; ++output_x) {
      const double frame_x = (double(output_x) + .5) * width / output_width;
      const int x = std::min(width - 1, int(frame_x));
      const size_t index = size_t(y) * width + x;
      const uint16_t pixel = frame[index];
      if (source_x[index] >= 0 && type[index] != 0) {
        const double sample_y =
            (source_y[index] + sub_y) * double(image.height) / image.source_height;
        const double sub_x = frame_x - x;
        const double sample_x =
            (source_x[index] + sub_x) * double(image.width) / image.source_width;
        const uint32_t sampled = reference_sample(image, sample_x, sample_y);
        uint8_t channels[3] = {uint8_t(sampled), uint8_t(sampled >> 8), uint8_t(sampled >> 16)};
        for (int channel = 0; channel < 3; ++channel) {
          const float gain = type[index] == 1 ? correction[index][channel] : 1.f;
          channels[channel] = uint8_t(std::clamp(
              channels[channel] * gain + overlay[index][channel] + .5f, 0.f, 255.f));
        }
        result[size_t(output_y) * output_width + output_x] =
            reference_pack(channels[0], channels[1], channels[2]);
      } else {
        result[size_t(output_y) * output_width + output_x] = reference_pack(
            uint8_t(reference_channel_value(pixel, 0, true) + .5f),
            uint8_t(reference_channel_value(pixel, 1, true) + .5f),
            uint8_t(reference_channel_value(pixel, 2, true) + .5f));
      }
    }
  }
  return result;
}

void compositor_matches_independent_reference_for_all_output_scales() {
  struct Dimensions {
    int width;
    int height;
    unsigned output_width;
    unsigned output_height;
    const char* description;
  };
  const Dimensions cases[] = {{12, 10, 6, 5, "half-size output"},
                              {10, 2160, 5, 1080, "1080p-capped output"},
                              {12, 10, 12, 10, "frame-sized output"},
                              {12, 10, 18, 15, "larger-than-frame output"}};
  for (const auto& test_case : cases) {
    platform::MenuBackgroundImage image;
    image.width = unsigned(test_case.width);
    image.height = unsigned(test_case.height);
    image.source_width = image.width;
    image.source_height = image.height;
    image.rgb.resize(size_t(image.width) * image.height * 3);
    for (int y = 0; y < test_case.height; ++y) {
      for (int x = 0; x < test_case.width; ++x) {
        const size_t index = (size_t(y) * image.width + x) * 3;
        image.rgb[index] = uint8_t((x * 13 + y * 3) % 220 + 20);
        image.rgb[index + 1] = uint8_t((x * 5 + y * 11) % 220 + 20);
        image.rgb[index + 2] = uint8_t((x * 7 + y * 5) % 220 + 20);
      }
    }
    std::vector<uint16_t> source_pixels(size_t(test_case.width) * test_case.height);
    std::vector<uint16_t> frame(source_pixels.size());
    std::vector<uint8_t> touched(frame.size(), 0);
    for (int y = 0; y < test_case.height; ++y) {
      for (int x = 0; x < test_case.width; ++x) {
        const size_t index = size_t(y) * test_case.width + x;
        const int red = 70 + (x * 7 + y * 3) % 90;
        const int green = 75 + (x * 5 + y * 7) % 90;
        const int blue = 65 + (x * 3 + y * 5) % 90;
        source_pixels[index] = reference_rgb565(red, green, blue);
        const bool overlay = x == test_case.width - 2 && y == test_case.height - 2;
        const float gain = !overlay && x % 4 == 2 && y % 4 == 2 ? 1.35f : 1.10f;
        int actual_red = int(reference_channel_value(source_pixels[index], 0, true) * gain + .5f);
        int actual_green = int(reference_channel_value(source_pixels[index], 1, true) * gain + .5f);
        int actual_blue = int(reference_channel_value(source_pixels[index], 2, true) * gain + .5f);
        if (overlay) {
          actual_red = int(reference_channel_value(source_pixels[index], 0, true) + .5f);
          actual_green = int(reference_channel_value(source_pixels[index], 1, true) + 60.5f);
          actual_blue = int(reference_channel_value(source_pixels[index], 2, true) + .5f);
        }
        frame[index] = reference_rgb565(actual_red, actual_green, actual_blue);
      }
    }
    zimg::Texture source{};
    source.width = test_case.width;
    source.height = test_case.height;
    source.width_again = test_case.width;
    source.pixels = source_pixels.data();
    const std::vector<zrndr::MenuBackgroundBlit> blits{
        {0, 0, 0, 0, test_case.width, test_case.height}};
    for (unsigned y = 0; y < test_case.output_height; ++y) {
      const int source_y = std::min(test_case.height - 1,
          int((double(y) + .5) * test_case.height / test_case.output_height));
      for (unsigned x = 0; x < test_case.output_width; ++x) {
        const int source_x = std::min(test_case.width - 1,
            int((double(x) + .5) * test_case.width / test_case.output_width));
        touched[size_t(source_y) * test_case.width + source_x] = 1;
      }
    }
    const size_t untouched = size_t(std::min(2, test_case.height - 1)) * test_case.width +
                             std::min(2, test_case.width - 1);
    if (test_case.output_width < unsigned(test_case.width) &&
        test_case.output_height < unsigned(test_case.height)) {
      require(!touched[untouched], "Downscaled fixture unexpectedly sampled every frame pixel");
      require(touched[size_t(test_case.width) + 1] && frame[untouched] != source_pixels[untouched],
              "Downscaled fixture lacks a sampled background pixel beside an unsampled pixel");
    }
    std::vector<uint32_t> actual;
    const auto expected = brute_force_compose(image, source, blits, frame, test_case.output_width,
                                               test_case.output_height);
    require(platform::compose_menu_background(image, &source, blits, frame.data(),
                                              test_case.width, test_case.height,
                                              test_case.width * 2, true, test_case.output_width,
                                              test_case.output_height, &actual),
            "Production compositor rejected a reference comparison case");
    require(actual == expected, test_case.description);
  }
}

void require(bool condition, const char* message) {
  if (!condition) throw std::runtime_error(message);
}

void write_word(std::ofstream& output, uint32_t value) {
  const char bytes[4] = {char(value), char(value >> 8), char(value >> 16), char(value >> 24)};
  output.write(bytes, sizeof bytes);
}

std::filesystem::path fixture_path() {
  return std::filesystem::temp_directory_path() /
         ("mw3-menu-background-" + std::to_string(
             std::chrono::steady_clock::now().time_since_epoch().count()) + ".mwhd");
}

void write_image(const std::filesystem::path& path, const char* magic = "MWHDBG1\0") {
  std::ofstream output(path, std::ios::binary);
  output.write(magic, 8);
  write_word(output, 4);
  write_word(output, 2);
  write_word(output, 2);
  write_word(output, 1);
  for (uint8_t value = 0; value < 24; ++value) output.put(char(value * 10));
}

void reader_rejects_unknown_format() {
  const auto path = fixture_path();
  write_image(path, "BADBG1\0");
  bool rejected = false;
  try {
    (void)platform::load_menu_background(path);
  } catch (const std::runtime_error&) {
    rejected = true;
  }
  std::filesystem::remove(path);
  require(rejected, "Unknown menu background magic was accepted");
}

void reader_rejects_truncated_payload() {
  const auto path = fixture_path();
  write_image(path);
  std::filesystem::resize_file(path, 25);
  bool rejected = false;
  try {
    (void)platform::load_menu_background(path);
  } catch (const std::runtime_error&) {
    rejected = true;
  }
  std::filesystem::remove(path);
  require(rejected, "Truncated menu background payload was accepted");
}

void compositor_replaces_only_background_pixels() {
  const auto path = fixture_path();
  write_image(path);
  const auto image = platform::load_menu_background(path);
  std::filesystem::remove(path);

  std::vector<uint16_t> source_pixels{0xf800, 0x07e0};
  zimg::Texture source{};
  source.width = 2;
  source.height = 1;
  source.width_again = 2;
  source.pixels = source_pixels.data();
  std::vector<uint16_t> frame{0xf800, 0xffff};
  const std::vector<zrndr::MenuBackgroundBlit> blits{{0, 0, 0, 0, 2, 1}};
  std::vector<uint32_t> output;
  require(platform::compose_menu_background(image, &source, blits, frame.data(), 2, 1, 4, true,
                                            4, 2, &output),
          "Menu background composition was not available for a valid source");
  require(output.size() == 8, "Menu background output dimensions changed");
  require(output[0] != 0xff0000ffu && output[0] != 0xff00ff00u,
          "HD background sample was not used for a matching source pixel");
  require(output[3] == 0xffffffffu && output[7] == 0xffffffffu,
          "Native menu artwork changed where it differs from the background");

  require(platform::compose_menu_background(image, &source, blits, frame.data(), 2, 1, 4, true,
                                            1, 1, &output),
          "Menu background composition rejected a smaller output size");
  require(output.size() == 1 && output[0] == 0xffffffffu,
          "Downscaled menu output was not completely written within its requested size");
}

void compositor_rejects_null_or_unreadable_sources_before_access() {
  platform::MenuBackgroundImage image;
  image.width = 1;
  image.height = 1;
  image.source_width = 1;
  image.source_height = 1;
  image.rgb.resize(3);
  const std::vector<zrndr::MenuBackgroundBlit> blits{{0, 0, 0, 0, 1, 1}};
  const std::vector<zrndr::MenuBackgroundBlit> no_blits;
  const uint16_t pixel = 0;
  std::vector<uint32_t> output;
  require(!platform::compose_menu_background(image, nullptr, blits, &pixel, 1, 1, 2, true, 1, 1,
                                             &output),
          "Menu background composition accepted a null source");

  const auto* stale_source = reinterpret_cast<const zimg::Texture*>(uintptr_t{1});
  require(!platform::compose_menu_background(image, stale_source, no_blits, &pixel, 1, 1, 2, true,
                                             1, 1, &output),
          "Empty menu blits accessed an unreadable source instead of failing");
}

void cached_menu_texture_action_recreates_texture_on_cache_hit() {
  using Action = platform::PreparedMenuTextureAction;
  require(platform::prepared_menu_texture_action(true, false, 0, 0, 4, 2) == Action::kCreate,
          "A cache hit reused a missing menu texture instead of recreating it");
  require(platform::prepared_menu_texture_action(true, true, 2, 1, 4, 2) == Action::kCreate,
          "A cache hit reused a menu texture with stale dimensions");
  require(platform::prepared_menu_texture_action(true, true, 4, 2, 4, 2) == Action::kReuse,
          "A matching menu texture was needlessly uploaded on a cache hit");
  require(platform::prepared_menu_texture_action(false, true, 4, 2, 4, 2) == Action::kUpdate,
          "A changed composition did not request a texture upload");
}

void compositor_writes_every_pixel_at_the_capped_height() {
  constexpr unsigned source_width = 4;
  constexpr unsigned source_height = 2160;
  const unsigned window_width = source_width;
  const unsigned window_height = source_height;
  const double fit = std::min({double(window_width) / source_width,
                               double(window_height) / source_height, 4.5});
  const double compose_scale = std::min(fit, 1080.0 / source_height);
  const unsigned output_width = std::max(1u, unsigned(std::lround(source_width * compose_scale)));
  const unsigned output_height = std::max(1u, unsigned(std::lround(source_height * compose_scale)));
  require(output_width == 2 && output_height == 1080,
          "The height cap no longer preserves the uniform fit scale");

  platform::MenuBackgroundImage image;
  image.width = source_width;
  image.height = source_height;
  image.source_width = source_width;
  image.source_height = source_height;
  image.rgb.resize(size_t(image.width) * image.height * 3);
  std::vector<uint16_t> source_pixels(size_t(source_width) * source_height, 0);
  zimg::Texture source{};
  source.width = int(source_width);
  source.height = int(source_height);
  source.width_again = int(source_width);
  source.pixels = source_pixels.data();
  std::vector<uint16_t> frame(size_t(source_width) * source_height, 0xffff);
  const std::vector<zrndr::MenuBackgroundBlit> blits{
      {0, 0, 0, 0, int(source_width), int(source_height)}};
  std::vector<uint32_t> output(size_t(output_width) * output_height, 0x12345678u);

  require(platform::compose_menu_background(image, &source, blits, frame.data(),
                                            int(source_width), int(source_height),
                                            int(source_width * 2), true, output_width,
                                            output_height, &output),
          "Menu background composition rejected a cap-sized output smaller than the source");
  require(output.size() == size_t(output_width) * output_height,
          "Capped output size changed during composition");
  for (uint32_t pixel : output)
    require(pixel == 0xffffffffu, "Capped output left a pixel unwritten or wrote out of bounds");
}

void cached_composition_matches_fresh_and_invalidates_inputs() {
  const auto path = fixture_path();
  write_image(path);
  const auto image = platform::load_menu_background(path);
  std::filesystem::remove(path);

  std::vector<uint16_t> source_pixels{0xf800, 0x07e0};
  zimg::Texture source{};
  source.width = 2;
  source.height = 1;
  source.width_again = 2;
  source.pixels = source_pixels.data();
  std::vector<uint16_t> frame{0xf800, 0xffff};
  std::vector<zrndr::MenuBackgroundBlit> blits{{0, 0, 0, 0, 2, 1}};
  platform::PreparedMenuBackgroundComposer composer;
  std::vector<uint32_t> reused, reference;
  bool cache_hit = false;
  require(composer.compose(image, &source, blits, frame.data(), 2, 1, 4, true, 4, 2,
                           &reused, &cache_hit) && !cache_hit,
          "Initial cached composition did not compose");
  const unsigned thread_count = composer.thread_count();
  require(platform::compose_menu_background(image, &source, blits, frame.data(), 2, 1, 4, true,
                                            4, 2, &reference) && reused == reference,
          "Reusable scratch composition changed output from the fresh path");

  require(composer.compose(image, &source, blits, frame.data(), 2, 1, 4, true, 4, 2,
                           &reused, &cache_hit) && cache_hit,
          "Unchanged menu frame missed the composition cache");
  require(reused == reference, "Cache hit output differed from a fresh composition");

  require(!composer.compose(image, nullptr, blits, frame.data(), 2, 1, 4, true, 4, 2,
                            &reused, &cache_hit) && !cache_hit,
          "Cache validation accepted a null menu source");
  require(composer.compose(image, &source, blits, frame.data(), 2, 1, 4, true, 4, 2,
                           &reused, &cache_hit) && !cache_hit,
          "Rejected null source left the composition cache valid");

  const auto* stale_source = reinterpret_cast<const zimg::Texture*>(uintptr_t{1});
  require(!composer.compose(image, stale_source, {}, frame.data(), 2, 1, 4, true, 4, 2,
                            &reused, &cache_hit) && !cache_hit,
          "Cache validation accessed a stale source with empty menu blits");
  require(composer.compose(image, &source, blits, frame.data(), 2, 1, 4, true, 4, 2,
                           &reused, &cache_hit) && !cache_hit,
          "Rejected empty menu blits left the composition cache valid");

  frame[1] ^= 0x001f;
  require(composer.compose(image, &source, blits, frame.data(), 2, 1, 4, true, 4, 2,
                           &reused, &cache_hit) && !cache_hit,
          "Changed frame pixels did not invalidate the cache");
  require(platform::compose_menu_background(image, &source, blits, frame.data(), 2, 1, 4, true,
                                            4, 2, &reference) && reused == reference,
          "Scratch reuse changed output after frame pixels changed");

  blits[0].source_x = 1;
  require(composer.compose(image, &source, blits, frame.data(), 2, 1, 4, true, 4, 2,
                           &reused, &cache_hit) && !cache_hit,
          "Changed menu background blits did not invalidate the cache");
  require(platform::compose_menu_background(image, &source, blits, frame.data(), 2, 1, 4, true,
                                            4, 2, &reference) && reused == reference,
          "Scratch reuse changed output after menu blits changed");
  require(composer.thread_count() == thread_count && thread_count <= 8,
          "Menu background worker count changed between compositions");
}

void worker_pool_propagates_exceptions_and_recovers_for_the_next_run() {
  platform::detail::MenuBackgroundWorkers workers(2);
  require(workers.thread_count() == 3, "Test worker pool did not create the requested workers");

  bool worker_exception_reached_caller = false;
  try {
    workers.run(512, [](unsigned first_row, unsigned) {
      if (first_row != 0) throw std::runtime_error("injected worker failure");
    });
  } catch (const std::runtime_error& error) {
    worker_exception_reached_caller = std::string(error.what()) == "injected worker failure";
  }
  require(worker_exception_reached_caller,
          "Worker exception was not rethrown on the caller thread");

  std::atomic<unsigned> completed_rows{0};
  workers.run(512, [&completed_rows](unsigned first_row, unsigned last_row) {
    completed_rows.fetch_add(last_row - first_row, std::memory_order_relaxed);
  });
  require(completed_rows == 512, "Worker pool did not complete a run after a worker exception");

  bool caller_exception_reached_caller = false;
  std::atomic<unsigned> caller_failure_worker_rows{0};
  try {
    workers.run(512, [&caller_failure_worker_rows](unsigned first_row, unsigned last_row) {
      if (first_row == 0) throw std::runtime_error("injected caller failure");
      caller_failure_worker_rows.fetch_add(last_row - first_row, std::memory_order_relaxed);
    });
  } catch (const std::runtime_error& error) {
    caller_exception_reached_caller = std::string(error.what()) == "injected caller failure";
  }
  require(caller_exception_reached_caller,
          "Caller chunk exception was not rethrown after workers finished");
  require(caller_failure_worker_rows > 0,
          "Caller failure returned before the worker chunks finished");

  completed_rows = 0;
  workers.run(512, [&completed_rows](unsigned first_row, unsigned last_row) {
    completed_rows.fetch_add(last_row - first_row, std::memory_order_relaxed);
  });
  require(completed_rows == 512, "Worker pool did not complete a run after a caller exception");
}

void worker_pool_recovers_after_failure_immediately_after_wakeup() {
  WakeupFailure injected_failure;
  platform::detail::MenuBackgroundWorkers workers(2, fail_once_after_worker_wakeup,
                                                   &injected_failure);
  std::atomic<unsigned> completed_rows{0};
  bool failure_reached_caller = false;
  try {
    workers.run(512, [&completed_rows](unsigned first_row, unsigned last_row) {
      completed_rows.fetch_add(last_row - first_row, std::memory_order_relaxed);
    });
  } catch (const std::runtime_error& error) {
    failure_reached_caller = std::string(error.what()) == "injected post-wakeup failure";
  }
  require(failure_reached_caller, "Post-wakeup worker failure was not rethrown on the caller");

  for (unsigned iteration = 0; iteration < 5; ++iteration) {
    completed_rows = 0;
    workers.run(512, [&completed_rows](unsigned first_row, unsigned last_row) {
      completed_rows.fetch_add(last_row - first_row, std::memory_order_relaxed);
    });
    require(completed_rows == 512,
            "Pool did not account for exactly one full run after a post-wakeup failure");
  }
}

void worker_pool_handles_single_worker_empty_and_inline_ranges() {
  platform::detail::MenuBackgroundWorkers workers(1);
  require(workers.thread_count() == 2, "Single-worker pool created the wrong thread count");
  std::atomic<unsigned> completed_rows{0};
  workers.run(256, [&completed_rows](unsigned first_row, unsigned last_row) {
    completed_rows.fetch_add(last_row - first_row, std::memory_order_relaxed);
  });
  require(completed_rows == 256, "Single worker did not cover its full assigned range");

  bool saw_empty_range = false;
  workers.run(0, [&saw_empty_range](unsigned first_row, unsigned last_row) {
    saw_empty_range = first_row == 0 && last_row == 0;
  });
  require(saw_empty_range, "Zero-row run did not use the inline empty range");

  unsigned inline_first = 1, inline_last = 0;
  workers.run(64, [&inline_first, &inline_last](unsigned first_row, unsigned last_row) {
    inline_first = first_row;
    inline_last = last_row;
  });
  require(inline_first == 0 && inline_last == 64,
          "Short run was partitioned instead of using the inline range");
}

void menu_background_output_cap_preserves_fit_and_layer_rect() {
  const auto capped = platform::menu_background_output_size(640, 480, 3440, 1440, 1080);
  const auto uncapped = platform::menu_background_output_size(640, 480, 3440, 1440, 0);
  require(capped.fit_scale == 3.0 && capped.compose_scale == 2.25 && capped.width == 1440 &&
              capped.height == 1080,
          "Ultrawide composition was not capped at 1080 with its aspect preserved");
  require(uncapped.fit_scale == 3.0 && uncapped.compose_scale == 3.0 && uncapped.width == 1920 &&
              uncapped.height == 1440,
          "Uncapped ultrawide composition did not use the full frame fit");

  const auto capped_rect = platform::menu_background_layer_rect(640, 480);
  const auto uncapped_rect = platform::menu_background_layer_rect(640, 480);
  require(capped_rect.x == uncapped_rect.x && capped_rect.y == uncapped_rect.y &&
              capped_rect.width == uncapped_rect.width &&
              capped_rect.height == uncapped_rect.height &&
              capped_rect.x == 0.f && capped_rect.y == 0.f && capped_rect.width == 640.f &&
              capped_rect.height == 480.f,
          "Composition cap changed the layer's frame-sized destination rectangle");

  const auto smaller_window = platform::menu_background_output_size(640, 480, 1280, 720, 1080);
  require(smaller_window.fit_scale == 1.5 && smaller_window.compose_scale == 1.5 &&
              smaller_window.width == 960 && smaller_window.height == 720,
          "Smaller-window output did not follow the full fit");
}

void gpu_cover_and_uv_geometry() {
  struct CoverCase {
    int width, height;
    float x, y, covered_width, covered_height;
  };
  const CoverCase cases[] = {{3440, 1440, 0, -570, 3440, 2580},
                             {1920, 1080, 0, -180, 1920, 1440},
                             {640, 480, 0, 0, 640, 480},
                             {5120, 1440, 0, -1200, 5120, 3840},
                             {480, 640, -186.66667f, 0, 853.33333f, 640}};
  for (const auto& entry : cases) {
    const auto rect = platform::menu_background_cover_rect(640, 480, entry.width, entry.height);
    require(std::abs(rect.x - entry.x) < .001f && std::abs(rect.y - entry.y) < .001f &&
                std::abs(rect.width - entry.covered_width) < .001f &&
                std::abs(rect.height - entry.covered_height) < .001f,
            "Menu cover no longer uniformly fills the output and centers the crop");
    const double scale = std::min(double(entry.width) / 640, double(entry.height) / 480);
    const platform::MenuBackgroundLayerRect fitted{
        float((entry.width - 640 * scale) * .5), float((entry.height - 480 * scale) * .5),
        float(640 * scale), float(480 * scale)};
    const platform::MenuBackgroundUvRect native_uv{.9f, .75f, 1.4f, 1.75f};
    const auto extended = platform::menu_background_extend_uv(native_uv, fitted, rect);
    // Re-evaluate the covering quad at the native frame corners: source
    // correspondence must survive while the repeating image fills the margins.
    const double left = extended.u0 + (double(fitted.x) - rect.x) / rect.width *
                                         (double(extended.u1) - extended.u0);
    const double top = extended.v0 + (double(fitted.y) - rect.y) / rect.height *
                                        (double(extended.v1) - extended.v0);
    const double right = extended.u0 + (double(fitted.x) + fitted.width - rect.x) / rect.width *
                                          (double(extended.u1) - extended.u0);
    const double bottom = extended.v0 + (double(fitted.y) + fitted.height - rect.y) / rect.height *
                                           (double(extended.v1) - extended.v0);
    require(std::abs(left - native_uv.u0) < .000001 && std::abs(top - native_uv.v0) < .000001 &&
                std::abs(right - native_uv.u1) < .000001 && std::abs(bottom - native_uv.v1) < .000001,
            "Menu cover extension moved the native scroll mapping or control corrections");
  }
  for (unsigned master_width : {1280u, 1920u}) {
    const auto covered_master = platform::menu_background_cover_rect(int(master_width), 480, 3440, 1440);
    const float expected_left = master_width == 1280 ? -200.f : -1160.f;
    require(covered_master.x == expected_left && covered_master.y == 0 &&
                covered_master.width == master_width * 3.f && covered_master.height == 1440,
            "Wide menu masters no longer cover ultrawide output at a uniform scale");
    platform::MenuBackgroundImage image;
    image.source_width = master_width;
    image.source_height = 480;
    image.width = master_width * 3;
    image.height = 1440;
    for (int64_t offset : {int64_t(0), int64_t(master_width - 1),
                           int64_t(master_width + 13), int64_t(master_width) * 5 + 13,
                           int64_t(-1)}) {
      const auto uv = platform::menu_background_uv_rect(image, offset, 479, 640, 480);
      const int64_t wrapped = (offset % master_width + master_width) % master_width;
      const double expected_u = double(wrapped) / master_width + .5 / image.width;
      require(std::abs(uv.u0 - expected_u) < .000001 &&
                  std::abs(uv.u1 - uv.u0 - 640.0 / master_width) < .000001 &&
                  std::abs(uv.v0 - (479.0 / 480 + .5 / image.height)) < .000001 &&
                  std::abs(uv.v1 - uv.v0 - 1.0) < .000001,
              "Menu UV phase, half-texel convention or native-image wrap changed");
    }
  }
  bool rejected = false;
  try {
    platform::menu_background_cover_rect(0, 480, 1920, 1080);
  } catch (const std::invalid_argument&) {
    rejected = true;
  }
  require(rejected, "Menu cover accepted an invalid required dimension");
  rejected = false;
  try {
    platform::menu_background_uv_rect({}, 0, 0, 640, 480);
  } catch (const std::invalid_argument&) {
    rejected = true;
  }
  require(rejected, "Menu UV rectangle accepted an invalid image");
}

void wide_master_prepares_from_game_texture_across_wrap() {
    constexpr int game_width = 1280, source_height = 960;
    constexpr int frame_width = 16, frame_height = 4;
    constexpr uint16_t original = uint16_t((12 << 11) | (25 << 5) | 12);
    std::vector<uint16_t> source_pixels(size_t(game_width) * source_height, original);
    std::vector<uint16_t> frame(frame_width * frame_height, original);
    zimg::Texture source{};
    source.width = source.width_again = game_width;
    source.height = source_height;
    source.pixels = source_pixels.data();
    for (unsigned master_width : {1280u, 1920u}) {
        // A 1920-wide source canvas is exercised through prepare(), not just the UV helper.
        platform::MenuBackgroundImage image{
            master_width, source_height, master_width, source_height, {}};
        image.rgb.resize(size_t(image.width) * image.height * 3);
        for (unsigned y = 0; y < image.height; ++y)
            for (unsigned x = 0; x < image.width; ++x) {
                const size_t at = (size_t(y) * image.width + x) * 3;
                image.rgb[at] = uint8_t(x / 8);
                image.rgb[at + 1] = uint8_t(y / 4);
                image.rgb[at + 2] = 80;
            }
        platform::PreparedMenuBackgroundComposer gpu_composer, cpu_composer;
        platform::MenuBackgroundGpuLayers layers;
        std::vector<uint32_t> composed;
        uint64_t revision = 0;
        double previous_phase = 0;
        int previous_offset = 0;
        for (int offset : {0, 900, 1273, 1284, 1297, 2564}) {
            const int wrapped = offset % game_width;
            const int first_width = std::min(frame_width, game_width - wrapped);
            std::vector<zrndr::MenuBackgroundBlit> blits{{0, 0, wrapped, 958, first_width, 2},
                                                         {0, 2, wrapped, 0, first_width, 2}};
            if (first_width < frame_width) {
                blits.push_back({first_width, 0, 0, 958, frame_width - first_width, 2});
                blits.push_back({first_width, 2, 0, 0, frame_width - first_width, 2});
            }
            bool cache_hit = true;
            require(gpu_composer.prepare_gpu(image, &source, blits, frame.data(), frame_width,
                                             frame_height, frame_width * 2, true, &layers,
                                             &cache_hit) &&
                        layers.status == platform::MenuBackgroundGpuStatus::kReady && !cache_hit,
                    "Wide master rejected a real game-width prepare or a multi-pixel wrap step");
            require(!revision || layers.revision == revision,
                    "Scrolling unchanged classifications uploaded new GPU maps");
            revision = layers.revision;
            const double phase = (double(layers.uv.u0) - .5 / image.width) * master_width;
            const double expected_phase = double(wrapped) * master_width / game_width;
            require(std::abs(phase - expected_phase) < .001 &&
                        std::abs((layers.uv.u1 - layers.uv.u0) * master_width -
                                 double(frame_width) * master_width / game_width) < .001,
                    "Wide master did not scale both scroll origin and view span from game pixels");
            if (offset == 1284)
                require(std::abs(phase + master_width - previous_phase -
                                 double(offset - previous_offset) * master_width / game_width) <
                            .001,
                        "Multi-pixel scroll jumped at the master's wrap boundary");
            previous_offset = offset;
            previous_phase = phase;
            require(cpu_composer.compose(image, &source, blits, frame.data(), frame_width,
                                         frame_height, frame_width * 2, true, frame_width,
                                         frame_height, &composed),
                    "Wide master CPU preparation failed instead of retaining fallback");
            for (int x = 0; x < frame_width; ++x) {
                const double source_x = (wrapped + x + .5) * master_width / game_width;
                const double wrapped_x =
                    source_x - std::floor(source_x / master_width) * master_width;
                const unsigned left = unsigned(wrapped_x);
                const unsigned right = (left + 1) % master_width;
                const double fraction = wrapped_x - left;
                const int expected_red =
                    int((left / 8) * (1 - fraction) + (right / 8) * fraction + .5);
                require(
                    std::abs(int(composed[size_t(x)] & 255) - expected_red) <= 1,
                    "CPU and GPU master coordinates differ beyond 8-bit quantization tolerance");
            }
            if (offset == 900 && master_width == 1920)
                require(phase > 1280 && (composed[0] & 255) > 160,
                        "Wide master never exposed the extra 640 source columns");
        }
    }
}

void upload_downsampling_averages_source_footprints() {
    platform::MenuBackgroundImage image{18, 12, 6, 4, std::vector<uint8_t>(18 * 12 * 3)};
    for (unsigned y = 0; y < image.height; ++y)
        for (unsigned x = 0; x < image.width; ++x)
            for (unsigned channel_index = 0; channel_index < 3; ++channel_index)
                image.rgb[(size_t(y) * image.width + x) * 3 + channel_index] =
                    (x + y) % 2 ? 255 : 0;
    const auto saved = image.rgb;
    const auto filtered = platform::menu_background_upload_image(image, 6);
    require(filtered.width == 9 && filtered.height == 6 && filtered.source_width == 6 &&
                filtered.source_height == 4 && image.rgb == saved,
            "Upload downsampling changed the full CPU source or canvas dimensions");
    require(std::all_of(filtered.rgb.begin(), filtered.rgb.end(),
                        [](uint8_t value) { return value == 128; }),
            "Menu upload point-sampled a checkerboard instead of filtering its footprint");
    const auto fractional = platform::menu_background_upload_image(image, 5);
    require(fractional.width == 7 && fractional.height == 5 &&
                std::all_of(fractional.rgb.begin(), fractional.rgb.end(),
                            [](uint8_t value) { return value >= 120 && value <= 135; }),
            "Menu upload lost fractional edge coverage while downsampling");
    require(platform::menu_background_upload_image(image, 12).rgb == saved,
            "Menu upload changed an image that needed no downsampling");
    // A zero or unknown window height (minimised or not yet sized) must not cap the texture at a
    // couple of pixels for the whole session: use the display height, else keep the full image.
    require(platform::menu_background_upload_height(480, 1080, 960) == 960,
            "A sized window did not give twice its height");
    require(platform::menu_background_upload_height(0, 1080, 960) == 2160,
            "A zero-height window did not fall back to the display height");
    require(platform::menu_background_upload_height(-1, 0, 960) == 960,
            "An unknown window and display did not keep the full image");
    require(platform::menu_background_upload_image(
                    image, platform::menu_background_upload_height(0, 0, image.height))
                    .rgb == saved,
            "A zero-height window filtered the image down instead of uploading it whole");
    // The half texel belongs to the texture the GPU samples (the filtered copy), not the image.
    const auto full_uv = platform::menu_background_uv_rect(image, 0, 0, 6, 4);
    const auto bound_uv = platform::menu_background_uv_rect(image, 0, 0, 6, 4, 6, 4, 9, 6);
    require(std::fabs(full_uv.u0 - .5f / 18.f) < 1e-6f && std::fabs(bound_uv.u0 - .5f / 9.f) < 1e-6f &&
                std::fabs(bound_uv.v0 - .5f / 6.f) < 1e-6f,
            "The UV half texel did not follow the bound texture's size");
}

void gpu_maps_share_classification_gain_cache_and_fallback() {
  platform::MenuBackgroundImage image{16, 16, 8, 8, std::vector<uint8_t>(16 * 16 * 3, 80)};
  constexpr uint16_t original = uint16_t((12 << 11) | (25 << 5) | 12);
  constexpr uint16_t dimmed = uint16_t((8 << 11) | (16 << 5) | 8);
  constexpr uint16_t glow = uint16_t((12 << 11) | (45 << 5) | 12);
  std::vector<uint16_t> source_pixels(64, original), frame(64, dimmed);
  zimg::Texture source{};
  source.width = source.height = source.width_again = 8;
  source.pixels = source_pixels.data();
  frame[0] = original;
  frame[9] = glow;
  frame[63] = 0xf81f;
  std::vector<zrndr::MenuBackgroundBlit> blits{
      {0, 0, 7, 6, 1, 2}, {1, 0, 0, 6, 7, 2},
      {0, 2, 7, 0, 1, 6}, {1, 2, 0, 0, 7, 6}};
  platform::PreparedMenuBackgroundComposer composer;
  platform::MenuBackgroundGpuLayers layers;
  bool hit = false;
  const auto prepare = [&] {
    return composer.prepare_gpu(image, &source, blits, frame.data(), 8, 8, 16, true, &layers, &hit);
  };
  require(prepare() && !hit && layers.status == platform::MenuBackgroundGpuStatus::kReady,
          "Wrapped GPU maps rejected attenuation and nonnegative added light");
  require(layers.overlay.size() == 64 && layers.gain.size() == 64 && layers.added.size() == 64,
          "GPU maps did not stay at frame resolution");
  require(layers.overlay[63] == 0xffff00ff && layers.overlay[0] == 0 &&
              layers.added[9] == 0x00005100 && layers.gain[9] == 0xffffffff &&
              layers.gain[0] != 0xffffffff,
          "GPU maps lost native artwork, added-light classification or the 5x5 gain");
  const auto expected_uv = platform::menu_background_uv_rect(image, 7, 6, 8, 8);
  require(layers.uv.u0 == expected_uv.u0 && layers.uv.v0 == expected_uv.v0,
          "GPU maps lost the game's wrapped scroll origin");
  // Telling the composer the bound texture is a smaller filtered copy moves the half texel and
  // drops the cached layers computed for the old size.
  composer.set_bound_texture_size(8, 8);
  require(prepare() && !hit, "A bound texture size change did not invalidate the cached layers");
  const auto bound_uv = platform::menu_background_uv_rect(image, 7, 6, 8, 8, 8, 8, 8, 8);
  require(layers.uv.u0 == bound_uv.u0 && layers.uv.v0 == bound_uv.v0 && layers.uv.u0 != expected_uv.u0,
          "The GPU UV half texel ignored the bound texture size");
  composer.set_bound_texture_size(0, 0);
  require(prepare() && layers.uv.u0 == expected_uv.u0,
          "Clearing the bound texture size did not restore the image's half texel");
  const auto* map_storage = layers.gain.data();
  require(prepare() && hit && layers.gain.data() == map_storage,
          "Unchanged GPU maps missed the cache or replaced retained storage");
  frame[0] = dimmed;
  require(prepare() && !hit, "GPU map cache ignored a changed frame");
  blits[0].source_x = 6;
  require(prepare() && !hit && layers.status == platform::MenuBackgroundGpuStatus::kMapping,
          "GPU maps accepted pieces that are not one wrapped source rectangle");
  require(prepare() && hit, "An unsupported map was unnecessarily reclassified on a cache hit");
  blits = {{0, 0, 0, 0, 8, 8}};
  std::fill(frame.begin(), frame.end(), uint16_t((14 << 11) | (29 << 5) | 14));
  require(prepare() && layers.status == platform::MenuBackgroundGpuStatus::kGain,
          "GPU maps silently clamped amplification that requires the CPU fallback");
  std::fill(frame.begin(), frame.end(), original);
  frame[9] = uint16_t((11 << 11) | (45 << 5) | 12);
  require(prepare() && layers.status == platform::MenuBackgroundGpuStatus::kAdded,
          "GPU maps silently discarded a negative added-light channel");
  std::fill(frame.begin(), frame.end(), original);
  require(prepare() && layers.status == platform::MenuBackgroundGpuStatus::kReady,
          "GPU map preparation failed to recover after an unsupported frame");
  source.alpha = reinterpret_cast<uint8_t*>(frame.data());
  require(!prepare() && !hit, "A GPU cache hit bypassed validation of an invalid source");
  source.alpha = nullptr;
  require(prepare() && !hit, "Invalid source rejection did not invalidate the GPU map cache");
  const uint64_t previous_revision = layers.revision;
  blits = {{0, 0, 7, 6, 1, 2}, {1, 0, 0, 6, 7, 2},
           {0, 2, 7, 0, 1, 6}, {1, 2, 0, 0, 7, 6}};
  require(prepare() && !hit && layers.status == platform::MenuBackgroundGpuStatus::kReady &&
              layers.revision == previous_revision && layers.uv.u0 == expected_uv.u0,
          "A UV-only scroll change requested an unnecessary GPU map upload");
}
}  // namespace

int main() {
  reader_rejects_unknown_format();
  reader_rejects_truncated_payload();
  compositor_replaces_only_background_pixels();
  compositor_rejects_null_or_unreadable_sources_before_access();
  compositor_matches_independent_reference_for_all_output_scales();
  cached_menu_texture_action_recreates_texture_on_cache_hit();
  compositor_writes_every_pixel_at_the_capped_height();
  cached_composition_matches_fresh_and_invalidates_inputs();
  run_with_watchdog("worker failures and recovery", [] {
    worker_pool_propagates_exceptions_and_recovers_for_the_next_run();
  });
  run_with_watchdog("post-wakeup failure recovery", [] {
    worker_pool_recovers_after_failure_immediately_after_wakeup();
  });
  run_with_watchdog("single worker and inline ranges", [] {
    worker_pool_handles_single_worker_empty_and_inline_ranges();
  });
  menu_background_output_cap_preserves_fit_and_layer_rect();
  gpu_cover_and_uv_geometry();
  wide_master_prepares_from_game_texture_across_wrap();
  upload_downsampling_averages_source_footprints();
  gpu_maps_share_classification_gain_cache_and_fallback();
}
