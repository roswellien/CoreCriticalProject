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
import os
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


def write_source(folder: Path, manifest: dict, files: dict[str, str]) -> Path:
    """Create a source folder with its pack.json and text payload files."""
    folder.mkdir(parents=True)
    (folder / "pack.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for relative, content in files.items():
        path = folder / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return folder


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

    def test_source_containing_a_symbolic_link_is_refused(self) -> None:
        source = copy_source(
            EXAMPLES / "valid" / "gameplay-only", self.root, strip_written_fields=True
        )
        # A link to a file outside the source: copytree would follow it and package
        # that outside file.
        outside = self.root / "outside.txt"
        outside.write_text("content from outside the source\n", encoding="utf-8")
        link = source / "mod" / "linked.txt"
        try:
            os.symlink(outside, link)
        except (OSError, NotImplementedError) as error:
            # Windows refuses to create symlinks without the privilege; then there
            # is no link to test with here.
            self.skipTest(f"cannot create a symbolic link: {error}")

        with self.assertRaises(pack_builder.UnsafeSourceError) as raised:
            pack_builder.build_pack(source, self.output)
        # The error names the offending entry, and no archive was written.
        self.assertIn("linked.txt", str(raised.exception))
        self.assertEqual(written_archives(self.output), [])

        # main reports it too, with exit code 1 and still no archive.
        printed = io.StringIO()
        with redirect_stdout(printed):
            exit_code = pack_builder.main([str(source), str(self.output)])
        self.assertEqual(exit_code, 1)
        self.assertIn("linked.txt", printed.getvalue())
        self.assertEqual(written_archives(self.output), [])

    def test_case_clash_helper_names_both_paths(self) -> None:
        # The launcher's installer compares entry names without regard to case, so a
        # source holding both of these must be refused before building. The helper
        # is tested directly, because a case-sensitive disk is not always at hand.
        clash = pack_builder.find_case_clash(["a/skin.bwtex", "a/Skin.bwtex"])
        self.assertEqual(clash, ("a/skin.bwtex", "a/Skin.bwtex"))
        # The clash is found wherever in the list the pair sits.
        clash = pack_builder.find_case_clash(["mod/mod.txt", "a/skin.bwtex", "a/SKIN.BWTEX"])
        self.assertEqual(clash, ("a/skin.bwtex", "a/SKIN.BWTEX"))

    def test_case_clash_helper_finds_no_clash_in_an_ordinary_list(self) -> None:
        paths = ["pack.json", "mod/mod.txt", "textures/skin.bwtex", "textures/gun.bwtex"]
        self.assertIsNone(pack_builder.find_case_clash(paths))

    def test_files_table_is_ordered_by_sorted_path_strings(self) -> None:
        # fill_file_table sorts Path objects, whose order differs by platform
        # (Windows compares names case-insensitively), so the written manifest must
        # use plain sorted() on the path strings: "B.txt" (code point 66) comes
        # before "a.txt" (97) on every platform.
        source = write_source(
            self.root / "src",
            {
                "schema_version": 3,
                "game_id": "mw3",
                "id": "test-order",
                "name": "Order test",
                "version": "1.0.0",
            },
            {"a.txt": "lowercase a\n", "B.txt": "uppercase B\n"},
        )

        archive_path = pack_builder.build_pack(source, self.output)

        unpacked = unpack(archive_path, self.root / "unpacked")
        self.assertEqual(check_pack.check_pack(unpacked), [])
        built_manifest = json.loads((unpacked / "pack.json").read_text(encoding="utf-8"))
        file_keys = list(built_manifest["files"])
        self.assertEqual(file_keys, sorted(file_keys))
        self.assertEqual(file_keys, ["B.txt", "a.txt"])

    def test_output_folder_equal_to_the_source_is_refused(self) -> None:
        source = copy_source(
            EXAMPLES / "valid" / "gameplay-only", self.root, strip_written_fields=True
        )
        digest = tree_digest(source)

        with self.assertRaises(pack_builder.OutputExistsError):
            pack_builder.build_pack(source, source)
        # Nothing was written: no archive exists and the source is untouched.
        self.assertEqual(written_archives(source), [])
        self.assertEqual(tree_digest(source), digest)

        # main reports it through the output error path, with exit code 1.
        printed = io.StringIO()
        with redirect_stdout(printed):
            exit_code = pack_builder.main([str(source), str(source)])
        self.assertEqual(exit_code, 1)
        self.assertEqual(written_archives(source), [])
        self.assertEqual(tree_digest(source), digest)

    def test_output_folder_inside_the_source_is_refused(self) -> None:
        source = copy_source(
            EXAMPLES / "valid" / "gameplay-only", self.root, strip_written_fields=True
        )
        digest = tree_digest(source)
        output = source / "out"

        with self.assertRaises(pack_builder.OutputExistsError):
            pack_builder.build_pack(source, output)
        self.assertEqual(written_archives(source), [])
        self.assertEqual(tree_digest(source), digest)

    def test_main_refuses_when_the_default_output_is_the_source_folder(self) -> None:
        # Running the command from the source folder with no output argument used
        # to write the archive into the source.
        source = copy_source(
            EXAMPLES / "valid" / "gameplay-only", self.root, strip_written_fields=True
        )
        digest = tree_digest(source)
        previous_directory = os.getcwd()
        os.chdir(source)
        self.addCleanup(os.chdir, previous_directory)

        printed = io.StringIO()
        with redirect_stdout(printed):
            exit_code = pack_builder.main([str(source)])

        self.assertEqual(exit_code, 1)
        self.assertEqual(written_archives(source), [])
        self.assertEqual(tree_digest(source), digest)

    def test_campaign_row_with_backslash_separators_is_in_provides(self) -> None:
        # The runtime loads `campaign=campaigns\test.camp` on Windows; the builder
        # must read the same campaign file, not drop it from provides.
        source = write_source(
            self.root / "src",
            {
                "schema_version": 3,
                "game_id": "mw3",
                "id": "test-backslash-campaign",
                "name": "Backslash campaign test",
                "version": "1.0.0",
                "gameplay": {"root": "mod"},
            },
            {
                "mod/mod.txt": "name=Backslash campaign test\ncampaign=campaigns\\test.camp\n",
                "mod/campaigns/test.camp": (
                    "name=Backslash Campaign\nmission=testworld 1\nmission=testworld 2\n"
                ),
            },
        )

        archive_path = pack_builder.build_pack(source, self.output)

        unpacked = unpack(archive_path, self.root / "unpacked")
        self.assertEqual(check_pack.check_pack(unpacked), [])
        built_manifest = json.loads((unpacked / "pack.json").read_text(encoding="utf-8"))
        self.assertEqual(
            built_manifest["provides"],
            {
                "missions": ["testworld/1", "testworld/2"],
                "campaigns": ["Backslash Campaign"],
            },
        )


if __name__ == "__main__":
    unittest.main()
