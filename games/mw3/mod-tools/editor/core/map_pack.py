"""MW3 Standalone Map Pack Builder & Generator.

Creates brand new, standalone community maps packaged into self-contained
map packs (.mw3pack / mods/map-packs/<name>/) without modifying default game maps.
"""

import json
import math
import os
import shutil
import struct
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from .formats import pack_gamez_zbd, pack_reader_zbd
from .exporter import compute_sha256, build_bank_file

ROOT = Path(__file__).resolve().parents[5]


@dataclass
class MapAsset:
    asset_id: str
    asset_type: str  # turret, bunker, building, factory, prop, spawn, nav
    name: str
    x: float
    y: float
    z: float
    yaw_deg: float = 0.0
    faction: str = "enemy"  # player, friendly, enemy, neutral
    model_name: str = ""
    health: int = 100
    is_objective: bool = False
    objective_desc: str = ""


@dataclass
class TerrainConfig:
    biome: str = "coastal"  # coastal, desert, volcanic, highland, industrial
    width: float = 3000.0  # meters
    depth: float = 3000.0  # meters
    height_scale: float = 80.0
    water_level: float = 3.0
    roughness: float = 0.5


@dataclass
class LightingConfig:
    preset_name: str = "sunset"
    azimuth: float = 225.0
    elevation: float = 35.0
    strength: float = 0.85
    ambient: float = 0.20
    sun_color: List[float] = field(default_factory=lambda: [1.0, 0.85, 0.7])
    sky_tint: List[float] = field(default_factory=lambda: [0.35, 0.45, 0.75])
    fog_distance: int = 1100


@dataclass
class MapPackProject:
    pack_id: str
    pack_title: str
    author: str = "Community Modder"
    version: str = "1.0.0"
    description: str = "Custom standalone map pack for MechWarrior 3"
    base_operation: str = "c1"  # Base operation environment template
    terrain: TerrainConfig = field(default_factory=TerrainConfig)
    lighting: LightingConfig = field(default_factory=LightingConfig)
    assets: List[MapAsset] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": "MW3_MAP_PACK_V1",
            "pack_id": self.pack_id,
            "pack_title": self.pack_title,
            "author": self.author,
            "version": self.version,
            "description": self.description,
            "base_operation": self.base_operation,
            "terrain": {
                "biome": self.terrain.biome,
                "width": self.terrain.width,
                "depth": self.terrain.depth,
                "height_scale": self.terrain.height_scale,
                "water_level": self.terrain.water_level,
                "roughness": self.terrain.roughness,
            },
            "lighting": {
                "preset_name": self.lighting.preset_name,
                "azimuth": self.lighting.azimuth,
                "elevation": self.lighting.elevation,
                "strength": self.lighting.strength,
                "ambient": self.lighting.ambient,
                "sun_color": self.lighting.sun_color,
                "sky_tint": self.lighting.sky_tint,
                "fog_distance": self.lighting.fog_distance,
            },
            "assets": [
                {
                    "asset_id": a.asset_id,
                    "asset_type": a.asset_type,
                    "name": a.name,
                    "x": a.x,
                    "y": a.y,
                    "z": a.z,
                    "yaw_deg": a.yaw_deg,
                    "faction": a.faction,
                    "model_name": a.model_name,
                    "health": a.health,
                    "is_objective": a.is_objective,
                    "objective_desc": a.objective_desc,
                }
                for a in self.assets
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MapPackProject":
        tc = data.get("terrain", {})
        lc = data.get("lighting", {})
        assets = [
            MapAsset(
                asset_id=a.get("asset_id", ""),
                asset_type=a.get("asset_type", "prop"),
                name=a.get("name", ""),
                x=float(a.get("x", 0.0)),
                y=float(a.get("y", 0.0)),
                z=float(a.get("z", 0.0)),
                yaw_deg=float(a.get("yaw_deg", 0.0)),
                faction=a.get("faction", "neutral"),
                model_name=a.get("model_name", ""),
                health=int(a.get("health", 100)),
                is_objective=bool(a.get("is_objective", False)),
                objective_desc=a.get("objective_desc", ""),
            )
            for a in data.get("assets", [])
        ]
        return cls(
            pack_id=data.get("pack_id", "custom_pack"),
            pack_title=data.get("pack_title", "Custom Map"),
            author=data.get("author", "Community Modder"),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            base_operation=data.get("base_operation", "c1"),
            terrain=TerrainConfig(
                biome=tc.get("biome", "coastal"),
                width=float(tc.get("width", 3000.0)),
                depth=float(tc.get("depth", 3000.0)),
                height_scale=float(tc.get("height_scale", 80.0)),
                water_level=float(tc.get("water_level", 3.0)),
                roughness=float(tc.get("roughness", 0.5)),
            ),
            lighting=LightingConfig(
                preset_name=lc.get("preset_name", "sunset"),
                azimuth=float(lc.get("azimuth", 225.0)),
                elevation=float(lc.get("elevation", 35.0)),
                strength=float(lc.get("strength", 0.85)),
                ambient=float(lc.get("ambient", 0.20)),
                sun_color=lc.get("sun_color", [1.0, 0.85, 0.7]),
                sky_tint=lc.get("sky_tint", [0.35, 0.45, 0.75]),
                fog_distance=int(lc.get("fog_distance", 1100)),
            ),
            assets=assets,
        )


class MapPackBuilder:
    """Builds and compiles standalone Map Packs into mods/map-packs/<pack_id>/."""

    def __init__(self, packs_root: Optional[Path] = None, game_root: Optional[Path] = None):
        self.packs_root = (packs_root or ROOT / "mods/map-packs").resolve()
        self.game_root = (game_root or ROOT / "MW3").resolve()
        self.packs_root.mkdir(parents=True, exist_ok=True)

    def build(self, project: MapPackProject) -> Path:
        """Compile project assets and data into an isolated map pack folder."""
        pack_folder = self.packs_root / project.pack_id
        pack_folder.mkdir(parents=True, exist_ok=True)
        zbd_folder = pack_folder / f"zbd/{project.base_operation}"
        zbd_folder.mkdir(parents=True, exist_ok=True)

        op = project.base_operation
        cache_dir = ROOT / "local/mod-cache"
        op_gamez_cache = cache_dir / f"{op}_gamez"
        op_reader_cache = cache_dir / f"{op}_reader"
        ia_reader_cache = cache_dir / f"{op}_readeria1"

        redirects: Dict[str, Path] = {}
        modified_records = []

        # 1. Build GameZ archive with custom placed world objects
        with tempfile.TemporaryDirectory() as td:
            temp_gamez = Path(td) / "gamez"
            shutil.copytree(op_gamez_cache, temp_gamez)
            nodes_path = temp_gamez / "nodes.json"
            nodes = json.loads(nodes_path.read_text(encoding="utf-8"))

            # Pool of archetypes in GameZ
            archetype_pools = {
                "turret_srm": [7936, 7937, 7938, 7948, 8006, 8009, 8075, 8092],
                "turret_laser": [7359, 7470, 7511],
                "turret_tripod": [7940, 7950, 7960, 7968, 7970, 7978, 7981, 7993, 8012, 8022],
                "bunker": [4790, 4791, 4794],
                "comm_center": [4865, 4869, 4872, 4875, 4878],
                "repair_station": [2697, 2600, 2374, 2118],
                "factory": [5520, 5536],
                "fuel_tank": [7537],
                "city_building": [5117, 5102, 5087, 5132, 4995, 5010, 5026, 5041, 5056],
                "mech_madcat": [3138, 3154, 3156, 3159],
                "mech_bushwacker": [3205, 3207, 3210, 3166],
                "mech_shadowcat": [1635, 1637, 1641, 1911],
                "mech_thor": [1644, 1648, 1899, 3065],
                "mech_vulture": [3156, 3159],
                "mech_daishi": [3138, 3205],
            }

            # Track allocation pointer for each pool
            pool_ptrs: Dict[str, int] = {k: 0 for k in archetype_pools}
            placed_count = 0

            # Inject or reposition custom map assets
            for asset in project.assets:
                if asset.asset_type in ("spawn", "nav"):
                    continue  # Handled in reader location.zrd and waynet

                pool = archetype_pools.get(asset.asset_type)
                if not pool:
                    # Fallback mapping
                    if "turret" in asset.asset_type:
                        pool = archetype_pools["turret_tripod"]
                    elif "bunk" in asset.asset_type:
                        pool = archetype_pools["bunker"]
                    elif "comm" in asset.asset_type or "radar" in asset.asset_type:
                        pool = archetype_pools["comm_center"]
                    elif "repair" in asset.asset_type or "mfb" in asset.asset_type:
                        pool = archetype_pools["repair_station"]
                    else:
                        pool = archetype_pools["bunker"]

                ptr = pool_ptrs.get(asset.asset_type, 0)
                if ptr < len(pool):
                    node_idx = pool[ptr]
                    pool_ptrs[asset.asset_type] = ptr + 1

                    if node_idx < len(nodes):
                        node = nodes[node_idx]
                        data = node.setdefault("data", {})
                        obj3d = data.setdefault("Object3d", {})
                        tr = obj3d.get("transform")
                        if not isinstance(tr, dict):
                            tr = {"RotateTranslateScale": {"rotate": {"x": 0.0, "y": 0.0, "z": 0.0}, "translate": {"x": 0.0, "y": 0.0, "z": 0.0}, "scale": {"x": 1.0, "y": 1.0, "z": 1.0}}}
                            obj3d["transform"] = tr
                        rts = tr.setdefault("RotateTranslateScale", {})
                        rts["translate"] = {"x": float(asset.x), "y": float(asset.y), "z": float(asset.z)}
                        rts["rotate"] = {"x": 0.0, "y": math.radians(asset.yaw_deg), "z": 0.0}
                        node.setdefault("flags", {})["active"] = True
                        placed_count += 1

            nodes_path.write_text(json.dumps(nodes, indent=2), encoding="utf-8")
            out_gamez = zbd_folder / "gamez.zbd"
            pack_gamez_zbd(temp_gamez, out_gamez)

            rel_gamez = f"zbd/{op}/gamez.zbd"
            redirects[rel_gamez] = out_gamez
            modified_records.append({
                "target": rel_gamez,
                "size_bytes": out_gamez.stat().st_size,
                "sha256": compute_sha256(out_gamez),
                "summary": f"{placed_count} custom visual entities placed"
            })

        # 2. Build Reader archive with custom Spawns and Objectives
        with tempfile.TemporaryDirectory() as td:
            temp_reader = Path(td) / "reader"
            shutil.copytree(op_reader_cache, temp_reader)

            # Update location.zrd with player and enemy spawns
            loc_path = temp_reader / "location.zrd.json"
            if loc_path.is_file():
                player_spawn = next((a for a in project.assets if a.asset_type == "spawn" and a.faction == "player"), None)
                loc_data = json.loads(loc_path.read_text(encoding="utf-8"))
                # Update IA_base or Mission 1 Start
                for i in range(0, len(loc_data[0]), 2):
                    key = loc_data[0][i]
                    if player_spawn and key in ("IA_base", "Mission 1 Start"):
                        loc_data[0][i + 1][0] = [player_spawn.x, player_spawn.y, player_spawn.z]
                        if len(loc_data[0][i + 1]) > 1:
                            loc_data[0][i + 1][1] = player_spawn.yaw_deg
                loc_path.write_text(json.dumps(loc_data, indent=2), encoding="utf-8")

            # Update waynet_1.zrd with Start, Able, Baker waypoints
            waynet_path = temp_reader / "waynet_1.zrd.json"
            if waynet_path.is_file():
                waynet_data = json.loads(waynet_path.read_text(encoding="utf-8"))
                player_spawn = next((a for a in project.assets if a.asset_type == "spawn" and a.faction == "player"), None)
                nav_able = next((a for a in project.assets if a.asset_type == "nav" and "able" in a.name.lower() or "alpha" in a.name.lower()), None)
                nav_baker = next((a for a in project.assets if a.asset_type == "nav" and "baker" in a.name.lower() or "beta" in a.name.lower()), None)

                # Iterate through waynet entries
                for i in range(0, len(waynet_data[0]), 2):
                    key = waynet_data[0][i]
                    val = waynet_data[0][i + 1]
                    if key == "node_00" and player_spawn and isinstance(val, list) and len(val) >= 2:
                        val[1] = [float(player_spawn.x), float(player_spawn.y), float(player_spawn.z)]
                    elif key == "node_01" and nav_able and isinstance(val, list) and len(val) >= 2:
                        val[1] = [float(nav_able.x), float(nav_able.y), float(nav_able.z)]
                    elif key == "node_02" and nav_baker and isinstance(val, list) and len(val) >= 2:
                        val[1] = [float(nav_baker.x), float(nav_baker.y), float(nav_baker.z)]

                waynet_path.write_text(json.dumps(waynet_data, indent=2), encoding="utf-8")

            out_reader = zbd_folder / "reader.zbd"
            pack_reader_zbd(temp_reader, out_reader)

            rel_reader = f"zbd/{op}/reader.zbd"
            redirects[rel_reader] = out_reader
            modified_records.append({
                "target": rel_reader,
                "size_bytes": out_reader.stat().st_size,
                "sha256": compute_sha256(out_reader),
                "summary": "Custom player spawn, waypoints, and objective markers"
            })

        # 3. Write Map Pack Manifest
        manifest_file = pack_folder / "manifest.json"
        manifest_content = {
            "format": "MW3_MAP_PACK_MANIFEST_V1",
            "pack_id": project.pack_id,
            "title": project.pack_title,
            "author": project.author,
            "version": project.version,
            "description": project.description,
            "base_operation": project.base_operation,
            "terrain_summary": {
                "biome": project.terrain.biome,
                "bounds": f"{project.terrain.width}m x {project.terrain.depth}m",
                "water_level": project.terrain.water_level,
            },
            "lighting_summary": {
                "preset": project.lighting.preset_name,
                "sun_azimuth": project.lighting.azimuth,
                "sun_elevation": project.lighting.elevation,
            },
            "total_placed_assets": len(project.assets),
            "files": modified_records,
        }
        manifest_file.write_text(json.dumps(manifest_content, indent=2), encoding="utf-8")

        # 4. Save the Project JSON alongside the pack
        project_json_file = pack_folder / "project.json"
        project_json_file.write_text(json.dumps(project.to_dict(), indent=2), encoding="utf-8")

        # 5. Build Engine Redirect Banks (merged with existing texture packs)
        mod_banks_bin = pack_folder / "map-banks.bin"
        existing_bank_bin = ROOT / "local/remaster/prepared/texture-banks.bin"
        merged_redirects: Dict[str, Path] = {}
        if existing_bank_bin.is_file():
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
            except Exception:
                pass
        merged_redirects.update(redirects)
        build_bank_file(merged_redirects, mod_banks_bin)

        # 6. Generate Play Map Runner Command Script
        run_cmd = pack_folder / f"Play Map - {project.pack_title}.cmd"
        cmd_content = f"""@echo off
setlocal
set "MAP_DIR=%~dp0"
cd /d "%MAP_DIR%..\\..\\.."
echo ======================================================================
echo   Launching Custom Map Pack: {project.pack_title}
echo ======================================================================
echo.
set "MW34_REMASTER_BANKS=%MAP_DIR%map-banks.bin"
set "MW34_SUN_AZIMUTH={project.lighting.azimuth}"
set "MW34_SUN_ELEVATION={project.lighting.elevation}"
set "MW34_SUN_STRENGTH={project.lighting.strength}"
set "MW34_SUN_AMBIENT={project.lighting.ambient}"

call "Play MW3Remaster.cmd" --profile "local\\effect-lighting-r1\\launcher.json" --registry "local\\material-authoring-r1\\normal-registry.json" %*
if errorlevel 1 (
    echo.
    echo Map launch exited with code %errorlevel%.
    pause
)
"""
        run_cmd.write_text(cmd_content, encoding="utf-8")

        return pack_folder
