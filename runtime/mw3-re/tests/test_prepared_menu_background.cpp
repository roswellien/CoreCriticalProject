#include "gamez/zimage/zimg_library.h"
#include "gamez/zrender/zrndr_blit.h"
#include "platform/prepared_menu_background.h"

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
void require(bool condition, const char* message);

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
  try {
    workers.run(512, [](unsigned first_row, unsigned) {
      if (first_row == 0) throw std::runtime_error("injected caller failure");
    });
  } catch (const std::runtime_error& error) {
    caller_exception_reached_caller = std::string(error.what()) == "injected caller failure";
  }
  require(caller_exception_reached_caller,
          "Caller chunk exception was not rethrown after workers finished");

  completed_rows = 0;
  workers.run(512, [&completed_rows](unsigned first_row, unsigned last_row) {
    completed_rows.fetch_add(last_row - first_row, std::memory_order_relaxed);
  });
  require(completed_rows == 512, "Worker pool did not complete a run after a caller exception");
}
}  // namespace

int main() {
  reader_rejects_unknown_format();
  reader_rejects_truncated_payload();
  compositor_replaces_only_background_pixels();
  compositor_matches_independent_reference_for_all_output_scales();
  cached_menu_texture_action_recreates_texture_on_cache_hit();
  compositor_writes_every_pixel_at_the_capped_height();
  cached_composition_matches_fresh_and_invalidates_inputs();
  worker_pool_propagates_exceptions_and_recovers_for_the_next_run();
}
