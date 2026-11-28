"""Build a schema version 3 content pack archive from a folder of authored content.

Usage, from the repository root:
    python games/mw3/mod-tools/pack_builder.py <source folder> [output folder]

The source folder holds a `pack.json` without `files` or `provides` — the builder
writes both — plus the pack's payload files. The builder assembles a copy in a
temporary folder, runs the contract 1 check from tools/packs/check_pack.py on it,
and only when that check is clean writes `<id>-<version>.mw3pack` into the output
folder (the current folder by default).

The source folder is never modified, and the output file must not already exist. The
build is refused, with no archive, when the source contains a symbolic link or
junction, an entry that is not a regular file or a folder (a named pipe would make the
copy hang), or two pack-relative paths that collide when letter case is ignored —
including a file beside a folder of the same name — which the launcher's installer
would reject because it compares names without regard to case, or when the output
folder is the source folder or a folder inside it. A pack that fails the check
produces no archive; every problem is printed with its problem code. The archive is
written under a temporary name in the output folder and renamed to its final name only
once the ZIP is closed, so a failed write leaves no partial archive behind and never
removes or replaces a file that existed before the build.

Building the same source twice gives a byte-identical archive on any platform,
because the archive's entry order, the manifest's key order and the timestamps are
fixed, so a pack's hash is reproducible.

The archive is a ZIP with `pack.json` at its root, the form the launcher's
PackStorage.Install reads. The manifest's fields are contract 1 in
docs/packs/contracts.md; example packs are in tests/fixtures/packs/.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

MOD_TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = MOD_TOOLS_DIR.parents[2]
# Workstream A owns the pack tools in tools/packs; the builder imports them from
# there instead of copying their code.
sys.path.insert(0, str(REPO_ROOT / "tools" / "packs"))

import check_pack
import fill_file_table

MANIFEST_NAME = "pack.json"
ARCHIVE_SUFFIX = ".mw3pack"
# The archive is assembled under this temporary name in the output folder and renamed
# to its final name only after the ZIP is closed, so a failed write leaves no partial
# archive behind.
PARTIAL_SUFFIX = ".partial"
# One fixed timestamp for every archive entry (the earliest the ZIP format holds),
# so two builds of the same source are byte-identical whatever the clock says.
FIXED_ARCHIVE_DATE_TIME = (1980, 1, 1, 0, 0, 0)
# A pinned compression level: the library default can differ between zlib builds.
ARCHIVE_COMPRESSION_LEVEL = 9
# The finished archive is hashed in chunks of this size, so printing its SHA-256
# never needs the whole archive in memory at once.
HASH_CHUNK_SIZE = 1024 * 1024


class PackBuildError(Exception):
    """The assembled pack failed the contract 1 check; `problems` says why."""

    def __init__(self, problems: list[check_pack.Problem]) -> None:
        self.problems = problems
        super().__init__("; ".join(problem.line() for problem in problems))


class OutputExistsError(Exception):
    """The build's output path cannot be used: it is taken, or it lies inside the source."""

    def __init__(self, path: Path, message: str | None = None) -> None:
        self.path = path
        super().__init__(message if message is not None else f"output already exists: {path}")


class UnsafeSourceError(Exception):
    """The source holds an entry that makes packaging it unsafe or ambiguous."""


def _is_link(path: Path) -> bool:
    """Whether path is a symbolic link or, on Windows, any reparse point such as a junction.

    Path.is_junction exists only from Python 3.12 — on 3.11 it silently reports
    False, so a junction would be followed — and os.path.islink does not report
    junctions either. On Windows the reparse point attribute is therefore read
    straight from lstat: every junction and symbolic link has
    FILE_ATTRIBUTE_REPARSE_POINT set, on every supported Python.
    """
    if os.name == "nt":
        try:
            attributes = os.lstat(path).st_file_attributes
        except OSError:
            return False
        return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    return os.path.islink(path)


def _reject_unsafe_entries(source_folder: Path) -> None:
    """Refuse a source with a link or an entry that is not a regular file or folder.

    shutil.copytree follows links while copying, so a link inside the source could
    package a file from outside the source folder, and a named pipe or socket would
    make the copy hang. The build stops before anything is copied, and the error
    names the entry.
    """
    for directory, dirnames, filenames in os.walk(source_folder, followlinks=False):
        # Every directory is checked when its parent is listed, before os.walk
        # descends into it: followlinks=False only skips what os.path.islink
        # reports, and on Python 3.11 that misses Windows junctions.
        for name in dirnames + filenames:
            entry = Path(directory) / name
            if _is_link(entry):
                raise UnsafeSourceError(
                    f"refusing to build: {entry} is a symbolic link or junction"
                )
            if not entry.is_file() and not entry.is_dir():
                raise UnsafeSourceError(
                    f"refusing to build: {entry} is not a regular file or a directory"
                )


def find_case_clash(paths: list[str]) -> tuple[str, str] | None:
    """The first pair of paths that collide when compared without regard to case.

    The launcher's installer compares entry names without regard to case, so on a
    case-sensitive file system a source can hold both `a/skin.bwtex` and
    `a/Skin.bwtex` — or a file `data` beside a folder `DATA/item.txt`, which cannot be
    extracted on Windows either — and the builder would pack both, only for the
    installer to reject the archive. Every parent folder prefix of each path is
    compared too, not just the whole path, so two spellings of one folder clash and
    so does a file whose name equals another path's folder. Returns the two paths,
    the earlier one first, or None when no two of them clash.
    """
    # Casefolded prefix -> (the prefix as spelled, the path it came from). A prefix
    # seen again with the same spelling is just a shared folder, not a clash.
    seen: dict[str, tuple[str, str]] = {}
    for path in paths:
        prefix = path
        while True:
            folded = prefix.casefold()
            if folded in seen:
                spelled, earlier_path = seen[folded]
                if spelled != prefix:
                    return earlier_path, path
            else:
                seen[folded] = (prefix, path)
            if "/" not in prefix:
                break
            prefix = prefix.rsplit("/", 1)[0]
    return None


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    # The same rule the pack check applies: json.loads would silently keep the last
    # of two equal keys, and two readers could then disagree about the manifest.
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"the key {key!r} appears twice")
        result[key] = value
    return result


def load_source_manifest(source_folder: Path) -> dict[str, Any]:
    """Read the source folder's pack.json, refusing what JSON cannot hold uniquely."""
    manifest_path = source_folder / MANIFEST_NAME
    if not manifest_path.is_file():
        problem = check_pack.Problem("manifest-invalid", f"no {MANIFEST_NAME} in {source_folder}")
        raise PackBuildError([problem])
    try:
        text = manifest_path.read_text(encoding="utf-8")
        manifest = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except (OSError, ValueError, UnicodeDecodeError) as error:
        problem = check_pack.Problem("manifest-invalid", str(error))
        raise PackBuildError([problem]) from error
    if not isinstance(manifest, dict):
        problem = check_pack.Problem("manifest-invalid", f"{MANIFEST_NAME} is not a JSON object")
        raise PackBuildError([problem])
    return manifest


def archive_name(manifest: dict[str, Any]) -> str:
    """`<id>-<version>.mw3pack`, or "" while the manifest has no usable pair."""
    pack_id = manifest.get("id")
    version = manifest.get("version")
    if not isinstance(pack_id, str) or not isinstance(version, str):
        return ""
    return f"{pack_id}-{version}{ARCHIVE_SUFFIX}"


def _mod_file_rows(path: Path) -> list[tuple[str, str]]:
    """The `key=value` rows of a mod.txt-style file, with keys lowercased.

    mod.txt and a campaign file are `key=value` lines, the key in any case, spaces
    around either side trimmed, `#` starting a comment line, and a campaign file may
    begin with a UTF-8 mark (runtime/mw3-re/docs/modding-reference.md).
    """
    rows: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        rows.append((key.strip().lower(), value.strip()))
    return rows


def _first_word(value: str) -> str:
    words = value.split()
    return words[0] if words else ""


def _file_inside(source_folder: Path, relative: str) -> Path | None:
    """The file at a pack-relative path, or None when it is not safe to read there.

    Contract 1's path rules decide what may be opened, so a gameplay root or campaign
    file that could leave the source folder is never read; the pack check reports it.
    """
    if not check_pack.path_is_safe(relative):
        return None
    candidate = source_folder / relative
    return candidate if candidate.is_file() else None


def build_provides(source_folder: Path, manifest: dict[str, Any]) -> dict[str, list[str]]:
    """The `provides` summary that contract 1 reserves for the pack tool.

    The names come from what the pack contains: mech and weapon names from mod.txt's
    `mech=` and `weapon=` rows, map names from its `ia_world=` rows, campaign names
    and missions from the campaign files its `campaign=` rows name, and skin names
    from the manifest's `visuals`. Empty groups are left out.
    """
    mechs: list[str] = []
    weapons: list[str] = []
    skins: list[str] = []
    maps: list[str] = []
    missions: list[str] = []
    campaigns: list[str] = []

    def add(names: list[str], name: str) -> None:
        if name and name not in names:
            names.append(name)

    gameplay = manifest.get("gameplay")
    if isinstance(gameplay, dict) and isinstance(gameplay.get("root"), str):
        root = gameplay["root"]
        mod_txt = _file_inside(source_folder, f"{root}/mod.txt")
        if mod_txt is not None:
            for key, value in _mod_file_rows(mod_txt):
                if key in ("mech", "weapon"):
                    add(mechs if key == "mech" else weapons, _first_word(value))
                elif key == "ia_world":
                    # `ia_world=<folder> <name>`: the map's shown name is the rest.
                    parts = value.split(None, 1)
                    add(maps, parts[1].strip() if len(parts) > 1 else _first_word(value))
                elif key == "campaign":
                    # The runtime's mod loader also accepts backslash separators in
                    # a campaign reference on Windows; normalize before the pack-path
                    # check, or the campaign and its missions would be dropped.
                    campaign_reference = value.replace("\\", "/")
                    campaign = _file_inside(source_folder, f"{root}/{campaign_reference}")
                    if campaign is None:
                        continue
                    for campaign_key, campaign_value in _mod_file_rows(campaign):
                        if campaign_key == "name":
                            add(campaigns, campaign_value)
                        elif campaign_key == "mission":
                            # `mission=<world> <number> ...`, named like a target.
                            words = campaign_value.split()
                            if len(words) >= 2:
                                add(missions, f"{words[0]}/{words[1]}")
    visuals = manifest.get("visuals")
    if isinstance(visuals, list):
        for visual in visuals:
            if isinstance(visual, dict) and visual.get("kind") == "skin":
                name = visual.get("name")
                if isinstance(name, str):
                    add(skins, name)

    provides: dict[str, list[str]] = {}
    for key, names in (
        ("mechs", mechs),
        ("weapons", weapons),
        ("skins", skins),
        ("maps", maps),
        ("missions", missions),
        ("campaigns", campaigns),
    ):
        if names:
            provides[key] = names
    return provides


def _serialize_manifest(manifest: dict[str, Any]) -> bytes:
    # The same layout tools/packs/fill_file_table.py writes, so a pack rebuilt from
    # an example folder keeps the form its fixture has.
    return (json.dumps(manifest, indent=2) + "\n").encode("utf-8")


def _pack_files(pack_folder: Path) -> list[str]:
    """Every file in the pack folder as a pack-relative path, in a fixed order."""
    return sorted(
        path.relative_to(pack_folder).as_posix()
        for path in pack_folder.rglob("*")
        if path.is_file()
    )


def _write_archive(pack_folder: Path, archive_path: Path) -> None:
    """Write the pack folder as a ZIP archive to archive_path, created exclusively.

    The archive is opened in exclusive-create mode, so a file already sitting at
    archive_path is never overwritten. Entry order, timestamps, attributes and
    compression level are all fixed, so the same folder always gives the same bytes.
    The launcher's PackStorage.Install reads a plain ZIP like this one.
    """
    with zipfile.ZipFile(
        archive_path,
        "x",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=ARCHIVE_COMPRESSION_LEVEL,
    ) as archive:
        for relative in _pack_files(pack_folder):
            info = zipfile.ZipInfo(relative, date_time=FIXED_ARCHIVE_DATE_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            # Unix, so the entry's attributes are read as a plain regular-file mode.
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, (pack_folder / relative).read_bytes())


def _rename_exclusive(source: Path, destination: Path) -> None:
    """Rename source to destination, failing when destination already exists.

    os.rename silently replaces an existing destination on POSIX, so the final name
    is claimed with a hard link first — os.link fails with EEXIST when the name is
    taken on every platform — and the temporary name is dropped afterwards. Where
    the file system has no hard links, fall back to os.rename after checking the
    name is free (on Windows os.rename itself refuses to replace an existing file).
    """
    try:
        os.link(source, destination)
    except OSError as error:
        if error.errno == errno.EEXIST:
            raise FileExistsError(f"output already exists: {destination}") from error
        if destination.exists() or os.path.islink(destination):
            raise FileExistsError(f"output already exists: {destination}") from error
        os.rename(source, destination)
        return
    os.unlink(source)


def build_pack(source_folder: Path, output_dir: Path) -> Path:
    """Build the source folder's `<id>-<version>.mw3pack` inside `output_dir`.

    Returns the archive's path. Raises PackBuildError when the assembled pack fails
    the contract 1 check — no archive is written then —, OutputExistsError when the
    archive path is already taken or the output folder is the source or inside it, and
    UnsafeSourceError when the source contains a link, an entry that is not a regular
    file or a folder, or two pack-relative paths that collide when letter case is
    ignored. The source folder is never modified. The archive is written under a
    temporary name and renamed into place only when complete, so a failed write
    leaves no partial archive and never replaces an existing file.
    """
    source_folder = Path(source_folder)
    output_dir = Path(output_dir)
    # Resolve both before comparing, so a relative or ".." output cannot disguise
    # itself: writing into the source would modify it, which the builder never does.
    # Nothing has been created yet when this refuses the build.
    source_resolved = source_folder.resolve()
    output_resolved = output_dir.resolve()
    if output_resolved == source_resolved or source_resolved in output_resolved.parents:
        raise OutputExistsError(
            output_dir, f"output folder is the source folder or inside it: {output_dir}"
        )
    _reject_unsafe_entries(source_folder)
    # The archive's entry names are the source's file paths, so two of them colliding
    # when case is ignored — whole paths or folder prefixes — would both be packed
    # and then rejected by the launcher's installer.
    clash = find_case_clash(_pack_files(source_folder))
    if clash is not None:
        first, second = clash
        raise UnsafeSourceError(
            f"refusing to build: {first} and {second} differ only in letter case"
        )
    manifest = load_source_manifest(source_folder)

    name = archive_name(manifest)
    if name and (output_dir / name).exists():
        raise OutputExistsError(output_dir / name)

    with tempfile.TemporaryDirectory(prefix="mw3pack-build-") as temporary:
        # The source is only read; the pack with its written tables is assembled in
        # the copy, so the check sees exactly what the archive will hold.
        staging = Path(temporary) / "pack"
        shutil.copytree(source_folder, staging)
        previous_files = manifest.get("files")
        assembled = dict(manifest)
        # Remove any written tables first, so the two keys added below always land
        # at the end: the written key order must not depend on the source manifest,
        # or the same content would not always build to the same bytes.
        assembled.pop("files", None)
        assembled.pop("provides", None)
        provides = build_provides(staging, manifest)
        if provides:
            assembled["provides"] = provides
        file_table = fill_file_table.build_file_table(
            staging, previous_files if isinstance(previous_files, dict) else {}
        )
        # build_file_table orders its entries by Path, and Path's order is not the
        # same on every platform (Windows compares names case-insensitively), so
        # re-key the table by the plain sorted() path strings: code-point order is
        # identical everywhere, and so is the manifest serialized from it.
        assembled["files"] = {path: file_table[path] for path in sorted(file_table)}
        (staging / MANIFEST_NAME).write_bytes(_serialize_manifest(assembled))

        problems = check_pack.check_pack(staging)
        if problems:
            raise PackBuildError(problems)

        if output_dir.exists() and not output_dir.is_dir():
            raise OutputExistsError(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        archive_path = output_dir / archive_name(assembled)
        partial_path = archive_path.with_name(archive_path.name + PARTIAL_SUFFIX)
        if partial_path.exists() or partial_path.is_symlink():
            # A temporary name left by an interrupted run is a file that existed
            # before this build; it is never removed or replaced, so refuse.
            raise OutputExistsError(partial_path)
        try:
            # The archive is written under the temporary name and renamed to its
            # final name only after the ZIP is closed, so a write that fails partway
            # leaves no partial archive and a retry does not meet "output already
            # exists". The rename refuses to replace a file that existed before.
            _write_archive(staging, partial_path)
            _rename_exclusive(partial_path, archive_path)
        except FileExistsError as error:
            partial_path.unlink(missing_ok=True)
            raise OutputExistsError(archive_path) from error
        except BaseException:
            # Whatever went wrong, the temporary archive this build created is
            # removed; no partial file is left behind.
            partial_path.unlink(missing_ok=True)
            raise
    return archive_path


def _file_sha256(path: Path) -> str:
    """The SHA-256 hex digest of a file, read in chunks rather than all at once."""
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        chunk = file.read(HASH_CHUNK_SIZE)
        while chunk:
            digest.update(chunk)
            chunk = file.read(HASH_CHUNK_SIZE)
    return digest.hexdigest()


def main(arguments: list[str]) -> int:
    if len(arguments) not in (1, 2):
        print(__doc__)
        return 2
    source_folder = Path(arguments[0])
    output_dir = Path(arguments[1]) if len(arguments) == 2 else Path(".")
    if not source_folder.is_dir():
        print(f"not a folder: {source_folder}")
        return 2
    try:
        archive_path = build_pack(source_folder, output_dir)
    except OutputExistsError as error:
        print(error)
        return 1
    except UnsafeSourceError as error:
        # An unsafe or ambiguous source entry is reported by name; no archive is written.
        print(error)
        return 1
    except PackBuildError as error:
        for problem in error.problems:
            print(problem.line())
        print("no archive written")
        return 1
    except (OSError, UnicodeDecodeError) as error:
        # A payload file the builder cannot read (a mod.txt that is not UTF-8, say)
        # is reported, not silently skipped: no archive is written for it.
        print(f"build failed: {error}")
        return 1
    digest = _file_sha256(archive_path)
    print(f"wrote {archive_path} (sha256 {digest})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
