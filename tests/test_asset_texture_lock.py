"""Source coordinate locks and exact alpha using independently authored pixels."""
import hashlib
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
import zlib

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools/asset-inventory"
spec = importlib.util.spec_from_file_location("probe", TOOLS / "probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
sys.modules["probe"] = probe
spec = importlib.util.spec_from_file_location("decoder_texture_lock_fixture", TOOLS / "decode_images.py")
decoder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decoder)
SHELL = shutil.which("pwsh") or shutil.which("powershell")


def read_rgba_png(path):
    """Independent PNG reader for noninterlaced RGBA8, including row filters."""
    png = path.read_bytes()
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("PNG signature")
    pos, compressed = 8, b""
    while pos < len(png):
        length = struct.unpack_from(">I", png, pos)[0]
        kind, payload = png[pos + 4:pos + 8], png[pos + 8:pos + 8 + length]
        if zlib.crc32(kind + payload) != struct.unpack_from(">I", png, pos + 8 + length)[0]:
            raise ValueError("PNG CRC")
        if kind == b"IHDR":
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if (depth, color, compression, filtering, interlace) != (8, 6, 0, 0, 0):
                raise ValueError("Unsupported fixture PNG")
        if kind == b"IDAT":
            compressed += payload
        pos += length + 12
    scanlines = zlib.decompress(compressed)
    stride, previous, decoded = width * 4, bytearray(width * 4), bytearray()
    if len(scanlines) != height * (stride + 1):
        raise ValueError("PNG rows")
    for y in range(height):
        offset = y * (stride + 1)
        mode = scanlines[offset]
        row = bytearray(scanlines[offset + 1:offset + stride + 1])
        for x in range(stride):
            left = row[x - 4] if x >= 4 else 0
            above = previous[x]
            upper_left = previous[x - 4] if x >= 4 else 0
            if mode == 1:
                predictor = left
            elif mode == 2:
                predictor = above
            elif mode == 3:
                predictor = (left + above) // 2
            elif mode == 4:
                p = left + above - upper_left
                distances = (abs(p - left), abs(p - above), abs(p - upper_left))
                predictor = (left, above, upper_left)[distances.index(min(distances))]
            elif mode == 0:
                predictor = 0
            else:
                raise ValueError("PNG filter")
            row[x] = (row[x] + predictor) & 255
        decoded.extend(row)
        previous = row
    return width, height, bytes(decoded)


@unittest.skipUnless(os.name == "nt" and SHELL, "Windows System.Drawing compatibility export only")
class TextureLockTests(unittest.TestCase):
    def setUp(self):
        fixture_root = ROOT / "local/work-ahead/test-fixtures"
        fixture_root.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="lock-", dir=fixture_root)
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.source = self.directory / "authored-source.png"
        self.candidate = self.directory / "authored-candidate.png"
        self.lock_spec = self.directory / "locks.json"
        self.rgba = b"".join(bytes((20 + i, 70 + i * 2, 120 + i * 3,
                                    {0: 0, 5: 64, 10: 128}.get(i, 255))) for i in range(16))
        self.source.write_bytes(decoder.png_bytes(4, 4, self.rgba))
        self.candidate.write_bytes(decoder.png_bytes(16, 16, bytes((201, 51, 151, 255)) * 256))
        self.spec = {"version": 1, "source_sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
                     "border_pixels": 1,
                     "regions": [{"name": "authored label", "x": 1, "y": 1, "width": 1, "height": 1}]}

    def run_export(self, name="final", source_anchored=False, detail_strength=0.5, **overrides):
        self.lock_spec.write_text(json.dumps(self.spec), encoding="utf-8")
        targets = {"OutputPath": self.directory / f"{name}.png",
                   "ReportPath": self.directory / f"{name}.json",
                   "CandidateColorPath": self.directory / f"{name}-color.png",
                   "ProtectedLayerPath": self.directory / f"{name}-protection.png",
                   "LockMaskPath": self.directory / f"{name}-mask.png",
                   "SourceGridPath": self.directory / f"{name}-grid.png"}
        targets.update(overrides)
        command = [SHELL, "-NoProfile", "-File", str(TOOLS / "lock_texture_export.ps1"),
                   "-SourcePath", str(self.source), "-CandidatePath", str(self.candidate),
                   "-LockSpecPath", str(self.lock_spec)]
        for key, value in targets.items():
            command.extend(("-" + key, str(value)))
        if source_anchored:
            command.extend(("-SourceAnchoredDetail", "-DetailStrength", str(detail_strength)))
        return subprocess.run(command, capture_output=True, text=True, timeout=45), targets

    def test_exact_grid_alpha_rectangles_border_and_edit_layers(self):
        result, targets = self.run_export()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(targets["ReportPath"].read_text(encoding="utf-8"))
        self.assertEqual(report["alpha_mismatched_pixels"], 0)
        self.assertEqual(report["protected_rgb_mismatched_channels"], 0)
        self.assertEqual(report["transparent_rgb_mismatched_channels"], 0)
        images = {key: read_rgba_png(path) for key, path in targets.items() if key != "ReportPath"}
        for image in images.values():
            self.assertEqual(image[:2], (16, 16))
        for y in range(16):
            for x in range(16):
                sx, sy = x // 4, y // 4
                source = self.rgba[(sy * 4 + sx) * 4:(sy * 4 + sx + 1) * 4]
                locked = sx in (0, 3) or sy in (0, 3) or (sx, sy) == (1, 1)
                rgb = source[:3] if source[3] else b"\0\0\0"
                index = (y * 16 + x) * 4
                pixel = lambda key: images[key][2][index:index + 4]
                self.assertEqual(pixel("OutputPath"), (rgb if locked or not source[3] else bytes((201, 51, 151))) + source[3:])
                self.assertEqual(pixel("SourceGridPath"), rgb + source[3:])
                self.assertEqual(pixel("CandidateColorPath"), (bytes((201, 51, 151)) if source[3] else b"\0\0\0") + source[3:])
                self.assertEqual(pixel("ProtectedLayerPath"), rgb + source[3:] if locked else bytes(4))
                self.assertEqual(pixel("LockMaskPath"), bytes((255 if locked else 0,)) * 3 + b"\xff")
        self.assertEqual(report["protected_export_pixels"], 13 * 16)
        original = targets["OutputPath"].read_bytes()
        repeat, _ = self.run_export()
        self.assertNotEqual(repeat.returncode, 0)
        self.assertEqual(targets["OutputPath"].read_bytes(), original)

    def test_source_anchoring_rejects_coarse_recolor_and_retains_capped_detail(self):
        self.rgba = b"".join(bytes((100, 110, 120, {0: 0, 5: 64, 10: 128}.get(i, 255))) for i in range(16))
        self.source.write_bytes(decoder.png_bytes(4, 4, self.rgba))
        self.spec["source_sha256"] = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.candidate.write_bytes(decoder.png_bytes(16, 16, bytes((0, 0, 255, 255)) * 256))
        result, targets = self.run_export("anchor-solid", source_anchored=True,
                                          ResizedCandidatePath=self.directory / "anchor-solid-raw.png")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(targets["ReportPath"].read_text(encoding="utf-8"))
        detail = report["source_anchored_detail"]
        self.assertTrue(detail["enabled"])
        self.assertEqual(detail["strength"], 0.5)
        self.assertEqual(detail["residual_cap_per_channel"], 20)
        self.assertEqual(detail["baseline_rgb_sha256"], hashlib.sha256(bytes((100, 110, 120)) * 256).hexdigest())
        final = read_rgba_png(targets["OutputPath"])[2]
        raw = read_rgba_png(targets["ResizedCandidatePath"])[2]
        self.assertEqual(raw, bytes((0, 0, 255, 255)) * 256)
        for y in range(16):
            for x in range(16):
                offset = (y * 16 + x) * 4
                alpha = self.rgba[((y // 4) * 4 + x // 4) * 4 + 3]
                self.assertEqual(final[offset:offset + 4], (bytes((100, 110, 120)) if alpha else bytes(3)) + bytes((alpha,)))
        checker = b"".join(bytes((255 if (x + y) % 2 else 0,)) * 3 + b"\xff" for y in range(16) for x in range(16))
        self.candidate.write_bytes(decoder.png_bytes(16, 16, checker))
        result, targets = self.run_export("anchor-checker", source_anchored=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        final = read_rgba_png(targets["OutputPath"])[2]
        edit_color = read_rgba_png(targets["CandidateColorPath"])[2]
        for y in range(16):
            for x in range(16):
                sx, sy, offset = x // 4, y // 4, (y * 16 + x) * 4
                alpha = self.rgba[(sy * 4 + sx) * 4 + 3]
                locked = sx in (0, 3) or sy in (0, 3) or (sx, sy) == (1, 1)
                delta = 10 if (x + y) % 2 else -10
                color = bytes((100 + delta, 110 + delta, 120 + delta)) if alpha else bytes(3)
                expected = (bytes((100, 110, 120)) if locked and alpha else color) + bytes((alpha,))
                self.assertEqual(final[offset:offset + 4], expected)
                self.assertEqual(edit_color[offset:offset + 4], color + bytes((alpha,)))
        report = json.loads(targets["ReportPath"].read_text(encoding="utf-8"))
        self.assertEqual(report["alpha_mismatched_pixels"], 0)
        self.assertEqual(report["protected_rgb_mismatched_channels"], 0)
        self.assertEqual(report["transparent_rgb_mismatched_channels"], 0)
        result, targets = self.run_export("anchor-zero", source_anchored=True, detail_strength=0)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(read_rgba_png(targets["OutputPath"])[2], read_rgba_png(self.directory / "anchor-solid.png")[2])

    def test_bad_source_identity_aspect_bounds_and_destination_rejected(self):
        self.spec["source_sha256"] = "0" * 64
        result, targets = self.run_export("bad-hash")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(targets["OutputPath"].exists())
        self.spec["source_sha256"] = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.spec["regions"][0]["x"] = 4
        result, targets = self.run_export("bad-rectangle")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(targets["OutputPath"].exists())
        self.spec["regions"][0]["x"] = 1
        self.candidate.write_bytes(decoder.png_bytes(16, 15, bytes((201, 51, 151, 255)) * 240))
        result, targets = self.run_export("bad-aspect")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(targets["OutputPath"].exists())
        forbidden = ROOT / "build/texture-lock-forbidden.png"
        result, _ = self.run_export("bad-destination", OutputPath=forbidden)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(forbidden.exists())


if __name__ == "__main__":
    unittest.main()
