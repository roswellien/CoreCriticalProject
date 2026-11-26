#include "check.h"
#include "crt/msvc_rand.h"

// MSVCRT's first values with the default seed of 1 (documented, and the values every
// Visual C++ program of the era produced without calling srand).
TEST(msvc_rand_default_seed_sequence) {
  crt::msvc_srand(1);
  EXPECT(crt::msvc_rand() == 41);
  EXPECT(crt::msvc_rand() == 18467);
  EXPECT(crt::msvc_rand() == 6334);
  EXPECT(crt::msvc_rand() == 26500);
  EXPECT(crt::msvc_rand() == 19169);
}

// #485: draws inside a DrawnFrameRandom never move the simulation's sequence,
// however many there are, and without one the sequence is MSVCRT's as before.
TEST(msvc_rand_drawn_frame_draws_leave_the_simulation_sequence) {
  crt::msvc_srand(1);
  EXPECT(crt::msvc_rand() == 41);
  {
    crt::DrawnFrameRandom drawn_frame;
    for (int i = 0; i < 1000; ++i) crt::msvc_rand();
  }
  EXPECT(crt::msvc_rand() == 18467);
  EXPECT(crt::msvc_rand() == 6334);
}

TEST(msvc_rand_drawn_frame_state_is_seeded_with_the_simulation) {
  crt::msvc_srand(1);
  crt::DrawnFrameRandom drawn_frame;
  EXPECT(crt::msvc_rand() == 41);
  {
    crt::DrawnFrameRandom nested;  // leaving a nested one keeps the drawn frame's state
  }
  EXPECT(crt::msvc_rand() == 18467);
}

#include <cmath>

#include "crt/msvc_math.h"

TEST(msvc_ftol_truncates_and_wraps) {
  EXPECT(crt::msvc_ftol(2.9) == 2);
  EXPECT(crt::msvc_ftol(-2.9) == -2);
  EXPECT(crt::msvc_ftol(3e9) == -1294967296);
  EXPECT(crt::msvc_ftol(1e20) == 0);
  EXPECT(crt::msvc_ftol(std::nan("")) == 0);
  EXPECT(crt::msvc_ftol64(-1e20) == INT64_MIN);
}
