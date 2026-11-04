"""Checks for the tools in tools/agents: the instruction file check, the skill copy and the git hooks."""

import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
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
hooks = load_tool("git_hooks")

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

    def test_outer_repository_ignore_rules_are_not_used(self):
        # The checked folder sits inside another repository's ignored build/ folder,
        # whose rules would otherwise excuse every path named here.
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        self.write(".gitignore", "build/\n")
        inner = self.root / "build/inner"
        inner.mkdir(parents=True)
        (inner / "AGENTS.md").write_text(
            GOOD_AGENTS.replace("`CODE_STYLE.md`", "`toolz/style/`"), encoding="utf-8"
        )
        self.assertEqual(
            messages(checker.check(inner, TRACKED)),
            ["AGENTS.md names `toolz/style/`, which isn't tracked."],
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
            syncer.sync(self.root, []), ["added .claude/skills/core-critical-demo/SKILL.md"]
        )
        self.assertEqual(self.copy("core-critical-demo/SKILL.md").read_text(), SKILL)

    def test_changed_source_is_updated(self):
        self.write_skill()
        syncer.sync(self.root, [])
        self.make_older(self.copy("core-critical-demo/SKILL.md"))
        self.write_skill(text=SKILL + "More steps.\n")
        self.assertEqual(
            syncer.sync(self.root, []), ["updated .claude/skills/core-critical-demo/SKILL.md"]
        )
        self.assertEqual(
            self.copy("core-critical-demo/SKILL.md").read_text(), SKILL + "More steps.\n"
        )

    def test_files_and_skills_gone_from_the_source_are_removed_with_their_folders(self):
        self.write_skill()
        self.write_skill("core-critical-demo/references/old.md", "Old.\n")
        self.write_skill("core-critical-retired/SKILL.md")
        syncer.sync(self.root, [])
        self.source("core-critical-demo/references/old.md").unlink()
        self.source("core-critical-demo/references").rmdir()
        self.source("core-critical-retired/SKILL.md").unlink()
        self.source("core-critical-retired").rmdir()
        tracked = [
            ".claude/skills/core-critical-demo/references/old.md",
            ".claude/skills/core-critical-retired/SKILL.md",
        ]
        self.assertEqual(
            syncer.sync(self.root, tracked),
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
            syncer.sync(self.root, []), ["added .claude/skills/core-critical-demo/SKILL.md"]
        )
        self.assertTrue((self.root / ".claude/settings.json").exists())
        self.assertTrue(self.copy("my-own-skill/SKILL.md").exists())
        self.assertFalse(self.copy("not-shared").exists())

    def test_second_run_changes_nothing(self):
        self.write_skill()
        syncer.sync(self.root, [])
        self.assertEqual(syncer.sync(self.root, []), [])

    def test_copy_edited_after_its_source_stops_without_changes(self):
        self.write_skill()
        syncer.sync(self.root, [])
        self.make_older(self.source("core-critical-demo/SKILL.md"))
        self.write(".claude/skills/core-critical-demo/SKILL.md", "Edited copy.\n")
        self.write_skill("core-critical-new/SKILL.md")
        with self.assertRaisesRegex(syncer.SyncStopped, "core-critical-demo/SKILL.md changed"):
            syncer.sync(self.root, [])
        self.assertEqual(self.copy("core-critical-demo/SKILL.md").read_text(), "Edited copy.\n")
        self.assertFalse(self.copy("core-critical-new").exists())

    def test_untracked_copy_with_no_source_stops_without_changes(self):
        # Claude Code writes a new skill straight into the copy; removing it would lose it.
        self.write_skill()
        self.write(".claude/skills/core-critical-new/SKILL.md", "New skill.\n")
        with self.assertRaisesRegex(syncer.SyncStopped, "core-critical-new/SKILL.md has no source"):
            syncer.sync(self.root, [])
        self.assertTrue(self.copy("core-critical-new/SKILL.md").exists())
        self.assertFalse(self.copy("core-critical-demo").exists())

    def test_missing_source_stops(self):
        self.write(".claude/skills/core-critical-demo/SKILL.md", SKILL)
        with self.assertRaisesRegex(syncer.SyncStopped, "missing"):
            syncer.sync(self.root, [])
        self.assertTrue(self.copy("core-critical-demo/SKILL.md").exists())

    def test_linked_copy_folder_stops(self):
        self.write_skill()
        (self.root / ".claude").mkdir()
        if not link_folder(self.root / ".agents/skills", self.copy("")):
            self.skipTest("this platform can't create a folder link here")
        with self.assertRaisesRegex(syncer.SyncStopped, r"\.claude/skills is a link"):
            syncer.sync(self.root, [])

    def test_linked_claude_folder_stops(self):
        self.write_skill()
        self.write("elsewhere/skills/README.md", "Not ours.\n")
        if not link_folder(self.root / "elsewhere", self.root / ".claude"):
            self.skipTest("this platform can't create a folder link here")
        with self.assertRaisesRegex(syncer.SyncStopped, r"\.claude/skills is a link"):
            syncer.sync(self.root, [])

    def test_linked_source_skill_stops_without_changes(self):
        self.write("elsewhere/SKILL.md", SKILL)
        (self.root / ".agents/skills").mkdir(parents=True)
        if not link_folder(self.root / "elsewhere", self.source("core-critical-demo")):
            self.skipTest("this platform can't create a folder link here")
        with self.assertRaisesRegex(syncer.SyncStopped, r"core-critical-demo is a link"):
            syncer.sync(self.root, [])
        self.assertFalse(self.copy("core-critical-demo").exists())


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


class SkillTests(FixtureTree):
    def add_skill(self, folder="core-critical-demo", files=None):
        """Write a skill to both folders, as sync_skills would, and return the tracked list."""
        files = files or {"SKILL.md": SKILL.replace("core-critical-demo", folder)}
        tracked = list(TRACKED)
        for relative_path, text in files.items():
            for skills_folder in (".agents/skills", ".claude/skills"):
                path = f"{skills_folder}/{folder}/{relative_path}"
                self.write(path, text)
                tracked.append(path)
        return tracked

    def errors_for_skill_md(self, text, folder="core-critical-demo"):
        return messages(self.check(self.add_skill(folder, {"SKILL.md": text})))

    def test_clean_skill_passes(self):
        self.assertEqual(self.check(self.add_skill()), [])

    def test_no_skills_at_all_passes(self):
        self.assertEqual(self.check(), [])

    def test_byte_difference_is_an_error(self):
        tracked = self.add_skill()
        self.write(".claude/skills/core-critical-demo/SKILL.md", SKILL + "Edited.\n")
        self.assertEqual(
            messages(self.check(tracked)),
            [
                (
                    ".claude/skills/core-critical-demo/SKILL.md differs from "
                    ".agents/skills/core-critical-demo/SKILL.md; "
                    f"{checker.SYNC_ADVICE}."
                )
            ],
        )

    def test_file_missing_from_the_copy_is_an_error(self):
        tracked = self.add_skill()
        tracked.remove(".claude/skills/core-critical-demo/SKILL.md")
        errors = messages(self.check(tracked))
        self.assertEqual(len(errors), 1)
        self.assertIn("SKILL.md has no copy in .claude/skills/", errors[0])

    def test_extra_file_in_the_copy_is_an_error(self):
        tracked = self.add_skill()
        self.write(".claude/skills/core-critical-demo/notes.md", "Extra.\n")
        tracked.append(".claude/skills/core-critical-demo/notes.md")
        errors = messages(self.check(tracked))
        self.assertEqual(len(errors), 1)
        self.assertIn("notes.md has no source in .agents/skills/", errors[0])

    def test_tracked_personal_skill_in_the_copy_is_an_error(self):
        tracked = self.add_skill()
        self.write(".claude/skills/my-own-skill/SKILL.md", "Mine.\n")
        tracked.append(".claude/skills/my-own-skill/SKILL.md")
        errors = messages(self.check(tracked))
        self.assertEqual(len(errors), 1)
        self.assertIn("isn't a shared skill", errors[0])

    def test_tracked_file_deleted_from_disk_is_a_difference(self):
        tracked = self.add_skill()
        (self.root / ".claude/skills/core-critical-demo/SKILL.md").unlink()
        errors = messages(self.check(tracked))
        self.assertEqual(len(errors), 1)
        self.assertIn("differs from", errors[0])

    def test_copy_with_no_source_is_an_error(self):
        self.write(".claude/skills/core-critical-demo/SKILL.md", SKILL)
        tracked = [*TRACKED, ".claude/skills/core-critical-demo/SKILL.md"]
        errors = messages(self.check(tracked))
        self.assertEqual(len(errors), 1)
        self.assertIn("has no source", errors[0])

    def test_file_directly_in_the_skills_folder_is_an_error(self):
        self.write(".agents/skills/README.md", "Skills.\n")
        errors = messages(self.check([*TRACKED, ".agents/skills/README.md"]))
        self.assertEqual(len(errors), 1)
        self.assertIn("sits directly in .agents/skills/", errors[0])

    def test_missing_skill_md_is_an_error(self):
        tracked = self.add_skill(files={"notes.md": "Notes.\n"})
        self.assertEqual(
            messages(self.check(tracked)), [".agents/skills/core-critical-demo/ has no SKILL.md."]
        )

    def test_missing_frontmatter_is_an_error(self):
        errors = self.errors_for_skill_md("# Demo\n\nSteps.\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("must start with a `---` frontmatter line", errors[0])

    def test_unclosed_frontmatter_is_an_error(self):
        errors = self.errors_for_skill_md("---\nname: core-critical-demo\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("no closing", errors[0])

    def test_name_not_matching_its_folder_is_an_error(self):
        errors = self.errors_for_skill_md(
            SKILL.replace("name: core-critical-demo", "name: core-critical-other")
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("must match its folder", errors[0])

    def test_badly_formed_names_are_errors(self):
        for folder in ("core-critical-Demo", "core-critical--demo"):
            with self.subTest(folder=folder):
                errors = self.errors_for_skill_md(
                    SKILL.replace("core-critical-demo", folder), folder
                )
                self.assertEqual(len(errors), 1)
                self.assertIn("lowercase letters, digits and single hyphens", errors[0])

    def test_name_without_the_prefix_is_an_error(self):
        # sync_skills skips such a folder, so only the source holds it.
        self.write(".agents/skills/demo/SKILL.md", SKILL.replace("core-critical-demo", "demo"))
        errors = messages(self.check([*TRACKED, ".agents/skills/demo/SKILL.md"]))
        self.assertEqual(len(errors), 1)
        self.assertIn("must start `core-critical-`", errors[0])

    def test_name_of_65_characters_is_an_error(self):
        folder = "core-critical-" + "a" * 51
        errors = self.errors_for_skill_md(SKILL.replace("core-critical-demo", folder), folder)
        self.assertEqual(len(errors), 1)
        self.assertIn("65 characters, over 64", errors[0])

    def test_description_length_limits(self):
        for description, length in (('""', 0), ("d" * 1025, 1025)):
            with self.subTest(length=length):
                errors = self.errors_for_skill_md(SKILL.replace("Demo skill.", description))
                self.assertEqual(len(errors), 1)
                self.assertIn(f"is {length} characters", errors[0])

    def test_values_yaml_would_misread_are_errors(self):
        cases = (
            ("description: >\n  Folded.", "is a `>` or `|` block"),
            ("description: Run checks: then report.", "needs quotes"),
            ("description: `tool` first.", "needs quotes"),
            ("description: # Heading", "needs quotes"),
            ("description: - item", "needs quotes"),
            ("description: ? key", "needs quotes"),
            ("description: , then", "needs quotes"),
            ("description: Ends in a colon:", "needs quotes"),
            ("description: Tab:\tafter", "needs quotes"),
            ('description: "Run" checks', "opens a quote that isn't closed"),
            ("description: Wrapped\n  onto a second line.", "continues onto another line"),
            ("description: Demo skill.\npaths: *.py", "`paths` needs quotes"),
            ("description: Demo skill.\npaths:\n  - *.py", "`paths` entry `*.py` needs quotes"),
            ("description: Demo skill.\npaths:\n  tools/", "`paths` lines must each be"),
        )
        for line, expected in cases:
            with self.subTest(line=line):
                errors = self.errors_for_skill_md(SKILL.replace("description: Demo skill.", line))
                self.assertEqual(len(errors), 1)
                self.assertIn(expected, errors[0])

    def test_unknown_key_is_an_error(self):
        errors = self.errors_for_skill_md(SKILL.replace("---\n\n", "allowed-tools: Bash\n---\n\n"))
        self.assertEqual(len(errors), 1)
        self.assertIn("frontmatter key `allowed-tools`", errors[0])

    def test_disable_model_invocation_must_be_true_or_false(self):
        errors = self.errors_for_skill_md(
            SKILL.replace("---\n\n", "disable-model-invocation: maybe\n---\n\n")
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("must be true or false", errors[0])

    def test_openai_settings_beyond_the_policy_are_an_error(self):
        settings = "policy:\n  allow_implicit_invocation: false\ninterface:\n  display_name: Demo\n"
        tracked = self.add_skill(files={"SKILL.md": SKILL, "agents/openai.yaml": settings})
        errors = messages(self.check(tracked))
        self.assertEqual(len(errors), 1)
        self.assertIn("agents/openai.yaml may hold only", errors[0])

    def test_missing_backticked_path_in_a_skill_is_an_error(self):
        errors = self.errors_for_skill_md(SKILL + "Read `docs/missing.md`.\n")
        self.assertEqual(
            errors,
            [
                (
                    ".agents/skills/core-critical-demo/SKILL.md names `docs/missing.md`, "
                    "which isn't tracked."
                )
            ],
        )

    def test_linked_skill_file_is_an_error(self):
        tracked = self.add_skill(files={"SKILL.md": SKILL, "notes.md": "Notes.\n"})
        source_notes = self.root / ".agents/skills/core-critical-demo/notes.md"
        source_notes.unlink()
        try:
            os.symlink(self.root / "CLAUDE.md", source_notes)
        except OSError:
            self.skipTest("this platform can't create a file link here")
        self.write(".claude/skills/core-critical-demo/notes.md", GOOD_CLAUDE)
        self.assertEqual(
            messages(self.check(tracked)),
            [".agents/skills/core-critical-demo/notes.md is a link; commit a real file instead."],
        )

    def test_valid_variations_pass(self):
        variations = {
            "a valid openai.yaml": {
                "SKILL.md": SKILL,
                "agents/openai.yaml": "# Codex\npolicy:\n  allow_implicit_invocation: false\n",
            },
            "a paths list": {
                "SKILL.md": SKILL.replace("---\n\n", "paths:\n  - tools/**\n---\n\n"),
            },
            "a quoted description holding ': '": {
                "SKILL.md": SKILL.replace("Demo skill.", '"Run checks: then report."'),
            },
            "a path relative to the skill folder": {
                "SKILL.md": SKILL + "Use `references/checklist.md` and `docs/guide.md`.\n",
                "references/checklist.md": "Checklist.\n",
            },
        }
        for variation, files in variations.items():
            with self.subTest(variation=variation):
                self.assertEqual(self.check(self.add_skill(files=files)), [])


class RepositoryTests(unittest.TestCase):
    """The real agent files in this checkout pass the check."""

    def test_repository_agent_files_pass(self):
        try:
            tracked_paths = checker.tracked_paths_from_git(ROOT)
        except checker.GitUnavailable as reason:
            self.fail(f"can't list tracked files: {reason}")
        errors = messages(checker.check(ROOT, tracked_paths))
        self.assertEqual(errors, [])


class GitHookTests(unittest.TestCase):
    """The pre-commit and pre-push hooks, on throwaway git repositories.

    A stand-in formatter rewrites each file it is given to FORMATTED, and a stand-in
    agent check passes unless a test says otherwise, so no real formatter is needed.
    """

    FORMATTED = "formatted\n"

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        # Drop git variables from an outer hook or worktree so git only sees this repository.
        self.environment = {
            key: value for key, value in os.environ.items() if not key.startswith("GIT_")
        }
        self.git("init", "-q")
        self.git("config", "user.name", "Hook test")
        self.git("config", "user.email", "hook-test@example.invalid")
        # Same bytes on the Windows runner as on Linux.
        self.git("config", "core.autocrlf", "false")
        self.write(".gitignore", "*.zbd\n")
        self.git("add", ".gitignore")
        self.git("commit", "-q", "-m", "start")
        self.formatter_calls = []
        self.formatter_exit_code = 0
        self.formatter_output = "web format: formatted 1 files\n"
        self.agent_check_exit_code = 0

    def git(self, *arguments, environment=None):
        result = subprocess.run(
            ["git", *arguments],
            cwd=self.root,
            env=environment or self.environment,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as file:
            file.write(text)

    def formatter(self, root, paths, environment):
        self.formatter_calls.append(list(paths))
        if self.formatter_exit_code == 0:
            for path in paths:
                with open(root / path, "w", encoding="utf-8", newline="\n") as file:
                    file.write(self.FORMATTED)
        return subprocess.CompletedProcess([], self.formatter_exit_code, self.formatter_output, "")

    def agent_check(self, root, environment):
        return subprocess.CompletedProcess([], self.agent_check_exit_code, "error: a problem\n", "")

    def pre_commit(self, environment=None):
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = hooks.pre_commit(
                self.root, environment or self.environment, self.formatter, self.agent_check
            )
        return exit_code, output.getvalue()

    def staged_text(self, name):
        return self.git("show", f":{name}")

    def test_fully_staged_file_is_formatted_and_staged(self):
        self.write("site/a.js", "messy\n")
        self.git("add", "site/a.js")
        exit_code, _ = self.pre_commit()
        self.assertEqual(exit_code, 0)
        self.assertEqual(self.formatter_calls, [["site/a.js"]])
        self.assertEqual(self.staged_text("site/a.js"), self.FORMATTED)
        self.assertEqual(self.git("diff", "--name-only"), "")

    def test_partly_staged_file_is_left_alone_with_a_note(self):
        self.write("a.js", "one\n")
        self.git("add", "a.js")
        self.git("commit", "-q", "-m", "a")
        self.write("a.js", "two\n")
        self.git("add", "a.js")
        self.write("a.js", "three\n")
        exit_code, output = self.pre_commit()
        self.assertEqual(exit_code, 0)
        self.assertEqual(self.formatter_calls, [])
        self.assertIn("only part of its changes are staged: a.js", output)
        self.assertEqual(self.staged_text("a.js"), "two\n")
        self.assertEqual(self.git("diff", "--name-only").strip(), "a.js")

    def test_ignored_file_blocks_the_commit(self):
        self.write("test.zbd", "game data\n")
        self.git("add", "-f", "test.zbd")
        exit_code, output = self.pre_commit()
        self.assertEqual(exit_code, 1)
        self.assertIn("test.zbd (rule '*.zbd'", output)
        self.assertEqual(self.formatter_calls, [])

    def test_failing_formatter_lets_the_commit_through_with_install_advice(self):
        self.formatter_exit_code = 2
        self.formatter_output = "web format: error: prettier is not installed\n"
        self.write("a.js", "messy\n")
        self.git("add", "a.js")
        exit_code, output = self.pre_commit()
        self.assertEqual(exit_code, 0)
        self.assertIn("the commit goes ahead", output)
        self.assertIn("npm ci --prefix tools/style", output)
        self.assertEqual(self.staged_text("a.js"), "messy\n")

    def test_failing_agent_check_blocks_the_commit(self):
        self.agent_check_exit_code = 1
        self.write("AGENTS.md", "# Rules\n")
        self.git("add", "AGENTS.md")
        exit_code, output = self.pre_commit()
        self.assertEqual(exit_code, 1)
        self.assertIn("error: a problem", output)

    def test_deleted_file_is_not_passed_to_the_formatter(self):
        self.write("b.js", "old\n")
        self.git("add", "b.js")
        self.git("commit", "-q", "-m", "b")
        self.git("rm", "-q", "b.js")
        self.write("c.js", "new\n")
        self.git("add", "c.js")
        self.pre_commit()
        self.assertEqual(self.formatter_calls, [["c.js"]])

    def test_large_commit_is_formatted_in_batches(self):
        names = [f"files/f{number:03}.js" for number in range(150)]
        for name in names:
            self.write(name, "messy\n")
        self.git("add", "files")
        exit_code, _ = self.pre_commit()
        self.assertEqual(exit_code, 0)
        self.assertEqual([len(call) for call in self.formatter_calls], [100, 50])
        self.assertEqual(self.git("diff", "--name-only"), "")
        self.assertEqual(self.staged_text(names[-1]), self.FORMATTED)

    def index_environment(self, index_name):
        """Point GIT_INDEX_FILE at a copy of the index, as git does for each kind of commit."""
        git_folder = Path(self.git("rev-parse", "--absolute-git-dir").strip())
        index_copy = git_folder / index_name
        if index_name != "index":
            index_copy.write_bytes((git_folder / "index").read_bytes())
            self.addCleanup(index_copy.unlink, missing_ok=True)
        return {**self.environment, "GIT_INDEX_FILE": str(index_copy)}

    def test_commit_of_named_paths_is_not_formatted(self):
        self.write("a.js", "messy\n")
        self.git("add", "a.js")
        # A copy, so the staged file is still seen; an empty index would pass for the wrong reason.
        exit_code, output = self.pre_commit(self.index_environment("next-index-1.lock"))
        self.assertEqual(exit_code, 0)
        self.assertEqual(self.formatter_calls, [])
        self.assertIn("temporary index", output)

    def test_plain_commit_and_commit_all_indexes_are_formatted(self):
        self.write("a.js", "messy\n")
        self.git("add", "a.js")
        for index_name in ("index", "index.lock"):
            with self.subTest(index=index_name):
                self.formatter_calls = []
                self.pre_commit(self.index_environment(index_name))
                self.assertEqual(self.formatter_calls, [["a.js"]])

    def test_relative_index_path_counts_as_the_real_index(self):
        self.write("a.js", "messy\n")
        self.git("add", "a.js")
        self.pre_commit({**self.environment, "GIT_INDEX_FILE": ".git/index"})
        self.assertEqual(self.formatter_calls, [["a.js"]])

    def test_nothing_staged_passes_without_running_anything(self):
        self.agent_check_exit_code = 1
        exit_code, _ = self.pre_commit()
        self.assertEqual(exit_code, 0)
        self.assertEqual(self.formatter_calls, [])

    def test_push_to_main_or_develop_is_blocked(self):
        for branch in ("main", "develop"):
            with self.subTest(branch=branch):
                line = f"refs/heads/topic abc123 refs/heads/{branch} def456\n"
                with redirect_stdout(io.StringIO()):
                    self.assertEqual(hooks.pre_push(line), 1)

    def test_push_to_a_topic_branch_passes(self):
        line = "refs/heads/topic abc123 refs/heads/carson-nr/ci/x def456\n"
        self.assertEqual(hooks.pre_push(line), 0)


if __name__ == "__main__":
    unittest.main()
