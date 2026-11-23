"""Synthetic legacy skin contracts; no game media or converter is required."""

import copy
import json
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

import test_prepared_chassis_packs as fixtures
from build_chassis_pack import build
from legacy_chassis_resources import append_images, image_members, load, members
from legacy_chassis_skins import CAPABILITY, definition_skins, metadata, texture_names, validate
from prepared_chassis_packs import REGISTRY, _banks, prepare, select
from zrd_document import decode, encode

archive = fixtures.archive


class LegacySkinTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        fixture = fixtures.ChassisPackTests()
        fixture.root = self.root
        self.project, self.descriptor, self.definition = fixture.legacy_project()
        block = ["MSG_SKIN_PRIMARY", ["paint0", "paint1", ["scar0", "paint0"]]]
        for letter in "BCDEFGH":
            block.extend(["MSG_SKIN_VARIANT" + letter, ["_" + letter.lower()]])
        block.extend(["damage", [0, 0, "damage0"]])
        self.definition[0].extend(["skins", block])
        self.rows, _, self.required = definition_skins(self.definition)
        self.descriptor.update(schema_version=2, skins=self.rows, textures={})
        for index, row in enumerate(self.rows):
            for base in ("paint0", "paint1", "scar0"):
                name = base + row["suffix"]
                pixels = struct.pack("<IHHIHHH", 3, 1, 1, 0, 0, 0, index + 1)
                (self.root / (name + ".bin")).write_bytes(pixels)
                self.descriptor["textures"][name] = name + ".bin"
        for name in ("glass", "damage0"):
            (self.root / (name + ".bin")).write_bytes(pixels)
            self.descriptor["textures"][name] = name + ".bin"
        material = bytearray(40)
        material[1] = 1
        (self.root / "material.bin").write_bytes(
            struct.pack("<I", 1) + material + struct.pack("<I", 6) + b"paint0"
        )
        self.save()
        self.host = {
            "content_capabilities": {"additional-mech-chassis": [1, 2, 3], CAPABILITY: [1]}
        }

    def save(self):
        (self.root / "legacy.json").write_text(json.dumps(self.descriptor))
        (self.root / "legacy-definition.zrd").write_bytes(encode(self.definition))

    def loaded(self):
        self.save()
        return load(self.descriptor, lambda name: (self.root / name).read_bytes())

    def test_all_eight_families_and_aliases_keep_their_pixels(self):
        data = self.loaded()
        names = texture_names(data, "c123456789012")
        self.assertEqual(len(names), len(self.descriptor["textures"]))
        for index, row in enumerate(self.rows):
            suffix = row["suffix"]
            for base in ("paint0", "paint1", "scar0"):
                self.assertEqual(names[base + suffix], names[base] + suffix)
                self.assertEqual(
                    struct.unpack_from("<H", data["textures"][base + suffix], 16)[0], index + 1
                )
        self.assertNotIn("glass_b", names)
        self.assertEqual(data["skins"], self.rows)

    def test_malformed_metadata_and_lookup_closure_rejected(self):
        for mutate in (
            lambda rows: rows.clear(),
            lambda rows: rows.append(copy.deepcopy(rows[-1])),
            lambda rows: rows[1].update(id=rows[0]["id"]),
            lambda rows: rows[1].update(message="MSG_SKIN_VARIANTC"),
            lambda rows: rows[0].update(suffix="_a"),
            lambda rows: rows[2].update(suffix="_b"),
            lambda rows: rows[1].update(suffix="../b"),
            lambda rows: rows[1].update(suffix=True),
            lambda rows: rows[1].update(extra=1),
        ):
            rows = copy.deepcopy(self.rows)
            mutate(rows)
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                metadata(rows)
        textures = self.loaded()["textures"]
        for name in ("paint1_h", "scar0_b", "damage0"):
            with self.subTest(missing=name), self.assertRaisesRegex(ValueError, "Missing"):
                validate(
                    self.definition,
                    {key: value for key, value in textures.items() if key != name},
                    self.rows,
                )
        rows = copy.deepcopy(self.rows)
        rows[1]["suffix"] = "_other"
        with self.assertRaisesRegex(ValueError, "disagree"):
            validate(self.definition, textures, rows)

    def test_invalid_definition_shapes_lengths_and_ambiguous_families(self):
        original = copy.deepcopy(self.definition)
        block = original[0][-1]
        mutations = [
            block + ["MSG_SKIN_PRIMARY", ["paint0"]],
            block[:-1] + [[0]],
            ["MSG_SKIN_PRIMARY", [["paint0"]]],
            ["MSG_SKIN_PRIMARY", [True]],
            ["MSG_SKIN_PRIMARY", ["a" * 31], "MSG_SKIN_VARIANTB", ["_b"]],
            ["MSG_SKIN_PRIMARY", ["paint0"], "damage", [False]],
        ]
        for value in mutations:
            definition = copy.deepcopy(original)
            definition[0][-1] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                definition_skins(definition)
        data = self.loaded()
        data["definition"][0][-1][1].append("paint0_b")
        data["definition"][0][-1][-1].append(0)
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            texture_names(data, "c123")

    def test_schema_one_compatibility_and_downgrade_rejection(self):
        self.descriptor.pop("skins")
        self.descriptor["schema_version"] = 1
        with self.assertRaisesRegex(ValueError, "upgrade"):
            self.loaded()
        self.definition[0][-1] = self.definition[0][-1][:2]
        data = self.loaded()
        self.assertNotIn("skins", data)
        self.assertEqual(
            texture_names(data, "c123"),
            {name: "c123_t" + str(index) for index, name in enumerate(sorted(data["textures"]))},
        )
        for version in (True, 3, "2"):
            self.descriptor["schema_version"] = version
            with self.subTest(version=version), self.assertRaises(ValueError):
                self.loaded()

    def test_resource_names_and_paths_remain_bounded(self):
        for name in ("PAINT0", "a" * 32):
            bad = copy.deepcopy(self.descriptor)
            bad["textures"][name] = "paint0.bin"
            with self.subTest(name=name), self.assertRaises(ValueError):
                load(bad, lambda path: (self.root / path).read_bytes())
        self.descriptor["textures"]["paint0"] = "../paint0.bin"
        self.save()
        with self.assertRaises(ValueError):
            build(self.project, self.root / "escaped")

    def built(self):
        build(self.project, self.root / "built")
        root = self.root / "built/pack"
        return root, json.loads((root / "pack.json").read_text())

    def test_legacy_skins_and_appearances_keep_independent_capabilities(self):
        from chassis_appearances import CAPABILITY as APPEARANCES_CAPABILITY

        upgraded = struct.pack("<IHHIHHH", 3, 1, 1, 0, 0, 0, 99)
        (self.root / "upgrade.bin").write_bytes(upgraded)
        project = json.loads(self.project.read_text())
        project["chassis"][0]["headlights"] = [
            {
                "id": "lamp",
                "space": "guest_node",
                "attachment": "torso",
                "position": [1.0, 2.0, 3.0],
                "direction": [0.0, 0.0, 1.0],
                "color": [1.0, 0.8, 0.6],
                "intensity": 2.0,
                "range": 92.0,
                "inner_angle": 15.0,
                "outer_angle": 30.0,
            }
        ]
        project["chassis"][0]["appearances"] = {
            "upgraded": {"textures": {"paint0": "upgrade.bin"}, "normals": []}
        }
        self.project.write_text(json.dumps(project))
        root, manifest = self.built()
        required = manifest["native_payload"]["required_capabilities"]
        self.assertEqual(required[CAPABILITY], 1)
        self.assertEqual(required[APPEARANCES_CAPABILITY], 1)
        self.assertEqual(required["mech-headlights"], 1)

        host = copy.deepcopy(self.host)
        host["content_capabilities"][APPEARANCES_CAPABILITY] = [1]
        host["content_capabilities"]["mech-headlights"] = [1]
        selected = select([(root, manifest)], host, appearance_mode="upgraded")
        self.assertEqual(selected[0]["appearance"]["selected"], "upgraded")
        self.assertEqual(selected[0]["legacy"]["textures"]["paint0"], upgraded)
        self.assertEqual(selected[0]["registration"]["headlights"][0]["id"], "lamp")

        for capability in (CAPABILITY, APPEARANCES_CAPABILITY, "mech-headlights"):
            unsupported_host = copy.deepcopy(host)
            unsupported_host["content_capabilities"].pop(capability)
            with self.subTest(capability=capability), self.assertRaisesRegex(
                ValueError, "Update the game runtime"
            ):
                select([(root, manifest)], unsupported_host, appearance_mode="upgraded")

    def test_pack_gate_and_hash_validation(self):
        root, manifest = self.built()
        self.assertEqual(manifest["native_payload"]["required_capabilities"][CAPABILITY], 1)
        self.assertEqual(len(select([(root, manifest)], self.host)[0]["legacy"]["skins"]), 8)
        with self.assertRaisesRegex(ValueError, "Update the game runtime"):
            select(
                [(root, manifest)], {"content_capabilities": {"additional-mech-chassis": [1, 2, 3]}}
            )
        manifest["native_payload"]["required_capabilities"].pop(CAPABILITY)
        with self.assertRaisesRegex(ValueError, "descriptor requires"):
            select([(root, manifest)], self.host)
        manifest["native_payload"]["required_capabilities"][CAPABILITY] = 1
        registry = json.loads((root / REGISTRY).read_text())
        descriptor = json.loads((root / registry["chassis"][0]["legacy"]).read_text())
        (root / descriptor["textures"]["paint0_h"]).write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError, "size mismatch|integrity"):
            select([(root, manifest)], self.host)

    def test_composed_native_definition_resolves_every_alias_and_preserves_stock(self):
        # Legal shared texture names must not rewrite skin grammar or suffixes.
        for name in ("_b", "skins", "damage", "MSG_SKIN_VARIANTB"):
            self.descriptor["textures"][name] = "glass.bin"
        self.save()
        root, manifest = self.built()
        records = select([(root, manifest)], self.host)
        game = self.root / "game/zbd"
        game.mkdir(parents=True)
        common = encode(
            [
                [
                    "ANIMATION_DEFINITIONS",
                    ["ANIMATION_LIST", ["ANIMATION_DEFINITION_FILE", ["stock.zrd"]]],
                ]
            ]
        )
        image = (self.root / "glass.bin").read_bytes()
        images = struct.pack("<6I32sII", 0, 1, 0, 1, 0, 0, b"stock", 64, 0xFFFFFFFF) + image
        originals = {
            "reader.zbd": archive(
                {"dfn_annihilator.zrd": encode(self.definition), "commonanim.zrd": common}
            ),
            "mechlib.zbd": archive(
                {
                    "materials": (self.root / "material.bin").read_bytes(),
                    "stock.flt": b"stock model",
                }
            ),
            "motion.zbd": archive({"stock_walk": b"stock motion"}),
            "rmechtex.zbd": images,
            "rimage.zbd": images,
        }
        for name, blob in originals.items():
            (game / name).write_bytes(blob)
        mapping = prepare(records, game.parent / "Mech3.exe", self.root / "session", {})
        banks = _banks(mapping["MW34_REMASTER_BANKS"])
        resource = records[0]["registration"]["resource"]
        definition = decode(
            members(Path(banks["zbd/reader.zbd"]).read_bytes())["dfn_" + resource + ".zrd"]
        )
        textures = image_members(Path(banks["zbd/rmechtex.zbd"]).read_bytes())
        validate(definition, textures, self.rows)
        block = definition[0][-1]
        primary = block[1]
        for index, row in enumerate(self.rows):
            for name in (primary[0], *primary[2]):
                self.assertEqual(
                    struct.unpack_from("<H", textures[name + row["suffix"]][0], 16)[0], index + 1
                )
        self.assertEqual(textures["stock"][0], image)
        for name, blob in originals.items():
            self.assertEqual((game / name).read_bytes(), blob)
        before = self.definition[0][:-2]
        after = definition[0][:-2]
        self.assertEqual(before[:-2], after[:-2])  # Unchanged mass/class/technology.

    def test_two_packs_keep_identities_and_texture_families_isolated(self):
        first = self.built()
        project = json.loads(self.project.read_text())
        project["pack_id"] = "another.legacy"
        other_project = self.root / "other.json"
        other_project.write_text(json.dumps(project))
        build(other_project, self.root / "other")
        second = (
            self.root / "other/pack",
            json.loads((self.root / "other/pack/pack.json").read_text()),
        )
        forward = select([first, second], self.host)
        self.assertEqual(forward, select([second, first], self.host))
        families = [
            set(texture_names(row["legacy"], row["registration"]["resource"]).values())
            for row in forward
        ]
        self.assertFalse(families[0] & families[1])

    def test_authoring_all_mode_keeps_suffix_alias_closure(self):
        from prepare_legacy_chassis import prepare as author

        game = self.root / "donor"
        (game / "zbd").mkdir(parents=True)
        definition = copy.deepcopy(self.definition)
        definition[0].extend(["configurations", ["MSG_CONFIG_PRIMARY", ["value", [1]]]])
        (game / "zbd/reader.zbd").write_bytes(
            archive(
                {
                    "dfn_example.zrd": encode(definition),
                    "anim_example.zrd": encode([["animation", [1]]]),
                    "example_prints.zrd": encode([["prints", [1]]]),
                }
            )
        )
        for name in ("mechlib.zbd", "motion.zbd"):
            (game / "zbd" / name).write_bytes(b"source fixture")
        image = (self.root / "glass.bin").read_bytes()
        seed = struct.pack("<6I32sII", 0, 1, 0, 1, 0, 0, b"glass", 64, 0xFFFFFFFF) + image
        textures = {
            name: (self.root / path).read_bytes()
            for name, path in self.descriptor["textures"].items()
            if name != "glass"
        }
        (game / "zbd/rmechtex.zbd").write_bytes(append_images(seed, textures))
        icon = (self.root / "image.bin").read_bytes()
        (game / "zbd/rimage.zbd").write_bytes(
            struct.pack("<6I32sII", 0, 1, 0, 1, 0, 0, b"icon_example_green", 64, 0xFFFFFFFF) + icon
        )
        converter = self.root / "converter"
        converter.mkdir()
        for tool in ("unzbd", "rezbd"):
            (converter / (tool + ".exe")).write_bytes(b"never executed fixture")

        def convert(command, **kwargs):
            output = Path(command[-1])
            if Path(command[0]).stem == "unzbd":
                with zipfile.ZipFile(output, "w") as z:
                    z.writestr("manifest.json", "[]")
                    z.writestr("materials.json", '[{"Textured":{"texture_name":"paint0"}}]')
                    for suffix in ("", "_1", "_hud"):
                        z.writestr(
                            "mech_example" + suffix + ".flt.json",
                            json.dumps(
                                {"models": [{"polygons": [{"materials": [{"material_index": 0}]}]}]}
                            ),
                        )
            elif command[2] == "mechlib":
                output.write_bytes(
                    archive(
                        {
                            "materials": (self.root / "material.bin").read_bytes(),
                            **{
                                "mech_example" + suffix + ".flt": (
                                    self.root / "node.bin"
                                ).read_bytes()
                                for suffix in ("", "_1", "_hud")
                            },
                        }
                    )
                )
            else:
                output.write_bytes(
                    archive({"example_walk": (self.root / "motion.bin").read_bytes()})
                )

        with patch("prepare_legacy_chassis.subprocess.run", side_effect=convert):
            project = author(
                game,
                "mw",
                "example",
                converter,
                self.root / "authored",
                "community.author",
                "Example",
                "annihilator",
                skins="all",
            )
        descriptor = json.loads((project.parent / "resources.json").read_text())
        data = load(descriptor, lambda name: (project.parent / name).read_bytes())
        self.assertEqual(len(data["skins"]), 8)
        self.assertEqual(set(data["textures"]), self.required)
        for name in self.required:
            self.assertEqual(
                data["textures"][name], (self.root / self.descriptor["textures"][name]).read_bytes()
            )


if __name__ == "__main__":
    unittest.main()
