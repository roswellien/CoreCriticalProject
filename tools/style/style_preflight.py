"""Pre-cleanup safety scans for check_style.py --preflight.

Before a language's one-time cleanup reformats or lint-fixes files, these scans look for
anything that depends on those files' exact bytes: tracked files holding a file's hash or
an identical copy (the stored-hash scan), and code that reads, slices or hashes a file
as text (the text-read search). check_style.py's run_preflight picks the files and prints
what the scans find; tools/style/README.md says how to handle each kind of hit.
"""

from __future__ import annotations

import hashlib
import posixpath
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[2]

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
