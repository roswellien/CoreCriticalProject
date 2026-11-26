"""Asset-free checks for the benchmark's Play settings and argv."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run


class BenchmarkLaunchTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        # resolve() expands Windows 8.3 short names (RUNNER~1) the way run.py does.
        self.root = Path(temporary.name).resolve()
        self.data = self.root / "data"
        self.runtime = self.root / "NativePreview"
        self.profile = self.root / "run-profile"
        self.output = self.root / "run"
        self.exe = self.root / "build" / "mw3.exe"
        self.definition = self.root / "definition.json"
        self.saved = {
            "Width": 3440,
            "Height": 1440,
            "WindowMode": "fullscreen_windowed",
            "AntiAliasing": "fxaa",
            "AnisotropicFiltering": 16,
            "DrawDistance": 1200,
            "FogDistance": 1100,
            "FlareStyle": "modern",
            "RenderThread": True,
            "Headlights": True,
            "DynamicLighting": True,
            "Shadows": True,
            "WaterDetail": True,
            "CloudDetail": True,
            "ActivePacks": [],
            "GamePath": str(self.root / "game"),
        }
        self.write(self.definition, {"version": 1, "scenes": [{"id": "c1mp1", "seed": 7}]})
        self.write(self.runtime / "runtime.json", {"roles": {"executable": "bin/mw3.exe"}})
        (self.data / "mods").mkdir(parents=True)

    @staticmethod
    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def pack(self, pack_id, kind):
        path = self.data / "mods" / pack_id
        self.write(
            path / "pack.json",
            {"schema_version": 2, "id": pack_id, "native_payload": {"profile": kind}},
        )
        return str(path)

    def build(self, overrides):
        settings = run.effective_settings(self.saved, overrides)
        return run.build_launch(
            self.definition,
            "c1mp1",
            self.output,
            self.profile,
            self.data,
            self.runtime,
            self.exe,
            settings,
        )

    def test_play_fullscreen_and_active_pack_precedence(self):
        updated = "com.mw3remaster.updated-mw3-mechs"
        mw5 = "com.mw3remaster.mw5-mechs"
        self.saved["ActivePacks"] = [mw5, "environment", updated, "skin"]
        first = self.pack(updated, "prepared-native-v1")
        second = self.pack(mw5, "prepared-native-v1")
        environment = self.pack("environment", "prepared-environment-v1")
        skin = self.pack("skin", "prepared-skins-v1")
        self.pack("disabled-ui", "prepared-ui-v1")
        self.pack(".rollback", "prepared-native-v1")
        fake_plan = {
            "ok": True,
            "argv": ["installed.exe", "--cc-vulkan-wsi", "--cc-render-thread", "1"],
        }
        with patch.object(run, "plan_launch", return_value=fake_plan) as planner:
            plan = self.build({})
        request = planner.call_args.args[0]
        self.assertEqual((request["schema_version"], request["window_mode"]), (4, "borderless"))
        self.assertEqual(
            (request["width"], request["height"], request["aa"], request["af"]),
            (3440, 1440, "fxaa", 16),
        )
        self.assertEqual(request["game_dir"], self.saved["GamePath"])
        self.assertEqual(request["write_dir"], str(self.profile))
        preview = request["preview"]
        self.assertEqual(preview["model_packs"], [first, second])
        self.assertEqual(preview["environment_packs"], [environment])
        self.assertEqual(preview["skin_packs"], [skin])
        self.assertEqual(preview["ui_packs"], [])
        self.assertEqual((preview["draw_distance"], preview["fog_distance"]), (1200, 1100))
        self.assertTrue(
            all(
                preview[k]
                for k in (
                    "headlights",
                    "dynamic_lighting",
                    "shadows",
                    "water_detail",
                    "cloud_detail",
                )
            )
        )
        argv = plan["argv"]
        self.assertNotIn("--window", argv)
        self.assertNotIn("--no-mods", argv)
        self.assertEqual(argv[argv.index("--benchmark-resolution") + 1], "3440x1440")
        roots = [argv[i + 1] for i, token in enumerate(argv) if token == "--benchmark-pack"]
        self.assertEqual(roots, [first, second, environment, skin])
        self.assertEqual(self.saved["ActivePacks"], [mw5, "environment", updated, "skin"])

    def test_overrides_and_play_dependencies(self):
        ui = self.pack("ui", "prepared-ui-v1")
        fake_plan = {"ok": True, "argv": ["installed.exe", "--window", "1280x720", "--windowed"]}
        overrides = {
            "Resolution": "1280x720",
            "WindowMode": "windowed",
            "AntiAliasing": "4",
            "AnisotropicFiltering": 8,
            "DrawDistance": 800,
            "FogDistance": 0,
            "FlareStyle": "original",
            "DynamicLighting": False,
            "Shadows": False,
            "Headlights": True,
            "WaterDetail": False,
            "CloudDetail": False,
            "GamePath": "override",
            "ActivePacks": ["ui"],
        }
        with patch.object(run, "plan_launch", return_value=fake_plan) as planner:
            plan = self.build(overrides)
        request = planner.call_args.args[0]
        self.assertEqual(
            (request["width"], request["height"], request["window_mode"]), (1280, 720, "windowed")
        )
        self.assertEqual(
            (request["aa"], request["af"], request["flare_style"]), ("4", 8, "original")
        )
        self.assertEqual(request["game_dir"], "override")
        preview = request["preview"]
        self.assertEqual((preview["draw_distance"], preview["fog_distance"]), (800, 0))
        self.assertFalse(
            any(
                preview[k]
                for k in (
                    "headlights",
                    "dynamic_lighting",
                    "shadows",
                    "water_detail",
                    "cloud_detail",
                )
            )
        )
        self.assertEqual(preview["ui_packs"], [ui])
        self.assertIn("--window", plan["argv"])

    def test_mandatory_conflicts_and_invalid_resolution_are_refused(self):
        for overrides in (
            {"RenderThread": False},
            {"Renderer": "dxgi"},
            {"VSync": True},
            {"PresentMode": "fifo"},
            {"DiskCache": True},
            {"Resolution": "bad"},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(ValueError):
                run.effective_settings(self.saved, overrides)
        self.saved["RenderThread"] = False
        self.assertTrue(run.effective_settings(self.saved, {})["RenderThread"])

    def test_suite_runs_conditioning_then_all_scenes_with_fresh_profiles(self):
        self.write(
            self.definition,
            {"version": 1, "scenes": [{"id": scene, "seed": 7} for scene in run.SUITE_SCENES]},
        )
        profiles = []

        def fake_scene(definition, scene, output, profile, *inputs):
            self.assertFalse(profile.exists())
            profiles.append(profile)
            profile.mkdir(parents=True)
            self.write(output / "summary.json", {"valid": True, "scene_id": scene})
            return 0

        with patch.object(run, "run_scene", side_effect=fake_scene):
            run.run_suite(
                self.definition, self.output, "A1", self.data, self.runtime, self.exe, self.saved
            )
        manifest = run.read_json(self.output / "suite.json")
        self.assertEqual(manifest["definition_sha256"], run.sha256(self.definition))
        self.assertEqual(manifest["label"], "A1")
        self.assertEqual(
            [profile.name for profile in profiles], ["conditioning", *run.SUITE_SCENES]
        )
        self.assertEqual([entry["id"] for entry in manifest["scenes"]], list(run.SUITE_SCENES))
        self.assertLessEqual(
            manifest["conditioning"]["finished_ns"], manifest["scenes"][0]["started_ns"]
        )

    def test_suite_does_not_publish_manifest_after_scene_failure(self):
        self.write(
            self.definition, {"version": 1, "scenes": [{"id": scene} for scene in run.SUITE_SCENES]}
        )
        with (
            patch.object(run, "run_scene", return_value=1) as launch,
            self.assertRaisesRegex(ValueError, "c1mp1.*status 1"),
        ):
            run.run_suite(
                self.definition,
                self.output,
                "B1",
                self.data,
                self.runtime,
                self.exe,
                self.saved,
            )
        self.assertEqual(launch.call_count, 1)
        self.assertFalse((self.output / "suite.json").exists())

    def test_scene_claims_profile_before_the_planner_writes_to_it(self):
        def planner(request):
            profile = Path(request["write_dir"])
            self.assertTrue(profile.is_dir())
            (profile / "catalog.bin").write_bytes(b"catalog")
            return {"ok": True, "argv": ["installed.exe"]}

        with (
            patch.object(run, "plan_launch", side_effect=planner),
            patch.object(run, "launch_scene", return_value=0) as launch,
        ):
            code = run.run_scene(
                self.definition,
                "c1mp1",
                self.output,
                self.profile,
                self.data,
                self.runtime,
                self.exe,
                self.saved,
            )
        self.assertEqual(code, 0)
        self.assertTrue((self.profile / "catalog.bin").is_file())
        self.assertTrue((self.profile / "launch-plan.json").is_file())
        self.assertEqual(launch.call_count, 1)


if __name__ == "__main__":
    unittest.main()
