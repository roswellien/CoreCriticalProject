"""Check an unpacked content pack against contracts 1 and 4 (docs/packs/contracts.md).

Usage, from the repository root:
    python tools/packs/check_pack.py <pack folder>

Prints one line per problem, each starting with its problem code, and exits 1 when
there is any. This checks what can be known from the pack alone. Whether a visual's
target exists in the game is known only to the runtime (contract 3).
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import json_schema_subset

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_SCHEMA_PATH = REPO_ROOT / "docs/packs/schemas/pack-manifest-v3.schema.json"
MANIFEST_NAME = "pack.json"

# Contract 1, "Data only": a pack never carries anything that can run.
EXECUTABLE_SUFFIXES = {
    ".bat", ".cmd", ".com", ".dll", ".dylib", ".exe", ".jar", ".js", ".lua", ".msi",
    ".ps1", ".py", ".scr", ".sh", ".so", ".vbs",
}  # fmt: skip
# Names Windows treats as devices whatever their extension, so they can never be files.
WINDOWS_DEVICE_NAME = re.compile(
    r"\A(CON|CONIN\$|CONOUT\$|PRN|AUX|NUL|COM[0-9]|LPT[0-9])\Z", re.IGNORECASE
)
MAX_PATH_LENGTH = 240
# Contract 4: what a visual may dress, and how each kind of target is named.
TARGET_PATTERNS = (
    re.compile(r"\A(mech-model|world):[a-z0-9][a-z0-9_-]{0,31}\Z"),
    re.compile(r"\Amission:[a-z0-9][a-z0-9_-]{0,31}/[0-9]{1,2}\Z"),
    re.compile(r"\Agame:mw3\Z"),
)


@dataclass(frozen=True)
class VisualKind:
    """One row of contract 4's "Kinds and their files" table."""

    # The target kinds ("<target kind>:<name>") a visual of this kind may dress.
    allowed_target_kinds: frozenset[str]
    # The roles the visual's files must hold, and the extra ones it may hold.
    required_roles: frozenset[str]
    optional_roles: frozenset[str]
    # Fields the visual must have besides target, kind and files ("lod", "name").
    required_fields: frozenset[str]


# Contract 4, "Kinds and their files". The manifest schema's kind enum must list
# exactly these kinds; test_example_packs.py checks that the two stay in step.
_GAME_REGISTRY_KIND = VisualKind(
    allowed_target_kinds=frozenset({"game"}),
    required_roles=frozenset({"registry"}),
    optional_roles=frozenset(),
    required_fields=frozenset(),
)
VISUAL_KINDS: dict[str, VisualKind] = {
    "model": VisualKind(
        allowed_target_kinds=frozenset({"mech-model"}),
        required_roles=frozenset({"mesh", "textures"}),
        optional_roles=frozenset({"normals", "materials"}),
        required_fields=frozenset({"lod"}),
    ),
    "skin": VisualKind(
        allowed_target_kinds=frozenset({"mech-model"}),
        required_roles=frozenset({"textures"}),
        optional_roles=frozenset({"normals"}),
        required_fields=frozenset({"name"}),
    ),
    "environment": VisualKind(
        allowed_target_kinds=frozenset({"world", "mission"}),
        required_roles=frozenset({"registry"}),
        optional_roles=frozenset(),
        required_fields=frozenset(),
    ),
    "ui": _GAME_REGISTRY_KIND,
    "music": _GAME_REGISTRY_KIND,
    "cinematic": _GAME_REGISTRY_KIND,
}


@dataclass(frozen=True)
class Problem:
    code: str
    message: str

    def line(self) -> str:
        return f"{self.code}: {self.message}"


class DuplicateKeyError(ValueError):
    pass


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    # json.loads keeps the last of two equal keys silently. Two readers could then
    # disagree about what the manifest says, so a repeated key is an error.
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"the key {key!r} appears twice")
        result[key] = value
    return result


def _reject_non_json_constant(name: str) -> Any:
    # json.loads accepts NaN, Infinity and -Infinity unless told not to, but they
    # are not JSON: a reader in another language refuses the same file, so the pack
    # check refuses it too (contract 1, manifest rules).
    raise ValueError(f"{name} is not a JSON value")


def path_is_safe(path: str) -> bool:
    """Whether a pack-relative path stays inside the pack on every operating system."""
    if not path or len(path) > MAX_PATH_LENGTH or "\\" in path:
        return False
    for part in path.split("/"):
        if part in ("", ".", ".."):
            return False
        # Windows drops a trailing dot or space, so "a." and "a" would be one file.
        if part.endswith((".", " ")):
            return False
        has_control_character = any(ord(character) < 32 for character in part)
        has_reserved_character = any(character in '<>:"|?*' for character in part)
        if has_control_character or has_reserved_character:
            return False
        name_before_first_dot = part.split(".")[0]
        if WINDOWS_DEVICE_NAME.match(name_before_first_dot):
            return False
    return True


def target_is_well_formed(target: str) -> bool:
    return any(pattern.match(target) for pattern in TARGET_PATTERNS)


def _schema_problems(manifest: Any) -> list[Problem]:
    schema = json.loads(MANIFEST_SCHEMA_PATH.read_text(encoding="utf-8"))
    problems = []
    for violation in json_schema_subset.find_violations(manifest, schema):
        where = violation.path or "/"
        is_unknown_field = violation.keyword == "additionalProperties"
        code = "manifest-unknown-field" if is_unknown_field else "manifest-invalid"
        problems.append(Problem(code, f"{where}: {violation.message}"))
    return problems


def _files_on_disk(pack_folder: Path) -> set[str]:
    found = set()
    for path in pack_folder.rglob("*"):
        if path.is_file():
            relative = path.relative_to(pack_folder).as_posix()
            if relative != MANIFEST_NAME:
                found.add(relative)
    return found


def _file_table_problems(pack_folder: Path, file_table: dict[str, Any]) -> list[Problem]:
    problems = []
    on_disk = _files_on_disk(pack_folder)
    for path in sorted(on_disk - set(file_table)):
        problems.append(Problem("file-undeclared", f"{path} is in the pack but not in files"))
    for path, entry in sorted(file_table.items()):
        if not path_is_safe(path):
            problems.append(Problem("path-unsafe", f"{path} could leave the pack folder"))
            continue
        if Path(path).suffix.lower() in EXECUTABLE_SUFFIXES:
            problems.append(Problem("payload-executable", f"{path} is a program or script"))
        if path not in on_disk:
            problems.append(Problem("file-missing", f"{path} is in files but not in the pack"))
            continue
        content = (pack_folder / path).read_bytes()
        size_matches = len(content) == entry.get("bytes")
        hash_matches = hashlib.sha256(content).hexdigest() == entry.get("sha256")
        if not (size_matches and hash_matches):
            problems.append(Problem("file-hash-mismatch", f"{path} differs from its files entry"))
    return problems


def _gameplay_problems(manifest: dict[str, Any], file_table: dict[str, Any]) -> list[Problem]:
    gameplay = manifest.get("gameplay")
    if gameplay is None:
        return []
    root = gameplay["root"]
    if not path_is_safe(root):
        return [Problem("path-unsafe", f"gameplay root {root} could leave the pack folder")]
    # The runtime recognises a mod by its mod.txt; a root without one is not a mod.
    if f"{root}/mod.txt" not in file_table:
        return [Problem("gameplay-root-invalid", f"{root}/mod.txt is not listed in files")]
    return []


def _visual_problems(manifest: dict[str, Any], file_table: dict[str, Any]) -> list[Problem]:
    problems = []
    has_gameplay = "gameplay" in manifest
    # Contract 4: inside one pack a model is keyed by target and lod, a skin by
    # target and name; a second binding with the same key is a duplicate.
    seen_model_keys: set[tuple[str, Any]] = set()
    seen_skin_keys: set[tuple[str, Any]] = set()
    for index, visual in enumerate(manifest.get("visuals", [])):
        target = visual["target"]
        kind = visual["kind"]
        # The schema's kind enum and VISUAL_KINDS name the same kinds (a test checks
        # it) and the schema check has already run, so this lookup cannot fail.
        kind_rule = VISUAL_KINDS[kind]
        well_formed = target_is_well_formed(target)
        if not well_formed:
            problems.append(Problem("visual-target-invalid", f"visual {index}: {target}"))
        if visual.get("needs_gameplay") and not has_gameplay:
            message = f"visual {index} needs a gameplay payload this pack does not have"
            problems.append(Problem("visual-needs-gameplay", message))
        # The kind-against-target rule needs a well-formed target: a malformed one
        # is already reported as visual-target-invalid, not piled on.
        if well_formed:
            target_kind = target.split(":", 1)[0]
            if target_kind not in kind_rule.allowed_target_kinds:
                message = f"visual {index}: a {kind} cannot dress {target}"
                problems.append(Problem("visual-kind-target-mismatch", message))
        files = visual["files"]
        for role in sorted(kind_rule.required_roles - set(files)):
            message = f"visual {index}: a {kind} needs a {role} file"
            problems.append(Problem("visual-role-missing", message))
        for role in sorted(files):
            if role not in kind_rule.required_roles | kind_rule.optional_roles:
                message = f"visual {index}: {role} is not a file role of a {kind}"
                problems.append(Problem("visual-role-unknown", message))
        for field in sorted(kind_rule.required_fields):
            if field not in visual:
                message = f"visual {index}: a {kind} needs a {field}"
                problems.append(Problem("visual-field-missing", message))
        if kind == "model":
            key = (target, visual.get("lod"))
            if key in seen_model_keys:
                lod = visual.get("lod")
                message = f"visual {index}: {target} already has a model with lod {lod}"
                problems.append(Problem("visual-duplicate-binding", message))
            seen_model_keys.add(key)
        elif kind == "skin":
            key = (target, visual.get("name"))
            if key in seen_skin_keys:
                name = visual.get("name")
                message = f"visual {index}: {target} already has a skin named {name!r}"
                problems.append(Problem("visual-duplicate-binding", message))
            seen_skin_keys.add(key)
        for role, path in sorted(files.items()):
            if path not in file_table:
                message = f"visual {index}, {role}: {path} is not listed in files"
                problems.append(Problem("visual-file-undeclared", message))
    return problems


def check_pack(pack_folder: Path) -> list[Problem]:
    """Every contract 1 and contract 4 problem in a pack; an empty list means valid."""
    manifest_path = pack_folder / MANIFEST_NAME
    if not manifest_path.is_file():
        return [Problem("manifest-invalid", f"no {MANIFEST_NAME}")]
    try:
        text = manifest_path.read_text(encoding="utf-8")
        manifest = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_non_json_constant,
        )
    except (ValueError, UnicodeDecodeError) as error:
        return [Problem("manifest-invalid", str(error))]

    problems = _schema_problems(manifest)
    if problems:
        # The later checks read fields the schema has just said are wrong or missing.
        return problems
    file_table = manifest["files"]
    problems += _file_table_problems(pack_folder, file_table)
    problems += _gameplay_problems(manifest, file_table)
    problems += _visual_problems(manifest, file_table)
    return problems


def main(arguments: list[str]) -> int:
    if len(arguments) != 1:
        print(__doc__)
        return 2
    problems = check_pack(Path(arguments[0]))
    for problem in problems:
        print(problem.line())
    if not problems:
        print("valid")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
