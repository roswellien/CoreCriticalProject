import struct
from unittest.mock import call, mock_open, patch
import unittest

import surface_materials


def _make_bwmesh1() -> bytes:
    out = bytearray(b"BWMESH1\0" + struct.pack("<I", 2))
    for owner, u_step in ((b"torso", 0.25), (b"canopy", 0.75)):
        out.extend(owner.ljust(32, b"\0"))
        out.extend(struct.pack("<II", 3, 0xFFFFFFFF))
        for idx in range(3):
            out.extend(
                struct.pack(
                    "<8f",
                    float(idx),
                    float(idx + 1),
                    float(idx + 2),
                    0.0,
                    0.0,
                    1.0,
                    u_step * idx,
                    0.5 * idx,
                )
            )
    return bytes(out)


def _make_bwmesh4() -> bytes:
    out = bytearray(b"BWMESH4\0" + struct.pack("<IIII", 2, 1, 1, 0))
    out.extend(struct.pack("<5d", 1.0, 2.0, 3.0, 0.25, 0.5))
    # 1 bone: name (32) + parent (32) + parent_index (4) + 2x mat4 (128)
    out.extend(b"root".ljust(32, b"\0") + b"".ljust(32, b"\0") + struct.pack("<i", -1))
    out.extend(struct.pack("<16f", 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1) * 2)
    # 1 ref: name (32) + 2x mat4 (128)
    out.extend(b"torso".ljust(32, b"\0"))
    out.extend(struct.pack("<16f", 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1) * 2)
    for owner, u_step in ((b"torso", 0.25), (b"canopy", 0.75)):
        out.extend(owner.ljust(32, b"\0"))
        out.extend(owner.ljust(32, b"\0"))
        out.extend(struct.pack("<III", 0, 3, 0xFFFFFFFF))
        for idx in range(3):
            out.extend(
                struct.pack(
                    "<8f",
                    float(idx),
                    float(idx + 1),
                    float(idx + 2),
                    0.0,
                    0.0,
                    1.0,
                    u_step * idx,
                    0.5 * idx,
                )
            )
    return bytes(out)


def _make_bwtex1(materials: tuple[str, ...] = ("armor_hull", "canopy_glass")) -> bytes:
    out = bytearray(b"BWTEX1\0\0" + struct.pack("<II", len(materials), len(materials)))
    out.extend(struct.pack("<" + "I" * len(materials), *range(len(materials))))
    for mat in materials:
        out.extend(mat.encode("ascii").ljust(32, b"\0"))
        out.extend(struct.pack("<IIQ", 1, 1, 0))
        out.extend(b"\x00\x7c")
    return bytes(out)


class SurfaceMaterialsTest(unittest.TestCase):
    def _height_pixels(self) -> bytes:
        return bytes((32, 0, 0, 255, 96, 0, 0, 255, 160, 0, 0, 255, 224, 0, 0, 255))

    def _thickness_pixels(self) -> bytes:
        return bytes((64, 0, 0, 255, 128, 0, 0, 255, 192, 0, 0, 255, 240, 0, 0, 255))

    def test_environment_and_extractors(self) -> None:
        self.assertEqual(
            surface_materials.surface_material_environment("MW34_BUSHWACKER_TEXTURES"),
            "MW34_BUSHWACKER_SURFACE_MATERIALS",
        )
        self.assertEqual(
            surface_materials.surface_material_environment("MW34_BUSHWACKER_LOD1_TEXTURES"),
            "MW34_BUSHWACKER_LOD1_SURFACE_MATERIALS",
        )
        with self.assertRaises(ValueError):
            surface_materials.surface_material_environment("MW34_BUSHWACKER_MESH")

        mesh1 = _make_bwmesh1()
        mesh4 = _make_bwmesh4()
        expected_hash = surface_materials.mesh_uv_identity(mesh1)
        self.assertEqual(expected_hash, 1335280070564434920)
        self.assertEqual(surface_materials.mesh_uv_identity(mesh4), expected_hash)

        # Changing a single UV coordinate must invalidate the mesh/UV identity hash.
        altered = bytearray(mesh1)
        altered[-4:] = struct.pack("<f", 0.875)
        self.assertNotEqual(surface_materials.mesh_uv_identity(bytes(altered)), expected_hash)

        self.assertEqual(
            surface_materials.texture_batch_materials(_make_bwtex1()),
            ["armor_hull", "canopy_glass"],
        )

    def test_file_extractors_stream_payloads(self) -> None:
        for extractor, payload in (
            (surface_materials.mesh_uv_identity_file, _make_bwmesh1()),
            (surface_materials.texture_batch_materials_file, _make_bwtex1()),
        ):
            with self.subTest(extractor=extractor.__name__):
                stream = mock_open(read_data=payload).return_value
                with patch.object(surface_materials.Path, "open", return_value=stream):
                    extractor("payload.bin")
                self.assertNotIn(call(), stream.read.call_args_list)
                self.assertNotIn(call(-1), stream.read.call_args_list)

    def test_file_reader_limits_read_and_probes_for_overflow(self) -> None:
        stream = mock_open(read_data=b"x" * 32).return_value
        with patch.object(surface_materials.Path, "open", return_value=stream):
            with self.assertRaisesRegex(ValueError, "exceeds size budget"):
                surface_materials.read_surface_materials_file("sidecar.bin", max_bytes=16)
        stream.read.assert_called_once_with(17)

    def test_writer_accepts_more_than_legacy_image_limit(self) -> None:
        materials = [f"material_{index:02d}" for index in range(33)]
        images = {
            f"height_{index:02d}": (surface_materials.ROLE_HEIGHT, 1, 1, b"\0\0\0\xff")
            for index in range(33)
        }
        images.update(
            {
                f"thickness_{index:02d}": (
                    surface_materials.ROLE_THICKNESS,
                    1,
                    1,
                    b"\0\0\0\xff",
                )
                for index in range(32)
            }
        )
        records = []
        for index, material in enumerate(materials):
            record = {
                "asset_id": "community.test:mech:close",
                "material_name": material,
                "height_image": f"height_{index:02d}",
            }
            if index < 32:
                record.update(
                    thickness_image=f"thickness_{index:02d}",
                    sss_participation=1.0,
                )
            records.append(record)
        packed = surface_materials.pack_surface_materials(
            asset_id="community.test:mech:close",
            mesh_uv_hash=1,
            batch_materials=materials,
            records=records,
            images=images,
        )
        self.assertEqual(struct.unpack_from("<I", packed, 20)[0], 65)
        self.assertEqual(len(surface_materials.read_surface_materials(packed)["images"]), 65)

    def test_independent_byte_level_wire_oracle_and_round_trip(self) -> None:
        mesh_hash = 1335280070564434920
        h_pixels = self._height_pixels()
        t_pixels = self._thickness_pixels()
        # Pass records and images in reverse order to verify deterministic sorting.
        packed = surface_materials.pack_surface_materials(
            asset_id="bushwacker:close",
            mesh_uv_hash=mesh_hash,
            batch_materials=["canopy_glass", "armor_hull"],
            records=[
                {
                    "asset_id": "bushwacker:close",
                    "material_name": "canopy_glass",
                    "thickness_image": "thick_canopy",
                    "sss_participation": 0.5,
                    "sss_tint": (0.25, 0.5, 0.75),
                    "sss_radius": 0.125,
                    "thickness_scale": 0.375,
                },
                {
                    "asset_id": "bushwacker:close",
                    "material_name": "armor_hull",
                    "height_image": "height_armor",
                    "height_reference": 0.5,
                    "height_amplitude": 0.25,
                    "max_displacement": 0.5,
                    "tessellation_cap": 4,
                    "uv_scale": (2.0, -2.0),
                    "uv_offset": (0.125, -0.25),
                    "address_mode_u": surface_materials.ADDRESS_MIRROR,
                    "address_mode_v": surface_materials.ADDRESS_CLAMP,
                    "atlas_rect": (0.125, 0.25, 0.875, 0.75),
                },
            ],
            images={
                "thick_canopy": (surface_materials.ROLE_THICKNESS, 2, 2, t_pixels),
                "height_armor": (surface_materials.ROLE_HEIGHT, 2, 2, h_pixels),
            },
        )

        # Independent manual construction of expected BWSFM1 bytes.
        oracle = bytearray()
        oracle.extend(b"BWSFM1\0\0")
        oracle.extend(struct.pack("<IIIIQ", 1, 2, 2, 2, mesh_hash))
        # Batch 0 is canopy_glass (sorted record 1); Batch 1 is armor_hull (sorted record 0).
        oracle.extend(struct.pack("<II", 1, 0))
        # Record 0: ("bushwacker:close", "armor_hull")
        oracle.extend(struct.pack("<I", 16) + b"bushwacker:close")
        oracle.extend(struct.pack("<I", 10) + b"armor_hull")
        oracle.extend(
            struct.pack(
                "<IIfffIffffIIffffffffff",
                0,  # height_armor is sorted image 0
                0xFFFFFFFF,
                0.5,
                0.25,
                0.5,
                4,
                2.0,
                -2.0,
                0.125,
                -0.25,
                2,
                3,
                0.125,
                0.25,
                0.875,
                0.75,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            )
        )
        # Record 1: ("bushwacker:close", "canopy_glass")
        oracle.extend(struct.pack("<I", 16) + b"bushwacker:close")
        oracle.extend(struct.pack("<I", 12) + b"canopy_glass")
        oracle.extend(
            struct.pack(
                "<IIfffIffffIIffffffffff",
                0xFFFFFFFF,
                1,  # thick_canopy is sorted image 1
                0.0,
                0.0,
                0.0,
                1,
                1.0,
                1.0,
                0.0,
                0.0,
                1,
                1,
                0.0,
                0.0,
                1.0,
                1.0,
                0.5,
                0.25,
                0.5,
                0.75,
                0.125,
                0.375,
            )
        )
        # Image 0: height_armor
        oracle.extend(struct.pack("<I", 12) + b"height_armor")
        oracle.extend(
            struct.pack(
                "<IIIQ",
                1,
                2,
                2,
                surface_materials.uncached_pixel_hash(h_pixels),
            )
        )
        oracle.extend(h_pixels)
        # Image 1: thick_canopy
        oracle.extend(struct.pack("<I", 12) + b"thick_canopy")
        oracle.extend(
            struct.pack(
                "<IIIQ",
                2,
                2,
                2,
                surface_materials.uncached_pixel_hash(t_pixels),
            )
        )
        oracle.extend(t_pixels)

        self.assertEqual(packed, bytes(oracle))

        parsed = surface_materials.read_surface_materials(
            packed,
            expected_asset_id="bushwacker:close",
            expected_mesh_uv_hash=mesh_hash,
            expected_batch_materials=["canopy_glass", "armor_hull"],
        )
        self.assertEqual(parsed["version"], 1)
        self.assertEqual(parsed["mesh_uv_hash"], mesh_hash)
        self.assertEqual(parsed["bindings"], [1, 0])
        self.assertEqual(len(parsed["records"]), 2)
        self.assertEqual(parsed["records"][0]["material_name"], "armor_hull")
        self.assertEqual(parsed["records"][0]["tessellation_cap"], 4)
        self.assertEqual(parsed["records"][1]["material_name"], "canopy_glass")
        self.assertAlmostEqual(parsed["records"][1]["sss_participation"], 0.5)
        self.assertEqual(len(parsed["images"]), 2)

        # Truncation at every byte offset must fail cleanly.
        for cutoff in range(len(packed)):
            with self.assertRaises(ValueError):
                surface_materials.read_surface_materials(packed[:cutoff])
        with self.assertRaises(ValueError):
            surface_materials.read_surface_materials(packed + b"\0")

    def test_neutral_absent_and_partial_bindings(self) -> None:
        packed = surface_materials.pack_surface_materials(
            asset_id="orion:close",
            mesh_uv_hash=42,
            batch_materials=["armor_hull", "unauthored_trim"],
            records=[{"asset_id": "orion:close", "material_name": "armor_hull"}],
        )
        parsed = surface_materials.read_surface_materials(
            packed,
            expected_asset_id="orion:close",
            expected_mesh_uv_hash=42,
            expected_batch_materials=["armor_hull", "unauthored_trim"],
        )
        self.assertEqual(parsed["bindings"], [0, surface_materials.NO_SURFACE_MATERIAL])
        rec = parsed["records"][0]
        self.assertEqual(rec["height_image"], surface_materials.NO_SURFACE_IMAGE)
        self.assertEqual(rec["thickness_image"], surface_materials.NO_SURFACE_IMAGE)
        self.assertEqual(rec["height_amplitude"], 0.0)
        self.assertEqual(rec["max_displacement"], 0.0)
        self.assertEqual(rec["tessellation_cap"], 1)
        self.assertEqual(rec["uv_scale"], (1.0, 1.0))
        self.assertEqual(rec["uv_offset"], (0.0, 0.0))
        self.assertEqual(rec["atlas_rect"], (0.0, 0.0, 1.0, 1.0))
        self.assertEqual(rec["sss_participation"], 0.0)

    def test_rejects_invalid_identifiers_ranges_compatibility_and_corruption(self) -> None:
        h_pixels = self._height_pixels()
        images = {"h": (surface_materials.ROLE_HEIGHT, 2, 2, h_pixels)}
        base_record = {
            "asset_id": "bushwacker:close",
            "material_name": "armor_hull",
            "height_image": "h",
            "height_reference": 0.5,
            "height_amplitude": 0.25,
            "max_displacement": 0.25,
            "tessellation_cap": 2,
        }

        bad_records = [
            {**base_record, "asset_id": "../escape"},
            {**base_record, "asset_id": "bad/slash"},
            {**base_record, "asset_id": "bad\0nul"},
            {**base_record, "material_name": "bad:colon"},
            {**base_record, "material_name": "hull..panel"},
            {**base_record, "material_name": "x" * 32},
            {**base_record, "height_reference": -0.1},
            {**base_record, "height_reference": 1.1},
            {**base_record, "height_reference": float("nan")},
            {**base_record, "height_amplitude": 20.0, "max_displacement": 20.0},
            {**base_record, "height_amplitude": 0.5, "max_displacement": 0.25},
            {**base_record, "height_image": None, "height_amplitude": 0.1},
            {**base_record, "height_image": None, "height_amplitude": 0.0, "max_displacement": 0.0, "tessellation_cap": 2},
            {**base_record, "tessellation_cap": 0},
            {**base_record, "tessellation_cap": 9},
            {**base_record, "uv_scale": (0.0, 1.0)},
            {**base_record, "uv_scale": (2000.0, 1.0)},
            {**base_record, "address_mode_u": 0},
            {**base_record, "address_mode_v": 4},
            {**base_record, "atlas_rect": (0.5, 0.0, 0.5, 1.0)},
            {**base_record, "atlas_rect": (-0.1, 0.0, 1.0, 1.0)},
            {**base_record, "sss_participation": 0.0, "sss_radius": 0.2},
            {**base_record, "sss_participation": 0.0, "thickness_scale": 0.2},
            {**base_record, "unknown_key": 1},
        ]
        for bad in bad_records:
            with self.assertRaises(ValueError):
                surface_materials.pack_surface_materials(
                    asset_id=bad["asset_id"] if isinstance(bad.get("asset_id"), str) else "bushwacker:close",
                    mesh_uv_hash=1,
                    batch_materials=["armor_hull"],
                    records=[bad],
                    images=images,
                )

        # Duplicate record rejected.
        with self.assertRaises(ValueError):
            surface_materials.pack_surface_materials(
                asset_id="bushwacker:close",
                mesh_uv_hash=1,
                batch_materials=["armor_hull"],
                records=[base_record, dict(base_record)],
                images=images,
            )

        packed = surface_materials.pack_surface_materials(
            asset_id="bushwacker:close",
            mesh_uv_hash=99,
            batch_materials=["armor_hull"],
            records=[base_record],
            images=images,
        )
        # Compatibility mismatches rejected.
        with self.assertRaises(ValueError):
            surface_materials.read_surface_materials(packed, expected_asset_id="shadowcat:close")
        with self.assertRaises(ValueError):
            surface_materials.read_surface_materials(packed, expected_mesh_uv_hash=100)
        with self.assertRaises(ValueError):
            surface_materials.read_surface_materials(packed, expected_batch_materials=["other_mat"])
        with self.assertRaises(ValueError):
            surface_materials.read_surface_materials(packed, max_bytes=len(packed) - 1)

        # Corrupted pixel byte rejected by hash check.
        corrupted = bytearray(packed)
        corrupted[-1] ^= 0xFF
        with self.assertRaises(ValueError):
            surface_materials.read_surface_materials(bytes(corrupted))


if __name__ == "__main__":
    unittest.main()
