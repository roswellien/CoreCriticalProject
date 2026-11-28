"""Check frozen recording validation without a game install."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from freeze import freeze, inspect_log, rank_windows
from run import sha256


class FreezeTest(unittest.TestCase):
    def test_generation_compares_bytes_from_two_fresh_profiles(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            game = root / "game"
            game.mkdir()
            recipe = root / "arena.json"
            recipe.write_text('{"map":"c4mp2","sides":[[],[]]}', encoding="utf-8")
            profiles = []

            def generate(argv, **kwargs):
                profile = Path(argv[argv.index("--write-dir") + 1])
                self.assertFalse(profile.exists())
                profiles.append(profile)
                profile.mkdir()
                setup = Path(argv[argv.index("--arena") + 1])
                output = Path(json.loads(setup.read_text(encoding="utf-8"))["out"])
                output.mkdir()
                (output / "match-7.jsonl").write_bytes(bytes([len(profiles)]))

            with (
                patch("freeze.BENCHMARK_ROOT", root),
                patch("freeze.subprocess.run", generate),
                self.assertRaisesRegex(ValueError, "differ byte for byte"),
            ):
                freeze(root / "mw3.exe", game, recipe, 7, root / "output")
            self.assertEqual(
                profiles, [root / "output" / attempt / "profile" for attempt in ("first", "second")]
            )
            self.assertFalse((root / "output" / "match-7.jsonl").exists())

    def test_archive_receipt_includes_uppercase_and_mixed_case_zbd_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            game = root / "game"
            archives = game / "zbd"
            archives.mkdir(parents=True)
            reader = archives / "READER.ZBD"
            reader.write_bytes(b"reader")
            terrain = archives / "Terrain.ZbD"
            terrain.write_bytes(b"terrain")
            (archives / "ignored.txt").write_bytes(b"ignored")
            (archives / "directory.zbd").mkdir()
            recipe = root / "arena.json"
            recipe.write_text('{"map":"c4mp2","sides":[[],[]]}', encoding="utf-8")
            executable = root / "mw3.exe"
            executable.write_bytes(b"executable")

            def generate(argv, **kwargs):
                setup = Path(argv[argv.index("--arena") + 1])
                output = Path(json.loads(setup.read_text(encoding="utf-8"))["out"])
                output.mkdir()
                (output / "match-7.jsonl").write_bytes(b"identical log")

            with (
                patch("freeze.BENCHMARK_ROOT", root),
                patch("freeze.subprocess.run", generate),
                patch("freeze.subprocess.check_output", return_value="commit\n"),
                patch("freeze.inspect_log", return_value={}),
            ):
                result = freeze(executable, game, recipe, 7, root / "output")
            self.assertEqual(
                result["game_archives"],
                {"reader.zbd": sha256(reader), "terrain.zbd": sha256(terrain)},
            )
            self.assertEqual(result["reader_zbd_sha256"], sha256(reader))

    def test_recording_shape_cadence_and_terminal_record(self):
        start = {
            "type": "start",
            "version": 2,
            "map": "c4mp2",
            "seed": 7,
            "frame_ms": 33,
            "record_every_update": True,
            "mechs": [{"side": 0}, {"side": 1}],
        }
        state = {
            "type": "state",
            "t": 0.033,
            "rounds": [],
            "beams": [],
            "mechs": [{"standing": True}, {"standing": False}],
        }
        second = dict(state, t=0.066)
        end = {"type": "end", "t": 0.066, "winner": "A", "lost": [0, 1]}
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "match.jsonl"

            def write(records):
                path.write_text(
                    "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
                )

            write([start, state, second, end])
            result = inspect_log(path, "c4mp2", 7, [1, 1])
            self.assertEqual(result["states"], 2)
            self.assertEqual(result["spacing_ms"], [33.0, 33.0])
            self.assertEqual(result["end"], end)
            boundary = dict(end, t=5.100)
            write([start, state, second, boundary])
            self.assertEqual(inspect_log(path, "c4mp2", 7, [1, 1])["end"], boundary)
            for records, reason in (
                ([dict(start, map="c3mp1"), state, second, end], "start"),
                ([dict(start, mechs=[]), state, second, end], "roster"),
                ([start, state, second], "terminal end"),
                ([start, state, second, end, end], "after the terminal"),
                ([start, state, second, dict(end, lost=[0, 2])], "end record losses"),
                ([start, state, second, dict(end, t=5.101)], "too far past the final state"),
                ([start, state, second, dict(end, t=185.0)], "too far past the final state"),
                ([start, state, dict(second, t=0.099), end], "Off-cadence"),
                ([start, state, dict(second, t=0.033), end], "Off-cadence"),
                ([start, state, dict(second, t=0.01), end], "Off-cadence"),
                ([start, state, dict(second, mechs=[]), end], "Incomplete mech state"),
            ):
                with self.subTest(reason=reason):
                    write(records)
                    with self.assertRaisesRegex(ValueError, reason):
                        inspect_log(path, "c4mp2", 7, [1, 1])

    def test_rank_windows_by_concurrent_activity(self):
        timestamps = [tick * 0.033 for tick in range(1, 3032)]
        activity = []
        for time in timestamps:
            if time < 10:
                activity.append((100, 16))
            elif 30 <= time < 60:
                activity.append((9, 12))
            else:
                activity.append((15, 2))
        windows = rank_windows(timestamps, activity)
        self.assertEqual(windows[0]["measured_start_seconds"], 30)
        self.assertEqual(windows[0]["activity"], 108)
        self.assertTrue(all(10 <= w["measured_start_seconds"] <= 70 for w in windows))


if __name__ == "__main__":
    unittest.main()
