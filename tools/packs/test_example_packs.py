"""The example packs agree with the pack contracts.

Run from the repository root:
    python -m unittest discover -s tools/packs -p "test_*.py"

tools/check.py runs this as the pack-contracts check.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import check_pack
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
