#include "crt/msvc_rand.h"

namespace crt {

namespace {
// MSVCRT keeps one seed per thread; the game draws from its main thread only.
uint32_t g_seed = 1;
// Ours (#485): the drawn frame's own state, and whether it is in use.
uint32_t g_drawn_frame_seed = 1;
bool g_in_drawn_frame = false;
}  // namespace

std::optional<uint32_t>& rand_fixed_seed() {
  static std::optional<uint32_t> s;
  return s;
}

void msvc_srand(uint32_t seed) {
  g_seed = rand_fixed_seed() ? *rand_fixed_seed() : seed;
  g_drawn_frame_seed = g_seed;
}

int msvc_rand() {
  uint32_t& state = g_in_drawn_frame ? g_drawn_frame_seed : g_seed;
  state = state * 214013u + 2531011u;
  return static_cast<int>((state >> 16) & 0x7fff);
}

uint32_t msvc_rand_state() { return g_seed; }

DrawnFrameRandom::DrawnFrameRandom() : was_drawn_frame_(g_in_drawn_frame) { g_in_drawn_frame = true; }
DrawnFrameRandom::~DrawnFrameRandom() { g_in_drawn_frame = was_drawn_frame_; }

}  // namespace crt
