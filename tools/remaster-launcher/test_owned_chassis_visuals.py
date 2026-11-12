"""Authored binary fixtures for the owned-controller visual boundary."""

import copy
import struct
import unittest

from chassis_catalog import encode_catalog
from prepared_chassis_packs import select
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


def geometry(batches=(("hip", "hip"),), policy=0):
    data = bytearray(b"BWMESH4\0" + struct.pack("<4I5d", len(batches), 12, 12, policy, 0, 0, 0, 0, 0))
    parents = (-1, 0, 1, 1, 2, 3, 0, 0, 6, 7, 8, 9) if policy == 3 else (-1,) + (0,) * 11
    for index, (bone, control) in enumerate(zip(BONES, CONTROLS)):
        data += name(bone) + name(control) + struct.pack("<i", parents[index]) + IDENTITY
    for control in CONTROLS:
        data += name(control) + IDENTITY
    for owner, visible in batches:
        data += name(owner) + name(visible) + struct.pack("<3I", 0, 3, 0xFFFFFFFF)
        data += struct.pack("<8f", 0, 0, 0, 0, 0, 1, 0, 0) * 3
    return bytes(data)


def tree(vertices=3, extra=()):
    data = bytearray()
    controls = CONTROLS + tuple(extra)
    for index, control in enumerate(controls):
        count = vertices.get(control, 3) if isinstance(vertices, dict) else vertices
        node = bytearray(352)
        node[:36] = control.encode().ljust(36, b"\0")
        struct.pack_into("<I", node, 36, 0x200)
        struct.pack_into("<I", node, 52, 5)
        struct.pack_into("<I", node, 60, 1)
        struct.pack_into("<I", node, 84, int(index != 0))
        struct.pack_into("<I", node, 92, len(controls) - 1 if index == 0 else 0)
        mesh = bytearray(92)
        struct.pack_into("<5I", mesh, 16, 1, count, 0, 0, 0)
        data += (
            node
            + mesh
            + bytes(count * 12)
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
        from test_prepared_chassis_packs import ChassisPackTests

        fixture = ChassisPackTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        project, descriptor, legacy_definition = fixture.legacy_project()
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

        # A full-original-joint mesh is a selected-only version 2 feature.
        source_mesh = bytearray(self.mesh)
        struct.pack_into("<I", source_mesh, 20, 2)
        (root / "mesh").write_bytes(source_mesh)
        build(project, root / "source-joints-built")
        source_pack = root / "source-joints-built/pack"
        source_manifest = json.loads((source_pack / "pack.json").read_text())
        select([(source_pack, source_manifest)], host, appearance_mode="original")
        with self.assertRaisesRegex(ValueError, "owned-chassis-visuals version 2"):
            select([(source_pack, source_manifest)], host, appearance_mode="new")
        host["content_capabilities"]["owned-chassis-visuals"] = [1, 2]
        selected = select([(source_pack, source_manifest)], host, appearance_mode="new")
        self.assertEqual(selected[0]["owned_visuals"]["capability_version"], 2)

        # The same pack remains usable as Original without native emission.
        from owned_emission import pack as pack_emission, mesh_bindings
        from surface_materials import mesh_uv_identity
        emission = pack_emission(mesh_uv_identity(bytes(source_mesh)),
                                 mesh_bindings(bytes(source_mesh), self.texture),
                                 [dict(id="glass", batch=0, strength=.35,
                                       regions=[(0, 0, 1, 1)], anchors=[])])
        (root / "emission").write_bytes(emission)
        document["chassis"][0]["appearances"]["new"]["emission"] = {
            "close": "emission", "distance": "emission"}
        project.write_text(json.dumps(document))
        build(project, root / "emission-built")
        emission_pack = root / "emission-built/pack"
        emission_manifest = json.loads((emission_pack / "pack.json").read_text())
        select([(emission_pack, emission_manifest)], host, appearance_mode="original")
        with self.assertRaisesRegex(ValueError, "owned-chassis-emission version 1"):
            select([(emission_pack, emission_manifest)], host, appearance_mode="new")
        host["content_capabilities"]["owned-chassis-emission"] = [1]
        selected = select([(emission_pack, emission_manifest)], host, appearance_mode="new")
        self.assertEqual(selected[0]["owned_visuals"]["emission_payloads"]["close"], emission)
        from pathlib import Path
        from prepared_chassis_packs import prepare
        prepared = prepare(selected, (fixture_game := fixture.legacy_game(legacy_definition)[0]), root / "emission-prepared", {})
        prefix = "MW34_CHASSIS_" + selected[0]["registration"]["resource"].upper()
        self.assertEqual(Path(prepared[prefix + "_EMISSION"]).read_bytes(), emission)
        self.assertEqual(Path(prepared[prefix + "_LOD1_EMISSION"]).read_bytes(), emission)
        invalid = copy.deepcopy(emission_manifest)
        invalid["native_payload"]["required_formats"].remove("BWMEM1")
        with self.assertRaisesRegex(ValueError, "Undeclared owned emission"):
            select([(emission_pack, invalid)], host, appearance_mode="original")

        mesh3 = geometry(policy=3)
        (root / "mesh").write_bytes(mesh3)
        # Reuse the same authenticated albedo/UV layouts; emission must still bind.
        data3 = pack_emission(mesh_uv_identity(mesh3), mesh_bindings(mesh3, self.texture),
                              [dict(id="glass", batch=0, strength=.35, regions=[(0,0,1,1)], anchors=[])])
        (root / "emission").write_bytes(data3)
        build(project, root / "arm-policy-built")
        pack3 = root / "arm-policy-built/pack"
        manifest3 = json.loads((pack3 / "pack.json").read_text())
        select([(pack3, manifest3)], host, appearance_mode="original")
        with self.assertRaisesRegex(ValueError, "owned-chassis-visuals version 3"):
            select([(pack3, manifest3)], host, appearance_mode="new")
        host["content_capabilities"]["owned-chassis-visuals"].append(3)
        self.assertEqual(select([(pack3, manifest3)], host, appearance_mode="new")[0]
                         ["owned_visuals"]["capability_version"], 3)

        # Attachment support is required only when this New appearance is selected.
        weapon_mesh = bytearray(mesh3)
        struct.pack_into("<I", weapon_mesh, 64 + 12 * 196 + 12 * 160 + 64, 4)
        (root / "mesh").write_bytes(weapon_mesh)
        document["chassis"][0]["appearances"]["new"].pop("emission")
        table = {"schema_version": 1}
        for lod in ("close", "distance"):
            table[lod] = dict(mesh_identity=f"{mesh_uv_identity(bytes(weapon_mesh)):016x}",
                             records=[dict(source_control="lhand", weapon="ERLargeLaser",
                                           bone="Forearm_Left", position=[0, 0, 0])])
        document["chassis"][0]["appearances"]["new"]["weapon_attachments"] = table
        project.write_text(json.dumps(document))
        build(project, root / "weapon-visual-built")
        pack4 = root / "weapon-visual-built/pack"
        manifest4 = json.loads((pack4 / "pack.json").read_text())
        select([(pack4, manifest4)], host, appearance_mode="original")
        with self.assertRaisesRegex(ValueError, "owned-chassis-weapon-visuals version 1"):
            select([(pack4, manifest4)], host, appearance_mode="new")
        host["content_capabilities"]["owned-chassis-weapon-visuals"] = [1]
        selected4 = select([(pack4, manifest4)], host, appearance_mode="new")
        self.assertTrue(selected4[0]["owned_visuals"]["weapon_attachments"])
        prepared4 = prepare(selected4, fixture_game, root / "weapon-prepared", {})
        from prepared_chassis_packs import CATALOG_KEY
        self.assertEqual(Path(prepared4[CATALOG_KEY]).read_bytes()[:8], b"MWCHAS8\0")

    def test_authored_arm_policy_topology(self):
        mesh = geometry(policy=3)
        self.assertEqual(mesh_metadata(mesh)["capability_version"], 3)
        for offset, data in (
            (128 + 2 * 196, struct.pack("<i", 0)),
            (128 + 4 * 196, struct.pack("<i", 3)),
            (64 + 4 * 196 + 32, name("rhand")),
            (64 + 2 * 196, name("Foreign")),
            (64 + 6 * 196 + 64, struct.pack("<i", 4)),
            (64 + 2 * 196 + 68, struct.pack("<d", 0.0)),
        ):
            invalid = bytearray(mesh); invalid[offset:offset+len(data)] = data
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                mesh_metadata(bytes(invalid))

    def test_source_joint_mode_and_unknown_flags(self):
        self.assertEqual(mesh_metadata(self.mesh)["capability_version"], 1)
        for flags in (1, 2, 3, 4, 0xFFFFFFFF):
            data = bytearray(self.mesh)
            struct.pack_into("<I", data, 20, flags)
            if flags > 2:
                with self.assertRaises(ValueError):
                    mesh_metadata(bytes(data))
            else:
                self.assertEqual(mesh_metadata(bytes(data))["capability_version"], flags)

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

    def test_weapon_visual_attachments_are_mesh_bound_and_selected_only(self):
        from surface_materials import mesh_uv_identity
        mesh = bytearray(geometry(tuple((c, c) for c in CONTROLS), policy=3))
        start = 64 + 12 * 196 + 12 * 160
        for index in range(12):
            struct.pack_into("<I", mesh, start + 64, index)
            start += 76 + 3 * 32
        self.resources["mesh"] = bytes(mesh)
        self.resources["texture"] = (b"BWTEX1\0\0" + struct.pack("<2I", 12, 1)
                                      + bytes(12 * 4) + self.texture[20:])
        table = {"schema_version": 1}
        rows = [dict(source_control=c, weapon="ERLargeLaser", bone=b, position=[0, 0, 0])
                for c, b in (("lhand", "Forearm_Left"), ("rhand", "Forearm_Right"))]
        for lod in ("close", "distance"):
            table[lod] = dict(mesh_identity=f"{mesh_uv_identity(bytes(mesh)):016x}", records=copy.deepcopy(rows))
        self.value["weapon_attachments"] = table
        result = self.read()
        self.assertEqual(result["weapon_attachments"]["close"]["records"], rows)
        visual = dict(rosters=result["rosters"], cockpit=[],
                      meshes={l: "mesh.bin" for l in ("close", "distance")},
                      textures={l: "texture.bin" for l in ("close", "distance")},
                      skin_textures={}, arm_damage=result["arm_damage"],
                      weapon_attachments=result["weapon_attachments"])
        record = dict(id="community.test:mech", name="Test", resource="example",
                      metadata_template="annihilator", owned_visuals=visual)
        self.assertEqual(encode_catalog([record])[:8], b"MWCHAS8\0")
        mutations = [lambda t: t["close"].update(mesh_identity="0" * 16),
                     lambda t: t["distance"]["records"].reverse(),
                     lambda t: t["close"]["records"].append(copy.deepcopy(rows[0])),
                     lambda t: t["close"]["records"][0].update(bone="Forearm_Right"),
                     lambda t: t["close"]["records"][0].update(position=[1, 0, 0]),
                     lambda t: t["close"]["records"][0].update(position=[float('nan'), 0, 0]),
                     lambda t: t.update(schema_version=True)]
        for mutate in mutations:
            invalid = copy.deepcopy(self.value)
            mutate(invalid["weapon_attachments"])
            with self.assertRaises(ValueError):
                self.read(invalid)

    def test_source_arm_subtrees_and_catalog_bounds(self):
        mesh = bytearray(self.mesh)
        struct.pack_into("<I", mesh, 20, 2)
        self.resources["mesh"] = bytes(mesh)
        result = self.read()
        self.assertEqual(result["arm_damage"]["close"], [
            dict(arm="larm", parent="hip", removed=["larm"]),
            dict(arm="rarm", parent="hip", removed=["rarm"]),
        ])
        visual = dict(rosters=result["rosters"], cockpit=[],
                      meshes={l: "mesh.bin" for l in ("close", "distance")},
                      textures={l: "texture.bin" for l in ("close", "distance")},
                      skin_textures={}, arm_damage=result["arm_damage"])
        record = dict(id="community.test:mech", name="Test", resource="example",
                      metadata_template="annihilator", owned_visuals=visual)
        self.assertEqual(encode_catalog([record])[:8], b"MWCHAS7\0")
        for plan in (dict(arm="hip", parent="hip", removed=["larm"]),
                     dict(arm="larm", parent="../hip", removed=["larm"]),
                     dict(arm="larm", parent="hip", removed=["foreign"]),
                     dict(arm="larm", parent="hip", removed=["larm", "larm"]),
                     dict(arm="larm", parent="hip", removed=[])):
            broken = copy.deepcopy(record)
            broken["owned_visuals"]["arm_damage"]["close"] = [plan]
            with self.subTest(plan=plan), self.assertRaises(ValueError):
                encode_catalog([broken])
        nested = bytearray(tree())
        node_size = len(nested) // len(CONTROLS)
        struct.pack_into("<I", nested, 92, 10)
        struct.pack_into("<I", nested, CONTROLS.index("larm") * node_size + 92, 1)
        self.legacy["models"]["close"] = bytes(nested)
        with self.assertRaisesRegex(ValueError, "Unsupported original arm subtree"):
            self.read()

    def test_source_joint_lods_remain_distinct_after_arm_loss(self):
        mesh = bytearray(self.mesh)
        struct.pack_into("<I", mesh, 20, 2)
        self.resources["mesh"] = bytes(mesh)
        self.legacy["models"]["distance"] = tree()
        for counts in ({"larm": 6}, {"rarm": 6}, {"larm": 6, "rarm": 6}):
            self.legacy["models"]["close"] = tree(counts)
            with self.subTest(counts=counts), self.assertRaisesRegex(ValueError, "after arm loss"):
                self.read()
        self.legacy["models"]["close"] = tree({"torso": 6})
        self.read()
        # A pre-existing stump must not alias a stump introduced by another mask.
        self.legacy["models"]["close"] = tree({"torso": 6}, extra=("larm_stub01",))
        with self.assertRaisesRegex(ValueError, "already contains an arm stump"):
            self.read()
        # Existing retarget modes retain their prior intact-signature contract.
        self.legacy["models"]["close"] = tree({"larm": 6})
        for flags in (0, 1):
            struct.pack_into("<I", mesh, 20, flags)
            self.resources["mesh"] = bytes(mesh)
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
