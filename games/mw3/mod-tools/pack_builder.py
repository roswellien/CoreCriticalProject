"""Build a schema version 3 content pack archive from a folder of authored content.

Usage, from the repository root:
    python games/mw3/mod-tools/pack_builder.py <source folder> [output folder]

The source folder holds a `pack.json` without `files` or `provides` — the builder
writes both — plus the pack's payload files. The builder assembles a copy in a
temporary folder, runs the contract 1 check from tools/packs/check_pack.py on it,
and only when that check is clean writes `<id>-<version>.mw3pack` into the output
folder (the current folder by default).

The source folder is never modified, and the output file must not already exist. A
pack that fails the check produces no archive; every problem is printed with its
problem code. Building the same source twice gives a byte-identical archive, because
the archive's entry order and timestamps are fixed, so a pack's hash is reproducible.

The archive is a ZIP with `pack.json` at its root, the form the launcher's
PackStorage.Install reads. The manifest's fields are contract 1 in
docs/packs/contracts.md; example packs are in tests/fixtures/packs/.
"""

from __future__ import annotations

import hashlib
import json
import shutil
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
# One fixed timestamp for every archive entry (the earliest the ZIP format holds),
# so two builds of the same source are byte-identical whatever the clock says.
FIXED_ARCHIVE_DATE_TIME = (1980, 1, 1, 0, 0, 0)
# A pinned compression level: the library default can differ between zlib builds.
ARCHIVE_COMPRESSION_LEVEL = 9


class PackBuildError(Exception):
    """The assembled pack failed the contract 1 check; `problems` says why."""

    def __init__(self, problems: list[check_pack.Problem]) -> None:
        self.problems = problems
        super().__init__("; ".join(problem.line() for problem in problems))


class OutputExistsError(Exception):
    """The archive path this build would write is already taken."""

    def __init__(self, path: Path) -> None:
        self.path = path
        super().__init__(f"output already exists: {path}")


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
                    campaign = _file_inside(source_folder, f"{root}/{value}")
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
    """Write the pack folder as a ZIP archive with `pack.json` at its root.

    Entry order, timestamps, attributes and compression level are all fixed, so the
    same folder always gives the same bytes. The launcher's PackStorage.Install
    reads a plain ZIP like this one.
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


def build_pack(source_folder: Path, output_dir: Path) -> Path:
    """Build the source folder's `<id>-<version>.mw3pack` inside `output_dir`.

    Returns the archive's path. Raises PackBuildError when the assembled pack fails
    the contract 1 check — no archive is written then — and OutputExistsError when
    the archive path is already taken. The source folder is never modified.
    """
    source_folder = Path(source_folder)
    output_dir = Path(output_dir)
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
        assembled["files"] = fill_file_table.build_file_table(
            staging, previous_files if isinstance(previous_files, dict) else {}
        )
        (staging / MANIFEST_NAME).write_bytes(_serialize_manifest(assembled))

        problems = check_pack.check_pack(staging)
        if problems:
            raise PackBuildError(problems)

        if output_dir.exists() and not output_dir.is_dir():
            raise OutputExistsError(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        archive_path = output_dir / archive_name(assembled)
        try:
            _write_archive(staging, archive_path)
        except FileExistsError as error:
            raise OutputExistsError(archive_path) from error
    return archive_path


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
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    print(f"wrote {archive_path} (sha256 {digest})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
