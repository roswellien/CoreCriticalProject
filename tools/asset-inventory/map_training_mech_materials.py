#!/usr/bin/env python3
"""Map Training mech model polygons to mechlib materials and rmechtex names.

This read-only parser follows the MW3 mechlib archive, material, node, mesh,
and polygon layouts documented by TerranMechworks' mech3doc project. Generated
reports are restricted to the repository's ignored local/ directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import struct


ROOT = pathlib.Path(__file__).resolve().parents[2]
EXPECTED_MODELS = (
    "mech_bushwacker.flt",
    "mech_bushwacker_1.flt",
    "mech_firefly.flt",
    "mech_firefly_1.flt",
)
FORMAT_REFERENCE = "https://terranmechworks.com/mech3doc/mechlib-archives.html"


def read_archive(path: pathlib.Path) -> tuple[bytes, dict[str, bytes]]:
    data = path.read_bytes()
    version, count = struct.unpack_from("<II", data, len(data) - 8)
    if version != 1 or count > 10000:
        raise ValueError("unsupported or implausible MW3 archive footer")
    toc = len(data) - 8 - count * 148
    if toc < 0:
        raise ValueError("archive TOC falls outside the input")
    entries: dict[str, bytes] = {}
    for index in range(count):
        record = data[toc + index * 148 : toc + (index + 1) * 148]
        start, length = struct.unpack_from("<II", record)
        name = record[8:72].split(b"\0", 1)[0].decode("ascii")
        if start + length > toc:
            raise ValueError(f"archive entry {name!r} exceeds the TOC boundary")
        entries[name] = data[start : start + length]
    return data, entries


def read_materials(data: bytes) -> list[dict]:
    version, count = struct.unpack_from("<II", data, len(data) - 8)
    toc = len(data) - 8 - count * 148
    material_blob = None
    for index in range(count):
        record = data[toc + index * 148 : toc + (index + 1) * 148]
        start, length = struct.unpack_from("<II", record)
        name = record[8:72].split(b"\0", 1)[0]
        if name == b"materials":
            material_blob = data[start : start + length]
            break
    if material_blob is None or len(material_blob) < 4:
        raise ValueError("mechlib materials entry is missing")
    material_count = struct.unpack_from("<I", material_blob)[0]
    pos = 4
    materials = []
    for index in range(material_count):
        if pos + 40 > len(material_blob):
            raise ValueError(f"truncated material record {index}")
        flags = material_blob[pos + 1]
        pos += 40
        name = None
        if flags & 1:
            if pos + 4 > len(material_blob):
                raise ValueError(f"missing texture-name length for material {index}")
            length = struct.unpack_from("<I", material_blob, pos)[0]
            pos += 4
            if length > 256 or pos + length > len(material_blob):
                raise ValueError(f"invalid texture-name length for material {index}")
            name = material_blob[pos : pos + length].decode("ascii")
            pos += length
        materials.append({"index": index, "textured": bool(flags & 1), "texture_name": name})
    if pos != len(material_blob):
        raise ValueError(f"materials entry has {len(material_blob) - pos} unparsed bytes")
    return materials


def parse_model(name: str, data: bytes, materials: list[dict]) -> dict:
    pos = 0
    nodes = []
    material_polygon_counts: dict[int, int] = {}
    while pos + 352 <= len(data):
        start = pos
        node_name = data[pos : pos + 36].split(b"\0", 1)[0].decode("ascii", "replace")
        flags = struct.unpack_from("<I", data, pos + 36)[0]
        node_type = struct.unpack_from("<I", data, pos + 52)[0]
        mesh_pointer = struct.unpack_from("<I", data, pos + 60)[0]
        if node_type != 5:
            raise ValueError(f"{name}: unexpected node type {node_type} at {pos}")
        if bool(flags & 0x200) != bool(mesh_pointer):
            raise ValueError(f"{name}: HasMesh flag/pointer mismatch at {pos}")
        pos += 352  # 208-byte node base and 144-byte Object3d data
        material_counts: dict[int, int] = {}
        polygon_count = 0
        if flags & 0x200:
            if pos + 92 > len(data):
                raise ValueError(f"{name}: truncated mesh header at {pos}")
            fields = struct.unpack_from("<23I", data, pos)
            polygon_count, vertex_count, normal_count, morph_count, light_count = fields[4:9]
            counts = (polygon_count, vertex_count, normal_count, morph_count, light_count)
            if any(value > 100000 for value in counts):
                raise ValueError(f"{name}: implausible mesh counts at {pos}: {counts}")
            q = pos + 92 + 12 * (vertex_count + normal_count + morph_count)
            if q > len(data):
                raise ValueError(f"{name}: mesh vectors exceed model boundary")
            light_extras = []
            for light_index in range(light_count):
                light_pos = q + light_index * 76
                if light_pos + 76 > len(data):
                    raise ValueError(f"{name}: truncated light data")
                extra_count = struct.unpack_from("<I", data, light_pos + 12)[0]
                if extra_count > 100000:
                    raise ValueError(f"{name}: implausible light extra count")
                light_extras.append(extra_count)
            q += 76 * light_count + 12 * sum(light_extras)
            polygon_infos = []
            for polygon in range(polygon_count):
                poly_pos = q + polygon * 36
                if poly_pos + 36 > len(data):
                    raise ValueError(f"{name}: truncated polygon table")
                polygon_infos.append(struct.unpack_from("<9I", data, poly_pos))
            q += 36 * polygon_count
            for info in polygon_infos:
                vertex_info = info[0]
                vertices = vertex_info & 0xFF
                material_index = info[7]
                if vertices < 3 or material_index >= len(materials):
                    raise ValueError(f"{name}: invalid polygon/material index")
                q += 4 * vertices
                if vertex_info & 0x200:
                    q += 4 * vertices
                if info[4]:  # UV pointer present
                    q += 8 * vertices
                q += 12 * vertices  # vertex colors
                material_counts[material_index] = material_counts.get(material_index, 0) + 1
            if q > len(data):
                raise ValueError(f"{name}: polygon data exceeds model boundary")
            pos = q
        for material_index, count in material_counts.items():
            material_polygon_counts[material_index] = material_polygon_counts.get(material_index, 0) + count
        nodes.append(
            {
                "name": node_name,
                "offset": start,
                "has_mesh": bool(flags & 0x200),
                "polygon_count": polygon_count,
                "material_polygon_counts": material_counts,
            }
        )
        if len(nodes) > 10000:
            raise ValueError(f"{name}: node limit exceeded")
    if pos != len(data):
        raise ValueError(f"{name}: {len(data) - pos} trailing or unparsed bytes at {pos}")
    used = []
    for material_index, count in sorted(material_polygon_counts.items()):
        material = materials[material_index]
        used.append({**material, "polygon_count": count})
    return {
        "model": name,
        "model_sha256": hashlib.sha256(data).hexdigest(),
        "node_count": len(nodes),
        "mesh_node_count": sum(node["has_mesh"] for node in nodes),
        "polygon_count": sum(material_polygon_counts.values()),
        "materials": used,
        "nodes": nodes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=pathlib.Path, nargs="?", default=ROOT / "MW3/zbd/mechlib.zbd")
    parser.add_argument("--probe", type=pathlib.Path, default=ROOT / "local/work-ahead/rmechtex-probe.json")
    parser.add_argument("--output", type=pathlib.Path, default=ROOT / "local/work-ahead/training-mech-textures-v1/mechlib-model-material-usage.json")
    args = parser.parse_args()
    archive_path = args.archive.resolve()
    output_path = args.output.resolve()
    local_root = (ROOT / "local").resolve()
    if not output_path.is_relative_to(local_root):
        raise SystemExit("output must be under the repository's local/ directory")
    raw, entries = read_archive(archive_path)
    materials = read_materials(raw)
    probe = json.loads(args.probe.read_text(encoding="utf-8"))
    texture_indices = {item["name"]: item["index"] for item in probe["entries"]}
    models = []
    for name in EXPECTED_MODELS:
        if name not in entries:
            raise SystemExit(f"missing expected model: {name}")
        models.append(parse_model(name, entries[name], materials))
    by_index = {item["index"]: item for item in materials}
    union = {}
    for model in models:
        for material in model["materials"]:
            index = material["index"]
            record = union.setdefault(index, {**by_index[index], "models": [], "polygon_count": 0})
            record["models"].append(model["model"])
            record["polygon_count"] += material["polygon_count"]
    for item in union.values():
        if item["texture_name"] is not None:
            item["rmechtex_index"] = texture_indices.get(item["texture_name"])
    report = {
        "schema_version": 1,
        "status": "model polygon material references parsed and boundary-validated",
        "source_archive": str(archive_path.relative_to(ROOT)),
        "source_archive_sha256": hashlib.sha256(raw).hexdigest(),
        "format_reference": FORMAT_REFERENCE,
        "texture_probe_sha256": hashlib.sha256(args.probe.read_bytes()).hexdigest(),
        "model_count": len(models),
        "models": models,
        "used_material_union": sorted(union.values(), key=lambda item: item["index"]),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output_path),
        "models": [{"model": m["model"], "nodes": m["node_count"], "meshes": m["mesh_node_count"], "polygons": m["polygon_count"]} for m in models],
        "unique_materials_used": len(union),
        "textured_materials_used": sum(item["texture_name"] is not None for item in union.values()),
        "unresolved_texture_indices": [item["texture_name"] for item in union.values() if item["texture_name"] and item.get("rmechtex_index") is None],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
