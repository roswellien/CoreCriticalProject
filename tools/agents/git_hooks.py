"""Git hooks that format and guard commits and keep pushes off main and develop.

Turn them on once per clone with `git config core.hooksPath .githooks`. The shims in
`.githooks/` find Python 3.11 or later and run this file with the hook's name. Git
runs hooks from the top of the worktree, so the current directory is the repository.

pre-commit, in order:

1. Blocks staged files that .gitignore covers. Original game files, executables,
   media, dumps and keys are all listed there and must never be committed.
2. Formats the staged files with every formatter switched on in
   `tools/style/check_style.py`, then stages the result, so pushes stop failing CI's
   style check. Formatting never blocks a commit: a formatter that is missing, the
   wrong version or fails is reported, the commit goes ahead, and CI still catches
   what is left. Two kinds of commit are left unformatted, with a note:
   - a file with only part of its changes staged, because formatting it and staging
     the result would also stage the changes that were left out;
   - `git commit <paths>`, because git commits those from a temporary index and keeps
     the unformatted copy in the real one, so the next commit would undo the formatting.
3. Runs `tools/agents/check_agent_files.py` and blocks the commit if it fails. That
   check reads files on disk, so a partly staged AGENTS.md is checked as it is on
   disk. When it blocks, the files already formatted and staged stay that way.

pre-push blocks any push to main or develop, on every remote (a contributor's own
fork included): those branches change only through pull requests, as
docs/github-workflow.md says.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path

# The same batch size as check_style.py's FILES_PER_CALL: a Windows command line holds
# about 32,000 characters, and a merge commit can stage hundreds of files.
FILES_PER_CALL = 100

PROTECTED_BRANCHES = ("refs/heads/main", "refs/heads/develop")

# What to run when a formatter is missing or the wrong version, from "Setup" in
# tools/style/README.md. Ruff (Python) and clang-format (C++) share one install.
_PIP_INSTALL = (
    "python -m venv tools/style/.venv, then tools/style/.venv/Scripts/python -m pip "
    "install --require-hashes -r tools/style/requirements.txt (bin/ instead of Scripts/ "
    "on Linux and macOS)"
)
INSTALL_COMMANDS = {
    "web": "npm ci --prefix tools/style",
    "python": _PIP_INSTALL,
    "cpp": _PIP_INSTALL,
    "csharp": "install a .NET 8 SDK (dotnet format comes with it)",
    "powershell": "pwsh -File tools/style/check_powershell.ps1 -Mode Install",
}

# check_style.py prints "<language> format: error: <reason>" for a formatter it couldn't run.
FORMATTER_ERROR_LINE = re.compile(r"^(\w+) format: error:", re.MULTILINE)

Environment = Mapping[str, str]
Formatter = Callable[[Path, list[str], Environment], subprocess.CompletedProcess[str]]
AgentCheck = Callable[[Path, Environment], subprocess.CompletedProcess[str]]


class GitFailed(Exception):
    """A git command the hook relies on failed, so the hook can't tell what is staged."""


def run(
    command: list[str], root: Path, environment: Environment, stdin_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=root,
        env=dict(environment),
        input=stdin_text,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        # Callers read the exit code; check-ignore, for one, uses 1 for "nothing ignored".
        check=False,
    )


def git(root: Path, environment: Environment, *arguments: str) -> str:
    result = run(["git", *arguments], root, environment)
    if result.returncode != 0:
        raise GitFailed(f"git {' '.join(arguments)}: {result.stderr.strip()}")
    return result.stdout


def split_nul(output: str) -> list[str]:
    """Split git's -z output, which keeps unusual file names unquoted."""
    return [path for path in output.split("\0") if path]


def in_batches(paths: list[str]) -> list[list[str]]:
    return [paths[start : start + FILES_PER_CALL] for start in range(0, len(paths), FILES_PER_CALL)]


def run_formatter(
    root: Path, paths: list[str], environment: Environment
) -> subprocess.CompletedProcess[str]:
    check_style = str(root / "tools/style/check_style.py")
    return run([sys.executable, check_style, "--fix", "--files", *paths], root, environment)


def run_agent_check(root: Path, environment: Environment) -> subprocess.CompletedProcess[str]:
    check_agent_files = str(root / "tools/agents/check_agent_files.py")
    return run([sys.executable, check_agent_files], root, environment)


# ---------------------------------------------------------------------------------------
# pre-commit
# ---------------------------------------------------------------------------------------


def ignored_staged_files(root: Path, environment: Environment, staged: list[str]) -> list[str]:
    """Return one line per staged file that an ignore rule covers, naming the rule."""
    # --no-index checks the rules even for files already added; -v names the matching rule,
    # which may also come from the contributor's own core.excludesFile or .git/info/exclude.
    result = run(
        ["git", "check-ignore", "--no-index", "-v", "-z", "--stdin"],
        root,
        environment,
        stdin_text="\0".join(staged) + "\0",
    )
    nothing_ignored = result.returncode == 1
    if nothing_ignored:
        return []
    if result.returncode != 0:
        raise GitFailed(f"git check-ignore: {result.stderr.strip()}")
    # With -v -z each match is four fields: source, line number, pattern, path.
    fields = result.stdout.split("\0")
    lines = []
    for start in range(0, len(fields) - 3, 4):
        source, line_number, pattern, path = fields[start : start + 4]
        lines.append(f"{path} (rule '{pattern}' in {source}:{line_number})")
    return lines


def commits_from_temporary_index(root: Path, environment: Environment) -> bool:
    """Return whether this commit is `git commit <paths>`, which uses a temporary index.

    Git sets GIT_INDEX_FILE for every hook: the real index for a plain commit, its
    index.lock for `git commit -a`, and a next-index-<pid>.lock file for a commit of
    named paths. `git rev-parse --git-path index` can't tell them apart, because it
    returns GIT_INDEX_FILE itself when that is set.
    """
    index_file = environment.get("GIT_INDEX_FILE")
    if not index_file:
        return False
    git_folder = Path(git(root, environment, "rev-parse", "--absolute-git-dir").strip())
    real_index_files = {
        (git_folder / "index").resolve(),
        (git_folder / "index.lock").resolve(),
    }
    # A relative GIT_INDEX_FILE is relative to the top of the worktree.
    index_path = Path(index_file)
    if not index_path.is_absolute():
        index_path = root / index_path
    return index_path.resolve() not in real_index_files


def format_staged_files(
    root: Path, environment: Environment, paths: list[str], formatter: Formatter
) -> None:
    """Format `paths` in batches and stage the result; report, never raise, a formatter failure."""
    formatter_failed = False
    output = ""
    for batch in in_batches(paths):
        result = formatter(root, batch, environment)
        output += result.stdout + result.stderr
        if result.returncode != 0:
            formatter_failed = True
    if output.strip():
        print(output.rstrip())
    if formatter_failed:
        print(
            "pre-commit: the commit goes ahead; CI's style check will flag anything left "
            "unformatted."
        )
        for language in sorted(set(FORMATTER_ERROR_LINE.findall(output))):
            if language in INSTALL_COMMANDS:
                print(f"pre-commit: to format {language} files, {INSTALL_COMMANDS[language]}.")
    # A file the formatter left alone is staged again unchanged, which does nothing.
    for batch in in_batches(paths):
        git(root, environment, "add", "--", *batch)


def pre_commit(
    root: Path,
    environment: Environment | None = None,
    formatter: Formatter = run_formatter,
    agent_check: AgentCheck = run_agent_check,
) -> int:
    environment = os.environ if environment is None else environment
    staged = split_nul(
        git(root, environment, "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR")
    )
    if not staged:
        return 0

    ignored = ignored_staged_files(root, environment, staged)
    if ignored:
        for line in ignored:
            print(f"pre-commit: blocked: {line}")
        print(
            "pre-commit: .gitignore covers these files, so they must not be committed (game "
            "files, media, dumps and keys stay local); unstage each with "
            "`git restore --staged <path>`."
        )
        return 1

    if commits_from_temporary_index(root, environment):
        print(
            "pre-commit: not formatted, because `git commit <paths>` commits from a "
            "temporary index; stage the files with `git add` and run `git commit` to have "
            "them formatted."
        )
    else:
        partly_staged = set(split_nul(git(root, environment, "diff", "--name-only", "-z")))
        to_format = []
        for path in staged:
            if path in partly_staged:
                print(
                    f"pre-commit: not formatted, because only part of its changes are staged: {path}"
                )
            elif (root / path).is_file():
                to_format.append(path)
        if to_format:
            format_staged_files(root, environment, to_format, formatter)

    agent_result = agent_check(root, environment)
    if agent_result.returncode != 0:
        print((agent_result.stdout + agent_result.stderr).rstrip())
        print("pre-commit: blocked by tools/agents/check_agent_files.py; fix the errors above.")
        return 1
    return 0


# ---------------------------------------------------------------------------------------
# pre-push
# ---------------------------------------------------------------------------------------


def pre_push(stdin_text: str) -> int:
    """Block a push whose target is main or develop; git passes one line per ref."""
    # Each line: <local ref> <local sha> <remote ref> <remote sha>.
    blocked = []
    for line in stdin_text.splitlines():
        fields = line.split()
        if len(fields) == 4 and fields[2] in PROTECTED_BRANCHES:
            blocked.append(fields[2])
    if blocked:
        for remote_ref in blocked:
            print(f"pre-push: blocked: a push to {remote_ref}")
        print(
            "pre-push: pushes to main and develop go through a pull request "
            "(see docs/github-workflow.md)."
        )
        return 1
    return 0


def main(argv: list[str]) -> int:
    hook = argv[0] if argv else ""
    try:
        if hook == "pre-commit":
            return pre_commit(Path.cwd())
        if hook == "pre-push":
            return pre_push(sys.stdin.read())
    except GitFailed as failure:
        print(f"{hook}: error: {failure}")
        return 1
    print(f"git_hooks.py: unknown hook {hook!r}; expected pre-commit or pre-push.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
