"""Run the project's style checkers and count what they find.

Usage, from the repository root:
    python tools/style/check_style.py           report every language and check
    python tools/style/check_style.py --fix     format the languages whose cleanup has landed
    python tools/style/check_style.py --fix --files a.js b.css  format only those files
    python tools/style/check_style.py --list    show which files each language checks
    python tools/style/check_style.py --preflight --language python  run pre-cleanup safety checks

Setup, the pinned tool versions and the rollout plan are in tools/style/README.md. The
rules themselves are in CODE_STYLE.md.

A check is "report only" until it is listed in ENFORCED below. Report-only findings are
printed but never fail the run. An enforced check with findings exits 1. A checker that
is missing, the wrong version or crashed exits 2, because a broken checker must never
look like a clean result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

STYLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = STYLE_DIR.parents[1]

# Which checks are switched on, per language. Each language's one-time cleanup PR adds
# its entry here (for example "python": {"format"}). This is the only switch: it decides
# both what --fix rewrites and which findings fail CI.
ENFORCED: dict[str, set[str]] = {"web": {"format"}}

# Tools get at most this many file paths per call, to stay under the Windows
# command-line length limit (about 32,000 characters).
FILES_PER_CALL = 100

EXIT_CLEAN = 0
EXIT_ENFORCED_FINDINGS = 1
EXIT_TOOL_ERROR = 2


@dataclass
class ToolRun:
    """What one call to an external checker returned."""

    exit_code: int
    output: str


@dataclass
class CheckResult:
    """The outcome of one check (for example "python lint") over all its files."""

    language: str
    check: str
    enforced: bool
    files_checked: int
    findings: list[str] = field(default_factory=list)
    error: str = ""

    @property
    def label(self) -> str:
        mode = "enforced" if self.enforced else "report only"
        return f"{self.language} {self.check} ({mode})"


@dataclass
class Check:
    """One check for one language: how to run it, and what its exit codes mean.

    run(paths, fix) calls the tool on a batch of paths. parse(output) returns one item
    per finding. found_exit_code is the code the tool uses for "found something"; 0
    always means clean.
    """

    run: Callable[[list[str], bool], ToolRun]
    parse: Callable[[str], list[str]]
    found_exit_code: int
    can_fix: bool


@dataclass
class Language:
    """The file suffixes a language covers and the checks that run on them.

    pinned_tool names the tool whose version is checked against requirements.txt or
    package.json before running. dotnet and PSScriptAnalyzer are pinned elsewhere (CI and
    check_powershell.ps1), so those languages have none.
    """

    suffixes: list[str]
    checks: dict[str, Check]
    pinned_tool: str | None = None


# ---------------------------------------------------------------------------------------
# Exclusions
# ---------------------------------------------------------------------------------------


def read_pattern_lines(path: Path) -> list[str]:
    """Return the non-blank, non-comment lines of an ignore-style file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def pattern_to_pathspec(pattern: str) -> str:
    """Turn one exclude.txt line into a git pathspec that excludes the same files.

    exclude.txt allows three shapes: a folder ending in "/", an exact file path, or a
    file-name pattern with no "/" that applies in every folder.
    """
    if pattern.endswith("/"):
        return f":(exclude,glob){pattern}**"
    if "/" in pattern:
        return f":(exclude){pattern}"
    if "*" in pattern or "?" in pattern:
        return f":(exclude,glob)**/{pattern}"
    raise ValueError(f"exclude.txt line {pattern!r} is not a folder/, a path or a name pattern")


def find_exclusion_drift(
    master: list[str], ruff_copy: list[str], prettier_copy: list[str]
) -> list[str]:
    """Describe every way the Ruff and Prettier copies differ from exclude.txt."""
    problems = []
    for copy_name, copy in (("ruff.toml", ruff_copy), (".prettierignore", prettier_copy)):
        missing = sorted(set(master) - set(copy))
        extra = sorted(set(copy) - set(master))
        if missing:
            problems.append(f"{copy_name} is missing {', '.join(missing)}")
        if extra:
            problems.append(f"{copy_name} has lines not in exclude.txt: {', '.join(extra)}")
    return problems


def load_exclusions() -> tuple[list[str], list[str]]:
    """Return the exclude.txt patterns and any drift between them and their copies."""
    master = read_pattern_lines(STYLE_DIR / "exclude.txt")
    ruff_settings = tomllib.loads((REPO_ROOT / "ruff.toml").read_text(encoding="utf-8"))
    ruff_copy = ruff_settings.get("extend-exclude", [])
    prettier_copy = read_pattern_lines(REPO_ROOT / ".prettierignore")
    return master, find_exclusion_drift(master, ruff_copy, prettier_copy)


def list_files(suffixes: list[str], exclude_patterns: list[str]) -> list[str]:
    """List tracked files with the given suffixes, minus the excluded ones."""
    include = [f"*{suffix}" for suffix in suffixes]
    exclude = [pattern_to_pathspec(pattern) for pattern in exclude_patterns]
    listing = subprocess.run(
        ["git", "ls-files", "-z", "--", *include, *exclude],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = [path for path in listing.stdout.split("\0") if path]
    # A file deleted in the working tree but not yet committed is still tracked.
    return [path for path in tracked if (REPO_ROOT / path).is_file()]


# ---------------------------------------------------------------------------------------
# Pinned tools
# ---------------------------------------------------------------------------------------


def tool_folders() -> list[Path]:
    """Folders searched for checkers before PATH: the local venv and node_modules."""
    venv_scripts = "Scripts" if os.name == "nt" else "bin"
    return [STYLE_DIR / ".venv" / venv_scripts, STYLE_DIR / "node_modules" / ".bin"]


def find_tool(name: str) -> str | None:
    """Find an executable, preferring tools/style's own installs, then PATH."""
    for folder in tool_folders():
        # shutil.which also finds Windows .cmd shims such as prettier.cmd.
        found = shutil.which(name, path=str(folder))
        if found:
            return found
    return shutil.which(name)


def read_pinned_versions() -> dict[str, str]:
    """Read the pinned versions from requirements.txt and package.json."""
    pins = {}
    for line in (STYLE_DIR / "requirements.txt").read_text(encoding="utf-8").splitlines():
        match = re.match(r"^([A-Za-z0-9_.-]+)==([^\s\\]+)", line)
        if match:
            pins[match.group(1)] = match.group(2)
    package = json.loads((STYLE_DIR / "package.json").read_text(encoding="utf-8"))
    pins.update(package["devDependencies"])
    return pins


def check_tool_version(name: str, expected: str) -> str:
    """Return an error message if the tool is missing or not the pinned version."""
    tool = find_tool(name)
    if tool is None:
        return f"{name} is not installed; see tools/style/README.md"
    version_output = run_tool([tool, "--version"]).output
    reported = re.findall(r"\d+\.\d+\.\d+", version_output)
    if expected not in reported:
        return f"{name} reports {version_output.strip()!r}, but {expected} is pinned"
    return ""


TOOL_NOT_FOUND_EXIT_CODE = 127  # The shell convention for "command not found".


def run_tool(command: list[str], stdin_text: str | None = None) -> ToolRun:
    """Run a checker from the repository root and capture everything it prints."""
    if shutil.which(command[0]) is None:
        return ToolRun(TOOL_NOT_FOUND_EXIT_CODE, f"{command[0]} is not installed")
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        input=stdin_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        # Checkers use non-zero exit codes for findings; the callers interpret them.
        check=False,
    )
    return ToolRun(completed.returncode, completed.stdout + completed.stderr)


# ---------------------------------------------------------------------------------------
# One runner and one output parser per checker
# ---------------------------------------------------------------------------------------


def tool_command(name: str) -> str:
    """The path to run for a tool; a bare name if missing, which run_tool reports."""
    return find_tool(name) or name


def run_clang_format(paths: list[str], fix: bool) -> ToolRun:
    mode = ["-i"] if fix else ["--dry-run", "--Werror"]
    return run_tool([tool_command("clang-format"), *mode, "--style=file", *paths])


def parse_clang_format(output: str) -> list[str]:
    # One line per problem: "path:line:col: error: code should be clang-formatted [...]".
    pattern = r"^(.+?):\d+:\d+: error: code should be clang-formatted"
    return sorted(set(re.findall(pattern, output, flags=re.MULTILINE)))


def run_ruff_format(paths: list[str], fix: bool) -> ToolRun:
    mode = [] if fix else ["--check", "--output-format", "concise"]
    return run_tool([tool_command("ruff"), "format", "--no-cache", *mode, *paths])


def parse_ruff_format(output: str) -> list[str]:
    # One line per file: "path:line:col: unformatted: File would be reformatted".
    pattern = r"^(.+?):\d+:\d+: unformatted:"
    return sorted(set(re.findall(pattern, output, flags=re.MULTILINE)))


def run_ruff_lint(paths: list[str], fix: bool) -> ToolRun:
    lint_options = ["--no-fix", "--no-cache", "--output-format", "concise"]
    return run_tool([tool_command("ruff"), "check", *lint_options, *paths])


def parse_ruff_lint(output: str) -> list[str]:
    # One line per finding: "path:line:col: CODE message".
    return re.findall(r"^.+?:\d+:\d+: .+$", output, flags=re.MULTILINE)


def run_dotnet_format(paths: list[str], fix: bool) -> ToolRun:
    with tempfile.TemporaryDirectory() as report_dir:
        mode = [] if fix else ["--verify-no-changes"]
        command = ["dotnet", "format", "whitespace", str(REPO_ROOT), "--folder", *mode]
        command += ["--report", report_dir, "--include", *paths]
        tool_run = run_tool(command)
        report_path = Path(report_dir) / "format-report.json"
        # The report, not the console text, says which files would change.
        report = report_path.read_text(encoding="utf-8") if report_path.exists() else "[]"
        return ToolRun(tool_run.exit_code, report)


def parse_dotnet_format(output: str) -> list[str]:
    changed_documents = json.loads(output)
    paths = {document["FilePath"] for document in changed_documents}
    return sorted(Path(os.path.relpath(path, REPO_ROOT)).as_posix() for path in paths)


def run_prettier(paths: list[str], fix: bool) -> ToolRun:
    mode = "--write" if fix else "--list-different"
    return run_tool([tool_command("prettier"), mode, *paths])


def powershell_runner(mode: str) -> Callable[[list[str], bool], ToolRun]:
    def run(paths: list[str], fix: bool) -> ToolRun:
        chosen_mode = "FormatFix" if fix else mode
        helper = str(STYLE_DIR / "check_powershell.ps1")
        command = ["pwsh", "-NoProfile", "-File", helper, "-Mode", chosen_mode]
        return run_tool(command, stdin_text="\n".join(paths))

    return run


def parse_lines(output: str) -> list[str]:
    return [line for line in output.splitlines() if line.strip()]


LANGUAGES: dict[str, Language] = {
    "cpp": Language(
        suffixes=[".cpp", ".hpp", ".h", ".inc"],
        checks={"format": Check(run_clang_format, parse_clang_format, 1, can_fix=True)},
        pinned_tool="clang-format",
    ),
    "python": Language(
        suffixes=[".py"],
        checks={
            "format": Check(run_ruff_format, parse_ruff_format, 1, can_fix=True),
            "lint": Check(run_ruff_lint, parse_ruff_lint, 1, can_fix=False),
        },
        pinned_tool="ruff",
    ),
    "csharp": Language(
        suffixes=[".cs"],
        # dotnet format uses exit code 2 for "files would change".
        checks={"format": Check(run_dotnet_format, parse_dotnet_format, 2, can_fix=True)},
    ),
    "web": Language(
        suffixes=[".js", ".cjs", ".mjs", ".css", ".html"],
        checks={"format": Check(run_prettier, parse_lines, 1, can_fix=True)},
        pinned_tool="prettier",
    ),
    "powershell": Language(
        suffixes=[".ps1", ".psm1", ".psd1"],
        checks={
            "format": Check(powershell_runner("FormatCheck"), parse_lines, 1, can_fix=True),
            "lint": Check(powershell_runner("Lint"), parse_lines, 1, can_fix=False),
        },
    ),
}


# ---------------------------------------------------------------------------------------
# Deciding outcomes
# ---------------------------------------------------------------------------------------


def classify_tool_run(tool_run: ToolRun, items: list[str], found_exit_code: int) -> str:
    """Read one tool call as "clean", "findings" or "error".

    A "found something" exit code with nothing parsed from the output is an error: the
    tool failed in a way the parser doesn't recognise, and must not count as clean.
    """
    if tool_run.exit_code == 0 and not items:
        return "clean"
    if tool_run.exit_code == found_exit_code and items:
        return "findings"
    return "error"


def overall_exit_code(results: list[CheckResult]) -> int:
    """Broken tools beat everything; then only enforced findings fail."""
    if any(result.error for result in results):
        return EXIT_TOOL_ERROR
    if any(result.enforced and result.findings for result in results):
        return EXIT_ENFORCED_FINDINGS
    return EXIT_CLEAN


def short_error(tool_run: ToolRun) -> str:
    """The exit code and last few output lines, enough to see why a tool failed."""
    last_lines = " | ".join(tool_run.output.strip().splitlines()[-3:])
    return f"exit code {tool_run.exit_code}: {last_lines}"


def in_batches(paths: list[str]) -> Iterator[list[str]]:
    for start in range(0, len(paths), FILES_PER_CALL):
        yield paths[start : start + FILES_PER_CALL]


def is_enforced(language: str, check_name: str) -> bool:
    return check_name in ENFORCED.get(language, set())


def version_error_for(language: str, pins: dict[str, str]) -> str:
    """Return why a language's pinned tool can't be used, or "" if it can."""
    pinned_tool = LANGUAGES[language].pinned_tool
    return check_tool_version(pinned_tool, pins[pinned_tool]) if pinned_tool else ""


def run_check(language: str, check_name: str, check: Check, paths: list[str]) -> CheckResult:
    result = CheckResult(language, check_name, is_enforced(language, check_name), len(paths))
    for batch in in_batches(paths):
        tool_run = check.run(batch, False)
        tool_finished_normally = tool_run.exit_code in (0, check.found_exit_code)
        items = check.parse(tool_run.output) if tool_finished_normally else []
        outcome = classify_tool_run(tool_run, items, check.found_exit_code)
        if outcome == "error":
            result.error = short_error(tool_run)
            return result
        result.findings.extend(items)
    return result


# ---------------------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------------------


def describe(result: CheckResult) -> str:
    if result.error:
        return f"{result.label}: error: {result.error}"
    count = len(result.findings)
    if result.check == "lint":
        return f"{result.label}: {count:,} findings in {result.files_checked:,} files checked"
    return f"{result.label}: {count:,} of {result.files_checked:,} files need formatting"


def write_github_summary(results: list[CheckResult]) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    rows = ["| Check | Mode | Files checked | Findings |", "| --- | --- | --- | --- |"]
    for result in results:
        mode = "enforced" if result.enforced else "report only"
        check_name = f"{result.language} {result.check}"
        files_checked = f"{result.files_checked:,}"
        findings = "error" if result.error else f"{len(result.findings):,}"
        rows.append(f"| {check_name} | {mode} | {files_checked} | {findings} |")
    with open(summary_path, "a", encoding="utf-8") as summary:
        summary.write("## Style checks\n\n" + "\n".join(rows) + "\n")


def print_github_warnings(results: list[CheckResult]) -> None:
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    for result in results:
        if result.findings and not result.enforced and not result.error:
            print(f"::warning title=Style report::{describe(result)}")


# ---------------------------------------------------------------------------------------
# Pre-cleanup safety checks
# ---------------------------------------------------------------------------------------

CODE_FILE_EXTENSIONS = {
    ".py",
    ".ps1",
    ".psm1",
    ".psd1",
    ".cs",
    ".cpp",
    ".hpp",
    ".h",
    ".c",
    ".inc",
    ".js",
    ".ts",
    ".cjs",
    ".mjs",
    ".sh",
    ".bash",
    ".cmake",
}

READ_PATTERNS = [
    r"\bopen\s*\(",
    r"\.open\s*\(",
    r"\.read\b",
    r"\bread_text\b",
    r"\bread_bytes\b",
    r"\breadFileSync\b",
    r"\breadFile\b",
    r"\bGet-Content\b",
    r"\bReadAllText\b",
    r"\bReadAllBytes\b",
    r"\bReadAllLines\b",
    r"\bGet-FileHash\b",
    r"\bsha256\b",
    r"\bSHA256\b",
    r"\bhashlib\b",
    r"\bfile_digest\b",
    r"\binspect\.getsource\b",
    r"\bfile\s*\(\s*(?:SHA256|READ|STRINGS)\b",
    r"\brequire_pin\b",
    r"\bCopy-HlpPin\b",
    r"\bHash-Hlp\b",
    r"\bsha\s*\(",
    r"\bpin\s*\(",
]
READ_OPERATION_REGEX = re.compile("|".join(READ_PATTERNS))
DYNAMIC_INVENTORY_REGEX = re.compile(
    r"\b(?:rglob|glob|walk|Get-ChildItem|EnumerateFiles|GetFiles|scandir)\b", re.IGNORECASE
)
SELF_PATH_REGEX = re.compile(r"\b__file__\b|\$PSCommandPath\b", re.IGNORECASE)
# A file type a script names for a folder listing: "*.py", or a quoted ".py". The first
# character must be a letter so numbers such as ".5" don't count as file types.
LISTING_SUFFIX_REGEX = re.compile(r"""\*\.([A-Za-z]\w*)\b|["']\.([A-Za-z]\w*)["']""")
# Folder listings in these folders are not reported. They hold frozen, hash-pinned
# evidence scripts that can't change; the stored-hash scan still finds any that keep a
# changed file's hash in the repository (issue #214).
FROZEN_LISTING_HOLDERS = ("tools/m4-", "tools/x87-")
# Hit kinds in the order they print for the same line.
TEXT_READ_KINDS = ("direct", "name", "listing")


class PreflightReadError(Exception):
    """A preflight scan could not read one of its repository inputs."""


def normalize_repo_path(path: str) -> str:
    """Normalize Git and formatter paths to repository-style separators."""
    return posixpath.normpath(path.replace("\\", "/"))


@dataclass
class StoredHashHit:
    """A tracked file that contains a formatted file's hash or duplicate bytes."""

    holding_file: str
    target_file: str
    label: str  # "unresolved digest match" or "identical copy"

    def describe(self) -> str:
        if self.label == "identical copy":
            return f"{self.holding_file}: identical copy of {self.target_file}"
        return f"{self.holding_file}: unresolved digest match for {self.target_file}"


@dataclass
class TextReadHit:
    """A code line that may read, slice, or hash a target file as text.

    kind is "direct" (the line names target_file by its path), "name" (the line names
    only a file name; details holds that name, then every target it could mean) or
    "listing" (the line lists a folder; details holds the file types that reach a
    target, empty when the script names none, so any target may be read).
    """

    holding_file: str
    line_number: int
    kind: str
    target_file: str = ""
    details: tuple[str, ...] = ()

    def sort_key(self) -> tuple[str, int, int, str]:
        first_target = self.target_file or (self.details[0] if self.details else "")
        return (
            self.holding_file,
            self.line_number,
            TEXT_READ_KINDS.index(self.kind),
            first_target,
        )

    def describe(self) -> str:
        location = f"{self.holding_file}:{self.line_number}"
        if self.kind == "name":
            name, *candidates = self.details
            files = "file" if len(candidates) == 1 else "files"
            listed = ", ".join(candidates)
            return f"{location}: names {name} (could be {len(candidates)} {files}: {listed})"
        if self.kind == "listing":
            file_types = ", ".join(f".{suffix}" for suffix in self.details) or "any type"
            return f"{location}: lists files ({file_types})"
        return f"{location}: reads {self.target_file}"


def is_frozen_listing_holder(path: str) -> bool:
    """Say whether path sits inside a tools/m4-<name>/ or tools/x87-<name>/ folder."""
    for prefix in FROZEN_LISTING_HOLDERS:
        if not path.startswith(prefix):
            continue
        folder_and_rest = path[len(prefix) :].split("/", 1)
        has_folder_name = len(folder_and_rest) == 2 and folder_and_rest[0] != ""
        if has_folder_name:
            return True
    return False


def lint_finding_path(finding: str) -> str:
    """Return the file path at the start of a Ruff or PSScriptAnalyzer finding line.

    Ruff prints "path:line:col: CODE message" and check_powershell.ps1 prints
    "path:line Rule message". A drive letter's colon is followed by a slash, not a
    digit, so it stays part of the path.
    """
    path_then_line = re.match(r"(.+?):\d+", finding)
    return path_then_line.group(1) if path_then_line else finding


def is_code_file(path: str) -> bool:
    name = Path(path).name
    if name in ("CMakeLists.txt", "Makefile"):
        return True
    return Path(path).suffix.lower() in CODE_FILE_EXTENSIONS


def read_code_text(path: Path) -> str:
    """Read a code file as UTF-8, or as Latin-1 when it isn't valid UTF-8.

    A few frozen files predate UTF-8 and can't be re-saved (for example the Latin-1
    multiplication sign in tools/m4-141-consumer-review/named_loader141_v1.py). Latin-1
    maps every byte to a character, so the whole file is still searched, and the search
    patterns are plain ASCII, which reads the same in both encodings.
    """
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def list_all_tracked_files(repo_root: Path = REPO_ROOT) -> list[str]:
    """List all tracked files in the repository."""
    listing = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = [path for path in listing.stdout.split("\0") if path]
    return [path for path in tracked if (repo_root / path).is_file()]


def run_stored_hash_scan(
    changed_files: list[str],
    all_tracked_files: list[str],
    repo_root: Path = REPO_ROOT,
) -> list[StoredHashHit]:
    """Find any tracked file containing the SHA-256 of a file the formatter would change.

    Labels hits as identical copies or unresolved digest matches.
    """
    if not changed_files:
        return []

    targets: dict[str, tuple[int, str, bytes]] = {}
    for path in changed_files:
        path = normalize_repo_path(path)
        full_path = repo_root / path
        if not full_path.is_file():
            raise PreflightReadError(f"cannot read {path}: file is not available")
        try:
            content = full_path.read_bytes()
        except OSError as error:
            raise PreflightReadError(f"cannot read {path}: {error}") from error
        digest = hashlib.sha256(content).hexdigest().lower()
        targets[path] = (len(content), digest, content)

    if not targets:
        return []

    hits: list[StoredHashHit] = []
    for candidate in all_tracked_files:
        candidate_path = repo_root / candidate
        try:
            candidate_bytes = candidate_path.read_bytes()
        except OSError as error:
            raise PreflightReadError(f"cannot read {candidate}: {error}") from error
        candidate_size = len(candidate_bytes)
        candidate_digest: str | None = None

        for target_path, (target_size, target_hex, target_bytes) in targets.items():
            if candidate == target_path:
                continue

            # Compare original bytes so hash-string case normalization cannot affect copies.
            if candidate_size == target_size:
                if candidate_digest is None:
                    candidate_digest = hashlib.sha256(candidate_bytes).hexdigest().lower()
                if candidate_digest == target_hex and candidate_bytes == target_bytes:
                    hits.append(StoredHashHit(candidate, target_path, "identical copy"))
                    continue

            # A digest alone does not establish which path or copy a holder identifies.
            if target_hex.encode("ascii") in candidate_bytes.lower():
                hits.append(StoredHashHit(candidate, target_path, "unresolved digest match"))

    hits.sort(key=lambda h: (h.holding_file, h.target_file, h.label))
    return hits


def run_text_read_search(
    target_files: list[str],
    all_tracked_files: list[str],
    repo_root: Path = REPO_ROOT,
) -> list[TextReadHit]:
    """Search code files for reads, slices, or hashes of target language files."""
    if not target_files:
        return []

    normalized_targets = {normalize_repo_path(path) for path in target_files}
    target_names: dict[str, list[str]] = {}
    for path in sorted(normalized_targets):
        target_names.setdefault(PurePosixPath(path).name, []).append(path)
    target_paths = normalized_targets

    target_suffixes = {PurePosixPath(path).suffix.lower().lstrip(".") for path in target_paths}
    target_suffixes.discard("")
    if not target_suffixes:
        return []
    suffix_pattern = "|".join(re.escape(s) for s in sorted(target_suffixes))
    token_re = re.compile(r"[\w\-./\\]+\.(?:" + suffix_pattern + r")\b")
    inventory_suffix_re = re.compile(r"\*?\.(?:" + suffix_pattern + r")\b", re.IGNORECASE)

    code_candidates = [f for f in all_tracked_files if is_code_file(f)]
    hits: list[TextReadHit] = []
    seen: set[tuple[str, int, str, str]] = set()

    def add_hit(hit: TextReadHit) -> None:
        what = hit.target_file or ",".join(hit.details)
        key = (hit.holding_file, hit.line_number, hit.kind, what)
        if key not in seen:
            seen.add(key)
            hits.append(hit)

    def reported_directly(code_file: str, line_number: int, target: str) -> bool:
        return (code_file, line_number, "direct", target) in seen

    for code_file in code_candidates:
        full_code_path = repo_root / code_file
        try:
            content = read_code_text(full_code_path)
        except OSError as error:
            raise PreflightReadError(f"cannot read {code_file}: {error}") from error

        read_operation = READ_OPERATION_REGEX.search(content)
        if not read_operation:
            continue

        normalized_code_file = normalize_repo_path(code_file)
        self_references = list(SELF_PATH_REGEX.finditer(content))
        direct_self_references = []
        for self_reference in self_references:
            line_start = content.rfind("\n", 0, self_reference.start()) + 1
            line_end = content.find("\n", self_reference.start())
            if line_end == -1:
                line_end = len(content)
            if READ_OPERATION_REGEX.search(content[line_start:line_end]):
                direct_self_references.append(self_reference)
        selected_self_references = direct_self_references or self_references
        if selected_self_references and normalized_code_file in target_paths:
            for self_reference in selected_self_references:
                line_number = content.count("\n", 0, self_reference.start()) + 1
                add_hit(TextReadHit(code_file, line_number, "direct", normalized_code_file))

        if not is_frozen_listing_holder(normalized_code_file):
            # A listing can read any file of the types its script names anywhere, so
            # report each listing line once with those types rather than once per file.
            named_suffixes = {
                (match.group(1) or match.group(2)).lower()
                for match in LISTING_SUFFIX_REGEX.finditer(content)
            }
            # Also count target types named inside a file name ("a.py"), as before #214.
            named_suffixes |= {
                match.group(0).lstrip("*").lstrip(".").lower()
                for match in inventory_suffix_re.finditer(content)
            }
            reachable_suffixes = tuple(sorted(named_suffixes & target_suffixes))
            names_no_file_type = not named_suffixes
            if reachable_suffixes or names_no_file_type:
                listing_lines = {
                    content.count("\n", 0, match.start()) + 1
                    for match in DYNAMIC_INVENTORY_REGEX.finditer(content)
                }
                for listing_line in sorted(listing_lines):
                    add_hit(
                        TextReadHit(code_file, listing_line, "listing", details=reachable_suffixes)
                    )

        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if line_stripped.startswith(("#include", "import ", "from ")):
                continue

            tokens = token_re.findall(line)
            if not tokens:
                continue

            direct_targets = set()
            candidates_by_name: dict[str, set[str]] = {}
            for tok in tokens:
                tok_norm = tok.replace("\\", "/").rstrip("\"'")
                if tok_norm in target_paths:
                    direct_targets.add(tok_norm)
                    continue
                sibling_path = normalize_repo_path(
                    (PurePosixPath(code_file).parent / tok_norm).as_posix()
                )
                if sibling_path in target_paths:
                    direct_targets.add(sibling_path)
                    continue
                # Only a file name matched, which several files may share, and an
                # unchanged file with the same name may be the one meant.
                name = PurePosixPath(tok_norm).name
                if name in target_names:
                    candidates_by_name.setdefault(name, set()).update(target_names[name])

            for target_file in sorted(direct_targets):
                add_hit(TextReadHit(code_file, idx, "direct", target_file))
            for name, candidates in sorted(candidates_by_name.items()):
                not_yet_reported = [
                    candidate
                    for candidate in sorted(candidates)
                    if not reported_directly(code_file, idx, candidate)
                ]
                if not_yet_reported:
                    add_hit(TextReadHit(code_file, idx, "name", details=(name, *not_yet_reported)))

    hits.sort(key=TextReadHit.sort_key)
    return hits


def run_preflight(language: str, exclude_patterns: list[str], check_name: str = "format") -> int:
    """Run pre-cleanup safety checks for one language.

    check_name says which cleanup is coming: "format" scans the files the formatter
    would change, "lint" the files with lint findings.
    """
    if language not in LANGUAGES:
        print(f"preflight: error: unknown language {language!r}")
        return EXIT_TOOL_ERROR

    # Checked before the tool versions, so asking for a check a language lacks fails
    # the same way on every machine.
    check = LANGUAGES[language].checks.get(check_name)
    if check is None:
        print(f"preflight: {language}: error: no {check_name} check")
        return EXIT_TOOL_ERROR

    pins = read_pinned_versions()
    version_error = version_error_for(language, pins)
    if version_error:
        print(f"preflight: {language}: error: {version_error}")
        return EXIT_TOOL_ERROR

    all_tracked = list_all_tracked_files(REPO_ROOT)
    target_files = list_files(LANGUAGES[language].suffixes, exclude_patterns)

    result = run_check(language, check_name, check, target_files)
    if result.error:
        print(f"preflight: {language} {check_name}: error: {result.error}")
        return EXIT_TOOL_ERROR
    # The files the coming cleanup will change: reformatted ones, or ones with lint findings.
    if check_name == "lint":
        target_paths = [lint_finding_path(finding) for finding in result.findings]
    else:
        target_paths = result.findings
    scan_targets = sorted({normalize_repo_path(path) for path in target_paths})
    try:
        hash_hits = run_stored_hash_scan(scan_targets, all_tracked, REPO_ROOT)
    except PreflightReadError as error:
        print(f"preflight: {language}: stored-hash scan: error: {error}")
        return EXIT_TOOL_ERROR
    print(f"preflight: {language}: stored-hash scan: {len(hash_hits):,} findings")
    for hit in hash_hits:
        print(f"  {hit.describe()}")

    try:
        text_hits = run_text_read_search(scan_targets, all_tracked, REPO_ROOT)
    except PreflightReadError as error:
        print(f"preflight: {language}: text-read search: error: {error}")
        return EXIT_TOOL_ERROR
    kind_counts = [sum(1 for hit in text_hits if hit.kind == kind) for kind in TEXT_READ_KINDS]
    direct_count, name_count, listing_count = kind_counts
    print(
        f"preflight: {language}: text-read search: {len(text_hits):,} findings "
        f"({direct_count:,} direct, {name_count:,} name matches, "
        f"{listing_count:,} folder listings)"
    )
    for hit in text_hits:
        print(f"  {hit.describe()}")

    return EXIT_CLEAN


# ---------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--language", action="append", choices=sorted(LANGUAGES))
    parser.add_argument("--check", choices=["format", "lint"])
    parser.add_argument("--fix", action="store_true", help="format enforced languages in place")
    parser.add_argument(
        "--files", nargs="+", help="with --fix, format only these files (paths from the root)"
    )
    parser.add_argument("--list", action="store_true", help="print the files each language checks")
    parser.add_argument(
        "--preflight", action="store_true", help="run pre-cleanup safety checks for one language"
    )
    parser.add_argument("--verbose", action="store_true", help="print every file or finding")
    return parser.parse_args(argv)


def selected_checks(arguments: argparse.Namespace) -> Iterator[tuple[str, str, Check]]:
    """Yield (language, check name, check) for everything the arguments ask for."""
    for language in arguments.language or sorted(LANGUAGES):
        for check_name, check in LANGUAGES[language].checks.items():
            if arguments.check in (None, check_name):
                yield language, check_name, check


def fix_enforced(arguments: argparse.Namespace, exclude_patterns: list[str]) -> int:
    """Rewrite files for enforced formatters only; never apply lint fixes.

    With --files, only the given files are formatted, and only those a full run would
    format (same suffixes and exclusions). A language with none of them is skipped
    without a word, so the git hook never reports a formatter the commit doesn't need.
    """
    pins = read_pinned_versions()
    wanted_files = None
    if arguments.files:
        wanted_files = {normalize_repo_path(path) for path in arguments.files}
    exit_code = EXIT_CLEAN
    for language, check_name, check in selected_checks(arguments):
        if not check.can_fix:
            continue
        if not is_enforced(language, check_name):
            if wanted_files is None:
                print(f"{language} {check_name}: skipped, its cleanup has not landed yet")
            continue
        paths = list_files(LANGUAGES[language].suffixes, exclude_patterns)
        if wanted_files is not None:
            paths = [path for path in paths if path in wanted_files]
            if not paths:
                continue
        # A different formatter version would lay files out differently from CI.
        version_error = version_error_for(language, pins)
        if version_error:
            print(f"{language} {check_name}: error: {version_error}")
            exit_code = EXIT_TOOL_ERROR
            continue
        failed_run = None
        for batch in in_batches(paths):
            tool_run = check.run(batch, True)
            if tool_run.exit_code != 0:
                failed_run = tool_run
                break
        if failed_run:
            print(f"{language} {check_name}: error: {short_error(failed_run)}")
            exit_code = EXIT_TOOL_ERROR
        else:
            print(f"{language} {check_name}: formatted {len(paths):,} files")
    return exit_code


def main(argv: list[str]) -> int:
    arguments = parse_arguments(argv)
    exclude_patterns, drift = load_exclusions()
    if drift:
        for problem in drift:
            print(f"exclusions: error: {problem}")
        return EXIT_TOOL_ERROR

    if arguments.files and not arguments.fix:
        print("files: error: --files only works with --fix")
        return EXIT_TOOL_ERROR

    if arguments.preflight:
        if arguments.list:
            print("preflight: error: --preflight cannot be combined with --list")
            return EXIT_TOOL_ERROR
        if not arguments.language or len(arguments.language) != 1:
            print("preflight: error: --preflight requires exactly one --language")
            return EXIT_TOOL_ERROR
        return run_preflight(arguments.language[0], exclude_patterns, arguments.check or "format")

    if arguments.list:
        for language in arguments.language or sorted(LANGUAGES):
            for path in list_files(LANGUAGES[language].suffixes, exclude_patterns):
                print(f"{language}\t{path}")
        return EXIT_CLEAN

    if arguments.fix:
        return fix_enforced(arguments, exclude_patterns)

    pins = read_pinned_versions()
    results = []
    for language, check_name, check in selected_checks(arguments):
        version_error = version_error_for(language, pins)
        if version_error:
            enforced = is_enforced(language, check_name)
            result = CheckResult(language, check_name, enforced, 0, error=version_error)
        else:
            paths = list_files(LANGUAGES[language].suffixes, exclude_patterns)
            result = run_check(language, check_name, check, paths)
        results.append(result)
        print(describe(result))
        if arguments.verbose:
            for finding in result.findings:
                print(f"    {finding}")

    write_github_summary(results)
    print_github_warnings(results)
    return overall_exit_code(results)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
