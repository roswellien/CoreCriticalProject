"""Pilot selection/hash/timing checks with authored ISO/AVI fixtures only."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[name] = module
    return module


video = load("video_probe", ROOT / "tools/asset-inventory/video_probe.py")
fixtures = load("pilot_video_fixtures", ROOT / "tests/test_asset_video.py")
prepare = load("prepare_video_pilot", ROOT / "tools/asset-inventory/prepare_video_pilot.py")
validate = load("validate_video_pilot", ROOT / "tools/asset-inventory/validate_video_pilot.py")


class VideoPilotTests(unittest.TestCase):
    def test_exact_iso_span_and_changed_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "authored.iso"
            data = fixtures.iso_fixture()
            path.write_bytes(data)
            iso_hash = hashlib.sha256(data).hexdigest()
            payload = fixtures.avi_fixture()
            asset_hash = hashlib.sha256(payload).hexdigest()
            entry, extracted = prepare.extract_selected(path, iso_hash, "VIDEO/TEST.AVI;1", asset_hash)
            self.assertEqual(extracted, payload)
            self.assertEqual(entry["offset"], 22 * 2048)
            with self.assertRaisesRegex(ValueError, "ISO identity"):
                prepare.extract_selected(path, "0" * 64, "VIDEO/TEST.AVI;1", asset_hash)
            with self.assertRaisesRegex(ValueError, "file identity"):
                prepare.extract_selected(path, iso_hash, "VIDEO/TEST.AVI;1", "0" * 64)
            with self.assertRaisesRegex(ValueError, "one requested"):
                prepare.extract_selected(path, iso_hash, "VIDEO/MISSING.AVI;1", asset_hash)

    def test_unsupported_rate_and_audio_rejected(self):
        payload = bytearray(fixtures.avi_fixture())
        with self.assertRaisesRegex(ValueError, "15 fps"):
            prepare.validate_contract(bytes(payload), 0, 1)
        pos = payload.index(b"vids")
        struct.pack_into("<I", payload, pos + 24, 15)
        with self.assertRaisesRegex(ValueError, "8-bit PCM"):
            prepare.validate_contract(bytes(payload), 0, 1)

    def test_timestamp_grid_allows_mux_rounding_but_not_missing_holds(self):
        timestamps = [f"{i / 15:.3f}" for i in range(75)]
        self.assertLess(validate.verify_grid(timestamps), 0.001)
        with self.assertRaisesRegex(ValueError, "display frames"):
            validate.verify_grid(timestamps[:-1])
        timestamps[20] = "2.0"
        with self.assertRaisesRegex(ValueError, "depart"):
            validate.verify_grid(timestamps)

    def test_audio_grid_rejects_offset_gap_and_short_excerpt(self):
        frames = [{"nb_samples": 22050, "best_effort_timestamp_time": str(i)} for i in range(5)]
        self.assertEqual(validate.verify_audio_grid(frames), 0)
        with self.assertRaisesRegex(ValueError, "sample count"):
            validate.verify_audio_grid(frames[:-1])
        frames[0]["best_effort_timestamp_time"] = "0.1"
        with self.assertRaisesRegex(ValueError, "timestamps"):
            validate.verify_audio_grid(frames)
        frames[0]["best_effort_timestamp_time"] = "0"
        frames[3]["best_effort_timestamp_time"] = "3.1"
        with self.assertRaisesRegex(ValueError, "timestamps"):
            validate.verify_audio_grid(frames)


if __name__ == "__main__":
    unittest.main()
