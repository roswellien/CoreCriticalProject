"""Exercise the native-only, non-executing argv boundary with authored paths."""

import copy
import importlib
import importlib.util
import json
import os
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
        for key, value in [("window_mode", "fullscreen"), ("window_mode", "borderless"), ("aa", "8")]:
            request = dict(self.request(), **{key: value})
            before = copy.deepcopy(request)
            result = plan(request)
            with self.subTest(key=key, value=value):
                self.assertFalse(result["ok"])
                self.assertTrue(result["reasons"])
                self.assertNotIn("argv", result)
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


if __name__ == "__main__":
    unittest.main()
