// Checks for how the renderer stores and reports textures (#518). Everything
// here is pure code with no Vulkan device, so it runs on any machine.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <optional>
#include <string>
#include <vector>

#include "frontend/core_critical/renderer/resource_timing.hpp"
#include "frontend/core_critical/renderer/texture_memory_report.hpp"
#include "frontend/core_critical/renderer/texture_staging.hpp"

namespace {

int g_failures = 0;

void check(bool condition, const char *what) {
  if (condition)
    return;
  std::fprintf(stderr, "TEST FAILURE: %s\n", what);
  ++g_failures;
}

void check_equal(const std::string &actual, const std::string &expected, const char *what) {
  if (actual == expected)
    return;
  std::fprintf(stderr, "TEST FAILURE: %s\n  expected: %s\n  actual:   %s\n", what,
               expected.c_str(), actual.c_str());
  ++g_failures;
}

using mw34::vkscene::DriverFigures;
using mw34::vkscene::TextureMemoryRow;
using mw34::vkscene::TextureSource;
constexpr std::uint64_t kMiB = 1024ULL * 1024ULL;

void check_memory_line_totals() {
  const std::vector<TextureMemoryRow> rows{
      {TextureSource::guest, 256, 256, 256 * 256 * 4, false},
      {TextureSource::guest, 256, 256, 256 * 256 * 2, true},
      {TextureSource::prepared_skin, 512, 512, 512 * 512 * 4, false},
      {TextureSource::normal, 1024, 512, 1024 * 512 * 4, false},
      // The parallax height images arrive as one total with no size.
      {TextureSource::height, 0, 0, 3 * kMiB / 2, false},
  };
  const std::string sources =
      "textures 4.8 MiB in 4, 16-bit 0.1 MiB; guest 0.3, skin 1.0, normal 2.0, canvas 0.0, "
      "height 1.5 MiB; top: 1024x512 n=1 2.0 MiB, 512x512 n=1 1.0 MiB, 256x256 n=2 0.3 MiB";
  check_equal(mw34::vkscene::texture_memory_line("mission preload", rows, 8 * kMiB,
                                                 DriverFigures{3072 * kMiB, 6144 * kMiB}),
              "mw3: texture memory (mission preload): tracked 8.0 MiB, driver usage 3072.0 of "
              "budget 6144.0 MiB; " +
                  sources,
              "Memory line totals, sources or sizes with driver figures");
  check_equal(mw34::vkscene::texture_memory_line("periodic", rows, 8 * kMiB, std::nullopt),
              "mw3: texture memory (periodic): tracked 8.0 MiB, driver figures unavailable; " +
                  sources,
              "Memory line without driver figures");
}

void check_memory_line_sizes() {
  check_equal(mw34::vkscene::texture_memory_line("empty", {}, 0, std::nullopt),
              "mw3: texture memory (empty): tracked 0.0 MiB, driver figures unavailable; "
              "textures 0.0 MiB in 0, 16-bit 0.0 MiB; guest 0.0, skin 0.0, normal 0.0, "
              "canvas 0.0, height 0.0 MiB; top: none",
              "Memory line with no textures");
  // Ten sizes of equal total: only the eight largest sizes are listed, larger first.
  std::vector<TextureMemoryRow> rows;
  for (unsigned edge = 1; edge <= 10; ++edge)
    rows.push_back({TextureSource::guest, edge, edge, kMiB, false});
  const auto line = mw34::vkscene::texture_memory_line("ties", rows, 0, std::nullopt);
  check(line.find("top: 10x10 n=1 1.0 MiB, 9x9 n=1 1.0 MiB,") != std::string::npos,
        "Equal size totals are not listed largest size first");
  check(line.find("3x3 n=1 1.0 MiB") != std::string::npos &&
            line.find("2x2 n=1") == std::string::npos,
        "The size list is not cut to the eight largest");
}

// The periodic memory line's gate: nothing while timing is off, the first
// report at once, then one per interval.
void check_periodic_gate() {
  using std::chrono::seconds;
  const std::chrono::steady_clock::time_point start{};
  mw34::timing::PeriodicReportGate off;
  check(!off.should_report(false, start, seconds(3)), "The gate reported with timing off");
  mw34::timing::PeriodicReportGate gate;
  check(gate.should_report(true, start, seconds(3)), "The gate held back the first report");
  check(!gate.should_report(true, start + seconds(2), seconds(3)),
        "The gate reported again inside the interval");
  check(gate.should_report(true, start + seconds(3), seconds(3)),
        "The gate held back a report once the interval passed");
  check(!gate.should_report(true, start + seconds(5), seconds(3)),
        "The interval did not restart at the last report");
}

namespace staging = mw34::texture_staging;
using staging::Pack16;

// The game's bit replication of an n-bit channel (gamez/zvideo/zvid_ddd3d.cpp, expand).
unsigned replicate(unsigned value, unsigned bits) {
  unsigned widened = 0;
  unsigned filled = 0;
  while (filled < 8) {
    widened = widened << bits | value;
    filled += bits;
  }
  return (widened >> (filled - 8)) & 0xff;
}
std::uint32_t texel(unsigned red, unsigned green, unsigned blue, unsigned alpha) {
  return red | green << 8 | blue << 16 | alpha << 24;
}

// Every 16-bit value of one format, widened one way into RGBA8, is recognized
// as that format and packs back to its own 16-bit value.
void check_round_trip(Pack16 format, const char *what, std::vector<std::uint32_t> rgba,
                      const std::vector<std::uint16_t> &expected) {
  check(staging::exact_pack16(rgba.data(), rgba.size(), staging::kAllPack16) == format, what);
  std::vector<std::uint16_t> packed(rgba.size());
  staging::pack16(reinterpret_cast<unsigned char *>(packed.data()), rgba.data(), rgba.size(),
                  format);
  check(packed == expected, what);
}

void check_exact_formats() {
  std::vector<std::uint16_t> r5g6b5, a1r5g5b5, b4g4r4a4;
  std::vector<std::uint32_t> r5g6b5_replicated, r5g6b5_rounded, a1r5g5b5_replicated,
      a1r5g5b5_rounded, b4g4r4a4_widened;
  for (unsigned value = 0; value < 65536; ++value) {
    const unsigned red5 = value >> 11, green6 = (value >> 5) & 63, blue5 = value & 31;
    r5g6b5.push_back(std::uint16_t(value));
    r5g6b5_replicated.push_back(
        texel(replicate(red5, 5), replicate(green6, 6), replicate(blue5, 5), 255));
    r5g6b5_rounded.push_back(staging::expand(std::uint16_t(value), 0));

    const unsigned alpha1 = value >> 15, red = (value >> 10) & 31, green = (value >> 5) & 31,
                   blue = value & 31;
    a1r5g5b5.push_back(std::uint16_t(value));
    a1r5g5b5_replicated.push_back(texel(replicate(red, 5), replicate(green, 5),
                                        replicate(blue, 5), alpha1 ? 255 : 0));
    a1r5g5b5_rounded.push_back(staging::expand(std::uint16_t(value), 1));

    // The game's ARGB4444 value, stored on the card as B4G4R4A4.
    const unsigned alpha4 = value >> 12, red4 = (value >> 8) & 15, green4 = (value >> 4) & 15,
                   blue4 = value & 15;
    b4g4r4a4_widened.push_back(staging::expand(std::uint16_t(value), 2));
    b4g4r4a4.push_back(std::uint16_t(blue4 << 12 | green4 << 8 | red4 << 4 | alpha4));
  }
  check_round_trip(Pack16::r5g6b5, "R5G6B5 widened by bit replication", r5g6b5_replicated,
                   r5g6b5);
  check_round_trip(Pack16::r5g6b5, "R5G6B5 widened by rounding down", r5g6b5_rounded, r5g6b5);
  check_round_trip(Pack16::a1r5g5b5, "A1R5G5B5 widened by bit replication",
                   a1r5g5b5_replicated, a1r5g5b5);
  check_round_trip(Pack16::a1r5g5b5, "A1R5G5B5 widened by rounding down", a1r5g5b5_rounded,
                   a1r5g5b5);
  check_round_trip(Pack16::b4g4r4a4, "ARGB4444 widened into B4G4R4A4", b4g4r4a4_widened,
                   b4g4r4a4);

  // One byte no format holds makes the whole texture stay RGBA8.
  auto off_by_one = r5g6b5_replicated;
  off_by_one[12345] = (off_by_one[12345] & ~0xffu) | 1u;
  check(staging::exact_pack16(off_by_one.data(), off_by_one.size(), staging::kAllPack16) ==
            Pack16::none,
        "A red value of 1 did not keep the texture at RGBA8");
  auto alpha_254 = a1r5g5b5_replicated;
  alpha_254[54321] = (alpha_254[54321] & 0x00ffffffu) | 254u << 24;
  check(staging::exact_pack16(alpha_254.data(), alpha_254.size(), staging::kAllPack16) ==
            Pack16::none,
        "An alpha of 254 did not keep the texture at RGBA8");
  // Two widenings mixed in one texture are not the same 16-bit data.
  auto mixed = r5g6b5_replicated;
  mixed.insert(mixed.end(), r5g6b5_rounded.begin(), r5g6b5_rounded.end());
  check(staging::exact_pack16(mixed.data(), mixed.size(), staging::kAllPack16) == Pack16::none,
        "Texels from two different widenings counted as one 16-bit format");

  // Opaque black and white fit every format: the mask decides which is used.
  const std::vector<std::uint32_t> black_white{texel(0, 0, 0, 255), texel(255, 255, 255, 255)};
  const auto pick = [&](unsigned allowed) {
    return staging::exact_pack16(black_white.data(), black_white.size(), allowed);
  };
  check(pick(staging::kAllPack16) == Pack16::r5g6b5, "R5G6B5 is not preferred");
  check(pick(staging::kAllPack16 & ~staging::pack16_bit(Pack16::r5g6b5)) == Pack16::a1r5g5b5,
        "A1R5G5B5 is not next when R5G6B5 is off");
  check(pick(staging::pack16_bit(Pack16::b4g4r4a4)) == Pack16::b4g4r4a4,
        "B4G4R4A4 alone was not used");
  check(pick(0) == Pack16::none, "A texture was narrowed with every format off");
}

void check_staging_sizes() {
  check(staging::staged_bytes(1, 1, Pack16::r5g6b5) == 4, "A 1x1 16-bit texture is not 4 bytes");
  check(staging::staged_bytes(3, 1, Pack16::b4g4r4a4) == 8,
        "A 3x1 16-bit texture is not rounded up to 8 bytes");
  check(staging::staged_bytes(4, 4, Pack16::a1r5g5b5) == 32, "A 4x4 16-bit texture is not 32");
  check(staging::staged_bytes(2, 2, Pack16::none) == 16, "A 2x2 RGBA8 texture is not 16");

  // stage_rgba8 copies RGBA8 as it is and packs 16-bit textures.
  const std::vector<std::uint32_t> rgba{texel(255, 0, 0, 255), texel(0, 255, 0, 255)};
  std::array<unsigned char, 8> copied{};
  staging::stage_rgba8(copied.data(), rgba.data(), rgba.size(), Pack16::none);
  check(std::memcmp(copied.data(), rgba.data(), 8) == 0, "RGBA8 staging changed the texels");
  std::array<std::uint16_t, 2> packed{};
  staging::stage_rgba8(reinterpret_cast<unsigned char *>(packed.data()), rgba.data(),
                       rgba.size(), Pack16::r5g6b5);
  check(packed[0] == 0xf800 && packed[1] == 0x07e0,
        "R5G6B5 staging put red or green in the wrong bits");
}

void check_sources_and_rule() {
  check(staging::may_pack16(TextureSource::guest) &&
            staging::may_pack16(TextureSource::prepared_skin),
        "Guest surfaces or skins may not be stored at 16 bits");
  check(!staging::may_pack16(TextureSource::normal) &&
            !staging::may_pack16(TextureSource::canvas) &&
            !staging::may_pack16(TextureSource::height),
        "A normal map, canvas or height image may be stored at 16 bits");

  const std::vector<std::uint32_t> opaque{texel(0, 0, 0, 255), texel(255, 255, 255, 255)};
  const std::vector<std::uint32_t> cutout{texel(0, 0, 0, 0), texel(255, 255, 255, 255)};
  const std::vector<std::uint32_t> eight_bit{texel(1, 2, 3, 255)};
  const auto choose = [](staging::Pack16Rule rule, bool has_image, Pack16 current, bool eligible,
                         const std::vector<std::uint32_t> &rgba) {
    return staging::choose_pack16(rule, has_image, current, eligible, rgba.data(), rgba.size(),
                                  staging::kAllPack16);
  };
  const auto is = [](staging::Pack16Choice choice, Pack16 pack, bool recreate) {
    return choice.pack == pack && choice.recreate == recreate;
  };
  using staging::Pack16Rule;
  for (const auto rule : {Pack16Rule::from_content, Pack16Rule::keep_or_widen}) {
    check(is(choose(rule, false, Pack16::none, true, opaque), Pack16::r5g6b5, false),
          "A new image with exact content was not made 16-bit");
    check(is(choose(rule, false, Pack16::none, true, eight_bit), Pack16::none, false),
          "A new image with 8-bit content was not made RGBA8");
    check(is(choose(rule, false, Pack16::none, false, opaque), Pack16::none, false),
          "A new image from a source that may not narrow was made 16-bit");
  }
  // At a preload the format follows the content, in either direction.
  check(is(choose(Pack16Rule::from_content, true, Pack16::none, true, opaque), Pack16::r5g6b5,
           true),
        "Preload kept an RGBA8 image for new exact content");
  check(is(choose(Pack16Rule::from_content, true, Pack16::r5g6b5, true, opaque),
           Pack16::r5g6b5, false),
        "Preload remade an image whose format already fits");
  check(is(choose(Pack16Rule::from_content, true, Pack16::r5g6b5, true, cutout),
           Pack16::a1r5g5b5, true),
        "Preload did not move an image to the format its new content needs");
  check(is(choose(Pack16Rule::from_content, true, Pack16::a1r5g5b5, true, eight_bit),
           Pack16::none, true),
        "Preload kept a 16-bit image for 8-bit content");
  check(is(choose(Pack16Rule::from_content, true, Pack16::r5g6b5, false, opaque), Pack16::none,
           true),
        "Preload kept a 16-bit image for a source that may not narrow");
  // During play an image never narrows and never changes 16-bit format.
  check(is(choose(Pack16Rule::keep_or_widen, true, Pack16::none, true, opaque), Pack16::none,
           false),
        "Play narrowed an RGBA8 image");
  check(is(choose(Pack16Rule::keep_or_widen, true, Pack16::r5g6b5, true, opaque),
           Pack16::r5g6b5, false),
        "Play remade a 16-bit image whose content still fits");
  check(is(choose(Pack16Rule::keep_or_widen, true, Pack16::r5g6b5, true, cutout), Pack16::none,
           true),
        "Play moved an image to another 16-bit format instead of RGBA8");
  check(is(choose(Pack16Rule::keep_or_widen, true, Pack16::b4g4r4a4, true, eight_bit),
           Pack16::none, true),
        "Play kept a 16-bit image for 8-bit content");
  check(is(choose(Pack16Rule::keep_or_widen, true, Pack16::r5g6b5, false, opaque), Pack16::none,
           true),
        "Play kept a 16-bit image for a source that may not narrow");
}

} // namespace

int main() {
  check_memory_line_totals();
  check_memory_line_sizes();
  check_periodic_gate();
  check_exact_formats();
  check_staging_sizes();
  check_sources_and_rule();
  if (g_failures) {
    std::fprintf(stderr, "mw3texture_checks: %d failure(s)\n", g_failures);
    return 1;
  }
  std::printf("mw3texture_checks: all checks passed\n");
  return 0;
}
