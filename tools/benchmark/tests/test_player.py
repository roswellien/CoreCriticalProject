"""Check the launcher's player benchmark coordinator without a game install."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import player
from run import sha256

SCENES = ("c1mp1", "c2mp2", "c3mp1", "c4mp2")


def fake_freeze(calls):
    """Stand in for freeze(): write a log and receipt the way the real one does."""

    def freeze(executable, game, recipe, seed, output, allowed_root):
        assert output.is_relative_to(allowed_root)
        output.mkdir(parents=True)
        log = output / f"match-{seed}.jsonl"
        log.write_text(f'{{"recipe":"{recipe.name}"}}\n', encoding="utf-8")
        (output / "freeze.json").write_text(json.dumps({"sha256": sha256(log)}), encoding="utf-8")
        calls.append(recipe.name)

    return freeze


def definition(shipped_hash="0" * 64):
    return {
        "version": 1,
        "scenes": [
            {"id": scene, "log": "x", "log_sha256": shipped_hash, "measured_seconds": 30}
            for scene in SCENES
        ],
    }


class ReferenceTest(unittest.TestCase):
    def test_first_run_generates_then_reuses_frozen_logs(self):
        with tempfile.TemporaryDirectory() as temporary:
            references = Path(temporary) / "references"
            calls = []
            freeze = fake_freeze(calls)
            path, notes = player.prepare_references(
                references, definition(), Path("fixtures"), None, None, freeze, sha256
            )
            self.assertEqual(calls, [player.SCENE_RECIPES[scene] for scene in SCENES])
            self.assertEqual(notes, list(SCENES))
            written = json.loads(path.read_text(encoding="utf-8"))
            for scene in written["scenes"]:
                log = references / scene["log"]
                self.assertEqual(scene["log_sha256"], sha256(log))
            self.assertFalse(list(references.glob("*.partial-*")))

            calls.clear()
            player.prepare_references(
                references, definition(), Path("fixtures"), None, None, freeze, sha256
            )
            self.assertEqual(calls, [])

    def test_matching_shipped_hash_is_not_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            references = Path(temporary)
            player.prepare_references(
                references, definition(), Path("f"), None, None, fake_freeze([]), sha256
            )
            frozen = sha256(references / "c1mp1" / "match-7.jsonl")
            shipped = definition()
            shipped["scenes"][0]["log_sha256"] = frozen
            _, notes = player.prepare_references(
                references, shipped, Path("f"), None, None, fake_freeze([]), sha256
            )
            self.assertNotIn("c1mp1", notes)

    def test_changed_frozen_log_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            references = Path(temporary)
            player.prepare_references(
                references, definition(), Path("f"), None, None, fake_freeze([]), sha256
            )
            (references / "c3mp1" / "match-7.jsonl").write_text("edited\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "changed since it was first generated"):
                player.prepare_references(
                    references, definition(), Path("f"), None, None, fake_freeze([]), sha256
                )

    def test_incomplete_scene_folder_is_regenerated(self):
        with tempfile.TemporaryDirectory() as temporary:
            references = Path(temporary)
            player.prepare_references(
                references, definition(), Path("f"), None, None, fake_freeze([]), sha256
            )
            (references / "c2mp2" / "match-7.jsonl").unlink()
            calls = []
            player.prepare_references(
                references, definition(), Path("f"), None, None, fake_freeze(calls), sha256
            )
            self.assertEqual(calls, [player.SCENE_RECIPES["c2mp2"]])
            self.assertTrue((references / "c2mp2" / "match-7.jsonl").is_file())

    def test_short_frame_row_is_a_readable_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            csv = Path(temporary) / "frames.csv"
            csv.write_text("scene_id,interval_ms\nc1mp1,10\n\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Malformed benchmark frame row"):
                player.read_intervals(csv)

    def test_reference_key_depends_on_every_input(self):
        base = player.reference_key("a", "b", "c")
        self.assertNotEqual(base, player.reference_key("x", "b", "c"))
        self.assertNotEqual(base, player.reference_key("a", "x", "c"))
        self.assertNotEqual(base, player.reference_key("a", "b", "x"))

    def test_executable_without_benchmark_options_is_unsupported(self):
        with tempfile.TemporaryDirectory() as temporary:
            exe = Path(temporary) / "mw3.exe"
            exe.write_bytes(b"MZ --benchmark-scene only")
            self.assertFalse(player.executable_supports_benchmark(exe))
            exe.write_bytes(b"MZ --benchmark-scene --arena-record-every-update")
            self.assertTrue(player.executable_supports_benchmark(exe))


class ReportTest(unittest.TestCase):
    def test_pooled_statistics_match_native_formulas(self):
        intervals = [10.0] * 98 + [20.0, 40.0]
        stats = player.pooled_statistics(intervals, 101, 1.0)
        self.assertEqual(stats["p95_ms"], 10.0)
        self.assertEqual(stats["p99_ms"], 20.0)
        self.assertEqual(stats["average_fps"], 101.0)
        self.assertEqual(stats["low_1_percent_fps"], 25.0)  # slowest 1 frame: 40 ms

    def test_report_lists_scenes_and_pooled_overall(self):
        with tempfile.TemporaryDirectory() as temporary:
            suite = Path(temporary)
            for index, scene in enumerate(SCENES):
                directory = suite / scene
                directory.mkdir()
                interval = 10.0 * (index + 1)
                rows = [f"{scene},0,0,0,"] + [f"{scene},{n},0,0,{interval}" for n in range(1, 4)]
                (directory / "frames.csv").write_text(
                    "scene_id,frame_seq,replay_time_seconds,present_elapsed_seconds,interval_ms\n"
                    + "\n".join(rows)
                    + "\n",
                    encoding="utf-8",
                )
                statistics = {
                    "average_fps": 100.0 / (index + 1),
                    "low_1_percent_fps": 1.0,
                    "p95_ms": interval,
                    "p99_ms": interval,
                    "mean_ms": interval,
                }
                summary = {"statistics": statistics, "measured_presents": 4, "gpu": "Test GPU"}
                (directory / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
            report = player.build_report(suite, definition(), {"Width": 1}, "key", ["c2mp2"])
            self.assertEqual([scene["id"] for scene in report["scenes"]], list(SCENES))
            self.assertEqual(report["scenes"][1]["average_fps"], 50.0)
            self.assertAlmostEqual(report["overall"]["average_fps"], 16 / 120)
            self.assertEqual(report["overall"]["p99_ms"], 40.0)
            self.assertEqual(report["gpu"], "Test GPU")
            self.assertEqual(report["reference_mismatch_scenes"], ["c2mp2"])

    def test_previous_report_needs_same_logs_and_settings(self):
        with tempfile.TemporaryDirectory() as temporary:
            results = Path(temporary)
            for name, key, settings in (("1", "key", "s"), ("2", "other", "s"), ("3", "key", "t")):
                (results / name).mkdir()
                earlier = {
                    "reference_key": key,
                    "settings_sha256": settings,
                    "finished": name,
                    "overall": {"average_fps": float(name)},
                }
                (results / name / "report.json").write_text(json.dumps(earlier), encoding="utf-8")
            found = player.previous_report(
                results, {"reference_key": "key", "settings_sha256": "s"}
            )
            self.assertEqual(found["finished"], "1")

    def test_damaged_earlier_report_is_skipped(self):
        with tempfile.TemporaryDirectory() as temporary:
            results = Path(temporary)
            (results / "1").mkdir()
            good = {"reference_key": "k", "settings_sha256": "s", "finished": "1", "overall": {}}
            (results / "1" / "report.json").write_text(json.dumps(good), encoding="utf-8")
            (results / "2").mkdir()
            (results / "2" / "report.json").write_text("{truncated", encoding="utf-8")
            found = player.previous_report(results, {"reference_key": "k", "settings_sha256": "s"})
            self.assertEqual(found["finished"], "1")

    def test_focus_loss_is_classified(self):
        self.assertEqual(player.classify_failure("benchmark window lost focus"), "focus_lost")
        self.assertEqual(
            player.classify_failure("benchmark window lacks input focus"), "focus_lost"
        )
        self.assertEqual(player.classify_failure("Vulkan swapchain changed"), "failed")

    def test_failure_reason_reads_newest_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            suite = Path(temporary)
            (suite / "c2mp2").mkdir()
            (suite / "c2mp2" / "summary.json").write_text(
                json.dumps({"failure": {"reason": "benchmark window lost focus"}}),
                encoding="utf-8",
            )
            self.assertEqual(player.failure_reason(suite), ("c2mp2", "benchmark window lost focus"))


if __name__ == "__main__":
    unittest.main()
