// Checks for how the renderer stores and reports textures (#518). Everything
// here is pure code with no Vulkan device, so it runs on any machine.
#include <cstdint>
#include <cstdio>
#include <optional>
#include <string>
#include <vector>

#include "frontend/core_critical/renderer/texture_memory_report.hpp"

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

} // namespace

int main() {
  check_memory_line_totals();
  check_memory_line_sizes();
  if (g_failures) {
    std::fprintf(stderr, "mw3texture_checks: %d failure(s)\n", g_failures);
    return 1;
  }
  std::printf("mw3texture_checks: all checks passed\n");
  return 0;
}
