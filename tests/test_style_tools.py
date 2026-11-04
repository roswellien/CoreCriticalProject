"""Checks for tools/style/check_style.py that need no style checker installed.

They cover the decisions the script makes on its own: which files are excluded, whether
the exclusion copies still agree, how each tool's exit code is read, and when a run fails.
"""

import hashlib
import importlib.util
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

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


class PreflightTests(unittest.TestCase):
    def test_stored_hash_scan_reports_identical_copy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "source.cpp"
            copy = temp_path / "copy.cpp"
            other = temp_path / "other.cpp"
            source.write_text("int x = 42;\n", encoding="utf-8")
            copy.write_text("int x = 42;\n", encoding="utf-8")
            other.write_text("int y = 99;\n", encoding="utf-8")

            hits = check_style.run_stored_hash_scan(
                ["source.cpp"], ["source.cpp", "copy.cpp", "other.cpp"], repo_root=temp_path
            )
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].holding_file, "copy.cpp")
            self.assertEqual(hits[0].target_file, "source.cpp")
            self.assertEqual(hits[0].label, "identical copy")
            self.assertIn("identical copy of source.cpp", hits[0].describe())

    def test_stored_hash_scan_reports_case_insensitive_unresolved_digest_match(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            target = temp_path / "target.py"
            manifest = temp_path / "manifest.json"
            target.write_text("print('test')\n", encoding="utf-8")
            target_digest = hashlib.sha256(target.read_bytes()).hexdigest().upper()
            manifest.write_text(f'{{"hash": "{target_digest}"}}\n', encoding="utf-8")

            hits = check_style.run_stored_hash_scan(
                ["target.py"], ["target.py", "manifest.json"], repo_root=temp_path
            )
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].holding_file, "manifest.json")
            self.assertEqual(hits[0].target_file, "target.py")
            self.assertEqual(hits[0].label, "unresolved digest match")
            self.assertIn("unresolved digest match for target.py", hits[0].describe())

    def test_stored_hash_scan_ignores_unchanged_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "a.cpp").write_text("int a = 1;\n", encoding="utf-8")
            (temp_path / "b.cpp").write_text("int a = 1;\n", encoding="utf-8")

            hits = check_style.run_stored_hash_scan([], ["a.cpp", "b.cpp"], repo_root=temp_path)
            self.assertEqual(hits, [])

    def test_text_read_search_finds_read_operations(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "fixture_template.html").write_text("<h1>Test</h1>", encoding="utf-8")
            builder = temp_path / "build.py"
            builder.write_text(
                'template = Path("fixture_template.html").read_text(encoding="utf-8")\n',
                encoding="utf-8",
            )
            ignored = temp_path / "ignored.py"
            ignored.write_text("import sys\nprint('hello')\n", encoding="utf-8")

            hits = check_style.run_text_read_search(
                ["fixture_template.html"],
                ["fixture_template.html", "build.py", "ignored.py"],
                repo_root=temp_path,
            )
            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].holding_file, "build.py")
            self.assertEqual(hits[0].target_file, "fixture_template.html")
            self.assertEqual(hits[0].line_number, 1)
            self.assertEqual(hits[0].describe(), "build.py:1: reads fixture_template.html")

    def test_text_read_search_finds_open_and_path_open_with_separate_references(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "fixture_template.html").write_text("<h1>Test</h1>", encoding="utf-8")
            builder = temp_path / "build.py"
            builder.write_text(
                'template_name = "fixture_template.html"\n'
                'with open(template_name, encoding="utf-8") as template:\n'
                "    contents = template.read()\n"
                'Path(template_name).open("rb").read()\n',
                encoding="utf-8",
            )

            hits = check_style.run_text_read_search(
                ["fixture_template.html"],
                ["fixture_template.html", "build.py"],
                repo_root=temp_path,
            )
            self.assertEqual(
                [(hit.line_number, hit.target_file) for hit in hits],
                [(1, "fixture_template.html")],
            )

    def test_text_read_search_resolves_sibling_before_ambiguous_basename(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            graphics_verify = "tools/graphics-trace/verify.py"
            vulkan_verify = "tools/vulkan-windowed/verify.py"
            caller = "tools/graphics-trace/check_controls.py"
            for path in (graphics_verify, vulkan_verify, caller):
                full_path = temp_path / path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text("# fixture\n", encoding="utf-8")
            (temp_path / caller).write_text(
                'verify_path = "verify.py"\nopen(verify_path).read()\n', encoding="utf-8"
            )

            hits = check_style.run_text_read_search(
                [graphics_verify, vulkan_verify],
                [graphics_verify, vulkan_verify, caller],
                repo_root=temp_path,
            )
            self.assertEqual(
                [(hit.line_number, hit.target_file) for hit in hits],
                [(1, graphics_verify)],
            )

    def test_text_read_search_reports_all_ambiguous_basename_targets(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            target_files = ["first/verify.py", "second/verify.py"]
            caller = "tools/check.py"
            for path in target_files + [caller]:
                full_path = temp_path / path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text("# fixture\n", encoding="utf-8")
            (temp_path / caller).write_text(
                'filename = "verify.py"\nopen(filename).read()\n', encoding="utf-8"
            )

            hits = check_style.run_text_read_search(
                target_files, target_files + [caller], repo_root=temp_path
            )
            self.assertEqual(
                [(hit.line_number, hit.target_file) for hit in hits],
                [(1, "first/verify.py"), (1, "second/verify.py")],
            )

    def test_text_read_search_reports_dynamic_suffix_inventory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            target_files = ["runtime/first.py", "runtime/second.py"]
            caller = "tools/inventory.py"
            for path in target_files + [caller]:
                full_path = temp_path / path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text("# fixture\n", encoding="utf-8")
            (temp_path / caller).write_text(
                'for path in root.rglob("*"):\n'
                "    hashlib.sha256(path.read_bytes()).hexdigest()\n",
                encoding="utf-8",
            )

            hits = check_style.run_text_read_search(
                target_files, target_files + [caller], repo_root=temp_path
            )
            self.assertEqual(
                [(hit.line_number, hit.target_file) for hit in hits],
                [(1, "runtime/first.py"), (1, "runtime/second.py")],
            )

    def test_text_read_search_finds_self_hashes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source = temp_path / "source.py"
            source.write_text(
                "import hashlib\n"
                "root = Path(__file__).resolve().parents[1]\n"
                "hashlib.sha256(Path(__file__).read_bytes()).hexdigest()\n",
                encoding="utf-8",
            )

            hits = check_style.run_text_read_search(
                ["source.py"], ["source.py"], repo_root=temp_path
            )
            self.assertEqual(
                [(hit.line_number, hit.target_file) for hit in hits],
                [(3, "source.py")],
            )

    def test_text_read_search_reads_code_files_that_are_not_utf8(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "target.py").write_text("print('test')\n", encoding="utf-8")
            # 0xD7 is a Latin-1 multiplication sign and invalid as UTF-8. The read sits
            # after it, so the hit proves the whole file was searched.
            (temp_path / "legacy.py").write_bytes(
                b"# 2 \xd7 3 table\nopen('target.py').read()\n"
            )

            hits = check_style.run_text_read_search(
                ["target.py"], ["target.py", "legacy.py"], repo_root=temp_path
            )
            self.assertEqual(
                [(hit.holding_file, hit.line_number, hit.target_file) for hit in hits],
                [("legacy.py", 2, "target.py")],
            )

    def test_scans_raise_path_specific_errors_when_files_cannot_be_read(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            target = temp_path / "target.py"
            target.write_text("print('test')\n", encoding="utf-8")
            original_read_bytes = Path.read_bytes

            def deny_manifest(path):
                if path.name == "manifest.json":
                    raise PermissionError("access denied")
                return original_read_bytes(path)

            (temp_path / "manifest.json").write_text("{}", encoding="utf-8")
            with patch.object(Path, "read_bytes", autospec=True, side_effect=deny_manifest):
                with self.assertRaisesRegex(
                    check_style.PreflightReadError, "manifest.json: access denied"
                ):
                    check_style.run_stored_hash_scan(
                        ["target.py"],
                        ["target.py", "manifest.json"],
                        repo_root=temp_path,
                    )

            (temp_path / "reader.py").write_text("open('target.py').read()\n", encoding="utf-8")
            original_read_text = Path.read_text

            def deny_reader(path, *args, **kwargs):
                if path.name == "reader.py":
                    raise PermissionError("access denied")
                return original_read_text(path, *args, **kwargs)

            with patch.object(Path, "read_text", autospec=True, side_effect=deny_reader):
                with self.assertRaisesRegex(
                    check_style.PreflightReadError, "reader.py: access denied"
                ):
                    check_style.run_text_read_search(
                        ["target.py"],
                        ["target.py", "reader.py"],
                        repo_root=temp_path,
                    )

    def test_formatter_paths_are_normalized(self):
        self.assertEqual(
            check_style.normalize_repo_path(r"tools\style\check.py"),
            "tools/style/check.py",
        )

    def test_text_read_search_ignores_non_read_code(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "header.hpp").write_text("#pragma once\n", encoding="utf-8")
            source = temp_path / "main.cpp"
            source.write_text('#include "header.hpp"\nint main() { return 0; }\n', encoding="utf-8")

            hits = check_style.run_text_read_search(
                ["header.hpp"], ["header.hpp", "main.cpp"], repo_root=temp_path
            )
            self.assertEqual(hits, [])

    def test_preflight_cli_requires_exactly_one_language(self):
        self.assertEqual(check_style.main(["--preflight"]), check_style.EXIT_TOOL_ERROR)
        self.assertEqual(
            check_style.main(["--preflight", "--language", "cpp", "--language", "python"]),
            check_style.EXIT_TOOL_ERROR,
        )
        self.assertEqual(
            check_style.main(["--preflight", "--list"]),
            check_style.EXIT_TOOL_ERROR,
        )

    def test_preflight_returns_tool_error_for_incomplete_scans(self):
        check_result = check_style.CheckResult(
            "python", "format", False, 1, findings=["target.py"]
        )
        with (
            patch.object(check_style, "read_pinned_versions", return_value={}),
            patch.object(check_style, "version_error_for", return_value=None),
            patch.object(check_style, "list_all_tracked_files", return_value=["target.py"]),
            patch.object(check_style, "list_files", return_value=["target.py"]),
            patch.object(check_style, "run_check", return_value=check_result),
            patch.object(check_style, "run_text_read_search", return_value=[]),
        ):
            for scan_name in ("run_stored_hash_scan", "run_text_read_search"):
                with self.subTest(scan=scan_name):
                    output = io.StringIO()
                    with (
                        patch.object(
                            check_style,
                            "run_stored_hash_scan",
                            return_value=[],
                        ),
                        patch.object(
                            check_style,
                            "run_text_read_search",
                            return_value=[],
                        ),
                        patch.object(
                            check_style,
                            scan_name,
                            side_effect=check_style.PreflightReadError(
                                "cannot read target.py: access denied"
                            ),
                        ),
                        redirect_stdout(output),
                    ):
                        self.assertEqual(
                            check_style.run_preflight("python", []),
                            check_style.EXIT_TOOL_ERROR,
                        )
                    self.assertIn("target.py: access denied", output.getvalue())

    def test_formatter_paths_collapse_relative_segments(self):
        self.assertEqual(
            check_style.normalize_repo_path(r"tools\style\..\check.py"),
            "tools/check.py",
        )


if __name__ == "__main__":
    unittest.main()
