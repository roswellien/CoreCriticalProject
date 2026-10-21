"""Create a campaign-first material queue from full-pixel world draw encounters.

The source trace records submission, not depth-visible pixels. Route and mission
order are explicit; neither scene serialization nor bank-load order substitutes.
"""

from pathlib import Path
import argparse
import csv
import hashlib
import json


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def build(config_path, output, limit=100):
    if limit < 1:
        raise ValueError("A positive campaign queue limit is required")
    if output.exists():
        raise ValueError("Choose a fresh campaign queue output")
    config = json.loads(config_path.read_text())
    inventory = {
        e["name"]: e for e in json.loads(Path(config["inventory"]).read_text())["textures"]
    }
    groups = json.loads(Path(config["water_inventory"]).read_text())["groups"]
    excluded = {
        n
        for group in ("water_surfaces", "surf_animation", "foam_and_splash")
        for n in groups[group]
    }
    index = {
        tuple(e["key"]): e for e in json.loads(Path(config["key_index"]).read_text())["bindings"]
    }
    with Path(config["previous_queue"]).open(encoding="utf-8", newline="") as stream:
        previous = {e["texture"]: e for e in csv.DictReader(stream)}
    sequence = []
    by_name = {}
    skipped = []
    pins = []
    last_mission = -1
    seen_missions = set()
    for run in config["runs"]:
        mission = run["mission"]
        mission_index = config["mission_order"].index(mission)
        if mission_index < last_mission or mission in seen_missions:
            raise ValueError("Campaign runs must be in unique progression order")
        last_mission = mission_index
        seen_missions.add(mission)
        path = Path(run["encounters"])
        pins.append(
            dict(
                mission=mission,
                trace_sha256=sha(path),
                route_sha256=sha(run["route"]),
                scope=run["scope"],
            )
        )
        last_sequence = 0
        last_frame = 0
        for line in path.read_text().splitlines():
            e = json.loads(line)
            if (
                e["event"] != "first_world_texture_submission"
                or e["sequence"] <= last_sequence
                or e["frame"] < last_frame
            ):
                raise ValueError("Encounter trace order invalid")
            last_sequence = e["sequence"]
            last_frame = e["frame"]
            key = (e["width"], e["height"], e["format"], e["hash"])
            if key not in index:
                raise ValueError("Unresolved texture blocks exact ordering: " + str(key))
            match = index[key]
            names = match["names"]
            categories = {inventory.get(n, {}).get("category") for n in names}
            reason = (
                "dedicated_water_surf"
                if excluded.intersection(names)
                else (
                    "sky_effect_or_water_candidate"
                    if categories.intersection(
                        {"sky_candidate", "effects_animation", "water_shore_candidate"}
                    )
                    else "unsupported_blended_material" if e["alpha_blend"] else None
                )
            )
            if reason:
                skipped.append(dict(mission=mission, frame=e["frame"], names=names, reason=reason))
                continue
            existing = {by_name[n] for n in names if n in by_name}
            if len(existing) > 1:
                raise ValueError(
                    "Pixel aliases join previously distinct queue families; review explicitly"
                )
            if existing:
                row = sequence[existing.pop()]
                if list(key) not in row["encountered_keys"]:
                    row["encountered_keys"].append(list(key))
                row["aliases"] = sorted(set(row["aliases"]) | set(names))
                for n in names:
                    by_name[n] = row["rank"] - 1
                continue
            row = dict(
                rank=len(sequence) + 1,
                texture=names[0],
                aliases=names,
                first_mission=mission,
                first_frame=e["frame"],
                submission_sequence=e["sequence"],
                first_key=list(key),
                encountered_keys=[list(key)],
                first_gpu_terrain=bool(e["terrain_gpu"]),
                alpha_test=bool(e["alpha_test"]),
                source_match=match["source"],
            )
            category = inventory.get(row["texture"], {}).get("category")
            row["lane"] = (
                "terrain_or_structure"
                if category == "terrain_marked_world_geometry"
                else "world_object" if category else "shared_or_original_mech_surface"
            )
            row["authoring_state"] = previous.get(row["texture"], {}).get(
                "authoring_state",
                "source/artwork review pending; newly encountered outside previous priority queue",
            )
            row["source_review"] = (
                "upgraded-world-catalog source pinned"
                if match["source"] == "world_catalog"
                else "installed bank matched; verify approved upgraded source before authoring"
            )
            if min(key[:2]) < 128:
                row["source_review"] += "; small tile requires detail review"
            sequence.append(row)
            for n in names:
                by_name[n] = len(sequence) - 1
    if len(sequence) < limit:
        raise ValueError(
            f"Only {len(sequence)} eligible families encountered; continue campaign capture, do not pad from bank order"
        )
    selected = sequence[:limit]
    report = dict(
        schema_version=1,
        scope="First distinct eligible terrain/world/object and original-mech surface families in this recorded campaign route; simultaneously submitted materials tie by draw sequence. Replacement mech maps already handled separately.",
        ordering="campaign mission order then first render submission, not pixel-depth visibility or asset load order",
        mission_order=config["mission_order"],
        limit=limit,
        eligible_encounter_groups=len(sequence),
        selected=selected,
        excluded=skipped,
        remaining_encounters=sequence[limit:],
        inputs=dict(
            config_sha256=sha(config_path), key_index_sha256=sha(config["key_index"]), runs=pins
        ),
        limits=[
            "A different camera route can encounter textures in a different order.",
            "A submitted surface may be occluded; GPU depth visibility is not measured.",
            "Same-name/different-pixel variants remain listed and require separate UV review.",
            "This queue does not prove all campaign states or vehicle LOD/damage appearances have been covered.",
        ],
    )
    output.mkdir(parents=True)
    (output / "queue.json").write_text(json.dumps(report, indent=2) + "\n")
    fields = [
        "rank",
        "texture",
        "aliases",
        "first_mission",
        "first_frame",
        "submission_sequence",
        "lane",
        "first_source_size",
        "source_review",
        "authoring_state",
    ]
    with (output / "first-100.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in selected:
            values = {k: row[k] for k in fields if k not in ("aliases", "first_source_size")}
            values["aliases"] = " | ".join(row["aliases"])
            values["first_source_size"] = "x".join(map(str, row["first_key"][:2]))
            writer.writerow(values)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    r = build(args.config, args.output, args.limit)
    print(
        json.dumps(
            dict(
                selected=len(r["selected"]),
                encountered=r["eligible_encounter_groups"],
                first=r["selected"][0]["texture"],
                last=r["selected"][-1]["texture"],
            ),
            indent=2,
        )
    )
