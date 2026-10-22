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
for chassis in CHASSIS:
    prefix = "MW34_" + chassis.upper()
    keys = {prefix + suffix for suffix in ("_MESH", "_LOD1_MESH", "_TEXTURES", "_LOD1_TEXTURES", "_NORMALS", "_LOD1_NORMALS")}
    if chassis == "bushwacker":
        keys.remove(prefix + "_MESH")
        keys.add(prefix + "_TEST")
    SKIN_KEYS[chassis] = {prefix + lod + "_SKIN_" + skin + "_TEXTURES"
                          for lod in ("", "_LOD1") for skin in "BCDEFGH"}
    keys.update(SKIN_KEYS[chassis])
    MODEL_KEYS[chassis] = keys
ALL_MODEL_KEYS = set().union(*MODEL_KEYS.values())
MAX_BYTES = 16 * 1024**3
MAX_JSON = 2 * 1024**2
# Exact compatibility admission after reviewing the current host's 36 compiled
# chassis/LOD rows, Bushwacker skin D, BWMESH1-6/BWTEX1/BWNRM2 readers and
# rehashing their pinned sources plus the executable. See the integration note.
REVIEWED_HOST_ADMISSIONS = {
'9c578de615168724fb40664ad03b870b34b68169802cd0fae371a6f2c2d666b6': {'0dec8fa9dc1671b16744b406cea2099dd5801613c037e42dbae9bd22d5fc1d93', 'd0a79be7a0e1fe30b22ca5005fa9d3c4ff133380833f80dd6d3d751766681a0d', 'b1a3edb7ed84daf399fa4bb5f3ed246a9d718470e5f6b0fac4fc16e4961af1b6'},  # Same sky correction, guarded host FP scope.
    # Installer/readability successor preserves the complete B-H reader.
    "a99afd84ddb8fb2375197d0406186286ce8d8775399cbf75373c5a07bcd8482c": {
        "8194028a835c85e46b0963864ea04acfe400749671b1eb7f28ae63a51a2f5532",
        "9c578de615168724fb40664ad03b870b34b68169802cd0fae371a6f2c2d666b6",  # Sky backdrop classification; resource readers unchanged.
        "0dec8fa9dc1671b16744b406cea2099dd5801613c037e42dbae9bd22d5fc1d93",  # Sky backdrop classification; resource readers unchanged.
        "d0a79be7a0e1fe30b22ca5005fa9d3c4ff133380833f80dd6d3d751766681a0d",  # Sky backdrop classification; resource readers unchanged.
        "b1a3edb7ed84daf399fa4bb5f3ed246a9d718470e5f6b0fac4fc16e4961af1b6",  # Sky backdrop classification; resource readers unchanged.
        "e293b3a5f79d3d85f7c04ddcd9f857046e66583f6c7d18255e3ceb43c2cfc46c",
        "c922df9f8663315972d14376ab5ac622cf82316d8ecf78a9c5eda7ecdca9ae95",  # Rebuilt lower-horizon split host; pack readers unchanged.
    },
    "a2e3f32d40904e7e2bf6e99f426cb758f47c3a14743dcdab3dd9895d607efb74": {
        # Optional B-H selection extends skin D; BWMESH1-6/BWTEX1/BWNRM2
        # remain compatible. Exact-image interning checks dimensions/full pixels.
        "a99afd84ddb8fb2375197d0406186286ce8d8775399cbf75373c5a07bcd8482c",
        # Same mech/skin readers; audited readability merge and explicit original support paths.
        "8194028a835c85e46b0963864ea04acfe400749671b1eb7f28ae63a51a2f5532",
        "9c578de615168724fb40664ad03b870b34b68169802cd0fae371a6f2c2d666b6",  # Sky backdrop classification; resource readers unchanged.
        "0dec8fa9dc1671b16744b406cea2099dd5801613c037e42dbae9bd22d5fc1d93",  # Sky backdrop classification; resource readers unchanged.
        "d0a79be7a0e1fe30b22ca5005fa9d3c4ff133380833f80dd6d3d751766681a0d",  # Sky backdrop classification; resource readers unchanged.
        "b1a3edb7ed84daf399fa4bb5f3ed246a9d718470e5f6b0fac4fc16e4961af1b6",  # Sky backdrop classification; resource readers unchanged.
        "e293b3a5f79d3d85f7c04ddcd9f857046e66583f6c7d18255e3ceb43c2cfc46c",
        "c922df9f8663315972d14376ab5ac622cf82316d8ecf78a9c5eda7ecdca9ae95",  # Rebuilt lower-horizon split host; pack readers unchanged.
        "e3ea21dba813995bc6d47dd75f0bb5d572b4ff92c7908b8eaea57c0088e93ae7",
        # Fixture UV-anchor host: rehashed executable/snapshot and all three
        # reviewed mech readers; their source hashes are unchanged.
        "bf9c4b5e3e626ea542a52100325508897a22355c82dbb22680b90273cce62b44",
        # C4 fixture-only rebuild; the three reviewed mech readers are byte-identical.
        "7e1c939111b219f32bd765e25d840c6196c1d9c5b7cfb073ac21b949aedfa5d9",
        # Fresh-pilot keyboard services only; all 116 other pinned host sources unchanged.
        "3f34ec34ac6fb6f729a8c544b387b79b81495e7c0f250b566ef25008772b4fa2",
        # Optional mission environment reader; all mech bindings/readers unchanged.
        "0d3d920f6b560ddcd92fbeeb4034d59430ddd46a19b75269255fc8ec83fe12ef",
        # AVI read-path routing only; all mech readers and bindings unchanged.
        "33bfcf1d6c2b7454d6a21aee1421c34cadbc7b1be5783485b70499b5bc0e8afa",
        # Also admits the explicit private codec image path; remaining 116 sources unchanged.
        "9fd17ba2459ac2d349adda33c0c84d41772bbd2ec7c0e2a620242c696526bb83",
        # Explicit installed original provider paths; all mech readers unchanged.
        "c1afedadd8ed9e13a956db917a1a5335a6581fac01374b367969d4e985852115"
    }
}


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


def compose(roots, host, verification=None):
    """Return selected records and a clean runtime environment; first chassis wins."""
    environment = {k: v for k, v in host.get("runtime_environment", {}).items() if k not in ALL_MODEL_KEYS}
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
        # These prepared-resource packs currently define no dependency-version
        # semantics. Reject such declarations rather than silently ignoring them.
        if manifest.get("dependencies") or manifest.get("conflicts"):
            raise ValueError("Dependency/conflict declarations are not supported for prepared-native-v1 yet")
        payload = manifest.get("native_payload", {})
        if (manifest.get("schema_version") != 2 or payload.get("profile") != "prepared-native-v1" or
                payload.get("path_base") != "pack-root" or payload.get("registry") != "models/models.json"):
            raise ValueError("Unsupported installed pack schema/profile")
        reference = payload.get("reference_host_sha256", "").lower()
        actual = host.get("executable_sha256", "").lower()
        # Explicit identity pairs are authored after reviewing a newer host's
        # compiled bindings. A pack cannot admit itself to an arbitrary host.
        admissions = REVIEWED_HOST_ADMISSIONS.get(reference, set())
        if not re.fullmatch(r"[0-9a-f]{64}", actual) or (actual != reference and actual not in admissions):
            raise ValueError("Prepared mech pack requires an explicitly admitted native host: " + reference)
        formats = {"BWTEX1"}
        formats.update("BWMESH" + str(v) for v in host.get("mesh_payload_versions", []))
        formats.update("BWNRM" + str(v) for v in host.get("normal_map_formats", []))
        if not set(payload.get("required_formats", [])).issubset(formats):
            raise ValueError("Native host lacks required pack formats")
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
            required = MODEL_KEYS[ident] - SKIN_KEYS[ident]
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
                expected = "BWNRM2" if key.endswith("_NORMALS") else "BWTEX1" if key.endswith("_TEXTURES") else None
                if (expected and fmt != expected) or (not expected and not fmt.startswith("BWMESH")):
                    raise ValueError("Incorrect model binding format")
                if fmt not in model.get("required_formats", []) or fmt not in payload.get("required_formats", []):
                    raise ValueError("Undeclared model format")
                resolved[key] = verified[name]
            if ident not in selected:
                selected[ident] = dict(id=ident, name=model["name"], status=model["status"], backend="native",
                    environment=resolved, required_files=list(resolved.values()),
                    skins=[{"id": skin} for skin in skins],
                    required_native_mesh_format=max(int(f[6:]) for f in model["required_formats"] if f.startswith("BWMESH")))
        if set(manifest.get("provides", {}).get("mechs", [])) != ids:
            raise ValueError("Pack chassis declaration differs from registry")
    for model in selected.values():
        environment.update(model["environment"])
    return list(selected.values()), environment
