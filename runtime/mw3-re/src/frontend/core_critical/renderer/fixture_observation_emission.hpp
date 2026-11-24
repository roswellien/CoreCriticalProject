#pragma once

namespace cc_mw3_re {

// Fixture emission owns fog[3]; tint weight is carried independently in mode.z.
inline void apply_fixture_observation_emission(float (&fog)[4], float intensity) {
  fog[3] = 1.f + intensity;
}

} // namespace cc_mw3_re
