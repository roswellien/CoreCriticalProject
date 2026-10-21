"""Authored fixtures for automatic relief and complete bank-content matching."""

from pathlib import Path
import json
import hashlib
import struct
import tempfile
import unittest

try:
    import numpy as np
except ImportError:
    np = None

from prepare_world_normals import generate_normal, prepare
from normal_materials import read_surface_bindings, pixel_hash

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipIf(np is None, "Offline material preparation requires NumPy")
class WorldNormalTests(unittest.TestCase):
    def test_flat_surface_and_capped_relief(self):
        flat = np.full((16, 16), 0x7BEF, dtype="<u2")
        w, h, pixels = generate_normal(flat.tobytes(), 16, 16, 1, terrain=True)
        self.assertEqual((w, h), (16, 16))
        self.assertEqual(pixels, bytes([128, 128, 255, 255]) * 256)
        pattern = np.zeros((32, 32), dtype="<u2")
        pattern[8:24, 8:24] = 65535
        for terrain, bound in [(False, 0.15), (True, 0.35)]:
            _, _, raw = generate_normal(pattern.tobytes(), 32, 32, 1, terrain=terrain)
            pixels = np.frombuffer(raw, dtype="uint8").reshape(32, 32, 4)
            normals = pixels[:, :, :3].astype("float64") / 127.5 - 1
            slopes = np.linalg.norm(normals[:, :, :2], axis=-1) / normals[:, :, 2]
            self.assertLessEqual(float(slopes.max()), bound + 0.015)
            self.assertGreater(float(slopes.max()), 0.03)
            if not terrain:
                self.assertTrue(np.all(pixels[:2, :, :3] == [128, 128, 255]))

    def test_resampling_preserves_aspect_and_data_orientation(self):
        # Transposing a material swaps its tangent axes; neither convention flips.
        pattern = np.zeros((32, 64), dtype="<u2")
        pattern[:, 16:40] = 65535
        w, h, a = generate_normal(pattern.tobytes(), 64, 32, 1, terrain=True, max_size=32)
        x, y, b = generate_normal(pattern.T.copy().tobytes(), 32, 64, 1, terrain=True, max_size=32)
        self.assertEqual((w, h, x, y), (32, 16, 16, 32))
        a = np.frombuffer(a, dtype="uint8").reshape(h, w, 4)
        b = np.frombuffer(b, dtype="uint8").reshape(y, x, 4).transpose(1, 0, 2)
        self.assertTrue(np.array_equal(a[:, :, 0], b[:, :, 1]))
        self.assertTrue(np.array_equal(a[:, :, 1], b[:, :, 0]))

    @unittest.skipUnless(
        (ROOT / "build/default/mw34_normal_hash.dll").exists(), "Build the offline hash helper"
    )
    def test_bank_identity_exclusions_and_alpha_candidates(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            bank = root / "bank.bin"
            names = ["GROUND", "cutout", "SKY"]
            table_end = 24 + 40 * len(names)
            colour = struct.pack("<4H", 0, 65535, 0x1234, 0x7654)
            payloads = [
                struct.pack("<IHHIHH", 0x25, 2, 2, 0, 0, 0) + colour,
                struct.pack("<IHHIHH", 0x2B, 2, 2, 0, 0, 0) + colour + bytes([0, 255, 64, 192]),
                struct.pack("<IHHIHH", 0x25, 2, 2, 0, 0, 0) + colour,
            ]
            data = bytearray(struct.pack("<6I", 0, 1, 0, 3, 0, 0))
            offset = table_end
            for name, payload in zip(names, payloads):
                data.extend(struct.pack("<32sII", name.encode(), offset, 0xFFFFFFFF))
                offset += len(payload)
            for payload in payloads:
                data.extend(payload)
            bank.write_bytes(data)
            before = hashlib.sha256(data).hexdigest()
            banks = root / "banks.json"
            banks.write_text(
                json.dumps(
                    [
                        dict(
                            source=str(bank),
                            target="zbd/t1/texture.zbd",
                            bank="texture",
                            expected_sha256=before,
                            installed_AI=True,
                        )
                    ]
                )
            )
            inventory = root / "inventory.json"
            inventory.write_text(
                json.dumps(
                    {
                        "textures": [
                            dict(name=n.lower(), category=c, scene_referenced_regions=["t1"])
                            for n, c in zip(
                                names,
                                [
                                    "terrain_marked_world_geometry",
                                    "other_environment_or_unclassified",
                                    "sky_candidate",
                                ],
                            )
                        ]
                    }
                )
            )
            result = prepare(
                banks, inventory, root / "output", ROOT / "build/default/mw34_normal_hash.dll"
            )
            self.assertEqual(result["unique_bindings"], 3)  # shared RGB565 plus both alpha formats
            self.assertEqual(result["exclusions"], {"sky_candidate": 1})
            self.assertEqual(hashlib.sha256(bank.read_bytes()).hexdigest(), before)
            entries = read_surface_bindings((root / "output/page-000.bin").read_bytes())
            self.assertEqual({k[2] for k, _ in entries}, {1, 2, 3})
            self.assertIn((2, 2, 1, pixel_hash(colour)), [key for key, _ in entries])
            with self.assertRaises(ValueError):
                prepare(
                    banks, inventory, root / "output", ROOT / "build/default/mw34_normal_hash.dll"
                )


if __name__ == "__main__":
    unittest.main()
