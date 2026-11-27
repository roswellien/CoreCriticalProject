"""Copy the shared agent skills from `.agents/skills/` into `.claude/skills/`.

Shared skills are written only in `.agents/skills/`, which Codex, Cursor and
Copilot read. Claude Code reads skills only from `.claude/skills/`, and a symlink
between the two would check out as a plain text file on Windows, so this script
keeps a real copy instead. `tools/agents/check_agent_files.py` fails when the copy
drifts from its source.

Only `core-critical-*` skill folders are managed. Any other folder in
`.claude/skills/` is a contributor's own Claude Code skill and is left alone.
A copy file with no source is removed only when git tracks it, so git can bring
it back. Git ignores OS litter and build artifacts (such as Thumbs.db, desktop.ini
or __pycache__ folders); sync skips them on both sides so they are neither copied
nor removed.

Exit codes: 0 when the copy matches its source (after any changes), 1 when the
script stopped without changing anything.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from check_agent_files import (
    REPO_ROOT,
    SKILL_COPY,
    SKILL_PREFIX,
    SKILL_SOURCE,
    GitUnavailable,
    tracked_paths_from_git,
)


class SyncStopped(Exception):
    """Raised, before anything changes, when copying would lose or corrupt work."""


def sync(
    root: Path,
    tracked_paths: list[str],
    ignored_paths: frozenset[str] = frozenset(),
) -> list[str]:
    """Mirror shared skills under `root` into the Claude Code copy; return one line per change.

    `tracked_paths` are the files git tracks under `root`, with forward slashes.
    `ignored_paths` are repository-relative paths git ignores, with forward slashes.
    Ignored files and files under ignored folders (such as Thumbs.db, desktop.ini or
    __pycache__) are excluded from both source and copy: never copied, never removed,
    and never a reason to stop.
    """
    source = root / SKILL_SOURCE
    copy = root / SKILL_COPY
    if not source.is_dir():
        raise SyncStopped(f"{SKILL_SOURCE}/ is missing, so there is nothing to copy from.")
    _refuse_links(root)

    source_files = _shared_skill_files(source, SKILL_SOURCE, ignored_paths)
    copy_files = _shared_skill_files(copy, SKILL_COPY, ignored_paths)
    _refuse_edited_copies(source_files, copy_files)
    _refuse_untracked_removals(source_files, copy_files, tracked_paths)

    changes = []
    for relative_path, source_file in sorted(source_files.items()):
        copy_file = copy / relative_path
        if relative_path not in copy_files:
            action = "added"
        elif source_file.read_bytes() != copy_file.read_bytes():
            action = "updated"
        else:
            continue
        copy_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_file, copy_file)
        changes.append(f"{action} {SKILL_COPY}/{relative_path}")

    for relative_path in sorted(copy_files.keys() - source_files.keys()):
        copy_files[relative_path].unlink()
        changes.append(f"removed {SKILL_COPY}/{relative_path}")
    _remove_empty_folders(copy)
    return changes


def _shared_skill_files(
    skills_folder: Path, prefix: str = "", ignored_paths: frozenset[str] = frozenset()
) -> dict[str, Path]:
    """Map each file in the folder's `core-critical-*` skills to its path relative to the folder.

    Files in `ignored_paths` or under an ignored folder are left out so OS litter
    (such as Thumbs.db, desktop.ini or __pycache__) is not synced or checked.
    """
    prefix = prefix or f"{skills_folder.parent.name}/{skills_folder.name}"
    files: dict[str, Path] = {}
    normalized_ignored = {path.rstrip("/") for path in ignored_paths if path.rstrip("/")}
    for skill_folder in _shared_skill_folders(skills_folder):
        # os.walk rather than Path.walk, which needs Python 3.12; CI runs 3.11.
        for folder, _, file_names in os.walk(skill_folder):
            for file_name in file_names:
                path = Path(folder) / file_name
                relative_path = path.relative_to(skills_folder).as_posix()
                repo_relative_path = f"{prefix}/{relative_path}"
                if _is_ignored(repo_relative_path, normalized_ignored):
                    continue
                files[relative_path] = path
    return files


def _is_ignored(repo_relative_path: str, normalized_ignored: set[str]) -> bool:
    """Return whether `repo_relative_path` or any parent folder is in `normalized_ignored`.

    Git-ignored files (such as Thumbs.db or desktop.ini) and ignored folders (such
    as __pycache__) should be excluded from sync.
    """
    if not normalized_ignored:
        return False
    if repo_relative_path in normalized_ignored:
        return True
    parts = repo_relative_path.split("/")[:-1]
    for depth in range(1, len(parts) + 1):
        if "/".join(parts[:depth]) in normalized_ignored:
            return True
    return False


def _shared_skill_folders(skills_folder: Path) -> list[Path]:
    if not skills_folder.is_dir():
        return []
    return sorted(
        child
        for child in skills_folder.iterdir()
        if child.is_dir() and child.name.startswith(SKILL_PREFIX)
    )


def _refuse_links(root: Path) -> None:
    """Stop when either skills folder, or anything in their shared skills, is a link.

    Someone may have linked the folders by hand instead of running this script.
    Copying through a link on the copy side would write a folder onto itself, and
    a link on the source side would be copied as a real file, hiding the link.
    os.path.realpath follows both symlinks and Windows junctions (Python 3.11 has
    no Path.is_junction), so a path whose real location differs from where it sits
    under the repository's real location passes through a link, including a linked
    `.claude` or `.agents` folder.
    """
    real_root = os.path.realpath(root)
    for skills_name in (SKILL_SOURCE, SKILL_COPY):
        skills_folder = root / skills_name
        if not skills_folder.exists():
            continue
        paths_to_check = [skills_folder]
        for skill_folder in _shared_skill_folders(skills_folder):
            # The skill folder first, so a linked folder is named rather than a file in it.
            paths_to_check.append(skill_folder)
            for folder, folder_names, file_names in os.walk(skill_folder):
                paths_to_check += [Path(folder) / name for name in [*folder_names, *file_names]]

        for path in paths_to_check:
            expected = os.path.join(real_root, *path.relative_to(root).parts)
            if os.path.normcase(os.path.realpath(path)) != os.path.normcase(expected):
                raise SyncStopped(
                    f"{path.relative_to(root).as_posix()} is a link; replace it with a real "
                    "folder or file, then rerun."
                )


def _refuse_edited_copies(source_files: dict[str, Path], copy_files: dict[str, Path]) -> None:
    """Stop when a copy file was changed after its source, so copying would undo that edit.

    Claude Code's own tools write skills into `.claude/skills/`, so an edit there is
    easy to make by mistake.
    """
    edited = []
    for relative_path in sorted(source_files.keys() & copy_files.keys()):
        source_file = source_files[relative_path]
        copy_file = copy_files[relative_path]
        copy_is_newer = copy_file.stat().st_mtime_ns > source_file.stat().st_mtime_ns
        if copy_is_newer and source_file.read_bytes() != copy_file.read_bytes():
            edited.append(f"{SKILL_COPY}/{relative_path}")
    if edited:
        raise SyncStopped(
            f"{', '.join(edited)} changed after its source in {SKILL_SOURCE}/; move the change "
            f"into {SKILL_SOURCE}/, or delete the copy file to discard it, then rerun."
        )


def _refuse_untracked_removals(
    source_files: dict[str, Path], copy_files: dict[str, Path], tracked_paths: list[str]
) -> None:
    """Stop when a copy file has no source and git doesn't track it, so removing it would lose it.

    Claude Code creates new skills in `.claude/skills/`, so a new shared skill can
    start there by mistake. Git can bring back a tracked file, not an untracked one.
    """
    tracked = set(tracked_paths)
    untracked = [
        f"{SKILL_COPY}/{relative_path}"
        for relative_path in sorted(copy_files.keys() - source_files.keys())
        if f"{SKILL_COPY}/{relative_path}" not in tracked
    ]
    if untracked:
        raise SyncStopped(
            f"{', '.join(untracked)} has no source in {SKILL_SOURCE}/ and isn't tracked, so "
            f"removing it would lose it; move it into {SKILL_SOURCE}/, where new shared skills "
            "go, or delete it to discard it, then rerun."
        )


def _remove_empty_folders(copy: Path) -> None:
    for skill_folder in _shared_skill_folders(copy):
        # Bottom-up, so a folder emptied by removing its subfolders goes too.
        for folder, _, _ in os.walk(skill_folder, topdown=False):
            if not os.listdir(folder):
                os.rmdir(folder)


def ignored_paths_from_git(root: Path) -> frozenset[str]:
    """Return every git-ignored untracked path under `.agents/skills` and `.claude/skills`.

    Git ignores OS litter and build artifacts (such as Thumbs.db, desktop.ini, or
    __pycache__ folders). Listing them allows sync to skip copying or removing them.
    """
    try:
        result = subprocess.run(
            [
                "git",
                "ls-files",
                "--others",
                "--ignored",
                "--exclude-standard",
                "--",
                SKILL_SOURCE,
                SKILL_COPY,
            ],
            cwd=root,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as missing_git:
        raise GitUnavailable("git is not on PATH") from missing_git
    if result.returncode != 0:
        raise GitUnavailable(result.stderr.decode("utf-8", errors="replace").strip())
    return frozenset(path for path in result.stdout.decode("utf-8").splitlines() if path)


def main() -> int:
    try:
        tracked_paths = tracked_paths_from_git(REPO_ROOT)
        ignored_paths = ignored_paths_from_git(REPO_ROOT)
        changes = sync(REPO_ROOT, tracked_paths, ignored_paths)
    except GitUnavailable as reason:
        print(f"error: can't list files from git ({reason}); run this inside a git checkout.")
        return 1
    except SyncStopped as reason:
        print(f"error: {reason}")
        return 1
    for change in changes:
        print(change)
    if not changes:
        print(f"{SKILL_COPY}/ already matches {SKILL_SOURCE}/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
