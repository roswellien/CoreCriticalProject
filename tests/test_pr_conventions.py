"""Checks for tools/github/check_pr_conventions.py, the PR base, branch and title check."""

import importlib.util
import io
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_checker():
    spec = importlib.util.spec_from_file_location(
        "check_pr_conventions", ROOT / "tools/github/check_pr_conventions.py"
    )
    module = importlib.util.module_from_spec(spec)
    # Registered before running, because dataclasses look their module up in sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checker = load_checker()

GOOD_TITLE = "Fix launcher: find a standard retail install in auto-detect"
GOOD_BRANCH = "carson-nr/fix/10-setup-verify-optional-tiers"


def levels(findings):
    return [finding.level for finding in findings]


class BaseBranchTests(unittest.TestCase):
    def test_release_from_develop_is_allowed(self):
        self.assertEqual(checker.check("Release launcher 1.0.45", "develop", "main", "roswellien"), [])

    def test_topic_branch_into_main_is_an_error(self):
        findings = checker.check("Release launcher 1.0.45", "fix/x", "main", "carson-nr")
        self.assertEqual(levels(findings), ["error"])

    def test_release_title_is_only_a_warning(self):
        findings = checker.check("Promote the workflow to main", "develop", "main", "roswellien")
        self.assertEqual(levels(findings), ["warning"])

    def test_sync_from_main_is_allowed(self):
        self.assertEqual(
            checker.check("Sync main into develop after launcher 1.0.45", "main", "develop", "roswellien"), []
        )

    def test_sync_title_is_only_a_warning(self):
        self.assertEqual(levels(checker.check("Merge main", "main", "develop", "roswellien")), ["warning"])

    def test_topic_branch_into_develop_is_allowed(self):
        self.assertEqual(checker.check(GOOD_TITLE, GOOD_BRANCH, "develop", "carson-nr"), [])

    def test_stacked_pr_is_not_checked(self):
        self.assertEqual(checker.check("anything.", "whatever", "carson-nr/feature/y", "carson-nr"), [])


class BranchNameTests(unittest.TestCase):
    def assert_branch(self, head, expected_levels, author="carson-nr"):
        self.assertEqual(levels(checker.check(GOOD_TITLE, head, "develop", author)), expected_levels, head)

    def test_with_and_without_issue_number(self):
        self.assert_branch("carson-nr/fix/10-setup-verify", [])
        self.assert_branch("carson-nr/docs/github-conventions", [])

    def test_every_type_is_accepted(self):
        for branch_type in checker.BRANCH_TYPES:
            self.assert_branch(f"carson-nr/{branch_type}/x", [])

    def test_bad_branches_warn(self):
        for head in (
            "carson-nr/feat/x",  # unknown type
            "Carson-NR/fix/x",  # uppercase
            "codex/fix-torso-mode-preset",  # old tool prefix
            "fix/launcher-autodetect",  # no username
            "carson-nr/fix/x-",  # trailing hyphen
        ):
            self.assert_branch(head, ["warning"])

    def test_username_must_match_author(self):
        self.assert_branch("roswellien/fix/x", ["warning"], author="carson-nr")
        self.assert_branch("carson-nr/fix/x", [], author="Carson-NR")


class TitleTests(unittest.TestCase):
    def title_levels(self, title):
        return levels(checker.check(title, GOOD_BRANCH, "develop", "carson-nr"))

    def test_valid_titles(self):
        for title in (
            GOOD_TITLE,
            "Fix CI: MSVC truncating-cast error and clang-format 7 files",
            "Add docs: illustrated field guide for new contributors",
            "Add mod-tools: export selected terrain tiles",
            "Re-enable renderer: dynamic shadows on NVIDIA",
        ):
            self.assertEqual(self.title_levels(title), [], title)

    def test_bad_titles_warn(self):
        for title in (
            "fix launcher: lowercase verb",
            "feat: conventional commit prefix",
            "Fix the launcher without an area",
            "Fix ui: unknown area",
        ):
            self.assertEqual(self.title_levels(title), ["warning"], title)

    def test_trailing_period_warns(self):
        self.assertEqual(self.title_levels("Fix launcher: stop at the period."), ["warning"])

    def test_length_limit(self):
        prefix = "Fix launcher: "
        at_limit = prefix + "x" * (checker.MAX_TITLE_LENGTH - len(prefix))
        self.assertEqual(self.title_levels(at_limit), [])
        self.assertEqual(self.title_levels(at_limit + "x"), ["warning"])


class AreaListTests(unittest.TestCase):
    """The checker's AREAS is the one list in code; the docs and the General form must match it."""

    def test_docs_area_labels_match(self):
        text = (ROOT / "docs/github-workflow.md").read_text(encoding="utf-8")
        documented = set(re.findall(r"`area: ([a-z-]+)`", text))
        self.assertEqual(documented, set(checker.AREAS), "docs/github-workflow.md area labels differ")

    def test_general_form_areas_match(self):
        text = (ROOT / ".github/ISSUE_TEMPLATE/general.yml").read_text(encoding="utf-8")
        area_block = text.split("id: area", 1)[1]
        options = set(re.findall(r"^ +- (.+)$", area_block, flags=re.MULTILINE)) - {"docs", "Not sure"}
        self.assertEqual(options, set(checker.AREAS), "general.yml area options differ")


class IssueFormHeadingTests(unittest.TestCase):
    """The CLI heading lists in docs/github-workflow.md must match each issue form's fields, in order."""

    def form_fields(self):
        forms = {}
        for path in sorted((ROOT / ".github/ISSUE_TEMPLATE").glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            name = re.search(r"^name: (.+)$", text, flags=re.MULTILINE)
            if name is None:  # config.yml
                continue
            # Field labels sit at six spaces; checkbox option labels are deeper ("- label:").
            labels = re.findall(r"^      label: (.+)$", text, flags=re.MULTILINE)
            forms[name[1].strip()] = [label.strip().strip("\"'") for label in labels]
        return forms

    def documented_headings(self):
        text = (ROOT / "docs/github-workflow.md").read_text(encoding="utf-8")
        section = text.split("Issues filed with `gh issue create`", 1)[1].split("### Labels", 1)[0]
        bullets = re.findall(r"^- ([^:\n]+): (.*?)(?=^- |\Z)", section, flags=re.MULTILINE | re.DOTALL)
        return {form: re.findall(r"`### ([^`]+)`", body) for form, body in bullets}

    def test_headings_match_forms(self):
        forms = self.form_fields()
        self.assertEqual(len(forms), 6, sorted(forms))
        self.assertEqual(self.documented_headings(), forms)


class ReportTests(unittest.TestCase):
    # report() always gets a plain dict, never os.environ: CTest runs these tests
    # inside the CI build job, where the real GITHUB_* variables are set.

    def test_plain_output_outside_actions(self):
        out = io.StringIO()
        checker.report([checker.Finding("warning", "Title ends with a period.")], {}, out)
        self.assertEqual(out.getvalue(), "warning: Title ends with a period.\n")

    def test_workflow_command_is_escaped(self):
        out = io.StringIO()
        checker.report([checker.Finding("warning", "100%\r\n::error::injected")], {"GITHUB_ACTIONS": "true"}, out)
        self.assertEqual(out.getvalue(), "::warning title=PR conventions::100%25%0D%0A::error::injected\n")

    def test_step_summary_is_written(self):
        with tempfile.TemporaryDirectory() as folder:
            summary = Path(folder) / "summary.md"
            finding = checker.Finding("warning", "Branch '`x`' is odd.\nsecond line")
            checker.report([finding], {"GITHUB_ACTIONS": "true", "GITHUB_STEP_SUMMARY": str(summary)}, io.StringIO())
            text = summary.read_text(encoding="utf-8")
        self.assertIn("## PR conventions", text)
        self.assertIn("- **warning**: `Branch 'x' is odd. second line`", text)

    def test_exit_code(self):
        # A subprocess without GITHUB_* variables, so main() cannot reach the CI run's summary.
        env = {name: value for name, value in os.environ.items() if not name.startswith("GITHUB_")}
        script = str(ROOT / "tools/github/check_pr_conventions.py")
        common = ["--title", GOOD_TITLE, "--author", "carson-nr"]
        warning = subprocess.run(
            [sys.executable, script, *common, "--head", "fix/x", "--base", "develop"],
            env=env, capture_output=True, text=True,
        )
        self.assertEqual(warning.returncode, 0, warning.stdout + warning.stderr)
        self.assertIn("warning: Branch 'fix/x'", warning.stdout)
        self.assertIn("does not match", warning.stdout)
        error = subprocess.run(
            [sys.executable, script, *common, "--head", "fix/x", "--base", "main"],
            env=env, capture_output=True, text=True,
        )
        self.assertEqual(error.returncode, 1, error.stdout + error.stderr)
        self.assertTrue(error.stdout.startswith("error: "), error.stdout)
        clean = subprocess.run(
            [sys.executable, script, *common, "--head", GOOD_BRANCH, "--base", "develop"],
            env=env, capture_output=True, text=True,
        )
        self.assertEqual((clean.returncode, clean.stdout), (0, ""), clean.stderr)


if __name__ == "__main__":
    unittest.main()
