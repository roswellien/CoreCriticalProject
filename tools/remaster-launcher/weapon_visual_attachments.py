"""Explicit mesh-bound arm muzzle metadata; never modifies gameplay sockets."""

import math
import re

CAPABILITY = "owned-chassis-weapon-visuals"
NAME = re.compile(r"[A-Za-z0-9_.-]{1,31}\Z")


def validate(value, meshes):
    if (not isinstance(value, dict) or set(value) != {"schema_version", "close", "distance"}
            or type(value["schema_version"]) is not int or value["schema_version"] != 1):
        raise ValueError("Invalid weapon visual attachment schema")
    result = {}
    previous = None
    for lod in ("close", "distance"):
        table = value[lod]
        if (not isinstance(table, dict) or set(table) != {"mesh_identity", "records"}
                or not isinstance(table["mesh_identity"], str)
                or not re.fullmatch("[0-9a-f]{16}", table["mesh_identity"])):
            raise ValueError("Invalid weapon visual mesh identity")
        mesh = meshes[lod]
        if int(table["mesh_identity"], 16) != mesh["identity"]:
            raise ValueError("Weapon visual mesh identity mismatch")
        records = table["records"]
        if not isinstance(records, list) or not 1 <= len(records) <= 64:
            raise ValueError("Invalid weapon visual attachment count")
        keys = []
        for row in records:
            if (not isinstance(row, dict)
                    or set(row) != {"source_control", "weapon", "bone", "position"}
                    or any(not isinstance(row[k], str) or not NAME.fullmatch(row[k])
                           for k in ("source_control", "weapon", "bone"))):
                raise ValueError("Invalid weapon visual attachment record")
            control = row["source_control"]
            if control not in ("lhand", "rhand"):
                raise ValueError("Weapon visual attachment requires source forearm")
            expected = "Forearm_Left" if control == "lhand" else "Forearm_Right"
            if row["bone"] != expected or mesh["controls"].get(expected) != control:
                raise ValueError("Weapon visual attachment bone/control mismatch")
            key = (control, row["weapon"])
            if key in keys:
                raise ValueError("Ambiguous weapon visual attachment")
            keys.append(key)
            position = row["position"]
            bounds = mesh["bounds"].get(expected)
            if (not isinstance(position, list) or len(position) != 3 or bounds is None
                    or any(type(v) not in (int, float) or not math.isfinite(v)
                           or not bounds[0][i] - .1 <= v <= bounds[1][i] + .1
                           for i, v in enumerate(position))):
                raise ValueError("Weapon visual muzzle outside rigid donor geometry")
        if previous is not None and keys != previous:
            raise ValueError("Weapon visual LOD keys mismatch")
        previous = keys
        result[lod] = {"mesh_identity": table["mesh_identity"],
                       "records": [dict(r, position=list(r["position"])) for r in records]}
    return result
