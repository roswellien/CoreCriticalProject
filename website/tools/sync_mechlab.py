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


# Topic tags shown on MechLab cards and used by the /news filter. A fixed list keeps
# the filter short and stops near-duplicates ("Renderer" vs "Rendering") creeping in.
CARD_TAGS = ("Renderer", "Native", "Launcher", "Playtest", "Tools", "Content", "Website", "Fix")
MAX_TAGS = 3

# Card thumbnails must be existing WebP files under website/assets/plates, given as a
# plain relative path, so a note can never point the page at another site or folder.
IMAGE_PATTERN = re.compile(r"[a-z0-9_-]+(/[a-z0-9_-]+)*\.webp")


def read_card_details(note_name: str, lines: list[str]) -> tuple[list[str], str, int]:
    """Read the optional "Tags:" and "Image:" lines directly under the title.

    Returns the tags, the image path ("" when there is none) and the index of the
    first line of the summary itself.
    """
    tags: list[str] = []
    image = ""
    line_index = 1
    while line_index < len(lines):
        line = lines[line_index].strip()
        if line.startswith("Tags:"):
            tags = [tag.strip() for tag in line[len("Tags:") :].split(",") if tag.strip()]
        elif line.startswith("Image:"):
            image = line[len("Image:") :].strip()
        else:
            break
        line_index += 1

    unknown_tags = [tag for tag in tags if tag not in CARD_TAGS]
    if unknown_tags:
        allowed = ", ".join(CARD_TAGS)
        raise ValueError(f"{note_name} has unknown tags {unknown_tags}; use: {allowed}")
    if len(tags) > MAX_TAGS or len(set(tags)) != len(tags):
        raise ValueError(f"{note_name} needs at most {MAX_TAGS} distinct tags")
    if image and not IMAGE_PATTERN.fullmatch(image):
        raise ValueError(f"{note_name} image must be a .webp path under assets/plates")
    return tags, image, line_index


def parse_note(path: Path, repository_root: Path) -> dict:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}\.md", path.name):
        raise ValueError("Daily notes must be named YYYY-MM-DD.md")
    day = date.fromisoformat(path.stem).isoformat()
    lines = path.read_text(encoding="utf-8").replace("\r\n", "\n").strip().splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError(f"{path.name} needs a # title")
    title = lines[0][2:].strip()
    tags, image, content_start = read_card_details(path.name, lines)
    body = "\n".join(lines[content_start:]).strip()
    if not title or len(title) > 180 or not body:
        raise ValueError(f"{path.name} needs a title and public summary text")

    opening_lines = []
    for line in lines[content_start:]:
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
        "tags": tags,
        "image": image,
        "commit": source_commit(repository_root, path),
    }


def read_notes(source: Path, repository_root: Path) -> list[dict]:
    if not source.is_dir():
        raise FileNotFoundError(f"MechLab note directory not found: {source}")
    notes = [parse_note(path, repository_root) for path in source.glob("????-??-??.md")]
    if not notes:
        raise ValueError(f"No public daily notes found in {source}")
    notes.sort(key=lambda note: note["date"], reverse=True)
    return notes
