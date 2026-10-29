"""Read public MechLab notes from this repository for the site build."""
from datetime import date
import os
from pathlib import Path
import re
import subprocess


def source_commit(repository_root: Path, note_path: Path) -> str:
    relative_path = note_path.relative_to(repository_root).as_posix()
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", relative_path],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    match = re.search(r"\b[0-9a-f]{40}\b", result.stdout)
    if match:
        return match.group(0)

    for variable in ("CF_PAGES_COMMIT_SHA", "GITHUB_SHA"):
        commit = os.environ.get(variable, "")
        if re.fullmatch(r"[0-9a-f]{40}", commit):
            return commit

    current = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    commit = current.stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Could not determine a source commit for a public summary")
    return commit


def parse_note(path: Path, repository_root: Path) -> dict[str, str]:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}\.md", path.name):
        raise ValueError("Daily notes must be named YYYY-MM-DD.md")
    day = date.fromisoformat(path.stem).isoformat()
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").strip().splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError(f"{path.name} needs a # title")
    title = lines[0][2:].strip()
    body = "\n".join(lines[1:]).strip()
    if not title or len(title) > 180 or not body:
        raise ValueError(f"{path.name} needs a title and public summary text")

    opening_lines = []
    for line in lines[1:]:
        if not line.strip():
            if opening_lines:
                break
            continue
        opening_lines.append(line.strip())
    excerpt = " ".join(opening_lines)
    if excerpt.startswith(("#", "- ")) or len(excerpt) > 600:
        raise ValueError(f"{path.name} needs a plain opening paragraph of at most 600 characters")

    return {
        "date": day,
        "title": title,
        "excerpt": excerpt,
        "body": body,
        "commit": source_commit(repository_root, path),
    }


def read_notes(source: Path, repository_root: Path) -> list[dict[str, str]]:
    if not source.is_dir():
        raise FileNotFoundError(f"MechLab note directory not found: {source}")
    notes = [parse_note(path, repository_root) for path in source.glob("????-??-??.md")]
    if not notes:
        raise ValueError(f"No public daily notes found in {source}")
    notes.sort(key=lambda note: note["date"], reverse=True)
    return notes
