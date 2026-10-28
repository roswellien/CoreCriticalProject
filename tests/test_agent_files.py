"""Checks for tools/agents/check_agent_files.py, the agent instruction file check."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_checker():
    spec = importlib.util.spec_from_file_location(
        "check_agent_files", ROOT / "tools/agents/check_agent_files.py"
    )
    module = importlib.util.module_from_spec(spec)
    # Registered before running, because dataclasses look their module up in sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checker = load_checker()

GOOD_AGENTS = (
    "# Rules\n\nFollow `docs/guide.md` and `CODE_STYLE.md`.\n\n"
    "## Where to find more\n\n- `docs/guide.md`: the guide.\n"
)
GOOD_CLAUDE = "@AGENTS.md\n\n## Claude Code\n\nFollow @CODE_STYLE.md when writing code.\n"
TRACKED = ["AGENTS.md", "CLAUDE.md", "CODE_STYLE.md", "docs/guide.md", "tools/style/check.py"]


def messages(findings, level="error"):
    return [finding.message for finding in findings if finding.level == level]


class FixtureTree(unittest.TestCase):
    """Each test writes a small repository into a temporary folder and checks it."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.write("AGENTS.md", GOOD_AGENTS)
        self.write("CLAUDE.md", GOOD_CLAUDE)

    def tearDown(self):
        self.folder.cleanup()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def check(self, tracked=TRACKED):
        return checker.check(self.root, tracked)


class PathTests(FixtureTree):
    def test_clean_tree_passes(self):
        self.assertEqual(self.check(), [])

    def test_missing_backticked_path_is_an_error(self):
        self.write("AGENTS.md", GOOD_AGENTS.replace("`CODE_STYLE.md`", "`docs/old-guide.md`"))
        self.assertEqual(
            messages(self.check()), ["AGENTS.md names `docs/old-guide.md`, which isn't tracked."]
        )

    def test_missing_import_is_an_error(self):
        self.write("CLAUDE.md", GOOD_CLAUDE.replace("@CODE_STYLE.md", "@STYLE.md"))
        self.assertEqual(
            messages(self.check()), ["CLAUDE.md imports @STYLE.md, which isn't tracked."]
        )

    def test_tracked_folder_counts_as_present(self):
        self.write("AGENTS.md", GOOD_AGENTS.replace("`CODE_STYLE.md`", "`tools/style/`"))
        self.assertEqual(self.check(), [])

    def test_folder_under_an_untracked_top_level_name_is_an_error(self):
        self.write("AGENTS.md", GOOD_AGENTS.replace("`CODE_STYLE.md`", "`toolz/style/`"))
        self.assertEqual(
            messages(self.check()), ["AGENTS.md names `toolz/style/`, which isn't tracked."]
        )

    def test_ignored_folders_pass_and_untracked_ones_still_fail(self):
        # check-ignore needs a repository, so this fixture is one.
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        self.write(".gitignore", "build/\nlocal/\n")
        named = "`build/`, `local/` and `toolz/style/`"
        self.write("AGENTS.md", GOOD_AGENTS.replace("`CODE_STYLE.md`", named))
        self.assertEqual(
            messages(self.check()), ["AGENTS.md names `toolz/style/`, which isn't tracked."]
        )

    def test_claude_file_without_the_agents_import_is_an_error(self):
        self.write("CLAUDE.md", GOOD_CLAUDE.replace("@AGENTS.md\n", "See AGENTS.md.\n"))
        self.assertEqual(
            messages(self.check()),
            ["CLAUDE.md doesn't import @AGENTS.md, so Claude Code misses every rule."],
        )

    def test_copilot_file_is_checked(self):
        self.write(".github/copilot-instructions.md", "Follow `AGENT.md`.\n")
        self.assertEqual(
            messages(self.check()),
            [".github/copilot-instructions.md names `AGENT.md`, which isn't tracked."],
        )

    def test_tokens_that_are_not_paths_are_skipped(self):
        not_paths = (
            "`origin/develop` `main` `<username>/<type>/<issue>-<topic>` "
            "`1.0.34.mw3update` `corecriticalinstaller-<version>.exe` `*.md`"
        )
        self.write("AGENTS.md", GOOD_AGENTS.replace("Follow", f"{not_paths} Follow"))
        self.assertEqual(self.check(), [])

    def test_anchor_and_quoted_import_are_reduced_to_the_path(self):
        self.write(
            "AGENTS.md",
            GOOD_AGENTS.replace("`CODE_STYLE.md`", "`docs/guide.md#names` and `@AGENTS.md`"),
        )
        self.assertEqual(self.check(), [])

    def test_missing_agents_file_is_an_error(self):
        (self.root / "AGENTS.md").unlink()
        self.assertEqual(
            messages(self.check()), ["AGENTS.md is missing; it holds every agent rule."]
        )


class SizeTests(FixtureTree):
    def agents_with_lines(self, line_count):
        # GOOD_AGENTS is 7 lines; pad the must-follow part up to `line_count`.
        padding = "Rule.\n" * (line_count - 7)
        return GOOD_AGENTS.replace("## Where", f"{padding}## Where")

    def test_151_lines_is_a_warning_only(self):
        self.write("AGENTS.md", self.agents_with_lines(151))
        findings = self.check()
        self.assertEqual(messages(findings), [])
        self.assertEqual(len(messages(findings, "warning")), 1)
        self.assertIn("151 lines", messages(findings, "warning")[0])

    def test_150_lines_passes(self):
        self.write("AGENTS.md", self.agents_with_lines(150))
        self.assertEqual(self.check(), [])

    def test_201_lines_is_an_error(self):
        self.write("AGENTS.md", self.agents_with_lines(201))
        errors = messages(self.check())
        self.assertEqual(len(errors), 1)
        self.assertIn("201 lines", errors[0])

    def test_missing_end_heading_is_an_error(self):
        self.write("AGENTS.md", GOOD_AGENTS.replace("## Where to find more", "## More"))
        errors = messages(self.check())
        self.assertEqual(len(errors), 1)
        self.assertIn("needs a", errors[0])

    def test_must_follow_part_over_4000_characters_is_an_error(self):
        heading = "# Rules\n"
        filler = "x" * (4001 - len(heading) - 1) + "\n"
        self.write("AGENTS.md", f"{heading}{filler}## Where to find more\n")
        errors = messages(self.check())
        self.assertEqual(len(errors), 1)
        self.assertIn("4001 characters", errors[0])

    def test_must_follow_part_of_exactly_4000_characters_passes(self):
        heading = "# Rules\n"
        filler = "x" * (4000 - len(heading) - 1) + "\n"
        self.write("AGENTS.md", f"{heading}{filler}## Where to find more\n")
        self.assertEqual(self.check(), [])

    def test_commands_heading_also_ends_the_must_follow_part(self):
        text = "# Rules\n\nRule.\n\n## Commands and layout\n\n" + "y" * 5000 + "\n"
        self.assertEqual(checker.must_follow_length(text), len("# Rules\n\nRule.\n\n"))


class RepositoryTests(unittest.TestCase):
    """The real agent files in this checkout pass the check."""

    def test_repository_agent_files_pass(self):
        try:
            tracked_paths = checker.tracked_paths_from_git(ROOT)
        except checker.GitUnavailable as reason:
            self.fail(f"can't list tracked files: {reason}")
        errors = messages(checker.check(ROOT, tracked_paths))
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
