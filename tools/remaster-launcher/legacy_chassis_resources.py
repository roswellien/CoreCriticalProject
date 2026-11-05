"""Compose additional chassis using MW3-format model, motion and reader resources.

This data-only contract keeps a chassis's own hierarchy and motion clips. Authors
convert source formats offline; the receiving coordinator never runs converters.
Only owned additions and the materials/common-animation indexes are composed into
private banks. The original installation is read-only.
"""

import math
import re
import struct
from pathlib import Path

from reader_archive import _directory
from zrd_document import decode, encode

FORMAT = "MW3LEGACY"
VERSION = 3
ROLES = ("definition", "materials", "silhouette", "models", "motions", "animations", "textures")


def resource_paths(document):
    """Validate descriptor shape and yield every declared payload reference."""
    expected = {"schema_version", "resource", *ROLES}
    if isinstance(document, dict) and document.get("schema_version") == 2:
        from legacy_chassis_skins import metadata

        expected.add("skins")
        metadata(document.get("skins"))
    if not isinstance(document, dict) or set(document) != expected:
        raise ValueError("Invalid legacy chassis descriptor fields")
    resource = document["resource"]
    if (
        type(document["schema_version"]) is not int
        or document["schema_version"] not in (1, 2)
        or not isinstance(resource, str)
        or not re.fullmatch(r"[a-z][a-z0-9_]{0,15}", resource)
    ):
        raise ValueError("Invalid legacy chassis resource/version")
    for role in ("definition", "materials", "silhouette"):
        if not isinstance(document[role], str):
            raise ValueError("Invalid legacy chassis payload path")
        yield role, None, document[role]
    for role, limit in (("models", 3), ("motions", 64), ("animations", 16), ("textures", 512)):
        table = document[role]
        if not isinstance(table, dict) or not 1 <= len(table) <= limit:
            raise ValueError("Invalid legacy chassis " + role)
        if role == "models" and set(table) != {"close", "distance", "cockpit"}:
            raise ValueError("Legacy chassis requires both LODs and cockpit")
        for name, path in table.items():
            if (
                not isinstance(name, str)
                or not re.fullmatch(r"[a-zA-Z0-9_.-]{1,31}", name)
                or not isinstance(path, str)
            ):
                raise ValueError("Invalid legacy chassis resource name/path")
            yield role, name, path


def materials(data):
    """Return bounded v27 material records and their optional texture names."""
    if len(data) < 4:
        raise ValueError("Truncated legacy materials")
    count = struct.unpack_from("<I", data)[0]
    if not 1 <= count <= 10000:
        raise ValueError("Invalid legacy material count")
    result, position = [], 4
    for _ in range(count):
        start = position
        if position + 40 > len(data):
            raise ValueError("Truncated legacy material record")
        textured = data[position + 1] & 1
        position += 40
        name = None
        if textured:
            if position + 4 > len(data):
                raise ValueError("Truncated legacy texture name")
            length = struct.unpack_from("<I", data, position)[0]
            position += 4
            if not 1 <= length <= 31 or position + length > len(data):
                raise ValueError("Invalid legacy texture name length")
            name = data[position : position + length].decode("ascii")
            if not re.fullmatch(r"[a-zA-Z0-9_.-]+", name):
                raise ValueError("Invalid legacy material texture name")
            position += length
        result.append((data[start:position], name))
    if position != len(data):
        raise ValueError("Trailing legacy material data")
    return result


def model(data, material_count, material_offset=0, names=None, nodes=None):
    """Check MW3 Object3d/mesh spans and relocate only material/name references.

    The 352-byte node, 92-byte mesh and 36-byte polygon layouts match the existing
    asset-inventory parser. PM bytes must first be written with the MW converter.
    """
    output = bytearray(data)
    position, node_count = 0, 0
    while position < len(data):
        if position + 352 > len(data) or node_count >= 256:
            raise ValueError("Truncated or excessive legacy model nodes")
        raw_name = data[position : position + 36]
        end = raw_name.find(b"\0")
        if end < 1:
            raise ValueError("Unterminated legacy model node")
        name = raw_name[:end].decode("ascii")
        if names and name in names:
            replacement = names[name].encode("ascii")
            if len(replacement) >= 36:
                raise ValueError("Legacy model node name exceeds limit")
            output[position : position + 36] = replacement.ljust(36, b"\0")
        flags = struct.unpack_from("<I", data, position + 36)[0]
        kind, pointer = struct.unpack_from("<I4xI", data, position + 52)
        if kind != 5 or bool(flags & 0x200) != bool(pointer):
            raise ValueError("Unsupported legacy node type or mesh flag")
        node_info = dict(name=name, parents=struct.unpack_from("<I", data, position + 84)[0],
                         children=struct.unpack_from("<I", data, position + 92)[0], vertices=0)
        if nodes is not None:
            nodes.append(node_info)
        position += 352
        node_count += 1
        if not flags & 0x200:
            continue
        if position + 92 > len(data):
            raise ValueError("Truncated legacy mesh header")
        counts = struct.unpack_from("<5I", data, position + 16)
        polygons, vertices, normals, morphs, lights = counts
        node_info["vertices"] = vertices
        if any(n > 100000 for n in counts):
            raise ValueError("Excessive legacy mesh count")
        position += 92 + 12 * (vertices + normals + morphs)
        if position > len(data):
            raise ValueError("Truncated legacy mesh vectors")
        extra = 0
        for index in range(lights):
            offset = position + 76 * index
            if offset + 76 > len(data):
                raise ValueError("Truncated legacy mesh light")
            extra += struct.unpack_from("<I", data, offset + 12)[0]
        position += 76 * lights + 12 * extra
        if position > len(data):
            raise ValueError("Truncated legacy mesh light vectors")
        rows = []
        for index in range(polygons):
            offset = position + 36 * index
            if offset + 36 > len(data):
                raise ValueError("Truncated legacy polygon table")
            row = struct.unpack_from("<9I", data, offset)
            if not 3 <= row[0] & 255 <= 255 or row[7] >= material_count:
                raise ValueError("Invalid legacy polygon/material index")
            struct.pack_into("<I", output, offset + 28, row[7] + material_offset)
            rows.append(row)
        position += 36 * polygons
        for row in rows:
            count = row[0] & 255
            length = count * (4 + (4 if row[0] & 0x200 else 0) + (8 if row[4] else 0) + 12)
            if position + length > len(data):
                raise ValueError("Truncated legacy polygon data")
            indices = struct.unpack_from(f"<{count}I", data, position)
            if any(index >= vertices for index in indices):
                raise ValueError("Invalid legacy polygon vertex index")
            if row[0] & 0x200:
                normal_indices = struct.unpack_from(f"<{count}I", data, position + count * 4)
                if any(index >= normals for index in normal_indices):
                    raise ValueError("Invalid legacy polygon normal index")
            position += length
    if node_count < 1:
        raise ValueError("Empty legacy model")
    return bytes(output)


def image(data):
    if len(data) < 16:
        raise ValueError("Truncated legacy image")
    flags, width, height, reserved, palette, stretch = struct.unpack_from("<IHHIHH", data)
    expected = 16 + width * height * (3 if flags == 11 else 2)
    if (
        flags not in (3, 5, 11)
        or not 1 <= width <= 4096
        or not 1 <= height <= 4096
        or reserved
        or palette
        or stretch
        or len(data) != expected
    ):
        raise ValueError("Unsupported legacy RGB565 image")


def motion(data):
    """Validate the v4 part/sample layout emitted by the offline MW converter.

    Each track has frame_count + 1 samples, including the closing sample. The
    vectors and quaternions remain unchanged; this does not retarget a skeleton.
    """
    if len(data) < 24:
        raise ValueError("Truncated legacy motion header")
    version, duration, frames, parts, low, high = struct.unpack_from("<IfIIff", data)
    if (
        version != 4
        or not math.isfinite(duration)
        or duration <= 0
        or not 1 <= frames <= 100000
        or not 1 <= parts <= 256
        or (low, high) != (-1.0, 1.0)
    ):
        raise ValueError("Unsupported legacy motion header")
    position, names = 24, set()
    for _ in range(parts):
        if position + 4 > len(data):
            raise ValueError("Truncated legacy motion part")
        length = struct.unpack_from("<I", data, position)[0]
        position += 4
        if not 1 <= length <= 35 or position + length + 4 > len(data):
            raise ValueError("Invalid legacy motion part name")
        name = data[position : position + length].decode("ascii")
        position += length
        if not re.fullmatch(r"[a-zA-Z0-9_.-]+", name) or name in names:
            raise ValueError("Invalid or duplicate legacy motion part")
        names.add(name)
        if struct.unpack_from("<I", data, position)[0] != 12:
            raise ValueError("Invalid legacy motion vector stride")
        position += 4
        end = position + (frames + 1) * 28
        if end > len(data):
            raise ValueError("Truncated legacy motion samples")
        if any(
            not math.isfinite(value) for (value,) in struct.iter_unpack("<f", data[position:end])
        ):
            raise ValueError("Non-finite legacy motion sample")
        position = end
    if position != len(data):
        raise ValueError("Trailing legacy motion data")


def load(document, read):
    """Load pinned resources; validate all content before composing any bank."""
    paths = list(resource_paths(document))
    result = {"resource": document["resource"]}
    source = document["resource"]
    reserved = {source, "mech_" + source}
    for suffix in ("", "_1", "_hud"):
        reserved.update({"mech_" + source + suffix, "mech_" + source + suffix + ".flt"})
    for role in ("motions", "animations", "textures"):
        for name in document[role]:
            if name.casefold() in reserved:
                raise ValueError("Colliding legacy resource name: " + name)
            reserved.add(name.casefold())
    for role, name, path in paths:
        data = read(path)
        if not isinstance(data, bytes) or not 0 < len(data) <= 16 * 1024**2:
            raise ValueError("Invalid legacy resource size")
        if name is None:
            result[role] = data
        else:
            result.setdefault(role, {})[name] = data
    table = materials(result["materials"])
    from chassis_icons import mask

    mask(result["silhouette"])
    for _, texture in table:
        if texture and texture not in result["textures"]:
            raise ValueError("Missing legacy material texture: " + texture)
    result["definition"] = decode(result["definition"])
    if (
        not isinstance(result["definition"], list)
        or len(result["definition"]) != 1
        or not isinstance(result["definition"][0], list)
    ):
        raise ValueError("Unsupported legacy definition root")
    from legacy_chassis_skins import validate

    validate(result["definition"], result["textures"], document.get("skins"))
    if document["schema_version"] == 2:
        result["schema_version"] = 2
        result["skins"] = document["skins"]
    for data in result["models"].values():
        model(data, len(table))
    for data in result["textures"].values():
        image(data)
    for data in result["motions"].values():
        motion(data)
    result["animations"] = {name: decode(data) for name, data in result["animations"].items()}
    return result


def rewrite_archive(original, additions, replacements=None):
    """Append payloads, retaining old bytes and all unaffected directory records."""
    replacements = replacements or {}
    start, records = _directory(original)
    known = {name.casefold(): record for name, _, _, record in records}
    if {name.casefold() for name in additions} & set(known) or not {
        name.casefold() for name in replacements
    } <= set(known):
        raise ValueError("Colliding legacy archive addition or missing index")
    if len(records) + len(additions) > 4096:
        raise ValueError("Legacy archive entry limit exceeded")
    payload = bytearray(original[:start])
    changed = {}
    for name, data in {**replacements, **additions}.items():
        if not re.fullmatch(r"[a-zA-Z0-9_.-]{1,63}", name):
            raise ValueError("Invalid legacy archive member name")
        template = known.get(name.casefold(), records[0][3])
        record = bytearray(template)
        struct.pack_into("<II", record, 0, len(payload), len(data))
        if name.casefold() not in known:
            record[8:72] = name.encode("ascii").ljust(64, b"\0")
        payload.extend(data)
        changed[name.casefold()] = record
    for name, _, _, record in records:
        payload.extend(changed.get(name.casefold(), record))
    for name in additions:
        payload.extend(changed[name.casefold()])
    payload.extend(struct.pack("<II", 1, len(records) + len(additions)))
    _directory(payload)
    return bytes(payload)


def image_members(data):
    if len(data) < 24:
        raise ValueError("Truncated legacy image bank")
    header = struct.unpack_from("<6I", data)
    count = header[3]
    end = 24 + count * 40
    if header != (0, 1, 0, count, 0, 0) or not 1 <= count <= 10000 or end > len(data):
        raise ValueError("Unsupported legacy image bank")
    rows = [struct.unpack_from("<32sII", data, 24 + i * 40) for i in range(count)]
    result = {}
    for i, (raw, offset, marker) in enumerate(rows):
        name = raw.split(b"\0", 1)[0].decode("ascii")
        stop = rows[i + 1][1] if i + 1 < count else len(data)
        if not name or name in result or offset < end or not offset < stop <= len(data):
            raise ValueError("Invalid legacy image bank entry")
        result[name] = (data[offset:stop], marker)
    return result


def append_images(original, additions):
    entries = image_members(original)
    if set(entries) & set(additions):
        raise ValueError("Legacy texture name collision")
    entries.update({name: (data, 0xFFFFFFFF) for name, data in additions.items()})
    if len(entries) > 10000:
        raise ValueError("Legacy texture bank entry limit")
    table = bytearray(struct.pack("<6I", 0, 1, 0, len(entries), 0, 0))
    payload = bytearray()
    start = 24 + len(entries) * 40
    for name, (data, marker) in entries.items():
        if len(name.encode("ascii")) >= 32:
            raise ValueError("Legacy texture name exceeds limit")
        table.extend(
            struct.pack("<32sII", name.encode().ljust(32, b"\0"), start + len(payload), marker)
        )
        payload.extend(data)
    return bytes(table + payload)


def replace_strings(value, names):
    if isinstance(value, list):
        return [replace_strings(child, names) for child in value]
    return names.get(value, value) if isinstance(value, str) else value


def animation_names(value, source, target, names):
    """Namespace local snake-case and camel-case identifiers, retaining shared effects."""
    if isinstance(value, list):
        for child in value:
            animation_names(child, source, target, names)
    elif isinstance(value, str) and (
        value.startswith(source + "_")
        or (value.startswith(source) and value[len(source) : len(source) + 1].isupper())
    ):
        names.setdefault(value, target + value[len(source) :])


def members(data):
    return {
        name.casefold(): data[offset : offset + length]
        for name, offset, length, _ in _directory(data)[1]
    }


def compose(records, banks, game_root, output):
    """Return a resource map after composing validated, namespaced legacy content."""
    loaded = {}
    for name in ("reader.zbd", "mechlib.zbd", "motion.zbd", "rmechtex.zbd"):
        loaded[name] = Path(banks.get("zbd/" + name, game_root / "zbd" / name)).read_bytes()
    reader = members(loaded["reader.zbd"])
    library = members(loaded["mechlib.zbd"])
    common = decode(reader["commonanim.zrd"])
    material_records = materials(library["materials"])
    additions = {name: {} for name in ("reader.zbd", "mechlib.zbd", "motion.zbd")}
    textures = {}
    for item in records:
        data, registration = item["legacy"], item["registration"]
        source, target = data["resource"], registration["resource"]
        definition = data["definition"][0]
        metadata = decode(reader["dfn_" + registration["metadata_template"] + ".zrd"])[0]
        for field in ("max_mass", "weight_class", "clan"):
            if (
                definition.count(field) != 1
                or metadata.count(field) != 1
                or definition[definition.index(field) + 1] != metadata[metadata.index(field) + 1]
            ):
                raise ValueError("Legacy chassis metadata template mismatch: " + field)
        names = {source: target, "mech_" + source: "mech_" + target}
        for suffix in ("", "_1", "_hud"):
            names["mech_" + source + suffix + ".flt"] = "mech_" + target + suffix + ".flt"
            names["mech_" + source + suffix] = "mech_" + target + suffix
        # Original actor code constructs names such as <resource>_fallb rather
        # than reading every clip name from the definition. Retain those suffixes.
        for name in data["motions"]:
            if not name.startswith(source + "_"):
                raise ValueError("Legacy motion does not belong to its chassis")
            names[name] = target + name[len(source) :]
        for index, name in enumerate(sorted(data["animations"])):
            names[name] = target + "_a" + str(index) + ".zrd"
        from legacy_chassis_skins import texture_names, validate

        for name, generated in texture_names(data, target).items():
            names[name] = generated
            textures[generated] = data["textures"][name]
        donor_materials = materials(data["materials"])
        base = len(material_records)
        for raw, name in donor_materials:
            if name and name not in data["textures"]:
                raise ValueError("Missing legacy material texture: " + name)
            if name in names:
                encoded = names[name].encode("ascii")
                raw = raw[:40] + struct.pack("<I", len(encoded)) + encoded
            material_records.append((raw, names.get(name, name)))
        for role, suffix in (("close", ""), ("distance", "_1"), ("cockpit", "_hud")):
            name = "mech_" + target + suffix + ".flt"
            additions["mechlib.zbd"][name] = model(
                data["models"][role], len(donor_materials), base, names
            )
        additions["motion.zbd"].update(
            {names[name]: blob for name, blob in data["motions"].items()}
        )
        for tree in data["animations"].values():
            animation_names(tree, source, target, names)
        rewritten = replace_strings(data["definition"], names)
        if "skins" in definition:
            # Skin keys and suffixes are literals, even when a resource happens
            # to use the same name. Only primary/damage texture references move.
            position = definition.index("skins")
            rewritten[0][position] = "skins"
            original_block = definition[position + 1]
            block = rewritten[0][position + 1]
            for offset in range(0, len(block), 2):
                key = original_block[offset]
                block[offset] = key
                if key not in ("MSG_SKIN_PRIMARY", "damage"):
                    block[offset + 1] = original_block[offset + 1].copy()
        validate(rewritten, textures, data.get("skins"))
        additions["reader.zbd"]["dfn_" + target + ".zrd"] = encode(rewritten)
        for name, tree in data["animations"].items():
            additions["reader.zbd"][names[name]] = encode(replace_strings(tree, names))
        animation_root = common[0][common[0].index("ANIMATION_DEFINITIONS") + 1]
        animation_list = animation_root[animation_root.index("ANIMATION_LIST") + 1]
        for name in data["animations"]:
            animation_list.extend(["ANIMATION_DEFINITION_FILE", [names[name]]])
    new_materials = struct.pack("<I", len(material_records)) + b"".join(
        raw for raw, _ in material_records
    )
    if len(material_records) > 10000:
        raise ValueError("Composed legacy material count exceeds limit")
    for name, extra in additions.items():
        replacements = {}
        if name == "mechlib.zbd":
            replacements["materials"] = new_materials
        elif name == "reader.zbd":
            replacements["commonanim.zrd"] = encode(common)
        path = output / name
        path.write_bytes(rewrite_archive(loaded[name], extra, replacements))
        banks["zbd/" + name] = str(path.resolve())
    path = output / "rmechtex.zbd"
    path.write_bytes(append_images(loaded["rmechtex.zbd"], textures))
    banks["zbd/rmechtex.zbd"] = str(path.resolve())
    return banks
