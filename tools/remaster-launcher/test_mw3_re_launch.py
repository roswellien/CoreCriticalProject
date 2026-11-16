"""Exercise the native-only, non-executing argv boundary with authored paths."""

import copy
import importlib
import importlib.util
import json
import os
import struct
import unittest
from unittest.mock import patch


class Mw3ReLaunchPlanTests(unittest.TestCase):
    @staticmethod
    def request():
        return {
            "schema_version": 2, "engine": "mw3-re", "runtime_root": "C:/Runtime",
            "executable": "C:/Runtime/bin/mw3.exe", "game_dir": "D:/Original MW3",
            "write_dir": "E:/Data/mw3-re/profiles/default", "renderer": "vulkan-wsi",
            "width": 1280, "height": 720, "aa": "2", "af": 8, "window_mode": "windowed",
            "render_thread": True, "lighting": "normal", "assets": ["F:/Mods Pack/alpha", "F:/Mods/é"],
        }

    def planner(self):
        self.assertIsNotNone(importlib.util.find_spec("mw3_re_launch"), "Native argv planner is not implemented")
        return importlib.import_module("mw3_re_launch").plan_launch

    def test_closed_wire_types(self):
        plan = self.planner()
        valid = self.request()
        for key in valid:
            missing = dict(valid)
            del missing[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                plan(missing)
        for key, value in [
            ("schema_version", True), ("schema_version", 1), ("engine", "legacy"), ("renderer", "software"),
            ("width", True), ("width", 639), ("width", 7681), ("width", 1280.0),
            ("height", 479), ("height", 4321), ("af", True), ("af", 3), ("af", 32),
            ("render_thread", 1), ("aa", 2), ("aa", "msaa4"), ("window_mode", "maximized"),
            ("lighting", "unknown"), ("assets", ()), ("assets", [True]), ("assets", ["F:/a"] * 129),
            ("extra", "no-silent-verbosity-option"),
        ]:
            request = dict(valid, **{key: value})
            before = copy.deepcopy(request)
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                plan(request)
            self.assertEqual(request, before)

    def test_known_unsupported_preferences_have_no_argv(self):
        plan = self.planner()
        for key, value in [("aa", "8")]:
            request = dict(self.request(), **{key: value})
            before = copy.deepcopy(request)
            result = plan(request)
            with self.subTest(key=key, value=value):
                self.assertFalse(result["ok"])
                self.assertTrue(result["reasons"])
                self.assertNotIn("argv", result)
                self.assertEqual(request, before)

    def test_fullscreen_and_borderless_plan_without_window_tokens(self):
        plan = self.planner()
        windowed_plan = plan(self.request())
        self.assertTrue(windowed_plan["ok"])
        without_window = windowed_plan["argv"].copy()
        index = without_window.index("--window")
        self.assertEqual(without_window[index:index + 3], ["--window", "1280x720", "--windowed"])
        del without_window[index:index + 3]
        for mode in ("fullscreen", "borderless"):
            request = dict(self.request(), window_mode=mode)
            before = copy.deepcopy(request)
            result = plan(request)
            with self.subTest(window_mode=mode):
                self.assertTrue(result["ok"])
                self.assertNotIn("--window", result["argv"])
                self.assertNotIn("--windowed", result["argv"])
                self.assertEqual(result["argv"], without_window)
                self.assertEqual(request, before)

    def test_schema_three_optional_pom_and_schema_two_identity(self):
        plan = self.planner()
        baseline = plan(self.request())
        for additions in ({}, {"visuals": {}}, {"visuals": {"pom": False}}):
            request = dict(self.request(), schema_version=3, **additions)
            before = copy.deepcopy(request)
            with self.subTest(additions=additions):
                self.assertEqual(plan(request), baseline)
                self.assertEqual(request, before)
        request = dict(self.request(), schema_version=3, visuals={"pom": True})
        before = copy.deepcopy(request)
        result = plan(request)
        self.assertTrue(result["ok"])
        args = result["argv"]
        self.assertEqual(args.count("--cc-pom"), 1)
        self.assertEqual(args[args.index("--cc-pom") + 1], "1")
        without_pom = args.copy()
        index = without_pom.index("--cc-pom")
        del without_pom[index:index + 2]
        self.assertEqual(without_pom, baseline["argv"])
        self.assertEqual(request, before)
        for lighting in ("off", "flat"):
            with self.subTest(lighting=lighting), self.assertRaises(ValueError):
                plan(dict(request, lighting=lighting))
        for additions in (
            {"visuals": None}, {"visuals": []}, {"visuals": True},
            {"visuals": {"unknown": False}}, {"visuals": {"pom": True, "fog": 0}},
            {"unknown": 1},
        ):
            with self.subTest(additions=additions), self.assertRaises(ValueError):
                plan(dict(self.request(), schema_version=3, **additions))
        for value in (0, 1, 1.0, "true", None, [], {}):
            with self.subTest(pom=value), self.assertRaises(ValueError):
                plan(dict(self.request(), schema_version=3, visuals={"pom": value}))
        with self.assertRaises(ValueError):
            plan(dict(self.request(), visuals={"pom": False}))

    def test_raw_json_duplicate_and_resource_bounds(self):
        self.planner()
        plan_json = importlib.import_module("mw3_re_launch").plan_json
        raw = json.dumps(dict(self.request(), schema_version=3, visuals={"pom": True}))
        self.assertEqual(plan_json(raw), self.planner()(json.loads(raw)))
        self.assertEqual(plan_json(raw.encode("utf-8")), plan_json(raw))
        for malformed in (
            raw[:-1] + ', "schema_version": 3}',
            raw.replace('"pom": true', '"pom": false, "pom": true'),
            raw.replace('"pom": true', '"pom": false, "p\\u006fm": true'),
            raw.replace('"visuals": {"pom": true}', '"visuals": {"pom": true, "extra": {"x": 1, "x": 2}}'),
            raw[:-1] + ', "visuals": {}}',
            raw[:-1] + ', "extra": NaN}',
            '[' * 65 + '0' + ']' * 65,
            '[' * 10000 + '0' + ']' * 10000,
            raw + ' ' * (2 * 1024 * 1024),
            raw.replace('"pom": true', '"pom": true, "extra": "é"') + ' ' * (2 * 1024 * 1024 - len(raw)),
            b'\xff', {}, None,
        ):
            with self.subTest(malformed=str(malformed)[:100]), self.assertRaises(ValueError):
                plan_json(malformed)
        # Strings containing delimiters and escaped quotes do not count as container nesting.
        quoted = dict(self.request(), assets=['F:/' + '[' * 80 + '\"quoted'])
        with self.assertRaisesRegex(ValueError, "path component"):
            plan_json(json.dumps(quoted))
        self.assertTrue(plan_json(json.dumps(dict(self.request(), assets=['F:/' + '[' * 80])))["ok"])
        padded = raw + ' ' * (2 * 1024 * 1024 - len(raw.encode("utf-8")))
        self.assertEqual(plan_json(padded), plan_json(raw))
        unicode_raw = json.dumps(self.request(), ensure_ascii=False)
        with self.assertRaisesRegex(ValueError, "too large"):
            plan_json(unicode_raw + ' ' * (2 * 1024 * 1024 - len(unicode_raw)))
        with self.assertRaisesRegex(ValueError, "Missing or unknown"):
            plan_json('[' * 64 + '0' + ']' * 64)
        with self.assertRaisesRegex(ValueError, "too deep"):
            plan_json('[' * 65 + '0' + ']' * 65)

    def test_quality_tokens_preserve_sampling_choices(self):
        plan = self.planner()
        for saved, native in [("off", "off"), ("1", "off"), ("fxaa", "fxaa"), ("2", "ssaa2"), ("4", "ssaa4")]:
            for lighting in ("off", "flat", "normal"):
                result = plan(dict(self.request(), aa=saved, lighting=lighting, render_thread=False, af=16))
                args = result["argv"]
                with self.subTest(saved=saved, lighting=lighting):
                    self.assertEqual(args[args.index("--cc-aa") + 1], native)
                    self.assertEqual(args[args.index("--cc-lighting") + 1], lighting)
                    self.assertEqual(args[args.index("--cc-render-thread") + 1], "0")
                    self.assertNotIn("--nosound", args)

    def test_all_path_components_precede_normalization(self):
        plan = self.planner()
        fields = ("runtime_root", "executable", "game_dir", "write_dir", "assets")
        bad_components = ["Game.", "Game ", "NUL", "nul.txt", "CONIN$", "conout$.txt", "COM0",
                          "LPT9", "Com¹.foo", "lpt²", "lpt³.bin", "profile:stream", "bad?", "bad*",
                          'bad"', "bad<", "a|b", "bad\x01"]
        for field in fields:
            for component in bad_components:
                request = self.request()
                path = {"runtime_root": "C:/Base/", "executable": "C:/Runtime/", "game_dir": "D:/Base/",
                        "write_dir": "E:/Base/", "assets": "F:/Base/"}[field] + component + "/profiles/native"
                request[field] = [path] if field == "assets" else path
                if field == "runtime_root":
                    request["executable"] = path + "/bin/mw3.exe"
                with self.subTest(field=field, component=component), self.assertRaises(ValueError):
                    plan(request)
                if field == "assets":
                    request["assets"] = ["F:/Valid first", path]
                    with self.subTest(field="assets[1]", component=component), self.assertRaises(ValueError):
                        plan(request)

    def test_absolute_path_and_disjoint_write_contract(self):
        plan = self.planner()
        for path in ["relative/path", "C:relative", "/absolute", "//server/share/path", "//?/C:/path",
                     "C:/Root/../escape", "C:/Root/./file", "C:/Root//file", ""]:
            for field in ("runtime_root", "executable", "game_dir", "write_dir", "assets"):
                request = self.request()
                request[field] = [path] if field == "assets" else path
                with self.subTest(field=field, path=path), self.assertRaises(ValueError):
                    plan(request)
        for path in ["C:/Runtime", "c:/runtime/cache", "C:/", "D:/Original MW3", "D:/Original MW3/cache", "D:/"]:
            with self.subTest(write=path), self.assertRaises(ValueError):
                plan(dict(self.request(), write_dir=path))
        with self.assertRaises(ValueError):
            plan(dict(self.request(), executable="C:/Other/mw3.exe"))
        long_directory = "D:/" + "/".join(["ordinary-directory"] * 20) + "/é space/"
        result = plan(dict(self.request(), game_dir=long_directory))
        self.assertTrue(result["ok"])
        self.assertEqual(result["argv"][2], long_directory)
        for field in ("runtime_root", "game_dir", "write_dir"):
            request = self.request()
            request[field] += "/"
            with self.subTest(trailing_separator=field):
                self.assertTrue(plan(request)["ok"])

    def test_complete_vulkan_argv_preserves_request(self):
        request = self.request()
        before = copy.deepcopy(request)
        environment = dict(os.environ)
        plan = self.planner()
        with patch("builtins.open", side_effect=AssertionError("Planner accessed files")), \
                patch("os.stat", side_effect=AssertionError("Planner probed paths")), \
                patch("subprocess.Popen", side_effect=AssertionError("Planner started a process")):
            result = plan(request)
        self.assertEqual(result, {
            "ok": True,
            "argv": ["C:/Runtime/bin/mw3.exe", "--install", "D:/Original MW3", "--write-dir",
                     "E:/Data/mw3-re/profiles/default", "--cc-vulkan-wsi", "--window", "1280x720",
                     "--windowed", "--cc-aa", "ssaa2", "--cc-af", "8", "--cc-render-thread", "1",
                     "--cc-lighting", "normal", "--assets", "F:/Mods Pack/alpha", "--assets", "F:/Mods/é"],
            "working_directory": "C:\\Runtime\\bin",
        })
        self.assertEqual(request, before)
        self.assertEqual(dict(os.environ), environment)


class NativePreviewPlanTests(unittest.TestCase):
    """Schema 4: the labelled Native preview reads small pack manifests and emits pack arguments."""

    def setUp(self):
        import tempfile
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = self.temporary.name
        self.plan = importlib.import_module("mw3_re_launch").plan_launch

    def write(self, relative, content):
        path = os.path.join(self.root, *relative.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if isinstance(content, bytes):
            with open(path, "wb") as stream:
                stream.write(content)
            return path
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(content if isinstance(content, str) else json.dumps(content))
        return path

    def model_pack(self, name="mechs", models=None, profile="prepared-native-v1"):
        """Build a pack in the installed layout: pack.json plus models/models.json and payload files."""
        for payload in ("mesh0", "tex0", "nrm0", "mesh1", "tex1", "nrm1", "solo-mesh", "solo-tex"):
            self.write(f"{name}/payload/{payload}.bin", "x")
        if models is None:
            models = [
                {"id": "strider", "backend": "native", "status": "runtime-candidate", "environment": {
                    "MW34_STRIDER_MESH": "payload/mesh0.bin", "MW34_STRIDER_TEXTURES": "payload/tex0.bin",
                    "MW34_STRIDER_NORMALS": "payload/nrm0.bin", "MW34_STRIDER_LOD1_MESH": "payload/mesh1.bin",
                    "MW34_STRIDER_LOD1_TEXTURES": "payload/tex1.bin", "MW34_STRIDER_LOD1_NORMALS": "payload/nrm1.bin",
                    "MW34_STRIDER_SKIN_B_TEXTURES": "payload/tex0.bin"}},
                {"id": "owens", "backend": "native", "status": "runtime-ready", "environment": {
                    "MW34_OWENS_MESH": "payload/solo-mesh.bin", "MW34_OWENS_TEXTURES": "payload/solo-tex.bin"}},
                {"id": "madcat", "backend": "legacy", "status": "runtime-ready", "environment": {}},
                {"id": "thor", "backend": "native", "status": "retired", "environment": {}},
            ]
        self.write(f"{name}/models/models.json", {"schema_version": 2, "models": models})
        self.write(f"{name}/pack.json", {"schema_version": 2, "native_payload": {
            "profile": profile, "registry": "models/models.json", "path_base": "pack-root"}})
        return os.path.join(self.root, name)

    def environment_pack(self, name="training", largest=1024):
        self.write(f"{name}/pack.json", {"schema_version": 2, "files": {
            "environment/banks/a.zbd": {"bytes": 100, "sha256": "0" * 64},
            "environment/banks/b.zbd": {"bytes": largest, "sha256": "1" * 64}},
            "native_payload": {"profile": "prepared-environment-v1"}})
        return os.path.join(self.root, name)

    def lighting_environment_pack(self, name="lighting"):
        entry = struct.pack("<IIIIQ6f", 1, 1, 1, 1, 123, 1.0, 1.0, 0.5, 1.0, 1.0, 1.0)
        effect = b"MWFX1\0\0\0" + (1).to_bytes(4, "little") + entry
        self.write(f"{name}/environment/effects.bin", effect)
        self.write(f"{name}/environment/environment.json", {
            "schema_version": 2, "payload_profile": "prepared-environment-v1",
            "operation": "training", "effects": "environment/effects.bin",
            "banks": {"zbd/training/rtexture.zbd": "environment/bank.zbd"}})
        self.write(f"{name}/environment/bank.zbd", "bank")
        self.write(f"{name}/pack.json", {"schema_version": 2, "files": {
            "environment/effects.bin": {"bytes": len(effect), "sha256": "0" * 64},
            "environment/environment.json": {"bytes": 1, "sha256": "1" * 64},
            "environment/bank.zbd": {"bytes": 4, "sha256": "2" * 64}},
            "native_payload": {"profile": "prepared-environment-v1",
                               "registry": "environment/environment.json"}})
        return os.path.join(self.root, name)

    def request(self, **preview):
        return {
            "schema_version": 4, "engine": "mw3-re", "runtime_root": "C:/Runtime",
            "executable": "C:/Runtime/bin/mw3.exe", "game_dir": "D:/Original MW3",
            "write_dir": "E:/Data/mw3-re/profiles/native-preview", "renderer": "vulkan-wsi",
            "width": 1280, "height": 720, "aa": "fxaa", "af": 16, "window_mode": "windowed",
            "render_thread": True, "lighting": "normal", "assets": [], "visuals": {"pom": True},
            "preview": preview,
        }

    # The planner accepts only Windows paths, so tests that read real packs from a temporary
    # directory run on Windows; validation-only tests below run everywhere.
    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_complete_preview_argv_order_and_absolute_pack_paths(self):
        models, training = self.model_pack(), self.environment_pack()
        result = self.plan(self.request(draw_distance=1200, hud="core-critical", hud_text=True,
                                        geometry="partial", model_packs=[models], environment_packs=[training]))
        payload = lambda name: os.path.join(models, "payload", name + ".bin")
        self.assertTrue(result["ok"])
        self.assertEqual(result["skipped_packs"], [])
        self.assertEqual(result["argv"][17:], [
            "--cc-dynamic-lighting", "0", "--cc-pom", "1", "--cc-draw-distance", "1200",
            "--cc-hud", "core-critical", "--cc-hud-text", "1",
            "--cc-geometry", "partial",
            "--cc-model", "strider", "0", payload("mesh0"), payload("tex0"),
            "--cc-model-normals", "strider", "0", payload("nrm0"),
            "--cc-model", "strider", "1", payload("mesh1"), payload("tex1"),
            "--cc-model-normals", "strider", "1", payload("nrm1"),
            "--cc-model", "owens", "0", payload("solo-mesh"), payload("solo-tex"),
            "--cc-environment-pack", training,
        ])
        self.assertEqual(result["argv"][16], "normal")

    def test_original_distance_adds_no_argument_and_defaults_apply(self):
        result = self.plan(self.request())
        self.assertTrue(result["ok"])
        self.assertNotIn("--cc-draw-distance", result["argv"])
        self.assertEqual(result["skipped_packs"], [])

    # The planner accepts only Windows paths, so tests that read real packs from a temporary
    # directory run on Windows; validation-only tests below run everywhere.
    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_oversized_map_pack_is_reported_not_loaded(self):
        large = self.environment_pack("shared", largest=2 ** 32 + 1)
        result = self.plan(self.request(environment_packs=[large]))
        self.assertTrue(result["ok"])
        self.assertNotIn("--cc-environment-pack", result["argv"])
        self.assertEqual([item["root"] for item in result["skipped_packs"]], [large])
        self.assertIn("4 GiB", result["skipped_packs"][0]["reason"])

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_four_gib_map_pack_remains_loadable(self):
        maximum = self.environment_pack("maximum", largest=2 ** 32)
        result = self.plan(self.request(environment_packs=[maximum]))
        self.assertTrue(result["ok"])
        self.assertIn("--cc-environment-pack", result["argv"])
        self.assertEqual(result["skipped_packs"], [])

    # The owner's MW5 and updated-MW3 packs both supply Avatar, Firefly, Owens and Strider; the
    # runtime refuses a second model or normal map for one chassis, so the first pack must win.
    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_chassis_in_two_packs_comes_from_the_first(self):
        first = self.model_pack("first")
        second = self.model_pack("second", models=[
            {"id": "strider", "backend": "native", "status": "runtime-ready", "environment": {
                "MW34_STRIDER_MESH": "payload/solo-mesh.bin", "MW34_STRIDER_TEXTURES": "payload/solo-tex.bin",
                "MW34_STRIDER_NORMALS": "payload/nrm0.bin"}},
            {"id": "thor", "backend": "native", "status": "runtime-ready", "environment": {
                "MW34_THOR_MESH": "payload/mesh0.bin", "MW34_THOR_TEXTURES": "payload/tex0.bin"}}])
        result = self.plan(self.request(model_packs=[first, second]))
        self.assertTrue(result["ok"])
        argv = result["argv"]
        model_levels = [(argv[i + 1], argv[i + 2]) for i, item in enumerate(argv) if item == "--cc-model"]
        normal_levels = [(argv[i + 1], argv[i + 2]) for i, item in enumerate(argv) if item == "--cc-model-normals"]
        self.assertEqual(model_levels, [("strider", "0"), ("strider", "1"), ("owens", "0"), ("thor", "0")])
        self.assertEqual(normal_levels, [("strider", "0"), ("strider", "1")])
        self.assertNotIn(os.path.join(second, "payload", "solo-mesh.bin"), argv)
        self.assertEqual(result["overridden_models"], [{"root": second, "chassis": "strider", "kept_from": first}])

    def test_invalid_choices_are_refused(self):
        for preview in ({"draw_distance": 2400}, {"draw_distance": "1200"}, {"hud": "neon"},
                        {"hud_text": True}, {"hud": "original", "hud_text": True}, {"geometry": "gpu"},
                        {"model_packs": "C:/one"}, {"unknown": 1}, {"model_packs": ["relative/pack"]}):
            with self.subTest(preview=preview), self.assertRaises(ValueError):
                self.plan(self.request(**preview))
        request = self.request()
        request["preview"] = []
        with self.assertRaises(ValueError):
            self.plan(request)

    # The planner accepts only Windows paths, so tests that read real packs from a temporary
    # directory run on Windows; validation-only tests below run everywhere.
    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_pack_problems_fail_the_whole_plan(self):
        escape = self.model_pack("escape", models=[{"id": "strider", "backend": "native",
            "status": "runtime-ready", "environment": {"MW34_STRIDER_MESH": "../outside.bin",
                                                       "MW34_STRIDER_TEXTURES": "payload/tex0.bin"}}])
        missing = self.model_pack("missing", models=[{"id": "strider", "backend": "native",
            "status": "runtime-ready", "environment": {"MW34_STRIDER_MESH": "payload/absent.bin",
                                                       "MW34_STRIDER_TEXTURES": "payload/tex0.bin"}}])
        wrong = self.model_pack("wrong", profile="prepared-environment-v1")
        for pack in (escape, missing, wrong, os.path.join(self.root, "no-such-pack")):
            with self.subTest(pack=pack), self.assertRaises(ValueError):
                self.plan(self.request(model_packs=[pack]))
        with self.assertRaises(ValueError):
            self.plan(self.request(environment_packs=[self.model_pack("mechs-as-map")]))

    # The planner accepts only Windows paths, so tests that read real packs from a temporary
    # directory run on Windows; validation-only tests below run everywhere.
    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_bushwacker_close_mesh_uses_its_historical_key(self):
        pack = self.model_pack("bush", models=[{"id": "bushwacker", "backend": "native", "status": "runtime-ready",
            "environment": {"MW34_BUSHWACKER_TEST": "payload/mesh0.bin", "MW34_BUSHWACKER_TEXTURES": "payload/tex0.bin",
                            "MW34_BUSHWACKER_LOD1_MESH": "payload/mesh1.bin",
                            "MW34_BUSHWACKER_LOD1_TEXTURES": "payload/tex1.bin"}}])
        argv = self.plan(self.request(model_packs=[pack]))["argv"]
        self.assertEqual(argv.count("--cc-model"), 2)
        self.assertEqual(argv[argv.index("--cc-model") + 3], os.path.join(pack, "payload", "mesh0.bin"))

    def test_pack_inside_write_root_is_refused(self):
        request = self.request(model_packs=["E:/Data/mw3-re/profiles/native-preview/mods/pack"])
        with self.assertRaises(ValueError):
            self.plan(request)

    def test_schema_four_json_round_trip(self):
        plan_json = importlib.import_module("mw3_re_launch").plan_json
        result = plan_json(json.dumps(self.request(draw_distance=1600)))
        self.assertEqual(result["argv"][result["argv"].index("--cc-draw-distance") + 1], "1600")

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_dynamic_lighting_uses_enabled_pack_catalog_and_headlight_inputs(self):
        from pathlib import Path
        environment = self.lighting_environment_pack()
        runtime = Path(self.root, "runtime")
        resources = runtime / "resources"
        resources.mkdir(parents=True)
        stock_headlight_catalog = (
            b"MWHDLT1\0" + struct.pack("<III", 1, 0, 0) + struct.pack("<I", 64) +
            b"0" * 64 + struct.pack("<II", 0, 0) + b"\x01" + bytes(31) + struct.pack("<I", 0)
        )
        (resources / "stock-headlights.bin").write_bytes(stock_headlight_catalog)
        bindings = Path(self.root, "headlights.txt")
        bindings.write_text("CC_MW3_HEADLIGHTS_V1\n42 -1\n", encoding="ascii")
        request = self.request(environment_packs=[environment], dynamic_lighting=True,
                               headlights=True, headlight_bindings=str(bindings),
                               stock_headlight_catalog=str(resources / "stock-headlights.bin"))
        request["runtime_root"] = str(runtime)
        request["executable"] = str(runtime / "bin" / "mw3.exe")
        result = self.plan(request)
        self.assertTrue(result["ok"])
        argv = result["argv"]
        catalog = str(Path(environment, "environment", "effects.bin"))
        self.assertEqual(argv[argv.index("--cc-dynamic-lighting") + 1], "1")
        self.assertEqual(argv[argv.index("--cc-effect-lights") + 1], catalog)
        self.assertEqual(argv[argv.index("--cc-fixture-lights") + 1], "1")
        self.assertEqual(argv[argv.index("--cc-mech-headlights") + 1:][:2],
                         [str(resources / "stock-headlights.bin"), str(bindings)])
        self.assertEqual(result["skipped_packs"], [])

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_missing_catalogs_are_reported_and_optional_lights_stay_off(self):
        request = self.request(dynamic_lighting=True, headlights=True,
                               headlight_bindings="C:/Data/headlights.txt")
        result = self.plan(request)
        argv = result["argv"]
        self.assertEqual(argv[argv.index("--cc-dynamic-lighting") + 1], "1")
        self.assertNotIn("--cc-effect-lights", argv)
        self.assertNotIn("--cc-fixture-lights", argv)
        self.assertNotIn("--cc-mech-headlights", argv)
        self.assertEqual({item["feature"] for item in result["skipped_packs"]},
                         {"effect_lights", "fixture_lights", "mech_headlights"})

    @unittest.skipUnless(os.name == "nt", "runtime catalog paths are Windows paths")
    def test_stock_effect_catalog_fallback_must_be_declared_under_runtime(self):
        from pathlib import Path
        runtime = Path(self.root, "runtime")
        resources = runtime / "resources"
        resources.mkdir(parents=True)
        entry = struct.pack("<IIIIQ6f", 1, 1, 1, 1, 456, 1.0, 1.0, 0.5, 1.0, 0.5, 0.25)
        catalog = resources / "stock-effect-lights.bin"
        catalog.write_bytes(b"MWFX1\0\0\0" + (1).to_bytes(4, "little") + entry)
        request = self.request(dynamic_lighting=True, stock_effect_catalog=str(catalog))
        request["runtime_root"] = str(runtime)
        request["executable"] = str(runtime / "bin" / "mw3.exe")
        result = self.plan(request)
        selected_catalog = result["argv"][result["argv"].index("--cc-effect-lights") + 1]
        self.assertEqual(selected_catalog, str(catalog))
        self.assertEqual(result["skipped_packs"], [])
        with self.assertRaisesRegex(ValueError, "leaves the runtime root"):
            self.plan(self.request(
                dynamic_lighting=True,
                stock_effect_catalog="C:/Outside/catalog.bin",
            ))

    def test_headlights_cannot_be_selected_without_dynamic_lighting(self):
        with self.assertRaisesRegex(ValueError, "require dynamic lighting"):
            self.plan(self.request(headlights=True))


if __name__ == "__main__":
    unittest.main()
