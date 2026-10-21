"""Authored pixel oracles for native effect admission; no game media."""

from pathlib import Path
import json
import struct
import tempfile
import unittest
from prepare_effect_lights import prepare
from normal_materials import pixel_hash

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "build/default/mw34_normal_hash.dll"


@unittest.skipUnless(HELPER.exists(), "Build the offline native hash helper")
class EffectCatalogTests(unittest.TestCase):
    def fixture(self, root, *, extra=b""):
        bank = root / "effect.zbd"
        descriptor = struct.pack("<IHHIHH", 43, 8, 1, 0, 0, 0)
        rgb = struct.pack("<8H", *([0x001F] * 8))
        alpha = bytes([0, 1, 15, 16, 127, 128, 254, 255])
        bank.write_bytes(
            struct.pack("<6I", 0, 1, 0, 1, 0, 0)
            + struct.pack("<32sII", b"PPCMUZ", 64, 0xFFFFFFFF)
            + descriptor
            + rgb
            + alpha
            + extra
        )
        key = b"zbd/t1/texture.zbd"
        value = str(bank).encode()
        mapping = root / "banks.bin"
        mapping.write_bytes(
            b"MWBANK1\0" + struct.pack("<III", 1, len(key), len(value)) + key + value
        )
        return mapping

    def test_original_alpha_zero_before_packing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            mapping = self.fixture(root)
            output = root / "catalog.bin"
            prepare(mapping, output, HELPER)
            receipt = json.loads(output.with_suffix(".json").read_text())
            keys = {(x["format"], x["hash"]) for x in receipt["aliases"]}
            # Native oracle: RGB clears only for ORIGINAL alpha zero. Packed
            # zero-alpha texels with source alpha 1 or 15 retain blue RGB.
            native = struct.pack(
                "<8H", 0x0000, 0x000F, 0x000F, 0x100F, 0x700F, 0x800F, 0xF00F, 0xF00F
            )
            self.assertIn((3, pixel_hash(native)), keys)
            wrong = struct.pack("<8H", 0, 0, 0, 0x100F, 0x700F, 0x800F, 0xF00F, 0xF00F)
            self.assertNotIn((3, pixel_hash(wrong)), keys)
            with self.assertRaisesRegex(ValueError, "fresh output"):
                prepare(mapping, output, HELPER)

    def test_invalid_entry_span_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            mapping = self.fixture(root, extra=b"x")
            with self.assertRaisesRegex(ValueError, "span"):
                prepare(mapping, root / "catalog.bin", HELPER)
            self.assertFalse((root / "catalog.bin").exists())


if __name__ == "__main__":
    unittest.main()
