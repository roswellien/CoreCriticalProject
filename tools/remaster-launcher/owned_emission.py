"""Bounded, explicitly authored emission for selected replacement batches.

BWMEM1 binds the full mesh/UV identity and RGB565 pixel identity. It contains
no images and never infers emitters from an asset name or bright pixels.
"""

import io
import math
import re
import struct

MAGIC = b"BWMEM1\0\0"
CAPABILITY = "owned-chassis-emission"
FORMAT = "BWMEM1"
MAX_BYTES = 1024 * 1024
NAME = re.compile(r"[A-Za-z0-9_.-]{1,31}\Z")


def mesh_bindings(mesh, textures):
    """Return the exact batch owners, bounds and interned color identities."""
    from owned_chassis_visuals import Reader, mesh_metadata
    from normal_materials import pixel_hash

    metadata = mesh_metadata(mesh)
    reader = Reader(mesh)
    if reader.take(8) != b"BWMESH4\0":
        raise ValueError("Emission requires owned BWMESH4 geometry")
    count, bones, refs = reader.number(), reader.number(), reader.number()
    reader.take(4 + 40 + bones * 196 + refs * 160)
    batches = []
    for _ in range(count):
        owner = reader.name()
        reader.name()
        bone, vertices, _ = struct.unpack("<III", reader.take(12))
        rows = list(struct.iter_unpack("<8f", reader.take(vertices * 32)))
        bounds = tuple((min(v[a] for v in rows), max(v[a] for v in rows)) for a in range(3))
        if bone == 0xFFFFFFFF:
            reader.take(vertices * 4)
        batches.append({"owner": owner, "bounds": bounds, "rigid": bone != 0xFFFFFFFF})
    reader.end()
    reader = Reader(textures)
    if reader.take(8) != b"BWTEX1\0\0" or reader.number() != metadata["batches"]:
        raise ValueError("Emission texture batch mismatch")
    materials = reader.number()
    if not 1 <= materials <= 64:
        raise ValueError("Invalid emission material count")
    indices = [reader.number() for _ in batches]
    colors = []
    for _ in range(materials):
        name = reader.name()
        width, height = reader.number(), reader.number()
        reader.take(8)
        if not 1 <= width <= 4096 or not 1 <= height <= 4096:
            raise ValueError("Invalid emission color dimensions")
        pixels = reader.take(width * height * 2)
        colors.append((name, width, height, pixel_hash(pixels)))
    reader.end()
    for batch, index in zip(batches, indices):
        if index >= len(colors):
            raise ValueError("Invalid emission material index")
        batch["material"], batch["width"], batch["height"], batch["hash"] = colors[index]
    return batches


def read(data, mesh_hash, bindings):
    if not isinstance(data, bytes) or not 20 <= len(data) <= MAX_BYTES:
        raise ValueError("Invalid owned emission size")
    stream = io.BytesIO(data)

    def take(size):
        value = stream.read(size)
        if len(value) != size:
            raise ValueError("Truncated owned emission")
        return value

    def number():
        return struct.unpack("<I", take(4))[0]

    def name():
        raw = take(32)
        value, separator, padding = raw.partition(b"\0")
        try:
            value = value.decode("ascii")
        except UnicodeDecodeError as error:
            raise ValueError("Invalid emission name") from error
        if not separator or any(padding) or not NAME.fullmatch(value):
            raise ValueError("Invalid emission name")
        return value

    def floats(count, low, high):
        values = struct.unpack("<" + "f" * count, take(count * 4))
        if any(not math.isfinite(v) or not low <= v <= high for v in values):
            raise ValueError("Invalid emission floating point value")
        return values

    if take(8) != MAGIC:
        raise ValueError("Unsupported owned emission format")
    count = number()
    if not 1 <= count <= 64 or struct.unpack("<Q", take(8))[0] != mesh_hash:
        raise ValueError("Emission mesh identity/count mismatch")
    records, ids, batches = [], set(), set()
    for _ in range(count):
        ident, batch = name(), number()
        owner, material = name(), name()
        width, height, identity = struct.unpack("<IIQ", take(16))
        if ident in ids or batch in batches or batch >= len(bindings):
            raise ValueError("Duplicate or invalid emission binding")
        ids.add(ident)
        batches.add(batch)
        expected = bindings[batch]
        if not expected.get("rigid", True):
            raise ValueError("Emission version 1 requires a rigid batch")
        if any(not math.isfinite(v) for pair in expected["bounds"] for v in pair) or any(
            low > high for low, high in expected["bounds"]
        ):
            raise ValueError("Invalid emission mesh bounds")
        if (owner, material, width, height, identity) != tuple(
            expected[k] for k in ("owner", "material", "width", "height", "hash")
        ):
            raise ValueError("Emission material identity mismatch")
        strength = floats(1, 0, 2)[0]
        region_count, anchor_count = number(), number()
        if not 1 <= region_count <= 32 or anchor_count > 8:
            raise ValueError("Invalid emission region/anchor count")
        regions = [floats(4, 0, 1) for _ in range(region_count)]
        if any(r[0] >= r[2] or r[1] >= r[3] for r in regions):
            raise ValueError("Empty emission UV rectangle")
        anchors, anchor_ids = [], set()
        for _ in range(anchor_count):
            anchor_id = name()
            position = floats(3, -1e6, 1e6)
            color, radius, intensity = floats(3, 0, 1), floats(1, 0, 4)[0], floats(1, 0, 2)[0]
            if anchor_id in anchor_ids or any(
                not expected["bounds"][a][0] - 4 <= position[a] <= expected["bounds"][a][1] + 4
                for a in range(3)
            ):
                raise ValueError("Duplicate or out-of-bounds emission anchor")
            anchor_ids.add(anchor_id)
            anchors.append(dict(id=anchor_id, position=position, color=color, radius=radius, intensity=intensity))
        records.append(dict(id=ident, batch=batch, owner=owner, material=material,
                            strength=strength, regions=regions, anchors=anchors))
    if stream.read(1):
        raise ValueError("Trailing owned emission bytes")
    return records


def pack(mesh_hash, bindings, records):
    def name(value):
        if not isinstance(value, str) or not NAME.fullmatch(value):
            raise ValueError("Invalid emission name")
        return value.encode("ascii").ljust(32, b"\0")

    if not 1 <= len(records) <= 64:
        raise ValueError("Invalid emission record count")
    data = bytearray(MAGIC + struct.pack("<IQ", len(records), mesh_hash))
    for record in records:
        batch = record["batch"]
        if type(batch) is not int or not 0 <= batch < len(bindings):
            raise ValueError("Invalid emission batch")
        binding = bindings[batch]
        regions, anchors = record["regions"], record.get("anchors", [])
        if not 1 <= len(regions) <= 32 or len(anchors) > 8:
            raise ValueError("Invalid emission region/anchor count")
        data += name(record["id"]) + struct.pack("<I", batch)
        data += name(binding["owner"]) + name(binding["material"])
        data += struct.pack("<IIQfII", binding["width"], binding["height"], binding["hash"],
                            record["strength"], len(regions), len(anchors))
        for region in regions:
            data += struct.pack("<4f", *region)
        for anchor in anchors:
            data += name(anchor["id"]) + struct.pack("<8f", *anchor["position"], *anchor["color"],
                                                    anchor["radius"], anchor["intensity"])
    result = bytes(data)
    read(result, mesh_hash, bindings)
    return result
