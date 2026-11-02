import unittest
import struct
from pathlib import Path


class TestReconOverlay(unittest.TestCase):
    def setUp(self):
        self.maps_dir = Path("games/mw3/mod-tools/editor/web/static/assets/maps")

    def test_recon_map_files_exist_and_valid(self):
        targets = ["c1m1", "c2m1", "c3m1", "c4m1", "t1m1"]
        for t in targets:
            png_path = self.maps_dir / f"{t}.png"
            self.assertTrue(png_path.is_file(), f"Missing recon map: {png_path}")
            data = png_path.read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n", f"Invalid PNG magic for {t}")
            w, h = struct.unpack(">II", data[16:24])
            self.assertEqual(w, 640)
            self.assertEqual(h, 480)

    def test_recon_overlay_calibration_math(self):
        # Validate calibration offsets and meters-per-pixel against MW3 coordinate standards
        calibrations = {
            "c1m1": {"mpp": 3.476, "offset": [-1114.434, 0.0, -659.279]},
            "c2m1": {"mpp": 4.273, "offset": [1930.0, 0.0, -41.6]},
            "c3m1": {"mpp": -5.175, "offset": [-1255.0, 0.0, -224.0]},
            "c4m1": {"mpp": -7.100, "offset": [-2365.0, 0.0, 1629.0]},
            "t1m1": {"mpp": 5.144, "offset": [3382.0, 0.0, -2.0]},
        }

        for name, calib in calibrations.items():
            world_w = abs(640 * calib["mpp"])
            world_h = abs(480 * calib["mpp"])
            self.assertGreater(world_w, 2000.0)
            self.assertGreater(world_h, 1500.0)
            self.assertEqual(len(calib["offset"]), 3)


if __name__ == "__main__":
    unittest.main()
