"""Terrain height-map derivation and BWSFM1 surface-material generator.

Derives metric height maps from tangent-space normal maps via Frankot-Chellappa
2D Poisson integration with optional high-pass colour luminance refinement.
Packs validated BWSFM1 environment surface-material sidecars for runtime POM.
"""

from __future__ import annotations

import argparse
import io
import json
import math
from pathlib import Path
import re
import struct
import sys

try:
    import numpy as np
except ImportError:
    np = None

try:
    from surface_materials import (
        pack_surface_materials,
        read_surface_materials,
        ROLE_HEIGHT,
        ADDRESS_WRAP,
        MAX_IMAGES,
    )
    from normal_materials import read_surface_bindings
    from prepared_environment_packs import REGIONS, sha
except ImportError:
    launcher_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(launcher_dir))
    from surface_materials import (
        pack_surface_materials,
        read_surface_materials,
        ROLE_HEIGHT,
        ADDRESS_WRAP,
        MAX_IMAGES,
    )
    from normal_materials import read_surface_bindings
    from prepared_environment_packs import REGIONS, sha


FAMILY_PROFILES = {
    "cliff": {"height_amplitude": 0.50, "max_displacement": 0.50, "color_weight": 0.10, "roughness": 0.85, "reflectivity": 0.03, "metallic": 0.0},
    "rock": {"height_amplitude": 0.45, "max_displacement": 0.45, "color_weight": 0.09, "roughness": 0.80, "reflectivity": 0.04, "metallic": 0.0},
    "road": {"height_amplitude": 0.20, "max_displacement": 0.20, "color_weight": 0.05, "roughness": 0.60, "reflectivity": 0.05, "metallic": 0.0},
    "asphalt": {"height_amplitude": 0.18, "max_displacement": 0.18, "color_weight": 0.04, "roughness": 0.55, "reflectivity": 0.05, "metallic": 0.0},
    "sand": {"height_amplitude": 0.25, "max_displacement": 0.25, "color_weight": 0.08, "roughness": 0.80, "reflectivity": 0.03, "metallic": 0.0},
    "beach": {"height_amplitude": 0.22, "max_displacement": 0.22, "color_weight": 0.07, "roughness": 0.75, "reflectivity": 0.04, "metallic": 0.0},
    "terrain": {"height_amplitude": 0.35, "max_displacement": 0.35, "color_weight": 0.08, "roughness": 0.75, "reflectivity": 0.04, "metallic": 0.0},
    "default": {"height_amplitude": 0.30, "max_displacement": 0.30, "color_weight": 0.06, "roughness": 0.70, "reflectivity": 0.04, "metallic": 0.0},
}


def classify_material_family(name: str) -> str:
    """Identify texture material family from its canonical identifier."""
    lower = name.lower()
    if any(k in lower for k in ("txwall", "cliff", "bluff")):
        return "cliff"
    if any(k in lower for k in ("rock", "boulder", "stone")):
        return "rock"
    if any(k in lower for k in ("road", "hwy", "pave", "path")):
        return "road"
    if any(k in lower for k in ("asphalt", "tarmac", "runway")):
        return "asphalt"
    if any(k in lower for k in ("sand", "dune")):
        return "sand"
    if any(k in lower for k in ("beach", "shore")):
        return "beach"
    if any(k in lower for k in ("txgter", "ter", "dirt", "mud", "grass", "ground")):
        return "terrain"
    return "default"


def frankot_chellappa(nx: np.ndarray, ny: np.ndarray, nz: np.ndarray) -> np.ndarray:
    """Reconstruct continuous height field z from surface normal components.

    Integrates surface slopes p = -nx/nz and q = -ny/nz in Fourier space
    using the Frankot-Chellappa least-squares formulation under periodic boundaries.
    """
    if np is None:
        raise RuntimeError("Terrain height-map derivation requires NumPy")
    if nx.shape != ny.shape or nx.shape != nz.shape:
        raise ValueError("Normal components must have identical shapes")
    h, w = nx.shape
    if h < 2 or w < 2:
        raise ValueError("Dimensions must be >= 2")

    safe_nz = np.maximum(nz, 1e-4)
    p = -nx / safe_nz
    q = -ny / safe_nz

    P = np.fft.fft2(p)
    Q = np.fft.fft2(q)

    u = np.fft.fftfreq(w)
    v = np.fft.fftfreq(h)
    U, V = np.meshgrid(u, v)

    # Fourier derivative of z: dZ/dx -> 2*pi*i*u * Z
    denom = (2.0 * np.pi * U) ** 2 + (2.0 * np.pi * V) ** 2
    denom[0, 0] = 1.0

    Z = (-1j * (2.0 * np.pi * U) * P - 1j * (2.0 * np.pi * V) * Q) / denom
    Z[0, 0] = 0.0

    z = np.real(np.fft.ifft2(Z))
    return z


def extract_color_highpass(
    color_bytes: bytes, width: int, height: int, cutoff_ratio: float = 0.05
) -> np.ndarray:
    """Extract zero-mean high-frequency luminance detail from colour texture.

    Suppresses broad illumination gradients while preserving surface grain.
    """
    if np is None:
        raise RuntimeError("Terrain height-map derivation requires NumPy")
    if len(color_bytes) < width * height * 4:
        raise ValueError("Incomplete colour byte payload")
    arr = np.frombuffer(color_bytes[: width * height * 4], dtype=np.uint8).reshape(height, width, 4)
    r = arr[..., 0].astype(np.float32) / 255.0
    g = arr[..., 1].astype(np.float32) / 255.0
    b = arr[..., 2].astype(np.float32) / 255.0
    lum = 0.299 * r + 0.587 * g + 0.114 * b

    L = np.fft.fft2(lum)
    u = np.fft.fftfreq(width)
    v = np.fft.fftfreq(height)
    U, V = np.meshgrid(u, v)
    radius_sq = U**2 + V**2

    # Highpass filter: 1 - Gaussian lowpass
    sigma_sq = (cutoff_ratio / 2.0) ** 2
    hpf = 1.0 - np.exp(-radius_sq / (2.0 * sigma_sq))
    hpf[0, 0] = 0.0

    detail = np.real(np.fft.ifft2(L * hpf))
    detail_std = float(np.std(detail))
    if detail_std > 1e-6:
        detail = (detail - float(np.mean(detail))) / detail_std
    else:
        detail = np.zeros_like(detail)
    return detail


def derive_height_map(
    normal_bytes: bytes,
    width: int,
    height: int,
    color_bytes: bytes | None = None,
    color_weight: float = 0.0,
    percentile_low: float = 0.5,
    percentile_high: float = 99.5,
) -> tuple[bytes, float, dict[str, float]]:
    """Derive normalized 8-bit height RGBA bytes and reference level.

    Returns:
        (rgba_bytes, height_reference, metrics)
    """
    if np is None:
        raise RuntimeError("Terrain height-map derivation requires NumPy")
    if len(normal_bytes) < width * height * 4:
        raise ValueError("Incomplete normal byte payload")
    arr = np.frombuffer(normal_bytes[: width * height * 4], dtype=np.uint8).reshape(height, width, 4)

    # Decoded tangent space normals: R=nx, G=ny, B=nz
    nx = (arr[..., 0].astype(np.float32) / 255.0) * 2.0 - 1.0
    ny = (arr[..., 1].astype(np.float32) / 255.0) * 2.0 - 1.0
    nz = arr[..., 2].astype(np.float32) / 255.0

    length = np.sqrt(nx**2 + ny**2 + nz**2)
    length = np.maximum(length, 1e-6)
    nx /= length
    ny /= length
    nz /= length

    z_raw = frankot_chellappa(nx, ny, nz)

    if color_bytes is not None and color_weight > 0.0:
        detail = extract_color_highpass(color_bytes, width, height)
        z_std = float(np.std(z_raw))
        z_raw = z_raw + (color_weight * z_std) * detail

    p_low = float(np.percentile(z_raw, percentile_low))
    p_high = float(np.percentile(z_raw, percentile_high))
    span = p_high - p_low
    if span < 1e-6:
        z_norm = np.full_like(z_raw, 0.5)
        height_ref = 0.5
    else:
        z_norm = np.clip((z_raw - p_low) / span, 0.0, 1.0)
        height_ref = float(np.median(z_norm))

    h_u8 = (np.clip(z_norm * 255.0, 0.0, 255.0) + 0.5).astype(np.uint8)

    # Store Red as scalar height, G=R, B=R, Alpha=255
    out_rgba = np.zeros((height, width, 4), dtype=np.uint8)
    out_rgba[..., 0] = h_u8
    out_rgba[..., 1] = h_u8
    out_rgba[..., 2] = h_u8
    out_rgba[..., 3] = 255

    metrics = {
        "raw_std": float(np.std(z_raw)),
        "percentile_low": p_low,
        "percentile_high": p_high,
        "height_reference": height_ref,
    }
    return out_rgba.tobytes(), height_ref, metrics


def evaluate_height_quality(
    height_rgba_bytes: bytes,
    normal_rgba_bytes: bytes,
    width: int,
    height: int,
    scale: float = 1.0,
) -> dict[str, float]:
    """Compare central-difference gradients of height map with original normals."""
    if np is None:
        raise RuntimeError("Terrain height-map derivation requires NumPy")
    h_arr = np.frombuffer(height_rgba_bytes[: width * height * 4], dtype=np.uint8).reshape(height, width, 4)
    z = h_arr[..., 0].astype(np.float32) / 255.0

    n_arr = np.frombuffer(normal_rgba_bytes[: width * height * 4], dtype=np.uint8).reshape(height, width, 4)
    nx_orig = (n_arr[..., 0].astype(np.float32) / 255.0) * 2.0 - 1.0
    ny_orig = (n_arr[..., 1].astype(np.float32) / 255.0) * 2.0 - 1.0
    nz_orig = n_arr[..., 2].astype(np.float32) / 255.0
    len_orig = np.maximum(np.sqrt(nx_orig**2 + ny_orig**2 + nz_orig**2), 1e-6)
    nx_orig /= len_orig
    ny_orig /= len_orig
    nz_orig /= len_orig

    # Periodic central differences: dz/dx and dz/dy
    dz_dx = (np.roll(z, -1, axis=1) - np.roll(z, 1, axis=1)) / 2.0 * scale
    dz_dy = (np.roll(z, -1, axis=0) - np.roll(z, 1, axis=0)) / 2.0 * scale

    nx_rec = -dz_dx
    ny_rec = -dz_dy
    nz_rec = np.ones_like(z)
    len_rec = np.maximum(np.sqrt(nx_rec**2 + ny_rec**2 + nz_rec**2), 1e-6)
    nx_rec /= len_rec
    ny_rec /= len_rec
    nz_rec /= len_rec

    dot = np.clip(nx_orig * nx_rec + ny_orig * ny_rec + nz_orig * nz_rec, -1.0, 1.0)
    angular_err_deg = np.arccos(dot) * (180.0 / np.pi)

    std_x_orig = float(np.std(nx_orig))
    std_x_rec = float(np.std(nx_rec))
    corr_x = (
        float(np.corrcoef(nx_orig.flatten(), nx_rec.flatten())[0, 1])
        if std_x_orig > 1e-6 and std_x_rec > 1e-6
        else 1.0
    )

    std_y_orig = float(np.std(ny_orig))
    std_y_rec = float(np.std(ny_rec))
    corr_y = (
        float(np.corrcoef(ny_orig.flatten(), ny_rec.flatten())[0, 1])
        if std_y_orig > 1e-6 and std_y_rec > 1e-6
        else 1.0
    )

    return {
        "median_angular_error_deg": float(np.median(angular_err_deg)),
        "p95_angular_error_deg": float(np.percentile(angular_err_deg, 95.0)),
        "mean_angular_error_deg": float(np.mean(angular_err_deg)),
        "correlation_x": corr_x if not math.isnan(corr_x) else 1.0,
        "correlation_y": corr_y if not math.isnan(corr_y) else 1.0,
    }


def build_region_terrain_sidecar(
    region: str,
    normal_pages_paths: list[Path],
    overrides_dir: Path | None = None,
    color_lookup: dict[tuple[int, int, int, int], bytes] | None = None,
    key_filter: set[tuple[int, int, int, int]] | None = None,
    max_dimension: int = 512,
    max_sidecar_bytes: int = 256 * 1024 * 1024,
) -> tuple[bytes, dict]:
    """Generate a valid BWSFM1 surface-material sidecar bytes and audit summary."""
    if np is None:
        raise RuntimeError("Terrain height-map derivation requires NumPy")
    if region not in REGIONS:
        raise ValueError(f"Unknown region identifier: {region}")

    overrides = {}
    if overrides_dir and overrides_dir.exists():
        overrides_cfg = overrides_dir / "materials.json"
        if overrides_cfg.exists():
            overrides = json.loads(overrides_cfg.read_text(encoding="utf-8"))

    discovered_materials: dict[str, tuple[int, int, bytes]] = {}
    for page_path in normal_pages_paths:
        if not page_path.exists():
            continue
        bindings = read_surface_bindings(page_path.read_bytes())
        for key, normal in bindings:
            if normal is not None:
                if key_filter is not None and key not in key_filter:
                    continue
                nw, nh, normal_bytes = normal
                w_col, h_col, fmt, dig = key
                mat_name = f"tex_{w_col}x{h_col}_{dig:016x}"
                discovered_materials[mat_name] = (nw, nh, normal_bytes)

    records = []
    images = {}
    batch_materials = []
    quality_summary = {}

    total_image_bytes = 0
    image_idx = 0
    for mat_name, (w, h, normal_bytes) in sorted(discovered_materials.items()):
        if len(images) >= MAX_IMAGES:
            break

        # Downsample oversized normals if requested
        if max_dimension > 0 and (w > max_dimension or h > max_dimension):
            stride = max(w // max_dimension, h // max_dimension)
            if stride > 1:
                arr = np.frombuffer(normal_bytes, dtype=np.uint8).reshape(h, w, 4)
                arr = arr[::stride, ::stride].copy()
                h, w = arr.shape[:2]
                normal_bytes = arr.tobytes()

        img_bytes_len = w * h * 4
        if total_image_bytes + img_bytes_len > max_sidecar_bytes - 1048576:
            break

        family = classify_material_family(mat_name)
        prof = FAMILY_PROFILES.get(family, FAMILY_PROFILES["default"]).copy()
        if mat_name in overrides:
            prof.update(overrides[mat_name])

        height_img_name = f"h_{mat_name}"
        color_bytes = color_lookup.get((w, h, 1, 0)) if color_lookup else None

        h_bytes, h_ref, _ = derive_height_map(
            normal_bytes,
            w,
            h,
            color_bytes=color_bytes,
            color_weight=prof.get("color_weight", 0.0),
        )

        quality = evaluate_height_quality(h_bytes, normal_bytes, w, h)
        quality_summary[mat_name] = quality

        images[height_img_name] = (ROLE_HEIGHT, w, h, h_bytes)
        total_image_bytes += img_bytes_len
        batch_materials.append(mat_name)

        rec = {
            "asset_id": region,
            "material_name": mat_name,
            "height_image": height_img_name,
            "height_reference": h_ref,
            "height_amplitude": float(prof["height_amplitude"]),
            "max_displacement": float(prof["max_displacement"]),
            "address_mode_u": ADDRESS_WRAP,
            "address_mode_v": ADDRESS_WRAP,
            "uv_scale": (1.0, 1.0),
            "uv_offset": (0.0, 0.0),
            "atlas_rect": (0.0, 0.0, 1.0, 1.0),
            "roughness": float(prof.get("roughness", 0.70)),
            "reflectivity": float(prof.get("reflectivity", 0.04)),
            "metallic": float(prof.get("metallic", 0.0)),
        }
        records.append(rec)
        image_idx += 1

    if not records:
        # Generate at least one default record so the sidecar is valid
        dummy_name = f"terrain_default_{region}"
        batch_materials.append(dummy_name)
        dummy_h = bytes([128, 128, 128, 255] * 16)
        dummy_img = f"h_{dummy_name}"
        images[dummy_img] = (ROLE_HEIGHT, 4, 4, dummy_h)
        records.append({
            "asset_id": region,
            "material_name": dummy_name,
            "height_image": dummy_img,
            "height_reference": 0.5,
            "height_amplitude": 0.35,
            "max_displacement": 0.35,
            "address_mode_u": ADDRESS_WRAP,
            "address_mode_v": ADDRESS_WRAP,
            "roughness": 0.75,
            "reflectivity": 0.04,
            "metallic": 0.0,
        })

    sidecar_bytes = pack_surface_materials(
        asset_id=region,
        mesh_uv_hash=0,
        batch_materials=batch_materials,
        records=records,
        images=images,
    )

    # Round-trip verification
    verified = read_surface_materials(sidecar_bytes, expected_asset_id=region)

    report = {
        "region": region,
        "records_count": len(verified["records"]),
        "images_count": len(verified["images"]),
        "quality": quality_summary,
    }
    return sidecar_bytes, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    inv = subparsers.add_parser("inventory", help="List terrain normal textures for region")
    inv.add_argument("--region", required=True, choices=list(REGIONS.keys()))
    inv.add_argument("--normals-manifest", type=Path, required=True)

    gen = subparsers.add_parser("generate", help="Generate BWSFM1 terrain height sidecar")
    gen.add_argument("--region", required=True, choices=list(REGIONS.keys()))
    gen.add_argument("--normals-manifest", type=Path, required=True)
    gen.add_argument("--output", type=Path, required=True)
    gen.add_argument("--overrides", type=Path)
    gen.add_argument("--report", type=Path)

    args = parser.parse_args()

    if args.command == "inventory":
        pages = [
            args.normals_manifest.parent / p
            for p in args.normals_manifest.read_text().splitlines()[1:]
            if p
        ]
        count = 0
        for page in pages:
            if page.exists():
                for key, normal in read_surface_bindings(page.read_bytes()):
                    if normal is not None:
                        count += 1
                        print(f"Key: {key} Dim: {normal[0]}x{normal[1]}")
        print(f"Total active terrain normals in {args.region}: {count}")

    elif args.command == "generate":
        pages = [
            args.normals_manifest.parent / p
            for p in args.normals_manifest.read_text().splitlines()[1:]
            if p
        ]
        sidecar_bytes, summary = build_region_terrain_sidecar(
            args.region, pages, overrides_dir=args.overrides
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(sidecar_bytes)
        print(f"Wrote {len(sidecar_bytes)} bytes BWSFM1 to {args.output}")
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
            print(f"Wrote report to {args.report}")


if __name__ == "__main__":
    main()
