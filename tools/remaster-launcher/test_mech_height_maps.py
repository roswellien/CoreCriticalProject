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
    get_mech_material_profile,
    MECH_MATERIAL_PROFILES,
    ALL_MECHS,
    HERO_MECHS,
    REPLACEMENT_MECHS,
    DETAILED_MW3_MECHS,
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

    def test_roster_chassis_counts(self):
        self.assertEqual(len(ALL_MECHS), 18)
        self.assertEqual(len(REPLACEMENT_MECHS), 14)
        self.assertEqual(len(DETAILED_MW3_MECHS), 4)
        self.assertEqual(HERO_MECHS, ("bushwacker", "madcat"))
        for mech in HERO_MECHS:
            self.assertIn(mech, ALL_MECHS)
            self.assertIn(mech, REPLACEMENT_MECHS)

    def test_material_profile_resolution(self):
        # Canopy glass (MW5 and detailed MW3)
        for name in ("window", "Window", "glazing0", "glazing1", "optical0", "optical1"):
            prof = get_mech_material_profile(name)
            self.assertEqual(prof["height_amplitude"], 0.0)
            self.assertGreaterEqual(prof["reflectivity"], 0.8)
            self.assertLessEqual(prof["roughness"], 0.1)

        # Weapons / mechanical
        for name in ("weapons", "Weapons", "weap_hole", "constant0", "constant1"):
            prof = get_mech_material_profile(name)
            self.assertGreaterEqual(prof["metallic"], 0.5)

        # Armor plates across chassis
        for name in ("Body", "Variant", "strider01", "avatar16", "owens08", "firefly02"):
            prof = get_mech_material_profile(name)
            self.assertGreater(prof["height_amplitude"], 0.0)
            self.assertLessEqual(prof["metallic"], 0.3)

    def test_extract_mech_geometry_across_bwmesh_formats(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            tex_path = temp_path / "test.bwtex1"
            # Write minimal valid BWTEX1 with 1 batch and 1 material
            tex_data = bytearray(b"BWTEX1\0\0" + struct.pack("<II", 1, 1))
            tex_data.extend(struct.pack("<I", 0))  # batch binding 0
            tex_data.extend(b"Body".ljust(32, b"\0"))
            tex_data.extend(struct.pack("<IIQ", 4, 4, 0))
            tex_data.extend(bytes(4 * 4 * 2))
            tex_path.write_bytes(tex_data)

            # 3 vertices (32 bytes each: float3 xyz + float3 n + float2 uv)
            v3 = bytearray()
            for _ in range(3):
                v3.extend(struct.pack("<ffffff", 0.0, 1.0, 2.0, 0.0, 1.0, 0.0))
                v3.extend(struct.pack("<ff", 0.0, 0.0))

            # Test BWMESH2 (visibility)
            m2 = bytearray(b"BWMESH2\0" + struct.pack("<I", 1))
            m2.extend(b"owner".ljust(32, b"\0"))
            m2.extend(b"visib".ljust(32, b"\0"))
            m2.extend(struct.pack("<II", 3, 0))
            m2.extend(v3)
            p2 = temp_path / "m2.bin"
            p2.write_bytes(m2)
            geo2 = extract_mech_geometry(p2, tex_path)
            self.assertEqual(geo2["total_vertices"], 3)
            self.assertIn("Body", geo2["materials"])

            # Test BWMESH3 (visibility + placement)
            m3 = bytearray(b"BWMESH3\0" + struct.pack("<I", 1))
            m3.extend(b"owner".ljust(32, b"\0"))
            m3.extend(b"visib".ljust(32, b"\0"))
            m3.extend(bytes(44))  # placement
            m3.extend(struct.pack("<II", 3, 0))
            m3.extend(v3)
            p3 = temp_path / "m3.bin"
            p3.write_bytes(m3)
            geo3 = extract_mech_geometry(p3, tex_path)
            self.assertEqual(geo3["total_vertices"], 3)

            # Test BWMESH4 (donor rig header)
            m4 = bytearray(b"BWMESH4\0" + struct.pack("<I", 1))
            m4.extend(struct.pack("<III", 1, 1, 0))  # 1 bone, 1 ref, 0 flags
            m4.extend(bytes(40))  # gait
            m4.extend(bytes(32 + 32 + 4 + 128))  # 1 bone
            m4.extend(bytes(32 + 128))  # 1 ref
            m4.extend(b"owner".ljust(32, b"\0"))
            m4.extend(b"visib".ljust(32, b"\0"))
            m4.extend(struct.pack("<I", 0))  # donor_bone
            m4.extend(struct.pack("<II", 3, 0))
            m4.extend(v3)
            p4 = temp_path / "m4.bin"
            p4.write_bytes(m4)
            geo4 = extract_mech_geometry(p4, tex_path)
            self.assertEqual(geo4["total_vertices"], 3)

            # Test BWMESH6 (visibility + placement + layered + anchored)
            m6 = bytearray(b"BWMESH6\0" + struct.pack("<I", 1))
            m6.extend(b"owner".ljust(32, b"\0"))
            m6.extend(b"visib".ljust(32, b"\0"))
            m6.extend(bytes(44))  # placement
            m6.extend(bytes(44))  # layered
            m6.extend(bytes(44))  # anchored
            m6.extend(struct.pack("<II", 3, 0))
            m6.extend(v3)
            p6 = temp_path / "m6.bin"
            p6.write_bytes(m6)
            geo6 = extract_mech_geometry(p6, tex_path)
            self.assertEqual(geo6["total_vertices"], 3)


if __name__ == "__main__":
    unittest.main()
