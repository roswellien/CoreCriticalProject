"""Bounded visual-only payloads for a chassis retaining its owned legacy controller."""

import math
import re
import struct

from legacy_chassis_resources import materials, model

CAPABILITY = "owned-chassis-visuals"
NAME = re.compile(r"[A-Za-z0-9_.-]{1,31}\Z")


def references(value):
    if (
        not isinstance(value, dict)
        or set(value) - {"normals", "emission", "weapon_attachments"} != {"schema_version", "meshes", "textures"}
        or type(value["schema_version"]) is not int
        or value["schema_version"] != 1
    ):
        raise ValueError("Invalid owned visual alternative")
    for role in ("meshes", "textures"):
        if not isinstance(value[role], dict) or set(value[role]) != {"close", "distance"}:
            raise ValueError("Owned visuals require both LODs")
        for lod, path in value[role].items():
            if not isinstance(path, str) or not path:
                raise ValueError("Invalid owned visual resource path")
            yield role, lod, path
    pages = value.get("normals", [])
    if (
        not isinstance(pages, list)
        or len(pages) > 16
        or any(not isinstance(p, str) or not p for p in pages)
        or len(set(pages)) != len(pages)
    ):
        raise ValueError("Invalid owned visual normal pages")
    for index, path in enumerate(pages):
        yield "normals", index, path
    if "emission" in value:
        table = value["emission"]
        if not isinstance(table, dict) or set(table) != {"close", "distance"}:
            raise ValueError("Owned emission requires both LODs")
        for lod, path in table.items():
            if not isinstance(path, str) or not path:
                raise ValueError("Invalid owned emission path")
            yield "emission", lod, path


class Reader:
    def __init__(self, data):
        if not isinstance(data, bytes) or not 0 < len(data) <= 256 * 1024**2:
            raise ValueError("Invalid owned visual resource size")
        self.data, self.position = data, 0

    def take(self, size):
        if size < 0 or self.position + size > len(self.data):
            raise ValueError("Truncated owned visual resource")
        result = self.data[self.position : self.position + size]
        self.position += size
        return result

    def number(self):
        return struct.unpack("<I", self.take(4))[0]

    def name(self, empty=False):
        raw = self.take(32)
        if b"\0" not in raw:
            raise ValueError("Unterminated owned visual name")
        name, padding = raw.split(b"\0", 1)
        if any(padding):
            raise ValueError("Invalid owned visual name padding")
        name = name.decode("ascii")
        if not (empty and not name) and not NAME.fullmatch(name):
            raise ValueError("Invalid owned visual name")
        return name

    def matrix(self):
        values = struct.unpack("<16d", self.take(128))
        if not all(math.isfinite(v) for v in values) or values[12:] != (0, 0, 0, 1):
            raise ValueError("Invalid owned visual rest matrix")
        a, b, c, _, d, e, f, _, g, h, i, *_ = values
        if abs(a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)) < 1e-12:
            raise ValueError("Singular owned visual rest matrix")

    def end(self):
        if self.position != len(self.data):
            raise ValueError("Trailing owned visual data")


def validate_arm_rest(bones):
    """Policy 3 needs a single, connected controller chain for each donor arm."""
    controls = {}
    parents = []
    arm_controls = {"larm", "rarm", "lhand", "rhand"}
    for index, (name, control, parent) in enumerate(bones):
        if control and control in controls:
            raise ValueError("Duplicate arm policy control")
        if control:
            controls[control] = index
        while parent >= 0 and not bones[parent][1]:
            parent = bones[parent][2]
        parents.append(parent)
        if control and control not in arm_controls and parent >= 0 and bones[parent][1] in arm_controls:
            raise ValueError("Unsupported bound arm descendant")
    for control, name, expected_parent in (
        ("larm", "Upperarm_Left", "torso"), ("rarm", "Upperarm_Right", "torso"),
        ("lhand", "Forearm_Left", "larm"), ("rhand", "Forearm_Right", "rarm"),
    ):
        index = controls.get(control)
        if index is None or bones[index][0] != name or parents[index] < 0 or bones[parents[index]][1] != expected_parent:
            raise ValueError("Authored arm parent mismatch")


def mesh_metadata(data):
    reader = Reader(data)
    if reader.take(8) != b"BWMESH4\0":
        raise ValueError("Owned visuals require BWMESH4")
    count = reader.number()
    bones, refs, flags = reader.number(), reader.number(), reader.number()
    if not 1 <= count <= 256 or not 1 <= bones <= 256 or not 1 <= refs <= 128 or flags > 3:
        raise ValueError("Invalid owned visual rig counts")
    gait = struct.unpack("<5d", reader.take(40))
    if not all(math.isfinite(v) for v in gait) or not 0 <= gait[0] <= 10:
        raise ValueError("Invalid owned visual gait")
    names, controls = set(), set()
    rig_bones = []
    for index in range(bones):
        name, control = reader.name(), reader.name(empty=True)
        parent = struct.unpack("<i", reader.take(4))[0]
        if name in names or not -1 <= parent < index:
            raise ValueError("Invalid owned visual bone hierarchy")
        names.add(name)
        if control:
            controls.add(control)
        reader.matrix()
        rig_bones.append((name, control, parent))
    if flags == 3:
        validate_arm_rest(rig_bones)
    references = set()
    for _ in range(refs):
        name = reader.name()
        if name in references:
            raise ValueError("Duplicate owned source reference")
        references.add(name)
        reader.matrix()
    if not controls <= references:
        raise ValueError("Unknown owned source reference")
    required_controls = {
        "hip",
        "torso",
        "larm",
        "rarm",
        "lhand",
        "rhand",
        "lthigh",
        "rthigh",
        "lcalf",
        "rcalf",
        "lfoot",
        "rfoot",
    }
    required_bones = {
        "Pelvis",
        "Torso_Twist",
        "Upperarm_Left",
        "Upperarm_Right",
        "Forearm_Left",
        "Forearm_Right",
        "Thigh_Left",
        "Thigh_Right",
        "Calf_Left",
        "Calf_Right",
        "Foot0_Left",
        "Foot0_Right",
    }
    if not required_controls <= references or not required_bones <= names:
        raise ValueError("Missing required owned retarget joint")
    owners, visibility, bindings = set(), set(), []
    rigid_bounds = {}
    for _ in range(count):
        owner = reader.name()
        owners.add(owner)
        visible = reader.name(empty=True)
        if not visible:
            raise ValueError("Owned batch requires source visibility")
        visibility.add(visible)
        bindings.append((owner, visible))
        bone, size, _ = reader.number(), reader.number(), reader.number()
        if bone != 0xFFFFFFFF and bone >= bones or not 0 < size <= 65535 or size % 3:
            raise ValueError("Invalid owned visual batch")
        for row in struct.iter_unpack("<8f", reader.take(size * 32)):
            if bone != 0xFFFFFFFF:
                key = rig_bones[bone][0]
                low, high = rigid_bounds.setdefault(key, ([math.inf] * 3, [-math.inf] * 3))
                for axis in range(3):
                    low[axis] = min(low[axis], row[axis])
                    high[axis] = max(high[axis], row[axis])
            if not all(math.isfinite(v) for v in row) or sum(v * v for v in row[3:6]) < 0.5:
                raise ValueError("Invalid owned visual vertex")
        if bone == 0xFFFFFFFF and any(
            index >= bones for (index,) in struct.iter_unpack("<I", reader.take(size * 4))
        ):
            raise ValueError("Invalid owned visual vertex bone")
    reader.end()
    return {
        "attachment_controls": {b[0]: b[1] for b in rig_bones},
        "attachment_bounds": rigid_bounds,
        "batches": count,
        "capability_version": flags if flags >= 2 else 1,
        "owners": owners,
        "visibility": visibility,
        "references": references,
        "bindings": bindings,
    }


def texture_metadata(data, batches):
    reader = Reader(data)
    if reader.take(8) != b"BWTEX1\0\0" or reader.number() != batches:
        raise ValueError("Owned visual texture batch mismatch")
    count = reader.number()
    if not 1 <= count <= 64:
        raise ValueError("Invalid owned visual material count")
    if any(reader.number() >= count for _ in range(batches)):
        raise ValueError("Invalid owned visual material binding")
    keys = set()
    from normal_materials import pixel_hash

    for _ in range(count):
        reader.name()
        width, height = reader.number(), reader.number()
        reader.take(8)
        if not 1 <= width <= 4096 or not 1 <= height <= 4096:
            raise ValueError("Invalid owned visual texture dimensions")
        pixels = reader.take(width * height * 2)
        keys.add((width, height, 1, pixel_hash(pixels)))
    reader.end()
    return keys


def source_nodes(data, material_count):
    nodes = []
    model(data, material_count, nodes=nodes)
    if len(nodes) > 128:
        raise ValueError("Owned source hierarchy exceeds renderer limit")
    stack, names = [], set()
    for index, node in enumerate(nodes):
        while stack and stack[-1][1] == 0:
            stack.pop()
        if (
            node["name"] in names
            or node["children"] > 64
            or node["parents"] != (1 if index else 0)
            or (index and not stack)
            or len(stack) > 16
        ):
            raise ValueError("Invalid owned source tree")
        names.add(node["name"])
        node["parent"] = stack[-1][0] if stack else None
        if stack:
            stack[-1][1] -= 1
        stack.append([node["name"], node["children"]])
    if any(remaining for _, remaining in stack):
        raise ValueError("Incomplete owned source tree")
    return {node["name"]: node for node in nodes}


def validate(value, legacy, read):
    payloads = {role: {} for role in ("meshes", "textures")}
    pages = []
    emission_payloads = {}
    for role, lod, path in references(value):
        if role == "emission":
            from owned_emission import FORMAT
            emission_payloads[lod] = read(path, FORMAT)
        elif role == "normals":
            page = read(path, "BWSNR2")
            if not 0 < len(page) <= 128 * 1024**2:
                raise ValueError("Invalid owned normal page size")
            if sum(map(len, pages)) + len(page) > 512 * 1024**2:
                raise ValueError("Owned normal resident budget exceeded")
            pages.append(page)
        else:
            payloads[role][lod] = read(path, "BWMESH4" if role == "meshes" else "BWTEX1")
    result = {"payloads": payloads, "rosters": {}, "capability_version": 1}
    attachment_meshes = {}
    if emission_payloads:
        from owned_emission import read as read_emission, mesh_bindings
        from surface_materials import mesh_uv_identity
        for lod, data in emission_payloads.items():
            read_emission(data, mesh_uv_identity(payloads["meshes"][lod]),
                          mesh_bindings(payloads["meshes"][lod], payloads["textures"][lod]))
        result["emission_payloads"] = emission_payloads
    keys = set()
    count = len(materials(legacy["materials"]))
    for lod in ("close", "distance"):
        metadata = mesh_metadata(payloads["meshes"][lod])
        from surface_materials import mesh_uv_identity
        attachment_meshes[lod] = {"identity": mesh_uv_identity(payloads["meshes"][lod]),
                                  "controls": metadata["attachment_controls"],
                                  "bounds": metadata["attachment_bounds"]}
        result["capability_version"] = max(result["capability_version"], metadata["capability_version"])
        keys.update(texture_metadata(payloads["textures"][lod], metadata["batches"]))
        nodes = source_nodes(legacy["models"][lod], count)
        if (
            not (metadata["owners"] | metadata["visibility"] | metadata["references"])
            <= nodes.keys()
        ):
            raise ValueError("Owned visual references a foreign source node")
        roster = []
        for name, node in nodes.items():
            if not node["vertices"]:
                continue
            owner = name
            while owner is not None and owner not in metadata["owners"]:
                owner = nodes[owner]["parent"]
            if owner is None:
                raise ValueError("Owned visual omits a source controller")
            roster.append({"name": name, "vertices": node["vertices"], "owner": owner})
        if not roster or {row["owner"] for row in roster} != metadata["owners"]:
            raise ValueError("Owned visual has unused or missing controller geometry")
        owner_by_node = {row["name"]: row["owner"] for row in roster}
        if any(owner_by_node.get(visible) != owner for owner, visible in metadata["bindings"]):
            raise ValueError("Owned visual visibility is outside controller ancestry")
        result["rosters"][lod] = roster
        if metadata["capability_version"] >= 2:
            arms = []
            removed_names = set()
            for arm in ("larm", "rarm"):
                removed = []
                for row in roster:
                    ancestor = row["name"]
                    while ancestor is not None and ancestor != arm:
                        ancestor = nodes[ancestor]["parent"]
                    if ancestor == arm:
                        removed.append(row["name"])
                if (not 1 <= len(removed) <= 8 or nodes[arm]["parent"] is None
                        or removed_names.intersection(removed)):
                    raise ValueError("Unsupported original arm subtree")
                removed_names.update(removed)
                arms.append(dict(arm=arm, parent=nodes[arm]["parent"], removed=removed))
            result.setdefault("arm_damage", {})[lod] = arms
    if "arm_damage" in result and set(result["arm_damage"]) != {"close", "distance"}:
        raise ValueError("Both owned LODs must use the same source joint mode")
    signatures = [
        {(row["name"], row["vertices"]) for row in result["rosters"][lod]}
        for lod in ("close", "distance")
    ]
    if signatures[0] == signatures[1]:
        raise ValueError("Owned source LOD signatures must be distinguishable")
    if "arm_damage" in result:
        damage_signatures = []
        for lod in ("close", "distance"):
            source = {row["name"]: row["vertices"] for row in result["rosters"][lod]}
            stumps = {plan["arm"] + "_stub01" for plan in result["arm_damage"][lod]}
            if stumps & source.keys():
                raise ValueError("Owned source tree already contains an arm stump")
            states = set()
            for mask in range(4):
                remaining = dict(source)
                for index, plan in enumerate(result["arm_damage"][lod]):
                    if mask & (1 << index):
                        for name in plan["removed"]:
                            del remaining[name]
                        # The runtime authenticates the same shared stump bytes
                        # for both LODs; only their presence affects identity here.
                        remaining[plan["arm"] + "_stub01"] = None
                states.add(frozenset(remaining.items()))
            damage_signatures.append(states)
        if damage_signatures[0] & damage_signatures[1]:
            raise ValueError("Owned source LOD signatures overlap after arm loss")
    cockpit = source_nodes(legacy["models"]["cockpit"], count)
    if sum(map(len, pages)) > 512 * 1024**2:
        raise ValueError("Owned normal resident budget exceeded")
    from normal_materials import read_surface_bindings

    bindings = set()
    for page in pages:
        if len(page) > 128 * 1024**2 or page[:8] != b"BWSNR2\0\0":
            raise ValueError("Invalid owned normal page")
        for key, _ in read_surface_bindings(page):
            if key not in keys or key in bindings:
                raise ValueError("Foreign or duplicate owned normal key")
            bindings.add(key)
    result["normal_pages"] = pages
    result["cockpit"] = [
        {"name": n["name"], "vertices": n["vertices"], "owner": n["name"]}
        for n in cockpit.values()
        if n["vertices"]
    ]
    if "weapon_attachments" in value:
        from weapon_visual_attachments import validate as validate_attachments
        result["weapon_attachments"] = validate_attachments(value["weapon_attachments"], attachment_meshes)
    return result
