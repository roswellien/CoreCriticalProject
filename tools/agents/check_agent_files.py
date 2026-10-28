"""Check the agent instruction files for missing paths and for size.

`AGENTS.md` is the single source of agent rules; `CLAUDE.md` and
`.github/copilot-instructions.md` only point to it. This check keeps the three
files trustworthy:

- Every repository path they name in backticks, and every Claude Code `@` import,
  must be a tracked file or folder. Claude Code skips a missing import silently.
- `AGENTS.md` stays at or under 200 lines, with a warning from 150. Longer
  instruction files are followed less reliably, and Claude Code's guidance is to
  stay under 200 lines.
- The must-follow part of `AGENTS.md` (everything before the first
  "## Commands and layout" or "## Where to find more" heading) fits in 4,000
  characters, because Copilot code review reads only the first 4,000 characters
  of an instruction file.

Exit codes: 0 when there are no errors (warnings may be printed), 1 when there
is at least one error.
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_FILES = ("AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md")

MAX_LINES = 200
WARNING_LINES = 150
MAX_MUST_FOLLOW_CHARACTERS = 4000
MUST_FOLLOW_END_HEADINGS = ("## Commands and layout", "## Where to find more")

# Shared skills are written in SKILL_SOURCE and copied into SKILL_COPY for Claude
# Code by tools/agents/sync_skills.py. Only folders named with SKILL_PREFIX are
# shared; other folders in SKILL_COPY are a contributor's own skills.
SKILL_SOURCE = ".agents/skills"
SKILL_COPY = ".claude/skills"
SKILL_PREFIX = "core-critical-"

# Backticks also hold branch names, version numbers and placeholders, so a token
# only counts as a path when it ends in one of these extensions or starts with a
# tracked top-level name. That leaves `origin/develop` and `1.0.34.mw3update` alone.
PATH_EXTENSIONS = (".md", ".py", ".yml", ".yaml", ".json", ".toml", ".ps1", ".cmd", ".txt")
CHARACTERS_NEVER_IN_A_PATH = frozenset(" <>*:")
BACKTICKED_TOKEN = re.compile(r"`([^`\n]+)`")
# A Claude Code import is "@path.md" at the start of a line or after a space. An
# import written inside backticks is not expanded, so the pattern skips it.
CLAUDE_IMPORT = re.compile(r"(?:^|\s)@([^\s`]+\.md)\b", re.MULTILINE)

SHRINK_ADVICE = (
    "move reference material word for word to a docs/ page and add a one-line "
    'pointer under "## Where to find more"'
)


@dataclass(frozen=True)
class Finding:
    level: str  # "error" or "warning"
    message: str


class GitUnavailable(Exception):
    """Raised when the list of tracked files can't be read from git."""


def check(root: Path, tracked_paths: list[str]) -> list[Finding]:
    """Return every problem in the agent instruction files under `root`."""
    agents_file = root / "AGENTS.md"
    if not agents_file.is_file():
        return [Finding("error", "AGENTS.md is missing; it holds every agent rule.")]

    tracked = _TrackedTree(tracked_paths, root)
    findings: list[Finding] = []
    for name in AGENT_FILES:
        instruction_file = root / name
        if instruction_file.is_file():
            text = instruction_file.read_text(encoding="utf-8")
            findings += _check_named_paths(name, text, tracked)
    claude_file = root / "CLAUDE.md"
    if claude_file.is_file():
        claude_imports = CLAUDE_IMPORT.findall(claude_file.read_text(encoding="utf-8"))
        if "AGENTS.md" not in claude_imports:
            findings.append(
                Finding(
                    "error",
                    "CLAUDE.md doesn't import @AGENTS.md, so Claude Code misses every rule.",
                )
            )
    findings += _check_size(agents_file.read_text(encoding="utf-8"))
    return findings


def must_follow_length(agents_text: str) -> int | None:
    """Return how many characters come before the first end heading, or None if there is none."""
    characters_so_far = 0
    for line in agents_text.splitlines(keepends=True):
        if line.rstrip() in MUST_FOLLOW_END_HEADINGS:
            return characters_so_far
        characters_so_far += len(line)
    return None


def tracked_paths_from_git(root: Path) -> list[str]:
    """Return every tracked path under `root`, with forward slashes."""
    try:
        # -z keeps unusual file names unquoted.
        result = subprocess.run(
            ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=False
        )
    except FileNotFoundError as missing_git:
        raise GitUnavailable("git is not on PATH") from missing_git
    if result.returncode != 0:
        raise GitUnavailable(result.stderr.decode("utf-8", errors="replace").strip())
    return [path for path in result.stdout.decode("utf-8").split("\0") if path]


class _TrackedTree:
    """Answers whether a path names a tracked file or a folder that holds one."""

    def __init__(self, tracked_paths: list[str], root: Path) -> None:
        self.root = root
        self.files = set(tracked_paths)
        self.folders: set[str] = set()
        for path in tracked_paths:
            parts = path.split("/")[:-1]
            for depth in range(1, len(parts) + 1):
                self.folders.add("/".join(parts[:depth]))
        self.top_level_names = {path.split("/", 1)[0] for path in tracked_paths}

    def contains(self, path: str) -> bool:
        return path in self.files or path in self.folders

    def ignores(self, path: str) -> bool:
        """Return whether .gitignore covers `path`, such as a local `build/` folder.

        Agent files may name a folder that is deliberately never committed. Any git
        failure, such as a folder that isn't a repository, counts as not ignored.
        """
        try:
            result = subprocess.run(
                ["git", "check-ignore", "-q", "--no-index", path],
                cwd=self.root,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError:
            return False
        return result.returncode == 0


def _check_named_paths(name: str, text: str, tracked: _TrackedTree) -> list[Finding]:
    findings = []
    for token in BACKTICKED_TOKEN.findall(text):
        path = _path_in_token(token, tracked)
        if path is None or tracked.contains(path):
            continue
        # A "build/" ignore rule matches only a name known to be a folder, so keep the slash.
        named_as_folder = token.split("#", 1)[0].endswith("/")
        if not tracked.ignores(f"{path}/" if named_as_folder else path):
            findings.append(Finding("error", f"{name} names `{token}`, which isn't tracked."))
    for path in CLAUDE_IMPORT.findall(text):
        if not tracked.contains(path):
            findings.append(Finding("error", f"{name} imports @{path}, which isn't tracked."))
    return findings


def _path_in_token(token: str, tracked: _TrackedTree) -> str | None:
    """Return the repository path a backticked token names, or None if it isn't a path."""
    if any(character in CHARACTERS_NEVER_IN_A_PATH for character in token):
        return None
    # Drop a "#section" anchor, and the "@" of an import quoted as an example.
    without_anchor = token.split("#", 1)[0].removeprefix("@")
    path = without_anchor.rstrip("/")
    if not path:
        return None
    starts_with_tracked_name = path.split("/", 1)[0] in tracked.top_level_names
    # A trailing slash marks a folder even when its top-level name isn't tracked,
    # so a typo or a deleted top-level folder is still caught.
    names_a_folder = without_anchor.endswith("/")
    if path.endswith(PATH_EXTENSIONS) or starts_with_tracked_name or names_a_folder:
        return path
    return None


def _check_size(agents_text: str) -> list[Finding]:
    findings = []
    line_count = len(agents_text.splitlines())
    if line_count > MAX_LINES:
        findings.append(
            Finding(
                "error",
                f"AGENTS.md has {line_count} lines, over the {MAX_LINES}-line limit; "
                f"{SHRINK_ADVICE}.",
            )
        )
    elif line_count > WARNING_LINES:
        findings.append(
            Finding(
                "warning",
                f"AGENTS.md has {line_count} lines, nearing the {MAX_LINES}-line limit; "
                f"{SHRINK_ADVICE}.",
            )
        )

    must_follow = must_follow_length(agents_text)
    if must_follow is None:
        headings = " or ".join(f'"{heading}"' for heading in MUST_FOLLOW_END_HEADINGS)
        findings.append(
            Finding("error", f"AGENTS.md needs a {headings} heading after its must-follow rules.")
        )
    elif must_follow > MAX_MUST_FOLLOW_CHARACTERS:
        findings.append(
            Finding(
                "error",
                f"AGENTS.md's must-follow part is {must_follow} characters, over the "
                f"{MAX_MUST_FOLLOW_CHARACTERS} that Copilot code review reads; {SHRINK_ADVICE}.",
            )
        )
    return findings


def main() -> int:
    try:
        tracked_paths = tracked_paths_from_git(REPO_ROOT)
    except GitUnavailable as reason:
        print(f"error: can't list tracked files ({reason}); run this inside a git checkout.")
        return 1

    findings = check(REPO_ROOT, tracked_paths)
    for finding in findings:
        print(f"{finding.level}: {finding.message}")

    agents_file = REPO_ROOT / "AGENTS.md"
    if agents_file.is_file():
        must_follow = must_follow_length(agents_file.read_text(encoding="utf-8"))
        if must_follow is not None:
            print(
                f"AGENTS.md must-follow part: {must_follow} of "
                f"{MAX_MUST_FOLLOW_CHARACTERS} characters."
            )
    return 1 if any(finding.level == "error" for finding in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
