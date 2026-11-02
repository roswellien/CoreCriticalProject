"""Tests for replacement mech height-map derivation and BWSFM1 generation."""

from pathlib import Path
import struct
import tempfile
import unittest

try:
    import numpy as np
except ImportError:
    np = None

from surface_materials import (
    pack_surface_materials,
    read_surface_materials,
    ROLE_HEIGHT,
    ADDRESS_WRAP,
)
from normal_materials import pack_normals
from mech_height_maps import (
    unpack_bwnrm2,
    unpack_bwtex1,
    extract_mech_geometry,
    MECH_MATERIAL_PROFILES,
    HERO_MECHS,
)
from visualize_terrain_heights import generate_html_inspection_report
from mech_inspector_html import generate_mech_html_report


@unittest.skipIf(np is None, "Mech height-map tests require NumPy")
class MechHeightMapsTests(unittest.TestCase):
    def test_unpack_bwnrm2_roundtrip(self):
        w, h = 16, 16
        n_raw = bytes([128, 128, 255, 255] * (w * h))
        images = {
            "Body": (w, h, n_raw),
            "Weapons": (w, h, n_raw),
        }
        batch_order = ["Body", "Body", "Weapons", "Body"]
        packed_data = pack_normals(batch_order, images)

        batches, unpacked_images = unpack_bwnrm2(packed_data)
        self.assertEqual(len(batches), 4)
        self.assertEqual(len(unpacked_images), 2)
        self.assertIn("Body", unpacked_images)
        self.assertIn("Weapons", unpacked_images)
        self.assertEqual(unpacked_images["Body"][0], w)
        self.assertEqual(unpacked_images["Body"][1], h)
        self.assertEqual(len(unpacked_images["Body"][3]), w * h * 4)

    def test_unpack_bwtex1_parsing(self):
        # Construct valid BWTEX1 header: magic(8), batches_count(4), names_len(4)
        batches = [0, 0, 1]
        names = ["Body", "Window"]
        w, h = 8, 8
        header = bytearray(b"BWTEX1\0\0" + struct.pack("<II", len(batches), len(names)))
        header.extend(struct.pack(f"<{len(batches)}I", *batches))

        # Add image records
        for name in names:
            header.extend(name.encode("ascii").ljust(32, b"\0"))
            header.extend(struct.pack("<IIQ", w, h, 0x12345678))
            header.extend(bytes([255, 255] * (w * h)))  # RGB565 white

        parsed_names, parsed_batches, parsed_images = unpack_bwtex1(bytes(header))
        self.assertEqual(parsed_names, names)
        self.assertEqual(parsed_batches, ["Body", "Body", "Window"])
        self.assertEqual(len(parsed_images), 2)
        self.assertEqual(parsed_images["Body"][0], w)
        self.assertEqual(len(parsed_images["Body"][3]), w * h * 2)

    def test_mech_material_profiles_values(self):
        # Cockpit Window must be flat (zero displacement) and highly reflective
        window_prof = MECH_MATERIAL_PROFILES["window"]
        self.assertEqual(window_prof["height_amplitude"], 0.0)
        self.assertEqual(window_prof["max_displacement"], 0.0)
        self.assertGreaterEqual(window_prof["reflectivity"], 0.8)
        self.assertLessEqual(window_prof["roughness"], 0.1)

        # Weapons must be metallic
        weapons_prof = MECH_MATERIAL_PROFILES["weapons"]
        self.assertGreaterEqual(weapons_prof["metallic"], 0.5)

        # Body armor must have subtle amplitude suitable for mechs
        body_prof = MECH_MATERIAL_PROFILES["body"]
        self.assertGreater(body_prof["height_amplitude"], 0.0)
        self.assertLessEqual(body_prof["height_amplitude"], 0.10)

    def test_synthetic_mech_surface_materials_bwsfm1_pack(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            w, h = 16, 16
            h_raw = bytes([128, 128, 128, 255] * (w * h))
            mat_names = ["Body", "Variant", "Weapons", "Window", "MissileHead"]
            batch_order = ["Body", "Body", "Variant", "Window", "Weapons", "MissileHead"]

            images = {}
            records = []
            for name in mat_names:
                h_name = f"h_{name}"
                images[h_name] = (ROLE_HEIGHT, w, h, h_raw)
                prof = MECH_MATERIAL_PROFILES.get(name.lower(), MECH_MATERIAL_PROFILES["default"])
                records.append({
                    "asset_id": "bushwacker:close",
                    "material_name": name,
                    "height_image": h_name,
                    "height_reference": prof["height_reference"],
                    "height_amplitude": prof["height_amplitude"],
                    "max_displacement": prof["max_displacement"],
                    "address_mode_u": ADDRESS_WRAP,
                    "address_mode_v": ADDRESS_WRAP,
                    "roughness": prof["roughness"],
                    "reflectivity": prof["reflectivity"],
                    "metallic": prof["metallic"],
                })

            mesh_hash = 0xf37bc1a0e8490f2a
            sidecar_bytes = pack_surface_materials(
                asset_id="bushwacker:close",
                mesh_uv_hash=mesh_hash,
                batch_materials=batch_order,
                records=records,
                images=images,
            )

            # Roundtrip verification
            verified = read_surface_materials(
                sidecar_bytes,
                expected_asset_id="bushwacker:close",
                expected_mesh_uv_hash=mesh_hash,
            )
            self.assertEqual(len(verified["records"]), 5)
            self.assertEqual(len(verified["images"]), 5)
            self.assertEqual(len(verified["bindings"]), len(batch_order))

            # HTML report generation check
            html_out = temp_path / "bushwacker_test.html"
            visual_entries = [
                {
                    "name": "Body",
                    "family": "body",
                    "width": w,
                    "height": h,
                    "median_error_deg": 1.2,
                    "correlation": 0.98,
                    "height_amplitude": 0.05,
                    "roughness": 0.55,
                    "reflectivity": 0.08,
                    "metallic": 0.20,
                    "color_data": "data:image/png;base64,dummy",
                    "normal_data": "data:image/png;base64,dummy",
                    "height_data": "data:image/png;base64,dummy",
                    "renorm_data": "data:image/png;base64,dummy",
                    "heatmap_data": "data:image/png;base64,dummy",
                }
            ]
            generate_html_inspection_report("Bushwacker Inspector", visual_entries, html_out)
            self.assertTrue(html_out.exists())
            content = html_out.read_text(encoding="utf-8")
            self.assertIn("Bushwacker Inspector", content)
            self.assertIn("glCanvas", content)

    def test_mech_3d_html_report_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            html_out = temp_path / "mech_3d_test.html"
            visual_entries = [
                {
                    "name": "Body",
                    "family": "body",
                    "width": 64,
                    "height": 64,
                    "median_error_deg": 1.5,
                    "correlation": 0.99,
                    "height_amplitude": 0.05,
                    "roughness": 0.45,
                    "reflectivity": 0.35,
                    "metallic": 0.20,
                    "color_data": "data:image/png;base64,dummy",
                    "normal_data": "data:image/png;base64,dummy",
                    "height_data": "data:image/png;base64,dummy",
                    "renorm_data": "data:image/png;base64,dummy",
                    "heatmap_data": "data:image/png;base64,dummy",
                }
            ]
            dummy_mesh_data = {
                "materials": {"Body": "AAAA"},
                "material_vert_counts": {"Body": 3},
                "center": [0.0, 1.0, 0.0],
                "radius": 4.5,
                "total_vertices": 3,
            }
            generate_mech_html_report("MadCat 3D Inspector", visual_entries, dummy_mesh_data, html_out)
            self.assertTrue(html_out.exists())
            content = html_out.read_text(encoding="utf-8")
            self.assertIn("MadCat 3D Inspector", content)
            self.assertIn("btnMode3D", content)
            self.assertIn("MESH_DATA", content)
            self.assertIn("glCanvas", content)


if __name__ == "__main__":
    unittest.main()
