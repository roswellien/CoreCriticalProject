"""Exercise strict diagnostics and their exclusion from scored suites."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from compare import compare as compare_scored
from strict_compare import compare


class StrictComparisonTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.fixture = {
            "version": 1,
            "mode": "strict",
            "valid": True,
            "scene_id": "fixture",
            "log_sha256": "a" * 64,
            "source_sha": "same-build",
            "width": 640,
            "height": 480,
            "pixel_hash_kind": "fnv1a64-swapchain-bgra8",
            "expected_ticks": 3,
            "frames": [
                {"tick": index, "time_seconds": 10 + index / 8, "pixel_hash": str(index) * 16}
                for index in range(3)
            ],
        }

    def write_fixture(self, name, document):
        directory = self.root / name
        directory.mkdir()
        path = directory / "strict.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def test_accepts_matching_tick_hashes(self):
        first = self.write_fixture("first", self.fixture)
        repeat = self.write_fixture("repeat", copy.deepcopy(self.fixture))
        self.assertEqual(compare(first, repeat.parent), (0, "All 3 strict ticks match"))

    def test_reports_first_differing_frame(self):
        first = self.write_fixture("first", self.fixture)
        different = copy.deepcopy(self.fixture)
        different["frames"][1]["pixel_hash"] = "f" * 16
        different["frames"][2]["pixel_hash"] = "f" * 16
        code, message = compare(first, self.write_fixture("different", different))
        self.assertEqual(code, 1)
        self.assertIn("First differing tick 1", message)

    def test_reports_first_missing_tick_and_rejects_invalid_run(self):
        first = self.write_fixture("first", self.fixture)
        shorter = copy.deepcopy(self.fixture)
        shorter["expected_ticks"] = 2
        shorter["frames"].pop()
        code, message = compare(first, self.write_fixture("shorter", shorter))
        self.assertEqual(code, 1)
        self.assertIn("First differing tick 2", message)
        shorter.update(valid=False, failure={"tick": 2, "reason": "timed out"})
        with self.assertRaisesRegex(ValueError, "timed out"):
            compare(first, self.write_fixture("failed", shorter))

    def test_scored_comparator_rejects_strict_file_and_directory(self):
        strict = self.write_fixture("first", self.fixture)
        for argument in (strict, strict.parent):
            with (
                self.subTest(argument=argument),
                self.assertRaisesRegex(ValueError, "strict diagnostics are unscored"),
            ):
                compare_scored([argument, self.root / "B1", self.root / "B2", self.root / "A2"])


if __name__ == "__main__":
    unittest.main()
