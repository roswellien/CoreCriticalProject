"""MW3-RE argv planning; lexical validation is not package/execution admission.

Schemas 2 and 3 are pure. Schema 4 (the labelled Native preview) also reads the pack manifests
and bounded lighting-catalog headers it is given to turn installed packs into arguments. Named
skin selections write the existing BWSKIN1 catalog below the isolated native write directory.
"""

from pathlib import Path, PureWindowsPath
import hashlib
import json
import math
import re
import struct


_FIELDS = frozenset({
    "schema_version", "engine", "runtime_root", "executable", "game_dir", "write_dir", "renderer",
    "width", "height", "aa", "af", "window_mode", "render_thread", "lighting", "assets",
})
_OPTIONAL_FIELDS = frozenset({"indeo_codec", "flare_style", "disk_cache", "vsync", "supports_vsync"})
_AA = {"off": "off", "1": "off", "fxaa": "fxaa", "2": "ssaa2", "4": "ssaa4"}
_MAX_JSON_BYTES = 2 * 1024 * 1024
_MAX_JSON_DEPTH = 64
# Pack manifests and model registries are small JSON files. Lighting catalogs are read only
# far enough to validate their bounded format headers and exact MWFX1 record size.
_MAX_MANIFEST_BYTES = 4 * 1024 * 1024
_MAX_PREVIEW_PACKS = 64
_MAX_REGISTRY_MODELS = 256
_PREVIEW_FIELDS = frozenset({"draw_distance", "fog_distance", "hud", "hud_text", "geometry", "model_packs",
                             "environment_packs", "ui_packs", "skin_packs", "dynamic_lighting", "shadows",
                             "headlights", "water_detail", "cloud_detail",
                             "headlight_bindings", "stock_effect_catalog",
                             "stock_headlight_catalog"})
# Keep the planner in step with kViewDistanceOptions; 800 is the original scenery range.
_PREVIEW_DRAW_DISTANCES = (800, 1200, 1600, 2400, 3200)
_PREVIEW_HUDS = ("original", "core-critical")
_PREVIEW_GEOMETRY = ("legacy", "partial")
_RUNTIME_MODEL_STATUSES = ("runtime-ready", "runtime-candidate")
# Texture table offsets are unsigned 32-bit values, so native packs can be at most 4 GiB.
_NATIVE_FILE_LIMIT = 2 ** 32

# BWSFM1 model sidecars are validated here as well as by the authoring tools because the
# packaged launcher runs this file with Python isolated mode and ships no sibling modules.
_MAX_MESH_BATCHES = 256
_MAX_TEXTURE_BATCHES = 4096
_MAX_TEXTURE_MATERIALS = 64
_MAX_IDENTIFIER_BYTES = 4096
_MAX_MATERIAL_NAME_BYTES = 31
_MAX_SURFACE_RECORDS = 4096
_MAX_SURFACE_IMAGES = 512
_MAX_SURFACE_DIMENSION = 4096
MAX_SIDECAR_BYTES = 512 * 1024 * 1024
# Decoded scalar-image budget per sidecar. The contract counts one retained byte per texel for
# both v1 (RGBA, red channel kept) and v2 (grayscale). It equals the file cap today, but stays a
# separate name so tests can lower it without the file-size gate hiding the per-texel accounting.
_MAX_SURFACE_DECODED_BYTES = MAX_SIDECAR_BYTES
_NO_SURFACE_MATERIAL = 0xFFFFFFFF
_NO_SURFACE_IMAGE = 0xFFFFFFFF
_ROLE_HEIGHT = 1
_ROLE_THICKNESS = 2
_ADDRESS_MODES = (1, 2, 3)
_SAFE_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]+\Z")
_SAFE_MATERIAL_NAME = re.compile(r"[A-Za-z0-9_.-]{1,31}\Z")


def _planner_identifier(value, label, maximum=_MAX_IDENTIFIER_BYTES):
    if not isinstance(value, str) or not value:
        raise ValueError(f"Invalid {label}")
    encoded = value.encode("utf-8")
    if (len(encoded) > maximum or "\0" in value or ".." in value or "/" in value or
            "\\" in value or not _SAFE_IDENTIFIER.fullmatch(value)):
        raise ValueError(f"Invalid {label}: {value!r}")
    return encoded


def _planner_material_name(value):
    if (not isinstance(value, str) or ".." in value or
            not _SAFE_MATERIAL_NAME.fullmatch(value)):
        raise ValueError(f"Invalid surface material name: {value!r}")
    return value.encode("ascii")


def _planner_f32(value, label, low, high):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"Nonfinite {label}")
    rounded = struct.unpack("<f", struct.pack("<f", float(value)))[0]
    if not math.isfinite(rounded) or not low <= rounded <= high:
        raise ValueError(f"Out-of-range {label}: {value}")
    return rounded


def _mesh_uv_identity_file(path):
    """Hash batch counts and vertex streams using the BWSFM1 mesh identity contract."""
    with Path(path).open("rb") as stream:
        def take(size):
            chunk = stream.read(size)
            if len(chunk) != size:
                raise ValueError("Truncated mesh payload for UV identity")
            return chunk

        magic = take(8)
        guard = magic == b"BWMESH7\0"
        donor = magic == b"BWMESH4\0"
        anchored = magic == b"BWMESH6\0"
        layered = anchored or magic == b"BWMESH5\0"
        placement = layered or magic == b"BWMESH3\0"
        visibility = guard or donor or placement or magic == b"BWMESH2\0"
        if not visibility and magic != b"BWMESH1\0":
            raise ValueError("Unsupported mesh payload format for UV identity")
        count = struct.unpack("<I", take(4))[0]
        if not 1 <= count <= _MAX_MESH_BATCHES:
            raise ValueError("Invalid mesh batch count for UV identity")
        if guard:
            samples = struct.unpack("<I", take(4))[0]
            if not 4 <= samples <= 4096:
                raise ValueError("Invalid Orion guard fit sample count")
            # Clearance moves the rigid batch at draw time; it does not alter UV identity.
            take(24 + 104 * samples)
        if donor:
            bones, refs, flags = struct.unpack("<III", take(12))
            if not 1 <= bones <= 256 or not 1 <= refs <= 128 or flags > 3:
                raise ValueError("Invalid donor rig header in mesh payload")
            take(40)
            for _ in range(bones):
                take(32 + 32 + 4 + 128)
            for _ in range(refs):
                take(32 + 128)

        value = 0xCBF29CE484222325
        for byte in struct.pack("<I", count):
            value = ((value ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
        for _ in range(count):
            take(32)
            if visibility:
                take(32)
            if guard and struct.unpack("<I", take(4))[0] > 2:
                raise ValueError("Invalid Orion guard side")
            if placement:
                take(32 + 12)
            if layered:
                take(32 + 12)
            if anchored:
                take(32 + 12)
            donor_bone = struct.unpack("<I", take(4))[0] if donor else 0
            vertex_count, _color = struct.unpack("<II", take(8))
            if not 1 <= vertex_count <= 65535 or vertex_count % 3:
                raise ValueError("Invalid mesh vertex count for UV identity")
            vertices = take(vertex_count * 32)
            if donor and donor_bone == 0xFFFFFFFF:
                take(vertex_count * 4)
            for byte in struct.pack("<I", vertex_count):
                value = ((value ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
            for byte in vertices:
                value = ((value ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
        if stream.read(1):
            raise ValueError("Trailing mesh payload data")
        return value


def _texture_batch_materials_file(path):
    """Read BWTEX1 batch bindings and material names with bounded streaming reads."""
    with Path(path).open("rb") as stream:
        def take(size):
            chunk = stream.read(size)
            if len(chunk) != size:
                raise ValueError("Truncated BWTEX1 payload")
            return chunk

        if take(8) != b"BWTEX1\0\0":
            raise ValueError("Expected BWTEX1 payload")
        batches, count = struct.unpack("<II", take(8))
        if not 1 <= batches <= _MAX_TEXTURE_BATCHES or not 1 <= count <= _MAX_TEXTURE_MATERIALS:
            raise ValueError("Invalid BWTEX1 batch/material counts")
        bindings = struct.unpack("<" + "I" * batches, take(batches * 4))
        if any(index >= count for index in bindings):
            raise ValueError("Invalid BWTEX1 material binding index")
        names = []
        for _ in range(count):
            raw_name = take(32)
            if not raw_name[0] or raw_name[31]:
                raise ValueError("Invalid BWTEX1 material name")
            name = raw_name.split(b"\0", 1)[0].decode("ascii")
            if ".." in name or not _SAFE_MATERIAL_NAME.fullmatch(name):
                raise ValueError("Unsafe BWTEX1 material name")
            width, height, _image_hash = struct.unpack("<IIQ", take(16))
            if not 1 <= width <= _MAX_SURFACE_DIMENSION or not 1 <= height <= _MAX_SURFACE_DIMENSION:
                raise ValueError("Invalid BWTEX1 dimensions")
            remaining = width * height * 2
            while remaining:
                chunk = take(min(remaining, 1024 * 1024))
                remaining -= len(chunk)
            names.append(name)
        if stream.read(1):
            raise ValueError("Trailing BWTEX1 data")
        return [names[index] for index in bindings]


def read_surface_materials_file(path, *, expected_asset_id=None, expected_mesh_uv_hash=None,
                                expected_batch_materials=None, max_bytes=MAX_SIDECAR_BYTES):
    """Validate the bounded BWSFM1 sidecar contract needed by the isolated launcher planner."""
    if type(max_bytes) is not int or not 0 < max_bytes <= MAX_SIDECAR_BYTES:
        raise ValueError("Invalid surface material budget")
    with Path(path).open("rb") as stream:
        data = stream.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError("Surface material sidecar exceeds size budget")
    if expected_asset_id is not None:
        _planner_identifier(expected_asset_id, "expected_asset_id")
    if expected_batch_materials is not None:
        if not isinstance(expected_batch_materials, list) or not 1 <= len(expected_batch_materials) <= _MAX_TEXTURE_BATCHES:
            raise ValueError("Invalid expected_batch_materials")
        for material_name in expected_batch_materials:
            _planner_material_name(material_name)

    offset = 0

    def take(size):
        nonlocal offset
        if size < 0 or offset + size > len(data):
            raise ValueError("Truncated surface material sidecar")
        value = data[offset:offset + size]
        offset += size
        return value

    def u32():
        return struct.unpack("<I", take(4))[0]

    def text(label, limit):
        length = u32()
        if not 1 <= length <= limit:
            raise ValueError(f"Invalid {label} length")
        raw = take(length)
        if b"\0" in raw:
            raise ValueError(f"Embedded NUL in {label}")
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise ValueError(f"Invalid UTF-8 in {label}") from error
        if label == "material_name":
            _planner_material_name(decoded)
        else:
            _planner_identifier(decoded, label, limit)
        return decoded

    if take(8) != b"BWSFM1\0\0":
        raise ValueError("Unsupported surface material magic")
    version, batch_count, record_count, image_count, mesh_uv_hash = struct.unpack("<IIIIQ", take(24))
    if version not in (1, 2):
        raise ValueError(f"Unsupported surface material version: {version}")
    if (not 1 <= batch_count <= _MAX_TEXTURE_BATCHES or record_count > _MAX_SURFACE_RECORDS or
            image_count > _MAX_SURFACE_IMAGES):
        raise ValueError("Invalid surface material counts")
    if expected_mesh_uv_hash is not None and mesh_uv_hash != expected_mesh_uv_hash:
        raise ValueError("Surface material mesh/UV compatibility hash mismatch")
    if expected_batch_materials is not None and len(expected_batch_materials) != batch_count:
        raise ValueError("Surface material batch count mismatch")
    bindings = struct.unpack("<" + "I" * batch_count, take(batch_count * 4))
    if any(index != _NO_SURFACE_MATERIAL and index >= record_count for index in bindings):
        raise ValueError("Surface material batch binding out of range")

    records = []
    previous_key = None
    for _ in range(record_count):
        asset_id = text("asset_id", _MAX_IDENTIFIER_BYTES)
        if expected_asset_id is not None and asset_id != expected_asset_id:
            raise ValueError("Surface material asset_id mismatch")
        material_name = text("material_name", _MAX_MATERIAL_NAME_BYTES)
        key = (asset_id.encode("utf-8"), material_name.encode("ascii"))
        if previous_key is not None and key <= previous_key:
            raise ValueError("Duplicate or unsorted surface material record")
        previous_key = key
        fields = struct.unpack("<IIfffIffffIIfffffffffffff", take(100))
        (height_index, thickness_index, height_reference, height_amplitude, max_displacement,
         tessellation_cap, scale_u, scale_v, offset_u, offset_v, address_u, address_v,
         atlas_min_u, atlas_min_v, atlas_max_u, atlas_max_v, sss_participation,
         tint_r, tint_g, tint_b, sss_radius, thickness_scale, roughness, reflectivity,
         metallic) = fields
        if height_index != _NO_SURFACE_IMAGE and height_index >= image_count:
            raise ValueError("height_image index out of range")
        if thickness_index != _NO_SURFACE_IMAGE and thickness_index >= image_count:
            raise ValueError("thickness_image index out of range")
        _planner_f32(height_reference, "height_reference", 0.0, 1.0)
        _planner_f32(height_amplitude, "height_amplitude", -16.0, 16.0)
        _planner_f32(max_displacement, "max_displacement", 0.0, 16.0)
        if max_displacement < abs(height_amplitude):
            raise ValueError("max_displacement < abs(height_amplitude)")
        if height_index == _NO_SURFACE_IMAGE and (height_amplitude != 0.0 or max_displacement != 0.0):
            raise ValueError("Non-zero height parameters without height_image")
        if not 1 <= tessellation_cap <= 8 or (height_index == _NO_SURFACE_IMAGE and tessellation_cap != 1):
            raise ValueError("Invalid tessellation_cap")
        for value, label in ((scale_u, "uv_scale[0]"), (scale_v, "uv_scale[1]")):
            _planner_f32(value, label, -1024.0, 1024.0)
        if scale_u == 0.0 or scale_v == 0.0:
            raise ValueError("Zero uv_scale component")
        _planner_f32(offset_u, "uv_offset[0]", -1024.0, 1024.0)
        _planner_f32(offset_v, "uv_offset[1]", -1024.0, 1024.0)
        if address_u not in _ADDRESS_MODES or address_v not in _ADDRESS_MODES:
            raise ValueError("Invalid UV address mode")
        for value in (atlas_min_u, atlas_min_v, atlas_max_u, atlas_max_v):
            _planner_f32(value, "atlas_rect", 0.0, 1.0)
        if not atlas_min_u < atlas_max_u or not atlas_min_v < atlas_max_v:
            raise ValueError("Invalid atlas_rect bounds")
        _planner_f32(sss_participation, "sss_participation", 0.0, 1.0)
        for value in (tint_r, tint_g, tint_b):
            _planner_f32(value, "sss_tint", 0.0, 1.0)
        _planner_f32(sss_radius, "sss_radius", 0.0, 16.0)
        _planner_f32(thickness_scale, "thickness_scale", 0.0, 16.0)
        if sss_participation == 0.0 and (sss_radius != 0.0 or thickness_scale != 0.0 or
                                         thickness_index != _NO_SURFACE_IMAGE):
            raise ValueError("SSS parameters set while sss_participation is zero")
        for value, label in ((roughness, "roughness"), (reflectivity, "reflectivity"),
                             (metallic, "metallic")):
            _planner_f32(value, label, 0.0, 1.0)
        records.append({"material_name": material_name, "height_image": height_index,
                        "thickness_image": thickness_index})

    images = []
    previous_name = None
    decoded_total = 0
    for _ in range(image_count):
        image_name = text("image_name", _MAX_IDENTIFIER_BYTES)
        image_key = image_name.encode("utf-8")
        if previous_name is not None and image_key <= previous_name:
            raise ValueError("Duplicate or unsorted surface material image name")
        previous_name = image_key
        role, width, height, expected_hash = struct.unpack("<IIIQ", take(20))
        if (role not in (_ROLE_HEIGHT, _ROLE_THICKNESS) or
                not 1 <= width <= _MAX_SURFACE_DIMENSION or
                not 1 <= height <= _MAX_SURFACE_DIMENSION):
            raise ValueError("Invalid surface material image header")
        pixel_count = width * height
        # v1 stores RGBA but only the red scalar is retained, so both versions decode to one
        # byte per texel; the stored bytes are still read and hashed in full below.
        stored_byte_count = pixel_count * (4 if version == 1 else 1)
        decoded_budget = min(max_bytes, _MAX_SURFACE_DECODED_BYTES)
        if decoded_total + pixel_count > decoded_budget:
            raise ValueError("Surface material decoded images exceed budget")
        decoded_total += pixel_count
        pixels = take(stored_byte_count)
        actual_hash = 0xCBF29CE484222325
        for byte in pixels:
            actual_hash = ((actual_hash ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
        if actual_hash != expected_hash:
            raise ValueError("Surface material image hash mismatch")
        images.append(role)
    if offset != len(data):
        raise ValueError("Trailing surface material data")
    for record in records:
        height_index = record["height_image"]
        if height_index != _NO_SURFACE_IMAGE and images[height_index] != _ROLE_HEIGHT:
            raise ValueError("height_image references a non-height image")
        thickness_index = record["thickness_image"]
        if thickness_index != _NO_SURFACE_IMAGE and images[thickness_index] != _ROLE_THICKNESS:
            raise ValueError("thickness_image references a non-thickness image")
    if expected_batch_materials is not None:
        for batch_index, record_index in enumerate(bindings):
            if (record_index != _NO_SURFACE_MATERIAL and
                    records[record_index]["material_name"] != expected_batch_materials[batch_index]):
                raise ValueError("Surface material binding disagrees with batch albedo material")
    return {"version": version, "mesh_uv_hash": mesh_uv_hash, "bindings": list(bindings)}


def plan_json(raw):
    """Plan bounded raw JSON, rejecting duplicate properties before dict conversion."""
    if type(raw) not in (str, bytes) or len(raw) > _MAX_JSON_BYTES:
        raise ValueError("Invalid native request JSON size or type")
    if type(raw) is bytes:
        raw = raw.decode("utf-8", errors="strict")
    if len(raw.encode("utf-8")) > _MAX_JSON_BYTES:
        raise ValueError("Native request JSON is too large")
    # Bound nesting before the recursive JSON decoder, ignoring delimiters inside strings.
    depth = 0
    in_string = False
    escaped = False
    for character in raw:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        elif character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > _MAX_JSON_DEPTH:
                raise ValueError("Native request JSON is too deep")
        elif character in "]}":
            depth -= 1

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate native request property")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError("Non-finite native request JSON number")

    return plan_launch(json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant))


def _windows_path(value, *, directory=True):
    """Check raw components before PureWindowsPath can collapse aliases."""
    if type(value) is not str or not value or re.match(r"[A-Za-z]:[\\/]", value) is None:
        raise ValueError("Invalid Windows path")
    names = value[2:].replace("\\", "/").split("/")
    names.pop(0)
    if directory and names and names[-1] == "":
        names.pop()
    if not names and not directory:
        raise ValueError("Invalid Windows path")
    device = re.compile(r"CON(?:IN\$|OUT\$)?|PRN|AUX|NUL|COM[0-9¹²³]|LPT[0-9¹²³]", re.IGNORECASE)
    for name in names:
        if (not name or name in (".", "..") or name.endswith((".", " "))
                or any(ord(character) < 32 or character in '<>:"|?*' for character in name)
                or device.fullmatch(name.split(".", 1)[0]) is not None):
            raise ValueError("Invalid Windows path component")
    return PureWindowsPath(value)


def _check_depth(text, limit=_MAX_JSON_DEPTH):
    """Bound nesting before the recursive JSON decoder, ignoring delimiters inside strings."""
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
        elif character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > limit:
                raise ValueError("Pack JSON is too deep")
        elif character in "]}":
            depth -= 1


def _read_pack_json(path):
    """Read one small pack manifest/registry, rejecting duplicates and non-finite numbers."""
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"Pack file is missing: {path}")
    if path.stat().st_size > _MAX_MANIFEST_BYTES:
        raise ValueError(f"Pack file is too large: {path}")
    text = path.read_text(encoding="utf-8-sig")
    _check_depth(text)

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate property in pack file: {path}")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError(f"Non-finite number in pack file: {path}")

    return json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_constant)


def _pack_member(root, relative):
    """Resolve a registry path inside its pack root and return it as an absolute path string.

    Registry values are relative to the pack root. The game's working directory is the runtime
    folder, so it must receive absolute paths.
    """
    if type(relative) is not str or not relative:
        raise ValueError(f"Invalid pack member path in {root}")
    parts = relative.replace("\\", "/").split("/")
    if re.match(r"[A-Za-z]:", relative) or relative.startswith(("/", "\\")) or ".." in parts or "" in parts:
        raise ValueError(f"Pack member path leaves its pack: {relative}")
    member = Path(root, *parts)
    if not member.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError(f"Pack member path leaves its pack: {relative}")
    if not member.is_file():
        raise ValueError(f"Pack member is missing: {member}")
    return str(member)


def _pack_payload(root, profile):
    """Return the pack's native_payload after checking it is the expected prepared profile."""
    manifest = _read_pack_json(Path(root, "pack.json"))
    payload = manifest.get("native_payload") if type(manifest) is dict else None
    if type(payload) is not dict or payload.get("profile") != profile:
        raise ValueError(f"Pack is not a {profile} pack: {root}")
    return manifest, payload


def _model_pack_arguments(root, taken=None):
    """Turn a prepared-native-v1 mech pack into prepared-model CLI arguments.

    `taken` maps each chassis already supplied by an earlier enabled pack to that pack's root. Such a
    chassis is left out of this pack, the same "first chassis wins" rule as prepared_mech_packs.py,
    because the native runtime refuses a second model or normal map for one chassis and level.
    Returns arguments, chassis lost to earlier packs, and skipped optional materials.

    The registry lists models; each keeps its file paths in an "environment" table using the
    names MW34_<ID>_MESH, MW34_<ID>_TEXTURES and MW34_<ID>_NORMALS, with LOD1_ after <ID> for
    the distance model. A level of detail is emitted only when both its mesh and textures exist.
    Optional BWSFM1 sidecars use MW34_<ID>[_LOD1]_SURFACE_MATERIALS keys.
    Alternative liveries preserve the retail B-H indices at both levels of detail.
    """
    _, payload = _pack_payload(root, "prepared-native-v1")
    if payload.get("path_base") != "pack-root":
        raise ValueError(f"Mech pack paths must be relative to the pack root: {root}")
    registry = _read_pack_json(_pack_member(root, payload.get("registry")))
    models = registry.get("models") if type(registry) is dict else None
    if type(models) is not list or len(models) > _MAX_REGISTRY_MODELS:
        raise ValueError(f"Invalid mech pack registry: {root}")
    arguments = []
    overridden = []
    skipped_materials = []
    taken = {} if taken is None else taken
    for model in models:
        if type(model) is not dict:
            raise ValueError(f"Invalid mech pack registry entry: {root}")
        if model.get("backend") != "native" or model.get("status") not in _RUNTIME_MODEL_STATUSES:
            continue
        chassis = model.get("id")
        files = model.get("environment")
        if type(chassis) is not str or re.fullmatch(r"[a-z0-9]+", chassis) is None or type(files) is not dict:
            raise ValueError(f"Invalid mech pack registry entry: {root}")
        if chassis in taken:
            overridden.append({"chassis": chassis, "kept_from": taken[chassis]})
            continue
        supplied = False
        for level, infix in ((0, ""), (1, "LOD1_")):
            prefix = f"MW34_{chassis.upper()}_{infix}"
            material_key = prefix + "SURFACE_MATERIALS"
            # Same rule as prepared_mech_packs.py: the Bushwacker close mesh keeps its historical
            # MW34_BUSHWACKER_TEST name.
            mesh_name = "TEST" if chassis == "bushwacker" and level == 0 else "MESH"
            mesh, textures = files.get(prefix + mesh_name), files.get(prefix + "TEXTURES")
            material_member = files.get(material_key)
            if mesh is None or textures is None:
                if isinstance(material_member, str) and material_member:
                    skipped_materials.append({
                        "chassis": chassis,
                        "lod": str(level),
                        "reason": "surface-material sidecar requires its matching mesh and textures",
                    })
                continue
            arguments += ["--cc-model", chassis, str(level), _pack_member(root, mesh),
                          _pack_member(root, textures)]
            for index, letter in enumerate("BCDEFGH", 1):
                skin_member = files.get(prefix + f"SKIN_{letter}_TEXTURES")
                if skin_member is None:
                    continue
                try:
                    skin_path = _pack_member(root, skin_member)
                    arguments += ["--cc-model-skin", chassis, str(level), str(index), skin_path]
                except (OSError, ValueError) as error:
                    skipped_materials.append({
                        "chassis": chassis, "lod": str(level), "skin": index,
                        "reason": f"skin texture is missing or invalid; primary fallback: {error}",
                    })
            normals = files.get(prefix + "NORMALS")
            if normals is not None:
                arguments += ["--cc-model-normals", chassis, str(level), _pack_member(root, normals)]
            if isinstance(material_member, str) and material_member:
                try:
                    material_path = _pack_member(root, material_member)
                    if Path(material_path).stat().st_size > MAX_SIDECAR_BYTES:
                        raise ValueError("BWSFM1 sidecar exceeds its size limit")
                    mesh_path = _pack_member(root, mesh)
                    texture_path = _pack_member(root, textures)
                    asset_lod = "close" if level == 0 else "distance"
                    read_surface_materials_file(
                        material_path,
                        expected_asset_id=f"{chassis}:{asset_lod}",
                        expected_mesh_uv_hash=_mesh_uv_identity_file(Path(mesh_path)),
                        expected_batch_materials=_texture_batch_materials_file(
                            Path(texture_path)),
                    )
                    arguments += ["--cc-model-materials", chassis, str(level), material_path]
                except (OSError, ValueError, OverflowError, struct.error, TypeError) as error:
                    skipped_materials.append({
                        "chassis": chassis,
                        "lod": str(level),
                        "reason": f"surface-material sidecar is missing or invalid: {error}",
                    })
            supplied = True
        if supplied:
            taken[chassis] = root
    return arguments, overridden, skipped_materials


def _skin_pack_arguments(roots, argv, write_directory, skipped):
    """Reuse the installed skin contract against the winning native mesh identities."""
    if not roots:
        return []
    from prepared_skin_packs import select, write_catalog, CATALOG_KEY
    models = {}
    for position, argument in enumerate(argv):
        if argument != "--cc-model":
            continue
        chassis, lod, mesh = argv[position + 1:position + 4]
        model = models.setdefault(chassis, {"id": chassis, "visuals": {}})
        model["visuals"]["close" if lod == "0" else "distance"] = {"mesh": mesh}
    skins = []
    ids = set()
    # This planner targets the native BWSKIN1 consumer introduced with this route;
    # the content pack cannot grant itself a host capability.
    host = {"content_capabilities": {"additional-mech-skins": [1]}}
    for directory in roots:
        try:
            root = Path(_windows_path(directory, directory=True))
            manifest = _read_pack_json(root / "pack.json")
            candidates = [{**model, "additional_skins": []} for model in models.values()]
            selected = select([(root, manifest)], host, candidates)
            if ids.intersection(skin["id"] for skin in selected):
                raise ValueError("Duplicate enabled additional skin identity")
            if len(skins) + len(selected) > 128:
                raise ValueError("Too many enabled additional skins")
            ids.update(skin["id"] for skin in selected)
            skins.extend(selected)
        except (OSError, ValueError, KeyError, TypeError) as error:
            skipped.append({"root": directory, "feature": "additional_skins", "reason": str(error)})
    if not skins:
        return []
    try:
        catalog = write_catalog([{"additional_skins": skins}], Path(write_directory) / "prepared-skins")
    except OSError as error:
        skipped.append({"root": str(write_directory), "feature": "additional_skins", "reason": str(error)})
        return []
    return ["--cc-skin-catalog", catalog[CATALOG_KEY]]


def _compact_skin_arguments(argv, write_directory, skipped):
    """Move stock path metadata off the Windows command line without reading pixels."""
    compact = []
    records = []
    position = 0
    while position < len(argv):
        if argv[position] != "--cc-model-skin":
            compact.append(argv[position])
            position += 1
            continue
        chassis, lod, index, path = argv[position + 1:position + 5]
        records.append((chassis, int(lod), int(index), path))
        position += 5
    if not records:
        return compact
    if len(records) > 512:
        raise ValueError("Too many native stock skin bindings")
    blob = bytearray(b"BWSKIDX1" + struct.pack("<I", len(records)))
    for chassis, lod, index, path in records:
        chassis_bytes, path_bytes = chassis.encode("utf-8"), path.encode("utf-8")
        if not 1 <= len(chassis_bytes) <= 32 or not 1 <= len(path_bytes) <= 4096:
            raise ValueError("Invalid native stock skin binding string size")
        blob += struct.pack("<I", len(chassis_bytes)) + chassis_bytes
        blob += struct.pack("<III", lod, index, len(path_bytes)) + path_bytes
    from native_assets import write_atomic
    output = Path(write_directory) / "prepared-skins" / "stock-skins.bin"
    try:
        write_atomic(output, blob)
    except OSError as error:
        skipped.append({"root": str(write_directory), "feature": "skin_textures", "reason": str(error)})
        return compact
    # write_directory is already a validated absolute path; resolving it would expand
    # 8.3 short names and make the argument differ from the request's own spelling.
    return compact + ["--cc-skin-bindings", str(output)]


def _environment_pack_skip_reason(root):
    """Return why a prepared-environment-v1 map pack must be left out, or None to load it."""
    manifest, _ = _pack_payload(root, "prepared-environment-v1")
    files = manifest.get("files")
    if type(files) is not dict:
        raise ValueError(f"Map pack has no file table: {root}")
    for name, entry in files.items():
        size = entry.get("bytes") if type(entry) is dict else None
        if type(size) is not int or size < 0:
            raise ValueError(f"Map pack file table is invalid: {root}")
        if size > _NATIVE_FILE_LIMIT:
            return f"{name} is {size} bytes; native texture offsets support files up to 4 GiB"
    return None


def _effect_catalog(root):
    """Resolve and validate the prepared environment pack's optional MWFX1 catalog."""
    manifest, payload = _pack_payload(root, "prepared-environment-v1")
    if payload.get("registry") != "environment/environment.json":
        return None, "environment pack has no supported lighting registry"
    registry_path = _pack_member(root, payload["registry"])
    registry = _read_pack_json(registry_path)
    member = registry.get("effects") if type(registry) is dict else None
    files = manifest.get("files")
    if type(member) is not str or type(files) is not dict or member not in files:
        return None, "environment pack has no declared effect-light catalog"
    try:
        path = _pack_member(root, member)
        size = Path(path).stat().st_size
        if size < 12 or size > 12 + 48 * 8192:
            return None, "effect-light catalog has an invalid size"
        with open(path, "rb") as stream:
            header = stream.read(12)
    except (OSError, ValueError) as error:
        return None, f"effect-light catalog is unavailable: {error}"
    if len(header) != 12 or header[:8] != b"MWFX1\0\0\0":
        return None, "effect-light catalog has an invalid MWFX1 header"
    count = int.from_bytes(header[8:12], "little")
    if not 0 < count <= 8192 or size != 12 + 48 * count:
        return None, "effect-light catalog has an invalid entry count or size"
    return path, None


def _detail_catalog_problem(root, role):
    """Return why a prepared environment pack has no usable detail map for one role."""
    try:
        manifest, payload = _pack_payload(root, "prepared-environment-v1")
        if payload.get("registry") != "environment/environment.json":
            return "environment pack has no supported detail registry"
        registry = _read_pack_json(_pack_member(root, payload["registry"]))
        detail = registry.get("detail") if type(registry) is dict else None
        if type(detail) is not dict or role not in detail:
            return f"environment pack does not provide the {role} detail map"
        member = detail[role]
        files = manifest.get("files")
        entry = files.get(member) if type(member) is str and type(files) is dict else None
        if type(entry) is not dict or entry.get("format") != "BWSNR2":
            return f"{role} detail map is not declared as BWSNR2"
        path = _pack_member(root, member)
        size = Path(path).stat().st_size
        if type(entry.get("bytes")) is not int or size != entry["bytes"] or size < 12 or size > 16 * 1024 * 1024:
            return f"{role} detail map has an invalid size"
        with open(path, "rb") as stream:
            header = stream.read(12)
        if len(header) != 12 or header[:8] != b"BWSNR2\0\0":
            return f"{role} detail map has an invalid BWSNR2 header"
        count = int.from_bytes(header[8:12], "little")
        if not 0 < count <= 256:
            return f"{role} detail map has an invalid surface count"
        return None
    except (OSError, ValueError, KeyError, TypeError) as error:
        return f"{role} detail map is unavailable: {error}"


def _stock_effect_catalog(path):
    if not path or not Path(path).is_file():
        return None
    path = Path(path)
    size = path.stat().st_size
    if size < 12 or size > 12 + 48 * 8192:
        return None
    with path.open("rb") as stream:
        header = stream.read(12)
    if header[:8] != b"MWFX1\0\0\0":
        return None
    count = int.from_bytes(header[8:12], "little")
    return str(path) if 0 < count <= 8192 and size == 12 + 48 * count else None


def _stock_headlight_catalog_available(path):
    if not path.is_file() or path.stat().st_size < 12:
        return False
    with path.open("rb") as stream:
        header = stream.read(12)
    count = int.from_bytes(header[8:12], "little")
    return header[:8] == b"MWHDLT1\0" and 0 < count <= 18


def _preview_choices(preview):
    """Validate the schema-4 preview object and return its choices with defaults."""
    if type(preview) is not dict or not set(preview).issubset(_PREVIEW_FIELDS):
        raise ValueError("Invalid native preview fields")
    choices = {
        "draw_distance": 800,
        "fog_distance": None,
        "hud": None,
        "hud_text": None,
        "geometry": None,
        "model_packs": [],
        "environment_packs": [],
        "ui_packs": [],
        "skin_packs": [],
        "dynamic_lighting": False,
        "shadows": False,
        "headlights": False,
        "water_detail": False,
        "cloud_detail": False,
        "headlight_bindings": None,
        "stock_effect_catalog": None,
        "stock_headlight_catalog": None,
    }
    choices.update(preview)
    distance = choices["draw_distance"]
    if type(distance) is not int or distance not in _PREVIEW_DRAW_DISTANCES:
        raise ValueError("Native preview scenery distance must be 800, 1200, 1600, 2400 or 3200")
    fog = choices["fog_distance"]
    if fog is not None and (type(fog) is not int or not 0 <= fog <= 3200):
        raise ValueError("Native fog distance must be between 0 and 3200")
    if choices["hud"] is not None and choices["hud"] not in _PREVIEW_HUDS:
        raise ValueError("Unknown native preview HUD")
    if choices["hud_text"] is not None:
        if type(choices["hud_text"]) is not bool:
            raise ValueError("Native preview HUD text selection must be Boolean")
        if choices["hud"] != "core-critical":
            raise ValueError("Native preview HUD text needs the core-critical HUD")
    if choices["geometry"] is not None and choices["geometry"] not in _PREVIEW_GEOMETRY:
        raise ValueError("Unknown native preview geometry mode")
    for field in ("model_packs", "environment_packs", "ui_packs", "skin_packs"):
        packs = choices[field]
        if type(packs) is not list or len(packs) > _MAX_PREVIEW_PACKS:
            raise ValueError(f"Invalid native preview {field}")
    for field in ("dynamic_lighting", "shadows", "headlights", "water_detail", "cloud_detail"):
        if type(choices[field]) is not bool:
            raise ValueError(f"Native preview {field} selection must be Boolean")
    if choices["headlights"] and not choices["dynamic_lighting"]:
        raise ValueError("Native headlights require dynamic lighting")
    for field in ("headlight_bindings", "stock_effect_catalog", "stock_headlight_catalog"):
        if choices[field] is not None:
            _windows_path(choices[field], directory=False)
    return choices


def _window_arguments(window_mode, width, height):
    """Return argv tokens for window presentation.

    The native runtime defaults to borderless desktop fullscreen; --window or --windowed makes
    it a window. Both fullscreen and borderless therefore emit no window tokens.
    """
    if window_mode == "windowed":
        return ["--window", f"{width}x{height}", "--windowed"]
    return []


def plan_launch(request):
    """Return complete argv or explicit unsupported reasons; never probe or start anything."""
    if type(request) is not dict:
        raise ValueError("Missing or unknown native request fields")
    disk_cache = request.get("disk_cache", True)
    if type(disk_cache) is not bool:
        raise ValueError("disk_cache must be a boolean")
    vsync = request.get("vsync", False)
    if type(vsync) is not bool:
        raise ValueError("vsync must be a boolean")
    supports_vsync = request.get("supports_vsync", False)
    if type(supports_vsync) is not bool:
        raise ValueError("supports_vsync must be a boolean")
    schema = request.get("schema_version")
    if type(schema) is not int or schema not in (2, 3, 4):
        raise ValueError("Unsupported native request schema")
    allowed = {2: _FIELDS | _OPTIONAL_FIELDS,
               3: _FIELDS | _OPTIONAL_FIELDS | {"visuals"},
               4: _FIELDS | _OPTIONAL_FIELDS | {"visuals", "preview"}}[schema]
    if not _FIELDS.issubset(request) or not set(request).issubset(allowed):
        raise ValueError("Missing or unknown native request fields")
    pom = False
    pom_quality = None
    if schema >= 3 and "visuals" in request:
        visuals = request["visuals"]
        if type(visuals) is not dict or not set(visuals).issubset({"pom", "pom_quality"}):
            raise ValueError("Invalid native visuals fields")
        if "pom" in visuals:
            if type(visuals["pom"]) is not bool:
                raise ValueError("Native POM selection must be Boolean")
            pom = visuals["pom"]
        if "pom_quality" in visuals:
            quality = visuals["pom_quality"]
            if type(quality) is not str or quality not in ("off", "low", "high"):
                raise ValueError("Native POM quality must be off, low, or high")
            if (quality == "off" and pom) or (
                quality != "off" and "pom" in visuals and not pom
            ):
                raise ValueError("Conflicting native POM selection")
            if quality != "off":
                pom = True
                pom_quality = quality
    if pom and request["lighting"] != "normal":
        raise ValueError("Native POM requires normal lighting")
    preview = _preview_choices(request.get("preview", {})) if schema == 4 else None
    disabled_detail = []
    if preview is not None and request["lighting"] != "normal":
        for choice in ("water_detail", "cloud_detail"):
            if preview[choice]:
                preview[choice] = False
                disabled_detail.append(choice)
    if request["engine"] != "mw3-re" or request["renderer"] != "vulkan-wsi":
        raise ValueError("Unsupported native engine or renderer")
    flare_style = request.get("flare_style", "modern")
    if flare_style not in ("modern", "original"):
        raise ValueError("Native flare style must be modern or original")
    for field, minimum, maximum in (("width", 640, 7680), ("height", 480, 4320)):
        if type(request[field]) is not int or not minimum <= request[field] <= maximum:
            raise ValueError("Unsupported native window dimensions")
    if type(request["af"]) is not int or request["af"] not in (1, 2, 4, 8, 16):
        raise ValueError("Unsupported native anisotropic filtering")
    if type(request["render_thread"]) is not bool:
        raise ValueError("Native render-thread selection must be Boolean")
    if type(request["aa"]) is not str or request["aa"] not in (*_AA, "8"):
        raise ValueError("Unknown native antialiasing selection")
    if request["window_mode"] not in ("windowed", "fullscreen", "borderless"):
        raise ValueError("Unknown native window mode")
    if request["lighting"] not in ("off", "flat", "normal"):
        raise ValueError("Unknown native lighting selection")
    if type(request["assets"]) is not list or len(request["assets"]) > 128:
        raise ValueError("Invalid native asset list")
    runtime = _windows_path(request["runtime_root"])
    executable = _windows_path(request["executable"], directory=False)
    game = _windows_path(request["game_dir"])
    write = _windows_path(request["write_dir"])
    codec_value = request.get("indeo_codec")
    codec = _windows_path(codec_value, directory=False) if codec_value is not None else None
    for asset in request["assets"]:
        _windows_path(asset)
    if executable == runtime or not executable.is_relative_to(runtime):
        raise ValueError("Native executable leaves the runtime root")
    if preview is not None:
        for field in ("stock_effect_catalog", "stock_headlight_catalog"):
            resource = preview[field]
            if (resource is not None and
                    not _windows_path(resource, directory=False).is_relative_to(runtime)):
                raise ValueError(f"Native preview {field} leaves the runtime root")
    for protected in (runtime, game):
        if write.is_relative_to(protected) or protected.is_relative_to(write):
            raise ValueError("Native write root overlaps a read-only input root")
    if preview is not None:
        for pack in preview["model_packs"] + preview["environment_packs"]:
            root = Path(str(_windows_path(pack)))
            if write.is_relative_to(root) or root.is_relative_to(write):
                raise ValueError("Native write root overlaps a preview pack")
    reasons = []
    if request["aa"] == "8":
        reasons.append("Saved 8-sample antialiasing has no qualified native mapping")
    if reasons:
        return {"ok": False, "reasons": reasons}
    argv = [
        request["executable"], "--install", request["game_dir"], "--write-dir", request["write_dir"],
        "--cc-vulkan-wsi",
        *_window_arguments(request["window_mode"], request["width"], request["height"]),
        "--cc-aa", _AA[request["aa"]], "--cc-af", str(request["af"]),
        "--cc-render-thread", "1" if request["render_thread"] else "0", "--cc-lighting", request["lighting"],
        "--cc-flare-style", flare_style,
    ]
    skipped_features = []
    if supports_vsync:
        argv.extend(("--cc-vsync", "1" if vsync else "0"))
    elif not vsync:
        # Older runtimes always present with vsync, so only a request to turn it off goes unmet.
        skipped_features.append({
            "feature": "vsync",
            "reason": "The selected MW3-RE runtime does not advertise support for VSync.",
        })
    if codec is None:
        skipped_features.append({
            "feature": "Indeo movies",
            "reason": "No original Ir50_32.dll passed the launcher's identity check; movie playback will use the existing imported-file fallback.",
        })
    else:
        argv.extend(("--indeo-codec", str(codec)))
    detail_flag_indices = {}
    if preview is not None:
        argv.extend(("--cc-dynamic-lighting", "1" if preview["dynamic_lighting"] else "0"))
        # Apply dependencies here so callers can preserve requested choices for suppression reports.
        sun_shadows = (preview["shadows"] and preview["dynamic_lighting"] and
                       request["lighting"] != "off")
        argv.extend(("--cc-sun-shadows", "1" if sun_shadows else "0"))
        detail_flag_indices["water_detail"] = len(argv) + 1
        argv.extend(("--cc-water-detail", "1" if preview["water_detail"] else "0"))
        detail_flag_indices["cloud_detail"] = len(argv) + 1
        argv.extend(("--cc-cloud-detail", "1" if preview["cloud_detail"] else "0"))
    if pom:
        argv.extend(("--cc-pom", pom_quality if pom_quality is not None else "1"))
    skipped = []
    for choice in disabled_detail:
        skipped.append({
            "root": str(runtime),
            "feature": choice,
            "reason": f"{choice.replace('_', ' ')} requires normal lighting",
        })
    overridden_models = []
    if preview is not None:
        # Schema 4 is the launcher's explicit selection boundary, even when no
        # environment packs are enabled. Prevent stale diagnostic catalogs from
        # silently supplying normal maps outside that selection.
        argv.append("--cc-environment-packs-explicit")
        if preview["shadows"] and request["lighting"] == "off":
            skipped.append({"root": str(runtime), "feature": "sun_shadows",
                            "reason": "sun shadows require sun lighting"})
        elif preview["shadows"] and not preview["dynamic_lighting"]:
            skipped.append({"root": str(runtime), "feature": "sun_shadows",
                            "reason": "sun shadows require dynamic lighting"})
        # 800 is the original range, so it adds no argument and older runtimes stay compatible.
        if preview["draw_distance"] != 800:
            argv.extend(("--cc-draw-distance", str(preview["draw_distance"])))
        if preview["fog_distance"] is not None:
            argv.extend(("--cc-fog-distance", str(preview["fog_distance"])))
        if preview["hud"] is not None:
            argv.extend(("--cc-hud", preview["hud"]))
        if preview["hud_text"] is not None:
            argv.extend(("--cc-hud-text", "1" if preview["hud_text"] else "0"))
        ui_seen = set()
        ui_identities = {}
        for pack in preview["ui_packs"]:
            try:
                root = Path(str(_windows_path(pack)))
                if write.is_relative_to(root) or root.is_relative_to(write):
                    skipped.append({"root": str(root), "feature": "ui_artwork",
                                    "reason": "Native write root overlaps the UI pack"})
                    continue
                reason = _ui_pack_skip_reason(root)
            except (OSError, ValueError, json.JSONDecodeError) as error:
                root = Path(str(pack))
                reason = f"UI pack is unreadable: {error}"
            if reason is not None:
                skipped.append({"root": str(root), "feature": "ui_artwork", "reason": reason})
                continue
            if preview["hud"] != "core-critical":
                skipped.append({"root": str(root), "feature": "ui_artwork",
                                "reason": "UI artwork requires the core-critical HUD"})
                continue
            try:
                manifest, payload = _pack_payload(root, "prepared-ui-v1")
                registry_name = payload.get("registry")
                registry_path = _verified_ui_member(root, manifest, registry_name)
                registry = _read_pack_json(registry_path)
                kind = registry["kind"]
                if kind not in ("hud", "menu"):
                    raise ValueError("unknown UI pack kind")
                if registry.get("payload_profile") != "prepared-ui-v1" or registry.get("schema_version") != 2:
                    raise ValueError("unsupported UI registry")
                sprites = registry.get("sprites")
                if type(sprites) is not dict or len(sprites) > 256:
                    raise ValueError("invalid UI sprite table")
                sprite_hashes = {}
                for identity, relative in sprites.items():
                    if (type(identity) is not str or re.fullmatch(r"[0-9a-f]{16}", identity) is None
                            or relative != f"ui/sprites/{identity}.rgba"):
                        raise ValueError("invalid UI sprite identity or path")
                    sprite_path = _verified_ui_member(root, manifest, relative, "MW3H-v1")
                    sprite_hashes[identity] = manifest["files"][relative]["sha256"].lower()
                    with sprite_path.open("rb") as stream:
                        header = stream.read(28)
                    if len(header) != 28 or header[:4] != b"MW3H":
                        raise ValueError("UI sprite header is missing or invalid")
                    width, height, u0, v0, u1, v1 = struct.unpack("<IIffff", header[4:])
                    if (not width or not height or width > 8192 or height > 8192
                            or sprite_path.stat().st_size != 28 + 4 * width * height
                            or not all(math.isfinite(value) for value in (u0, v0, u1, v1))
                            or u0 < 0 or v0 < 0 or u1 > 1 or v1 > 1 or u0 >= u1 or v0 >= v1):
                        raise ValueError("UI sprite dimensions, length or UV coordinates are invalid")
                # The runtime enumerates this directory, not the registry. Match its
                # exact extension check so every loaded sprite has passed validation.
                sprite_dir = root / "ui" / "sprites"
                runtime_sprites = set()
                if sprite_dir.is_dir():
                    runtime_sprites = {f"ui/sprites/{path.name}" for path in sprite_dir.iterdir()
                                       if path.suffix == ".rgba"}
                if runtime_sprites != set(sprites.values()):
                    raise ValueError("UI sprite directory does not match the registry")
                if kind in ui_seen:
                    skipped.append({"root": str(root), "feature": "ui_artwork",
                                    "reason": f"A {kind} UI pack was already selected"})
                    continue
                conflict = next((identity for identity, digest in sprite_hashes.items()
                                 if identity in ui_identities and ui_identities[identity][0] != digest), None)
                if conflict is not None:
                    skipped.append({"root": str(root), "feature": "ui_artwork",
                                    "reason": f"UI identity {conflict} conflicts with earlier pack "
                                              f"{ui_identities[conflict][1]}"})
                    continue
                background = registry.get("background")
                if background is not None:
                    if kind != "menu" or background != "ui/background.mwhd":
                        raise ValueError("unsupported menu background binding")
                    background_path = _verified_ui_member(root, manifest, background, "MWHDBG1")
                    with background_path.open("rb") as stream:
                        header = stream.read(24)
                    if len(header) != 24 or header[:8] != b"MWHDBG1\0":
                        raise ValueError("menu background header is missing or invalid")
                    width, height, source_width, source_height = struct.unpack("<IIII", header[8:])
                    if (not width or not height or not source_width or not source_height
                            or max(width, height, source_width, source_height) > 16384
                            or width * source_height != height * source_width
                            or background_path.stat().st_size != 24 + 3 * width * height):
                        raise ValueError("menu background dimensions or length are invalid")
                    argv.extend(("--cc-menu-background", str(background_path)))
                if not sprite_hashes:
                    if background is None:
                        raise ValueError("UI pack has no available artwork")
                else:
                    argv.extend(("--cc-hud-artwork", str(root)))
                    for identity, digest in sprite_hashes.items():
                        ui_identities.setdefault(identity, (digest, str(root)))
                ui_seen.add(kind)
            except (OSError, AttributeError, KeyError, TypeError, json.JSONDecodeError, ValueError) as error:
                skipped.append({"root": str(root), "feature": "ui_artwork",
                                "reason": f"UI pack metadata is missing or invalid: {error}"})
        if preview["geometry"] is not None:
            argv.extend(("--cc-geometry", preview["geometry"]))
        supplied_chassis = {}
        for pack in preview["model_packs"]:
            arguments, overridden, skipped_materials = _model_pack_arguments(
                pack, supplied_chassis)
            argv.extend(arguments)
            overridden_models.extend({"root": pack, **item} for item in overridden)
            skipped.extend({"root": pack, "feature": "skin_textures" if "skin" in item else "surface_materials", **item}
                           for item in skipped_materials)
        argv = _compact_skin_arguments(argv, write, skipped)
        argv.extend(_skin_pack_arguments(preview["skin_packs"], argv, write, skipped))
        effect_catalog = None
        effect_catalog_problem = None
        detail_catalogs = {"water": None, "surf": None, "cloud": None}
        detail_problems = {role: [] for role in detail_catalogs}
        for pack in preview["environment_packs"]:
            reason = _environment_pack_skip_reason(pack)
            if reason is None:
                argv.extend(("--cc-environment-pack", pack))
                if preview["dynamic_lighting"] and effect_catalog is None:
                    effect_catalog, effect_reason = _effect_catalog(pack)
                    if effect_reason and effect_catalog_problem is None:
                        effect_catalog_problem = {"root": pack, "feature": "effect_lights",
                                                  "reason": effect_reason}
                for role in detail_catalogs:
                    problem = _detail_catalog_problem(pack, role)
                    if problem is None:
                        detail_catalogs[role] = pack
                    else:
                        detail_problems[role].append((pack, problem))
            else:
                skipped.append({"root": pack, "reason": reason})
        for choice, roles, label in (("water_detail", ("water", "surf"), "water_detail"),
                                     ("cloud_detail", ("cloud",), "cloud_detail")):
            if preview[choice] and not all(detail_catalogs[role] for role in roles):
                missing_role = next(role for role in roles if not detail_catalogs[role])
                if detail_problems[missing_role]:
                    root, reason = detail_problems[missing_role][0]
                else:
                    root, reason = str(runtime), f"no enabled environment pack provides the {missing_role} detail map"
                skipped.append({"root": root, "feature": label, "reason": reason})
                argv[detail_flag_indices[choice]] = "0"
        if preview["dynamic_lighting"]:
            if effect_catalog is None:
                effect_catalog = _stock_effect_catalog(preview["stock_effect_catalog"])
            if effect_catalog is not None:
                argv.extend(("--cc-effect-lights", effect_catalog, "--cc-fixture-lights", "1"))
            else:
                skipped.append(effect_catalog_problem or {
                    "root": str(runtime), "feature": "effect_lights",
                    "reason": "no valid effect-light catalog is installed"})
                skipped.append({"root": str(runtime), "feature": "fixture_lights",
                                "reason": "fixture lights require an enabled effect-light catalog"})
            if preview["headlights"]:
                stock_headlight_path = preview["stock_headlight_catalog"]
                stock_headlights = Path(stock_headlight_path) if stock_headlight_path else None
                binding_path = preview["headlight_bindings"]
                if effect_catalog is None:
                    skipped.append({"root": str(runtime), "feature": "mech_headlights",
                                    "reason": "headlights require an enabled effect-light catalog"})
                elif (stock_headlights is None or
                      not _stock_headlight_catalog_available(stock_headlights)):
                    skipped.append({
                        "root": stock_headlight_path or str(runtime),
                        "feature": "mech_headlights",
                        "reason": "stock headlight catalog is missing or invalid",
                    })
                elif not binding_path or not Path(binding_path).is_file():
                    skipped.append({
                        "root": binding_path or str(runtime),
                        "feature": "mech_headlights",
                        "reason": "headlight toggle binding is missing",
                    })
                else:
                    argv.extend(("--cc-mech-headlights", str(stock_headlights), binding_path))
    for asset in request["assets"]:
        argv.extend(("--assets", asset))
    result = {"ok": True, "argv": argv, "working_directory": str(executable.parent),
              "skipped_features": skipped_features,
              "environment": {"MW3_DISK_CACHE": "1" if disk_cache else "0"}}
    if preview is not None:
        result["skipped_packs"] = skipped
        result["overridden_models"] = overridden_models
    return result


def _ui_pack_skip_reason(root):
    """Return a bounded failure reason for an unavailable prepared UI pack."""
    manifest_path = root / "pack.json"
    try:
        if not root.is_dir() or not manifest_path.is_file():
            return "UI pack directory or pack.json is missing"
        _, payload = _pack_payload(root, "prepared-ui-v1")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return f"UI pack manifest is invalid: {error}"
    registry = payload.get("registry")
    if registry != "ui/ui.json" or not (root / registry).is_file():
        return "UI pack registry is missing or unsupported"
    return None


def _verified_ui_member(root, manifest, relative, expected_format=None):
    """Check a UI resource against the installed pack's declared size, format and digest."""
    path = Path(_pack_member(root, relative))
    files = manifest.get("files")
    metadata = files.get(relative) if type(files) is dict else None
    if (type(metadata) is not dict or type(metadata.get("bytes")) is not int
            or metadata["bytes"] != path.stat().st_size
            or re.fullmatch(r"[0-9a-fA-F]{64}", metadata.get("sha256", "")) is None
            or (expected_format is not None and metadata.get("format") != expected_format)):
        raise ValueError(f"UI resource declaration is missing or invalid: {relative}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest().lower() != metadata["sha256"].lower():
        raise ValueError(f"UI resource integrity failure: {relative}")
    return path
