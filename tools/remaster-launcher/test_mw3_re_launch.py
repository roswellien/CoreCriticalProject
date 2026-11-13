"""Exercise the native-only, non-executing argv boundary with authored paths."""

import copy
import importlib
import importlib.util
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
