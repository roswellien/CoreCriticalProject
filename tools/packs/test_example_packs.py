"""The example packs agree with the pack contracts.

Run from the repository root:
    python -m unittest discover -s tools/packs -p "test_*.py"

tools/check.py runs this as the pack-contracts check.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import check_pack
import fill_file_table
import json_schema_subset

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "tests/fixtures/packs"
SCHEMAS = REPO_ROOT / "docs/packs/schemas"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class ExamplePacks(unittest.TestCase):
    def setUp(self) -> None:
        self.expected = read_json(EXAMPLES / "expected.json")

    def test_every_example_folder_is_listed(self) -> None:
        # A pack nobody listed would be an example nothing checks.
        valid_folders = sorted(path.name for path in (EXAMPLES / "valid").iterdir())
        broken_folders = sorted(path.name for path in (EXAMPLES / "broken").iterdir())
        self.assertEqual(valid_folders, sorted(self.expected["valid"]))
        self.assertEqual(broken_folders, sorted(self.expected["broken"]))

    def test_valid_packs_have_no_problems(self) -> None:
        for name in self.expected["valid"]:
            with self.subTest(pack=name):
                problems = check_pack.check_pack(EXAMPLES / "valid" / name)
                self.assertEqual([problem.line() for problem in problems], [])

    def test_each_broken_pack_breaks_only_its_own_rule(self) -> None:
        for name, entry in self.expected["broken"].items():
            with self.subTest(pack=name):
                problems = check_pack.check_pack(EXAMPLES / "broken" / name)
                found_codes = [problem.code for problem in problems]
                # A runtime-only fault must look valid here; otherwise the example
                # would be testing a pack rule under the runtime rule's name.
                found_by_pack_check = entry["found_by"] == "pack-check"
                expected_codes = [entry["code"]] if found_by_pack_check else []
                self.assertEqual(found_codes, expected_codes)

    def test_example_content_report_matches_its_schema(self) -> None:
        schema = read_json(SCHEMAS / "content-report-v1.schema.json")
        report = read_json(EXAMPLES / "example-content-report.json")
        self.assertEqual(json_schema_subset.find_violations(report, schema), [])

    def test_content_report_schema_rejects_an_unknown_severity(self) -> None:
        schema = read_json(SCHEMAS / "content-report-v1.schema.json")
        report = read_json(EXAMPLES / "example-content-report.json")
        report["sources"][1]["problems"][0]["severity"] = "fatal"
        keywords = [v.keyword for v in json_schema_subset.find_violations(report, schema)]
        self.assertEqual(keywords, ["enum"])


def base_manifest(visuals: list[dict]) -> dict:
    """A minimal valid manifest holding the given visuals; the test fills in files."""
    return {
        "schema_version": 3,
        "game_id": "mw3",
        "id": "test-pack",
        "name": "Test pack",
        "version": "1.0.0",
        "visuals": visuals,
    }


class VisualKindRules(unittest.TestCase):
    """Each contract 4 kind rule fires on a pack built in a temporary folder.

    The example packs cover one instance of each new rule; these build the other
    instances (a skin without a name, both duplicate keys) and the allowed shapes,
    so no rule can pass by accident.
    """

    def build_pack(self, manifest: dict, payloads: dict[str, bytes]) -> Path:
        folder = Path(tempfile.mkdtemp(prefix="pack-test-"))
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        for relative, content in payloads.items():
            destination = folder / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        manifest = dict(manifest)
        # Fill the files table the way fill_file_table.py fills an example pack, so
        # the pack is valid apart from the rule under test.
        manifest["files"] = fill_file_table.build_file_table(folder, {})
        (folder / "pack.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return folder

    def codes_for(self, manifest: dict, payloads: dict[str, bytes]) -> list[str]:
        problems = check_pack.check_pack(self.build_pack(manifest, payloads))
        return [problem.code for problem in problems]

    def test_kind_not_allowed_for_its_target(self) -> None:
        visuals = [
            {
                "target": "world:c1",
                "kind": "skin",
                "name": "Example Stripe",
                "files": {"textures": "visuals/stripe.bwtex"},
            }
        ]
        payloads = {"visuals/stripe.bwtex": b"placeholder textures"}
        codes = self.codes_for(base_manifest(visuals), payloads)
        self.assertEqual(codes, ["visual-kind-target-mismatch"])

    def test_required_role_absent(self) -> None:
        visuals = [
            {
                "target": "mech-model:thor",
                "kind": "model",
                "lod": 0,
                "files": {"textures": "visuals/thor.bwtex"},
            }
        ]
        payloads = {"visuals/thor.bwtex": b"placeholder textures"}
        codes = self.codes_for(base_manifest(visuals), payloads)
        self.assertEqual(codes, ["visual-role-missing"])

    def test_role_the_kind_does_not_list(self) -> None:
        visuals = [
            {
                "target": "mech-model:thor",
                "kind": "skin",
                "name": "Example Stripe",
                "files": {
                    "textures": "visuals/stripe.bwtex",
                    "mesh": "visuals/mesh.bwmesh",
                },
            }
        ]
        payloads = {
            "visuals/stripe.bwtex": b"placeholder textures",
            "visuals/mesh.bwmesh": b"placeholder mesh",
        }
        codes = self.codes_for(base_manifest(visuals), payloads)
        self.assertEqual(codes, ["visual-role-unknown"])

    def test_model_without_lod(self) -> None:
        visuals = [
            {
                "target": "mech-model:thor",
                "kind": "model",
                "files": {
                    "mesh": "visuals/close.bwmesh",
                    "textures": "visuals/thor.bwtex",
                },
            }
        ]
        payloads = {
            "visuals/close.bwmesh": b"placeholder mesh",
            "visuals/thor.bwtex": b"placeholder textures",
        }
        codes = self.codes_for(base_manifest(visuals), payloads)
        self.assertEqual(codes, ["visual-field-missing"])

    def test_skin_without_name(self) -> None:
        visuals = [
            {
                "target": "mech-model:thor",
                "kind": "skin",
                "files": {"textures": "visuals/stripe.bwtex"},
            }
        ]
        payloads = {"visuals/stripe.bwtex": b"placeholder textures"}
        codes = self.codes_for(base_manifest(visuals), payloads)
        self.assertEqual(codes, ["visual-field-missing"])

    def test_two_models_with_the_same_lod(self) -> None:
        visuals = [
            {
                "target": "mech-model:thor",
                "kind": "model",
                "lod": 0,
                "files": {
                    "mesh": "visuals/close_a.bwmesh",
                    "textures": "visuals/thor.bwtex",
                },
            },
            {
                "target": "mech-model:thor",
                "kind": "model",
                "lod": 0,
                "files": {
                    "mesh": "visuals/close_b.bwmesh",
                    "textures": "visuals/thor.bwtex",
                },
            },
        ]
        payloads = {
            "visuals/close_a.bwmesh": b"placeholder mesh a",
            "visuals/close_b.bwmesh": b"placeholder mesh b",
            "visuals/thor.bwtex": b"placeholder textures",
        }
        codes = self.codes_for(base_manifest(visuals), payloads)
        self.assertEqual(codes, ["visual-duplicate-binding"])

    def test_two_skins_with_the_same_name(self) -> None:
        visuals = [
            {
                "target": "mech-model:thor",
                "kind": "skin",
                "name": "Example Stripe",
                "files": {"textures": "visuals/stripe_a.bwtex"},
            },
            {
                "target": "mech-model:thor",
                "kind": "skin",
                "name": "Example Stripe",
                "files": {"textures": "visuals/stripe_b.bwtex"},
            },
        ]
        payloads = {
            "visuals/stripe_a.bwtex": b"placeholder textures a",
            "visuals/stripe_b.bwtex": b"placeholder textures b",
        }
        codes = self.codes_for(base_manifest(visuals), payloads)
        self.assertEqual(codes, ["visual-duplicate-binding"])

    def test_two_models_with_different_lods_are_valid(self) -> None:
        visuals = [
            {
                "target": "mech-model:thor",
                "kind": "model",
                "lod": lod,
                "files": {
                    "mesh": f"visuals/close_{lod}.bwmesh",
                    "textures": "visuals/thor.bwtex",
                },
            }
            for lod in (0, 1)
        ]
        payloads = {
            "visuals/close_0.bwmesh": b"placeholder close mesh",
            "visuals/close_1.bwmesh": b"placeholder distant mesh",
            "visuals/thor.bwtex": b"placeholder textures",
        }
        self.assertEqual(self.codes_for(base_manifest(visuals), payloads), [])

    def test_environment_on_a_world_is_valid(self) -> None:
        visuals = [
            {
                "target": "world:c1",
                "kind": "environment",
                "files": {"registry": "visuals/c1.reg"},
            }
        ]
        payloads = {"visuals/c1.reg": b"placeholder registry"}
        self.assertEqual(self.codes_for(base_manifest(visuals), payloads), [])

    def test_manifest_with_a_non_json_constant_is_invalid(self) -> None:
        visuals = [
            {
                "target": "mech-model:thor",
                "kind": "model",
                "lod": 0,
                "files": {
                    "mesh": "visuals/close.bwmesh",
                    "textures": "visuals/thor.bwtex",
                },
                # The schema does not look inside options, so a constant placed here
                # is rejected only by the JSON reader, which is the rule under test.
                # In a field the schema checks, the schema would reject it anyway.
                "options": {"value": 0},
            }
        ]
        payloads = {
            "visuals/close.bwmesh": b"placeholder mesh",
            "visuals/thor.bwtex": b"placeholder textures",
        }
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                folder = self.build_pack(base_manifest(visuals), payloads)
                manifest_path = folder / "pack.json"
                text = manifest_path.read_text(encoding="utf-8")
                self.assertIn('"value": 0', text)
                manifest_path.write_text(
                    text.replace('"value": 0', f'"value": {constant}'), encoding="utf-8"
                )
                problems = check_pack.check_pack(folder)
                self.assertEqual([problem.code for problem in problems], ["manifest-invalid"])

    def test_schema_kind_enum_matches_the_checker_table(self) -> None:
        # VISUAL_KINDS and the schema's kind enum must name the same kinds, or a
        # kind the schema accepts could crash the checker instead of being judged.
        schema = read_json(SCHEMAS / "pack-manifest-v3.schema.json")
        enum = schema["$defs"]["visual"]["properties"]["kind"]["enum"]
        self.assertEqual(sorted(enum), sorted(check_pack.VISUAL_KINDS))


class SchemaSubset(unittest.TestCase):
    def test_an_unsupported_keyword_is_refused_not_skipped(self) -> None:
        schema = {"type": "string", "format": "uri"}
        with self.assertRaises(json_schema_subset.UnsupportedSchemaError):
            json_schema_subset.find_violations("x", schema)

    def test_true_is_not_the_integer_one(self) -> None:
        violations = json_schema_subset.find_violations(True, {"const": 1})
        self.assertEqual([violation.keyword for violation in violations], ["const"])

    def test_unsafe_paths_are_refused(self) -> None:
        unsafe_paths = ["../a", "a/../b", "/a", "a\\b", "C:/a", "a/NUL.txt", "a/b.", ""]
        for path in unsafe_paths:
            with self.subTest(path=path):
                self.assertFalse(check_pack.path_is_safe(path))
        self.assertTrue(check_pack.path_is_safe("mod/zbd/dfn_example.zrd"))


if __name__ == "__main__":
    unittest.main()
