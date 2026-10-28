"""Check the agent instruction files and shared skills for missing paths, size and drift.

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

Shared skills live in `.agents/skills/core-critical-<task>/`, with an exact copy
in `.claude/skills/` for Claude Code (made by `tools/agents/sync_skills.py`):

- The tracked files in both folders match byte for byte.
- Each skill is a folder with a `SKILL.md` whose frontmatter uses only the keys
  every tool reads the same way (`name`, `description`, `disable-model-invocation`,
  `paths`). A tool that can't parse a skill's frontmatter skips the skill
  silently, so values YAML would misread must be quoted.
- `name` equals the folder name, starts `core-critical-`, uses lowercase letters,
  digits and single hyphens, and is at most 64 characters; `description` is 1 to
  1,024 characters. These are the limits of the Agent Skills format.
- An optional `agents/openai.yaml` (read by Codex) sets only
  `policy.allow_implicit_invocation`.
- Backticked paths in a skill's Markdown files are tracked, either from the
  repository root or from the skill's own folder.

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
SKILL_KEYS = ("name", "description", "disable-model-invocation", "paths")
SKILL_NAME = re.compile(rf"{re.escape(SKILL_PREFIX)}[a-z0-9]+(-[a-z0-9]+)*")
MAX_SKILL_NAME_CHARACTERS = 64
MAX_DESCRIPTION_CHARACTERS = 1024
# Unquoted, YAML reads a value starting with one of these, or holding a colon before
# a space or the end, or a "#" after a space, as something other than plain text, or
# fails to parse it at all.
YAML_SPECIAL_STARTS = tuple("[]{}>|*&!%@`#,?-")
YAML_SPECIAL_INSIDE = re.compile(r":(\s|$)|\s#")
OPENAI_POLICY_LINE = re.compile(r"\s+allow_implicit_invocation: (true|false)")
SYNC_ADVICE = f"edit skills only in {SKILL_SOURCE}/, then run `python tools/agents/sync_skills.py`"

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
    findings += _check_skills(root, tracked)
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


def _check_named_paths(
    name: str, text: str, tracked: _TrackedTree, skill_folder: str | None = None
) -> list[Finding]:
    """Report named paths that aren't tracked; in a skill, a path may also be relative to its folder."""
    findings = []
    for token in BACKTICKED_TOKEN.findall(text):
        path = _path_in_token(token, tracked)
        if path is None or tracked.contains(path):
            continue
        if skill_folder is not None and tracked.contains(f"{skill_folder}/{path}"):
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


def _check_skills(root: Path, tracked: _TrackedTree) -> list[Finding]:
    source_files = _tracked_under(SKILL_SOURCE, tracked)
    copy_files = _tracked_under(SKILL_COPY, tracked)
    findings = _check_skill_copy(root, source_files, copy_files)

    skill_folders = set()
    for relative_path in sorted(source_files):
        folder, separator, _ = relative_path.partition("/")
        if separator:
            skill_folders.add(folder)
        else:
            findings.append(
                Finding(
                    "error",
                    f"{SKILL_SOURCE}/{relative_path} sits directly in {SKILL_SOURCE}/; "
                    "each skill is a folder holding a SKILL.md.",
                )
            )
    for folder in sorted(skill_folders):
        findings += _check_skill_folder(root, folder, source_files, tracked)
    return findings


def _tracked_under(folder: str, tracked: _TrackedTree) -> set[str]:
    """Return the tracked files under `folder`, relative to it."""
    prefix = f"{folder}/"
    return {path.removeprefix(prefix) for path in tracked.files if path.startswith(prefix)}


def _check_skill_copy(root: Path, source_files: set[str], copy_files: set[str]) -> list[Finding]:
    """Report every difference between the shared skills and their Claude Code copy."""
    findings = []
    for relative_path in sorted(source_files | copy_files):
        source_name = f"{SKILL_SOURCE}/{relative_path}"
        copy_name = f"{SKILL_COPY}/{relative_path}"
        folder, separator, _ = relative_path.partition("/")
        is_shared = separator != "" and folder.startswith(SKILL_PREFIX)
        if not is_shared:
            if relative_path in copy_files:
                findings.append(
                    Finding(
                        "error",
                        f"{copy_name} is tracked but isn't a shared skill; shared skills go in "
                        f"{SKILL_SOURCE}/ under a `{SKILL_PREFIX}` name, and a personal skill "
                        "stays out of git.",
                    )
                )
            # A source file outside a shared skill folder is reported by the folder checks.
            continue

        if relative_path not in copy_files:
            problem = f"{source_name} has no copy in {SKILL_COPY}/"
        elif relative_path not in source_files:
            problem = f"{copy_name} has no source in {SKILL_SOURCE}/"
        elif _bytes_or_none(root / source_name) != _bytes_or_none(root / copy_name):
            # A tracked file deleted from disk reads as None, so it counts as a difference.
            problem = f"{copy_name} differs from {source_name}"
        else:
            continue
        findings.append(Finding("error", f"{problem}; {SYNC_ADVICE}."))
    return findings


def _bytes_or_none(path: Path) -> bytes | None:
    return path.read_bytes() if path.is_file() else None


def _check_skill_folder(
    root: Path, folder: str, source_files: set[str], tracked: _TrackedTree
) -> list[Finding]:
    skill_folder = f"{SKILL_SOURCE}/{folder}"
    skill_file = root / skill_folder / "SKILL.md"
    if f"{folder}/SKILL.md" not in source_files or not skill_file.is_file():
        return [Finding("error", f"{skill_folder}/ has no SKILL.md.")]

    findings = _check_frontmatter(
        f"{skill_folder}/SKILL.md", folder, skill_file.read_text(encoding="utf-8")
    )
    openai_file = root / skill_folder / "agents/openai.yaml"
    if f"{folder}/agents/openai.yaml" in source_files and openai_file.is_file():
        findings += _check_openai_settings(
            f"{skill_folder}/agents/openai.yaml", openai_file.read_text(encoding="utf-8")
        )
    for relative_path in sorted(source_files):
        markdown_file = root / SKILL_SOURCE / relative_path
        in_this_skill = relative_path.startswith(f"{folder}/")
        if in_this_skill and relative_path.endswith(".md") and markdown_file.is_file():
            findings += _check_named_paths(
                f"{SKILL_SOURCE}/{relative_path}",
                markdown_file.read_text(encoding="utf-8"),
                tracked,
                skill_folder,
            )
    return findings


def _check_frontmatter(skill_name: str, folder: str, text: str) -> list[Finding]:
    """Check a SKILL.md's frontmatter, reading only the small YAML subset skills here use."""
    lines = text.splitlines()
    if not lines or lines[0].rstrip() != "---":
        return [Finding("error", f"{skill_name} must start with a `---` frontmatter line.")]
    closing_line = next(
        (index for index in range(1, len(lines)) if lines[index].rstrip() == "---"), None
    )
    if closing_line is None:
        return [Finding("error", f"{skill_name} has no closing `---` frontmatter line.")]

    findings = []
    raw_values: dict[str, str] = {}
    key = ""
    value = ""
    for line in lines[1:closing_line]:
        if not line.strip() or line.startswith("#"):
            continue
        # Indented and "- " lines continue the key above, such as a `paths` list. A
        # `>` or `|` block's lines are reported once, with the block itself, below.
        if line.startswith((" ", "\t", "-")):
            if key and not value.strip().startswith((">", "|")):
                findings += _check_continuation(skill_name, key, line)
            continue
        key, _, value = line.partition(":")
        if key not in SKILL_KEYS:
            allowed = ", ".join(f"`{allowed_key}`" for allowed_key in SKILL_KEYS)
            findings.append(
                Finding("error", f"{skill_name} has frontmatter key `{key}`; only {allowed}.")
            )
        raw_values[key] = value.strip()

    for key in ("name", "description"):
        if key not in raw_values:
            findings.append(Finding("error", f"{skill_name} needs a `{key}` in its frontmatter."))
            continue
        problem = _plain_value_problem(raw_values[key])
        if problem is not None:
            findings.append(Finding("error", f"{skill_name}'s `{key}` {problem}."))
            raw_values.pop(key)

    if "name" in raw_values:
        findings += _check_skill_name(skill_name, folder, _unquoted(raw_values["name"]))
    if "description" in raw_values:
        description_length = len(_unquoted(raw_values["description"]))
        if not 1 <= description_length <= MAX_DESCRIPTION_CHARACTERS:
            findings.append(
                Finding(
                    "error",
                    f"{skill_name}'s `description` is {description_length} characters; it must "
                    f"be 1 to {MAX_DESCRIPTION_CHARACTERS}.",
                )
            )
    invocation = raw_values.get("disable-model-invocation")
    if invocation is not None and invocation not in ("true", "false"):
        findings.append(
            Finding("error", f"{skill_name}'s `disable-model-invocation` must be true or false.")
        )
    inline_paths = raw_values.get("paths", "")
    paths_problem = _plain_value_problem(inline_paths) if inline_paths else None
    if paths_problem is not None:
        findings.append(Finding("error", f"{skill_name}'s `paths` {paths_problem}."))
    return findings


def _check_continuation(skill_name: str, key: str, line: str) -> list[Finding]:
    """Check a line that continues the key above: only a `paths` list item may."""
    if key != "paths":
        return [
            Finding(
                "error",
                f"{skill_name}'s `{key}` continues onto another line; write it on one line.",
            )
        ]
    item = line.strip()
    if not item.startswith("- "):
        return [Finding("error", f"{skill_name}'s `paths` lines must each be `- <pattern>`.")]
    problem = _plain_value_problem(item[2:].strip())
    if problem is None:
        return []
    return [Finding("error", f"{skill_name}'s `paths` entry `{item[2:].strip()}` {problem}.")]


def _plain_value_problem(raw_value: str) -> str | None:
    """Say why a one-line frontmatter value would be misread, or None if it reads as written."""
    if raw_value != _unquoted(raw_value):
        return None
    if raw_value.startswith((">", "|")):
        return "is a `>` or `|` block; write it on one line"
    if raw_value.startswith(("'", '"')):
        return "opens a quote that isn't closed at the end of the value; quote the whole value"
    if raw_value.startswith(YAML_SPECIAL_STARTS) or YAML_SPECIAL_INSIDE.search(raw_value):
        return "needs quotes, because YAML reads it differently or can't parse it unquoted"
    return None


def _unquoted(raw_value: str) -> str:
    is_quoted = len(raw_value) >= 2 and raw_value[0] in "'\"" and raw_value[-1] == raw_value[0]
    return raw_value[1:-1] if is_quoted else raw_value


def _check_skill_name(skill_name: str, folder: str, name: str) -> list[Finding]:
    findings = []
    if name != folder:
        findings.append(
            Finding("error", f"{skill_name}'s `name` is `{name}`; it must match its folder.")
        )
    if not SKILL_NAME.fullmatch(name):
        findings.append(
            Finding(
                "error",
                f"{skill_name}'s `name` must start `{SKILL_PREFIX}` and use only lowercase "
                "letters, digits and single hyphens.",
            )
        )
    if len(name) > MAX_SKILL_NAME_CHARACTERS:
        findings.append(
            Finding(
                "error",
                f"{skill_name}'s `name` is {len(name)} characters, over "
                f"{MAX_SKILL_NAME_CHARACTERS}.",
            )
        )
    return findings


def _check_openai_settings(settings_name: str, text: str) -> list[Finding]:
    """Codex settings may only switch implicit use of the skill on or off."""
    meaningful_lines = [
        line.rstrip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    only_the_policy_line = (
        len(meaningful_lines) == 2
        and meaningful_lines[0] == "policy:"
        and OPENAI_POLICY_LINE.fullmatch(meaningful_lines[1]) is not None
    )
    if only_the_policy_line:
        return []
    return [
        Finding(
            "error",
            f"{settings_name} may hold only `policy:` and one indented "
            "`allow_implicit_invocation: true` or `false` line.",
        )
    ]


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
