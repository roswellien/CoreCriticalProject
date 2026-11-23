"""Validate installed prepared mech content and compose whole-chassis bindings.

Pack paths and metadata are untrusted. Host admissions belong to the authored
launch profile, never a content pack. This module does not execute pack code.
"""
import hashlib
import json
from pathlib import Path
import re

CHASSIS = "bushwacker madcat vulture thor orion daishi shadowcat puma annihilator cauldron sunder supernova blackhawk champion strider avatar owens firefly".split()
MODEL_KEYS = {}
SKIN_KEYS = {}
SURFACE_KEYS = {}
for chassis in CHASSIS:
    prefix = "MW34_" + chassis.upper()
    keys = {prefix + suffix for suffix in ("_MESH", "_LOD1_MESH", "_TEXTURES", "_LOD1_TEXTURES", "_NORMALS", "_LOD1_NORMALS")}
    if chassis == "bushwacker":
        keys.remove(prefix + "_MESH")
        keys.add(prefix + "_TEST")
    SKIN_KEYS[chassis] = {prefix + lod + "_SKIN_" + skin + "_TEXTURES"
                          for lod in ("", "_LOD1") for skin in "BCDEFGH"}
    SURFACE_KEYS[chassis] = {prefix + "_SURFACE_MATERIALS", prefix + "_LOD1_SURFACE_MATERIALS"}
    keys.update(SKIN_KEYS[chassis])
    keys.update(SURFACE_KEYS[chassis])
    MODEL_KEYS[chassis] = keys
ALL_MODEL_KEYS = set().union(*MODEL_KEYS.values())
MAX_BYTES = 16 * 1024**3
MAX_JSON = 2 * 1024**2


def read_json(path):
    if path.stat().st_size > MAX_JSON:
        raise ValueError("Pack JSON exceeds size limit")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique)


def resolve(root, name):
    if not isinstance(name, str) or not name or len(name) > 240 or "\\" in name:
        raise ValueError("Invalid pack path")
    parts = name.split("/")
    for part in parts:
        if (not part or part in (".", "..") or part[-1] in ". " or
                any(ord(c) < 32 or c in '<>:"|?*' for c in part) or
                re.fullmatch(r"CON|CONIN\$|CONOUT\$|PRN|AUX|NUL|COM[0-9Â¹Â²Â³]|LPT[0-9Â¹Â²Â³]", part.split(".")[0], re.I)):
            raise ValueError("Unsafe pack path: " + name)
    path = root.joinpath(*parts)
    for item in (path, *path.parents):
        if item.is_symlink() or (hasattr(item, "is_junction") and item.is_junction()):
            raise ValueError("Links are not supported in installed packs")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Pack path leaves installed root")
    return path.resolve()


def canonical_pack_root(directory):
    """Anchor containment to the actual manifest opened by Windows.

    MSIX filesystem virtualization can redirect an existing file while resolving
    its directory still returns the logical path. Reject links first, then use
    the manifest's physical parent as the resource root. Descendant containment
    checks remain strict and do not permit per-file escapes.
    """
    declared = Path(directory).absolute()
    manifest = declared / "pack.json"
    for item in (manifest, *manifest.parents):
        if item.is_symlink() or (hasattr(item, "is_junction") and item.is_junction()):
            raise ValueError("Links are not supported in installed packs")
    return manifest.resolve(strict=True).parent


def compose(roots, host, verification=None, chassis_records=None):
    """Return selected records and a clean runtime environment; first chassis wins."""
    environment = {k: v for k, v in host.get("runtime_environment", {}).items()
                   if k not in ALL_MODEL_KEYS
                   and k not in ('MW34_ADDITIONAL_SKINS', 'MW34_ADDITIONAL_CHASSIS')
                   and not (k.startswith("MW34_CHASSIS_") and k.endswith("_SURFACE_MATERIALS"))}
    selected = {}
    metadata = []
    enabled_ids = set()
    for directory in roots:
        root = canonical_pack_root(directory)
        manifest = read_json(resolve(root, "pack.json"))
        ident = manifest.get("id", "")
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,127}", ident) or ident in enabled_ids:
            raise ValueError("Invalid or duplicate enabled pack ID")
        enabled_ids.add(ident)
        metadata.append((root, manifest))
    for root, manifest in metadata:
        if manifest.get('native_payload', {}).get('profile') == 'additional-chassis-v1':
            if chassis_records is None:
                raise ValueError('Additional chassis packs require the current launcher coordinator')
            continue
        if manifest.get('native_payload', {}).get('profile') == 'prepared-skins-v1':
            continue  # Additions compose after the winning chassis is known.
        # These prepared-resource packs currently define no dependency-version
        # semantics. Reject such declarations rather than silently ignoring them.
        if manifest.get("dependencies") or manifest.get("conflicts"):
            raise ValueError("Dependency/conflict declarations are not supported for prepared-native-v1 yet")
        payload = manifest.get("native_payload", {})
        if (manifest.get("schema_version") != 2 or payload.get("profile") != "prepared-native-v1" or
                payload.get("path_base") != "pack-root" or payload.get("registry") != "models/models.json"):
            raise ValueError("Unsupported installed pack schema/profile")
        from content_capabilities import advertised, require
        from surface_materials import (
            CAPABILITY as SURFACE_CAPABILITY,
            FORMAT as SURFACE_FORMAT,
            mesh_uv_identity_file,
            read_surface_materials_file,
            texture_batch_materials_file,
        )
        require(host, payload, ident)
        formats = {"BWTEX1"}
        formats.update("BWMESH" + str(v) for v in host.get("mesh_payload_versions", []))
        formats.update("BWNRM" + str(v) for v in host.get("normal_map_formats", []))
        if 1 in advertised(host).get(SURFACE_CAPABILITY, []):
            formats.add(SURFACE_FORMAT)
        if not set(payload.get("required_formats", [])).issubset(formats):
            raise ValueError("Native host lacks required pack formats")
        if (SURFACE_FORMAT in payload.get("required_formats", [])
                and payload.get("required_capabilities", {}).get(SURFACE_CAPABILITY) != 1):
            raise ValueError("Surface material format requires surface-materials capability version 1")
        files = manifest.get("files", {})
        if not files or len(files) > 10000:
            raise ValueError("Missing or excessive pack file table")
        seen = {"pack.json"}
        verified = {}
        total = 0
        for name, pin in files.items():
            if name.casefold() in seen:
                raise ValueError("Colliding pack paths")
            seen.add(name.casefold())
            path = resolve(root, name)
            size = pin.get("bytes")
            if type(size) is not int or size < 0 or size > MAX_BYTES:
                raise ValueError("Invalid pack member size")
            total += size
            if total > MAX_BYTES or not path.is_file() or path.stat().st_size != size:
                raise ValueError("Pack member missing or incorrect size: " + name)
            if verification is not None:
                digest = verification.digest(path, pin.get("sha256", "").lower())
            else:
                with path.open("rb") as stream:
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != pin.get("sha256", "").lower():
                raise ValueError("Pack member hash mismatch: " + name)
            fmt = pin.get("format")
            if fmt:
                with path.open("rb") as stream:
                    magic = stream.read(8).rstrip(b"\0").decode("ascii")
                if fmt not in formats or fmt != magic:
                    raise ValueError("Unsupported/mislabeled native payload")
            verified[name] = str(path)
        registry_name = payload["registry"]
        if registry_name not in verified:
            raise ValueError("Undeclared pack registry")
        registry = read_json(Path(verified[registry_name]))
        if registry.get("schema_version") != 2 or registry.get("payload_profile") != "prepared-native-v1":
            raise ValueError("Unsupported prepared model registry")
        ids = set()
        for model in registry.get("models", []):
            ident = model.get("id")
            if ident not in MODEL_KEYS or ident in ids or ident not in host.get("model_ids", []):
                raise ValueError("Duplicate or unsupported chassis: " + str(ident))
            ids.add(ident)
            skins = model.get("skin_ids", [])
            if (not isinstance(skins,list) or any(not isinstance(skin,str) or skin not in list('bcdefgh') for skin in skins) or
                    len(skins)!=len(set(skins))):
                raise ValueError("Invalid alternate skin declaration")
            if (model.get("backend") != "native" or model.get("status") not in ("runtime-ready", "runtime-candidate") or
                    not set(skins).issubset(host.get("skin_ids", {}).get(ident, [])) or
                    not set(model.get("required_formats", [])).issubset(formats)):
                raise ValueError("Unsupported model status, skins or formats")
            if model["status"] == "runtime-candidate" and not host.get("include_runtime_candidates", False):
                raise ValueError("Enable runtime candidates explicitly to use this mech pack")
            bindings = model.get("environment", {})
            required = MODEL_KEYS[ident] - SKIN_KEYS[ident] - SURFACE_KEYS[ident]
            skin_keys = {"MW34_"+ident.upper()+lod+"_SKIN_"+skin.upper()+"_TEXTURES"
                         for skin in skins for lod in ('','_LOD1')}
            if set(bindings) & SKIN_KEYS[ident] != skin_keys:
                raise ValueError("Alternate skin declaration differs from its close/distance bindings")
            if not required.issubset(bindings) or not set(bindings).issubset(MODEL_KEYS[ident]):
                raise ValueError("Incomplete or unsupported chassis bindings")
            resolved = {}
            for key, name in bindings.items():
                if name not in verified:
                    raise ValueError("Undeclared model payload")
                fmt = files[name].get("format", "")
                expected = (
                    SURFACE_FORMAT if key.endswith("_SURFACE_MATERIALS")
                    else "BWNRM2" if key.endswith("_NORMALS")
                    else "BWTEX1" if key.endswith("_TEXTURES")
                    else None
                )
                if (expected and fmt != expected) or (not expected and not fmt.startswith("BWMESH")):
                    raise ValueError("Incorrect model binding format")
                if fmt not in model.get("required_formats", []) or fmt not in payload.get("required_formats", []):
                    raise ValueError("Undeclared model format")
                resolved[key] = verified[name]
            for lod, suffix in (("close", ""), ("distance", "_LOD1")):
                surf_key = "MW34_" + ident.upper() + suffix + "_SURFACE_MATERIALS"
                if surf_key not in resolved:
                    continue
                if payload.get("required_capabilities", {}).get(SURFACE_CAPABILITY) != 1:
                    raise ValueError("Surface material bindings require surface-materials capability version 1")
                mesh_key = ("MW34_BUSHWACKER_TEST" if ident == "bushwacker" and not suffix
                            else "MW34_" + ident.upper() + suffix + "_MESH")
                tex_key = "MW34_" + ident.upper() + suffix + "_TEXTURES"
                read_surface_materials_file(
                    Path(resolved[surf_key]),
                    expected_asset_id=f"{ident}:{lod}",
                    expected_mesh_uv_hash=mesh_uv_identity_file(Path(resolved[mesh_key])),
                    expected_batch_materials=texture_batch_materials_file(Path(resolved[tex_key])),
                )
            if ident not in selected:
                selected[ident] = dict(id=ident, name=model["name"], status=model["status"], backend="native",
                    environment=resolved, required_files=list(resolved.values()),
                    skins=[{"id": skin} for skin in skins],
                    required_native_mesh_format=max(int(f[6:]) for f in model["required_formats"] if f.startswith("BWMESH")))
        if set(manifest.get("provides", {}).get("mechs", [])) != ids:
            raise ValueError("Pack chassis declaration differs from registry")
    for model in selected.values():
        environment.update(model["environment"])
    added = []
    if chassis_records is not None:
        from prepared_chassis_packs import select as select_chassis
        added = select_chassis(metadata, host, verification, host.get('mech_appearance'))
        chassis_records.extend(added)
    from prepared_skin_packs import select
    visual_records = [record for record in added if 'visuals' in record['registration']]
    views = [dict(id=r['registration']['id'], visuals=r['registration']['visuals']) for r in visual_records]
    select(metadata, host, list(selected.values()) + views, verification)
    for record, view in zip(visual_records, views):
        if 'additional_skins' in view:
            record['additional_skins'] = view['additional_skins']
    return list(selected.values()), environment
