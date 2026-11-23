import copy
import json
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_prepared_chassis_packs as fixtures
from build_chassis_pack import build
from chassis_appearances import choose, compose_normals, inherited_pages, mode, validate
from legacy_chassis_resources import image_members
from normal_materials import pack_surface_bindings, pixel_hash, read_surface_bindings
from prepared_chassis_packs import _banks, prepare, select
from play_remaster import (
    _chassis_preparation_environment,
    _prepared_profile_bindings,
)
from zrd_document import encode


def texture(word):
    return struct.pack("<IHHIHHH", 5, 1, 1, 0, 0, 0, word)


class AppearanceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.original = texture(0x4321)
        self.upgrade = texture(0x1234)
        self.key = (1, 1, 1, pixel_hash(self.upgrade[16:]))
        self.normal = (1, 1, bytes([128, 128, 255, 255]))
        self.page = pack_surface_bindings([(self.key, self.normal)])
        self.resources = {"up.bin": self.upgrade, "normal.bin": self.page}
        self.appearances = {
            "upgraded": {"textures": {"example_skin": "up.bin"}, "normals": ["normal.bin"]}
        }
        self.legacy = {
            "textures": {"example_skin": self.original},
            "models": {"close": b"geometry"},
            "definition": ["gameplay"],
            "headlights": [{"id": "left", "range": 92}],
        }
        self.host = {
            "content_capabilities": {"additional-mech-chassis": [1, 2, 3], "mech-appearances": [1]},
            "normal_map_formats": [2],
            "authored_normal_catalog_versions": [1],
        }

    def validated(self, appearances=None):
        return validate(
            appearances or self.appearances, self.legacy, lambda path, fmt: self.resources[path]
        )

    def pack(self):
        project, self.descriptor, self.definition = fixtures.ChassisPackTests.legacy_project(self)
        for name, data in self.resources.items():
            (self.root / name).write_bytes(data)
        document = json.loads(project.read_text())
        document["chassis"][0]["appearances"] = self.appearances
        project.write_text(json.dumps(document))
        build(project, self.root / "built")
        root = self.root / "built/pack"
        return root, json.loads((root / "pack.json").read_text())

    def test_select_changes_only_colors_and_retains_input_and_lamps(self):
        before = copy.deepcopy(self.legacy)
        upgraded = self.validated()
        for request, expected in [
            (None, "original"),
            ("original", "original"),
            ("upgraded", "upgraded"),
            ("new", "upgraded"),
        ]:
            with self.subTest(request=request):
                chosen, pages, coverage = choose(self.legacy, upgraded, request)
                self.assertEqual(coverage["selected"], expected)
                self.assertEqual(
                    chosen["textures"]["example_skin"],
                    self.upgrade if expected == "upgraded" else self.original,
                )
                self.assertEqual(pages, [self.page] if expected == "upgraded" else [])
                self.assertEqual(
                    coverage["reason"], "new-model-unavailable" if request == "new" else None
                )
                for role in ("definition", "models", "headlights"):
                    self.assertEqual(chosen[role], before[role])
        self.assertEqual(self.legacy, before)

    def test_fallback_without_optional_upgrade(self):
        selected, pages, coverage = choose(self.legacy, None, "upgraded")
        self.assertEqual(selected, self.legacy)
        self.assertEqual(pages, [])
        self.assertEqual(
            coverage,
            {"requested": "upgraded", "selected": "original", "reason": "upgrade-unavailable"},
        )
        for value in ("unknown", "", False, [], {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                mode(value)

    def test_rejects_changes_outside_texture_contract(self):
        mutations = [
            lambda a: a.update(new={}),
            lambda a: a["upgraded"].update(models={}),
            lambda a: a["upgraded"].update(headlights=[]),
            lambda a: a["upgraded"]["textures"].update(foreign="up.bin"),
            lambda a: a["upgraded"].update(textures={}),
            lambda a: a["upgraded"].update(normals=["normal.bin", "normal.bin"]),
        ]
        for mutate in mutations:
            candidate = copy.deepcopy(self.appearances)
            mutate(candidate)
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                self.validated(candidate)

    def test_normals_must_match_selected_color_and_valid_binary(self):
        cases = [
            self.page[:-1],
            self.page + b"x",
            pack_surface_bindings([((1, 1, 1, 5), self.normal)]),
        ]
        for data in cases:
            self.resources["normal.bin"] = data
            with self.subTest(data=data[:12]), self.assertRaises(ValueError):
                self.validated()
        self.resources["normal.bin"] = self.page
        self.resources["second.bin"] = self.page
        self.appearances["upgraded"]["normals"].append("second.bin")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.validated()

    def test_pack_modes_keep_one_registration_and_validate_inactive_pages(self):
        root, manifest = self.pack()
        before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
        original = select([(root, manifest)], self.host, appearance_mode="original")[0]
        upgraded = select([(root, manifest)], self.host, appearance_mode="upgraded")[0]
        self.assertEqual(original["registration"], upgraded["registration"])
        self.assertEqual(upgraded["registration"]["id"], "community.legacy:mech")
        self.assertEqual(upgraded["legacy"]["textures"]["example_skin"], self.upgrade)
        for role in original["legacy"].keys() - {"textures"}:
            self.assertEqual(original["legacy"][role], upgraded["legacy"][role])
        no_normals = copy.deepcopy(self.host)
        no_normals.pop("normal_map_formats")
        select([(root, manifest)], no_normals, appearance_mode="original")
        with self.assertRaisesRegex(ValueError, "normal map format"):
            select([(root, manifest)], no_normals, appearance_mode="upgraded")
        no_catalog_version = copy.deepcopy(self.host)
        no_catalog_version.pop("authored_normal_catalog_versions")
        with self.assertRaisesRegex(ValueError, "authored normal catalog version 1"):
            select([(root, manifest)], no_catalog_version, appearance_mode="upgraded")
        no_feature = copy.deepcopy(self.host)
        no_feature["content_capabilities"].pop("mech-appearances")
        with self.assertRaisesRegex(ValueError, "Update the game runtime"):
            select([(root, manifest)], no_feature)
        self.assertEqual(before, {p: p.read_bytes() for p in before})
        page_path = next(
            root / name for name, pin in manifest["files"].items() if pin.get("format") == "BWSNR2"
        )
        page_path.write_bytes(self.page[:-1])
        with self.assertRaises(ValueError):
            select([(root, manifest)], self.host, appearance_mode="original")

    def test_coordinator_forwards_mode_and_returns_fallback_coverage(self):
        from prepared_mech_packs import compose

        root, _ = self.pack()
        records = []
        compose([str(root)], self.host | {"mech_appearance": "new"}, chassis_records=records)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["legacy"]["textures"]["example_skin"], self.upgrade)
        self.assertEqual(
            records[0]["appearance"],
            {"requested": "new", "selected": "upgraded", "reason": "new-model-unavailable"},
        )

    def test_composition_checks_expanded_output_budget(self):
        world = self.root / "compressed.bin"
        large_normal = (16, 16, self.normal[2] * 256)
        world.write_bytes(pack_surface_bindings([((1, 1, 1, 99), large_normal)], compressed=True))
        with (
            patch("chassis_appearances.MAX_CATALOG_BYTES", 512),
            self.assertRaisesRegex(ValueError, "resident budget"),
        ):
            compose_normals(
                [{"appearance_normal_pages": [self.page]}],
                {"MW34_SURFACE_NORMALS": str(world)},
                self.root / "too-large",
            )

    def test_composer_preserves_inherited_native_page_budget(self):
        world = self.root / "world.bin"
        world_normal = (2, 2, self.normal[2] * 4)
        world.write_bytes(pack_surface_bindings([((1, 1, 1, 99), world_normal)]))
        # Scale only the authored-pack limit so the fixture exercises an inherited
        # native page larger than that limit without allocating hundreds of MiB.
        with patch("chassis_appearances.MAX_PAGE_BYTES", len(self.page)):
            result = compose_normals(
                [{"appearance_normal_pages": [self.page]}],
                {"MW34_SURFACE_NORMALS": str(world)},
                self.root / "inherited",
            )
        bindings = {}
        for page in inherited_pages(result["MW34_SURFACE_NORMALS"]):
            bindings.update(read_surface_bindings(page.read_bytes()))
        self.assertEqual(bindings, {(1, 1, 1, 99): world_normal, self.key: self.normal})

    def test_composer_keeps_world_normals_and_does_not_change_settings(self):
        world_key = (1, 1, 1, 99)
        world = self.root / "world.bin"
        world.write_bytes(pack_surface_bindings([(world_key, self.normal)]))
        index = self.root / "world.txt"
        index.write_text("MW34SNA1\nworld.bin\n")
        environment = {
            "MW34_SURFACE_NORMALS": str(index),
            "MW34_NORMAL_MAPS": "0",
            "MW34_MECH_HEADLIGHTS": "1",
        }
        before = dict(environment)
        self.assertEqual(compose_normals([{}], environment, self.root / "none"), {})
        result = compose_normals(
            [{"appearance_normal_pages": [self.page]}], environment, self.root / "out"
        )
        bindings = {}
        for path in inherited_pages(result["MW34_SURFACE_NORMALS"]):
            bindings.update(read_surface_bindings(path.read_bytes()))
        self.assertEqual(bindings, {world_key: self.normal, self.key: self.normal})
        self.assertEqual(environment, before)
        self.assertEqual(set(result), {"MW34_SURFACE_NORMALS"})
        world.write_bytes(pack_surface_bindings([(self.key, (1, 1, bytes([127, 128, 255, 255])))]))
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            compose_normals(
                [{"appearance_normal_pages": [self.page]}], environment, self.root / "conflict"
            )

    def test_composer_repackages_sixteen_inherited_pages_with_appearance_page(self):
        world_pages = []
        world_keys = [(1, 1, 1, 0x100000 + index) for index in range(16)]
        for index, key in enumerate(world_keys):
            page = self.root / f"world-{index}.bin"
            page.write_bytes(pack_surface_bindings([(key, self.normal)]))
            world_pages.append(page.name)
        index = self.root / "world.txt"
        index.write_text("MW34SNA1\n" + "\n".join(world_pages) + "\n")
        result = compose_normals(
            [{"appearance_normal_pages": [self.page]}],
            {"MW34_SURFACE_NORMALS": str(index)},
            self.root / "combined",
        )
        pages = inherited_pages(result["MW34_SURFACE_NORMALS"])
        self.assertLessEqual(len(pages), 16)
        bindings = {}
        for page in pages:
            bindings.update(read_surface_bindings(page.read_bytes()))
        self.assertEqual(set(bindings), {*world_keys, self.key})

    def test_chassis_preparation_environment_preserves_and_resolves_profile_catalog(self):
        profile_environment = {"MW34_SURFACE_NORMALS": "world/surface-normals.txt"}
        prepared_environment = {"MW34_REMASTER_BANKS": "/prepared/banks.bin"}
        with patch("play_remaster.ROOT", self.root):
            effective = _chassis_preparation_environment(
                profile_environment, prepared_environment
            )
        self.assertEqual(
            effective["MW34_SURFACE_NORMALS"],
            str((self.root / "world/surface-normals.txt").resolve()),
        )
        self.assertEqual(effective["MW34_REMASTER_BANKS"], "/prepared/banks.bin")
        self.assertEqual(
            _prepared_profile_bindings(profile_environment, prepared_environment),
            {
                "MW34_SURFACE_NORMALS": "world/surface-normals.txt",
                "MW34_REMASTER_BANKS": "/prepared/banks.bin",
            },
        )
        fresh_catalog = {"MW34_SURFACE_NORMALS": "/prepared/fresh.txt"}
        self.assertEqual(
            _chassis_preparation_environment(profile_environment, fresh_catalog)[
                "MW34_SURFACE_NORMALS"
            ],
            "/prepared/fresh.txt",
        )

    def test_native_bank_preparation_contains_upgrade_and_normal_catalog(self):
        root, manifest = self.pack()
        records = select([(root, manifest)], self.host, appearance_mode="upgraded")
        directory = self.root / "game/zbd"
        directory.mkdir(parents=True)
        common = encode(
            [
                [
                    "ANIMATION_DEFINITIONS",
                    ["ANIMATION_LIST", ["ANIMATION_DEFINITION_FILE", ["stock.zrd"]]],
                ]
            ]
        )
        stock = {
            "reader.zbd": fixtures.archive(
                {"dfn_annihilator.zrd": encode(self.definition), "commonAnim.zrd": common}
            ),
            "mechlib.zbd": fixtures.archive(
                {"materials": (self.root / "material.bin").read_bytes(), "stock.flt": b"original"}
            ),
            "motion.zbd": fixtures.archive({"stock_walk": b"original"}),
        }
        bank = (
            struct.pack("<6I", 0, 1, 0, 1, 0, 0)
            + struct.pack("<32sII", b"stock", 64, 0xFFFFFFFF)
            + self.original
        )
        stock.update({"rmechtex.zbd": bank, "rimage.zbd": bank})
        for name, data in stock.items():
            (directory / name).write_bytes(data)
        result = prepare(records, directory.parent / "Mech3.exe", self.root / "out", {})
        textures = image_members(
            Path(_banks(result["MW34_REMASTER_BANKS"])["zbd/rmechtex.zbd"]).read_bytes()
        )
        self.assertIn(self.upgrade, [data for data, flags in textures.values()])
        self.assertEqual(textures["stock"][0], self.original)
        pages = inherited_pages(result["MW34_SURFACE_NORMALS"])
        self.assertEqual(
            dict(read_surface_bindings(pages[0].read_bytes())), {self.key: self.normal}
        )
        for name, data in stock.items():
            self.assertEqual((directory / name).read_bytes(), data)

    def test_builder_rejects_malformed_headlights(self):
        project, _, _ = fixtures.ChassisPackTests.legacy_project(self)
        document = json.loads(project.read_text())
        document["chassis"][0]["headlights"] = [{"id": "preserve-me"}]
        project.write_text(json.dumps(document))
        with self.assertRaisesRegex(ValueError, "Invalid headlight fields"):
            build(project, self.root / "rejected")

    def test_builder_rejects_unsafe_appearance_path(self):
        self.appearances["upgraded"]["textures"]["example_skin"] = "../outside.bin"
        with self.assertRaisesRegex(ValueError, "Unsafe pack path"):
            self.pack()


if __name__ == "__main__":
    unittest.main()
