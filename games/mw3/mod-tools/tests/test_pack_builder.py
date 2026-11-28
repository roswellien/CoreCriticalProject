"""The pack builder turns a source folder into a valid schema 3 `.mw3pack` archive.

Run from the repository root:
    python -m unittest discover -s games/mw3/mod-tools/tests -p "test_pack_builder.py"
or run this file directly. Standard library only, like tools/packs/test_example_packs.py.
The shared example packs in tests/fixtures/packs are the inputs.
"""

from __future__ import annotations

import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
MOD_TOOLS_DIR = TESTS_DIR.parent
REPO_ROOT = MOD_TOOLS_DIR.parents[2]
sys.path.insert(0, str(MOD_TOOLS_DIR))
sys.path.insert(0, str(REPO_ROOT / "tools" / "packs"))

import check_pack
import pack_builder

EXAMPLES = REPO_ROOT / "tests" / "fixtures" / "packs"

# Broken example packs whose fault survives the builder rewriting the file table.
# The table faults (file-*, path-unsafe) are what the builder fixes, and
# visual-target-unknown is the runtime's to find, so those are not sources that
# must fail here.
BROKEN_SOURCES = [
    "gameplay-root-invalid",
    "manifest-invalid",
    "manifest-unknown-field",
    "payload-executable",
    "visual-file-undeclared",
    "visual-needs-gameplay",
    "visual-target-invalid",
]


def tree_digest(folder: Path) -> str:
    """A hash over every file's path and content, to prove a folder was untouched."""
    digest = hashlib.sha256()
    for path in sorted(folder.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(folder).as_posix().encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def copy_source(fixture: Path, parent: Path, strip_written_fields: bool) -> Path:
    """Copy an example pack into a source folder, optionally as an author writes it.

    An author's source pack.json has no `files` or `provides`; the builder writes
    both. Stripping them gives the copy that form.
    """
    source = parent / fixture.name
    shutil.copytree(fixture, source)
    if strip_written_fields:
        manifest_path = source / "pack.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.pop("files", None)
        manifest.pop("provides", None)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return source


def unpack(archive_path: Path, folder: Path) -> Path:
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(folder)
    return folder


def written_archives(folder: Path) -> list[Path]:
    return list(folder.rglob("*.mw3pack")) if folder.is_dir() else []


class PackBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.output = self.root / "out"

    def test_valid_example_packs_build_unpack_and_check_clean(self) -> None:
        for fixture in sorted((EXAMPLES / "valid").iterdir()):
            with self.subTest(pack=fixture.name):
                manifest = json.loads((fixture / "pack.json").read_text(encoding="utf-8"))
                source = copy_source(fixture, self.root, strip_written_fields=False)
                source_digest = tree_digest(source)
                output = self.root / f"out-{fixture.name}"

                archive_path = pack_builder.build_pack(source, output)

                # The archive is <id>-<version>.mw3pack, a ZIP with pack.json at its
                # root, entries in a fixed order with a fixed timestamp.
                self.assertEqual(
                    archive_path, output / f"{manifest['id']}-{manifest['version']}.mw3pack"
                )
                with zipfile.ZipFile(archive_path) as archive:
                    names = archive.namelist()
                    self.assertIn("pack.json", names)
                    self.assertEqual(names, sorted(names))
                    self.assertFalse(any(name.endswith("/") for name in names))
                    for info in archive.infolist():
                        self.assertEqual(info.date_time, pack_builder.FIXED_ARCHIVE_DATE_TIME)

                # Unpacked, the archive is a pack the contract 1 check accepts, with
                # the same manifest the example pack's expected result has.
                unpacked = unpack(archive_path, self.root / f"unpacked-{fixture.name}")
                self.assertEqual(check_pack.check_pack(unpacked), [])
                built_manifest = json.loads((unpacked / "pack.json").read_text(encoding="utf-8"))
                self.assertEqual(built_manifest, manifest)

                # The source folder was never modified.
                self.assertEqual(tree_digest(source), source_digest)

    def test_author_source_without_files_or_provides_builds_the_same_archive(self) -> None:
        for fixture in sorted((EXAMPLES / "valid").iterdir()):
            with self.subTest(pack=fixture.name):
                plain = copy_source(fixture, self.root / "plain", strip_written_fields=False)
                stripped = copy_source(fixture, self.root / "stripped", strip_written_fields=True)
                first = pack_builder.build_pack(plain, self.root / "out-plain")
                second = pack_builder.build_pack(stripped, self.root / "out-stripped")
                self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_building_the_same_source_twice_gives_byte_identical_archives(self) -> None:
        source = copy_source(
            EXAMPLES / "valid" / "gameplay-only", self.root, strip_written_fields=True
        )
        first = pack_builder.build_pack(source, self.root / "out-first")
        second = pack_builder.build_pack(source, self.root / "out-second")
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_broken_packs_produce_no_archive(self) -> None:
        # The issue asks for at least three; every broken pack whose fault is not a
        # wrong file table is tried.
        self.assertGreaterEqual(len(BROKEN_SOURCES), 3)
        for name in BROKEN_SOURCES:
            with self.subTest(pack=name):
                source = copy_source(
                    EXAMPLES / "broken" / name, self.root, strip_written_fields=True
                )
                output = self.root / f"out-{name}"
                with self.assertRaises(pack_builder.PackBuildError) as raised:
                    pack_builder.build_pack(source, output)
                codes = [problem.code for problem in raised.exception.problems]
                self.assertEqual(codes, [name])
                self.assertEqual(written_archives(output), [])

    def test_main_prints_each_problem_with_its_code(self) -> None:
        source = copy_source(
            EXAMPLES / "broken" / "payload-executable", self.root, strip_written_fields=True
        )
        printed = io.StringIO()
        with redirect_stdout(printed):
            exit_code = pack_builder.main([str(source), str(self.output)])
        self.assertEqual(exit_code, 1)
        self.assertIn("payload-executable:", printed.getvalue())
        self.assertEqual(written_archives(self.output), [])

    def test_output_path_must_not_already_exist(self) -> None:
        source = copy_source(
            EXAMPLES / "valid" / "gameplay-only", self.root, strip_written_fields=True
        )
        first = pack_builder.build_pack(source, self.output)
        original_bytes = first.read_bytes()
        with self.assertRaises(pack_builder.OutputExistsError):
            pack_builder.build_pack(source, self.output)
        self.assertEqual(first.read_bytes(), original_bytes)

    def test_provides_come_from_the_pack_content(self) -> None:
        source = self.root / "src"
        (source / "mod" / "campaigns").mkdir(parents=True)
        (source / "visuals").mkdir(parents=True)
        manifest = {
            "schema_version": 3,
            "game_id": "mw3",
            "id": "test-provides",
            "name": "Provides test",
            "version": "1.0.0",
            "gameplay": {"root": "mod"},
            "visuals": [
                {
                    "target": "mech-model:thor",
                    "kind": "skin",
                    "name": "Test Skin",
                    "files": {"textures": "visuals/skin.bwtex"},
                }
            ],
        }
        (source / "pack.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (source / "mod" / "mod.txt").write_text(
            "name=Provides test\n"
            "mech=test_mech tech=clan mass=70 class=heavy model=thor title=Test Mech\n"
            "weapon=test_gun ammo=yes tech=clan title=Test Gun\n"
            "ia_world=testworld Test World\n"
            "campaign=campaigns/test.camp\n",
            encoding="utf-8",
        )
        (source / "mod" / "campaigns" / "test.camp").write_text(
            "name=Test Campaign\nmission=testworld 1\nmission=testworld 2\n",
            encoding="utf-8",
        )
        (source / "visuals" / "skin.bwtex").write_text("placeholder texture\n", encoding="utf-8")

        archive_path = pack_builder.build_pack(source, self.output)

        self.assertEqual(archive_path.name, "test-provides-1.0.0.mw3pack")
        unpacked = unpack(archive_path, self.root / "unpacked")
        self.assertEqual(check_pack.check_pack(unpacked), [])
        built_manifest = json.loads((unpacked / "pack.json").read_text(encoding="utf-8"))
        self.assertEqual(
            built_manifest["provides"],
            {
                "mechs": ["test_mech"],
                "weapons": ["test_gun"],
                "skins": ["Test Skin"],
                "maps": ["Test World"],
                "missions": ["testworld/1", "testworld/2"],
                "campaigns": ["Test Campaign"],
            },
        )


if __name__ == "__main__":
    unittest.main()
