"""Unit tests for MW3 Environment, Atmosphere, Weather, and MW34ENV1 binary encoder."""

import math
import struct
import sys
import unittest
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT))

from editor.core.environment import (
    ENV_FIELDS,
    EnvironmentConfig,
    encode_mw34env1,
    get_environment_preset,
    solve_time_of_day,
)


class TestEnvironmentBuilder(unittest.TestCase):
    def test_solve_time_of_day_noon(self):
        noon = solve_time_of_day(12.0)
        self.assertAlmostEqual(noon.elevation, 75.0, delta=2.0)
        self.assertAlmostEqual(noon.azimuth, 180.0, delta=2.0)
        self.assertGreater(noon.sun_strength, 1.0)
        self.assertGreater(noon.ambient_strength, 0.3)

    def test_solve_time_of_day_sunset(self):
        sunset = solve_time_of_day(18.0)
        self.assertAlmostEqual(sunset.elevation, 1.0, delta=2.0)
        self.assertAlmostEqual(sunset.azimuth, 270.0, delta=2.0)
        self.assertEqual(sunset.preset_name, "sunset")

    def test_solve_time_of_day_night(self):
        night = solve_time_of_day(0.0)  # Midnight
        self.assertLess(night.sun_strength, 0.25)
        self.assertLess(night.ambient_strength, 0.15)

    def test_presets_exist_and_apply(self):
        presets = ["dawn", "morning", "noon", "sunset", "dusk", "night", "storm", "dust", "smog", "volcanic", "interior"]
        for p in presets:
            cfg = get_environment_preset(p)
            self.assertEqual(cfg.preset_name, p)
            if p == "interior":
                self.assertTrue(cfg.is_interior)
                self.assertEqual(cfg.sun_strength, 0.0)
            elif p == "storm":
                self.assertGreater(cfg.rain_intensity, 0.8)
                self.assertTrue(cfg.has_lightning)
            elif p == "volcanic":
                self.assertGreater(cfg.volcanic_ash, 0.5)

    def test_encode_mw34env1_binary_format(self):
        cfg = get_environment_preset("storm")
        data = encode_mw34env1("c1m1", cfg)

        self.assertTrue(data.startswith(b"MW34ENV1"))

        ptr = 8
        count = struct.unpack_from("<I", data, ptr)[0]
        self.assertEqual(count, 1)
        ptr += 4

        ident_len = struct.unpack_from("<I", data, ptr)[0]
        ptr += 4
        ident = data[ptr : ptr + ident_len].decode("ascii")
        ptr += ident_len
        self.assertEqual(ident, "c1m1")

        # Unpack each field in ENV_FIELDS order
        cfg_dict = cfg.to_dict()
        for name, f_count, low, high in ENV_FIELDS:
            if f_count == 0:
                val = struct.unpack_from("<I", data, ptr)[0]
                ptr += 4
                self.assertEqual(bool(val), bool(cfg_dict[name]), f"Mismatch for {name}")
            elif f_count == 1:
                val = struct.unpack_from("<f", data, ptr)[0]
                ptr += 4
                self.assertAlmostEqual(val, float(cfg_dict[name]), places=2, msg=f"Mismatch for {name}")
            else:
                vals = list(struct.unpack_from("<" + "f" * f_count, data, ptr))
                ptr += 4 * f_count
                for i in range(f_count):
                    self.assertAlmostEqual(vals[i], float(cfg_dict[name][i]), places=2, msg=f"Mismatch for {name}[{i}]")

        lights_count = struct.unpack_from("<I", data, ptr)[0]
        self.assertEqual(lights_count, 0)


if __name__ == "__main__":
    unittest.main()
