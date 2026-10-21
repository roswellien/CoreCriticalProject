#!/usr/bin/env python3

"""MW3 Authentic In-Game 3D Asset Extractor.

Extracts real 3D geometry (vertices & polygons) directly from MW3 GameZ
and MechLib archives, normalizing them for rendering in the 3D Web Studio.
"""

import json
import math
import os
import sys
import zipfile
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from editor.config import cache_directory, game_directory, tool_directory

ROOT = Path(__file__).resolve().parents[5]
C1_GAMEZ_DIR = cache_directory() / "c1_gamez"
OUTPUT_JSON = ROOT / "games/mw3/mod-tools/editor/web/static/assets/game_assets_3d.json"
TEMP_MECHLIB_ZIP = ROOT / "local/temp_mechlib.zip"
MECHLIB_ZBD = game_directory() / "zbd/mechlib.zbd"
UNZBD_EXE = tool_directory() / "unzbd.exe"


def make_transform_matrix(t, r, s):
    """Build a row-major affine matrix using radian Euler angles and column vectors.

    Scale applies per local axis, followed by X/Y/Z rotation and translation.
    Keeping this convention explicit prevents preview extraction from transposing
    or changing the handedness of the original scene's placement hierarchy.
    """
    cx, sx = math.cos(r["x"]), math.sin(r["x"])
    cy, sy = math.cos(r["y"]), math.sin(r["y"])
    cz, sz = math.cos(r["z"]), math.sin(r["z"])

    r00 = cz * cy
    r01 = cz * sy * sx - sz * cx
    r02 = cz * sy * cx + sz * sx
    r10 = sz * cy
    r11 = sz * sy * sx + cz * cx
    r12 = sz * sy * cx - cz * sx
    r20 = -sy
    r21 = cy * sx
    r22 = cy * cx

    r00 *= s["x"]
    r01 *= s["y"]
    r02 *= s["z"]
    r10 *= s["x"]
    r11 *= s["y"]
    r12 *= s["z"]
    r20 *= s["x"]
    r21 *= s["y"]
    r22 *= s["z"]

    return [
        [r00, r01, r02, t["x"]],
        [r10, r11, r12, t["y"]],
        [r20, r21, r22, t["z"]],
        [0.0, 0.0, 0.0, 1.0],
    ]


def mat_mul(a, b):
    """Compose parent/local 4x4 transforms; callers supply ordinary row lists."""
    res = [[0.0] * 4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            res[i][j] = sum(a[i][k] * b[k][j] for k in range(4))
    return res


def transform_pt(m, pt):
    """Transform a source position and round preview coordinates to three decimals."""
    x = m[0][0] * pt["x"] + m[0][1] * pt["y"] + m[0][2] * pt["z"] + m[0][3]
    y = m[1][0] * pt["x"] + m[1][1] * pt["y"] + m[1][2] * pt["z"] + m[1][3]
    z = m[2][0] * pt["x"] + m[2][1] * pt["y"] + m[2][2] * pt["z"] + m[2][3]
    return [round(x, 3), round(y, 3), round(z, 3)]


def extract_gamez_node(nodes, models, root_idx, ignore=None):
    """Flatten a chosen node subtree into a centred preview triangle mesh.

    Node/model indices belong to the selected extraction. Ignored visual names
    exclude destroyed/debris/shadow variants; this is a static preview extraction,
    not an exporter of gameplay hierarchy, collision or animation behavior.
    """
    if ignore is None:
        ignore = ["destr", "debris", "smoke", "shadow"]
    all_verts = []
    all_faces = []

    # Root offset removal so model is centered at (0,0,0)

    root_tr = nodes[root_idx].get("data", {}).get("Object3d", {}).get("transform", {})
    root_t = {"x": 0, "y": 0, "z": 0}
    if isinstance(root_tr, dict) and "RotateTranslateScale" in root_tr:
        root_t = root_tr["RotateTranslateScale"]["translate"]
    base_mat = [
        [1, 0, 0, -root_t["x"]],
        [0, 1, 0, -root_t["y"]],
        [0, 0, 1, -root_t["z"]],
        [0, 0, 0, 1],
    ]

    def walk(idx, parent_mat):
        n = nodes[idx]
        name = n.get("name", "").lower()
        if any(ign in name for ign in ignore):
            return
        tr = n.get("data", {}).get("Object3d", {}).get("transform", {})
        if isinstance(tr, dict) and "RotateTranslateScale" in tr:
            rts = tr["RotateTranslateScale"]
            loc_mat = make_transform_matrix(rts["translate"], rts["rotate"], rts["scale"])
            cur_mat = mat_mul(parent_mat, loc_mat)
        else:
            cur_mat = parent_mat
        mi = n.get("model_index", -1)
        if mi >= 0 and mi < len(models):
            m = models[mi]
            v_offset = len(all_verts)
            for v in m.get("vertices", []):
                all_verts.append(transform_pt(cur_mat, v))
            for p in m.get("polygons", []):
                idx_list = p.get("vertex_indices", [])
                if len(idx_list) == 3:
                    all_faces.append(
                        [idx_list[0] + v_offset, idx_list[1] + v_offset, idx_list[2] + v_offset]
                    )
                elif len(idx_list) == 4:
                    all_faces.append(
                        [idx_list[0] + v_offset, idx_list[1] + v_offset, idx_list[2] + v_offset]
                    )
                    all_faces.append(
                        [idx_list[0] + v_offset, idx_list[2] + v_offset, idx_list[3] + v_offset]
                    )
        for c in n.get("child_indices", []):
            walk(c, cur_mat)

    walk(root_idx, base_mat)

    # Normalize Y to ground level

    if all_verts:
        min_y = min(p[1] for p in all_verts)
        all_verts = [[p[0], round(p[1] - min_y, 3), p[2]] for p in all_verts]
    return {"vertices": all_verts, "faces": all_faces}


def extract_mech_data(data):
    """Flatten a static MechLib scene and lift its lowest point to preview ground.

    This produces geometry for the browser, not the original articulated rig or
    a native model adapter. The source node transforms are accumulated recursively.
    """
    nodes = data.get("nodes", [])
    models = data.get("models", [])
    ident = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    all_verts = []
    all_faces = []

    def walk(idx, parent_mat):
        n = nodes[idx]
        name = n.get("name", "").lower()
        if any(ign in name for ign in ["destr", "debris", "smoke", "cockpit_int"]):
            return
        tr = n.get("data", {}).get("Object3d", {}).get("transform", {})
        if isinstance(tr, dict) and "RotateTranslateScale" in tr:
            rts = tr["RotateTranslateScale"]
            loc_mat = make_transform_matrix(rts["translate"], rts["rotate"], rts["scale"])
            cur_mat = mat_mul(parent_mat, loc_mat)
        else:
            cur_mat = parent_mat
        mi = n.get("model_index", -1)
        if mi >= 0 and mi < len(models):
            m = models[mi]
            v_offset = len(all_verts)
            for v in m.get("vertices", []):
                all_verts.append(transform_pt(cur_mat, v))
            for p in m.get("polygons", []):
                idx_list = p.get("vertex_indices", [])
                if len(idx_list) == 3:
                    all_faces.append(
                        [idx_list[0] + v_offset, idx_list[1] + v_offset, idx_list[2] + v_offset]
                    )
                elif len(idx_list) == 4:
                    all_faces.append(
                        [idx_list[0] + v_offset, idx_list[1] + v_offset, idx_list[2] + v_offset]
                    )
                    all_faces.append(
                        [idx_list[0] + v_offset, idx_list[2] + v_offset, idx_list[3] + v_offset]
                    )
        for c in n.get("child_indices", []):
            walk(c, cur_mat)

    walk(0, ident)

    # Normalize Y

    if all_verts:
        min_y = min(p[1] for p in all_verts)
        all_verts = [[p[0], round(p[1] - min_y, 3), p[2]] for p in all_verts]
    return {"vertices": all_verts, "faces": all_faces}


def main():
    """Write ignored preview geometry from configured local archives/extractions."""
    print("Extracting authentic MW3 in-game 3D assets...")
    assets = {}

    # 1. Extract Buildings & Turrets from GameZ

    nodes_path = C1_GAMEZ_DIR / "nodes.json"
    models_path = C1_GAMEZ_DIR / "models.json"
    if nodes_path.is_file() and models_path.is_file():
        c1_nodes = json.loads(nodes_path.read_text(encoding="utf-8"))
        c1_models = json.loads(models_path.read_text(encoding="utf-8"))

        building_targets = {
            "turret_srm": 7936,
            "turret_laser": 7359,
            "bunker": 4790,
            "comm_center": 4865,
            "fuel_tank": 7537,
            "city_building": 5117,
        }

        for k, root_idx in building_targets.items():
            mesh = extract_gamez_node(c1_nodes, c1_models, root_idx)
            assets[k] = mesh
            print(
                f"  [OK] Extracted {k}: {len(mesh['vertices'])} verts, {len(mesh['faces'])} faces"
            )
    # 2. Extract BattleMechs from MechLib

    if not TEMP_MECHLIB_ZIP.is_file() and MECHLIB_ZBD.is_file() and UNZBD_EXE.is_file():
        import subprocess

        subprocess.run(
            [str(UNZBD_EXE), "mw", "mechlib", str(MECHLIB_ZBD), str(TEMP_MECHLIB_ZIP)],
            capture_output=True,
        )
    if TEMP_MECHLIB_ZIP.is_file():
        with zipfile.ZipFile(TEMP_MECHLIB_ZIP) as z:
            mech_targets = {
                "mech_madcat": "mech_madcat.flt.json",
                "mech_bushwacker": "mech_bushwacker.flt.json",
                "mech_thor": "mech_thor.flt.json",
                "mech_shadowcat": "mech_shadowcat.flt.json",
                "mech_vulture": "mech_vulture.flt.json",
                "mech_daishi": "mech_daishi.flt.json",
            }
            for k, arc_name in mech_targets.items():
                if arc_name in z.namelist():
                    data = json.loads(z.read(arc_name).decode("utf-8"))
                    mesh = extract_mech_data(data)
                    assets[k] = mesh
                    print(
                        f"  [OK] Extracted {k}: {len(mesh['vertices'])} verts, {len(mesh['faces'])} faces"
                    )
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(assets), encoding="utf-8")
    print(
        f"\nSaved {len(assets)} in-game 3D assets to {OUTPUT_JSON} ({OUTPUT_JSON.stat().st_size} bytes)"
    )


if __name__ == "__main__":
    main()
