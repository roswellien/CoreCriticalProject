"""Generate BWSFM1 height-map surface-material catalogs from environment normal maps.

Reads an environment pack's BWSNR2/BWSNR3 normal catalogs, integrates tangent-space
normals into tileable linear height fields via Frankot-Chellappa Poisson integration,
and packs a validated region-level BWSFM1 sidecar (mesh_uv_hash = 0) for Core Critical
parallax occlusion mapping (POM).

Does not ship or bundle original game media; operates on local user-supplied packs.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys

try:
    import numpy as np
except ImportError:
    np = None

_LAUNCHER_DIR = Path(__file__).resolve().parent
if str(_LAUNCHER_DIR) not in sys.path:
    sys.path.insert(0, str(_LAUNCHER_DIR))

from normal_materials import NO_NORMAL, uncached_pixel_hash  # noqa: E402
from surface_materials import (  # noqa: E402
    ADDRESS_WRAP,
    MAX_IMAGES,
    MAX_SIDECAR_BYTES,
    ROLE_HEIGHT,
    pack_surface_materials,
    read_surface_materials,
)

# Host-world-unit relief profiles per surface family (MW3 mechs are ~10-14 units tall).
FAMILY_PROFILES: dict[str, dict[str, float]] = {
    "cliff": {
        "height_amplitude": 0.42,
        "roughness": 0.85,
        "reflectivity": 0.03,
        "metallic": 0.0,
    },
    "rock": {
        "height_amplitude": 0.36,
        "roughness": 0.82,
        "reflectivity": 0.04,
        "metallic": 0.0,
    },
    "building": {
        "height_amplitude": 0.24,
        "roughness": 0.72,
        "reflectivity": 0.05,
        "metallic": 0.05,
    },
    "road": {
        "height_amplitude": 0.16,
        "roughness": 0.62,
        "reflectivity": 0.05,
        "metallic": 0.0,
    },
    "sand": {
        "height_amplitude": 0.22,
        "roughness": 0.80,
        "reflectivity": 0.03,
        "metallic": 0.0,
    },
    "terrain": {
        "height_amplitude": 0.30,
        "roughness": 0.78,
        "reflectivity": 0.04,
        "metallic": 0.0,
    },
    "default": {
        "height_amplitude": 0.22,
        "roughness": 0.72,
        "reflectivity": 0.04,
        "metallic": 0.0,
    },
}

_EXCLUDED_SUBSTRINGS = (
    "water",
    "_surf",
    "surf_",
    "foam",
    "cloud",
    "sky",
    "glass",
    "flare",
    "smoke",
    "spark",
    "muzzle",
    "laser",
    "hud",
    "font",
    "cursor",
    "shadow",
    "decal",
    "fire",
    "expl",
    "glow",
    "light",
    "lamp",
    "window",
)


def should_skip_material(name: str) -> bool:
    """Return True for transparent, sky, water, or UI surfaces unsuitable for POM."""
    lower = name.lower()
    if lower == "surf":
        return True
    return any(token in lower for token in _EXCLUDED_SUBSTRINGS)


def classify_material_family(name: str) -> str:
    """Classify a material identifier into a relief amplitude family."""
    lower = name.lower()
    if any(k in lower for k in ("cliff", "bluff", "canyon", "crag", "txwall")):
        return "cliff"
    if any(k in lower for k in ("rock", "boulder", "stone", "rubble", "slate")):
        return "rock"
    if any(k in lower for k in ("wall", "bldg", "hq", "base", "bunk", "conc", "brick", "metal")):
        return "building"
    if any(k in lower for k in ("road", "hwy", "pave", "asphalt", "tarmac", "runway", "street")):
        return "road"
    if any(k in lower for k in ("sand", "dune", "beach", "shore", "desert")):
        return "sand"
    if any(k in lower for k in ("ter", "dirt", "mud", "grass", "ground", "snow", "ice", "soil")):
        return "terrain"
    return "default"


def read_named_normal_images(page_bytes: bytes) -> dict[str, tuple[int, int, bytes]]:
    """Extract unique named RGBA8 normal images from a BWSNR2 or BWSNR3 catalog page."""
    stream = io.BytesIO(page_bytes)

    def read(size: int) -> bytes:
        chunk = stream.read(size)
        if len(chunk) != size:
            raise ValueError("Truncated BWSNR catalog page")
        return chunk

    def u32() -> int:
        return struct.unpack("<I", read(4))[0]

    def read_name() -> str:
        raw = read(32)
        end = raw.find(b"\0")
        if end <= 0:
            raise ValueError("Invalid material name in BWSNR catalog")
        return raw[:end].decode("ascii")

    surface_magic = read(8)
    if surface_magic not in (b"BWSNR2\0\0", b"BWSNR3\0\0"):
        raise ValueError(f"Unsupported surface catalog magic: {surface_magic!r}")
    count = u32()
    if count > 4096:
        raise ValueError("Surface binding count exceeds BWSNR limit")
    for _ in range(count):
        read(20)  # SurfaceKey: w, h, fmt, hash
        read_name()

    normal_magic = read(8)
    expected_normal = b"BWNRM3\0\0" if surface_magic == b"BWSNR3\0\0" else b"BWNRM2\0\0"
    if normal_magic != expected_normal or u32() != count:
        raise ValueError("Invalid embedded normal payload in BWSNR catalog")
    image_count = u32()
    if image_count > 64:
        raise ValueError("Normal image count exceeds BWSNR limit")
    for _ in range(count):
        idx = u32()
        if idx != NO_NORMAL and idx >= image_count:
            raise ValueError("Out-of-range normal index in BWSNR catalog")

    images: dict[str, tuple[int, int, bytes]] = {}
    for _ in range(image_count):
        material = read_name()
        if material in images:
            raise ValueError(f"Duplicate normal image name {material!r} in BWSNR catalog")
        width, height, expected_hash = struct.unpack("<IIQ", read(16))
        if not 0 < width <= 4096 or not 0 < height <= 4096:
            raise ValueError(f"Invalid normal image dimensions {width}x{height} for {material}")
        pixel_bytes = width * height * 4
        if normal_magic == b"BWNRM3\0\0":
            from normal_codec import decode

            encoded_size = struct.unpack("<Q", read(8))[0]
            if not 0 < encoded_size <= width * height * 8:
                raise ValueError(f"Invalid encoded normal size for {material}")
            pixels = decode(read(encoded_size), pixel_bytes)
        else:
            pixels = read(pixel_bytes)
        if uncached_pixel_hash(pixels) != expected_hash:
            raise ValueError(f"Normal image hash mismatch for {material}")
        images[material] = (width, height, pixels)
    if stream.read(1):
        raise ValueError("Trailing bytes in BWSNR catalog page")
    return images


def frankot_chellappa_height(normal_rgba: bytes, width: int, height: int) -> tuple[bytes, float]:
    """Integrate an RGBA8 tangent-space normal map into a tileable linear RGBA8 height map.

    Returns (rgba_bytes, height_reference) where R stores the linear height in [0, 255]
    and height_reference is the normalized mean height in [0, 1].
    """
    if np is None:
        raise RuntimeError("Height-map generation requires NumPy")
    if width < 2 or height < 2:
        raise ValueError("Height map dimensions must be at least 2x2")

    arr = np.frombuffer(normal_rgba, dtype=np.uint8).reshape(height, width, 4).astype(np.float32)
    # Match sun_scene.frag BWNRM2/3 decoding: max((channel - 128) / 127, -1).
    nx = np.maximum((arr[:, :, 0] - 128.0) / 127.0, -1.0)
    ny = np.maximum((arr[:, :, 1] - 128.0) / 127.0, -1.0)
    nz = np.maximum((arr[:, :, 2] - 128.0) / 127.0, 0.05)

    p = -nx / nz
    q = -ny / nz

    u = np.fft.fftfreq(width)
    v = np.fft.fftfreq(height)
    uu, vv = np.meshgrid(u, v)

    denom = (2.0 * math.pi) ** 2 * (uu * uu + vv * vv)
    denom[0, 0] = 1.0
    z_freq = (-1j * 2.0 * math.pi * uu * np.fft.fft2(p) - 1j * 2.0 * math.pi * vv * np.fft.fft2(q)) / denom
    z_freq[0, 0] = 0.0

    z = np.real(np.fft.ifft2(z_freq)).astype(np.float32)
    z_min = float(np.min(z))
    z_max = float(np.max(z))
    span = z_max - z_min
    if span <= 1e-6:
        norm = np.full((height, width), 0.5, dtype=np.float32)
        reference = 0.5
    else:
        norm = np.clip((z - z_min) / span, 0.0, 1.0)
        reference = float(np.clip(np.mean(norm), 0.0, 1.0))

    u8 = np.clip(np.round(norm * 255.0), 0, 255).astype(np.uint8)
    out = np.empty((height, width, 4), dtype=np.uint8)
    out[:, :, 0] = u8
    out[:, :, 1] = u8
    out[:, :, 2] = u8
    out[:, :, 3] = 255
    return out.tobytes(), reference


def _downsample_rgba(pixels: bytes, width: int, height: int, max_dim: int) -> tuple[int, int, bytes]:
    if max_dim <= 0 or (width <= max_dim and height <= max_dim):
        return width, height, pixels
    stride_x = max(1, math.ceil(width / max_dim))
    stride_y = max(1, math.ceil(height / max_dim))
    if stride_x == 1 and stride_y == 1:
        return width, height, pixels
    new_w = max(1, width // stride_x)
    new_h = max(1, height // stride_y)
    arr = np.frombuffer(pixels, dtype=np.uint8).reshape(height, width, 4).astype(np.float32)
    cropped = arr[: new_h * stride_y, : new_w * stride_x, :]
    blocks = cropped.reshape(new_h, stride_y, new_w, stride_x, 4)
    nx = np.maximum((blocks[:, :, :, :, 0] - 128.0) / 127.0, -1.0).mean(axis=(1, 3))
    ny = np.maximum((blocks[:, :, :, :, 1] - 128.0) / 127.0, -1.0).mean(axis=(1, 3))
    nz = np.maximum((blocks[:, :, :, :, 2] - 128.0) / 127.0, -1.0).mean(axis=(1, 3))
    length = np.maximum(np.sqrt(nx * nx + ny * ny + nz * nz), 1e-6)
    out = np.empty((new_h, new_w, 4), dtype=np.uint8)
    out[:, :, 0] = np.clip(np.round((nx / length) * 127.0 + 128.0), 0, 255).astype(np.uint8)
    out[:, :, 1] = np.clip(np.round((ny / length) * 127.0 + 128.0), 0, 255).astype(np.uint8)
    out[:, :, 2] = np.clip(np.round((nz / length) * 127.0 + 128.0), 0, 255).astype(np.uint8)
    out[:, :, 3] = 255
    return new_w, new_h, out.tobytes()


def _normal_energy(pixels: bytes, width: int, height: int) -> float:
    arr = np.frombuffer(pixels, dtype=np.uint8).reshape(height, width, 4).astype(np.float32)
    dx = np.abs(arr[:, :, 0] - 128.0)
    dy = np.abs(arr[:, :, 1] - 128.0)
    return float(np.mean(np.maximum(dx, dy)))


def _manifest_pages(manifest_path: Path) -> list[Path]:
    if not manifest_path.is_file():
        return []
    lines = [line.strip() for line in manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [manifest_path.parent / rel for rel in lines[1:]]


def build_environment_surface_materials(
    pack_dir: Path,
    *,
    region: str | None = None,
    max_dimension: int = 128,
    max_materials: int = MAX_IMAGES,
    min_normal_energy: float = 2.0,
) -> tuple[bytes, dict]:
    """Build a validated region-level BWSFM1 sidecar from an environment pack directory."""
    if np is None:
        raise RuntimeError("Height-map generation requires NumPy")

    env_dir = pack_dir / "environment"
    env_json_path = env_dir / "environment.json"
    if region is None:
        if not env_json_path.is_file():
            raise ValueError("Cannot infer region without environment/environment.json")
        env_json = json.loads(env_json_path.read_text(encoding="utf-8"))
        region = str(env_json["operation"])

    pages = _manifest_pages(env_dir / "authored.txt") + _manifest_pages(env_dir / "world.txt")
    if not pages:
        raise ValueError(f"No BWSNR catalog pages found under {env_dir}")

    # Key every unique normal image by its authenticated 64-bit pixel hash
    # ("n_<16-hex>") so authored.txt and world.txt pages can never collide or
    # shadow each other, while retaining the original material name for family
    # classification.
    unique_normals: dict[str, tuple[str, int, int, bytes]] = {}
    skipped_excluded = 0
    for page in pages:
        if not page.is_file():
            continue
        for mat_name, img in read_named_normal_images(page.read_bytes()).items():
            width, height, pixels = img
            if should_skip_material(mat_name) or width < 2 or height < 2:
                skipped_excluded += 1
                continue
            norm_hash = uncached_pixel_hash(pixels)
            key_name = f"n_{norm_hash:016x}"
            if key_name not in unique_normals:
                # Downsample immediately to keep memory bounded across large packs.
                dw, dh, reduced = _downsample_rgba(pixels, width, height, max_dimension)
                if dw < 2 or dh < 2:
                    continue
                unique_normals[key_name] = (mat_name, dw, dh, reduced)
            else:
                # Prefer a non-generic authored name for family classification.
                existing_name, ew, eh, epx = unique_normals[key_name]
                if existing_name.startswith("surface") and not mat_name.startswith("surface"):
                    unique_normals[key_name] = (mat_name, ew, eh, epx)

    candidates: list[tuple[float, str, str, int, int, bytes]] = []
    skipped_flat = 0
    for key_name, (orig_name, width, height, pixels) in unique_normals.items():
        energy = _normal_energy(pixels, width, height)
        if energy < min_normal_energy:
            skipped_flat += 1
            continue
        candidates.append((energy, key_name, orig_name, width, height, pixels))

    # Prefer the strongest-relief surfaces if a region has more than MAX_IMAGES materials.
    candidates.sort(key=lambda item: (-item[0], item[1]))
    limit = min(max_materials, MAX_IMAGES)
    selected = candidates[:limit]
    if not selected:
        raise ValueError(f"No eligible normal maps found for region {region!r}")

    records = []
    images: dict[str, tuple[int, int, int, bytes]] = {}
    batch_materials: list[str] = []
    total_image_bytes = 0
    budget_limit = MAX_SIDECAR_BYTES - 1024 * 1024

    for _, key_name, orig_name, dw, dh, reduced in sorted(selected, key=lambda item: item[1]):
        if dw < 2 or dh < 2:
            continue
        image_bytes = dw * dh * 4
        if total_image_bytes + image_bytes > budget_limit:
            break
        height_pixels, height_ref = frankot_chellappa_height(reduced, dw, dh)
        family = classify_material_family(orig_name)
        profile = FAMILY_PROFILES[family]
        image_name = f"h_{key_name}"
        images[image_name] = (ROLE_HEIGHT, dw, dh, height_pixels)
        total_image_bytes += image_bytes
        batch_materials.append(key_name)
        records.append(
            {
                "asset_id": region,
                "material_name": key_name,
                "height_image": image_name,
                "height_reference": height_ref,
                "height_amplitude": profile["height_amplitude"],
                "max_displacement": profile["height_amplitude"],
                "address_mode_u": ADDRESS_WRAP,
                "address_mode_v": ADDRESS_WRAP,
                "uv_scale": (1.0, 1.0),
                "uv_offset": (0.0, 0.0),
                "atlas_rect": (0.0, 0.0, 1.0, 1.0),
                "roughness": profile["roughness"],
                "reflectivity": profile["reflectivity"],
                "metallic": profile["metallic"],
            }
        )

    sidecar = pack_surface_materials(
        asset_id=region,
        mesh_uv_hash=0,
        batch_materials=batch_materials,
        records=records,
        images=images,
    )
    verified = read_surface_materials(sidecar, expected_asset_id=region)
    summary = {
        "region": region,
        "total_normals": len(unique_normals),
        "selected_materials": len(verified["records"]),
        "skipped_excluded": skipped_excluded,
        "skipped_flat": skipped_flat,
        "sidecar_bytes": len(sidecar),
        "decoded_image_bytes": total_image_bytes,
    }
    return sidecar, summary


def update_environment_pack(pack_dir: Path, sidecar_bytes: bytes) -> dict:
    """Write environment/surface_materials.bin and update environment.json + pack.json hashes."""
    rel_sfm = "environment/surface_materials.bin"
    env_rel = "environment/environment.json"
    env_json_path = pack_dir / env_rel
    pack_json_path = pack_dir / "pack.json"
    env_json = json.loads(env_json_path.read_text(encoding="utf-8"))
    manifest = json.loads(pack_json_path.read_text(encoding="utf-8"))
    if not isinstance(env_json, dict) or not isinstance(manifest, dict):
        raise ValueError("Environment registry and pack manifest must be objects")
    files = manifest.setdefault("files", {})
    native_payload = manifest.setdefault("native_payload", {})
    if not isinstance(files, dict) or not isinstance(native_payload, dict):
        raise ValueError("Invalid environment pack file table or native payload")
    if native_payload.setdefault("registry", env_rel) != env_rel:
        raise ValueError("Unsupported environment registry path")
    registry_pin = files.setdefault(env_rel, {})
    req_formats = native_payload.setdefault("required_formats", [])
    req_caps = native_payload.get("required_capabilities")
    if not isinstance(registry_pin, dict) or not isinstance(req_formats, list):
        raise ValueError("Invalid environment registry pin or required formats")
    if req_caps is None:
        req_caps = native_payload["required_capabilities"] = {}
    if not isinstance(req_caps, dict):
        raise ValueError("Invalid environment capability requirements")

    env_json["surface_materials"] = rel_sfm
    env_json_bytes = (json.dumps(env_json, indent=2) + "\n").encode("utf-8")
    files[rel_sfm] = {
        "bytes": len(sidecar_bytes),
        "sha256": hashlib.sha256(sidecar_bytes).hexdigest(),
        "format": "BWSFM1",
    }
    registry_pin.update(bytes=len(env_json_bytes), sha256=hashlib.sha256(env_json_bytes).hexdigest())
    if "BWSFM1" not in req_formats:
        req_formats.append("BWSFM1")
    req_caps["surface-materials"] = 1
    manifest_bytes = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")

    (pack_dir / rel_sfm).write_bytes(sidecar_bytes)
    env_json_path.write_bytes(env_json_bytes)
    pack_json_path.write_bytes(manifest_bytes)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack-dir", type=Path, required=True, help="Local environment pack folder")
    parser.add_argument("--region", default=None, help="Override region/asset_id")
    parser.add_argument("--output", type=Path, default=None, help="Write standalone BWSFM1 file")
    parser.add_argument("--update-pack", action="store_true", help="Write into pack and update manifests")
    parser.add_argument("--max-dimension", type=int, default=128, help="Max height-map width/height")
    parser.add_argument("--max-materials", type=int, default=MAX_IMAGES, help="Max materials per region")
    args = parser.parse_args()

    sidecar, summary = build_environment_surface_materials(
        args.pack_dir,
        region=args.region,
        max_dimension=args.max_dimension,
        max_materials=args.max_materials,
    )
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(sidecar)
    if args.update_pack:
        update_environment_pack(args.pack_dir, sidecar)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
