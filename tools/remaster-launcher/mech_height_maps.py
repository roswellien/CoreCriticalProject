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
import math
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
from normal_materials import uncached_pixel_hash
from normal_codec import decode as decode_normals

ROOT = Path(__file__).resolve().parents[2]
if not (ROOT / "local").exists():
    candidate_main = Path(r"D:\Projects\MW34Recomp")
    if (candidate_main / "local").exists():
        ROOT = candidate_main

HERO_MECHS = ("bushwacker", "madcat")

REPLACEMENT_MECHS = (
    "bushwacker",
    "madcat",
    "vulture",
    "thor",
    "orion",
    "daishi",
    "shadowcat",
    "puma",
    "annihilator",
    "cauldron",
    "sunder",
    "supernova",
    "blackhawk",
    "champion",
)

DETAILED_MW3_MECHS = (
    "strider",
    "avatar",
    "owens",
    "firefly",
)

ALL_MECHS = REPLACEMENT_MECHS + DETAILED_MW3_MECHS

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
    "footpad": {
        "height_amplitude": 0.06,
        "max_displacement": 0.06,
        "height_reference": 0.5,
        "roughness": 0.80,
        "reflectivity": 0.04,
        "metallic": 0.05,
    },
    "collar": {
        "height_amplitude": 0.05,
        "max_displacement": 0.05,
        "height_reference": 0.5,
        "roughness": 0.50,
        "reflectivity": 0.10,
        "metallic": 0.40,
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


def get_mech_material_profile(mat_name: str) -> dict[str, float]:
    """Resolve calibrated PBR parameters for a mech material name."""
    clean_key = mat_name.lower()
    if clean_key in MECH_MATERIAL_PROFILES:
        return MECH_MATERIAL_PROFILES[clean_key].copy()
    if any(k in clean_key for k in ("window", "glazing", "optical", "glass")):
        return MECH_MATERIAL_PROFILES["window"].copy()
    if any(k in clean_key for k in ("weapon", "weap", "constant", "gun")):
        return MECH_MATERIAL_PROFILES["weapons"].copy()
    if "missile" in clean_key:
        return MECH_MATERIAL_PROFILES["missilehead"].copy()
    if "footpad" in clean_key:
        return MECH_MATERIAL_PROFILES["footpad"].copy()
    if "collar" in clean_key:
        return MECH_MATERIAL_PROFILES["collar"].copy()
    return MECH_MATERIAL_PROFILES["default"].copy()


def unpack_bwnrm2(data: bytes) -> tuple[list[int], dict[str, tuple[int, int, int, bytes]]]:
    """Unpack BWNRM2/BWNRM3 normal sidecar into (batch_indices, images)."""
    if not (data.startswith(b"BWNRM2\0\0") or data.startswith(b"BWNRM3\0\0")):
        raise ValueError("Invalid normal map sidecar magic")
    compressed = data.startswith(b"BWNRM3\0\0")
    stream = io.BytesIO(data[8:])

    def take(size):
        raw = stream.read(size)
        if len(raw) != size:
            raise ValueError("Truncated normal map sidecar")
        return raw

    batch_count, image_count = struct.unpack("<II", take(8))
    if not 1 <= batch_count <= 256 or image_count > 64:
        raise ValueError("Invalid normal map counts")
    batches = list(struct.unpack(f"<{batch_count}I", take(batch_count * 4)))
    images = {}
    decoded_bytes = 0
    for _ in range(image_count):
        raw_name = take(32)
        if not raw_name[0] or raw_name[-1]:
            raise ValueError("Invalid normal map name")
        name = raw_name.split(b"\0")[0].decode("ascii")
        if name in images:
            raise ValueError("Duplicate normal map name")
        w, h, phash = struct.unpack("<IIQ", take(16))
        span = w * h * 4
        decoded_bytes += span
        if not 1 <= w <= 4096 or not 1 <= h <= 4096 or decoded_bytes > 256 * 1024**2:
            raise ValueError("Invalid normal map dimensions or byte budget")
        if compressed:
            encoded_size = struct.unpack("<Q", take(8))[0]
            if not 0 < encoded_size <= w * h * 8:
                raise ValueError("Invalid compressed normal map size")
            pixels = decode_normals(take(encoded_size), span)
        else:
            pixels = take(span)
        if uncached_pixel_hash(pixels) != phash:
            raise ValueError("Normal map pixel hash mismatch")
        images[name] = (w, h, phash, pixels)
    if any(index != 0xFFFFFFFF and index >= image_count for index in batches):
        raise ValueError("Invalid normal map batch binding")
    if stream.read(1):
        raise ValueError("Trailing normal map data")
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
    """Locate the mesh, normals, and textures payload files for any mech."""
    candidate_roots = []
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        candidate_roots.append(
            Path(localappdata)
            / "Packages/OpenAI.Codex_2p2nqsd0c76g0/LocalCache/Local/MW3Remaster/mods/com.mw3remaster.mw5-mechs"
        )
    candidate_roots.append(ROOT / "local/work-ahead/combined-model-pack-20261024-r1")
    candidate_roots.append(ROOT / "local/remaster")

    def resolve_path(p_str: str | None, base: Path) -> Path | None:
        if not p_str:
            return None
        p = Path(p_str)
        if p.is_absolute() and p.exists():
            return p
        if (base / p_str).exists():
            return base / p_str
        if (base.parent / p_str).exists():
            return base.parent / p_str
        if (ROOT / p_str).exists():
            return ROOT / p_str
        return None

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

                norm_path = resolve_path(env.get(norm_key), root)
                tex_path = resolve_path(env.get(tex_key), root)
                mesh_path = resolve_path(env.get(mesh_key), root) if mesh_key else None

                if norm_path and norm_path.exists() and tex_path and tex_path.exists():
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
    donor = magic == b"BWMESH4\0"
    anchored = magic == b"BWMESH6\0"
    layered = anchored or magic == b"BWMESH5\0"
    placement = layered or magic == b"BWMESH3\0"
    visibility = donor or placement or magic == b"BWMESH2\0"
    if not visibility and magic != b"BWMESH1\0":
        raise ValueError(f"Unsupported mesh payload format {magic!r}")

    count = struct.unpack("<I", stream.read(4))[0]
    if donor:
        bones, refs, _flags = struct.unpack("<III", stream.read(12))
        stream.read(40)  # 5 float64 gait parameters
        for _ in range(bones):
            stream.read(32 + 32 + 4 + 128)
        for _ in range(refs):
            stream.read(32 + 128)

    mat_verts: dict[str, bytearray] = {}
    all_xyz: list[tuple[float, float, float]] = []
    for i in range(count):
        stream.read(32)  # owner
        if visibility:
            stream.read(32)  # visibility
        if placement:
            stream.read(44)  # placement
        if layered:
            stream.read(44)  # layered
        if anchored:
            stream.read(44)  # anchored
        donor_bone = 0
        if donor:
            donor_bone = struct.unpack("<I", stream.read(4))[0]
        vc, _col = struct.unpack("<II", stream.read(8))
        vbytes = stream.read(vc * 32)
        if donor and donor_bone == 0xFFFFFFFF:
            stream.read(vc * 4)

        mat = mats[i]
        if mat not in mat_verts:
            mat_verts[mat] = bytearray()
        mat_verts[mat].extend(vbytes)
        stride = max(1, vc // 20)
        for j in range(0, vc, stride):
            all_xyz.append(struct.unpack("<fff", vbytes[j * 32 : j * 32 + 12]))

    if not all_xyz:
        all_xyz = [(0.0, 0.0, 0.0)]

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

    if not resources.get("mesh") or not resources["mesh"].is_file():
        raise ValueError("A mesh payload is required for verified surface-material compatibility")
    mesh_uv_hash = mesh_uv_identity_file(resources["mesh"])

    normal_names = list(n_images)
    if len(_n_batches) != len(batch_materials):
        raise ValueError("Normal and albedo batch counts differ")
    for material, index in zip(batch_materials, _n_batches):
        if index != 0xFFFFFFFF and normal_names[index] != material:
            raise ValueError("Normal and albedo material bindings differ")

    records = []
    images = {}
    quality_summary = {}
    visual_entries = []

    # Process all unique materials present on the mech
    unique_materials = list(dict.fromkeys(batch_materials))

    for mat_name in unique_materials:
        clean_key = mat_name.lower()
        prof = get_mech_material_profile(mat_name)
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
                stride = max(math.ceil(nw / max_dimension), math.ceil(nh / max_dimension))
                if stride > 1:
                    arr = np.frombuffer(normal_bytes, dtype=np.uint8).reshape(nh, nw, 4)
                    arr = arr[::stride, ::stride].copy()
                    nh, nw = arr.shape[:2]
                    normal_bytes = arr.tobytes()

            if prof["height_amplitude"] == 0.0:
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
            c_stride = max(math.ceil(color_w / max_dimension), math.ceil(color_h / max_dimension))
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
    parser.add_argument(
        "--mech",
        required=True,
        choices=list(ALL_MECHS) + ["all", "heroes", "replacements", "detailed"],
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--html-report", type=Path)
    parser.add_argument("--contact-sheets-dir", type=Path)
    parser.add_argument("--max-dimension", type=int, default=2048)

    args = parser.parse_args()

    if args.mech == "all":
        targets = list(ALL_MECHS)
    elif args.mech == "heroes":
        targets = list(HERO_MECHS)
    elif args.mech == "replacements":
        targets = list(REPLACEMENT_MECHS)
    elif args.mech == "detailed":
        targets = list(DETAILED_MW3_MECHS)
    else:
        targets = [args.mech]

    multi = len(targets) > 1

    for mech_id in targets:
        print(f"\n[{mech_id.upper()}] Building surface materials...")
        html_out = args.html_report
        if html_out and multi:
            html_out = html_out.parent / f"{mech_id}_{html_out.name}"

        sidecar_bytes, summary = build_mech_surface_materials(
            mech_id=mech_id,
            max_dimension=args.max_dimension,
            html_report_path=html_out,
            contact_sheets_dir=args.contact_sheets_dir,
        )

        out_path = args.output
        if out_path:
            if multi:
                out_path = out_path.parent / f"{mech_id}_{out_path.name}"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(sidecar_bytes)
            print(f"Wrote {len(sidecar_bytes):,} bytes BWSFM1 to {out_path}")

        print(
            f"Processed {summary['records_count']} materials across "
            f"{summary['batches_count']} batches. UV Hash: {summary['mesh_uv_hash']}"
        )
        if html_out:
            print(f"Generated HTML inspection report: {html_out}")


if __name__ == "__main__":
    main()
