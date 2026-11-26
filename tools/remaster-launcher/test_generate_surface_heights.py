"""Asset-free unit tests for BWSFM1 height-map generation."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_surface_heights as gen
from normal_materials import pack_normals
from surface_materials import read_surface_materials


def _pack_named_bwsnr2(entries: list[tuple[tuple[int, int, int, int], str, tuple[int, int, bytes]]]) -> bytes:
    header = bytearray(b"BWSNR2\0\0" + struct.pack("<I", len(entries)))
    names = []
    images = {}
    for key, mat_name, normal in entries:
        header.extend(struct.pack("<IIIQ32s", *key, mat_name.encode("ascii")))
        names.append(mat_name)
        images[mat_name] = normal
    return bytes(header) + pack_normals(names, images)


def _make_sine_normal_map(width: int = 32, height: int = 32) -> bytes:
    """Create a synthetic tileable normal map from z(x, y) = sin(2*pi*x/w) * cos(2*pi*y/h)."""
    out = bytearray(width * height * 4)
    idx = 0
    for y in range(height):
        v = 2.0 * math.pi * y / height
        for x in range(width):
            u = 2.0 * math.pi * x / width
            dzdx = 0.4 * math.cos(u) * math.cos(v)
            dzdy = -0.4 * math.sin(u) * math.sin(v)
            nx, ny, nz = -dzdx, -dzdy, 1.0
            inv = 1.0 / math.sqrt(nx * nx + ny * ny + nz * nz)
            nx, ny, nz = nx * inv, ny * inv, nz * inv
            out[idx] = max(0, min(255, int(round(nx * 127.0 + 128.0))))
            out[idx + 1] = max(0, min(255, int(round(ny * 127.0 + 128.0))))
            out[idx + 2] = max(0, min(255, int(round(nz * 127.0 + 128.0))))
            out[idx + 3] = 255
            idx += 4
    return bytes(out)


class GenerateSurfaceHeightsTests(unittest.TestCase):
    @unittest.skipIf(gen.np is None, "NumPy is required for height-map derivation")
    def test_frankot_chellappa_reconstructs_nonflat_height(self):
        normal_bytes = _make_sine_normal_map(32, 32)
        height_bytes, ref = gen.frankot_chellappa_height(normal_bytes, 32, 32)
        self.assertEqual(len(height_bytes), 32 * 32 * 4)
        self.assertGreater(ref, 0.2)
        self.assertLess(ref, 0.8)
        red = gen.np.frombuffer(height_bytes, dtype=gen.np.uint8).reshape(32, 32, 4)[:, :, 0].astype(float)
        self.assertLess(float(red.min()), 10.0)
        self.assertGreater(float(red.max()), 245.0)
        # Verify positive correlation (> 0.95) with the ground-truth sine*cos height field.
        xs = gen.np.arange(32) * (2.0 * math.pi / 32.0)
        ys = gen.np.arange(32) * (2.0 * math.pi / 32.0)
        xx, yy = gen.np.meshgrid(xs, ys)
        gt = gen.np.sin(xx) * gen.np.cos(yy)
        corr = float(gen.np.corrcoef(red.ravel(), gt.ravel())[0, 1])
        self.assertGreater(corr, 0.95)
        # Narrow normal maps (e.g. 512x2) must downsample without reshaping errors.
        narrow = _make_sine_normal_map(512, 2)
        nw, nh, nbytes = gen._downsample_rgba(narrow, 512, 2, 128)
        self.assertEqual((nw, nh), (128, 2))
        self.assertEqual(len(nbytes), 128 * 2 * 4)

    def test_excludes_water_and_classifies_families(self):
        self.assertTrue(gen.should_skip_material("c2_water01"))
        self.assertTrue(gen.should_skip_material("sky_clouds"))
        self.assertFalse(gen.should_skip_material("c2ter01"))
        self.assertEqual(gen.classify_material_family("txwall02"), "cliff")
        self.assertEqual(gen.classify_material_family("c2rock04"), "rock")
        self.assertEqual(gen.classify_material_family("m_hq12"), "building")
        self.assertEqual(gen.classify_material_family("c2road01"), "road")
        self.assertEqual(gen.classify_material_family("c2ter01"), "terrain")

    @unittest.skipIf(gen.np is None, "NumPy is required for height-map derivation")
    def test_build_and_update_synthetic_environment_pack(self):
        with tempfile.TemporaryDirectory() as tmp:
            pack_dir = Path(tmp) / "pack"
            env_dir = pack_dir / "environment"
            env_dir.mkdir(parents=True)

            normal_bytes = _make_sine_normal_map(32, 32)
            flat_bytes = bytes([128, 128, 255, 255]) * (32 * 32)
            page = _pack_named_bwsnr2(
                [
                    ((32, 32, 1, 0x1111), "c2ter01", (32, 32, normal_bytes)),
                    ((32, 32, 1, 0x2222), "c2_water01", (32, 32, normal_bytes)),
                    ((32, 32, 1, 0x3333), "c2flat01", (32, 32, flat_bytes)),
                ]
            )
            page_path = env_dir / "world-000.bin"
            page_path.write_bytes(page)
            (env_dir / "world.txt").write_text("MW34SNP1\nworld-000.bin\n", encoding="utf-8")

            env_json = {
                "schema_version": 1,
                "payload_profile": "prepared-environment-v1",
                "operation": "operation2",
                "world_manifest": "environment/world.txt",
            }
            env_bytes = (json.dumps(env_json, indent=2) + "\n").encode("utf-8")
            (env_dir / "environment.json").write_bytes(env_bytes)

            pack_json = {
                "schema_version": 2,
                "id": "test.env.op2",
                "native_payload": {
                    "profile": "prepared-environment-v1",
                    "registry": "environment/environment.json",
                    "required_formats": ["BWSNR2"],
                },
                "files": {
                    "environment/environment.json": {
                        "bytes": len(env_bytes),
                        "sha256": hashlib.sha256(env_bytes).hexdigest(),
                        "format": "json",
                    }
                },
            }
            (pack_dir / "pack.json").write_text(json.dumps(pack_json, indent=2) + "\n", encoding="utf-8")

            sidecar, summary = gen.build_environment_surface_materials(pack_dir, max_dimension=32)
            self.assertEqual(summary["region"], "operation2")
            self.assertEqual(summary["selected_materials"], 1)
            self.assertEqual(summary["skipped_excluded"], 1)
            self.assertEqual(summary["skipped_flat"], 1)

            parsed = read_surface_materials(sidecar, expected_asset_id="operation2")
            self.assertEqual(len(parsed["records"]), 1)
            self.assertTrue(parsed["records"][0]["material_name"].startswith("n_"))
            self.assertAlmostEqual(
                parsed["records"][0]["height_amplitude"],
                gen.FAMILY_PROFILES["terrain"]["height_amplitude"],
                places=5,
            )

            manifest = gen.update_environment_pack(pack_dir, sidecar)
            self.assertIn("BWSFM1", manifest["native_payload"]["required_formats"])
            self.assertEqual(
                manifest["native_payload"]["required_capabilities"]["surface-materials"], 1
            )
            self.assertIn("environment/surface_materials.bin", manifest["files"])
            self.assertTrue((env_dir / "surface_materials.bin").is_file())

    def test_update_repins_default_registry_and_handles_null_capabilities(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "environment/environment.json"
            registry.parent.mkdir()
            registry.write_text("{}", encoding="utf-8")
            (root / "pack.json").write_text(
                '{"native_payload":{"required_capabilities":null}}', encoding="utf-8"
            )
            updated = gen.update_environment_pack(root, b"fixture")
            pin = updated["files"]["environment/environment.json"]
            raw = registry.read_bytes()
            self.assertEqual(pin["bytes"], len(raw))
            self.assertEqual(pin["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(updated["native_payload"]["required_capabilities"],
                             {"surface-materials": 1})

    def test_update_rejects_bad_capabilities_before_mutating(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "environment/environment.json"
            registry.parent.mkdir()
            registry.write_bytes(b"{}")
            manifest = root / "pack.json"
            original = b'{"native_payload":{"required_capabilities":[]}}'
            manifest.write_bytes(original)
            with self.assertRaisesRegex(ValueError, "capability requirements"):
                gen.update_environment_pack(root, b"fixture")
            self.assertEqual(registry.read_bytes(), b"{}")
            self.assertEqual(manifest.read_bytes(), original)
            self.assertFalse((root / "environment/surface_materials.bin").exists())


if __name__ == "__main__":
    unittest.main()
