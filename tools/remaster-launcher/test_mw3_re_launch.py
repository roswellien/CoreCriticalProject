"""Exercise the native-only, non-executing argv boundary with authored paths."""

import copy
import hashlib
import importlib
import importlib.util
import json
import os
import re
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import PureWindowsPath
from unittest.mock import patch


class Mw3ReLaunchPlanTests(unittest.TestCase):
    @staticmethod
    def request():
        return {
            "schema_version": 2, "engine": "mw3-re", "runtime_root": "C:/Runtime",
            "executable": "C:/Runtime/bin/mw3.exe", "game_dir": "D:/Original MW3",
            "write_dir": "E:/Data/mw3-re/profiles/default", "renderer": "vulkan-wsi",
            "width": 1280, "height": 720, "aa": "2", "af": 8, "window_mode": "windowed",
            "render_thread": True, "lighting": "normal", "flare_style": "modern",
            "assets": ["F:/Mods Pack/alpha", "F:/Mods/é"],
        }

    def planner(self):
        self.assertIsNotNone(importlib.util.find_spec("mw3_re_launch"), "Native argv planner is not implemented")
        return importlib.import_module("mw3_re_launch").plan_launch

    def test_closed_wire_types(self):
        plan = self.planner()
        valid = self.request()
        for key in valid:
            if key == "flare_style":
                continue
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
            ("flare_style", "smooth"), ("flare_style", True),
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

    def test_disk_cache_switch_reaches_only_the_child_environment(self):
        plan = self.planner()
        default = plan(self.request())
        self.assertEqual(default["environment"], {"MW3_DISK_CACHE": "1"})
        enabled = plan(dict(self.request(), disk_cache=True))
        disabled = plan(dict(self.request(), disk_cache=False))
        self.assertEqual(enabled["environment"], {"MW3_DISK_CACHE": "1"})
        self.assertEqual(disabled["environment"], {"MW3_DISK_CACHE": "0"})
        # The cache switch never changes the game's own command line.
        self.assertEqual(enabled["argv"], disabled["argv"])
        for value in (1, "0", None):
            with self.subTest(disk_cache=value), self.assertRaisesRegex(ValueError, "disk_cache"):
                plan(dict(self.request(), disk_cache=value))

    def test_verified_indeo_path_is_emitted_and_missing_codec_is_reported(self):
        plan = self.planner()
        verified = plan(dict(self.request(), indeo_codec="D:/Original MW3/native-inputs/Ir50_32.dll"))
        self.assertTrue(verified["ok"])
        index = verified["argv"].index("--indeo-codec")
        self.assertEqual(verified["argv"][index + 1], "D:\\Original MW3\\native-inputs\\Ir50_32.dll")
        self.assertEqual(verified["skipped_features"], [{
            "feature": "vsync",
            "reason": "The selected MW3-RE runtime does not advertise support for VSync.",
        }])

        missing = plan(self.request())
        self.assertNotIn("--indeo-codec", missing["argv"])
        self.assertEqual(len(missing["skipped_features"]), 2)
        self.assertEqual(missing["skipped_features"][0]["feature"], "vsync")
        self.assertEqual(missing["skipped_features"][1]["feature"], "Indeo movies")
        self.assertIn("imported-file fallback", missing["skipped_features"][1]["reason"])
        with self.assertRaisesRegex(ValueError, "path component"):
            plan(dict(self.request(), indeo_codec="D:/Original MW3/../Ir50_32.dll"))

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

    def test_flare_style_is_validated_and_defaults_to_modern(self):
        plan = self.planner()
        for style in ("modern", "original"):
            request = dict(self.request(), flare_style=style)
            args = plan(request)["argv"]
            self.assertEqual(args[args.index("--cc-flare-style") + 1], style)
        for invalid in ("smooth", "", True, None):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                plan(dict(self.request(), flare_style=invalid))
        legacy_wire = self.request()
        del legacy_wire["flare_style"]
        args = plan(legacy_wire)["argv"]
        self.assertEqual(args[args.index("--cc-flare-style") + 1], "modern")

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
                     "--cc-lighting", "normal", "--cc-flare-style", "modern",
                     "--assets", "F:/Mods Pack/alpha", "--assets", "F:/Mods/é"],
            "working_directory": "C:\\Runtime\\bin",
            "skipped_features": [{
                "feature": "vsync",
                "reason": "The selected MW3-RE runtime does not advertise support for VSync.",
            }, {
                "feature": "Indeo movies",
                "reason": "No original Ir50_32.dll passed the launcher's identity check; movie playback will use the existing imported-file fallback.",
            }],
            "environment": {"MW3_DISK_CACHE": "1"},
        })
        self.assertEqual(request, before)
        self.assertEqual(dict(os.environ), environment)

    def test_vsync_support_and_strict_wire_types(self):
        plan = self.planner()
        for schema in (2, 3, 4):
            base = dict(self.request(), schema_version=schema)
            if schema == 4:
                base["preview"] = {}
            # Default (both omitted): no --cc-vsync emitted, skipped feature recorded
            res_default = plan(base)
            self.assertNotIn("--cc-vsync", res_default["argv"])
            vsync_skipped = [f for f in res_default["skipped_features"] if f["feature"] == "vsync"]
            self.assertEqual(len(vsync_skipped), 1)
            self.assertIn("runtime does not advertise support", vsync_skipped[0]["reason"])

            # Unsupported runtime asked for vsync on: it already presents with vsync, nothing skipped
            res_unsupported = plan(dict(base, supports_vsync=False, vsync=True))
            self.assertNotIn("--cc-vsync", res_unsupported["argv"])
            self.assertFalse(any(f["feature"] == "vsync" for f in res_unsupported["skipped_features"]))

            # Supported runtime: vsync omitted -> emits 0, no vsync skipped feature
            res_omitted = plan(dict(base, supports_vsync=True))
            idx = res_omitted["argv"].index("--cc-vsync")
            self.assertEqual(res_omitted["argv"][idx + 1], "0")
            self.assertFalse(any(f["feature"] == "vsync" for f in res_omitted["skipped_features"]))

            # Supported runtime: vsync=False -> emits 0
            res_off = plan(dict(base, supports_vsync=True, vsync=False))
            idx = res_off["argv"].index("--cc-vsync")
            self.assertEqual(res_off["argv"][idx + 1], "0")
            self.assertFalse(any(f["feature"] == "vsync" for f in res_off["skipped_features"]))

            # Supported runtime: vsync=True -> emits 1
            res_on = plan(dict(base, supports_vsync=True, vsync=True))
            idx = res_on["argv"].index("--cc-vsync")
            self.assertEqual(res_on["argv"][idx + 1], "1")
            self.assertFalse(any(f["feature"] == "vsync" for f in res_on["skipped_features"]))

            # Strict boolean validation
            for invalid in (1, 0, "true", "false", None, 1.0, [], {}):
                with self.subTest(schema=schema, vsync=invalid), self.assertRaisesRegex(ValueError, "vsync must be a boolean"):
                    plan(dict(base, vsync=invalid))
                with self.subTest(schema=schema, supports_vsync=invalid), self.assertRaisesRegex(ValueError, "supports_vsync must be a boolean"):
                    plan(dict(base, supports_vsync=invalid))

class NativePreviewPlanTests(unittest.TestCase):
    """Schema 4: the labelled Native preview reads small pack manifests and emits pack arguments."""

    def setUp(self):
        import tempfile
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = self.temporary.name
        planner_module = importlib.import_module("mw3_re_launch")
        plan_launch = planner_module.plan_launch

        def plan_with_portable_fixture_paths(request):
            if os.name == "nt":
                return plan_launch(request)

            original_windows_path = planner_module._windows_path

            def windows_path(value, **kwargs):
                if isinstance(value, str) and os.path.isabs(value):
                    try:
                        relative = os.path.relpath(value, self.root)
                    except ValueError:
                        relative = ".."
                    if relative == "." or not relative.startswith(".." + os.sep):
                        parts = [] if relative == "." else relative.split(os.sep)
                        return PureWindowsPath("F:/test-fixtures", *parts)
                return original_windows_path(value, **kwargs)

            with patch.object(planner_module, "_windows_path", side_effect=windows_path):
                return plan_launch(request)

        self.plan = plan_with_portable_fixture_paths

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
            relative = f"{name}/payload/{payload}.bin"
            if not os.path.exists(os.path.join(self.root, *relative.split("/"))):
                self.write(relative, "x")
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

    def surface_sidecar(self, asset_id):
        from surface_materials import (
            mesh_uv_identity,
            pack_surface_materials,
            texture_batch_materials,
        )
        from test_surface_materials import _make_bwmesh1, _make_bwtex1

        mesh = _make_bwmesh1()
        textures = _make_bwtex1()
        sidecar = pack_surface_materials(
            asset_id=asset_id,
            mesh_uv_hash=mesh_uv_identity(mesh),
            batch_materials=texture_batch_materials(textures),
            records=[],
        )
        return mesh, textures, sidecar

    def add_surface_material(self, name, chassis, level=0, sidecar=None):
        infix = "LOD1_" if level == 1 else ""
        stem = f"{name}/payload"
        mesh_name = f"mesh{level}"
        texture_name = f"tex{level}"
        if sidecar is None:
            lod_name = "distance" if level == 1 else "close"
            mesh, textures, sidecar = self.surface_sidecar(f"{chassis}:{lod_name}")
        else:
            mesh, textures, sidecar = sidecar
        mesh_path = self.write(f"{stem}/{mesh_name}.bin", mesh)
        texture_path = self.write(f"{stem}/{texture_name}.bin", textures)
        material_path = self.write(f"{stem}/materials{level}.bin", sidecar)
        return {
            f"MW34_{chassis.upper()}_{infix}MESH": f"payload/{mesh_name}.bin",
            f"MW34_{chassis.upper()}_{infix}TEXTURES": f"payload/{texture_name}.bin",
            f"MW34_{chassis.upper()}_{infix}SURFACE_MATERIALS": f"payload/materials{level}.bin",
        }

    def environment_pack(self, name="training", largest=1024):
        self.write(f"{name}/pack.json", {"schema_version": 2, "files": {
            "environment/banks/a.zbd": {"bytes": 100, "sha256": "0" * 64},
            "environment/banks/b.zbd": {"bytes": largest, "sha256": "1" * 64}},
            "native_payload": {"profile": "prepared-environment-v1"}})
        return os.path.join(self.root, name)

    def ui_pack(self, name="menu", kind="menu", background=True, pixel=(1, 2, 3, 255),
                sprite="0123456789abcdef"):
        image = b"MW3H" + struct.pack("<IIffff", 1, 1, 0.0, 0.0, 1.0, 1.0) + bytes(pixel)
        sprites = {}
        files = {}
        if sprite is not None:
            relative = f"ui/sprites/{sprite}.rgba"
            self.write(f"{name}/{relative}", image)
            sprites[sprite] = relative
            files[relative] = {"bytes": len(image), "sha256": hashlib.sha256(image).hexdigest(),
                               "format": "MW3H-v1"}
        registry = {"schema_version": 2, "payload_profile": "prepared-ui-v1", "kind": kind,
                    "sprites": sprites,
                    "background": "ui/background.mwhd" if background else None}
        self.write(f"{name}/ui/ui.json", registry)
        registry_bytes = json.dumps(registry).encode("utf-8")
        files["ui/ui.json"] = {"bytes": len(registry_bytes),
                               "sha256": hashlib.sha256(registry_bytes).hexdigest()}
        if background:
            background_bytes = b"MWHDBG1\0" + struct.pack("<IIII", 1, 1, 1, 1) + bytes(3)
            self.write(f"{name}/ui/background.mwhd", background_bytes)
            files["ui/background.mwhd"] = {"bytes": len(background_bytes),
                                             "sha256": hashlib.sha256(background_bytes).hexdigest(),
                                             "format": "MWHDBG1"}
        self.write(f"{name}/pack.json", {"schema_version": 2, "files": files, "native_payload": {
            "profile": "prepared-ui-v1", "registry": "ui/ui.json", "path_base": "pack-root"}})
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

    def menu_pack(self, name="menu", tamper=False):
        background = struct.pack("<8sIIII", b"MWHDBG1\0", 4, 2, 2, 1) + bytes(range(24))
        registry = json.dumps({"schema_version": 2, "payload_profile": "prepared-ui-v1",
                               "kind": "menu", "sprites": {},
                               "background": "ui/background.mwhd"}).encode()
        background_path = self.write(f"{name}/ui/background.mwhd", background)
        registry_path = self.write(f"{name}/ui/ui.json", registry)
        files = {}
        for relative, path, file_format in (
                ("ui/background.mwhd", background_path, "MWHDBG1"),
                ("ui/ui.json", registry_path, None)):
            with open(path, "rb") as stream:
                payload = stream.read()
            files[relative] = {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
            if file_format:
                files[relative]["format"] = file_format
        self.write(f"{name}/pack.json", {"schema_version": 2, "files": files,
            "native_payload": {"profile": "prepared-ui-v1", "registry": "ui/ui.json"}})
        if tamper:
            with open(background_path, "r+b") as stream:
                stream.seek(-1, os.SEEK_END)
                stream.write(b"x")
        return os.path.join(self.root, name)

    def request(self, **preview):
        return {
            "schema_version": 4, "engine": "mw3-re", "runtime_root": "C:/Runtime",
            "executable": "C:/Runtime/bin/mw3.exe", "game_dir": "D:/Original MW3",
            # Skin metadata is written below write_dir, so Windows runs need a real directory;
            # elsewhere the planner only validates the Windows path and never writes there.
            "write_dir": (os.path.join(self.root, "native-writes") if os.name == "nt"
                          else "E:/Data/mw3-re/profiles/native-preview"),
            "renderer": "vulkan-wsi",
            "width": 1280, "height": 720, "aa": "fxaa", "af": 16, "window_mode": "windowed",
            "render_thread": True, "lighting": "normal", "assets": [], "visuals": {"pom": True},
            "preview": preview,
        }

    def skin_bindings(self, result):
        path = result["argv"][result["argv"].index("--cc-skin-bindings") + 1]
        blob = Path(path).read_bytes()
        self.assertEqual(blob[:8], b"BWSKIDX1")
        count = struct.unpack_from("<I", blob, 8)[0]
        offset = 12
        rows = []
        for _ in range(count):
            size = struct.unpack_from("<I", blob, offset)[0]
            offset += 4
            chassis = blob[offset:offset + size].decode("utf-8")
            offset += size
            lod, index, size = struct.unpack_from("<III", blob, offset)
            offset += 12
            texture = blob[offset:offset + size].decode("utf-8")
            offset += size
            rows.append([chassis, str(lod), str(index), texture])
        self.assertEqual(offset, len(blob))
        return rows

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
        argv = result["argv"]
        tail_start = argv.index("--cc-dynamic-lighting")
        self.assertEqual(argv[argv.index("--cc-lighting") + 2:tail_start],
                         ["--cc-flare-style", "modern"])
        self.assertEqual(argv[tail_start:], [
            "--cc-dynamic-lighting", "0", "--cc-sun-shadows", "0", "--cc-water-detail", "0",
            "--cc-cloud-detail", "0", "--cc-pom", "1", "--cc-environment-packs-explicit",
            "--cc-draw-distance", "1200",
            "--cc-hud", "core-critical", "--cc-hud-text", "1",
            "--cc-geometry", "partial",
            "--cc-model", "strider", "0", payload("mesh0"), payload("tex0"),
            "--cc-model-normals", "strider", "0", payload("nrm0"),
            "--cc-model", "strider", "1", payload("mesh1"), payload("tex1"),
            "--cc-model-normals", "strider", "1", payload("nrm1"),
            "--cc-model", "owens", "0", payload("solo-mesh"), payload("solo-tex"),
            "--cc-skin-bindings", os.path.join(self.root, "native-writes", "prepared-skins", "stock-skins.bin"),
            "--cc-environment-pack", training,
        ])
        self.assertEqual(argv[16], "normal")

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_retail_skin_indices_both_lods_and_winning_model_pack(self):
        environment = {"MW34_STRIDER_MESH": "payload/mesh0.bin",
                       "MW34_STRIDER_TEXTURES": "payload/tex0.bin",
                       "MW34_STRIDER_LOD1_MESH": "payload/mesh1.bin",
                       "MW34_STRIDER_LOD1_TEXTURES": "payload/tex1.bin"}
        for lod, infix in ((0, ""), (1, "LOD1_")):
            for letter in "BCDEFGH":
                environment[f"MW34_STRIDER_{infix}SKIN_{letter}_TEXTURES"] = f"payload/tex{lod}.bin"
        model = {"id": "strider", "backend": "native", "status": "runtime-ready", "environment": environment}
        first = self.model_pack("skin-first", [model])
        second = self.model_pack("skin-second", [model])
        result = self.plan(self.request(model_packs=[first, second]))
        rows = self.skin_bindings(result)
        expected = [["strider", str(lod), str(index), os.path.join(first, "payload", f"tex{lod}.bin")]
                    for lod in (0, 1) for index in range(1, 8)]
        self.assertEqual(rows, expected)
        self.assertEqual(len(result["overridden_models"]), 1)
        environment["MW34_STRIDER_SKIN_B_TEXTURES"] = "../outside.bin"
        environment["MW34_STRIDER_LOD1_SKIN_H_TEXTURES"] = "payload/missing.bin"
        self.model_pack("skin-first", [model])
        result = self.plan(self.request(model_packs=[first]))
        self.assertEqual(len(self.skin_bindings(result)), 12)
        self.assertNotIn("--cc-model-skin", result["argv"])
        self.assertEqual([entry["feature"] for entry in result["skipped_packs"]],
                         ["skin_textures", "skin_textures"])

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_named_skin_catalog_validates_selected_mesh_and_integrity(self):
        from test_prepared_skin_packs import SkinPackTests
        fixture = SkinPackTests("runTest")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        request = self.request(model_packs=[str(fixture.base)], skin_packs=[str(fixture.pack)])
        request["write_dir"] = os.path.join(self.root, "native-writes")
        result = self.plan(request)
        self.assertEqual(result["skipped_packs"], [])
        catalog = Path(result["argv"][result["argv"].index("--cc-skin-catalog") + 1])
        # The catalog writer resolves its path, which expands 8.3 short names in TEMP.
        self.assertTrue(catalog.resolve().is_relative_to(Path(request["write_dir"]).resolve()))
        self.assertEqual(catalog.read_bytes()[:12], b"BWSKIN1\0" + struct.pack("<I", 1))
        self.assertIn(b"Sommerset", catalog.read_bytes())
        fixture.registry["skins"][0]["mesh_sha256"]["distance"] = "0" * 64
        fixture.save()
        result = self.plan(request)
        self.assertNotIn("--cc-skin-catalog", result["argv"])
        self.assertIn("distance mesh", result["skipped_packs"][0]["reason"])
        fixture.registry["skins"][0]["mesh_sha256"]["distance"] = hashlib.sha256(
            (fixture.base / "payload/MW34_ORION_LOD1_MESH.bin").read_bytes()).hexdigest()
        fixture.save()
        (fixture.pack / "texture.bin").write_bytes(fixture.pixels[:-1] + b"x")
        result = self.plan(request)
        self.assertNotIn("--cc-skin-catalog", result["argv"])
        self.assertIn("integrity", result["skipped_packs"][0]["reason"])

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_full_stock_roster_stays_below_windows_command_line_limit(self):
        from prepared_mech_packs import CHASSIS
        payloads = {role: f"payload/{hashlib.sha256(role.encode()).hexdigest()}.bin"
                    for role in ("mesh0", "mesh1", "tex0", "tex1", "nrm0", "nrm1")}
        for relative in payloads.values():
            self.write(f"full-stock-roster/{relative}", "x")
        models = []
        for chassis in CHASSIS:
            environment = {}
            for lod, infix in ((0, ""), (1, "LOD1_")):
                prefix = f"MW34_{chassis.upper()}_{infix}"
                environment[prefix + ("TEST" if chassis == "bushwacker" and lod == 0 else "MESH")] = payloads[f"mesh{lod}"]
                environment[prefix + "TEXTURES"] = payloads[f"tex{lod}"]
                environment[prefix + "NORMALS"] = payloads[f"nrm{lod}"]
                for letter in "BCDEFGH":
                    environment[prefix + f"SKIN_{letter}_TEXTURES"] = payloads[f"tex{lod}"]
            models.append({"id": chassis, "backend": "native", "status": "runtime-ready",
                           "environment": environment})
        pack = self.model_pack("full-stock-roster", models)
        result = self.plan(self.request(model_packs=[pack]))
        self.assertEqual(len(self.skin_bindings(result)), 18 * 2 * 7)
        self.assertEqual(result["argv"].count("--cc-skin-bindings"), 1)
        self.assertNotIn("--cc-model-skin", result["argv"])
        command_line = subprocess.list2cmdline(result["argv"])
        self.assertLess(len(command_line.encode("utf-16-le")) // 2, 32767)

    def test_original_distance_adds_no_argument_and_defaults_apply(self):
        result = self.plan(self.request())
        self.assertTrue(result["ok"])
        self.assertNotIn("--cc-draw-distance", result["argv"])
        self.assertIn("--cc-environment-packs-explicit", result["argv"])
        self.assertEqual(result["argv"][result["argv"].index("--cc-sun-shadows") + 1], "0")
        self.assertEqual(result["skipped_packs"], [])

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_menu_background_pack_is_hash_checked_and_emitted(self):
        pack = self.menu_pack()
        result = self.plan(self.request(hud="core-critical", ui_packs=[pack]))
        background = os.path.join(pack, "ui", "background.mwhd")
        self.assertIn("--cc-menu-background", result["argv"])
        self.assertEqual(result["argv"].index("--cc-menu-background") + 1,
                         result["argv"].index(background))
        self.assertEqual(result["skipped_packs"], [])

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_tampered_menu_background_is_reported_and_left_off(self):
        pack = self.menu_pack(tamper=True)
        result = self.plan(self.request(hud="core-critical", ui_packs=[pack]))
        self.assertNotIn("--cc-menu-background", result["argv"])
        self.assertEqual(result["skipped_packs"][0]["feature"], "ui_artwork")
        self.assertIn("integrity failure", result["skipped_packs"][0]["reason"])

    def test_no_ui_packs_leaves_hud_options_unset(self):
        result = self.plan(self.request())
        self.assertNotIn("--cc-hud", result["argv"])
        self.assertNotIn("--cc-hud-text", result["argv"])

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_ui_sprite_packs_route_to_native_artwork_and_menu_background(self):
        hud = self.ui_pack("hud", "hud", background=False)
        menu = self.ui_pack("menu", "menu", background=True)
        result = self.plan(self.request(hud="core-critical", ui_packs=[hud, menu]))
        argv = result["argv"]
        self.assertEqual(argv.count("--cc-hud-artwork"), 2)
        self.assertEqual(
            [argv[i + 1] for i, value in enumerate(argv) if value == "--cc-hud-artwork"],
            [hud, menu],
        )
        background = os.path.join(menu, "ui", "background.mwhd")
        self.assertEqual(argv.count("--cc-menu-background"), 1)
        self.assertEqual(argv[argv.index("--cc-menu-background") + 1], background)
        self.assertEqual(result["skipped_packs"], [])

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_identical_ui_identity_hashes_are_accepted_in_input_order(self):
        hud = self.ui_pack("hud-identical", "hud", background=False)
        menu = self.ui_pack("menu-identical", "menu", background=False)
        result = self.plan(self.request(hud="core-critical", hud_text=True, ui_packs=[hud, menu]))
        artwork = [result["argv"][i + 1] for i, value in enumerate(result["argv"])
                   if value == "--cc-hud-artwork"]
        self.assertEqual(artwork, [hud, menu])
        self.assertEqual(result["skipped_packs"], [])

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_conflicting_ui_identity_keeps_first_pack_and_reports_later_pack(self):
        first = self.ui_pack("hud-first", "hud", background=False)
        second = self.ui_pack("menu-conflict", "menu", background=False, pixel=(9, 8, 7, 255))
        result = self.plan(self.request(hud="core-critical", hud_text=True, ui_packs=[first, second]))
        artwork = [result["argv"][i + 1] for i, value in enumerate(result["argv"])
                   if value == "--cc-hud-artwork"]
        self.assertEqual(artwork, [first])
        self.assertEqual(result["skipped_packs"][0]["root"], second)
        self.assertIn("0123456789abcdef", result["skipped_packs"][0]["reason"])
        self.assertIn(first, result["skipped_packs"][0]["reason"])

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_undeclared_ui_sprites_are_reported_and_not_routed(self):
        first = self.ui_pack("hud-declared", "hud", background=False)
        conflicting = (b"MW3H" + struct.pack("<IIffff", 1, 1, 0.0, 0.0, 1.0, 1.0)
                       + bytes((9, 8, 7, 255)))
        for name, sprite, background, extra in (
                ("empty-registry", None, False, conflicting),
                ("background-with-extra", None, True, conflicting),
                ("undeclared-conflict", "1111111111111111", False, conflicting),
                ("undeclared-malformed", "1111111111111111", False, b"not MW3H")):
            with self.subTest(name=name):
                second = self.ui_pack(name, "menu", background=background, sprite=sprite)
                self.write(f"{name}/ui/sprites/0123456789abcdef.rgba", extra)
                result = self.plan(self.request(hud="core-critical", ui_packs=[first, second]))
                self.assertTrue(result["ok"])
                artwork = [result["argv"][i + 1] for i, value in enumerate(result["argv"])
                           if value == "--cc-hud-artwork"]
                self.assertEqual(artwork, [first])
                self.assertEqual(len(result["skipped_packs"]), 1)
                skipped = result["skipped_packs"][0]
                self.assertEqual(skipped["root"], second)
                self.assertEqual(skipped["feature"], "ui_artwork")
                self.assertIn("sprite directory does not match the registry", skipped["reason"])

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_empty_ui_sprite_table_never_routes_artwork(self):
        for background in (False, True):
            with self.subTest(background=background):
                menu = self.ui_pack(f"empty-sprites-{background}", "menu",
                                    background=background, sprite=None)
                result = self.plan(self.request(hud="core-critical", ui_packs=[menu]))
                self.assertTrue(result["ok"])
                self.assertNotIn("--cc-hud-artwork", result["argv"])
                if background:
                    # A background-only menu pack is routed to the menu background alone.
                    self.assertIn("--cc-menu-background", result["argv"])
                    self.assertEqual(result["skipped_packs"], [])
                else:
                    self.assertNotIn("--cc-menu-background", result["argv"])
                    self.assertEqual(len(result["skipped_packs"]), 1)
                    skipped = result["skipped_packs"][0]
                    self.assertEqual(skipped["root"], menu)
                    self.assertEqual(skipped["feature"], "ui_artwork")
                    self.assertIn("no available artwork", skipped["reason"])

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_duplicate_ui_kind_reports_later_pack(self):
        first = self.ui_pack("hud-first", "hud", background=False)
        second = self.ui_pack("hud-second", "hud", background=False, pixel=(9, 8, 7, 255))
        result = self.plan(self.request(hud="core-critical", ui_packs=[first, second]))
        artwork = [result["argv"][i + 1] for i, value in enumerate(result["argv"])
                   if value == "--cc-hud-artwork"]
        self.assertEqual(artwork, [first])
        self.assertEqual(result["skipped_packs"][0]["root"], second)
        self.assertIn("hud UI pack was already selected", result["skipped_packs"][0]["reason"])

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_missing_ui_pack_is_reported_without_artwork_argv(self):
        missing = os.path.join(self.root, "absent-ui-pack")
        result = self.plan(self.request(hud="core-critical", ui_packs=[missing]))
        self.assertNotIn("--cc-hud-artwork", result["argv"])
        self.assertEqual(result["skipped_packs"][0]["feature"], "ui_artwork")
        self.assertIn("missing", result["skipped_packs"][0]["reason"])

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_ui_pack_without_core_critical_hud_is_reported_and_skipped(self):
        hud = self.ui_pack("hud-without-hud-mode", "hud", background=False)
        result = self.plan(self.request(ui_packs=[hud]))
        self.assertTrue(result["ok"])
        self.assertNotIn("--cc-hud-artwork", result["argv"])
        self.assertEqual(result["skipped_packs"][0]["root"], hud)
        self.assertIn("requires the core-critical HUD", result["skipped_packs"][0]["reason"])

    def test_invalid_ui_pack_path_is_reported_and_skipped(self):
        result = self.plan(self.request(ui_packs=["relative/pack"]))
        self.assertTrue(result["ok"])
        self.assertNotIn("--cc-hud-artwork", result["argv"])
        self.assertEqual(result["skipped_packs"][0]["root"], os.path.join("relative", "pack"))
        self.assertIn("unreadable", result["skipped_packs"][0]["reason"])

    def test_sun_shadows_require_both_launcher_choices_and_sun_lighting(self):
        for shadows in (False, True):
            for dynamic_lighting in (False, True):
                with self.subTest(shadows=shadows, dynamic_lighting=dynamic_lighting):
                    result = self.plan(self.request(
                        shadows=shadows, dynamic_lighting=dynamic_lighting))
                    argv = result["argv"]
                    self.assertTrue(result["ok"])
                    self.assertEqual(argv[argv.index("--cc-sun-shadows") + 1],
                                     "1" if shadows and dynamic_lighting else "0")
                    # Dynamic lighting can separately report missing local-light catalogs.
                    shadow_skips = [item for item in result["skipped_packs"]
                                    if item.get("feature") == "sun_shadows"]
                    expected_skips = []
                    if shadows and not dynamic_lighting:
                        expected_skips.append({
                            "root": "C:\\Runtime", "feature": "sun_shadows",
                            "reason": "sun shadows require dynamic lighting",
                        })
                    self.assertEqual(shadow_skips, expected_skips)

        for dynamic_lighting in (False, True):
            with self.subTest(lighting="off", dynamic_lighting=dynamic_lighting):
                without_sun = self.plan(dict(
                    self.request(shadows=True, dynamic_lighting=dynamic_lighting),
                    lighting="off", visuals={"pom": False}))
                no_sun_argv = without_sun["argv"]
                self.assertEqual(no_sun_argv[no_sun_argv.index("--cc-sun-shadows") + 1], "0")
                shadow_skips = [item for item in without_sun["skipped_packs"]
                                if item.get("feature") == "sun_shadows"]
                self.assertEqual(shadow_skips, [{
                    "root": "C:\\Runtime", "feature": "sun_shadows",
                    "reason": "sun shadows require sun lighting",
                }])

        for value in (0, 1, 1.0, "true", None, [], {}):
            with self.subTest(shadows=value), self.assertRaises(ValueError):
                self.plan(self.request(shadows=value))

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

    def test_surface_materials_are_emitted_for_each_lod_and_first_chassis_wins(self):
        first_model = {"id": "strider", "backend": "native", "status": "runtime-ready",
                       "environment": {}}
        first_model["environment"].update(self.add_surface_material("first", "strider", 0))
        first_model["environment"].update(self.add_surface_material("first", "strider", 1))
        first = self.model_pack("first", [first_model])
        second_model = {"id": "strider", "backend": "native", "status": "runtime-ready",
                        "environment": {}}
        second_model["environment"].update(self.add_surface_material("second", "strider", 0))
        second = self.model_pack("second", [second_model])

        result = self.plan(self.request(model_packs=[first, second]))
        argv = result["argv"]
        material_bindings = [
            (argv[index + 1], argv[index + 2], argv[index + 3])
            for index, argument in enumerate(argv)
            if argument == "--cc-model-materials"
        ]
        self.assertEqual(material_bindings, [
            ("strider", "0", os.path.join(first, "payload", "materials0.bin")),
            ("strider", "1", os.path.join(first, "payload", "materials1.bin")),
        ])
        self.assertEqual(result["skipped_packs"], [])
        self.assertEqual(result["overridden_models"], [
            {"root": second, "chassis": "strider", "kept_from": first},
        ])

    @unittest.skipUnless(os.name == "nt", "isolated pack translation reads Windows paths")
    def test_surface_material_sidecar_plans_when_planner_is_alone_under_isolated_python(self):
        model = {"id": "strider", "backend": "native", "status": "runtime-ready",
                 "environment": {}}
        model["environment"].update(self.add_surface_material("isolated", "strider"))
        pack = self.model_pack("isolated", [model])
        request = self.request(model_packs=[pack])

        with tempfile.TemporaryDirectory() as isolated_directory:
            planner_copy = Path(isolated_directory) / "mw3_re_launch.py"
            shutil.copyfile(Path(__file__).with_name("mw3_re_launch.py"), planner_copy)
            isolated_script = (
                "import json, runpy, sys; "
                "planner = runpy.run_path(sys.argv[1]); "
                "print(json.dumps(planner['plan_json'](sys.stdin.read())))"
            )
            result = subprocess.run(
                [sys.executable, "-I", "-c", isolated_script, str(planner_copy)],
                input=json.dumps(request), text=True, capture_output=True, check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        plan = json.loads(result.stdout)
        self.assertTrue(plan["ok"])
        self.assertIn("--cc-model-materials", plan["argv"])
        self.assertFalse(any(item.get("feature") == "surface_materials"
                             for item in plan["skipped_packs"]))

    def test_invalid_surface_material_sidecar_is_reported_and_left_off(self):
        model = {"id": "strider", "backend": "native", "status": "runtime-ready",
                 "environment": {}}
        bindings = self.add_surface_material("invalid", "strider")
        bindings["MW34_STRIDER_SURFACE_MATERIALS"] = "payload/not-bwsfm1.bin"
        self.write("invalid/payload/not-bwsfm1.bin", b"not a sidecar")
        model["environment"].update(bindings)
        pack = self.model_pack("invalid", [model])

        result = self.plan(self.request(model_packs=[pack]))
        self.assertTrue(result["ok"])
        self.assertIn("--cc-model", result["argv"])
        self.assertNotIn("--cc-model-materials", result["argv"])
        skipped = [item for item in result["skipped_packs"]
                   if item.get("feature") == "surface_materials"]
        self.assertEqual(len(skipped), 1)
        self.assertEqual((skipped[0]["root"], skipped[0]["chassis"], skipped[0]["lod"]),
                         (pack, "strider", "0"))
        self.assertIn("invalid", skipped[0]["reason"].lower())

    def test_null_and_non_string_surface_material_entries_are_ignored(self):
        for declaration in (None, 0, [], {}, ""):
            with self.subTest(declaration=declaration):
                model = {"id": "strider", "backend": "native", "status": "runtime-ready",
                         "environment": {
                             "MW34_STRIDER_MESH": "payload/mesh0.bin",
                             "MW34_STRIDER_TEXTURES": "payload/tex0.bin",
                             "MW34_STRIDER_SURFACE_MATERIALS": declaration,
                         }}
                pack = self.model_pack(f"undeclared-{type(declaration).__name__}", [model])
                result = self.plan(self.request(model_packs=[pack]))
                self.assertTrue(result["ok"])
                self.assertIn("--cc-model", result["argv"])
                self.assertNotIn("--cc-model-materials", result["argv"])
                self.assertEqual(result["skipped_packs"], [])

        model = {"id": "strider", "backend": "native", "status": "runtime-ready",
                 "environment": {"MW34_STRIDER_SURFACE_MATERIALS": None}}
        pack = self.model_pack("null-sidecar-without-assets", [model])
        result = self.plan(self.request(model_packs=[pack]))
        self.assertTrue(result["ok"])
        self.assertEqual(result["skipped_packs"], [])

    def test_surface_material_without_matching_mesh_or_textures_is_reported(self):
        model = {"id": "strider", "backend": "native", "status": "runtime-ready",
                 "environment": {
                     "MW34_STRIDER_TEXTURES": "payload/tex0.bin",
                     "MW34_STRIDER_SURFACE_MATERIALS": "payload/materials.bin",
                 }}
        pack = self.model_pack("missing-material-mesh", [model])
        result = self.plan(self.request(model_packs=[pack]))
        skipped = [item for item in result["skipped_packs"]
                   if item.get("feature") == "surface_materials"]
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["reason"],
                         "surface-material sidecar requires its matching mesh and textures")

    def test_oversized_and_mismatched_surface_materials_are_skipped(self):
        from surface_materials import (
            mesh_uv_identity,
            pack_surface_materials,
            texture_batch_materials,
        )

        mesh, textures, valid_sidecar = self.surface_sidecar("strider:close")
        mismatched_uv_sidecar = pack_surface_materials(
            asset_id="strider:close",
            mesh_uv_hash=0,
            batch_materials=texture_batch_materials(textures),
            records=[],
        )
        mismatched_materials_sidecar = pack_surface_materials(
            asset_id="strider:close",
            mesh_uv_hash=mesh_uv_identity(mesh),
            batch_materials=["not-the-texture-material"],
            records=[],
        )
        for label, sidecar in (("oversized", valid_sidecar),
                               ("uv-mismatch", mismatched_uv_sidecar),
                               ("materials-mismatch", mismatched_materials_sidecar),
                               ("reader-typeerror", valid_sidecar)):
            with self.subTest(case=label):
                bindings = self.add_surface_material(
                    label, "strider", sidecar=(mesh, textures, sidecar))
                model = {"id": "strider", "backend": "native", "status": "runtime-ready",
                         "environment": bindings}
                pack = self.model_pack(label, [model])
                if label == "oversized":
                    with patch("mw3_re_launch.MAX_SIDECAR_BYTES", 1):
                        result = self.plan(self.request(model_packs=[pack]))
                elif label == "reader-typeerror":
                    with patch("mw3_re_launch.read_surface_materials_file",
                               side_effect=TypeError("bad sidecar value")):
                        result = self.plan(self.request(model_packs=[pack]))
                else:
                    result = self.plan(self.request(model_packs=[pack]))
                self.assertTrue(result["ok"])
                self.assertIn("--cc-model", result["argv"])
                self.assertNotIn("--cc-model-materials", result["argv"])
                skipped = [item for item in result["skipped_packs"]
                           if item.get("feature") == "surface_materials"]
                self.assertEqual(len(skipped), 1)

    def test_surface_material_reader_accepts_grayscale_v2_and_rgba_v1(self):
        from test_surface_materials import _legacy_v1_sidecar_from_v2

        _, _, sidecar = self.surface_sidecar("strider:close")
        legacy = _legacy_v1_sidecar_from_v2(sidecar)
        module = importlib.import_module("mw3_re_launch")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "height.bwsfm1"
            for payload, version in ((sidecar, 2), (legacy, 1)):
                with self.subTest(version=version):
                    path.write_bytes(payload)
                    parsed = module.read_surface_materials_file(path)
                    self.assertEqual(parsed["version"], version)

    def test_invalid_choices_are_refused(self):
        for preview in ({"draw_distance": 1000}, {"draw_distance": "1200"}, {"hud": "neon"},
                        {"hud_text": True}, {"hud": "original", "hud_text": True}, {"geometry": "gpu"},
                        {"model_packs": "C:/one"}, {"ui_packs": "C:/one"}, {"unknown": 1},
                        {"model_packs": ["relative/pack"]}):
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
        request = self.request()
        request["preview"]["model_packs"] = [os.path.join(request["write_dir"], "mods", "pack")]
        with self.assertRaises(ValueError):
            self.plan(request)

    def test_schema_four_json_round_trip(self):
        plan_json = importlib.import_module("mw3_re_launch").plan_json
        for distance in (1200, 1600, 2400, 3200):
            with self.subTest(distance=distance):
                result = plan_json(json.dumps(self.request(draw_distance=distance)))
                argument_index = result["argv"].index("--cc-draw-distance") + 1
                self.assertEqual(result["argv"][argument_index], str(distance))

    def test_draw_distance_table_matches_runtime(self):
        repository_root = Path(__file__).resolve().parents[2]
        header = repository_root / "runtime/mw3-re/src/gamez/zclass/visual_distance.h"
        source = header.read_text(encoding="utf-8")
        table = re.search(r"kViewDistanceOptions\[\]\s*=\s*\{(.*?)\};", source, re.DOTALL)
        self.assertIsNotNone(table, "Runtime view-distance table is missing")
        pairs = [(int(distance), int(start)) for distance, start in
                 re.findall(r"\{\s*(\d+)\s*,\s*(\d+)\s*\}", table.group(1))]
        expected = [(800, 700), (1200, 1050), (1600, 1450), (2400, 2250), (3200, 3050)]
        self.assertEqual(pairs, expected)
        planner_distances = importlib.import_module("mw3_re_launch")._PREVIEW_DRAW_DISTANCES
        self.assertEqual(planner_distances, tuple(distance for distance, _ in pairs))

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_dynamic_lighting_uses_enabled_pack_catalog_and_headlight_inputs(self):
        from pathlib import Path
        from build_stock_headlights import build_catalog
        environment = self.lighting_environment_pack()
        runtime = Path(self.root, "runtime")
        resources = runtime / "resources"
        resources.mkdir(parents=True)
        stock_headlight_catalog = build_catalog()
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

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_missing_declared_effect_catalog_is_reported_as_skipped(self):
        from pathlib import Path
        environment = self.lighting_environment_pack()
        (Path(environment) / "environment" / "effects.bin").unlink()
        result = self.plan(self.request(environment_packs=[environment],
                                        dynamic_lighting=True))
        self.assertTrue(result["ok"])
        self.assertIn("--cc-environment-pack", result["argv"])
        self.assertNotIn("--cc-effect-lights", result["argv"])
        skipped = [item for item in result["skipped_packs"]
                   if item.get("feature") == "effect_lights"]
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["root"], environment)
        self.assertIn("unavailable", skipped[0]["reason"])

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
        for lighting in ("off", "flat"):
            result = self.plan(dict(self.request(water_detail=True, cloud_detail=True),
                                    lighting=lighting, visuals={"pom": False}))
            self.assertEqual(result["argv"][result["argv"].index("--cc-water-detail") + 1], "0")
            self.assertEqual(result["argv"][result["argv"].index("--cc-cloud-detail") + 1], "0")
            disabled = {item["feature"]: item for item in result["skipped_packs"]}
            self.assertEqual(set(disabled), {"water_detail", "cloud_detail"})
            self.assertTrue(all("requires normal lighting" in item["reason"]
                                for item in disabled.values()))
        for field, value in (("water_detail", 1), ("cloud_detail", "true")):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "must be Boolean"):
                self.plan(self.request(**{field: value}))

    def test_surface_detail_does_not_relax_the_pom_lighting_requirement(self):
        request = self.request(water_detail=True)
        request["lighting"] = "flat"
        with self.assertRaisesRegex(ValueError, "Native POM requires normal lighting"):
            self.plan(request)

    def detail_environment_pack(self, name, roles):
        detail = {}
        files = {}
        for role in roles:
            member = f"environment/{role}.bin"
            catalog = b"BWSNR2\0\0" + (1).to_bytes(4, "little")
            self.write(f"{name}/{member}", catalog)
            detail[role] = member
            files[member] = {"bytes": len(catalog), "sha256": "0" * 64, "format": "BWSNR2"}
        registry = {"schema_version": 2, "payload_profile": "prepared-environment-v1",
                    "operation": "training", "banks": {}, "detail": detail}
        registry_bytes = json.dumps(registry).encode("utf-8")
        self.write(f"{name}/environment/environment.json", registry_bytes)
        files["environment/environment.json"] = {
            "bytes": len(registry_bytes), "sha256": "1" * 64, "format": "JSON"}
        self.write(f"{name}/pack.json", {"schema_version": 2, "files": files,
                    "native_payload": {"profile": "prepared-environment-v1",
                                       "registry": "environment/environment.json"}})
        return os.path.join(self.root, name)

    @unittest.skipUnless(os.name == "nt", "pack translation reads Windows paths")
    def test_missing_detail_roles_are_reported_and_feature_flags_stay_off(self):
        water_pack = self.detail_environment_pack("water", ("water", "surf"))
        water_result = self.plan(self.request(environment_packs=[water_pack],
                                              water_detail=True, cloud_detail=True))
        water_argv = water_result["argv"]
        self.assertEqual(water_argv[water_argv.index("--cc-water-detail") + 1], "1")
        self.assertEqual(water_argv[water_argv.index("--cc-cloud-detail") + 1], "0")
        skipped = [item for item in water_result["skipped_packs"]
                   if item.get("feature") == "cloud_detail"]
        self.assertEqual(len(skipped), 1)
        self.assertIn("cloud detail map", skipped[0]["reason"])

        complete_pack = self.detail_environment_pack(
            "complete", ("water", "surf", "cloud"))
        complete_result = self.plan(self.request(environment_packs=[complete_pack],
                                                 water_detail=True, cloud_detail=True))
        complete_argv = complete_result["argv"]
        self.assertEqual(complete_argv[complete_argv.index("--cc-water-detail") + 1], "1")
        self.assertEqual(complete_argv[complete_argv.index("--cc-cloud-detail") + 1], "1")
        self.assertEqual(complete_result["skipped_packs"], [])

        water_only_pack = self.detail_environment_pack("water-only", ("water",))
        water_only_result = self.plan(self.request(environment_packs=[water_only_pack],
                                                   water_detail=True))
        water_only_argv = water_only_result["argv"]
        self.assertEqual(water_only_argv[water_only_argv.index("--cc-water-detail") + 1], "0")
        self.assertTrue(any(item.get("feature") == "water_detail"
                            for item in water_only_result["skipped_packs"]))

    def test_missing_detail_roles_without_environment_packs_report_runtime_fallback(self):
        result = self.plan(self.request(water_detail=True, environment_packs=[]))
        argv = result["argv"]
        self.assertEqual(argv[argv.index("--cc-water-detail") + 1], "0")
        skipped = [item for item in result["skipped_packs"]
                   if item.get("feature") == "water_detail"]
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["root"], "C:\\Runtime")


if __name__ == "__main__":
    unittest.main()
