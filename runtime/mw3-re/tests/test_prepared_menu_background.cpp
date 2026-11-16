#include "gamez/zimage/zimg_library.h"
#include "gamez/zrender/zrndr_blit.h"
#include "platform/prepared_menu_background.h"

#include <chrono>
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
}
}  // namespace

int main() {
  reader_rejects_unknown_format();
  reader_rejects_truncated_payload();
  compositor_replaces_only_background_pixels();
}
