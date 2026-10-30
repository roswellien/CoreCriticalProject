"""Prepare a local, portable chassis project from user-supplied MW3/PM resources.

Mech3AX is an author-side dependency, never a runtime or pack executable. Source
archives stay read-only. The project retains the selected chassis's three model
hierarchies, named motions and primary configuration. Other configurations and
skin variants are deliberately outside this first authoring pass.
"""

import argparse
import hashlib
import json
import re
import struct
import subprocess
import zipfile
from pathlib import Path

from legacy_chassis_resources import image_members, members
from zrd_document import decode, encode


def source_members(path, game_kind="mw"):
    data = path.read_bytes()
    if len(data) < 12:
        raise ValueError("Truncated source archive")
    if game_kind == "pm":
        if struct.unpack_from("<I", data, len(data) - 12)[0] != 2:
            raise ValueError("Unsupported PM archive footer")
        # PM's additional footer word is retained in provenance. Reconstruct only
        # the directory view for offline extraction, never a playable PM bank.
        data = data[:-12] + struct.pack("<II", 1, struct.unpack_from("<I", data, len(data) - 8)[0])
    return members(data)


def field(items, name):
    if not isinstance(items, list) or items.count(name) != 1:
        raise ValueError("Missing or repeated source field: " + name)
    return items[items.index(name) + 1]


def strings(tree):
    if isinstance(tree, list):
        for value in tree:
            yield from strings(value)
    elif isinstance(tree, str):
        yield tree


def prepare(game, game_kind, resource, converter, output, pack_id, name, metadata_template):
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,15}", resource):
        raise ValueError("Invalid source chassis resource")
    if game_kind not in ("mw", "pm"):
        raise ValueError("Unsupported source game")
    game, converter, output = (
        Path(game).resolve(),
        Path(converter).resolve(),
        Path(output).resolve(),
    )
    if output.is_relative_to(game):
        raise ValueError("Authoring output must be outside the original installation")
    output.mkdir(parents=True, exist_ok=False)
    work = output / "conversion"
    project = output / "project"
    work.mkdir()
    project.mkdir()
    provenance = {"source_game": game_kind, "resource": resource, "inputs": {}, "commands": []}

    def remember(path):
        provenance["inputs"][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()

    def run(tool, arguments, log):
        executable = converter / (tool + ".exe")
        remember(executable)
        command = [str(executable), *map(str, arguments)]
        with (work / log).open("w", encoding="utf-8") as stream:
            subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True)
        provenance["commands"].append(command)

    for kind in ("mechlib", "motion"):
        source = game / "zbd" / (kind + ".zbd")
        remember(source)
        run("unzbd", [game_kind, kind, source, work / (kind + ".zip")], kind + "-read.log")
    names = ["mech_" + resource + suffix + ".flt" for suffix in ("", "_1", "_hud")]
    with zipfile.ZipFile(work / "mechlib.zip") as source:
        models = {key: json.loads(source.read(key + ".json")) for key in names}
        all_materials = json.loads(source.read("materials.json"))
        used = sorted(
            {
                binding["material_index"]
                for model in models.values()
                for mesh in model["models"]
                for polygon in mesh["polygons"]
                for binding in polygon["materials"]
            }
        )
        indices = {old: new for new, old in enumerate(used)}
        selected_materials = [all_materials[index] for index in used]
        for model in models.values():
            for mesh in model["models"]:
                for polygon in mesh["polygons"]:
                    for binding in polygon["materials"]:
                        binding["material_index"] = indices[binding["material_index"]]
        manifest = [
            row
            for row in json.loads(source.read("manifest.json"))
            if row["name"] in {"version", "format", "materials", *names}
        ]
        with zipfile.ZipFile(work / "selected-models.zip", "w") as target:
            target.writestr("manifest.json", json.dumps(manifest))
            target.writestr("materials.json", json.dumps(selected_materials))
            for key, model in models.items():
                target.writestr(key + ".json", json.dumps(model))
    run(
        "rezbd",
        ["mw", "mechlib", work / "selected-models.zip", work / "models-mw.zbd"],
        "models-write.log",
    )
    run("rezbd", ["mw", "motion", work / "motion.zip", work / "motion-mw.zbd"], "motion-write.log")
    model_data = source_members(work / "models-mw.zbd")
    motion_data = {
        key: value
        for key, value in source_members(work / "motion-mw.zbd").items()
        if key.startswith(resource + "_")
    }
    reader_path = game / "zbd/reader.zbd"
    remember(reader_path)
    reader = source_members(reader_path, game_kind)
    definition = decode(reader["dfn_" + resource + ".zrd"])
    body = definition[0]
    configurations = field(body, "configurations")
    body[body.index("configurations") + 1] = [
        "MSG_CONFIG_PRIMARY",
        field(configurations, "MSG_CONFIG_PRIMARY"),
    ]
    skins = field(body, "skins")
    primary = ["MSG_SKIN_PRIMARY", field(skins, "MSG_SKIN_PRIMARY")]
    if "damage" in skins:
        primary.extend(["damage", field(skins, "damage")])
    body[body.index("skins") + 1] = primary
    textures = {}
    texture_path = game / "zbd/rmechtex.zbd"
    remember(texture_path)
    texture_bank = image_members(texture_path.read_bytes())
    required = {
        entry["Textured"]["texture_name"] for entry in selected_materials if "Textured" in entry
    }
    required.update(value for value in strings(primary) if value in texture_bank)
    for texture in sorted(required):
        if texture not in texture_bank:
            shared_path = game / "zbd/c1/rtexture.zbd"
            remember(shared_path)
            texture_bank.update(image_members(shared_path.read_bytes()))
        if texture not in texture_bank:
            raise ValueError("Missing source texture: " + texture)
        textures[texture] = texture_bank[texture][0]

    icon_path = game / "zbd/rimage.zbd"
    remember(icon_path)
    icon = image_members(icon_path.read_bytes())["icon_" + resource + "_green"][0]
    if struct.unpack_from("<IHHIHH", icon) != (3, 41, 50, 0, 0, 0) or len(icon) != 4116:
        raise ValueError("Unsupported source chassis silhouette")
    from chassis_icons import MAGIC

    # Recover the green channel's mask. Ceiling preserves its six-bit value when
    # the normal icon composer quantizes the mask back to RGB565.
    pixels = bytes(
        (((word >> 5) & 63) * 255 + 62) // 63 for (word,) in struct.iter_unpack("<H", icon[16:])
    )
    silhouette = MAGIC + struct.pack("<II", 41, 50) + pixels

    def write(relative, data):
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return relative

    descriptor = {
        "schema_version": 1,
        "resource": resource,
        "definition": write("definition.zrd", encode(definition)),
        "materials": write("materials.bin", model_data["materials"]),
        "silhouette": write("silhouette.bin", silhouette),
        "models": {
            role: write(role + ".bin", model_data[key])
            for role, key in zip(("close", "distance", "cockpit"), names)
        },
        "motions": {
            key: write("motions/" + key + ".bin", value) for key, value in motion_data.items()
        },
        "animations": {},
        "textures": {
            key: write("textures/" + key + ".bin", value) for key, value in textures.items()
        },
    }
    for member in ("anim_" + resource + ".zrd", resource + "_prints.zrd"):
        descriptor["animations"][member] = write("animations/" + member, reader[member])
    write("resources.json", (json.dumps(descriptor, indent=2) + "\n").encode())
    authored_project = {
        "pack_id": pack_id,
        "name": name + " - Additional Chassis",
        "version": "0.1.0-preview",
        "author": "Local author",
        "description": "Local legacy chassis conversion candidate. Primary configuration and skin; native compatibility requires validation.",
        "chassis": [
            {
                "id": "mech",
                "name": name,
                "metadata_template": metadata_template,
                "legacy": "resources.json",
            }
        ],
    }
    write("project.json", (json.dumps(authored_project, indent=2) + "\n").encode())
    for path, expected in provenance["inputs"].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError("Source changed during authoring: " + path)
    (output / "provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    return project / "project.json"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--source-game", choices=("mw", "pm"), required=True)
    parser.add_argument("--resource", required=True)
    parser.add_argument("--converter-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--pack-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--metadata-template", required=True)
    args = parser.parse_args()
    print(
        prepare(
            args.game_root,
            args.source_game,
            args.resource,
            args.converter_dir,
            args.output,
            args.pack_id,
            args.name,
            args.metadata_template,
        )
    )
