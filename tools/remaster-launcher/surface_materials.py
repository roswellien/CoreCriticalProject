"""Pack and validate optional BWSFM1 surface-material sidecars for replacement mechs.

BWSFM1 carries explicit height, displacement, UV transform/addressing/atlas and
subsurface-scattering (SSS) parameters plus linear red-channel RGBA8 images.
Normal-map alpha is never modified or repurposed. Spatial amplitudes, displacement
bounds, radii and thickness scales are expressed in native host world units.
"""

from __future__ import annotations

import io
import math
from pathlib import Path
import re
import struct

from normal_materials import uncached_pixel_hash

MAGIC = b"BWSFM1\0\0"
VERSION = 1
CAPABILITY = "surface-materials"
FORMAT = "BWSFM1"

NO_SURFACE_MATERIAL = 0xFFFFFFFF
NO_SURFACE_IMAGE = 0xFFFFFFFF

ROLE_HEIGHT = 1
ROLE_THICKNESS = 2

ADDRESS_WRAP = 1
ADDRESS_MIRROR = 2
ADDRESS_CLAMP = 3

MAX_BATCHES = 4096
MAX_RECORDS = 4096
MAX_IMAGES = 512
MAX_IDENTIFIER_BYTES = 4096
MAX_MATERIAL_NAME_BYTES = 31
MAX_DIMENSION = 4096
MAX_SIDECAR_BYTES = 256 * 1024 * 1024
MAX_WORLD_AMPLITUDE = 16.0
MAX_UV_TRANSFORM = 1024.0

SAFE_IDENTIFIER = re.compile(r"[A-Za-z0-9_.:-]+\Z")
SAFE_MATERIAL_NAME = re.compile(r"[A-Za-z0-9_.-]{1,31}\Z")


def surface_material_environment(texture_environment: str) -> str:
    """Derive the paired MW34_*_SURFACE_MATERIALS name from a validated texture binding."""
    if not texture_environment.startswith("MW34_") or not texture_environment.endswith("_TEXTURES"):
        raise ValueError("Surface materials require a MW34_*_TEXTURES binding")
    return texture_environment[:-9] + "_SURFACE_MATERIALS"


def _validate_identifier(value: object, label: str, max_bytes: int = MAX_IDENTIFIER_BYTES) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Invalid {label}")
    encoded = value.encode("utf-8")
    if (
        len(encoded) > max_bytes
        or "\0" in value
        or ".." in value
        or "/" in value
        or "\\" in value
        or not SAFE_IDENTIFIER.fullmatch(value)
    ):
        raise ValueError(f"Invalid {label}: {value!r}")
    return encoded


def _validate_material_name(value: object) -> bytes:
    if not isinstance(value, str) or ".." in value or not SAFE_MATERIAL_NAME.fullmatch(value):
        raise ValueError(f"Invalid surface material name: {value!r}")
    return value.encode("ascii")


def _f32(value: object, label: str, low: float, high: float) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError(f"Nonfinite {label}")
    rounded = struct.unpack("<f", struct.pack("<f", float(value)))[0]
    if not math.isfinite(rounded) or not low <= rounded <= high:
        raise ValueError(f"Out-of-range {label}: {value}")
    return rounded


def mesh_uv_identity(mesh_bytes: bytes) -> int:
    """Compute the 64-bit FNV-1a geometry/UV compatibility hash over a BWMESH payload.

    Hashes the batch count and every batch's vertex count and 32-byte
    (x, y, z, nx, ny, nz, u, v) vertex stream so any geometry or UV layout change
    invalidates bindings built for another mesh.
    """
    if not isinstance(mesh_bytes, (bytes, bytearray)) or len(mesh_bytes) < 12:
        raise ValueError("Invalid mesh payload for UV identity")
    return _mesh_uv_identity(io.BytesIO(mesh_bytes))


def mesh_uv_identity_file(path: Path) -> int:
    """Compute a mesh/UV identity without loading the complete payload."""
    with Path(path).open("rb") as stream:
        return _mesh_uv_identity(stream)


def _mesh_uv_identity(stream) -> int:

    def take(size: int) -> bytes:
        chunk = stream.read(size)
        if len(chunk) != size:
            raise ValueError("Truncated mesh payload for UV identity")
        return chunk

    magic = take(8)
    donor = magic == b"BWMESH4\0"
    anchored = magic == b"BWMESH6\0"
    layered = anchored or magic == b"BWMESH5\0"
    placement = layered or magic == b"BWMESH3\0"
    visibility = donor or placement or magic == b"BWMESH2\0"
    if not visibility and magic != b"BWMESH1\0":
        raise ValueError("Unsupported mesh payload format for UV identity")
    count = struct.unpack("<I", take(4))[0]
    if not 1 <= count <= 256:
        raise ValueError("Invalid mesh batch count for UV identity")
    if donor:
        bones, refs, flags = struct.unpack("<III", take(12))
        if not 1 <= bones <= 256 or not 1 <= refs <= 128 or flags > 2:
            raise ValueError("Invalid donor rig header in mesh payload")
        take(40)  # 5 float64 gait parameters
        for _ in range(bones):
            take(32 + 32 + 4 + 128)
        for _ in range(refs):
            take(32 + 128)

    hash_value = 0xCBF29CE484222325
    for byte in struct.pack("<I", count):
        hash_value = ((hash_value ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF

    for _ in range(count):
        take(32)  # owner name
        if visibility:
            take(32)
        if placement:
            take(32 + 12)
        if layered:
            take(32 + 12)
        if anchored:
            take(32 + 12)
        donor_bone = 0
        if donor:
            donor_bone = struct.unpack("<I", take(4))[0]
        vertex_count, _color = struct.unpack("<II", take(8))
        if not 1 <= vertex_count <= 65535 or vertex_count % 3 != 0:
            raise ValueError("Invalid mesh vertex count for UV identity")
        vertices = take(vertex_count * 32)
        if donor and donor_bone == 0xFFFFFFFF:
            take(vertex_count * 4)
        for byte in struct.pack("<I", vertex_count):
            hash_value = ((hash_value ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
        for byte in vertices:
            hash_value = ((hash_value ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF

    if stream.read(1):
        raise ValueError("Trailing mesh payload data")
    return hash_value


def texture_batch_materials(texture_bytes: bytes) -> list[str]:
    """Extract the ordered per-batch material names from a validated BWTEX1 payload."""
    if not isinstance(texture_bytes, (bytes, bytearray)) or len(texture_bytes) < 16:
        raise ValueError("Invalid BWTEX1 payload")
    return _texture_batch_materials(io.BytesIO(texture_bytes))


def texture_batch_materials_file(path: Path) -> list[str]:
    """Extract material names without loading the complete texture payload."""
    with Path(path).open("rb") as stream:
        return _texture_batch_materials(stream)


def _texture_batch_materials(stream) -> list[str]:

    def take(size: int) -> bytes:
        chunk = stream.read(size)
        if len(chunk) != size:
            raise ValueError("Truncated BWTEX1 payload")
        return chunk

    if take(8) != b"BWTEX1\0\0":
        raise ValueError("Expected BWTEX1 payload")
    batches, count = struct.unpack("<II", take(8))
    if not 1 <= batches <= MAX_BATCHES or not 1 <= count <= 64:
        raise ValueError("Invalid BWTEX1 batch/material counts")
    bindings = list(struct.unpack("<" + "I" * batches, take(batches * 4)))
    if any(index >= count for index in bindings):
        raise ValueError("Invalid BWTEX1 material binding index")
    names = []
    for _ in range(count):
        raw_name = take(32)
        if not raw_name[0] or raw_name[31]:
            raise ValueError("Invalid BWTEX1 material name")
        name = raw_name.split(b"\0", 1)[0].decode("ascii")
        if ".." in name or not SAFE_MATERIAL_NAME.fullmatch(name):
            raise ValueError("Unsafe BWTEX1 material name")
        width, height, _hash = struct.unpack("<IIQ", take(16))
        if not 1 <= width <= MAX_DIMENSION or not 1 <= height <= MAX_DIMENSION:
            raise ValueError("Invalid BWTEX1 dimensions")
        remaining = width * height * 2
        while remaining:
            chunk = take(min(remaining, 1024 * 1024))
            remaining -= len(chunk)
        names.append(name)
    if stream.read(1):
        raise ValueError("Trailing BWTEX1 data")
    return [names[index] for index in bindings]


def normalize_record(record: dict, image_roles: dict[str, int]) -> dict:
    """Validate one authored surface-material record and fill neutral defaults."""
    if not isinstance(record, dict):
        raise ValueError("Surface material record must be a dict")
    allowed_keys = {
        "asset_id",
        "material_name",
        "height_image",
        "thickness_image",
        "height_reference",
        "height_amplitude",
        "max_displacement",
        "tessellation_cap",
        "uv_scale",
        "uv_offset",
        "address_mode_u",
        "address_mode_v",
        "atlas_rect",
        "sss_participation",
        "sss_tint",
        "sss_radius",
        "thickness_scale",
        "roughness",
        "reflectivity",
        "metallic",
    }
    if not {"asset_id", "material_name"} <= set(record) or set(record) - allowed_keys:
        raise ValueError("Invalid surface material record fields")

    _validate_identifier(record["asset_id"], "asset_id")
    _validate_material_name(record["material_name"])

    height_image = record.get("height_image")
    if height_image is not None:
        if not isinstance(height_image, str) or image_roles.get(height_image) != ROLE_HEIGHT:
            raise ValueError(f"Missing or non-height image reference: {height_image!r}")

    thickness_image = record.get("thickness_image")
    if thickness_image is not None:
        if not isinstance(thickness_image, str) or image_roles.get(thickness_image) != ROLE_THICKNESS:
            raise ValueError(f"Missing or non-thickness image reference: {thickness_image!r}")

    height_reference = _f32(record.get("height_reference", 0.0), "height_reference", 0.0, 1.0)
    height_amplitude = _f32(
        record.get("height_amplitude", 0.0),
        "height_amplitude",
        -MAX_WORLD_AMPLITUDE,
        MAX_WORLD_AMPLITUDE,
    )
    max_displacement = _f32(
        record.get("max_displacement", abs(height_amplitude)),
        "max_displacement",
        0.0,
        MAX_WORLD_AMPLITUDE,
    )
    if max_displacement < abs(height_amplitude):
        raise ValueError("max_displacement must be >= abs(height_amplitude)")
    if height_image is None and (height_amplitude != 0.0 or max_displacement != 0.0):
        raise ValueError("Non-zero height amplitude or displacement requires a height_image")

    tessellation_cap = record.get("tessellation_cap", 1)
    if type(tessellation_cap) is not int or not 1 <= tessellation_cap <= 8:
        raise ValueError("tessellation_cap must be an integer in 1..8")
    if height_image is None and tessellation_cap != 1:
        raise ValueError("tessellation_cap > 1 requires a height_image")

    raw_scale = record.get("uv_scale", (1.0, 1.0))
    if not isinstance(raw_scale, (list, tuple)) or len(raw_scale) != 2:
        raise ValueError("uv_scale requires 2 numbers")
    uv_scale = (
        _f32(raw_scale[0], "uv_scale[0]", -MAX_UV_TRANSFORM, MAX_UV_TRANSFORM),
        _f32(raw_scale[1], "uv_scale[1]", -MAX_UV_TRANSFORM, MAX_UV_TRANSFORM),
    )
    if uv_scale[0] == 0.0 or uv_scale[1] == 0.0:
        raise ValueError("uv_scale components must be non-zero")

    raw_offset = record.get("uv_offset", (0.0, 0.0))
    if not isinstance(raw_offset, (list, tuple)) or len(raw_offset) != 2:
        raise ValueError("uv_offset requires 2 numbers")
    uv_offset = (
        _f32(raw_offset[0], "uv_offset[0]", -MAX_UV_TRANSFORM, MAX_UV_TRANSFORM),
        _f32(raw_offset[1], "uv_offset[1]", -MAX_UV_TRANSFORM, MAX_UV_TRANSFORM),
    )

    address_u = record.get("address_mode_u", ADDRESS_WRAP)
    address_v = record.get("address_mode_v", ADDRESS_WRAP)
    if (
        type(address_u) is not int
        or type(address_v) is not int
        or address_u not in (ADDRESS_WRAP, ADDRESS_MIRROR, ADDRESS_CLAMP)
        or address_v not in (ADDRESS_WRAP, ADDRESS_MIRROR, ADDRESS_CLAMP)
    ):
        raise ValueError("address_mode_u/v must be 1 (wrap), 2 (mirror), or 3 (clamp)")

    raw_atlas = record.get("atlas_rect", (0.0, 0.0, 1.0, 1.0))
    if not isinstance(raw_atlas, (list, tuple)) or len(raw_atlas) != 4:
        raise ValueError("atlas_rect requires 4 numbers")
    atlas_rect = tuple(_f32(v, "atlas_rect", 0.0, 1.0) for v in raw_atlas)
    if not (atlas_rect[0] < atlas_rect[2] and atlas_rect[1] < atlas_rect[3]):
        raise ValueError("atlas_rect requires min_u < max_u and min_v < max_v")

    sss_participation = _f32(record.get("sss_participation", 0.0), "sss_participation", 0.0, 1.0)
    raw_tint = record.get("sss_tint", (0.0, 0.0, 0.0))
    if not isinstance(raw_tint, (list, tuple)) or len(raw_tint) != 3:
        raise ValueError("sss_tint requires 3 numbers")
    sss_tint = tuple(_f32(v, "sss_tint", 0.0, 1.0) for v in raw_tint)
    sss_radius = _f32(record.get("sss_radius", 0.0), "sss_radius", 0.0, MAX_WORLD_AMPLITUDE)
    thickness_scale = _f32(
        record.get("thickness_scale", 0.0), "thickness_scale", 0.0, MAX_WORLD_AMPLITUDE
    )
    if sss_participation == 0.0 and (
        sss_radius != 0.0 or thickness_scale != 0.0 or thickness_image is not None
    ):
        raise ValueError("Non-zero SSS radius, thickness scale, or thickness image requires sss_participation > 0")

    roughness = _f32(record.get("roughness", 0.7), "roughness", 0.0, 1.0)
    reflectivity = _f32(record.get("reflectivity", 0.04), "reflectivity", 0.0, 1.0)
    metallic = _f32(record.get("metallic", 0.0), "metallic", 0.0, 1.0)

    return {
        "asset_id": record["asset_id"],
        "material_name": record["material_name"],
        "height_image": height_image,
        "thickness_image": thickness_image,
        "height_reference": height_reference,
        "height_amplitude": height_amplitude,
        "max_displacement": max_displacement,
        "tessellation_cap": tessellation_cap,
        "uv_scale": uv_scale,
        "uv_offset": uv_offset,
        "address_mode_u": address_u,
        "address_mode_v": address_v,
        "atlas_rect": atlas_rect,
        "sss_participation": sss_participation,
        "sss_tint": sss_tint,
        "sss_radius": sss_radius,
        "thickness_scale": thickness_scale,
        "roughness": roughness,
        "reflectivity": reflectivity,
        "metallic": metallic,
    }


def pack_surface_materials(
    *,
    asset_id: str,
    mesh_uv_hash: int,
    batch_materials: list[str],
    records: list[dict],
    images: dict[str, tuple[int, int, int, bytes]] | None = None,
) -> bytes:
    """ Deterministically serialize a BWSFM1 surface-material sidecar.

    ``images`` maps image_name -> (role, width, height, rgba_bytes).
    ``records`` is a list of material record dicts for ``asset_id``. Records are
    sorted by ``(asset_id, material_name)`` and bound to matching batch materials;
    batches whose material has no record receive ``NO_SURFACE_MATERIAL``.
    """
    _validate_identifier(asset_id, "asset_id")
    if type(mesh_uv_hash) is not int or not 0 <= mesh_uv_hash < (1 << 64):
        raise ValueError("Invalid mesh_uv_hash")
    if not isinstance(batch_materials, list) or not 1 <= len(batch_materials) <= MAX_BATCHES:
        raise ValueError("Invalid batch_materials count")
    for mat_name in batch_materials:
        _validate_material_name(mat_name)
    if not isinstance(records, list) or len(records) > MAX_RECORDS:
        raise ValueError("Invalid surface material record count")

    images = images or {}
    if not isinstance(images, dict) or len(images) > MAX_IMAGES:
        raise ValueError("Invalid surface material image count")

    image_roles: dict[str, int] = {}
    validated_images: dict[str, tuple[int, int, int, int, bytes]] = {}
    for name, entry in images.items():
        _validate_identifier(name, "image name")
        if not isinstance(entry, (tuple, list)) or len(entry) != 4:
            raise ValueError("Image entry must be (role, width, height, pixels)")
        role, width, height, pixels = entry
        if (
            type(role) is not int
            or role not in (ROLE_HEIGHT, ROLE_THICKNESS)
            or type(width) is not int
            or type(height) is not int
            or not 1 <= width <= MAX_DIMENSION
            or not 1 <= height <= MAX_DIMENSION
            or not isinstance(pixels, (bytes, bytearray))
            or len(pixels) != width * height * 4
        ):
            raise ValueError(f"Invalid surface material image: {name!r}")
        raw_pixels = bytes(pixels)
        image_roles[name] = role
        validated_images[name] = (role, width, height, uncached_pixel_hash(raw_pixels), raw_pixels)

    batch_material_set = set(batch_materials)
    normalized_records = []
    seen_identities = set()
    used_image_names = set()
    for raw_record in records:
        norm = normalize_record(raw_record, image_roles)
        if norm["asset_id"] != asset_id:
            raise ValueError("Record asset_id disagrees with pack asset_id")
        if norm["material_name"] not in batch_material_set:
            raise ValueError(f"Surface material {norm['material_name']!r} is not present in batch_materials")
        identity = (norm["asset_id"], norm["material_name"])
        if identity in seen_identities:
            raise ValueError(f"Duplicate surface material record: {identity}")
        seen_identities.add(identity)
        if norm["height_image"] is not None:
            used_image_names.add(norm["height_image"])
        if norm["thickness_image"] is not None:
            used_image_names.add(norm["thickness_image"])
        normalized_records.append(norm)

    normalized_records.sort(key=lambda r: (r["asset_id"].encode("utf-8"), r["material_name"].encode("ascii")))
    ordered_image_names = sorted(used_image_names, key=lambda s: s.encode("utf-8"))
    image_index_by_name = {name: idx for idx, name in enumerate(ordered_image_names)}
    record_index_by_material = {r["material_name"]: idx for idx, r in enumerate(normalized_records)}

    bindings = [
        record_index_by_material.get(mat_name, NO_SURFACE_MATERIAL)
        for mat_name in batch_materials
    ]

    out = bytearray(MAGIC)
    out.extend(
        struct.pack(
            "<IIIIQ",
            VERSION,
            len(bindings),
            len(normalized_records),
            len(ordered_image_names),
            mesh_uv_hash,
        )
    )
    out.extend(struct.pack("<" + "I" * len(bindings), *bindings))

    for rec in normalized_records:
        asset_bytes = rec["asset_id"].encode("utf-8")
        mat_bytes = rec["material_name"].encode("ascii")
        h_idx = (
            NO_SURFACE_IMAGE
            if rec["height_image"] is None
            else image_index_by_name[rec["height_image"]]
        )
        t_idx = (
            NO_SURFACE_IMAGE
            if rec["thickness_image"] is None
            else image_index_by_name[rec["thickness_image"]]
        )
        out.extend(struct.pack("<I", len(asset_bytes)) + asset_bytes)
        out.extend(struct.pack("<I", len(mat_bytes)) + mat_bytes)
        out.extend(
            struct.pack(
                "<IIfffIffffIIfffffffffffff",
                h_idx,
                t_idx,
                rec["height_reference"],
                rec["height_amplitude"],
                rec["max_displacement"],
                rec["tessellation_cap"],
                rec["uv_scale"][0],
                rec["uv_scale"][1],
                rec["uv_offset"][0],
                rec["uv_offset"][1],
                rec["address_mode_u"],
                rec["address_mode_v"],
                rec["atlas_rect"][0],
                rec["atlas_rect"][1],
                rec["atlas_rect"][2],
                rec["atlas_rect"][3],
                rec["sss_participation"],
                rec["sss_tint"][0],
                rec["sss_tint"][1],
                rec["sss_tint"][2],
                rec["sss_radius"],
                rec["thickness_scale"],
                rec["roughness"],
                rec["reflectivity"],
                rec["metallic"],
            )
        )

    decoded_total = 0
    for name in ordered_image_names:
        role, width, height, digest, raw_pixels = validated_images[name]
        decoded_total += len(raw_pixels)
        if decoded_total > MAX_SIDECAR_BYTES:
            raise ValueError("Surface material decoded image budget exceeded")
        name_bytes = name.encode("utf-8")
        out.extend(struct.pack("<I", len(name_bytes)) + name_bytes)
        out.extend(struct.pack("<IIIQ", role, width, height, digest))
        out.extend(raw_pixels)

    if len(out) > MAX_SIDECAR_BYTES:
        raise ValueError("Surface material sidecar exceeds 256 MiB limit")
    return bytes(out)


def read_surface_materials(
    data: bytes,
    *,
    expected_asset_id: str | None = None,
    expected_mesh_uv_hash: int | None = None,
    expected_batch_materials: list[str] | None = None,
    max_bytes: int = MAX_SIDECAR_BYTES,
) -> dict:
    """Parse and validate a BWSFM1 surface-material sidecar."""
    if type(max_bytes) is not int or not 0 < max_bytes <= MAX_SIDECAR_BYTES:
        raise ValueError("Invalid surface material budget")
    if not isinstance(data, (bytes, bytearray)) or len(data) > max_bytes:
        raise ValueError("Surface material sidecar exceeds size budget")
    if expected_asset_id is not None:
        _validate_identifier(expected_asset_id, "expected_asset_id")
    if expected_batch_materials is not None:
        if not isinstance(expected_batch_materials, list) or not 1 <= len(expected_batch_materials) <= MAX_BATCHES:
            raise ValueError("Invalid expected_batch_materials")
        for mat_name in expected_batch_materials:
            _validate_material_name(mat_name)

    stream = io.BytesIO(data)

    def take(size: int) -> bytes:
        if size < 0:
            raise ValueError("Invalid read size")
        chunk = stream.read(size)
        if len(chunk) != size:
            raise ValueError("Truncated surface material sidecar")
        return chunk

    def u32() -> int:
        return struct.unpack("<I", take(4))[0]

    def text(label: str, limit: int) -> str:
        length = u32()
        if not 1 <= length <= limit:
            raise ValueError(f"Invalid {label} length")
        raw = take(length)
        if b"\0" in raw:
            raise ValueError(f"Embedded NUL in {label}")
        try:
            decoded = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"Invalid UTF-8 in {label}") from exc
        if label == "material_name":
            _validate_material_name(decoded)
        else:
            _validate_identifier(decoded, label, limit)
        return decoded

    if take(8) != MAGIC:
        raise ValueError("Unsupported surface material magic")
    version, batch_count, record_count, image_count, mesh_uv_hash = struct.unpack(
        "<IIIIQ", take(24)
    )
    if version != VERSION:
        raise ValueError(f"Unsupported surface material version: {version}")
    if (
        not 1 <= batch_count <= MAX_BATCHES
        or record_count > MAX_RECORDS
        or image_count > MAX_IMAGES
    ):
        raise ValueError("Invalid surface material counts")
    if expected_mesh_uv_hash is not None and mesh_uv_hash != expected_mesh_uv_hash:
        raise ValueError("Surface material mesh/UV compatibility hash mismatch")
    if expected_batch_materials is not None and len(expected_batch_materials) != batch_count:
        raise ValueError("Surface material batch count mismatch")

    bindings = list(struct.unpack("<" + "I" * batch_count, take(batch_count * 4)))
    for index in bindings:
        if index != NO_SURFACE_MATERIAL and index >= record_count:
            raise ValueError("Surface material batch binding out of range")

    raw_records = []
    previous_key = None
    for _ in range(record_count):
        rec_asset = text("asset_id", MAX_IDENTIFIER_BYTES)
        if expected_asset_id is not None and rec_asset != expected_asset_id:
            raise ValueError("Surface material asset_id mismatch")
        mat_name = text("material_name", MAX_MATERIAL_NAME_BYTES)
        sort_key = (rec_asset.encode("utf-8"), mat_name.encode("ascii"))
        if previous_key is not None and sort_key <= previous_key:
            raise ValueError("Duplicate or unsorted surface material record")
        previous_key = sort_key

        fields = struct.unpack("<IIfffIffffIIfffffffffffff", take(100))
        (
            h_idx,
            t_idx,
            height_reference,
            height_amplitude,
            max_displacement,
            tessellation_cap,
            scale_u,
            scale_v,
            offset_u,
            offset_v,
            address_u,
            address_v,
            atlas_min_u,
            atlas_min_v,
            atlas_max_u,
            atlas_max_v,
            sss_participation,
            tint_r,
            tint_g,
            tint_b,
            sss_radius,
            thickness_scale,
            roughness,
            reflectivity,
            metallic,
        ) = fields

        if h_idx != NO_SURFACE_IMAGE and h_idx >= image_count:
            raise ValueError("height_image index out of range")
        if t_idx != NO_SURFACE_IMAGE and t_idx >= image_count:
            raise ValueError("thickness_image index out of range")

        _f32(height_reference, "height_reference", 0.0, 1.0)
        _f32(height_amplitude, "height_amplitude", -MAX_WORLD_AMPLITUDE, MAX_WORLD_AMPLITUDE)
        _f32(max_displacement, "max_displacement", 0.0, MAX_WORLD_AMPLITUDE)
        if max_displacement < abs(height_amplitude):
            raise ValueError("max_displacement < abs(height_amplitude)")
        if h_idx == NO_SURFACE_IMAGE and (height_amplitude != 0.0 or max_displacement != 0.0):
            raise ValueError("Non-zero height parameters without height_image")
        if not 1 <= tessellation_cap <= 8 or (h_idx == NO_SURFACE_IMAGE and tessellation_cap != 1):
            raise ValueError("Invalid tessellation_cap")

        _f32(scale_u, "uv_scale[0]", -MAX_UV_TRANSFORM, MAX_UV_TRANSFORM)
        _f32(scale_v, "uv_scale[1]", -MAX_UV_TRANSFORM, MAX_UV_TRANSFORM)
        if scale_u == 0.0 or scale_v == 0.0:
            raise ValueError("Zero uv_scale component")
        _f32(offset_u, "uv_offset[0]", -MAX_UV_TRANSFORM, MAX_UV_TRANSFORM)
        _f32(offset_v, "uv_offset[1]", -MAX_UV_TRANSFORM, MAX_UV_TRANSFORM)
        if address_u not in (ADDRESS_WRAP, ADDRESS_MIRROR, ADDRESS_CLAMP) or address_v not in (
            ADDRESS_WRAP,
            ADDRESS_MIRROR,
            ADDRESS_CLAMP,
        ):
            raise ValueError("Invalid UV address mode")

        for val in (atlas_min_u, atlas_min_v, atlas_max_u, atlas_max_v):
            _f32(val, "atlas_rect", 0.0, 1.0)
        if not (atlas_min_u < atlas_max_u and atlas_min_v < atlas_max_v):
            raise ValueError("Invalid atlas_rect bounds")

        _f32(sss_participation, "sss_participation", 0.0, 1.0)
        for val in (tint_r, tint_g, tint_b):
            _f32(val, "sss_tint", 0.0, 1.0)
        _f32(sss_radius, "sss_radius", 0.0, MAX_WORLD_AMPLITUDE)
        _f32(thickness_scale, "thickness_scale", 0.0, MAX_WORLD_AMPLITUDE)
        if sss_participation == 0.0 and (
            sss_radius != 0.0 or thickness_scale != 0.0 or t_idx != NO_SURFACE_IMAGE
        ):
            raise ValueError("SSS parameters set while sss_participation is zero")

        _f32(roughness, "roughness", 0.0, 1.0)
        _f32(reflectivity, "reflectivity", 0.0, 1.0)
        _f32(metallic, "metallic", 0.0, 1.0)

        raw_records.append(
            {
                "asset_id": rec_asset,
                "material_name": mat_name,
                "height_image": h_idx,
                "thickness_image": t_idx,
                "height_reference": height_reference,
                "height_amplitude": height_amplitude,
                "max_displacement": max_displacement,
                "tessellation_cap": tessellation_cap,
                "uv_scale": (scale_u, scale_v),
                "uv_offset": (offset_u, offset_v),
                "address_mode_u": address_u,
                "address_mode_v": address_v,
                "atlas_rect": (atlas_min_u, atlas_min_v, atlas_max_u, atlas_max_v),
                "sss_participation": sss_participation,
                "sss_tint": (tint_r, tint_g, tint_b),
                "sss_radius": sss_radius,
                "thickness_scale": thickness_scale,
                "roughness": roughness,
                "reflectivity": reflectivity,
                "metallic": metallic,
            }
        )

    images = []
    previous_image_name = None
    decoded_total = 0
    for _ in range(image_count):
        img_name = text("image_name", MAX_IDENTIFIER_BYTES)
        img_key = img_name.encode("utf-8")
        if previous_image_name is not None and img_key <= previous_image_name:
            raise ValueError("Duplicate or unsorted surface material image name")
        previous_image_name = img_key
        role, width, height, expected_hash = struct.unpack("<IIIQ", take(20))
        if (
            role not in (ROLE_HEIGHT, ROLE_THICKNESS)
            or not 1 <= width <= MAX_DIMENSION
            or not 1 <= height <= MAX_DIMENSION
        ):
            raise ValueError("Invalid surface material image header")
        byte_count = width * height * 4
        if decoded_total + byte_count > max_bytes:
            raise ValueError("Surface material decoded images exceed budget")
        decoded_total += byte_count
        pixels = take(byte_count)
        if uncached_pixel_hash(pixels) != expected_hash:
            raise ValueError("Surface material image hash mismatch")
        images.append(
            {
                "name": img_name,
                "role": role,
                "width": width,
                "height": height,
                "hash": expected_hash,
                "pixels": pixels,
            }
        )

    if stream.read(1):
        raise ValueError("Trailing surface material data")

    for rec in raw_records:
        h_idx = rec["height_image"]
        if h_idx != NO_SURFACE_IMAGE and images[h_idx]["role"] != ROLE_HEIGHT:
            raise ValueError("height_image references a non-height image")
        t_idx = rec["thickness_image"]
        if t_idx != NO_SURFACE_IMAGE and images[t_idx]["role"] != ROLE_THICKNESS:
            raise ValueError("thickness_image references a non-thickness image")

    if expected_batch_materials is not None:
        for batch_index, rec_index in enumerate(bindings):
            if rec_index == NO_SURFACE_MATERIAL:
                continue
            if raw_records[rec_index]["material_name"] != expected_batch_materials[batch_index]:
                raise ValueError("Surface material binding disagrees with batch albedo material")

    return {
        "version": version,
        "mesh_uv_hash": mesh_uv_hash,
        "bindings": bindings,
        "records": raw_records,
        "images": images,
    }


def read_surface_materials_file(
    path: Path,
    *,
    expected_asset_id: str | None = None,
    expected_mesh_uv_hash: int | None = None,
    expected_batch_materials: list[str] | None = None,
    max_bytes: int = MAX_SIDECAR_BYTES,
) -> dict:
    """Read at most the sidecar budget plus one byte before parsing."""
    if type(max_bytes) is not int or not 0 < max_bytes <= MAX_SIDECAR_BYTES:
        raise ValueError("Invalid surface material budget")
    with Path(path).open("rb") as stream:
        data = stream.read(max_bytes + 1)
    return read_surface_materials(
        data,
        expected_asset_id=expected_asset_id,
        expected_mesh_uv_hash=expected_mesh_uv_hash,
        expected_batch_materials=expected_batch_materials,
        max_bytes=max_bytes,
    )
