"""Checks for tools/style/check_style.py that need no style checker installed.

They cover the decisions the script makes on its own: which files are excluded, whether
the exclusion copies still agree, how each tool's exit code is read, and when a run fails.
"""

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_check_style():
    spec = importlib.util.spec_from_file_location(
        "check_style", ROOT / "tools/style/check_style.py"
    )
    module = importlib.util.module_from_spec(spec)
    # dataclasses look the module up by name while the file runs.
    sys.modules["check_style"] = module
    spec.loader.exec_module(module)
    return module


check_style = load_check_style()


class ExclusionPatternTests(unittest.TestCase):
    def test_folder_excludes_everything_below_it(self):
        self.assertEqual(
            check_style.pattern_to_pathspec("tools/m4-*/"), ":(exclude,glob)tools/m4-*/**"
        )

    def test_file_path_excludes_exactly_that_file(self):
        self.assertEqual(
            check_style.pattern_to_pathspec("games/web/three.min.js"),
            ":(exclude)games/web/three.min.js",
        )

    def test_name_pattern_applies_in_every_folder(self):
        self.assertEqual(check_style.pattern_to_pathspec("*_vert.h"), ":(exclude,glob)**/*_vert.h")

    def test_unknown_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            check_style.pattern_to_pathspec("README")

    def test_every_real_exclude_line_has_a_known_shape(self):
        patterns = check_style.read_pattern_lines(ROOT / "tools/style/exclude.txt")
        self.assertTrue(patterns)
        for pattern in patterns:
            check_style.pattern_to_pathspec(pattern)

    def test_real_exclusion_copies_match(self):
        _, drift = check_style.load_exclusions()
        self.assertEqual(drift, [])

    def test_extra_or_missing_copy_lines_are_reported(self):
        master = ["tools/m4-*/", "*_vert.h"]
        drift = check_style.find_exclusion_drift(
            master, ruff_copy=master + ["extra/"], prettier_copy=["tools/m4-*/"]
        )
        self.assertEqual(len(drift), 2)
        self.assertIn("ruff.toml has lines not in exclude.txt: extra/", drift)
        self.assertIn(".prettierignore is missing *_vert.h", drift)


class ToolOutputTests(unittest.TestCase):
    def test_every_check_reads_its_exit_codes_safely(self):
        for language_name, language in check_style.LANGUAGES.items():
            for check_name, check in language.checks.items():
                with self.subTest(language=language_name, check=check_name):
                    found = check.found_exit_code

                    def classify(exit_code, items, found=found):
                        tool_run = check_style.ToolRun(exit_code, "")
                        return check_style.classify_tool_run(tool_run, items, found)

                    self.assertEqual(classify(0, []), "clean")
                    self.assertEqual(classify(found, ["a finding"]), "findings")
                    # A "found something" code with nothing parsed is never a clean result.
                    self.assertEqual(classify(found, []), "error")
                    self.assertEqual(classify(found + 1, ["a finding"]), "error")
                    self.assertEqual(classify(check_style.TOOL_NOT_FOUND_EXIT_CODE, []), "error")

    def test_dotnet_format_uses_two_for_findings(self):
        csharp_format = check_style.LANGUAGES["csharp"].checks["format"]
        self.assertEqual(csharp_format.found_exit_code, 2)

    def test_powershell_helper_uses_one_for_findings_so_its_two_is_an_error(self):
        for check in check_style.LANGUAGES["powershell"].checks.values():
            self.assertEqual(check.found_exit_code, 1)

    def test_missing_tool_is_reported_not_raised(self):
        tool_run = check_style.run_tool(["mw34-no-such-style-tool"])
        self.assertEqual(tool_run.exit_code, check_style.TOOL_NOT_FOUND_EXIT_CODE)

    def test_parsers_read_real_tool_output(self):
        clang_output = (
            "tools/a.cpp:3:1: error: code should be clang-formatted [-Wclang-format-violations]\n"
            "#include <x.h>\n"
            "tools/a.cpp:9:2: error: code should be clang-formatted [-Wclang-format-violations]\n"
        )
        self.assertEqual(check_style.parse_clang_format(clang_output), ["tools/a.cpp"])

        ruff_format_output = (
            "tools\\b.py:16:17: unformatted: File would be reformatted\n"
            "1 file would be reformatted\n"
        )
        self.assertEqual(check_style.parse_ruff_format(ruff_format_output), ["tools\\b.py"])

        ruff_lint_output = "tools\\b.py:3:47: F401 [*] `os` imported but unused\nFound 1 error.\n"
        self.assertEqual(len(check_style.parse_ruff_lint(ruff_lint_output)), 1)


class RunOutcomeTests(unittest.TestCase):
    def result(self, enforced=False, findings=(), error=""):
        return check_style.CheckResult(
            "python", "format", enforced, files_checked=3, findings=list(findings), error=error
        )

    def test_report_only_findings_pass(self):
        results = [self.result(findings=["a.py"])]
        self.assertEqual(check_style.overall_exit_code(results), check_style.EXIT_CLEAN)

    def test_enforced_findings_fail(self):
        results = [self.result(enforced=True, findings=["a.py"])]
        self.assertEqual(check_style.overall_exit_code(results), check_style.EXIT_ENFORCED_FINDINGS)

    def test_broken_tool_fails_even_when_nothing_is_enforced(self):
        results = [self.result(error="exit code 3"), self.result(enforced=True, findings=["a"])]
        self.assertEqual(check_style.overall_exit_code(results), check_style.EXIT_TOOL_ERROR)

    def test_crashed_tool_never_counts_as_zero_findings(self):
        crashing_check = check_style.Check(
            run=lambda paths, fix: check_style.ToolRun(3, "Traceback: boom"),
            parse=lambda output: [],
            found_exit_code=1,
            can_fix=False,
        )
        result = check_style.run_check("python", "lint", crashing_check, ["a.py"])
        self.assertIn("exit code 3", result.error)
        self.assertEqual(result.findings, [])


if __name__ == "__main__":
    unittest.main()
