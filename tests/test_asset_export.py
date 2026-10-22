"""Windows export guards and alpha preservation using authored RGBA pixels."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools/asset-inventory"
spec = importlib.util.spec_from_file_location("probe", TOOLS / "probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
sys.modules["probe"] = probe
spec = importlib.util.spec_from_file_location("decoder_export_fixture", TOOLS / "decode_images.py")
decoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decoder)
SHELL = shutil.which("pwsh") or shutil.which("powershell")


@unittest.skipUnless(os.name == "nt" and SHELL, "Windows System.Drawing exporter only")
class ExportTests(unittest.TestCase):
    def test_alpha_guards_and_no_overwrite(self):
        # Work-ahead directories may be archival junctions. Authored fixtures
        # must stay in a direct local folder so export containment is exercised.
        fixture_root = ROOT / "local/authored-test-fixtures"
        fixture_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="export-", dir=fixture_root) as directory:
            directory = Path(directory).resolve()
            self.assertTrue(directory.is_relative_to(ROOT.resolve()))
            source = directory / "authored.png"
            source.write_bytes(decoder.png_bytes(2, 2, bytes((255, 0, 0, 0, 0, 255, 0, 64,
                                                           0, 0, 255, 128, 255, 255, 255, 255))))
            destination = directory / "export.png"

            def export(path, height=8, width=8):
                return subprocess.run([SHELL, "-NoProfile", "-File", str(TOOLS / "export_preview.ps1"),
                                       "-InputPath", str(source), "-OutputPath", str(path),
                                       "-Width", str(width), "-Height", str(height), "-PreserveSourceAlpha"],
                                      capture_output=True, text=True, timeout=30)

            result = export(destination)
            self.assertEqual(result.returncode, 0, result.stderr)
            original_export = destination.read_bytes()
            self.assertEqual(struct.unpack_from(">II", original_export, 16), (8, 8))
            comparison = subprocess.run([SHELL, "-NoProfile", "-File", str(TOOLS / "compare_preview.ps1"),
                                         "-SourcePath", str(source), "-CandidatePath", str(destination)],
                                        capture_output=True, text=True, timeout=30)
            self.assertEqual(comparison.returncode, 0, comparison.stderr)
            metrics = json.loads(comparison.stdout)
            self.assertEqual(metrics["alpha_mae_against_nearest_original"], 0)
            self.assertEqual(metrics["alpha_iou_at_128"], 1)
            self.assertEqual(metrics["occupied_fraction"], 0.75)
            self.assertEqual(metrics["partial_alpha_fraction"], 0.5)
            self.assertAlmostEqual(metrics["mean_opacity"], 447 / 1020)
            self.assertNotEqual(export(destination).returncode, 0)
            self.assertEqual(destination.read_bytes(), original_export)
            self.assertNotEqual(export(directory / "bad-aspect.png", height=7).returncode, 0)
            self.assertFalse((directory / "bad-aspect.png").exists())
            self.assertNotEqual(export(directory / "bad-scale.png", height=7, width=7).returncode, 0)
            outside = ROOT / "build/asset-export-forbidden.png"
            self.assertNotEqual(export(outside).returncode, 0)
            self.assertFalse(outside.exists())


if __name__ == "__main__":
    unittest.main()
