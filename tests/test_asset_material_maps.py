"""Authored data-map fixtures verify derivatives, signs and export guards."""
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

from test_asset_texture_lock import decoder, read_rgba_png

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools/asset-inventory"
SHELL = shutil.which("pwsh") or shutil.which("powershell")


@unittest.skipUnless(os.name == "nt" and SHELL, "Windows System.Drawing material export only")
class MaterialMapTests(unittest.TestCase):
    def setUp(self):
        fixtures = ROOT / "local/work-ahead/test-fixtures"
        fixtures.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="materials-", dir=fixtures)
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.height = self.directory / "authored-height.png"
        self.color = self.directory / "authored-color.png"
        self.color.write_bytes(decoder.png_bytes(8, 8, bytes((83, 123, 173, 255)) * 64))
        self.original_color = self.color.read_bytes()
        self.write_gray(lambda x, y: 128)

    def write_gray(self, formula, width=8, height=8):
        self.height.write_bytes(decoder.png_bytes(width, height,
                                                b"".join(bytes((formula(x, y),)) * 3 + b"\xff"
                                                         for y in range(height) for x in range(width))))

    def export(self, name="maps", **options):
        output = self.directory / name
        arguments = {"HeightPath": self.height, "ColorPath": self.color,
                     "ExpectHeightSha256": hashlib.sha256(self.height.read_bytes()).hexdigest(),
                     "ExpectColorSha256": hashlib.sha256(self.color.read_bytes()).hexdigest(),
                     "OutputDir": output, "FlatBorderPixels": 0}
        arguments.update(options)
        command = [SHELL, "-NoProfile", "-File", str(TOOLS / "export_material_maps.ps1")]
        for key, value in arguments.items():
            command.extend(("-" + key, str(value)))
        result = subprocess.run(command, capture_output=True, text=True, timeout=45)
        self.assertEqual(self.color.read_bytes(), self.original_color)
        return result, output

    def test_flat_data_pngs_without_gamma_and_input_unchanged(self):
        result, output = self.export(HeightChannel="StrictGrayscale")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(read_rgba_png(output / "height.png"), (8, 8, bytes((128, 128, 128, 255)) * 64))
        self.assertEqual(read_rgba_png(output / "normal-plus-y.png"), (8, 8, bytes((128, 128, 255, 255)) * 64))
        self.assertEqual(read_rgba_png(output / "normal-minus-y.png"), (8, 8, bytes((128, 127, 255, 255)) * 64))
        for filename in ("height.png", "normal-plus-y.png", "normal-minus-y.png"):
            png = (output / filename).read_bytes()
            pos, chunks = 8, []
            while pos < len(png):
                length = struct.unpack_from(">I", png, pos)[0]
                chunks.append(png[pos + 4:pos + 8])
                pos += length + 12
            self.assertEqual(set(chunks), {b"IHDR", b"IDAT", b"IEND"})
        report = json.loads((output / "export-report.json").read_text(encoding="utf-8"))
        self.assertTrue(report["albedo_unchanged"])
        self.assertEqual(report["metrics"]["height_min"], 128)
        self.assertEqual(report["metrics"]["height_max"], 128)
        original = (output / "normal-plus-y.png").read_bytes()
        result, _ = self.export(HeightChannel="StrictGrayscale")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((output / "normal-plus-y.png").read_bytes(), original)

    def test_central_ramp_signs_unit_length_green_pair_and_collar(self):
        self.write_gray(lambda x, y: 32 + x * 8 + y * 12)
        result, output = self.export("ramp", Strength=8)
        self.assertEqual(result.returncode, 0, result.stderr)
        plus = read_rgba_png(output / "normal-plus-y.png")[2]
        minus = read_rgba_png(output / "normal-minus-y.png")[2]
        dx, dy = 8 / 255, 12 / 255
        vector = (-8 * dx, 8 * dy, 1)
        length = math.sqrt(sum(value * value for value in vector))
        expected = tuple(math.floor((value / length * 0.5 + 0.5) * 255 + 0.5) for value in vector)
        center = (3 * 8 + 3) * 4
        self.assertEqual(plus[center:center + 4], bytes(expected) + b"\xff")
        self.assertLess(plus[center], 128)
        self.assertGreater(plus[center + 1], 128)
        for index in range(0, len(plus), 4):
            self.assertEqual(plus[index], minus[index])
            self.assertEqual(plus[index + 2], minus[index + 2])
            self.assertEqual(plus[index + 1] + minus[index + 1], 255)
            decoded = tuple(value / 127.5 - 1 for value in plus[index:index + 3])
            self.assertLessEqual(abs(math.sqrt(sum(value * value for value in decoded)) - 1), math.sqrt(3) / 255)
        result, collared = self.export("collared", Strength=8, FlatBorderPixels=1)
        self.assertEqual(result.returncode, 0, result.stderr)
        with_collar = read_rgba_png(collared / "normal-plus-y.png")[2]
        self.assertEqual((output / "height.png").read_bytes(), (collared / "height.png").read_bytes())
        for y in range(8):
            for x in range(8):
                i = (y * 8 + x) * 4
                self.assertEqual(with_collar[i:i + 4], bytes((128, 128, 255, 255)) if x in (0, 7) or y in (0, 7) else plus[i:i + 4])
        report = json.loads((collared / "export-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["metrics"]["flat_border_pixels_checked"], 28)
        result, flat = self.export("zero-strength", Strength=0)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(read_rgba_png(flat / "normal-plus-y.png")[2], bytes((128, 128, 255, 255)) * 64)

    def test_red_channel_is_explicit_and_transparency_rejected(self):
        self.height.write_bytes(decoder.png_bytes(8, 8, bytes((71, 137, 211, 255)) * 64))
        result, strict = self.export("strict-tint", HeightChannel="StrictGrayscale")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((strict / "height.png").exists())
        result, red = self.export("red-tint", HeightChannel="RedChannel")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(read_rgba_png(red / "height.png")[2], bytes((71, 71, 71, 255)) * 64)
        report = json.loads((red / "export-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["height_channel"], "RedChannel")
        self.assertEqual(report["authored_non_grayscale_pixels"], 64)
        self.assertEqual(report["authored_max_rgb_channel_spread"], 140)
        self.height.write_bytes(decoder.png_bytes(8, 8, bytes((71, 71, 71, 254)) * 64))
        result, transparent = self.export("bad-alpha")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((transparent / "height.png").exists())

    def test_aspect_bounds_expected_identity_and_output_roots(self):
        result, output = self.export("bad-hash", ExpectHeightSha256="0" * 64)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((output / "height.png").exists())
        result, output = self.export("bad-color-hash", ExpectColorSha256="0" * 64)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((output / "height.png").exists())
        result, output = self.export("bad-strength", Strength=-1)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((output / "height.png").exists())
        result, output = self.export("bad-collar", FlatBorderPixels=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((output / "height.png").exists())
        forbidden = ROOT / "build/material-export-forbidden"
        result, _ = self.export("bad-root", OutputDir=forbidden)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((forbidden / "height.png").exists())
        self.write_gray(lambda x, y: 128, width=8, height=7)
        result, output = self.export("bad-aspect")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((output / "height.png").exists())
        self.write_gray(lambda x, y: 128, width=4, height=4)
        result, output = self.export("sized-height", HeightChannel="StrictGrayscale")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(read_rgba_png(output / "height.png"), (8, 8, bytes((128, 128, 128, 255)) * 64))
        oversized = bytearray(self.height.read_bytes())
        struct.pack_into(">I", oversized, 16, 8193)
        self.height.write_bytes(oversized)
        result, output = self.export("oversized-header")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dimensions exceed", result.stderr)
        self.assertFalse((output / "height.png").exists())


if __name__ == "__main__":
    unittest.main()
