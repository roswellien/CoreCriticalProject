"""Copy the shared agent skills from `.agents/skills/` into `.claude/skills/`.

Shared skills are written only in `.agents/skills/`, which Codex, Cursor and
Copilot read. Claude Code reads skills only from `.claude/skills/`, and a symlink
between the two would check out as a plain text file on Windows, so this script
keeps a real copy instead. `tools/agents/check_agent_files.py` fails when the copy
drifts from its source.

Only `core-critical-*` skill folders are managed. Any other folder in
`.claude/skills/` is a contributor's own Claude Code skill and is left alone.
A copy file with no source is removed only when git tracks it, so git can bring
it back.

Exit codes: 0 when the copy matches its source (after any changes), 1 when the
script stopped without changing anything.
"""

from __future__ import annotations

import os
import shutil
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


def sync(root: Path, tracked_paths: list[str]) -> list[str]:
    """Mirror the shared skills under `root` into the Claude Code copy; return one line per change.

    `tracked_paths` are the files git tracks under `root`, with forward slashes.
    """
    source = root / SKILL_SOURCE
    copy = root / SKILL_COPY
    if not source.is_dir():
        raise SyncStopped(f"{SKILL_SOURCE}/ is missing, so there is nothing to copy from.")
    _refuse_links(root)

    source_files = _shared_skill_files(source)
    copy_files = _shared_skill_files(copy)
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


def _shared_skill_files(skills_folder: Path) -> dict[str, Path]:
    """Map each file in the folder's `core-critical-*` skills to its path relative to the folder."""
    files: dict[str, Path] = {}
    for skill_folder in _shared_skill_folders(skills_folder):
        # os.walk rather than Path.walk, which needs Python 3.12; CI runs 3.11.
        for folder, _, file_names in os.walk(skill_folder):
            for file_name in file_names:
                path = Path(folder) / file_name
                files[path.relative_to(skills_folder).as_posix()] = path
    return files


def _shared_skill_folders(skills_folder: Path) -> list[Path]:
    if not skills_folder.is_dir():
        return []
    return sorted(
        child
        for child in skills_folder.iterdir()
        if child.is_dir() and child.name.startswith(SKILL_PREFIX)
    )


def _refuse_links(root: Path) -> None:
    """Stop when the copy, or anything in its shared skills, is a link to somewhere else.

    Someone may have linked the folders by hand instead of running this script;
    copying through such a link would write a folder onto itself. os.path.realpath
    follows both symlinks and Windows junctions (Python 3.11 has no
    Path.is_junction), so a path whose real location differs from where it sits
    under the copy's real location passes through a link.
    """
    copy = root / SKILL_COPY
    if not copy.exists():
        return
    expected_copy = os.path.join(os.path.realpath(copy.parent), copy.name)
    paths_to_check = [(copy, expected_copy)]
    real_copy = os.path.realpath(copy)
    for skill_folder in _shared_skill_folders(copy):
        # The skill folder first, so a linked folder is named rather than a file in it.
        paths_to_check.append((skill_folder, os.path.join(real_copy, skill_folder.name)))
        for folder, folder_names, file_names in os.walk(skill_folder):
            for name in [*folder_names, *file_names]:
                path = Path(folder) / name
                expected = os.path.join(real_copy, *path.relative_to(copy).parts)
                paths_to_check.append((path, expected))

    for path, expected in paths_to_check:
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


def main() -> int:
    try:
        changes = sync(REPO_ROOT, tracked_paths_from_git(REPO_ROOT))
    except GitUnavailable as reason:
        print(f"error: can't list tracked files ({reason}); run this inside a git checkout.")
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
