"""Rank local world material authoring by placed polygon use and surface area.

Reads previously decoded scenes; writes local metadata only. Counts are static
scene references, not measured visibility or mission play-time frequency.
"""

from pathlib import Path
from collections import defaultdict, Counter
import argparse
import hashlib
import json
import math
import re
import zipfile

REGIONS = ("t1", "c1", "c2", "c3", "c4", "c4b")
VEHICLE_ROOT = re.compile(
    r"^(veh_|mobile_?hq(?:\.flt)?$|mfbody$|ttruck$|bmtruck$|vtruck$|heli$|m5heli$|apc$|hulk_apc$)"
)
IMPACT = re.compile(
    r"cliff|mesa|rock|lava|^txwall|bridge|brg|factory|plant|plnt|port|bunk|build|hangar|door"
)


def sha(path):
    """Stream a decoded scene or inventory file's SHA-256 for the output record."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def polygon_area(vertices, polygon):
    """Sum triangle areas in squared model-local coordinate units.

    Triangle strips use consecutive triples; other polygons use a fan around
    the first vertex. Cross-product magnitude ignores winding. This estimates
    stored geometry area without applying node transforms or screen projection.
    """
    indices = polygon["vertex_indices"]
    if len(indices) < 3:
        return 0.0

    def xyz(i):
        return tuple(vertices[i][a] for a in ("x", "y", "z"))

    points = [xyz(i) for i in indices]
    triangles = (
        ((i - 2, i - 1, i) for i in range(2, len(points)))
        if polygon.get("flags", {}).get("tri_strip")
        else ((0, i - 1, i) for i in range(2, len(points)))
    )
    area = 0.0
    for a, b, c in triangles:
        u = [points[b][i] - points[a][i] for i in range(3)]
        v = [points[c][i] - points[a][i] for i in range(3)]
        cross = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        area += math.sqrt(sum(x * x for x in cross)) * 0.5
    if not math.isfinite(area):
        raise ValueError("Nonfinite scene geometry")
    return area


def rank(scenes, inventory, output, water_inventory):
    """Write a static authoring queue from the six configured decoded scene ZIPs.

    Repeated node placements, stored LODs and material layers each contribute
    references. Terrain-flagged and other nodes are ranked separately, so one
    texture can occur in both lanes. Both lanes must have eligible references.
    Names guide authoring selection; runtime binding still needs exact pixels.
    """
    output = Path(output)
    if output.exists():
        raise ValueError("Choose a fresh output directory")
    types = {x["name"]: x for x in json.loads(Path(inventory).read_text())["textures"]}
    rows = defaultdict(
        lambda: dict(
            terrain=0,
            objects=0,
            terrain_area=0.0,
            objects_area=0.0,
            vehicle=0,
            regions=set(),
            nodes=set(),
            vehicle_roots=set(),
        )
    )
    pins = []
    families = defaultdict(set)
    for region in REGIONS:
        path = Path(scenes) / (region + "-gamez.zip")
        pins.append(dict(region=region, sha256=sha(path)))
        with zipfile.ZipFile(path) as archive:
            nodes, models, materials, textures = [
                json.loads(archive.read(x + ".json"))
                for x in ("nodes", "models", "materials", "textures")
            ]
        # Retain every recognized root that reaches a node. The per-root visited
        # set tolerates repeated child references without counting a cycle twice.
        vehicle_nodes = defaultdict(set)
        for i, node in enumerate(nodes):
            if not VEHICLE_ROOT.search(node["name"].lower()):
                continue
            vehicle_root = node["name"].lower()
            stack = [i]
            seen = set()
            while stack:
                node_index = stack.pop()
                if node_index in seen:
                    continue
                if not 0 <= node_index < len(nodes):
                    raise ValueError("Invalid vehicle child index")
                seen.add(node_index)
                vehicle_nodes[node_index].add(vehicle_root)
                stack.extend(nodes[node_index].get("child_indices", []))
        for i, node in enumerate(nodes):
            model_index = node.get("model_index", -1)
            if model_index is None or model_index == -1:
                continue
            model = models[model_index]
            lane = "terrain" if node.get("flags", {}).get("terrain") else "objects"
            for polygon in model.get("polygons", []):
                area = polygon_area(model["vertices"], polygon)
                # Multiple material layers count separately, retaining their cost/use.
                for ref in polygon.get("materials", []):
                    material = materials[ref["material_index"]].get("Textured")
                    if not material:
                        continue
                    name = Path(textures[material["texture_index"]]["name"]).stem.lower()
                    row = rows[name]
                    row[lane] += 1
                    row[lane + "_area"] += area
                    row["regions"].add(region)
                    row["nodes"].add((region, i))
                    if i in vehicle_nodes:
                        row["vehicle"] += 1
                        row["vehicle_roots"].update(vehicle_nodes[i])
                        for vehicle_root in vehicle_nodes[i]:
                            families[vehicle_root].add(name)
    water = json.loads(Path(water_inventory).read_text())["groups"]
    dedicated = {
        n.lower()
        for group in ("water_surfaces", "surf_animation", "foam_and_splash")
        for n in water[group]
    }
    eligible = {
        n: r
        for n, r in rows.items()
        if n not in dedicated
        and n in types
        and types[n]["category"]
        not in ("sky_candidate", "effects_animation", "water_shore_candidate")
    }
    result = {}
    selections = defaultdict(set)
    for lane in ("terrain", "objects"):
        ordered = sorted(
            (n for n, r in eligible.items() if r[lane]),
            key=lambda n: (-eligible[n][lane], -len(eligible[n]["regions"]), n),
        )
        if not ordered:
            raise ValueError("No eligible " + lane + " material references; cannot rank coverage")
        # Frequency controls queue order. Area and landmark-name matches add
        # review candidates without changing that order or claiming visibility.
        frequency_quartile_count = math.ceil(len(ordered) * 0.25)
        area_rank = sorted(ordered, key=lambda n: (-eligible[n][lane + "_area"], n))
        area_priority = set(area_rank[: max(1, math.ceil(len(ordered) * 0.1))])
        result[lane] = []
        total_references = sum(eligible[n][lane] for n in ordered)
        for i, name in enumerate(ordered):
            row = eligible[name]
            reasons = []
            if i < frequency_quartile_count:
                reasons.append("top_quartile_reference_frequency")
            if name in area_priority:
                reasons.append("top_decile_static_surface_area")
            if IMPACT.search(name):
                reasons.append("landmark_material_candidate_requires_art_review")
            if reasons:
                selections[name].update(reasons)
            result[lane].append(
                dict(
                    name=name,
                    rank=i + 1,
                    polygon_material_references=row[lane],
                    local_surface_area=row[lane + "_area"],
                    regions=sorted(row["regions"]),
                    node_count=len(row["nodes"]),
                    reasons=reasons,
                )
            )
        result[lane + "_summary"] = dict(
            eligible_names=len(ordered),
            top_quartile_count=frequency_quartile_count,
            total_references=total_references,
            top_quartile_reference_coverage=sum(
                eligible[n][lane] for n in ordered[:frequency_quartile_count]
            )
            / total_references,
        )
    for name, row in eligible.items():
        if row["vehicle"]:
            selections[name].add("vehicle_all_materials")
    result["vehicle_families"] = {k: sorted(v) for k, v in sorted(families.items())}
    result["authoring_queue"] = [
        dict(
            name=n,
            reasons=sorted(v),
            vehicle_roots=sorted(eligible[n]["vehicle_roots"]),
            existing_category=types[n]["category"],
        )
        for n, v in sorted(selections.items())
    ]
    result["inputs"] = dict(
        scenes=pins,
        inventory_sha256=sha(Path(inventory)),
        water_inventory_sha256=sha(Path(water_inventory)),
    )
    result["dedicated_water_exclusions"] = sorted(dedicated)
    result["method"] = (
        "Placed node polygon-material reference count; separately ranked terrain-flag and other world nodes; repeated placements and stored LODs count. Local polygon area is an impact proxy, not projected screen area. No runtime visibility or mission-time weighting."
    )
    result["limits"] = [
        "Terrain flags also mark walls/structures; lanes overlap by texture name.",
        "Vehicle descendants use explicit root-name anchors; auxiliary effects remain excluded from opaque relief. Family completeness requires roster review.",
        "Water/sky/effects stay on dedicated paths.",
        "Distinct pixel/bank identities must retain separate normals even when names match.",
    ]
    output.mkdir(parents=True)
    (output / "priorities.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenes", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--water-inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = rank(args.scenes, args.inventory, args.output, args.water_inventory)
    print(
        json.dumps(
            {k: result[k] for k in ("terrain_summary", "objects_summary", "vehicle_families")},
            indent=2,
        )
    )
