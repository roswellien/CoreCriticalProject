"""Tests for terrain height map derivation and BWSFM1 generation."""

from pathlib import Path
import struct
import tempfile
import unittest

try:
    import numpy as np
except ImportError:
    np = None

from surface_materials import (
    read_surface_materials,
    ROLE_HEIGHT,
    ADDRESS_WRAP,
    MAX_IMAGES,
)
from normal_materials import pack_surface_bindings
from terrain_height_maps import (
    frankot_chellappa,
    extract_color_highpass,
    derive_height_map,
    evaluate_height_quality,
    classify_material_family,
    build_region_terrain_sidecar,
    FAMILY_PROFILES,
)


@unittest.skipIf(np is None, "Terrain height-map derivation requires NumPy")
class TerrainHeightMapsTests(unittest.TestCase):
    def test_frankot_chellappa_synthetic_reconstruction(self):
        w, h = 64, 64
        x = np.arange(w)
        y = np.arange(h)
        X, Y = np.meshgrid(x, y)
        z_true = np.sin(2.0 * np.pi * X / w) * np.cos(2.0 * np.pi * Y / h)

        # Analytical derivatives
        dz_dx = (2.0 * np.pi / w) * np.cos(2.0 * np.pi * X / w) * np.cos(2.0 * np.pi * Y / h)
        dz_dy = -(2.0 * np.pi / h) * np.sin(2.0 * np.pi * X / w) * np.sin(2.0 * np.pi * Y / h)
        denom = np.sqrt(dz_dx**2 + dz_dy**2 + 1.0)
        nx = -dz_dx / denom
        ny = -dz_dy / denom
        nz = 1.0 / denom

        z_rec = frankot_chellappa(nx, ny, nz)
        z_rec -= np.mean(z_rec)

        corr = np.corrcoef(z_true.flatten(), z_rec.flatten())[0, 1]
        self.assertGreater(corr, 0.999)

    def test_extract_color_highpass_dc_suppression(self):
        w, h = 32, 32
        # Constant flat colour has zero AC/detail
        flat_color = bytes([180, 120, 70, 255] * (w * h))
        detail = extract_color_highpass(flat_color, w, h)
        self.assertEqual(detail.shape, (h, w))
        self.assertAlmostEqual(float(np.max(np.abs(detail))), 0.0, places=5)

        # High-frequency alternating pattern preserves signal
        checker_bytes = bytearray()
        for j in range(h):
            for i in range(w):
                val = 255 if (i + j) % 2 == 0 else 0
                checker_bytes.extend([val, 128, 128, 255])
        checker_detail = extract_color_highpass(bytes(checker_bytes), w, h)
        self.assertGreater(float(np.std(checker_detail)), 0.5)

    def test_derive_height_map_structure_and_quality(self):
        w, h = 32, 32
        # Normal map pointing straight up (0, 0, 1) -> (128, 128, 255, 255)
        flat_normals = bytes([128, 128, 255, 255] * (w * h))
        h_bytes, h_ref, metrics = derive_height_map(flat_normals, w, h)

        self.assertEqual(len(h_bytes), w * h * 4)
        self.assertAlmostEqual(h_ref, 0.5, places=2)
        self.assertIn("raw_std", metrics)

        quality = evaluate_height_quality(h_bytes, flat_normals, w, h)
        self.assertIn("median_angular_error_deg", quality)
        self.assertIn("correlation_x", quality)
        self.assertLess(quality["median_angular_error_deg"], 5.0)

    def test_classify_material_family(self):
        self.assertEqual(classify_material_family("txwall06_cliff"), "cliff")
        self.assertEqual(classify_material_family("txgter_1_variant"), "terrain")
        self.assertEqual(classify_material_family("beach01_sand"), "sand")
        self.assertEqual(classify_material_family("hwy_road_asphalt"), "road")
        self.assertEqual(classify_material_family("unknown_prop_32"), "default")

    def test_build_region_terrain_sidecar_roundtrip_and_determinism(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            w, h = 16, 16

            # Build a valid normal page containing 2 textures
            n1 = bytes([128, 128, 255, 255] * (w * h))
            n2 = bytes([160, 100, 220, 255] * (w * h))
            entries = [
                ((w, h, 1, 0x1111222233334444), (w, h, n1)),
                ((w, h, 1, 0x5555666677778888), (w, h, n2)),
            ]
            page_data = pack_surface_bindings(entries)
            page_file = temp_path / "normals-000.bin"
            page_file.write_bytes(page_data)

            # Generate sidecar
            sidecar_bytes_1, report_1 = build_region_terrain_sidecar("training", [page_file])
            sidecar_bytes_2, report_2 = build_region_terrain_sidecar("training", [page_file])

            # Determinism check
            self.assertEqual(sidecar_bytes_1, sidecar_bytes_2)
            self.assertEqual(report_1, report_2)

            # Validate header and round-trip
            self.assertTrue(sidecar_bytes_1.startswith(b"BWSFM1\0\0"))
            verified = read_surface_materials(sidecar_bytes_1, expected_asset_id="training")
            self.assertEqual(len(verified["records"]), 2)
            self.assertEqual(len(verified["images"]), 2)

            rec0 = verified["records"][0]
            self.assertEqual(rec0["asset_id"], "training")
            self.assertEqual(rec0["address_mode_u"], ADDRESS_WRAP)
            self.assertEqual(rec0["address_mode_v"], ADDRESS_WRAP)
            self.assertIn("roughness", rec0)
            self.assertIn("reflectivity", rec0)
            self.assertIn("metallic", rec0)
            self.assertGreaterEqual(rec0["roughness"], 0.0)
            self.assertLessEqual(rec0["roughness"], 1.0)

            img0 = verified["images"][0]
            self.assertEqual(img0["role"], ROLE_HEIGHT)
            self.assertEqual(img0["width"], w)
            self.assertEqual(img0["height"], h)

    def test_refuse_invalid_region_or_truncated_data(self):
        with self.assertRaises(ValueError):
            build_region_terrain_sidecar("invalid_region_xyz", [])

        with self.assertRaises(ValueError):
            derive_height_map(b"truncated", 32, 32)


if __name__ == "__main__":
    unittest.main()
