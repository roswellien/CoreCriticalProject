"""Asset-free checks for source packaging, configured paths and Studio boundaries."""

import hashlib
import http.client
import http.server
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "games/mw3/mod-tools"))
from editor import config
from editor.core.map_pack import MapPackBuilder, MapPackProject, pack_directory
import run_studio


def load_release_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"tools/release/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_release_module("build_mod_tools")
setup = load_release_module("setup_mod_tools")


class ReleaseToolsTests(unittest.TestCase):
    def test_package_exact_inventory_and_reproducibility(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            first = builder.build(output / "first")
            second = builder.build(output / "second")
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as package:
                names = set(package.namelist())
                manifest = json.loads(builder.MANIFEST.read_text())
                self.assertEqual(names, set(manifest["files"]) | {"PACKAGE-CONTENTS.json"})
                self.assertFalse(any(name.startswith(("local/", "MW3/", "reports/", "mods/"))
                                     or name.endswith((".exe", ".dll", ".zbd", "game_assets_3d.json"))
                                     for name in names))
                for entry in json.loads(package.read("PACKAGE-CONTENTS.json"))["files"]:
                    self.assertEqual(hashlib.sha256(package.read(entry["path"])).hexdigest(), entry["sha256"])
            with self.assertRaisesRegex(ValueError, "already exist"):
                builder.build(output / "first")

    def test_package_rejects_path_escape_and_duplicates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "a.py").write_text("# authored fixture\n")
            for files in (["../outside"], ["C:/outside"], ["a.py", "a.py"], ["missing.py"]):
                manifest = root / "files.json"
                manifest.write_text(json.dumps({"schema_version": 1, "files": files}))
                with self.assertRaises(ValueError):
                    builder.package_entries(root, manifest)

    def test_settings_are_local_and_explicit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            settings = root / "settings.json"
            with patch.dict(os.environ, {"MW34_MOD_TOOLS_CONFIG": str(settings)}):
                self.assertEqual(config.load_settings(), {})
                setup.write_settings(settings, {"schema_version": 1, "game_root": str(root / "owned game"),
                                                "mech3ax_dir": str(root / "tools")})
                # Windows runners may supply an 8.3 temporary path. The API
                # returns resolved paths, so compare the same canonical form.
                self.assertEqual(config.game_directory(), (root / "owned game").resolve())
                self.assertEqual(config.tool_directory(), (root / "tools").resolve())
                settings.write_text('{"schema_version":99}')
                with self.assertRaisesRegex(ValueError, "Unsupported"):
                    config.load_settings()

    def test_setup_rejects_unknown_converter_without_executing_it(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "zbd").mkdir()
            for file in ("reader.zbd", "rimage.zbd"):
                (root / "zbd" / file).write_bytes(b"authored fixture only")
            (root / "unzbd.exe").write_bytes(b"never execute this fixture")
            with self.assertRaisesRegex(ValueError, "does not match"):
                setup.validate_inputs(root, root)

    def test_pack_validation_precedes_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for pack_id in ("../escape", "nested/path", "x&echo", "", "a" * 65, "é"):
                with self.assertRaises(ValueError):
                    pack_directory(root, pack_id)
            self.assertEqual(
                pack_directory(root, "authored-map_1"), (root / "authored-map_1").resolve()
            )
            pack_builder = MapPackBuilder(packs_root=root / "packs", game_root=root / "game")
            project = MapPackProject("safe_id", "A title & a command")
            project.lighting.strength = "1 & command"
            with self.assertRaisesRegex(ValueError, "finite numbers"):
                pack_builder.build(project)
            self.assertFalse((root / "packs/safe_id").exists())
            project.base_operation = "../../escape"
            with self.assertRaisesRegex(ValueError, "base operation"):
                pack_builder.build(project)


class StudioBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root_patch = patch.object(run_studio, "PROJECT_ROOT", Path(self.temporary.name))
        self.root_patch.start()
        self.server = http.server.HTTPServer(("127.0.0.1", 0), run_studio.StudioRequestHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.root_patch.stop()
        self.temporary.cleanup()

    def request(self, path, body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            connection.request("POST" if body is not None else "GET", path, body=body,
                               headers=headers or {})
            response = connection.getresponse()
            return response.status, response.read(), dict(response.getheaders())
        finally:
            connection.close()

    def test_local_preview_still_serves(self):
        status, body, headers = self.request("/api/list-packs")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["packs"], [])
        self.assertNotIn("Access-Control-Allow-Origin", headers)
        self.assertEqual(self.request("/")[0], 200)

    def test_cross_origin_host_body_and_traversal_are_rejected(self):
        self.assertEqual(self.request("/", headers={"Host": "untrusted.example"})[0], 403)
        json_headers = {"Content-Type": "application/json"}
        headers = {**json_headers, "Origin": "https://untrusted.example"}
        self.assertEqual(self.request("/api/export-pack", "{}", headers)[0], 403)
        self.assertEqual(self.request("/api/export-pack", "{}")[0], 415)
        self.assertEqual(self.request("/api/export-pack", "[]", json_headers)[0], 400)
        self.assertEqual(self.request("/api/export-pack", "{", json_headers)[0], 400)
        self.assertEqual(self.request("/api/export-pack", "", {**json_headers, "Content-Length": "1048577"})[0], 400)
        with patch.object(run_studio.subprocess, "Popen") as launch:
            self.assertEqual(self.request("/api/launch-map", '{"pack_id":"../escape"}', json_headers)[0], 400)
            launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
