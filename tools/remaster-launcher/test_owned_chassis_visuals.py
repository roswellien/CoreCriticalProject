"""Authored binary fixtures for the owned-controller visual boundary."""

import copy
import struct
import unittest

from chassis_catalog import encode_catalog
from normal_materials import pack_surface_bindings, pixel_hash
from owned_chassis_visuals import mesh_metadata, references, validate

CONTROLS = (
    "hip",
    "torso",
    "larm",
    "rarm",
    "lhand",
    "rhand",
    "lthigh",
    "rthigh",
    "lcalf",
    "rcalf",
    "lfoot",
    "rfoot",
)
BONES = (
    "Pelvis",
    "Torso_Twist",
    "Upperarm_Left",
    "Upperarm_Right",
    "Forearm_Left",
    "Forearm_Right",
    "Thigh_Left",
    "Thigh_Right",
    "Calf_Left",
    "Calf_Right",
    "Foot0_Left",
    "Foot0_Right",
)
IDENTITY = struct.pack("<16d", 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)


def name(value):
    return value.encode().ljust(32, b"\0")


def geometry(batches=(("hip", "hip"),)):
    data = bytearray(b"BWMESH4\0" + struct.pack("<4I5d", len(batches), 12, 12, 0, 0, 0, 0, 0, 0))
    for index, (bone, control) in enumerate(zip(BONES, CONTROLS)):
        data += name(bone) + name(control) + struct.pack("<i", -1 if index == 0 else 0) + IDENTITY
    for control in CONTROLS:
        data += name(control) + IDENTITY
    for owner, visible in batches:
        data += name(owner) + name(visible) + struct.pack("<3I", 0, 3, 0xFFFFFFFF)
        data += struct.pack("<8f", 0, 0, 0, 0, 0, 1, 0, 0) * 3
    return bytes(data)


def tree(vertices=3):
    data = bytearray()
    for index, control in enumerate(CONTROLS):
        node = bytearray(352)
        node[:36] = control.encode().ljust(36, b"\0")
        struct.pack_into("<I", node, 36, 0x200)
        struct.pack_into("<I", node, 52, 5)
        struct.pack_into("<I", node, 60, 1)
        struct.pack_into("<I", node, 84, int(index != 0))
        struct.pack_into("<I", node, 92, 11 if index == 0 else 0)
        mesh = bytearray(92)
        struct.pack_into("<5I", mesh, 16, 1, vertices, 0, 0, 0)
        data += (
            node
            + mesh
            + bytes(vertices * 12)
            + struct.pack("<9I", 3, 0, 0, 0, 0, 0, 0, 0, 0)
            + struct.pack("<3I", 0, 1, 2)
            + bytes(36)
        )
    return bytes(data)


class OwnedVisualTests(unittest.TestCase):
    def setUp(self):
        self.mesh = geometry()
        self.texture = (
            b"BWTEX1\0\0"
            + struct.pack("<3I", 1, 1, 0)
            + name("paint")
            + struct.pack("<IIQH", 1, 1, 0, 0x1234)
        )
        self.resources = {"mesh": self.mesh, "texture": self.texture}
        self.value = {
            "schema_version": 1,
            "meshes": {l: "mesh" for l in ("close", "distance")},
            "textures": {l: "texture" for l in ("close", "distance")},
        }
        cockpit = bytearray(352)
        cockpit[:36] = b"cockpit".ljust(36, b"\0")
        struct.pack_into("<I", cockpit, 52, 5)
        self.legacy = {
            "materials": struct.pack("<I", 1) + bytes(40),
            "models": {"close": tree(), "distance": tree(6), "cockpit": bytes(cockpit)},
        }

    def read(self, value=None):
        return validate(value or self.value, self.legacy, lambda path, fmt: self.resources[path])

    def test_selection_validates_inactive_fields_but_gates_only_selected_normals(self):
        import json

        from build_chassis_pack import build
        from prepared_chassis_packs import select
        from test_prepared_chassis_packs import ChassisPackTests

        fixture = ChassisPackTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        project, descriptor, _ = fixture.legacy_project()
        root = fixture.root
        (root / "node.bin").write_bytes(tree())
        (root / "distance.bin").write_bytes(tree(6))
        descriptor["models"]["distance"] = "distance.bin"
        (root / "cockpit.bin").write_bytes(self.legacy["models"]["cockpit"])
        descriptor["models"]["cockpit"] = "cockpit.bin"
        (root / "legacy.json").write_text(json.dumps(descriptor))
        (root / "mesh").write_bytes(self.mesh)
        (root / "texture").write_bytes(self.texture)
        color = struct.pack("<IHH8xH", 5, 1, 1, 0x1234)
        (root / "color").write_bytes(color)
        page = pack_surface_bindings(
            [((1, 1, 1, pixel_hash(color[16:])), (1, 1, bytes([128, 128, 255, 255])))]
        )
        (root / "normal").write_bytes(page)
        document = json.loads(project.read_text())
        document["chassis"][0]["appearances"] = {
            "new": self.value,
            "upgraded": {"textures": {"example_skin": "color"}, "normals": ["normal"]},
        }
        project.write_text(json.dumps(document))
        build(project, root / "owned-built")
        pack = root / "owned-built/pack"
        manifest = json.loads((pack / "pack.json").read_text())
        host = {
            "content_capabilities": {
                "additional-mech-chassis": [1, 2, 3],
                "mech-appearances": [1],
                "owned-chassis-visuals": [1],
            }
        }
        rows = select([(pack, manifest)], host, appearance_mode="new")
        self.assertEqual(rows[0]["appearance"]["selected"], "new")
        self.assertEqual(rows[0]["appearance_normal_pages"], [])
        with self.assertRaisesRegex(ValueError, "normal map"):
            select([(pack, manifest)], host, appearance_mode="upgraded")
        # Exercise the selected owned normal path independently of the upgraded one.
        owned_normal = pack_surface_bindings(
            [((1, 1, 1, pixel_hash(self.texture[-2:])), (1, 1, bytes([128, 128, 255, 255])))]
        )
        (root / "owned-normal").write_bytes(owned_normal)
        document["chassis"][0]["appearances"]["new"]["normals"] = ["owned-normal"]
        project.write_text(json.dumps(document))
        build(project, root / "owned-normals-built")
        normal_pack = root / "owned-normals-built/pack"
        normal_manifest = json.loads((normal_pack / "pack.json").read_text())
        host["normal_map_formats"] = [2]
        with self.assertRaisesRegex(ValueError, "authored normal catalog"):
            select([(normal_pack, normal_manifest)], host, appearance_mode="new")
        host["authored_normal_catalog_versions"] = [1]
        selected = select([(normal_pack, normal_manifest)], host, appearance_mode="new")
        self.assertEqual(selected[0]["appearance_normal_pages"], [owned_normal])
        for fmt in ("BWMESH4", "BWTEX1", "BWSNR2"):
            invalid = copy.deepcopy(manifest)
            invalid["native_payload"]["required_formats"].remove(fmt)
            with self.subTest(fmt=fmt), self.assertRaises(ValueError):
                select([(pack, invalid)], host, appearance_mode="original")

    def test_rosters_are_derived_and_resources_are_immutable(self):
        before = copy.deepcopy((self.value, self.legacy, self.resources))
        result = self.read()
        self.assertEqual(len(result["rosters"]["close"]), 12)
        self.assertEqual({r["owner"] for r in result["rosters"]["distance"]}, {"hip"})
        self.assertEqual(result["cockpit"], [])
        self.assertEqual(before, (self.value, self.legacy, self.resources))
        self.legacy["models"]["distance"] = self.legacy["models"]["close"]
        with self.assertRaisesRegex(ValueError, "LOD signatures"):
            self.read()

    def test_visibility_and_tree_ancestry_fail_closed(self):
        for batches in (
            (("hip", "hip"), ("torso", "larm")),
            (("foreign", "hip"),),
            (("hip", "foreign"),),
        ):
            with self.subTest(batches=batches):
                self.resources["mesh"] = geometry(batches)
                self.resources["texture"] = (
                    b"BWTEX1\0\0"
                    + struct.pack("<II", len(batches), 1)
                    + struct.pack("<I", 0) * len(batches)
                    + self.texture[20:]
                )
                with self.assertRaises(ValueError):
                    self.read()
        self.resources["mesh"] = self.mesh
        self.resources["texture"] = self.texture
        bad = bytearray(tree())
        struct.pack_into("<I", bad, 92, 10)
        self.legacy["models"]["close"] = bytes(bad)
        with self.assertRaisesRegex(ValueError, "tree"):
            self.read()

    def test_truncation_limits_unknown_fields_and_lods(self):
        for size in (0, 7, 12, 63, len(self.mesh) - 1):
            with self.subTest(size=size), self.assertRaises(ValueError):
                mesh_metadata(self.mesh[:size])
        for value in (
            dict(self.value, gameplay={}),
            dict(self.value, schema_version=True),
            dict(self.value, meshes={"close": "mesh"}),
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                list(references(value))
        bad = bytearray(self.mesh)
        struct.pack_into("<I", bad, 8, 257)
        with self.assertRaises(ValueError):
            mesh_metadata(bytes(bad))
        self.resources["texture"] = self.texture + b"x"
        with self.assertRaisesRegex(ValueError, "Trailing"):
            self.read()

    def test_catalog_preserves_headlights_and_rejects_foreign_roster_fields(self):
        lamp = {
            "id": "left",
            "space": "guest_node",
            "attachment": "torso",
            "position": [-0.96, 2.06, -2.2],
            "direction": [0, 0, -1],
            "color": [1, 0.95, 0.85],
            "intensity": 3,
            "range": 92,
            "inner_angle": 15,
            "outer_angle": 25.5,
        }
        record = {
            "id": "community.test:mech",
            "name": "Test",
            "resource": "example",
            "metadata_template": "annihilator",
            "headlights": [lamp],
        }
        old = encode_catalog([record])
        row = {"name": "hip", "owner": "hip", "vertices": 3}
        visual = {
            "meshes": {l: "mesh.bin" for l in ("close", "distance")},
            "textures": {l: "texture.bin" for l in ("close", "distance")},
            "rosters": {l: [row] for l in ("close", "distance")},
            "cockpit": [],
            "skin_textures": {"example_t0": 0},
        }
        new = encode_catalog([dict(record, owned_visuals=visual)])
        self.assertEqual(new[:8], b"MWCHAS6\0")
        self.assertEqual(new[8 : len(old)], old[8:])
        for changed in (
            dict(row, vertices=0),
            dict(row, owner="../foreign"),
            dict(row, vertices=True),
        ):
            broken = copy.deepcopy(visual)
            broken["rosters"]["close"] = [changed]
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                encode_catalog([dict(record, owned_visuals=broken)])

    def test_normals_require_full_selected_color_and_unique_keys(self):
        key = (1, 1, 1, pixel_hash(self.texture[-2:]))
        normal = (1, 1, bytes((128, 128, 255, 255)))
        self.resources["normal"] = pack_surface_bindings([(key, normal)])
        self.value["normals"] = ["normal"]
        self.assertEqual(len(self.read()["normal_pages"]), 1)
        self.resources["other"] = self.resources["normal"]
        self.value["normals"] = ["normal", "other"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            self.read()
        self.value["normals"] = ["normal"]
        self.resources["normal"] = pack_surface_bindings([((1, 1, 1, key[3] ^ 1), normal)])
        with self.assertRaisesRegex(ValueError, "Foreign"):
            self.read()


if __name__ == "__main__":
    unittest.main()
