"""Derive high-fidelity BWSFM1 surface material height sidecars for replacement mechs.

Extracts high-resolution normal maps from BWNRM2 and albedo textures from BWTEX1,
derives Poisson height maps tailored for mech armor and weaponry, preserves smooth
reflective canopy properties for cockpit glass (Window), computes mesh UV hashes,
and packs verified BWSFM1 sidecars and interactive 3D WebGL visual inspection reports.
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
from pathlib import Path
import struct
import sys

try:
    import numpy as np
except ImportError:
    np = None

from surface_materials import (
    pack_surface_materials,
    read_surface_materials,
    mesh_uv_identity_file,
    texture_batch_materials_file,
    ROLE_HEIGHT,
    ADDRESS_WRAP,
    MAX_IMAGES,
)
from terrain_height_maps import (
    derive_height_map,
    evaluate_height_quality,
    derive_normal_map_rgba,
)
from visualize_terrain_heights import (
    encode_png,
    compute_angular_error_heatmap,
    generate_contact_sheet_png,
    generate_html_inspection_report,
)
from mech_inspector_html import generate_mech_html_report
from launch_terrain_inspector import rgb565_to_rgba8

ROOT = Path(__file__).resolve().parents[2]
if not (ROOT / "local").exists():
    candidate_main = Path(r"D:\Projects\MW34Recomp")
    if (candidate_main / "local").exists():
        ROOT = candidate_main

HERO_MECHS = ("bushwacker", "madcat")

MECH_MATERIAL_PROFILES: dict[str, dict[str, float]] = {
    "body": {
        "height_amplitude": 0.05,
        "max_displacement": 0.05,
        "height_reference": 0.5,
        "roughness": 0.55,
        "reflectivity": 0.08,
        "metallic": 0.20,
    },
    "variant": {
        "height_amplitude": 0.05,
        "max_displacement": 0.05,
        "height_reference": 0.5,
        "roughness": 0.60,
        "reflectivity": 0.06,
        "metallic": 0.15,
    },
    "weapons": {
        "height_amplitude": 0.06,
        "max_displacement": 0.06,
        "height_reference": 0.5,
        "roughness": 0.45,
        "reflectivity": 0.12,
        "metallic": 0.60,
    },
    "window": {
        "height_amplitude": 0.0,
        "max_displacement": 0.0,
        "height_reference": 0.5,
        "roughness": 0.05,
        "reflectivity": 0.85,
        "metallic": 0.0,
    },
    "missilehead": {
        "height_amplitude": 0.03,
        "max_displacement": 0.03,
        "height_reference": 0.5,
        "roughness": 0.50,
        "reflectivity": 0.08,
        "metallic": 0.30,
    },
    "default": {
        "height_amplitude": 0.05,
        "max_displacement": 0.05,
        "height_reference": 0.5,
        "roughness": 0.55,
        "reflectivity": 0.08,
        "metallic": 0.20,
    },
}


def unpack_bwnrm2(data: bytes) -> tuple[list[int], dict[str, tuple[int, int, int, bytes]]]:
    """Unpack BWNRM2/BWNRM3 normal sidecar into (batch_indices, images)."""
    if not (data.startswith(b"BWNRM2\0\0") or data.startswith(b"BWNRM3\0\0")):
        raise ValueError("Invalid normal map sidecar magic")
    compressed = data.startswith(b"BWNRM3\0\0")
    batch_count, image_count = struct.unpack("<II", data[8:16])
    offset = 16
    batches = list(struct.unpack(f"<{batch_count}I", data[offset:offset + batch_count * 4]))
    offset += batch_count * 4
    images: dict[str, tuple[int, int, int, bytes]] = {}
    for _ in range(image_count):
        raw_name = data[offset:offset + 32]
        name = raw_name.split(b"\0")[0].decode("ascii")
        offset += 32
        w, h, phash = struct.unpack("<IIQ", data[offset:offset + 16])
        offset += 16
        if compressed:
            c_len = struct.unpack("<Q", data[offset:offset + 8])[0]
            offset += 8
            pixels = data[offset:offset + c_len]
            offset += c_len
        else:
            span = w * h * 4
            pixels = data[offset:offset + span]
            offset += span
        images[name] = (w, h, phash, pixels)
    return batches, images


def unpack_bwtex1(data: bytes) -> tuple[list[str], list[str], dict[str, tuple[int, int, int, bytes]]]:
    """Unpack BWTEX1 albedo sidecar into (material_names, batch_materials, images_rgb565)."""
    if not data.startswith(b"BWTEX1\0\0"):
        raise ValueError("Invalid albedo texture sidecar magic")
    count, names_len = struct.unpack("<II", data[8:16])
    offset = 16
    batch_indices = struct.unpack(f"<{count}I", data[offset:offset + count * 4])
    offset += count * 4
    names: list[str] = []
    images: dict[str, tuple[int, int, int, bytes]] = {}
    for _ in range(names_len):
        raw_name = data[offset:offset + 32]
        name = raw_name.split(b"\0")[0].decode("ascii")
        names.append(name)
        offset += 32
        w, h, ident = struct.unpack("<IIQ", data[offset:offset + 16])
        offset += 16
        span = w * h * 2
        pixels565 = data[offset:offset + span]
        offset += span
        images[name] = (w, h, ident, pixels565)
    batch_materials = [names[idx] for idx in batch_indices]
    return names, batch_materials, images


def find_mech_payloads(mech_id: str) -> dict[str, Path]:
    """Locate the mesh, normals, and textures payload files for a replacement mech."""
    candidate_roots = []
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        candidate_roots.append(
            Path(localappdata)
            / "Packages/OpenAI.Codex_2p2nqsd0c76g0/LocalCache/Local/MW3Remaster/mods/com.mw3remaster.mw5-mechs"
        )
    candidate_roots.append(ROOT / "local/work-ahead/combined-model-pack-20261024-r1")
    candidate_roots.append(ROOT / "local/remaster")

    for root in candidate_roots:
        models_json_path = root / "models/models.json"
        if not models_json_path.exists():
            models_json_path = root / "models.json"
        if not models_json_path.exists():
            continue

        try:
            data = json.loads(models_json_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        for m in data.get("models", []):
            if m.get("id") == mech_id:
                env = m.get("environment", {})
                norm_key = f"MW34_{mech_id.upper()}_NORMALS"
                tex_key = f"MW34_{mech_id.upper()}_TEXTURES"
                mesh_candidates = [
                    f"MW34_{mech_id.upper()}_TEST",
                    f"MW34_{mech_id.upper()}_MESH",
                    f"MW34_{mech_id.upper()}_CLOSE_MESH",
                ]
                mesh_key = next((k for k in mesh_candidates if k in env), None)

                if norm_key in env and tex_key in env:
                    norm_path = root / env[norm_key]
                    tex_path = root / env[tex_key]
                    mesh_path = (root / env[mesh_key]) if mesh_key else None

                    if norm_path.exists() and tex_path.exists():
                        return {
                            "normals": norm_path,
                            "textures": tex_path,
                            "mesh": mesh_path,
                            "root": root,
                        }

    raise FileNotFoundError(f"Could not locate payload files for mech '{mech_id}'.")


def extract_mech_geometry(mesh_path: Path, texture_path: Path) -> dict:
    """Extract and group mech vertices by material for real-time 3D WebGL rendering."""
    mats = texture_batch_materials_file(texture_path)
    stream = io.BytesIO(mesh_path.read_bytes())
    magic = stream.read(8)
    count = struct.unpack("<I", stream.read(4))[0]
    mat_verts: dict[str, bytearray] = {}
    all_xyz: list[tuple[float, float, float]] = []
    for i in range(count):
        stream.read(32)  # owner
        stream.read(32)  # visibility
        if magic in (b"BWMESH3\0", b"BWMESH5\0", b"BWMESH6\0"):
            stream.read(44)  # placement
        if magic in (b"BWMESH5\0", b"BWMESH6\0"):
            stream.read(44)  # layered
        if magic in (b"BWMESH6\0",):
            stream.read(44)  # anchored
        vc, _col = struct.unpack("<II", stream.read(8))
        vbytes = stream.read(vc * 32)
        mat = mats[i]
        if mat not in mat_verts:
            mat_verts[mat] = bytearray()
        mat_verts[mat].extend(vbytes)
        stride = max(1, vc // 20)
        for j in range(0, vc, stride):
            all_xyz.append(struct.unpack("<fff", vbytes[j * 32 : j * 32 + 12]))

    xs = [c[0] for c in all_xyz]
    ys = [c[1] for c in all_xyz]
    zs = [c[2] for c in all_xyz]
    cx = (min(xs) + max(xs)) / 2.0
    cy = (min(ys) + max(ys)) / 2.0
    cz = (min(zs) + max(zs)) / 2.0
    radius = max(((c[0] - cx) ** 2 + (c[1] - cy) ** 2 + (c[2] - cz) ** 2) ** 0.5 for c in all_xyz)

    encoded_mats = {
        mat: base64.b64encode(bytes(buf)).decode("ascii")
        for mat, buf in mat_verts.items()
    }
    return {
        "materials": encoded_mats,
        "material_vert_counts": {mat: len(buf) // 32 for mat, buf in mat_verts.items()},
        "center": [round(cx, 3), round(cy, 3), round(cz, 3)],
        "radius": round(radius, 3),
        "total_vertices": sum(len(buf) // 32 for buf in mat_verts.values()),
    }


def build_mech_surface_materials(
    mech_id: str,
    max_dimension: int = 2048,
    html_report_path: Path | None = None,
    contact_sheets_dir: Path | None = None,
    overrides: dict[str, dict[str, float]] | None = None,
) -> tuple[bytes, dict]:
    """Derive height maps and build verified BWSFM1 sidecar for a replacement mech."""
    overrides = overrides or {}
    resources = find_mech_payloads(mech_id)

    normals_data = resources["normals"].read_bytes()
    textures_data = resources["textures"].read_bytes()

    _n_batches, n_images = unpack_bwnrm2(normals_data)
    _mat_names, batch_materials, t_images = unpack_bwtex1(textures_data)

    mesh_uv_hash = 0
    if resources.get("mesh") and resources["mesh"].exists():
        mesh_uv_hash = mesh_uv_identity_file(resources["mesh"])

    records = []
    images = {}
    quality_summary = {}
    visual_entries = []

    # Process all unique materials present on the mech
    unique_materials = list(dict.fromkeys(batch_materials))

    for mat_name in unique_materials:
        clean_key = mat_name.lower()
        prof = MECH_MATERIAL_PROFILES.get(clean_key, MECH_MATERIAL_PROFILES["default"]).copy()
        if mat_name in overrides:
            prof.update(overrides[mat_name])

        height_img_name = f"h_{mat_name}"

        # Albedo extraction (RGB565 -> RGBA8)
        color_bytes = None
        color_w, color_h = 0, 0
        if mat_name in t_images:
            tw, th, _ident, t_pix565 = t_images[mat_name]
            color_bytes = rgb565_to_rgba8(t_pix565)
            color_w, color_h = tw, th

        # Normal extraction
        normal_bytes = None
        nw, nh = color_w, color_h
        if mat_name in n_images:
            nw, nh, _phash, normal_bytes = n_images[mat_name]

        # Handle cockpit window or materials without normal maps
        if normal_bytes is None:
            nw = color_w if color_w > 0 else 64
            nh = color_h if color_h > 0 else 64
            normal_bytes = bytes([128, 128, 255, 255] * (nw * nh))
            h_bytes = bytes([128, 128, 128, 255] * (nw * nh))
            h_ref = 0.5
            quality = {"median_angular_error_deg": 0.0, "correlation_x": 1.0}
        else:
            # Downsample oversized normals if requested
            if max_dimension > 0 and (nw > max_dimension or nh > max_dimension):
                stride = max(nw // max_dimension, nh // max_dimension)
                if stride > 1:
                    arr = np.frombuffer(normal_bytes, dtype=np.uint8).reshape(nh, nw, 4)
                    arr = arr[::stride, ::stride].copy()
                    nh, nw = arr.shape[:2]
                    normal_bytes = arr.tobytes()

            if prof["height_amplitude"] <= 0.0:
                h_bytes = bytes([128, 128, 128, 255] * (nw * nh))
                h_ref = 0.5
                quality = {"median_angular_error_deg": 0.0, "correlation_x": 1.0}
            else:
                h_bytes, h_ref, _ = derive_height_map(
                    normal_bytes,
                    nw,
                    nh,
                    color_bytes=color_bytes if (color_w, color_h) == (nw, nh) else None,
                    color_weight=0.0,
                )
                quality = evaluate_height_quality(h_bytes, normal_bytes, nw, nh)

        # Downsample oversized color if needed
        if color_bytes and max_dimension > 0 and (color_w > max_dimension or color_h > max_dimension):
            c_stride = max(color_w // max_dimension, color_h // max_dimension)
            if c_stride > 1:
                arr_c = np.frombuffer(color_bytes, dtype=np.uint8).reshape(color_h, color_w, 4)
                arr_c = arr_c[::c_stride, ::c_stride].copy()
                color_h, color_w = arr_c.shape[:2]
                color_bytes = arr_c.tobytes()

        images[height_img_name] = (ROLE_HEIGHT, nw, nh, h_bytes)
        quality_summary[mat_name] = quality

        rec = {
            "asset_id": f"{mech_id}:close",
            "material_name": mat_name,
            "height_image": height_img_name,
            "height_reference": h_ref,
            "height_amplitude": float(prof["height_amplitude"]),
            "max_displacement": float(prof["max_displacement"]),
            "address_mode_u": ADDRESS_WRAP,
            "address_mode_v": ADDRESS_WRAP,
            "roughness": float(prof.get("roughness", 0.55)),
            "reflectivity": float(prof.get("reflectivity", 0.08)),
            "metallic": float(prof.get("metallic", 0.20)),
        }
        records.append(rec)

        if html_report_path or contact_sheets_dir:
            heatmap_bytes, median_err, corr = compute_angular_error_heatmap(
                normal_bytes, h_bytes, nw, nh
            )
            renorm_bytes = derive_normal_map_rgba(h_bytes, nw, nh)

            if contact_sheets_dir:
                cs_dir = Path(contact_sheets_dir)
                cs_dir.mkdir(parents=True, exist_ok=True)
                if color_bytes:
                    if (color_w, color_h) != (nw, nh):
                        sy = max(1, color_h // nh)
                        sx = max(1, color_w // nw)
                        arr_c = np.frombuffer(color_bytes, dtype=np.uint8).reshape(color_h, color_w, 4)
                        c_for_cs = arr_c[::sy, ::sx][:nh, :nw].copy().tobytes()
                    else:
                        c_for_cs = color_bytes
                else:
                    c_for_cs = normal_bytes

                cs_bytes = generate_contact_sheet_png(
                    c_for_cs,
                    normal_bytes,
                    h_bytes,
                    renorm_bytes,
                    heatmap_bytes,
                    nw,
                    nh,
                )
                (cs_dir / f"{mech_id}_{mat_name}_contact_sheet.png").write_bytes(cs_bytes)

            if html_report_path:
                def to_b64(raw: bytes, iw: int, ih: int, max_thumb: int = 512) -> str:
                    thumb_w, thumb_h = iw, ih
                    if max_thumb > 0 and (iw > max_thumb or ih > max_thumb):
                        stride = max(iw // max_thumb, ih // max_thumb)
                        if stride > 1:
                            arr = np.frombuffer(raw, dtype=np.uint8).reshape(ih, iw, 4)[::stride, ::stride].copy()
                            thumb_h, thumb_w = arr.shape[:2]
                            raw = arr.tobytes()
                    png = encode_png(thumb_w, thumb_h, raw)
                    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")

                visual_entries.append({
                    "name": mat_name,
                    "family": clean_key,
                    "width": nw,
                    "height": nh,
                    "median_error_deg": float(quality.get("median_angular_error_deg", median_err)),
                    "correlation": float(quality.get("correlation_x", corr)),
                    "height_amplitude": float(prof["height_amplitude"]),
                    "roughness": float(prof.get("roughness", 0.55)),
                    "reflectivity": float(prof.get("reflectivity", 0.08)),
                    "metallic": float(prof.get("metallic", 0.20)),
                    "color_data": to_b64(color_bytes, color_w, color_h) if color_bytes else None,
                    "normal_data": to_b64(normal_bytes, nw, nh),
                    "height_data": to_b64(h_bytes, nw, nh),
                    "renorm_data": to_b64(renorm_bytes, nw, nh),
                    "heatmap_data": to_b64(heatmap_bytes, nw, nh),
                })

    sidecar_bytes = pack_surface_materials(
        asset_id=f"{mech_id}:close",
        mesh_uv_hash=mesh_uv_hash,
        batch_materials=batch_materials,
        records=records,
        images=images,
    )

    verified = read_surface_materials(
        sidecar_bytes,
        expected_asset_id=f"{mech_id}:close",
        expected_mesh_uv_hash=mesh_uv_hash,
    )

    if html_report_path and visual_entries:
        report_title = f"{mech_id.capitalize()} Surface Material & Height Map Inspector"
        mesh_path = resources.get("mesh")
        if mesh_path and mesh_path.exists():
            mesh_data = extract_mech_geometry(mesh_path, resources["textures"])
            generate_mech_html_report(report_title, visual_entries, mesh_data, Path(html_report_path))
        else:
            generate_html_inspection_report(report_title, visual_entries, Path(html_report_path))

    report = {
        "mech": mech_id,
        "asset_id": f"{mech_id}:close",
        "mesh_uv_hash": f"0x{mesh_uv_hash:016x}",
        "records_count": len(verified["records"]),
        "images_count": len(verified["images"]),
        "batches_count": len(verified["bindings"]),
        "quality": quality_summary,
    }
    return sidecar_bytes, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mech", required=True, choices=list(HERO_MECHS) + ["all"])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--html-report", type=Path)
    parser.add_argument("--contact-sheets-dir", type=Path)
    parser.add_argument("--max-dimension", type=int, default=2048)

    args = parser.parse_args()

    targets = list(HERO_MECHS) if args.mech == "all" else [args.mech]

    for mech_id in targets:
        print(f"Building surface materials for {mech_id.capitalize()}...")
        html_out = args.html_report
        if html_out and args.mech == "all":
            html_out = html_out.parent / f"{mech_id}_{html_out.name}"

        sidecar_bytes, summary = build_mech_surface_materials(
            mech_id=mech_id,
            max_dimension=args.max_dimension,
            html_report_path=html_out,
            contact_sheets_dir=args.contact_sheets_dir,
        )

        out_path = args.output
        if out_path:
            if args.mech == "all":
                out_path = out_path.parent / f"{mech_id}_{out_path.name}"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(sidecar_bytes)
            print(f"Wrote {len(sidecar_bytes):,} bytes BWSFM1 to {out_path}")

        print(f"Processed {summary['records_count']} materials across {summary['batches_count']} batches.")
        if html_out:
            print(f"Generated HTML inspection report: {html_out}")


if __name__ == "__main__":
    main()
