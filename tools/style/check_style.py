"""Run the project's style checkers and count what they find.

Usage, from the repository root:
    python tools/style/check_style.py           report every language and check
    python tools/style/check_style.py --fix     format the languages whose cleanup has landed
    python tools/style/check_style.py --list    show which files each language checks

Setup, the pinned tool versions and the rollout plan are in tools/style/README.md. The
rules themselves are in CODE_STYLE.md.

A check is "report only" until it is listed in ENFORCED below. Report-only findings are
printed but never fail the run. An enforced check with findings exits 1. A checker that
is missing, the wrong version or crashed exits 2, because a broken checker must never
look like a clean result.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

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
# Main
# ---------------------------------------------------------------------------------------


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--language", action="append", choices=sorted(LANGUAGES))
    parser.add_argument("--check", choices=["format", "lint"])
    parser.add_argument("--fix", action="store_true", help="format enforced languages in place")
    parser.add_argument("--list", action="store_true", help="print the files each language checks")
    parser.add_argument("--verbose", action="store_true", help="print every file or finding")
    return parser.parse_args(argv)


def selected_checks(arguments: argparse.Namespace) -> Iterator[tuple[str, str, Check]]:
    """Yield (language, check name, check) for everything the arguments ask for."""
    for language in arguments.language or sorted(LANGUAGES):
        for check_name, check in LANGUAGES[language].checks.items():
            if arguments.check in (None, check_name):
                yield language, check_name, check


def fix_enforced(arguments: argparse.Namespace, exclude_patterns: list[str]) -> int:
    """Rewrite files for enforced formatters only; never apply lint fixes."""
    pins = read_pinned_versions()
    exit_code = EXIT_CLEAN
    for language, check_name, check in selected_checks(arguments):
        if not check.can_fix:
            continue
        if not is_enforced(language, check_name):
            print(f"{language} {check_name}: skipped, its cleanup has not landed yet")
            continue
        # A different formatter version would lay files out differently from CI.
        version_error = version_error_for(language, pins)
        if version_error:
            print(f"{language} {check_name}: error: {version_error}")
            exit_code = EXIT_TOOL_ERROR
            continue
        paths = list_files(LANGUAGES[language].suffixes, exclude_patterns)
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
