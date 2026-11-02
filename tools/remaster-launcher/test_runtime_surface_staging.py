"""Verify that authored staging paths ship their coordinator dependencies."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import refresh_content_runtime
import stage_native_runtime


class RuntimeSurfaceStagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_refresh_pins_surface_materials(self):
        source = self.root / "source"
        coordinator = source / "coordinator"
        coordinator.mkdir(parents=True)
        (source / "profile.json").write_text(json.dumps({
            "native": {"content_capabilities": {"prepared-mechs": [1]}}
        }))
        files = {
            "profile.json": refresh_content_runtime.pin(source / "profile.json"),
        }
        (source / "runtime.json").write_text(json.dumps({
            "profile": "profile.json", "files": files,
        }))
        output = self.root / "refreshed"
        refresh_content_runtime.stage(source, output, "test-1")
        name = "coordinator/surface_materials.py"
        manifest = json.loads((output / "runtime.json").read_text())
        self.assertEqual(manifest["files"][name], refresh_content_runtime.pin(output / name))

    def test_initial_stage_pins_surface_materials(self):
        root = self.root / "inputs"
        (root / "reports/m4-crt-fdiv-entry-prefix/preparation-r2").mkdir(parents=True)
        (root / "local/remaster").mkdir(parents=True)
        executable = root / "host.exe"
        executable.write_bytes(b"fixture host")
        snapshot = root / "snapshot.json"
        snapshot.write_text("{}")
        (root / "reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-O2.obj").write_bytes(b"fixture entry")
        decoder = root / "decoder.exe"
        decoder.write_bytes(b"fixture decoder")
        (root / "local/remaster/music.json").write_text(json.dumps({"decoder": "decoder.exe"}))
        profile = root / "selected.json"
        profile.write_text(json.dumps({
            "graphics": {},
            "native": {
                "executable": str(executable),
                "executable_sha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
                "source_snapshot": str(snapshot),
                "runtime_environment": {"MW34_SEED": "host", "MW34_STARTUP": "loader"},
                "content_capabilities": {"prepared-mechs": [1]},
                "original_support_versions": [1],
            },
        }))
        python_home = root / "python"
        python_home.mkdir()
        with patch.object(stage_native_runtime, "ROOT", root):
            stage_native_runtime.stage(profile, self.root / "staged", python_home)
        output = self.root / "staged"
        name = "coordinator/surface_materials.py"
        manifest = json.loads((output / "runtime.json").read_text())
        self.assertEqual(manifest["files"][name], refresh_content_runtime.pin(output / name))


if __name__ == "__main__":
    unittest.main()
