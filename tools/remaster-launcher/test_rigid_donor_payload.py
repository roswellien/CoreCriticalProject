"""Asset-free checks for the native rigid donor authoring interface."""

import math
import struct
import unittest
from dataclasses import replace

from rigid_donor_payload import Batch, Bone, encode_constant_textures, encode_mesh


def frame(position):
    x, y, z = position
    return (1.0, 0.0, 0.0, x, 0.0, 1.0, 0.0, y, 0.0, 0.0, 1.0, z, 0.0, 0.0, 0.0, 1.0)


def fixture():
    declarations = [
        ("Pelvis", "hip", -1, (0, 0, 4)),
        ("Torso_Twist", "torso", 0, (0, 0, 5)),
        ("Upperarm_Left", "larm", 1, (0, 2, 5)),
        ("Forearm_Left", "lhand", 2, (1, 2, 4)),
        ("Upperarm_Right", "rarm", 1, (0, -2, 5)),
        ("Forearm_Right", "rhand", 4, (1, -2, 4)),
        ("Thigh_Left", "lthigh", 0, (0, 1, 4)),
        ("Calf_Left", "lcalf", 6, (1, 1, 2)),
        ("Foot0_Left", "lfoot", 7, (0, 1, 0.5)),
        ("Thigh_Right", "rthigh", 0, (0, -1, 4)),
        ("Calf_Right", "rcalf", 9, (1, -1, 2)),
        ("Foot0_Right", "rfoot", 10, (0, -1, 0.5)),
    ]
    bones = [
        Bone(name, control, parent, frame(position))
        for name, control, parent, position in declarations
    ]
    references = {bone.control: bone.rest for bone in bones}
    vertices = b"".join(
        struct.pack("<8f", *point, 0, 0, 1, 0.5, 0.5) for point in [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
    )
    return bones, references, [Batch("hip", "hip_polys", 0, vertices)]


def encode(bones=None, references=None, batches=None, **options):
    default_bones, default_references, default_batches = fixture()
    return encode_mesh(
        default_bones if bones is None else bones,
        default_references if references is None else references,
        default_batches if batches is None else batches,
        walk_x=(0.1, -0.1),
        walk_z=(0.5, 0.5),
        **options,
    )


class RigidDonorPayloadChecks(unittest.TestCase):
    def test_wire_offsets_and_original_corner_bytes(self):
        bones, references, batches = fixture()
        data = encode()
        self.assertEqual(data[:8], b"BWMESH4\0")
        self.assertEqual(struct.unpack_from("<4I", data, 8), (1, 12, 12, 1))
        self.assertEqual(struct.unpack_from("<5d", data, 24), (0.0, 0.1, -0.1, 0.5, 0.5))
        self.assertEqual(data[64:96].rstrip(b"\0"), b"Pelvis")
        self.assertEqual(struct.unpack_from("<i", data, 128)[0], -1)
        self.assertEqual(struct.unpack_from("<16d", data, 132), bones[0].rest)
        offset = 64 + len(bones) * 196 + len(references) * 160
        self.assertEqual(data[offset : offset + 32].rstrip(b"\0"), b"hip")
        self.assertEqual(data[offset + 32 : offset + 64].rstrip(b"\0"), b"hip_polys")
        self.assertEqual(struct.unpack_from("<3I", data, offset + 64), (0, 3, 0xFFFFFFFF))
        self.assertEqual(data[offset + 76 :], batches[0].vertices)

    def test_measured_hinge_metadata_is_opt_in(self):
        bones, references, batches = fixture()
        with self.assertRaisesRegex(ValueError, "hinge frames"):
            encode(bones, references, batches, hinge_axes=True)
        for name, parent in [
            ("Calf_Left", 6),
            ("Calf_Right", 9),
            ("Forearm_Left", 2),
            ("Forearm_Right", 4),
            ("Foot0_Left", 7), ("Foot0_Right", 10),
        ]:
            bones.append(Bone("HingeAxis_" + name, "", parent, frame((0, 0, 0))))
        with self.assertRaisesRegex(ValueError, "sole points"):
            encode(bones, references, batches, hinge_axes=True)
        for side, parent in [("Left", 8), ("Right", 11)]:
            for number in range(3):
                bones.append(Bone(f"Sole_{side}_{number}", "", parent, frame((number, 0, 0))))
        data = encode(bones, references, batches, hinge_axes=True)
        self.assertEqual(struct.unpack_from("<I", data, 20)[0], 3)
        self.assertEqual(struct.unpack_from("<I", encode(), 20)[0], 1)
        self.assertTrue(data.endswith(batches[0].vertices))

    def test_fixed_housing_inherits_proximal_control(self):
        bones, references, batches = fixture()
        bones.append(Bone("ElbowHousing", "", 2, frame((1, 2, 4))))
        batch = replace(batches[0], owner="larm", visibility="larm", bone=12)
        self.assertTrue(encode(bones, references, [batch]))
        with self.assertRaisesRegex(ValueError, "owner disagrees"):
            encode(bones, references, [replace(batch, owner="lhand")])

    def test_names_parents_and_unknown_bindings_are_rejected(self):
        bones, references, _ = fixture()
        for altered in [
            replace(bones[1], name="Pelvis"),
            replace(bones[1], name="x" * 32),
            replace(bones[1], name="Torso\0"),
            replace(bones[1], parent=2),
            replace(bones[1], parent=-2),
            replace(bones[1], control="invented"),
        ]:
            with self.subTest(altered=altered), self.assertRaises(ValueError):
                encode([bones[0], altered, *bones[2:]], references)
        with self.assertRaises(ValueError):
            encode(references={name: value for name, value in references.items() if name != "hip"})

    def test_distance_dispatch_preserves_the_toe_bone(self):
        bones, references, batches = fixture()
        bones.append(Bone("ToeFront_Right", "rtoe02", 11, frame((1, -1, 0.5))))
        references["rtoe02"] = bones[-1].rest
        batch = replace(batches[0], owner="rfoot", visibility="rfoot", bone=12)
        self.assertTrue(encode(bones, references, [batch]))

    def test_invalid_matrices_and_gait_are_rejected(self):
        bones, _, _ = fixture()
        for value in [math.nan, math.inf]:
            matrix = list(bones[0].rest)
            matrix[0] = value
            with self.assertRaises(ValueError):
                encode([replace(bones[0], rest=tuple(matrix)), *bones[1:]])
        for index, value in [(0, 0.0), (15, 0.0)]:
            matrix = list(bones[0].rest)
            matrix[index] = value
            with self.assertRaises(ValueError):
                encode([replace(bones[0], rest=tuple(matrix)), *bones[1:]])
        for value in [-1, 11, math.nan]:
            with self.assertRaises(ValueError):
                encode(hip_drop=value)

    def test_incomplete_nonfinite_and_nonunit_corners_are_rejected(self):
        _, _, batches = fixture()
        bad = [
            b"",
            batches[0].vertices[:-1],
            struct.pack("<8f", math.nan, 0, 0, 0, 0, 1, 0, 0) * 3,
            struct.pack("<8f", 0, 0, 0, 0, 0, 0, 0, 0) * 3,
        ]
        for vertices in bad:
            with self.subTest(size=len(vertices)), self.assertRaises(ValueError):
                encode(batches=[replace(batches[0], vertices=vertices)])
        with self.assertRaises(ValueError):
            encode(batches=[replace(batches[0], bone=12)])

    def test_native_batch_and_corner_limits(self):
        _, _, batches = fixture()
        self.assertTrue(encode(batches=batches * 256))
        with self.assertRaisesRegex(ValueError, "Batch count"):
            encode(batches=batches * 257)
        self.assertTrue(encode(batches=[replace(batches[0], vertices=batches[0].vertices * 21845)]))
        with self.assertRaisesRegex(ValueError, "vertex count"):
            encode(batches=[replace(batches[0], vertices=batches[0].vertices * 21846)])
        self.assertTrue(encode_constant_textures([("A", (0, 0, 0))], [0] * 256))
        with self.assertRaisesRegex(ValueError, "counts"):
            encode_constant_textures([("A", (0, 0, 0))], [0] * 257)

    def test_constant_texture_batch_roster_and_rgb565(self):
        data = encode_constant_textures([("Red", (255, 0, 0)), ("Green", (0, 255, 0))], [1, 0, 1])
        self.assertEqual(data[:8], b"BWTEX1\0\0")
        self.assertEqual(struct.unpack_from("<5I", data, 8), (3, 2, 1, 0, 1))
        self.assertEqual(struct.unpack_from("<II", data, 60), (1, 1))
        self.assertEqual(struct.unpack_from("<H", data, 76)[0], 0xF800)
        self.assertEqual(struct.unpack_from("<H", data, 126)[0], 0x07E0)
        for materials, indices in [
            ([], [0]),
            ([("Bad", (256, 0, 0))], [0]),
            ([("A", (0, 0, 0))], [1]),
            ([("A", (0, 0, 0)), ("A", (1, 1, 1))], [0]),
        ]:
            with self.assertRaises(ValueError):
                encode_constant_textures(materials, indices)


if __name__ == "__main__":
    unittest.main()
