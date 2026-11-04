"""Checks for tools/check.py that run no real build, test or formatter.

The process runner and tool lookups are replaced at the module boundary, so these cover
only the decisions the script makes on its own: which checks run, how each result is
reported, when a check counts as not run, and which exit code a run ends with.
"""

import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_check_command():
    spec = importlib.util.spec_from_file_location("check_command", ROOT / "tools/check.py")
    module = importlib.util.module_from_spec(spec)
    # dataclasses look the module up by name while the file runs.
    sys.modules["check_command"] = module
    spec.loader.exec_module(module)
    return module


check = load_check_command()
PASS, FAIL, NOT_RUN = check.PASS, check.FAIL, check.NOT_RUN


def results(*statuses):
    return [check.Result(f"check{index}", status, "why") for index, status in enumerate(statuses)]


class ExitCodeTests(unittest.TestCase):
    def test_exit_code_for_each_mix_of_results(self):
        cases = [
            ((PASS, PASS), check.EXIT_CLEAN),
            ((PASS, FAIL), check.EXIT_FAILED),
            ((PASS, NOT_RUN), check.EXIT_NOT_RUN),
            # A check that didn't run wins over a failure, as in check_style.py.
            ((FAIL, NOT_RUN), check.EXIT_NOT_RUN),
        ]
        for statuses, expected in cases:
            with self.subTest(statuses=statuses):
                self.assertEqual(check.overall_exit_code(results(*statuses)), expected)


class SummaryLineTests(unittest.TestCase):
    def test_summary_line_for_each_status(self):
        cases = [
            (check.Result("build", PASS), "build: pass"),
            (check.Result("ctest", FAIL), "ctest: fail"),
            (
                check.Result("ctest", FAIL, "skipped because the build failed"),
                "ctest: fail (skipped because the build failed)",
            ),
            (
                check.Result("style", NOT_RUN, "ruff missing; run setup"),
                "style: not run (ruff missing; run setup)",
            ),
        ]
        for result, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(result.summary_line(), expected)


class SelectionTests(unittest.TestCase):
    def names(self, only=None, areas=None, windows=True):
        with patch.object(check, "is_windows", return_value=windows):
            return [item.name for item in check.selected_checks(only, areas)]

    def test_default_run_is_the_ci_checks_in_order(self):
        self.assertEqual(self.names(), ["build", "ctest", "format-check", "style"])

    def test_only_keeps_table_order(self):
        self.assertEqual(self.names(only=["style", "build"]), ["build", "style"])

    def test_launcher_area_adds_both_launcher_checks(self):
        expected = ["build", "ctest", "format-check", "style", "launcher-wpf", "launcher-dispatch"]
        self.assertEqual(self.names(areas=["launcher"]), expected)

    def test_windows_only_check_elsewhere_is_not_run_and_exits_2(self):
        with (
            patch.object(check, "is_windows", return_value=False),
            patch.object(check, "run_command", return_value=0) as runner,
            redirect_stdout(io.StringIO()) as output,
        ):
            exit_code = check.main(["--only", "launcher-wpf"])
        self.assertEqual(exit_code, check.EXIT_NOT_RUN)
        self.assertIn("launcher-wpf: not run (Windows only", output.getvalue())
        runner.assert_not_called()

    def test_unknown_only_name_is_an_argument_error(self):
        with (
            redirect_stdout(io.StringIO()),
            patch("sys.stderr", io.StringIO()),
            self.assertRaises(SystemExit) as raised,
        ):
            check.parse_arguments(["--only", "lint"])
        self.assertEqual(raised.exception.code, 2)

    def test_setup_installs_only_what_the_selected_checks_need(self):
        cases = [
            (["build", "ctest"], []),
            (["format-check"], ["venv"]),
            (["style"], ["venv", "npm", "psscriptanalyzer"]),
            (["launcher-wpf"], ["sdl3"]),
        ]
        for only, expected in cases:
            with self.subTest(only=only):
                with patch.object(check, "is_windows", return_value=True):
                    selected = check.selected_checks(only, None)
                self.assertEqual(check.setup_steps_for(selected), expected)


class NotRunTests(unittest.TestCase):
    """A check whose tool or input is missing reports not run and never runs or passes."""

    def run_quietly(self, function, earlier=None):
        with (
            patch.object(check, "run_command", return_value=0) as runner,
            redirect_stdout(io.StringIO()),
        ):
            result = function(earlier or {})
        return result, runner

    def test_ctest_follows_the_build_in_the_same_run(self):
        cases = [(FAIL, FAIL), (NOT_RUN, NOT_RUN)]
        for build_status, expected in cases:
            with self.subTest(build_status=build_status):
                earlier = {"build": check.Result("build", build_status, "why")}
                result, runner = self.run_quietly(check.check_ctest, earlier)
                self.assertEqual(result.status, expected)
                runner.assert_not_called()

    def test_format_check_reuses_a_passing_build_configure(self):
        earlier = {"build": check.Result("build", PASS)}
        with (
            patch.object(check, "pinned_clang_format", return_value="/venv/clang-format"),
            patch.object(check, "configure_problem", return_value=""),
        ):
            result, runner = self.run_quietly(check.check_format, earlier)
        self.assertEqual(result.status, PASS)
        commands = [call.args[0] for call in runner.call_args_list]
        format_target = ["cmake", "--build", str(check.BUILD_DIR), "--target", "format-check"]
        self.assertEqual(commands, [format_target])

    def test_format_check_ignores_a_clang_format_on_path(self):
        with (
            patch.object(check, "pinned_clang_format", return_value=None),
            patch.object(check, "find_on_path", return_value="/usr/bin/clang-format"),
        ):
            result, runner = self.run_quietly(check.check_format)
        self.assertEqual(result.status, NOT_RUN)
        runner.assert_not_called()

    def test_build_without_visual_studio_is_not_run(self):
        with (
            patch.object(check, "is_windows", return_value=True),
            patch.object(check, "find_on_path", return_value="cmake"),
            patch.object(check, "visual_studio_found", return_value=False),
        ):
            result, runner = self.run_quietly(check.check_build)
        self.assertEqual(result.status, NOT_RUN)
        self.assertIn("Visual Studio", result.detail)
        runner.assert_not_called()

    def test_ctest_without_a_build_is_not_run(self):
        with (
            patch.object(check, "find_on_path", return_value="ctest"),
            patch.object(check, "BUILD_DIR", ROOT / "no-such-build-folder"),
        ):
            result, runner = self.run_quietly(check.check_ctest)
        self.assertEqual(result.status, NOT_RUN)
        runner.assert_not_called()

    def test_launcher_wpf_without_sdl3_is_not_run(self):
        with (
            patch.object(check, "find_on_path", return_value="dotnet"),
            patch.object(check, "sdl3_runtime_found", return_value=False),
        ):
            result, runner = self.run_quietly(check.check_launcher_wpf)
        self.assertEqual(result.status, NOT_RUN)
        self.assertIn("--area launcher", result.detail)
        runner.assert_not_called()

    def test_style_exit_codes(self):
        cases = [(0, PASS), (1, FAIL), (2, NOT_RUN)]
        for exit_code, expected in cases:
            with (
                self.subTest(exit_code=exit_code),
                patch.object(check, "run_command", return_value=exit_code),
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(check.check_style({}).status, expected)


class ConfigureTests(unittest.TestCase):
    def test_configure_options_per_os(self):
        cases = [
            (True, None, ["cmake", "--preset", "default", "-A", "x64"]),
            (
                False,
                "/venv/clang-format",
                [
                    "cmake",
                    "--preset",
                    "default",
                    "-DCMAKE_CXX_COMPILER=clang++",
                    "-DMW34_CLANG_FORMAT=/venv/clang-format",
                ],
            ),
        ]
        for windows, clang_format, expected in cases:
            with (
                self.subTest(windows=windows),
                patch.object(check, "is_windows", return_value=windows),
            ):
                self.assertEqual(check.configure_command(clang_format), expected)


if __name__ == "__main__":
    unittest.main()
