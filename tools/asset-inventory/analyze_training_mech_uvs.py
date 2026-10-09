#!/usr/bin/env python3
"""Extract and summarize Training mech polygon UVs by mesh and material.

Reads the local mechlib archive using the bounded layout already validated by
map_training_mech_materials.py. It writes a report only under local/.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import pathlib
import struct
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2]
PARSER_PATH = pathlib.Path(__file__).with_name("map_training_mech_materials.py")
spec = importlib.util.spec_from_file_location("training_mech_parser", PARSER_PATH)
parser_module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(parser_module)


def parse_model_uvs(name: str, data: bytes, materials: list[dict]) -> list[dict]:
    pos = 0
    by_mesh_material: dict[tuple[str, int], dict] = {}
    while pos + 352 <= len(data):
        node_name = data[pos : pos + 36].split(b"\0", 1)[0].decode("ascii", "replace")
        flags = struct.unpack_from("<I", data, pos + 36)[0]
        node_type = struct.unpack_from("<I", data, pos + 52)[0]
        if node_type != 5:
            raise ValueError(f"{name}: unexpected node type {node_type} at {pos}")
        pos += 352
        if not (flags & 0x200):
            continue
        if pos + 92 > len(data):
            raise ValueError(f"{name}: truncated mesh header")
        fields = struct.unpack_from("<23I", data, pos)
        polygon_count, vertex_count, normal_count, morph_count, light_count = fields[4:9]
        counts = (polygon_count, vertex_count, normal_count, morph_count, light_count)
        if any(value > 100000 for value in counts):
            raise ValueError(f"{name}: implausible mesh counts {counts}")
        q = pos + 92
        q += 12 * (vertex_count + normal_count + morph_count)
        light_extras = []
        for index in range(light_count):
            light_pos = q + index * 76
            if light_pos + 76 > len(data):
                raise ValueError(f"{name}: truncated light data")
            extra_count = struct.unpack_from("<I", data, light_pos + 12)[0]
            if extra_count > 100000:
                raise ValueError(f"{name}: implausible light extra count")
            light_extras.append(extra_count)
        q += 76 * light_count + 12 * sum(light_extras)
        polygon_infos = []
        for index in range(polygon_count):
            at = q + index * 36
            if at + 36 > len(data):
                raise ValueError(f"{name}: truncated polygon table")
            polygon_infos.append(struct.unpack_from("<9I", data, at))
        q += 36 * polygon_count
        for info in polygon_infos:
            vertex_info = info[0]
            count = vertex_info & 0xFF
            material_index = info[7]
            if count < 3 or material_index >= len(materials):
                raise ValueError(f"{name}: invalid polygon/material index")
            vertices_bytes = 4 * count
            if q + vertices_bytes > len(data):
                raise ValueError(f"{name}: vertex indices exceed model boundary")
            vertex_indices = struct.unpack_from(f"<{count}I", data, q)
            if any(index >= vertex_count for index in vertex_indices):
                raise ValueError(f"{name}: vertex index exceeds mesh vertex count")
            q += vertices_bytes
            if vertex_info & 0x200:
                if q + vertices_bytes > len(data):
                    raise ValueError(f"{name}: normal indices exceed model boundary")
                normal_indices = struct.unpack_from(f"<{count}I", data, q)
                if any(index >= normal_count for index in normal_indices):
                    raise ValueError(f"{name}: normal index exceeds mesh normal count")
                q += vertices_bytes
            has_uvs = bool(info[4])
            coords = []
            if has_uvs:
                uv_bytes = 8 * count
                if q + uv_bytes > len(data):
                    raise ValueError(f"{name}: UV data exceeds model boundary")
                coords = list(struct.unpack_from(f"<{count * 2}f", data, q))
                if any(not math.isfinite(value) for value in coords):
                    raise ValueError(f"{name}: non-finite UV coordinate")
                q += uv_bytes
            color_bytes = 12 * count
            if q + color_bytes > len(data):
                raise ValueError(f"{name}: vertex colors exceed model boundary")
            q += color_bytes
            if has_uvs:
                key = (node_name, material_index)
                stats = by_mesh_material.setdefault(key, {
                    "model": name,
                    "mesh_node": node_name,
                    "material_index": material_index,
                    "texture_name": materials[material_index]["texture_name"],
                    "uv_polygons": 0,
                    "uv_vertices": 0,
                    "u_min": float("inf"), "u_max": float("-inf"),
                    "v_min": float("inf"), "v_max": float("-inf"),
                    "uvs_outside_0_1": 0,
                })
                u_values, v_values = coords[0::2], coords[1::2]
                stats["uv_polygons"] += 1
                stats["uv_vertices"] += count
                stats["u_min"] = min(stats["u_min"], min(u_values))
                stats["u_max"] = max(stats["u_max"], max(u_values))
                stats["v_min"] = min(stats["v_min"], min(v_values))
                stats["v_max"] = max(stats["v_max"], max(v_values))
                stats["uvs_outside_0_1"] += sum(not (0.0 <= x <= 1.0) for x in coords)
        if q > len(data):
            raise ValueError(f"{name}: mesh data exceeds model boundary")
        pos = q
    if pos != len(data):
        raise ValueError(f"{name}: {len(data) - pos} unparsed trailing bytes")
    return list(by_mesh_material.values())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("archive", type=pathlib.Path, nargs="?", default=ROOT / "MW3/zbd/mechlib.zbd")
    ap.add_argument("--output", type=pathlib.Path, default=ROOT / "local/work-ahead/training-mech-textures-v1/mechlib-model-uv-usage.json")
    args = ap.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / "local").resolve()):
        raise SystemExit("output must be under the repository's local/ directory")
    raw, entries = parser_module.read_archive(args.archive.resolve())
    materials = parser_module.read_materials(raw)
    model_names = parser_module.EXPECTED_MODELS
    groups = []
    for name in model_names:
        if name not in entries:
            raise SystemExit(f"missing expected model: {name}")
        groups.extend(parse_model_uvs(name, entries[name], materials))
    by_material: dict[int, dict] = {}
    for item in groups:
        index = item["material_index"]
        agg = by_material.setdefault(index, {
            "material_index": index,
            "texture_name": item["texture_name"],
            "mesh_records": 0,
            "uv_polygons": 0,
            "uv_vertices": 0,
            "u_min": float("inf"), "u_max": float("-inf"),
            "v_min": float("inf"), "v_max": float("-inf"),
            "uvs_outside_0_1": 0,
            "meshes": [],
        })
        agg["mesh_records"] += 1
        for key in ("uv_polygons", "uv_vertices", "uvs_outside_0_1"):
            agg[key] += item[key]
        for key in ("u_min", "v_min"):
            agg[key] = min(agg[key], item[key])
        for key in ("u_max", "v_max"):
            agg[key] = max(agg[key], item[key])
        agg["meshes"].append(item)
    usage_path = ROOT / "local/work-ahead/training-mech-textures-v1/mechlib-model-material-usage.json"
    usage = json.loads(usage_path.read_text(encoding="utf-8-sig"))
    model_used = {item["index"] for item in usage["used_material_union"]}
    uv_used = set(by_material)
    report = {
        "schema_version": 1,
        "status": "UV coordinates extracted and bounds-validated for textured mech polygons",
        "source_archive": str(args.archive.resolve().relative_to(ROOT)),
        "model_count": len(model_names),
        "materials_with_uvs": len(by_material),
        "used_textured_material_indices": sorted(index for index in model_used if materials[index]["textured"]),
        "used_textured_materials_without_uvs": sorted(index for index in model_used if materials[index]["textured"] and index not in uv_used),
        "unreferenced_material_indices_without_uvs": sorted(set(m["index"] for m in materials) - model_used),
        "materials": sorted(by_material.values(), key=lambda item: item["material_index"]),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "materials_with_uvs": report["materials_with_uvs"],
        "used_textured_materials_without_uvs": len(report["used_textured_materials_without_uvs"]),
        "uv_coordinates_outside_0_1": sum(m["uvs_outside_0_1"] for m in report["materials"]),
        "u_bounds": [min(m["u_min"] for m in report["materials"]), max(m["u_max"] for m in report["materials"])],
        "v_bounds": [min(m["v_min"] for m in report["materials"]), max(m["v_max"] for m in report["materials"])],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
