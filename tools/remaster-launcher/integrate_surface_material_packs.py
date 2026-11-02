"""Integrate surface material BWSFM1 sidecars into environment and mech asset packs.

Maintains strict schema-2 archive closure, updates version numbers semantically,
pins SHA-256 and byte counts, and verifies with prepared_environment_packs.select
and prepared_mech_packs.compose.
"""

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import zipfile

import prepared_environment_packs as prep_env
import prepared_mech_packs as prep_mech
from surface_materials import (
    CAPABILITY as SURFACE_CAPABILITY,
    FORMAT as SURFACE_FORMAT,
    read_surface_materials_file,
)

ROOT = Path(__file__).resolve().parents[2]
MW3_DETAILED = {"strider", "avatar", "owens", "firefly"}
MW5_REPLACEMENTS = {
    "bushwacker", "madcat", "vulture", "thor", "orion", "daishi",
    "shadowcat", "puma", "annihilator", "cauldron", "sunder",
    "supernova", "blackhawk", "champion",
}
ALL_18_CHASSIS = sorted(MW3_DETAILED | MW5_REPLACEMENTS)


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def verify_archive(path: Path) -> dict:
    """Read every member, verify hashes/closure, and reject leaked absolute paths."""
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("pack.json"))
        assert manifest["schema_version"] == 2
        declared = manifest["files"]
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate zip members in {path}")
        if set(names) != {"pack.json", *declared}:
            missing = set(declared) - set(names)
            extra = set(names) - {"pack.json", *declared}
            raise ValueError(f"Archive closure failure in {path}: missing={missing}, extra={extra}")
        for name, pin in declared.items():
            if name.startswith("/") or ":" in name or "\\" in name or ".." in name.split("/"):
                raise ValueError(f"Illegal file entry path: {name}")
            info = archive.getinfo(name)
            if info.file_size != pin["bytes"]:
                raise ValueError(
                    f"Byte count mismatch in {path} for {name}: expected {pin['bytes']}, got {info.file_size}"
                )
            with archive.open(name) as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if actual != pin["sha256"]:
                raise ValueError(f"Digest mismatch in {path} for {name}")
        for check_name in ("pack.json", manifest.get("native_payload", {}).get("registry", "")):
            if check_name and check_name in names:
                raw = archive.read(check_name)
                for forbidden in (b"D:/", b"C:/", b"D:\\", b"C:\\"):
                    if forbidden in raw:
                        raise ValueError(f"Forbidden developer path in {check_name}")
        return manifest


def integrate_training_pack(
    source_pack: Path,
    training_sfm: Path,
    output_pack: Path,
    version: str = "1.2.0",
) -> Path:
    """Integrate training_materials.bwsfm1 into training-textures mw3pack."""
    sfm_bytes = training_sfm.read_bytes()
    sfm_sha = hashlib.sha256(sfm_bytes).hexdigest()
    read_surface_materials_file(training_sfm, expected_asset_id="training")

    output_pack.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="mw3-train-pack-") as temp_dir:
        stage = Path(temp_dir)
        with zipfile.ZipFile(source_pack) as archive:
            archive.extractall(stage)

        pack_json_path = stage / "pack.json"
        manifest = json.loads(pack_json_path.read_text(encoding="utf-8"))
        registry_rel = manifest["native_payload"]["registry"]
        registry_path = stage / registry_rel
        registry = json.loads(registry_path.read_text(encoding="utf-8"))

        sfm_rel = "environment/surface_materials.bin"
        (stage / sfm_rel).write_bytes(sfm_bytes)

        registry["ground_surface_materials"] = sfm_rel
        registry["surface_materials"] = sfm_rel
        write_json(registry_path, registry)

        manifest["version"] = version
        manifest["description"] = (
            "Prepared environment texture banks, matching normals, and calibrated PBR surface "
            "materials with displacement height maps. Uses the matching native host for reviewed "
            "lamp/glow definitions. Local playtest candidate."
        )
        if "surface_materials" not in manifest.get("provides", {}):
            manifest.setdefault("provides", {})["surface_materials"] = True

        formats = manifest["native_payload"].setdefault("required_formats", [])
        if SURFACE_FORMAT not in formats:
            formats.append(SURFACE_FORMAT)

        caps = manifest["native_payload"].setdefault("required_capabilities", {})
        caps[SURFACE_CAPABILITY] = 1

        files = manifest["files"]
        files[sfm_rel] = {
            "bytes": len(sfm_bytes),
            "sha256": sfm_sha,
            "format": SURFACE_FORMAT,
        }
        reg_bytes = registry_path.read_bytes()
        files[registry_rel] = {
            "bytes": len(reg_bytes),
            "sha256": hashlib.sha256(reg_bytes).hexdigest(),
        }

        write_json(pack_json_path, manifest)

        partial = output_pack.with_suffix(".partial")
        with zipfile.ZipFile(partial, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zout:
            for item in sorted(stage.rglob("*")):
                if item.is_file():
                    zout.write(item, item.relative_to(stage).as_posix())

        verify_archive(partial)
        if output_pack.exists():
            output_pack.unlink()
        partial.rename(output_pack)

    return output_pack


def integrate_mech_packs(
    source_model_pack: Path,
    sfm_dir: Path,
    output_dir: Path,
    version: str = "0.2.0-local.20261102",
) -> dict[str, Path]:
    """Integrate all 18 mech BWSFM1 sidecars into mw5-mechs and updated-mw3-mechs packs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    with tempfile.TemporaryDirectory(prefix="mw3-mech-packs-") as temp_dir:
        source_stage = Path(temp_dir) / "source"
        with zipfile.ZipFile(source_model_pack) as z:
            z.extractall(source_stage)

        source_registry = json.loads((source_stage / "models/models.json").read_text(encoding="utf-8"))
        models_by_id = {m["id"]: m for m in source_registry["models"]}

        for pack_suffix, title, mechs_subset in (
            ("mw5-mechs", "MW5 Replacement Mechs", MW5_REPLACEMENTS),
            ("updated-mw3-mechs", "Updated MW3 Mechs", MW3_DETAILED),
        ):
            pack_id = f"com.mw3remaster.{pack_suffix}"
            pack_stage = Path(temp_dir) / pack_suffix
            pack_stage.mkdir(parents=True, exist_ok=True)
            payload_dir = pack_stage / "payload"
            payload_dir.mkdir(parents=True, exist_ok=True)

            files = {}
            copied_payloads = set()
            records = []

            for ident in sorted(mechs_subset):
                model = copy.deepcopy(models_by_id[ident])
                sfm_path = sfm_dir / f"{ident}_materials.bwsfm1"
                if not sfm_path.is_file():
                    raise FileNotFoundError(f"Missing sidecar for chassis: {ident} at {sfm_path}")
                sfm_bytes = sfm_path.read_bytes()
                sfm_sha = hashlib.sha256(sfm_bytes).hexdigest()

                sfm_name = f"payload/{sfm_sha}.bin"
                if sfm_name not in files:
                    (pack_stage / sfm_name).write_bytes(sfm_bytes)
                    files[sfm_name] = {
                        "bytes": len(sfm_bytes),
                        "sha256": sfm_sha,
                        "format": SURFACE_FORMAT,
                    }

                env = model["environment"]
                surf_key = f"MW34_{ident.upper()}_SURFACE_MATERIALS"
                env[surf_key] = sfm_name

                # Copy all referenced payloads from source pack into this pack
                for env_key, rel_payload in env.items():
                    if rel_payload == sfm_name:
                        continue
                    src_file = source_stage / rel_payload
                    dst_file = pack_stage / rel_payload
                    if rel_payload not in copied_payloads:
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(src_file, dst_file)
                        copied_payloads.add(rel_payload)
                        src_manifest = json.loads((source_stage / "pack.json").read_text(encoding="utf-8"))
                        pin = src_manifest["files"][rel_payload]
                        files[rel_payload] = copy.deepcopy(pin)

                req_formats = model.setdefault("required_formats", [])
                if SURFACE_FORMAT not in req_formats:
                    req_formats.append(SURFACE_FORMAT)
                model["required_formats"] = sorted(set(req_formats))

                records.append(model)

            reg_rel = "models/models.json"
            registry_data = {
                "schema_version": 2,
                "payload_profile": "prepared-native-v1",
                "models": records,
            }
            write_json(pack_stage / reg_rel, registry_data)
            reg_bytes = (pack_stage / reg_rel).read_bytes()
            files[reg_rel] = {
                "bytes": len(reg_bytes),
                "sha256": hashlib.sha256(reg_bytes).hexdigest(),
            }

            all_formats = sorted({fmt for m in records for fmt in m["required_formats"]})
            source_manifest = json.loads((source_stage / "pack.json").read_text(encoding="utf-8"))
            host_ref_sha = source_manifest["native_payload"]["reference_host_sha256"]
            manifest = {
                "schema_version": 2,
                "game_id": "mw3",
                "id": pack_id,
                "name": title,
                "version": version,
                "author": "MW3 Remaster Project",
                "category": "Mechs",
                "description": (
                    "Local prepared native visual assets with calibrated PBR surface materials "
                    "and displacement height maps; original gameplay remains in control."
                ),
                "distribution": "local-only; no redistribution clearance",
                "provides": {
                    "mechs": [m["id"] for m in records],
                    "textures": True,
                    "normal_maps": True,
                    "surface_materials": True,
                },
                "native_payload": {
                    "profile": "prepared-native-v1",
                    "registry": reg_rel,
                    "path_base": "pack-root",
                    "required_capabilities": {
                        "prepared-mechs": 1,
                        "surface-materials": 1,
                    },
                    "reference_host_sha256": host_ref_sha,
                    "required_formats": all_formats,
                },
                "files": files,
            }
            write_json(pack_stage / "pack.json", manifest)

            out_pack_path = output_dir / f"{pack_id}.mw3pack"
            partial = out_pack_path.with_suffix(".partial")
            with zipfile.ZipFile(
                partial, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True
            ) as zout:
                for item in sorted(pack_stage.rglob("*")):
                    if item.is_file():
                        zout.write(item, item.relative_to(pack_stage).as_posix())

            verify_archive(partial)
            if out_pack_path.exists():
                out_pack_path.unlink()
            partial.rename(out_pack_path)
            results[pack_suffix] = out_pack_path

    return results


def sync_active_unpacked_mod(
    mod_dir: Path,
    sfm_dir: Path,
    version: str = "1.4.0",
) -> None:
    """Synchronize the active unpacked mod directory in LocalAppData with BWSFM1 sidecars."""
    if not mod_dir.is_dir():
        print(f"Active mod directory not found: {mod_dir}")
        return

    pack_json_path = mod_dir / "pack.json"
    models_json_path = mod_dir / "models/models.json"
    if not pack_json_path.is_file() or not models_json_path.is_file():
        raise FileNotFoundError(f"Missing pack.json or models.json in {mod_dir}")

    manifest = json.loads(pack_json_path.read_text(encoding="utf-8"))
    registry = json.loads(models_json_path.read_text(encoding="utf-8"))
    files = manifest.setdefault("files", {})

    payload_dir = mod_dir / "payload"
    payload_dir.mkdir(parents=True, exist_ok=True)

    for model in registry["models"]:
        ident = model["id"]
        sfm_path = sfm_dir / f"{ident}_materials.bwsfm1"
        if not sfm_path.is_file():
            continue
        sfm_bytes = sfm_path.read_bytes()
        sfm_sha = hashlib.sha256(sfm_bytes).hexdigest()
        sfm_name = f"payload/{sfm_sha}.bin"

        target_file = mod_dir / sfm_name
        if not target_file.exists() or target_file.stat().st_size != len(sfm_bytes):
            target_file.write_bytes(sfm_bytes)

        files[sfm_name] = {
            "bytes": len(sfm_bytes),
            "sha256": sfm_sha,
            "format": SURFACE_FORMAT,
        }

        surf_key = f"MW34_{ident.upper()}_SURFACE_MATERIALS"
        model["environment"][surf_key] = sfm_name

        req_formats = model.setdefault("required_formats", [])
        if SURFACE_FORMAT not in req_formats:
            req_formats.append(SURFACE_FORMAT)
        model["required_formats"] = sorted(set(req_formats))

    write_json(models_json_path, registry)
    reg_bytes = models_json_path.read_bytes()
    files["models/models.json"] = {
        "bytes": len(reg_bytes),
        "sha256": hashlib.sha256(reg_bytes).hexdigest(),
    }

    manifest["version"] = version
    manifest.setdefault("provides", {})["surface_materials"] = True

    np_formats = manifest["native_payload"].setdefault("required_formats", [])
    if SURFACE_FORMAT not in np_formats:
        np_formats.append(SURFACE_FORMAT)
    manifest["native_payload"]["required_formats"] = sorted(set(np_formats))

    caps = manifest["native_payload"].setdefault("required_capabilities", {})
    caps[SURFACE_CAPABILITY] = 1

    write_json(pack_json_path, manifest)
    print(f"Synchronized active unpacked mod at {mod_dir} (version {version})")


MAIN_REPO = Path("D:/Projects/MW34Recomp")


def find_input(relative_path: str) -> Path:
    candidates = [
        ROOT / relative_path,
        MAIN_REPO / relative_path,
    ]
    for c in candidates:
        if c.is_file():
            return c
        if c.is_dir() and any(c.iterdir()):
            return c
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sfm-dir", type=Path, default=find_input("local/remaster"))
    parser.add_argument(
        "--training-source",
        type=Path,
        default=find_input("local/asset-packs/environments-sky-repair-20261022-r1/training-textures-1.1.1.mw3pack"),
    )
    parser.add_argument(
        "--training-output-dir",
        type=Path,
        default=ROOT / "local/asset-packs/environments-surface-materials-20261102-r1",
    )
    parser.add_argument(
        "--mech-source",
        type=Path,
        default=find_input("local/work-ahead/model-pack-1.3.0-20261024/mw3-remastered-models-1.3.0.mw3pack"),
    )
    parser.add_argument(
        "--mech-output-dir",
        type=Path,
        default=ROOT / "local/asset-packs/mechs-surface-materials-20261102-r1",
    )
    default_mod = (
        "%LOCALAPPDATA%/Packages/OpenAI.Codex_2p2nqsd0c76g0/LocalCache/Local/MW3Remaster/mods/com.mw3remaster.mw5-mechs"
    )
    parser.add_argument(
        "--active-mod-dir",
        type=Path,
        default=Path(os.path.expandvars(default_mod)),
    )
    args = parser.parse_args()

    training_sfm = args.sfm_dir / "training_materials.bwsfm1"
    if not training_sfm.is_file():
        raise FileNotFoundError(f"Missing training materials: {training_sfm}")

    training_out = args.training_output_dir / "training-textures-1.2.0.mw3pack"
    print(f"Integrating training pack -> {training_out}...")
    integrate_training_pack(args.training_source, training_sfm, training_out, version="1.2.0")
    print(f"Training pack generated and verified: {training_out}")

    # Copy to assets/MW3/Textures/
    runtime_textures = ROOT / "assets/MW3/Textures/training-textures-1.2.0.mw3pack"
    runtime_textures.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(training_out, runtime_textures)
    print(f"Copied training pack to {runtime_textures}")

    print(f"Integrating mech packs -> {args.mech_output_dir}...")
    mech_packs = integrate_mech_packs(
        args.mech_source, args.sfm_dir, args.mech_output_dir, version="0.2.0-local.20261102"
    )
    for name, path in mech_packs.items():
        print(f"Mech pack generated and verified: {name} -> {path}")

    # Also build combined 1.4.0 model pack in work-ahead
    combined_out_dir = ROOT / "local/work-ahead/model-pack-1.4.0-20261102"
    combined_out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Building combined model pack 1.4.0 -> {combined_out_dir}...")
    # To build combined pack, we can extract and add all 18 mechs
    with tempfile.TemporaryDirectory(prefix="mw3-combined-") as temp_dir:
        comb_stage = Path(temp_dir)
        with zipfile.ZipFile(args.mech_source) as z:
            z.extractall(comb_stage)
        comb_reg = json.loads((comb_stage / "models/models.json").read_text(encoding="utf-8"))
        comb_manifest = json.loads((comb_stage / "pack.json").read_text(encoding="utf-8"))
        for model in comb_reg["models"]:
            mid = model["id"]
            msfm = (args.sfm_dir / f"{mid}_materials.bwsfm1").read_bytes()
            msfm_sha = hashlib.sha256(msfm).hexdigest()
            mrel = f"payload/{msfm_sha}.bin"
            (comb_stage / mrel).write_bytes(msfm)
            comb_manifest["files"][mrel] = {
                "bytes": len(msfm),
                "sha256": msfm_sha,
                "format": SURFACE_FORMAT,
            }
            model["environment"][f"MW34_{mid.upper()}_SURFACE_MATERIALS"] = mrel
            reqs = model.setdefault("required_formats", [])
            if SURFACE_FORMAT not in reqs:
                reqs.append(SURFACE_FORMAT)
            model["required_formats"] = sorted(set(reqs))
        write_json(comb_stage / "models/models.json", comb_reg)
        comb_reg_b = (comb_stage / "models/models.json").read_bytes()
        comb_manifest["files"]["models/models.json"] = {
            "bytes": len(comb_reg_b),
            "sha256": hashlib.sha256(comb_reg_b).hexdigest(),
        }
        comb_manifest["version"] = "1.4.0"
        comb_manifest.setdefault("provides", {})["surface_materials"] = True
        comb_formats = comb_manifest["native_payload"].setdefault("required_formats", [])
        if SURFACE_FORMAT not in comb_formats:
            comb_formats.append(SURFACE_FORMAT)
        comb_manifest["native_payload"]["required_formats"] = sorted(set(comb_formats))
        comb_manifest["native_payload"].setdefault("required_capabilities", {})[SURFACE_CAPABILITY] = 1
        write_json(comb_stage / "pack.json", comb_manifest)

        comb_pack_file = combined_out_dir / "mw3-remastered-models-1.4.0.mw3pack"
        with zipfile.ZipFile(
            comb_pack_file, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True
        ) as zout:
            for item in sorted(comb_stage.rglob("*")):
                if item.is_file():
                    zout.write(item, item.relative_to(comb_stage).as_posix())
        verify_archive(comb_pack_file)
        print(f"Combined model pack generated: {comb_pack_file}")

    # Synchronize active mod directory
    if args.active_mod_dir.is_dir():
        sync_active_unpacked_mod(args.active_mod_dir, args.sfm_dir, version="1.4.0")

    print("\nAll surface material packs integrated and verified successfully!")


if __name__ == "__main__":
    main()
