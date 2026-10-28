"""Checks for the agent-file tools in tools/agents: the instruction file check and the skill copy."""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools/agents"


def load_tool(name):
    # sync_skills imports check_agent_files as a sibling module, so the folder goes on the path.
    if str(TOOLS) not in sys.path:
        sys.path.insert(0, str(TOOLS))
    spec = importlib.util.spec_from_file_location(name, TOOLS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    # Registered before running, because dataclasses look their module up in sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


checker = load_tool("check_agent_files")
syncer = load_tool("sync_skills")

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


SKILL = "---\nname: core-critical-demo\ndescription: Demo skill.\n---\n\nSteps.\n"


class SyncTests(FixtureTree):
    def source(self, relative_path):
        return self.root / ".agents/skills" / relative_path

    def copy(self, relative_path):
        return self.root / ".claude/skills" / relative_path

    def write_skill(self, relative_path="core-critical-demo/SKILL.md", text=SKILL):
        self.write(f".agents/skills/{relative_path}", text)

    def make_older(self, path):
        # A whole minute back, so file systems with coarse timestamps still order the two.
        older = path.stat().st_mtime - 60
        os.utime(path, (older, older))

    def test_new_skill_is_added(self):
        self.write_skill()
        self.assertEqual(
            syncer.sync(self.root), ["added .claude/skills/core-critical-demo/SKILL.md"]
        )
        self.assertEqual(self.copy("core-critical-demo/SKILL.md").read_text(), SKILL)

    def test_changed_source_is_updated(self):
        self.write_skill()
        syncer.sync(self.root)
        self.make_older(self.copy("core-critical-demo/SKILL.md"))
        self.write_skill(text=SKILL + "More steps.\n")
        self.assertEqual(
            syncer.sync(self.root), ["updated .claude/skills/core-critical-demo/SKILL.md"]
        )
        self.assertEqual(
            self.copy("core-critical-demo/SKILL.md").read_text(), SKILL + "More steps.\n"
        )

    def test_files_and_skills_gone_from_the_source_are_removed_with_their_folders(self):
        self.write_skill()
        self.write_skill("core-critical-demo/references/old.md", "Old.\n")
        self.write_skill("core-critical-retired/SKILL.md")
        syncer.sync(self.root)
        self.source("core-critical-demo/references/old.md").unlink()
        self.source("core-critical-demo/references").rmdir()
        self.source("core-critical-retired/SKILL.md").unlink()
        self.source("core-critical-retired").rmdir()
        self.assertEqual(
            syncer.sync(self.root),
            [
                "removed .claude/skills/core-critical-demo/references/old.md",
                "removed .claude/skills/core-critical-retired/SKILL.md",
            ],
        )
        self.assertFalse(self.copy("core-critical-demo/references").exists())
        self.assertFalse(self.copy("core-critical-retired").exists())
        self.assertTrue(self.copy("core-critical-demo/SKILL.md").exists())

    def test_other_claude_files_and_unshared_skills_are_left_alone(self):
        self.write_skill()
        self.write(".claude/settings.json", "{}\n")
        self.write(".claude/skills/my-own-skill/SKILL.md", "Mine.\n")
        self.write_skill("not-shared/SKILL.md", "Skipped.\n")
        self.assertEqual(
            syncer.sync(self.root), ["added .claude/skills/core-critical-demo/SKILL.md"]
        )
        self.assertTrue((self.root / ".claude/settings.json").exists())
        self.assertTrue(self.copy("my-own-skill/SKILL.md").exists())
        self.assertFalse(self.copy("not-shared").exists())

    def test_second_run_changes_nothing(self):
        self.write_skill()
        syncer.sync(self.root)
        self.assertEqual(syncer.sync(self.root), [])

    def test_copy_edited_after_its_source_stops_without_changes(self):
        self.write_skill()
        syncer.sync(self.root)
        self.make_older(self.source("core-critical-demo/SKILL.md"))
        self.write(".claude/skills/core-critical-demo/SKILL.md", "Edited copy.\n")
        self.write_skill("core-critical-new/SKILL.md")
        with self.assertRaisesRegex(syncer.SyncStopped, "core-critical-demo/SKILL.md changed"):
            syncer.sync(self.root)
        self.assertEqual(self.copy("core-critical-demo/SKILL.md").read_text(), "Edited copy.\n")
        self.assertFalse(self.copy("core-critical-new").exists())

    def test_missing_source_stops(self):
        self.write(".claude/skills/core-critical-demo/SKILL.md", SKILL)
        with self.assertRaisesRegex(syncer.SyncStopped, "missing"):
            syncer.sync(self.root)
        self.assertTrue(self.copy("core-critical-demo/SKILL.md").exists())

    def test_linked_copy_folder_stops(self):
        self.write_skill()
        (self.root / ".claude").mkdir()
        if not link_folder(self.root / ".agents/skills", self.copy("")):
            self.skipTest("this platform can't create a folder link here")
        with self.assertRaisesRegex(syncer.SyncStopped, r"\.claude/skills is a link"):
            syncer.sync(self.root)


def link_folder(target, link):
    """Link `link` to the folder `target`; return False when the platform refuses."""
    try:
        os.symlink(target, link, target_is_directory=True)
        return True
    except OSError:
        pass
    if sys.platform != "win32":
        return False
    # Windows needs Developer Mode for symlinks, but any user can make a junction,
    # which is how a contributor would most likely link the folders by hand.
    import _winapi

    try:
        _winapi.CreateJunction(str(target), str(link))
        return True
    except OSError:
        return False


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
