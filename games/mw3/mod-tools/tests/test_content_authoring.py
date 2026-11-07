"""Asset-free path checks and actual native-CLI integration when explicitly supplied."""

import json
import os
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from editor.core.content_authoring import (
    ContentAuthoring,
    ContentToolError,
    templates,
)


class ContentAuthoringTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.install = self.root / "original"
        self.install.mkdir()
        (self.install / "untouched").write_bytes(b"original bytes")
        self.config = self.root / "settings.json"
        self.previous = os.environ.get("MW34_MOD_TOOLS_CONFIG")
        os.environ["MW34_MOD_TOOLS_CONFIG"] = str(self.config)
        self.config.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "game_root": str(self.install),
                    "content_workspace": str(self.root / "workspace"),
                    "content_tool": os.environ.get("MW3CONTENT", ""),
                }
            )
        )

    def tearDown(self):
        self.assertEqual((self.install / "untouched").read_bytes(), b"original bytes")
        if self.previous is None:
            os.environ.pop("MW34_MOD_TOOLS_CONFIG", None)
        else:
            os.environ["MW34_MOD_TOOLS_CONFIG"] = self.previous
        self.temporary.cleanup()

    def test_workspace_paths_and_install_are_confined(self):
        authoring = ContentAuthoring()
        for name in ("../original/untouched", "/absolute", "C:\\absolute", "nested/../../outside"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                authoring.path(name)
        with self.assertRaises(ValueError):
            authoring.save("../escape", {})
        saved = authoring.save("authored", templates()["package"])
        self.assertTrue(Path(saved["source"]).is_relative_to(self.root / "workspace"))
        payload = Path(saved["source"]).with_name("pack.tmp")
        payload.write_bytes(b"authored payload")
        authoring.save("authored", templates()["package"])
        self.assertEqual(payload.read_bytes(), b"authored payload")
        config = json.loads(self.config.read_text())
        config["content_workspace"] = str(self.install / "mods")
        self.config.write_text(json.dumps(config))
        with self.assertRaises(ValueError):
            ContentAuthoring()

    def test_arena_playtest_roles_use_native_arguments_and_separate_writes(self):
        runtime = self.root / "mw3.exe"
        runtime.write_bytes(b"test fixture")
        settings = json.loads(self.config.read_text())
        settings["native_runtime"] = str(runtime)
        self.config.write_text(json.dumps(settings))
        authoring = ContentAuthoring()
        resolved = {
            "content": {
                "definitions": [
                    {"kind": "mission", "id": "demo:arena", "data": {"multiplayer": True}}
                ]
            }
        }
        with (
            mock.patch.object(authoring, "cli", return_value=resolved),
            mock.patch("editor.core.content_authoring.subprocess.Popen") as spawn,
        ):
            spawn.return_value.poll.return_value = None
            spawn.return_value.pid = 123
            with self.assertRaises(ValueError):
                authoring.playtest("profiles/arena.json", "demo:arena")
            spawn.assert_not_called()
            host = authoring.playtest(
                "profiles/arena.json", "demo:arena", {"mode": "host", "port": 27888}
            )
            host_arguments = spawn.call_args.args[0]
            self.assertIn("--host", host_arguments)
            self.assertNotIn("--assets", host_arguments)
            self.assertEqual(host_arguments[host_arguments.index("--net-wait") + 1], "2")
            joined = authoring.playtest(
                "profiles/arena.json", "demo:arena", {"mode": "join", "address": "127.0.0.1:27888"}
            )
            self.assertNotEqual(host["log"], joined["log"])
            self.assertIn("--join", spawn.call_args.args[0])
            with self.assertRaises(ValueError):
                authoring.playtest("profiles/arena.json", "demo:arena", {"mode": "host"})
            with self.assertRaises(ValueError):
                authoring.playtest(
                    "profiles/arena.json", "demo:arena", {"mode": "join", "players": 9}
                )

    def test_native_api_checks_origin_and_returns_authored_templates(self):
        import http.server

        from run_studio import StudioRequestHandler

        server = http.server.HTTPServer(("127.0.0.1", 0), StudioRequestHandler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with urllib.request.urlopen(base + "/api/content/templates") as response:
                payload = json.load(response)
            self.assertEqual(payload["templates"]["package"]["schema_version"], 3)
            request = urllib.request.Request(
                base + "/api/content",
                data=b'{"action":"save","project_id":"http-demo","source":{}}',
                headers={"Content-Type": "application/json", "Origin": "https://untrusted.invalid"},
            )
            with self.assertRaises(urllib.error.HTTPError) as refused:
                urllib.request.urlopen(request)
            self.assertEqual(refused.exception.code, 403)
            refused.exception.close()
            self.assertFalse((self.root / "workspace").exists())
            request.remove_header("Origin")
            request.add_header("Origin", base)
            with urllib.request.urlopen(request) as response:
                result = json.load(response)
            self.assertEqual(result["status"], "ok")
            self.assertTrue((self.root / "workspace/sources/http-demo/pack.json").is_file())
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)

    @unittest.skipUnless(
        os.environ.get("MW3CONTENT"), "Supply MW3CONTENT for real native CLI integration"
    )
    def test_native_compile_install_profile_and_rejected_pin_preserves_save(self):
        authoring = ContentAuthoring()
        starters = templates()
        source = starters["package"]
        source["definitions"] = [value for value in starters.values() if "kind" in value]
        authoring.save("authored", source)
        authoring.compile("authored")
        authoring.install("authored")
        exported = authoring.package("authored")
        self.assertTrue(Path(exported["output"]).is_file())
        profile = templates()["profile"]
        profile["packages"] = [{"id": source["id"], "version": source["version"]}]
        profile["selections"] = {"hud": "my-mod:wide-hud"}
        authoring.save_profile("profiles/test.json", profile)
        saved = authoring.path("profiles/test.json").read_bytes()
        neighboring_profile = authoring.path("profiles/test.staging.json")
        neighboring_profile.write_bytes(b"existing profile")
        profile["packages"][0]["version"] = "99.0.0"
        with self.assertRaises(ContentToolError):
            authoring.save_profile("profiles/test.json", profile)
        self.assertEqual(authoring.path("profiles/test.json").read_bytes(), saved)
        self.assertEqual(neighboring_profile.read_bytes(), b"existing profile")
        result = authoring.cli(
            "inspect",
            str(authoring.path("profiles/test.json")),
            "--store",
            str(authoring.path("store")),
        )
        self.assertTrue(result["ok"])

    @unittest.skipUnless(
        os.environ.get("MW3CONTENT"), "Supply MW3CONTENT for real native CLI integration"
    )
    def test_dependency_rebuild_and_export_preserve_previous_artifacts(self):
        authoring = ContentAuthoring()
        dependency = templates()["package"]
        dependency["id"] = "shared-items"
        authoring.save("shared", dependency)
        authoring.compile("shared")
        authoring.install("shared")
        source = templates()["package"]
        source["dependencies"] = [{"id": "shared-items", "min_version": "1.0.0"}]
        authoring.save("dependent", source)
        first = authoring.compile("dependent")
        first_export = authoring.package("dependent")
        original_manifest = Path(first["output"], "pack.json").read_bytes()
        original_export = Path(first_export["output"]).read_bytes()
        source["version"] = "1.1.0"
        authoring.save("dependent", source)
        second = authoring.compile("dependent")
        second_export = authoring.package("dependent")
        repeated_export = authoring.package("dependent")
        self.assertNotEqual(first["output"], second["output"])
        self.assertNotEqual(first_export["output"], second_export["output"])
        self.assertNotEqual(second_export["output"], repeated_export["output"])
        self.assertIn("1.1.0", Path(second_export["output"]).name)
        self.assertEqual(Path(first["output"], "pack.json").read_bytes(), original_manifest)
        self.assertEqual(Path(first_export["output"]).read_bytes(), original_export)
        receipt = authoring.path("compiled/dependent/latest.json").read_bytes()
        source["dependencies"][0]["version"] = "99.0.0"
        authoring.save("dependent", source)
        with self.assertRaises(ContentToolError):
            authoring.compile("dependent")
        self.assertEqual(authoring.path("compiled/dependent/latest.json").read_bytes(), receipt)
        installed = authoring.install("dependent")
        self.assertEqual(installed["version"], "1.1.0")
        profile = templates()["profile"]
        profile["packages"] = [{"id": "my-mod", "version": "1.1.0", "path": second["output"]}]
        saved_result = authoring.save_profile("profiles/pinned.json", profile)
        saved = json.loads(authoring.path("profiles/pinned.json").read_text())
        self.assertEqual(saved_result["profile"], saved)
        self.assertEqual({pin["id"] for pin in saved["packages"]}, {"my-mod", "shared-items"})
        self.assertTrue(all(len(pin["sha256"]) == 64 for pin in saved["packages"]))
        self.assertEqual(
            next(pin for pin in saved["packages"] if pin["id"] == "my-mod")["path"],
            second["output"],
        )
        dependency["version"] = "2.0.0"
        authoring.save("shared", dependency)
        authoring.compile("shared")
        authoring.install("shared")
        authoring.save_profile("profiles/pinned.json", saved_result["profile"])
        resolved = authoring.cli(
            "resolve",
            str(authoring.path("profiles/pinned.json")),
            "--store",
            str(authoring.path("store")),
        )
        library = next(
            pin for pin in resolved["content"]["lock"]["packages"] if pin["id"] == "shared-items"
        )
        self.assertEqual(library["version"], "1.0.0")


if __name__ == "__main__":
    unittest.main()
