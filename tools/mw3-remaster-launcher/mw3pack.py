#!/usr/bin/env python3
"""MW3Pack Developer & Modder Utility
Validates, packages, unpacks, and generates boilerplate asset packs for MechWarrior 3 Remastered.
"""
import argparse, json, os, sys, zipfile
from pathlib import Path

SCHEMA_VERSION = 1

def validate_pack(folder: Path) -> tuple[bool, str]:
    if not folder.is_dir():
        return False, f"Not a directory: {folder}"
    manifest_path = folder / "pack.json"
    if not manifest_path.is_file():
        return False, f"Missing mandatory descriptor: {manifest_path}"

    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return False, f"Invalid JSON in pack.json: {exc}"

    if data.get("schema_version") != SCHEMA_VERSION:
        return False, f"Unsupported schema_version {data.get('schema_version')} (expected {SCHEMA_VERSION})"

    for req in ["id", "name", "version", "author", "description"]:
        if not data.get(req):
            return False, f"Missing required field in pack.json: '{req}'"

    valid_dirs = {"textures", "models", "audio", "hud", "preview.png", "pack.json"}
    found_assets = False
    for item in folder.iterdir():
        if item.name.lower() in valid_dirs or item.name == "pack.json":
            if item.is_dir() and any(item.iterdir()):
                found_assets = True

    preview = folder / "preview.png"
    if preview.exists() and not preview.is_file():
        return False, "preview.png exists but is not a regular image file"

    return True, f"Pack '{data['name']}' ({data['id']} v{data['version']}) is valid."

def build_pack(folder: Path, output_file: Path | None = None) -> Path:
    ok, msg = validate_pack(folder)
    if not ok:
        raise ValueError(f"Pack validation failed: {msg}")

    manifest = json.loads((folder / "pack.json").read_text(encoding="utf-8-sig"))
    if not output_file:
        output_file = folder.parent / f"{manifest['id']}.mw3pack"

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_file, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for root, dirs, files in os.walk(folder):
            for file in files:
                abs_p = Path(root) / file
                rel_p = abs_p.relative_to(folder)
                zf.write(abs_p, arcname=str(rel_p).replace("\\", "/"))

    print(f"Successfully built asset pack: {output_file} ({output_file.stat().st_size / 1024:.1f} KB)")
    return output_file

def unpack_pack(archive: Path, dest_dir: Path | None = None) -> Path:
    if not archive.is_file():
        raise FileNotFoundError(f"Pack archive not found: {archive}")

    with zipfile.ZipFile(archive, "r") as zf:
        manifest_entry = next((e for e in zf.namelist() if e.endswith("pack.json")), None)
        if not manifest_entry:
            raise ValueError("Archive is missing pack.json")
        data = json.loads(zf.read(manifest_entry).decode("utf-8-sig"))
        pack_id = data.get("id", archive.stem)

        if not dest_dir:
            dest_dir = archive.parent / pack_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        zf.extractall(dest_dir)

    print(f"Extracted pack '{data.get('name')}' to {dest_dir}")
    return dest_dir

def create_template(pack_id: str, dest_dir: Path) -> Path:
    target = dest_dir / pack_id
    target.mkdir(parents=True, exist_ok=True)
    (target / "textures").mkdir(exist_ok=True)
    (target / "models" / "mechs").mkdir(parents=True, exist_ok=True)
    (target / "models" / "world").mkdir(parents=True, exist_ok=True)
    (target / "audio" / "sfx").mkdir(parents=True, exist_ok=True)
    (target / "audio" / "music").mkdir(parents=True, exist_ok=True)
    (target / "hud").mkdir(exist_ok=True)

    manifest = {
        "schema_version": 1,
        "id": pack_id,
        "name": pack_id.replace("-", " ").title(),
        "version": "1.0.0",
        "author": "Your Name",
        "homepage": "https://example.com/mw3-pack",
        "description": "Custom asset pack for MechWarrior 3 Remastered.",
        "category": "General",
        "min_engine_version": "1.0.0",
        "dependencies": [],
        "conflicts": [],
        "provides": {
            "mechs": [],
            "world_models": [],
            "textures": True,
            "normal_maps": True,
            "audio": False,
            "cd_music": False
        }
    }
    (target / "pack.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Created boilerplate mod template in: {target}")
    return target

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    v_p = sub.add_parser("validate", help="Validate an asset pack folder")
    v_p.add_argument("folder", type=Path)

    b_p = sub.add_parser("build", help="Build a .mw3pack archive from a folder")
    b_p.add_argument("folder", type=Path)
    b_p.add_argument("-o", "--output", type=Path, default=None)

    u_p = sub.add_parser("unpack", help="Unpack a .mw3pack archive")
    u_p.add_argument("archive", type=Path)
    u_p.add_argument("-d", "--dest", type=Path, default=None)

    t_p = sub.add_parser("template", help="Create a boilerplate mod template")
    t_p.add_argument("pack_id", type=str)
    t_p.add_argument("-d", "--dest", type=Path, default=Path("."))

    args = p.parse_args()
    if args.command == "validate":
        ok, msg = validate_pack(args.folder)
        print(msg)
        sys.exit(0 if ok else 1)
    elif args.command == "build":
        build_pack(args.folder, args.output)
    elif args.command == "unpack":
        unpack_pack(args.archive, args.dest)
    elif args.command == "template":
        create_template(args.pack_id, args.dest)

if __name__ == "__main__":
    main()
