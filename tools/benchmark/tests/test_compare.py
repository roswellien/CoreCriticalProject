"""Exercise the suite comparator with native-schema, asset-free results."""

import hashlib
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from compare import CSV_COLUMNS, PRESSURE_KEYS, canonical_settings, compare, main
from run import BLOCK_ORDER, SUITE_SCENES, read_json, sha256


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def write_summary(path, summary):
    summary["settings_sha256"] = hashlib.sha256(
        canonical_settings(summary["settings"]).encode()
    ).hexdigest()
    write_json(path, summary)


class ComparisonTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()

    def make_block(self, means=(10, 10, 10, 10), nested_a2=False, arm_settings=None):
        arm_settings = arm_settings or {}
        paths = []
        for index, (label, mean) in enumerate(zip(BLOCK_ORDER, means, strict=True)):
            directory = self.root / label
            if nested_a2 and label == "A2":
                directory = self.root / "A1" / label
            paths.append(directory)
            start = 100 * (index + 1)
            manifest = {
                "version": 1,
                "label": label,
                "host": "test-machine",
                "definition_sha256": "a" * 64,
                "started_ns": start,
                "finished_ns": start + 100,
                "scenes": [],
            }
            entries = [(scene, scene) for scene in SUITE_SCENES]
            if label == "A1":
                entries.insert(0, (SUITE_SCENES[0], "conditioning"))
            for offset, (scene, name) in enumerate(entries):
                output = directory / name
                profile = directory / "profiles" / name
                write_json(
                    profile / "launch-plan.json",
                    {"argv": ["mw3", "--write-dir", str(profile), "--benchmark-out", str(output)]},
                )
                output.mkdir(parents=True, exist_ok=True)
                csv = output / "frames.csv"
                # Each arm has different valid counts. Means must weight runs equally.
                count = index + 2
                rows = [",".join(CSV_COLUMNS), f"{scene},1,10,10,"]
                rows.extend(f"{scene},{i + 1},10,10,{mean}" for i in range(1, count))
                csv.write_text("\n".join(rows) + "\n", encoding="utf-8")
                summary = {
                    "version": 1,
                    "scene_id": scene,
                    "valid": True,
                    "settings": {
                        "disk_cache": "disabled",
                        "packs": ["first", "second"],
                        "shadows": "1",
                        "shadow_range": "500",
                        **arm_settings.get(label[0], {}),
                    },
                    "frames_sha256": sha256(csv),
                    "measured_presents": count,
                    "intervals": count - 1,
                    "source_sha": label[0],
                    "executable_sha256": label[0].lower() * 64,
                    "gpu": "GPU",
                    "vulkan_driver_version": 1,
                    "video_memory_pressure": dict.fromkeys(PRESSURE_KEYS, 0),
                    "statistics": {
                        "mean_ms": mean,
                        "p50_ms": mean,
                        "p95_ms": mean,
                        "p99_ms": mean,
                        "average_fps": count / 30,
                        "low_1_percent_fps": 1000 / mean,
                    },
                    "process_to_epoch_seconds": "unavailable",
                    "scene_load_to_epoch_seconds": 1,
                }
                path = output / "summary.json"
                write_summary(path, summary)
                entry = {
                    "id": scene,
                    "summary": f"{name}/summary.json",
                    "summary_sha256": sha256(path),
                    "profile": f"profiles/{name}",
                    "started_ns": start + offset * 10,
                    "finished_ns": start + offset * 10 + 8,
                }
                if name == "conditioning":
                    manifest["conditioning"] = entry
                else:
                    manifest["scenes"].append(entry)
            write_json(directory / "suite.json", manifest)
        return paths

    def edit_manifest(self, label, update):
        path = self.root / label / "suite.json"
        manifest = read_json(path)
        update(manifest)
        write_json(path, manifest)

    def edit_summary(self, label, update, scene="c2mp2"):
        path = self.root / label / scene / "summary.json"
        summary = read_json(path)
        update(summary)
        write_summary(path, summary)
        self.edit_manifest(
            label,
            lambda manifest: next(
                entry for entry in manifest["scenes"] if entry["id"] == scene
            ).update(summary_sha256=sha256(path)),
        )

    def run_cli(self, paths, output, error=None):
        argv = ["compare.py", *map(str, paths), "--out", str(output)]
        stderr = StringIO()
        with (
            patch.object(sys, "argv", argv),
            patch("compare.BENCHMARK_ROOT", self.root),
            redirect_stdout(StringIO()),
            redirect_stderr(stderr),
        ):
            if error is None:
                main()
                return
            with self.assertRaises(SystemExit) as caught:
                main()
        self.assertEqual(caught.exception.code, 2)
        self.assertRegex(stderr.getvalue(), rf"^compare: .*{error}")
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_strict_change_and_spread_boundaries(self):
        for means, expected in (
            ((10, 10.5, 10.5, 10), "no change"),
            ((10, 9.5, 9.5, 10), "no change"),
            ((10, 10.500001, 10.500001, 10), "regression"),
            ((10, 9.499999, 9.499999, 10), "improvement"),
            ((9.75, 11, 11, 10.25), "regression"),
            ((9.749999, 11, 11, 10.250001), "inconclusive"),
        ):
            with self.subTest(means=means):
                result = compare(self.make_block(means))
                self.assertEqual(result["overall"]["verdict"], expected)
                self.assertTrue(
                    all(row["verdict"] == expected for row in result["scenes"].values())
                )

    def test_scored_suite_rejects_strict_launch_plan_and_renamed_result(self):
        for strict_location in ("launch plan", "summary"):
            with self.subTest(strict_location=strict_location):
                paths = self.make_block()
                scene = SUITE_SCENES[0]
                if strict_location == "launch plan":
                    plan = self.root / "A1" / "profiles" / scene / "launch-plan.json"
                    document = read_json(plan)
                    document["argv"].append("--benchmark-strict")
                    write_json(plan, document)
                else:
                    summary = self.root / "A1" / scene / "summary.json"
                    write_json(
                        summary,
                        {
                            "version": 1,
                            "mode": "strict",
                            "valid": True,
                            "scene_id": scene,
                            "expected_ticks": 1,
                            "frames": [{"tick": 0, "time_seconds": 10, "pixel_hash": "a" * 16}],
                        },
                    )
                    self.edit_manifest(
                        "A1",
                        lambda manifest: manifest["scenes"][0].update(
                            summary_sha256=sha256(summary)
                        ),
                    )
                with self.assertRaisesRegex(ValueError, "strict diagnostics are unscored"):
                    compare(paths)

    def test_unequal_counts_weight_runs_and_scenes_equally(self):
        paths = self.make_block((9.8, 10, 10.4, 10.2))
        for label in ("B1", "B2"):
            self.edit_summary(label, lambda summary: summary["statistics"].update(mean_ms=12))
        result = compare([path / "suite.json" for path in paths])
        scene = result["scenes"]["c1mp1"]
        self.assertEqual((scene["a_mean_ms"], scene["b_mean_ms"]), (10, 10.2))
        self.assertEqual([run["measured_presents"] for run in scene["runs"].values()], [2, 3, 4, 5])
        self.assertAlmostEqual(
            result["overall"]["change_percent"], 100 * ((1.02**3 * 1.2) ** 0.25 - 1)
        )

    def test_one_noisy_scene_invalidates_the_block(self):
        paths = self.make_block((10, 11, 11, 10))
        self.edit_summary("B2", lambda summary: summary["statistics"].update(mean_ms=12))
        result = compare(paths)
        self.assertEqual(result["overall"]["verdict"], "inconclusive")
        self.assertGreater(result["overall"]["noise_percent"], 5)
        self.assertEqual(result["scenes"]["c1mp1"]["verdict"], "inconclusive")

    def test_wrong_order_missing_scene_and_manifest_drift(self):
        paths = self.make_block()
        with self.assertRaisesRegex(ValueError, "A1 B1 B2 A2 order"):
            compare([paths[0], paths[2], paths[1], paths[3]])
        for mutate, reason in (
            (lambda run: run["scenes"].pop(), "missing, extra"),
            (lambda run: run.update(started_ns=100), "overlap"),
            (lambda run: run.update(definition_sha256="b" * 64), "definition_sha256"),
            (lambda run: run["scenes"][0].update(summary_sha256="b" * 64), "summary identity"),
            (lambda run: run["scenes"][1].update(profile="profiles/c1mp1"), "profiles must"),
        ):
            with self.subTest(reason=reason):
                self.edit_manifest("B1", mutate)
                with self.assertRaisesRegex(ValueError, reason):
                    compare(paths)
                self.make_block()
        self.edit_manifest("A1", lambda run: run.pop("conditioning"))
        with self.assertRaisesRegex(ValueError, "conditioning"):
            compare(paths)

    def test_invalid_summary_and_csv_are_rejected(self):
        for update, reason in (
            (lambda run: run.update(valid=False), "invalid run"),
            (lambda run: run.update(failure={"reason": "failed"}), "failure"),
            (
                lambda run: run["video_memory_pressure"].update(recoveries=1),
                "video_memory_pressure",
            ),
            (lambda run: run["settings"].update(disk_cache="enabled"), "disk_cache"),
            (lambda run: run.update(measured_presents=1), "invalid measured"),
            (lambda run: run.update(intervals=0), "interval count"),
            (lambda run: run.update(measured_presents=5, intervals=4), "CSV row count"),
            (lambda run: run.update(frames_sha256="a" * 64), "frames_sha256"),
        ):
            with self.subTest(reason=reason):
                paths = self.make_block()
                self.edit_summary("B1", update)
                with self.assertRaisesRegex(ValueError, reason):
                    compare(paths)

    def test_conditioning_summary_cannot_alias_scored_summary(self):
        paths = self.make_block()
        scored = paths[0] / "c1mp1"
        profile = paths[0] / "profiles" / "conditioning"
        write_json(
            profile / "launch-plan.json",
            {"argv": ["mw3", "--write-dir", str(profile), "--benchmark-out", str(scored)]},
        )
        self.edit_manifest(
            "A1",
            lambda run: run["conditioning"].update(
                summary="c1mp1/summary.json", summary_sha256=sha256(scored / "summary.json")
            ),
        )
        with self.assertRaisesRegex(ValueError, "summary paths must be distinct"):
            compare(paths)

    def test_nested_suites_cannot_share_scored_summary(self):
        paths = self.make_block(nested_a2=True)
        scored = paths[-1] / "c2mp2"
        profile = paths[0] / "profiles" / "c2mp2"
        write_json(
            profile / "launch-plan.json",
            {"argv": ["mw3", "--write-dir", str(profile), "--benchmark-out", str(scored)]},
        )
        self.edit_manifest(
            "A1",
            lambda run: run["scenes"][1].update(
                summary="A2/c2mp2/summary.json", summary_sha256=sha256(scored / "summary.json")
            ),
        )
        with self.assertRaisesRegex(ValueError, "summary paths must be distinct"):
            compare(paths)

    def test_summary_must_be_directly_in_launch_output(self):
        paths = self.make_block()
        profile = paths[1] / "profiles" / "c1mp1"
        argv = ["mw3", "--write-dir", str(profile)]
        scene = str(paths[1] / "c1mp1")
        for options in (
            [],
            ["--benchmark-out"],
            ["--benchmark-out", str(paths[1])],
            ["--benchmark-out", str(self.root)],
            ["--benchmark-out", str(paths[1] / "c2mp2")],
            ["--benchmark-out", scene, "--benchmark-out", scene],
        ):
            with self.subTest(options=options):
                write_json(profile / "launch-plan.json", {"argv": argv + options})
                with self.assertRaisesRegex(ValueError, "launch plan --benchmark-out"):
                    compare(paths)

    def test_relocated_suite_rejects_original_launch_paths(self):
        paths = self.make_block()
        paths[1] = paths[1].rename(self.root / "relocated-B1")
        with self.assertRaisesRegex(ValueError, "launch plan does not use its isolated profile"):
            compare(paths)

    def test_malformed_containers_exit_two(self):
        output = self.root / "comparison.json"
        for relative, value, error in (
            ("suite.json", [], "JSON object"),
            ("suite.json", {"scenes": {}}, "scenes must be a JSON array"),
            ("suite.json", {"scenes": ["scene"]}, "scene must be a JSON object"),
            ("suite.json", {"conditioning": "yes"}, "conditioning must be a JSON object"),
            ("conditioning/summary.json", [], "JSON object"),
            ("conditioning/summary.json", {"settings": []}, "settings must be a JSON object"),
            ("conditioning/summary.json", {"statistics": []}, "statistics must be a JSON object"),
            ("profiles/conditioning/launch-plan.json", [], "JSON object"),
            ("profiles/conditioning/launch-plan.json", {"argv": {}}, "argv must be"),
            ("profiles/conditioning/launch-plan.json", {"argv": None}, "argv must be"),
            ("profiles/conditioning/launch-plan.json", {"argv": [None]}, "argv must be"),
        ):
            with self.subTest(relative=relative, value=value):
                paths = self.make_block()
                path = paths[0] / relative
                if isinstance(value, dict):
                    write_json(path, read_json(path) | value)
                else:
                    write_json(path, value)
                if path.name == "summary.json":
                    digest = sha256(path)
                    self.edit_manifest(
                        "A1",
                        lambda run, digest=digest: run["conditioning"].update(
                            summary_sha256=digest
                        ),
                    )
                self.run_cli(paths, output, error)
        self.assertFalse(output.exists())

    def test_cli_creates_nested_output_parent_and_keeps_existing_report(self):
        paths = self.make_block()
        output = self.root / "reports" / "nested" / "comparison.json"
        self.run_cli(paths, output)
        self.assertEqual(read_json(output)["overall"]["verdict"], "no change")
        original = output.read_bytes()
        self.run_cli(paths, output, "File exists")
        self.assertEqual(output.read_bytes(), original)

    def test_version_and_identity_types_are_strict(self):
        paths = self.make_block()
        output = self.root / "comparison.json"
        for value in (True, 1.0):
            with self.subTest(version=value):
                self.edit_manifest(
                    "B1", lambda manifest, value=value: manifest.update(version=value)
                )
                self.run_cli(paths, output, "expected version 1")
        self.edit_manifest("B1", lambda manifest: manifest.update(version=1))
        for host in (["test-machine"], ""):
            with self.subTest(host=host):
                self.edit_manifest("B1", lambda manifest, host=host: manifest.update(host=host))
                self.run_cli(paths, output, "missing host or definition identity")
        self.edit_manifest("B1", lambda manifest: manifest.update(host="test-machine"))
        for fields, error in (
            ({"version": True}, "wrong summary version"),
            ({"version": 1.0}, "wrong summary version"),
            ({"source_sha": True}, "missing build identity"),
            ({"source_sha": ""}, "missing build identity"),
            ({"gpu": 1}, "missing GPU or driver identity"),
            ({"gpu": ""}, "missing GPU or driver identity"),
        ):
            with self.subTest(fields=fields):
                self.edit_summary("B1", lambda summary, fields=fields: summary.update(fields))
                self.run_cli(paths, output, error)
                self.edit_summary(
                    "B1", lambda summary: summary.update(version=1, source_sha="B", gpu="GPU")
                )
        self.assertFalse(output.exists())

    def test_effective_setting_delta_and_pack_precedence(self):
        paths = self.make_block()

        def update(run):
            run["settings"].update(shadows="0", shadow_range="0")

        self.edit_summary("B1", update, SUITE_SCENES[0])
        with self.assertRaisesRegex(ValueError, r"arm B settings drift: shadow_range, shadows"):
            compare(paths, "shadows", ["shadow_range"])
        for scene in SUITE_SCENES:
            for label in ("B1", "B2"):
                self.edit_summary(label, update, scene)
        with self.assertRaisesRegex(ValueError, r"undeclared.*: shadow_range$"):
            compare(paths, "shadows")
        result = compare(paths, "shadows", ["shadow_range"])
        self.assertEqual(result["settings_delta"]["observed"], ["shadow_range", "shadows"])
        for label in ("B1", "B2"):
            self.edit_summary(label, lambda run: run["settings"]["packs"].reverse())
        with self.assertRaisesRegex(ValueError, r"undeclared.*packs"):
            compare(paths, "shadows", ["shadow_range"])
        with self.assertRaisesRegex(ValueError, r"Frozen workload keys.*packs"):
            compare(paths, "shadows", ["shadow_range", "packs"])

    def test_primary_setting_must_change_in_every_scene_with_same_arm_values(self):
        paths = self.make_block()
        for label in ("B1", "B2"):
            self.edit_summary(label, lambda run: run["settings"].update(shadows="0"))
        with self.assertRaisesRegex(ValueError, "c1mp1: declared primary setting must differ"):
            compare(paths, "shadows")
        for scene in SUITE_SCENES:
            for label in ("B1", "B2"):
                value = "2" if scene == "c4mp2" else "0"
                self.edit_summary(
                    label, lambda run, value=value: run["settings"].update(shadows=value), scene
                )
        with self.assertRaisesRegex(ValueError, "c4mp2: inconsistent between-arm values"):
            compare(paths, "shadows")

    def test_lighting_catalog_digests_can_be_declared_for_on_off_comparisons(self):
        for setting, digests, enabled in (
            ("dynamic_lighting", ["effects_catalog_sha256"], "A"),
            ("mech_headlights", ["headlight_catalog_sha256", "headlight_bindings_sha256"], "B"),
        ):
            with self.subTest(setting=setting, enabled=enabled):
                arm_settings = {arm: {setting: "0"} for arm in ("A", "B")}
                arm_settings[enabled] = {setting: "1", **dict.fromkeys(digests, "a" * 64)}
                paths = self.make_block(arm_settings=arm_settings)
                with self.assertRaisesRegex(
                    ValueError,
                    f"undeclared between-arm settings differences: {', '.join(sorted(digests))}$",
                ):
                    compare(paths, setting)
                result = compare(paths, setting, digests)
                self.assertEqual(result["settings_delta"]["observed"], sorted([setting, *digests]))

    def test_catalog_digest_cannot_change_when_present_in_both_arms(self):
        paths = self.make_block(
            arm_settings={
                "A": {"dynamic_lighting": "1", "effects_catalog_sha256": "a" * 64},
                "B": {"dynamic_lighting": "0", "effects_catalog_sha256": "b" * 64},
            }
        )
        with self.assertRaisesRegex(ValueError, r"catalog digest.*effects_catalog_sha256"):
            compare(paths, "dynamic_lighting", ["effects_catalog_sha256"])
        with self.assertRaisesRegex(ValueError, r"Frozen workload keys.*effects_catalog_sha256"):
            compare(paths, "effects_catalog_sha256")
        with self.assertRaisesRegex(ValueError, r"Frozen workload keys.*base_assets_sha256"):
            compare(paths, "dynamic_lighting", ["base_assets_sha256"])

    def test_fingerprint_must_bind_embedded_settings(self):
        paths = self.make_block()
        summary_path = paths[1] / "c2mp2" / "summary.json"
        summary = read_json(summary_path)
        summary["settings"]["shadows"] = "0"
        write_json(summary_path, summary)
        self.edit_manifest(
            "B1", lambda run: run["scenes"][1].update(summary_sha256=sha256(summary_path))
        )
        with self.assertRaisesRegex(ValueError, "settings_sha256"):
            compare(paths)


if __name__ == "__main__":
    unittest.main()
