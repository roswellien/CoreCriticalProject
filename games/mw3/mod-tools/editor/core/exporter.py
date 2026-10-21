"""Mod Exporter.

Packages an authored mod into an isolated local mod directory,
repacking modified archives with byte-exact precision, writing manifests,
and generating engine redirect bank files without touching the base installation.
"""

import hashlib
import json
import os
import shutil
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from .formats import pack_gamez_zbd, pack_reader_zbd
from .mission_loader import MissionData
from .project import ModProject

ROOT = Path(__file__).resolve().parents[5]


def compute_sha256(path: Path) -> str:
    """Compute lowercase SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def build_bank_file(redirects: Dict[str, Path], output_bin: Path) -> Path:
    """Build binary MW34_REMASTER_BANKS redirect file.

    Format:
      Magic: "MWBANK1\\0" (8 bytes)
      Count: uint32 (number of redirected targets)
      For each entry:
        key_len: uint32
        val_len: uint32
        key: ASCII string (e.g. "zbd/c1/gamez.zbd")
        val: ASCII absolute path string
    """
    output_bin.parent.mkdir(parents=True, exist_ok=True)
    out = bytearray(b"MWBANK1\0" + struct.pack("<I", len(redirects)))
    for key, target_path in redirects.items():
        k_bytes = key.replace("\\", "/").encode("ascii")
        v_bytes = str(target_path.resolve()).encode("ascii")
        out.extend(struct.pack("<II", len(k_bytes), len(v_bytes)))
        out.extend(k_bytes)
        out.extend(v_bytes)
    output_bin.write_bytes(out)
    return output_bin


@dataclass
class ExportReceipt:
    mod_dir: Path
    manifest_path: Path
    redirect_bank_path: Path
    modified_files: List[Dict[str, Any]]
    run_command: str


class ModExporter:
    """Exports a mod project to an isolated local directory."""

    def __init__(self, output_root: Optional[Path] = None):
        self.output_root = (Path(output_root) if output_root else ROOT / "local/mods").resolve()
        self.output_root.mkdir(parents=True, exist_ok=True)

    def export(self, project: ModProject, mission: MissionData) -> ExportReceipt:
        """Export project deltas into a packaged mod folder."""
        def _safe_rel(p: Path) -> str:
            try:
                return p.resolve().relative_to(ROOT.resolve()).as_posix()
            except ValueError:
                return str(p.resolve())

        # Clean folder name
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project.project_name.lower())
        mod_dir = self.output_root / safe_name
        mod_dir.mkdir(parents=True, exist_ok=True)
        zbd_dest_dir = mod_dir / f"zbd/{mission.operation}"
        zbd_dest_dir.mkdir(parents=True, exist_ok=True)

        modified_files = []
        redirects: Dict[str, Path] = {}

        # 1. Apply GameZ modifications if any object was modified
        if project.modified_objects:
            with tempfile.TemporaryDirectory() as td:
                temp_extract = Path(td) / "gamez_edit"
                # Copy original extracted gamez cache files into temp_extract
                shutil.copytree(mission.raw_nodes_json_path.parent, temp_extract)
                nodes_path = temp_extract / "nodes.json"
                nodes = json.loads(nodes_path.read_text(encoding="utf-8"))

                # Apply object modifications while preserving all other fields
                for node_idx, edits in project.modified_objects.items():
                    if 0 <= node_idx < len(nodes):
                        n = nodes[node_idx]
                        if "name" in edits and edits["name"]:
                            n["name"] = edits["name"]
                        if "active" in edits:
                            n.setdefault("flags", {})["active"] = bool(edits["active"])
                        data = n.setdefault("data", {})
                        if isinstance(data, dict):
                            obj3d = data.setdefault("Object3d", {})
                            if isinstance(obj3d, dict):
                                tr = obj3d.setdefault("transform", {})
                                if isinstance(tr, dict):
                                    rts = tr.setdefault("RotateTranslateScale", {})
                                    if isinstance(rts, dict):
                                        t = rts.setdefault("translate", {})
                                        if "x" in edits: t["x"] = float(edits["x"])
                                        if "y" in edits: t["y"] = float(edits["y"])
                                        if "z" in edits: t["z"] = float(edits["z"])
                                        r = rts.setdefault("rotate", {})
                                        if "rot_y" in edits: r["y"] = float(edits["rot_y"])
                                        elif "yaw_degrees" in edits:
                                            import math
                                            r["y"] = math.radians(float(edits["yaw_degrees"]))

                # Write modified nodes.json
                nodes_path.write_text(json.dumps(nodes, indent=2), encoding="utf-8")

                # Repack to mod directory
                out_gamez = zbd_dest_dir / "gamez.zbd"
                pack_gamez_zbd(temp_extract, out_gamez)

                rel_key = f"zbd/{mission.operation}/gamez.zbd"
                redirects[rel_key] = out_gamez
                orig_gamez = mission.game_root / rel_key
                modified_files.append({
                    "target": rel_key,
                    "exported_path": _safe_rel(out_gamez),
                    "original_sha256": compute_sha256(orig_gamez),
                    "modified_sha256": compute_sha256(out_gamez),
                    "size_bytes": out_gamez.stat().st_size,
                    "changes": f"{len(project.modified_objects)} world objects modified"
                })

        # 2. Apply Spawn modifications if any spawn point was modified
        if project.modified_spawns:
            with tempfile.TemporaryDirectory() as td:
                temp_extract = Path(td) / "reader_edit"
                op_reader_cache = mission.game_root.parent / f"local/mod-cache/{mission.operation}_reader"
                shutil.copytree(op_reader_cache, temp_extract)
                loc_path = temp_extract / "location.zrd.json"
                if loc_path.is_file():
                    loc_data = json.loads(loc_path.read_text(encoding="utf-8"))
                    for i in range(0, len(loc_data[0]), 2):
                        sp_name = loc_data[0][i]
                        if sp_name in project.modified_spawns:
                            sp_edits = project.modified_spawns[sp_name]
                            pos = loc_data[0][i + 1][0]
                            if "x" in sp_edits: pos[0] = float(sp_edits["x"])
                            if "y" in sp_edits: pos[1] = float(sp_edits["y"])
                            if "z" in sp_edits: pos[2] = float(sp_edits["z"])
                            if "yaw_degrees" in sp_edits and len(loc_data[0][i + 1]) > 1:
                                loc_data[0][i + 1][1] = float(sp_edits["yaw_degrees"])
                    loc_path.write_text(json.dumps(loc_data, indent=2), encoding="utf-8")

                    out_reader = zbd_dest_dir / "reader.zbd"
                    pack_reader_zbd(temp_extract, out_reader)

                    rel_key = f"zbd/{mission.operation}/reader.zbd"
                    redirects[rel_key] = out_reader
                    orig_reader = mission.game_root / rel_key
                    modified_files.append({
                        "target": rel_key,
                        "exported_path": _safe_rel(out_reader),
                        "original_sha256": compute_sha256(orig_reader),
                        "modified_sha256": compute_sha256(out_reader),
                        "size_bytes": out_reader.stat().st_size,
                        "changes": f"{len(project.modified_spawns)} spawn points modified"
                    })

        # 3. If nothing was modified (unchanged round-trip export test), export an unchanged gamez.zbd
        if not modified_files:
            out_gamez = zbd_dest_dir / "gamez.zbd"
            with tempfile.TemporaryDirectory() as td:
                temp_extract = Path(td) / "gamez_unmodified"
                shutil.copytree(mission.raw_nodes_json_path.parent, temp_extract)
                pack_gamez_zbd(temp_extract, out_gamez)
            rel_key = f"zbd/{mission.operation}/gamez.zbd"
            redirects[rel_key] = out_gamez
            orig_gamez = mission.game_root / rel_key
            modified_files.append({
                "target": rel_key,
                "exported_path": _safe_rel(out_gamez),
                "original_sha256": compute_sha256(orig_gamez),
                "modified_sha256": compute_sha256(out_gamez),
                "size_bytes": out_gamez.stat().st_size,
                "changes": "Unchanged round-trip export"
            })

        # 4. Write manifest.json
        manifest_path = mod_dir / "manifest.json"
        manifest_data = {
            "name": project.project_name,
            "version": project.version,
            "author": project.author,
            "description": project.description,
            "target_operation": mission.operation,
            "target_mission": mission.mission_id,
            "engine": "MW34Recomp Native Vulkan",
            "modified_files": modified_files,
        }
        manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

        # 5. Build MW34_REMASTER_BANKS redirect file
        # We merge existing prepared texture banks with mod redirects
        existing_bank_bin = ROOT / "local/remaster/prepared/texture-banks.bin"
        mod_bank_bin = mod_dir / "mod-banks.bin"
        merged_redirects: Dict[str, Path] = {}
        if existing_bank_bin.is_file():
            # Read existing entries
            try:
                bdata = existing_bank_bin.read_bytes()
                if bdata.startswith(b"MWBANK1\0"):
                    cnt = struct.unpack("<I", bdata[8:12])[0]
                    cur = 12
                    for _ in range(cnt):
                        alen, blen = struct.unpack("<II", bdata[cur:cur + 8])
                        cur += 8
                        akey = bdata[cur:cur + alen].decode("ascii")
                        cur += alen
                        bval = bdata[cur:cur + blen].decode("ascii")
                        cur += blen
                        merged_redirects[akey] = Path(bval)
            except Exception as e:
                print(f"Warning: could not read existing banks: {e}")
        # Add mod redirects (taking precedence)
        merged_redirects.update(redirects)
        build_bank_file(merged_redirects, mod_bank_bin)

        # 6. Generate Play Mod command script
        cmd_path = mod_dir / "Play-Mod.cmd"
        cmd_script = f"""@echo off
setlocal
cd /d "%~dp0..\\..\\.."
echo Launching MW3 Mod: {project.project_name}...
set "MW34_REMASTER_BANKS=%~dp0mod-banks.bin"
call "Play MW3 - Dynamic Night Lighting Preview.cmd" %*
"""
        cmd_path.write_text(cmd_script, encoding="utf-8")

        run_cmd = f'powershell -ExecutionPolicy Bypass -Command "$env:MW34_REMASTER_BANKS=\'{mod_bank_bin}\'; tools/remaster-launcher/play_native.ps1 -Profile local/effect-lighting-r1/launcher.json"'

        return ExportReceipt(
            mod_dir=mod_dir,
            manifest_path=manifest_path,
            redirect_bank_path=mod_bank_bin,
            modified_files=modified_files,
            run_command=run_cmd,
        )
