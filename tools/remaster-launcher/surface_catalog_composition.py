"""Compose authored normal catalogs without changing their selected image pixels.

Identical duplicate bindings collapse. Conflicting images require an explicit
full-content key -> source catalog choice; input order never resolves a conflict.
All inputs remain read-only, and the output manifest is published last.
"""
import hashlib
from pathlib import Path

from normal_materials import pack_surface_bindings, read_surface_bindings


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def compose(paths, output, *, overrides=None):
    paths = [Path(path).resolve() for path in paths]
    if not paths or len(paths) > 128 or len(set(paths)) != len(paths):
        raise ValueError("Invalid source catalog list")
    choices = {key: Path(path).resolve() for key, path in (overrides or {}).items()}
    output = Path(output)
    if output.exists():
        raise ValueError("Use a fresh composition directory")
    pins = {path: sha(path) for path in paths}
    pages = [read_surface_bindings(path.read_bytes()) for path in paths]
    candidates = {}
    duplicate_count = 0
    conflicts = set()
    for path, entries in zip(paths, pages):
        for key, image in entries:
            if key in candidates:
                duplicate_count += 1
            candidates.setdefault(key, []).append((path, image))
    selected = {}
    for key, variants in candidates.items():
        if all(image == variants[0][1] for _, image in variants):
            selected[key] = variants[0]
            continue
        conflicts.add(key)
        winner = choices.get(key)
        matches = [variant for variant in variants if variant[0] == winner]
        if not matches:
            raise ValueError("Conflicting surface images require an explicit source choice: " + str(key))
        selected[key] = matches[0]
    if set(choices) != conflicts:
        raise ValueError("Source choices must name exactly the conflicting full-content keys")
    output.mkdir(parents=True)
    catalogs = []
    for index, (path, entries) in enumerate(zip(paths, pages)):
        kept = [(key, image) for key, image in entries if selected[key][0] == path]
        if not kept:
            continue
        encoded = pack_surface_bindings(kept)
        # Round-trip checks the existing binary format and exact selected images.
        if read_surface_bindings(encoded) != kept:
            raise ValueError("Composed surface catalog changed selected image data")
        target = output / f"page-{index:03}.bin"
        target.write_bytes(encoded)
        catalogs.append(target.resolve())
    if any(sha(path) != pin for path, pin in pins.items()):
        raise ValueError("Source catalog changed during composition")
    manifest = output / "surface-normals.txt"
    manifest.write_text("MW34SNA1\n" + "\n".join(map(str, catalogs)) + "\n", encoding="utf-8")
    return dict(manifest=str(manifest.resolve()), input_sha256={str(p): h for p, h in pins.items()},
                bindings=len(selected), duplicates=duplicate_count, resolved_conflicts=len(conflicts),
                output_sha256={str(p): sha(p) for p in catalogs})
