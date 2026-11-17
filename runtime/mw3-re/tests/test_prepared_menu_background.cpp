#include "gamez/zimage/zimg_library.h"
#include "gamez/zrender/zrndr_blit.h"
#include "platform/prepared_menu_background.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
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
}  // namespace

int main() {
  reader_rejects_unknown_format();
  reader_rejects_truncated_payload();
  compositor_replaces_only_background_pixels();
  cached_menu_texture_action_recreates_texture_on_cache_hit();
  compositor_writes_every_pixel_at_the_capped_height();
  cached_composition_matches_fresh_and_invalidates_inputs();
}
