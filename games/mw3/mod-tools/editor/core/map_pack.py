"""Prototype map edits against existing locally extracted operation archives.

The browser project contains terrain/lighting previews and requested placements.
The exporter currently repositions a bounded pool of existing GameZ nodes and
updates selected reader locations; it does not synthesize the preview terrain
or implement every requested gameplay property. Outputs are local derived game
data, not self-contained redistributable maps. Original archives remain read-only.
"""

import json
import math
import os
import re
import shutil
import struct
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from .formats import pack_gamez_zbd, pack_reader_zbd
from .exporter import compute_sha256, build_bank_file
from .environment import EnvironmentConfig, encode_mw34env1, get_environment_preset
from ..config import cache_directory, game_directory

ROOT = Path(__file__).resolve().parents[5]


def pack_directory(packs_root: Path, pack_id: str) -> Path:
    """Resolve one pack, including existing symlinks, within its owned directory."""
    if not isinstance(pack_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", pack_id):
        raise ValueError("Pack ID must be 1–64 ASCII letters, digits, hyphens or underscores.")
    root = packs_root.resolve()
    destination = (root / pack_id).resolve()
    if not destination.is_relative_to(root):
        raise ValueError("Pack directory resolves outside the packs folder.")
    return destination


@dataclass
class MapAsset:
    """Browser placement request; not every field is currently applied to game data."""

    asset_id: str
    asset_type: str  # turret, bunker, building, factory, prop, spawn, nav, trig_*
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
    trigger_radius: float = 40.0
    trigger_action: str = ""
    trigger_message: str = ""
    trigger_audio: str = "betty_alarm"
    height_offset: float = 0.0
    ai_skill: str = "regular"  # green, regular, veteran, elite
    ai_stance: str = "guard"  # guard, patrol, ambush, free_fire
    ai_range: str = "medium"  # short, medium, long
    ai_retreat_health: int = 15


@dataclass
class TerrainConfig:
    """Preview terrain parameters in metres; stored in the project/summary only."""

    biome: str = "coastal"  # coastal, desert, volcanic, highland, industrial
    width: float = 3000.0  # meters
    depth: float = 3000.0  # meters
    height_scale: float = 80.0
    water_level: float = 3.0
    roughness: float = 0.5
    height_modifications: Dict[str, float] = field(default_factory=dict)


LightingConfig = EnvironmentConfig


@dataclass
class MapPackProject:
    """Serializable preview scene and requested edits to one base operation."""

    pack_id: str
    pack_title: str
    author: str = "Community Modder"
    version: str = "1.0.0"
    description: str = "Custom standalone map pack for MechWarrior 3"
    base_operation: str = "c1"  # Base operation environment template
    terrain: TerrainConfig = field(default_factory=TerrainConfig)
    lighting: LightingConfig = field(default_factory=LightingConfig)
    assets: List[MapAsset] = field(default_factory=list)
    objectives: Dict[str, Any] = field(default_factory=lambda: {
        "primary": [
            {"id": "obj_pri_1", "desc": "Neutralize Clan Smoke Jaguar defenders", "target": "any_enemy", "completed": False},
            {"id": "obj_pri_2", "desc": "Proceed to designated Extraction Zone", "target": "trig_evac", "completed": False}
        ],
        "secondary": [
            {"id": "obj_sec_1", "desc": "Destroy auxiliary fuel storage silos", "target": "fuel_tank", "completed": False}
        ],
        "briefing_text": "Satellite recon has confirmed hostile Clan Smoke Jaguar activity in this sector. Neutralize all perimeter defenses and eliminate the patrol lance before proceeding to extraction.",
        "audio_track": "action_theme_1",
    })
    drop_config: Dict[str, Any] = field(default_factory=lambda: {
        "player_mech": "mech_madcat",
        "drop_type": "orbital_drop_pod",
        "tonnage": 75.0,
        "armor_tons": 14.0,
        "heatsinks": 16,
        "jump_jets": 0,
        "weapons": {
            "left_arm": "ER PPC",
            "right_arm": "ER PPC",
            "left_torso": "Clan LRM-20",
            "right_torso": "Clan LRM-20",
            "center_torso": "Medium Pulse Laser"
        },
        "lancemates": [
            {"name": "Lt. Alan Mattila", "mech": "mech_bushwacker", "orders": "escort"},
            {"name": "Sgt. Epona Rhi", "mech": "mech_shadowcat", "orders": "free_fire"}
        ]
    })

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
                "height_modifications": self.terrain.height_modifications,
            },
            "lighting": self.lighting.to_dict(),
            "objectives": self.objectives,
            "drop_config": self.drop_config,
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
                    "trigger_radius": a.trigger_radius,
                    "trigger_action": a.trigger_action,
                    "trigger_message": a.trigger_message,
                    "trigger_audio": a.trigger_audio,
                    "height_offset": a.height_offset,
                    "ai_skill": a.ai_skill,
                    "ai_stance": a.ai_stance,
                    "ai_range": a.ai_range,
                    "ai_retreat_health": a.ai_retreat_health,
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
                trigger_radius=float(a.get("trigger_radius", 40.0)),
                trigger_action=a.get("trigger_action", ""),
                trigger_message=a.get("trigger_message", ""),
                trigger_audio=a.get("trigger_audio", "betty_alarm"),
                height_offset=float(a.get("height_offset", 0.0)),
                ai_skill=a.get("ai_skill", "regular"),
                ai_stance=a.get("ai_stance", "guard"),
                ai_range=a.get("ai_range", "medium"),
                ai_retreat_health=int(a.get("ai_retreat_health", 15)),
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
                height_modifications=tc.get("height_modifications", {}),
            ),
            lighting=EnvironmentConfig.from_dict(lc) if isinstance(lc, dict) else EnvironmentConfig(),
            objectives=data.get("objectives", {
                "primary": [
                    {"id": "obj_pri_1", "desc": "Neutralize Clan Smoke Jaguar defenders", "target": "any_enemy", "completed": False},
                    {"id": "obj_pri_2", "desc": "Proceed to designated Extraction Zone", "target": "trig_evac", "completed": False}
                ],
                "secondary": [
                    {"id": "obj_sec_1", "desc": "Destroy auxiliary fuel storage silos", "target": "fuel_tank", "completed": False}
                ],
                "briefing_text": "Satellite recon has confirmed hostile Clan Smoke Jaguar activity in this sector. Neutralize all perimeter defenses and eliminate the patrol lance before proceeding to extraction.",
                "audio_track": "action_theme_1",
            }),
            drop_config=data.get("drop_config", {
                "player_mech": "mech_madcat",
                "drop_type": "orbital_drop_pod",
                "tonnage": 75.0,
                "armor_tons": 14.0,
                "heatsinks": 16,
                "jump_jets": 0,
                "weapons": {
                    "left_arm": "ER PPC",
                    "right_arm": "ER PPC",
                    "left_torso": "Clan LRM-20",
                    "right_torso": "Clan LRM-20",
                    "center_torso": "Medium Pulse Laser"
                },
                "lancemates": [
                    {"name": "Lt. Alan Mattila", "mech": "mech_bushwacker", "orders": "escort"},
                    {"name": "Sgt. Epona Rhi", "mech": "mech_shadowcat", "orders": "free_fire"}
                ]
            }),
            assets=assets,
        )


class MapPackBuilder:
    """Write prototype archive overrides under one owned pack directory.

    The fixed archetype pools below are source-node indices, not a general object
    factory. See the code/provenance review for known capacity/aliasing limits.
    Existing packs are updated incrementally; a failed build can leave partial files.
    """

    def __init__(self, packs_root: Optional[Path] = None, game_root: Optional[Path] = None):
        self.packs_root = (packs_root or ROOT / "mods/map-packs").resolve()
        self.game_root = (game_root or game_directory()).resolve()
        self.packs_root.mkdir(parents=True, exist_ok=True)

    def build(self, project: MapPackProject) -> Path:
        """Compile project assets and data into an isolated map pack folder."""
        pack_folder = pack_directory(self.packs_root, project.pack_id)
        if project.base_operation not in {"c1", "c2", "c3", "c4", "c4b", "t1"}:
            raise ValueError("Unsupported base operation; select an installed MW3 operation.")
        # These values enter a CMD launcher. Require real finite numbers before
        # creating any files; labels and arbitrary strings never become shell text.
        for value in (
            project.lighting.azimuth,
            project.lighting.elevation,
            project.lighting.strength,
            project.lighting.ambient,
        ):
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError("Launcher lighting values must be finite numbers.")
        pack_folder.mkdir(parents=True, exist_ok=True)
        zbd_folder = pack_folder / f"zbd/{project.base_operation}"
        zbd_folder.mkdir(parents=True, exist_ok=True)

        op = project.base_operation
        cache_dir = cache_directory()
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
                "bridge_span": [5715, 5746, 5759, 5768],
                "ramp": [4278, 5215],
                "dock": [4343, 4383, 4423, 4463],
                "defense_wall": [2720, 2729, 2704, 2762],
                "security_gate": [7525],
                "powerline_pole": [8303, 8320, 8321, 8438, 8455],
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
                            tr = {
                                "RotateTranslateScale": {
                                    "rotate": {"x": 0.0, "y": 0.0, "z": 0.0},
                                    "translate": {"x": 0.0, "y": 0.0, "z": 0.0},
                                    "scale": {"x": 1.0, "y": 1.0, "z": 1.0},
                                }
                            }
                            obj3d["transform"] = tr
                        rts = tr.setdefault("RotateTranslateScale", {})
                        rts["translate"] = {
                            "x": float(asset.x),
                            "y": float(asset.y),
                            "z": float(asset.z),
                        }
                        rts["rotate"] = {"x": 0.0, "y": math.radians(asset.yaw_deg), "z": 0.0}
                        node.setdefault("flags", {})["active"] = True
                        placed_count += 1

            nodes_path.write_text(json.dumps(nodes, indent=2), encoding="utf-8")
            out_gamez = zbd_folder / "gamez.zbd"
            pack_gamez_zbd(temp_gamez, out_gamez)

            rel_gamez = f"zbd/{op}/gamez.zbd"
            redirects[rel_gamez] = out_gamez
            modified_records.append(
                {
                    "target": rel_gamez,
                    "size_bytes": out_gamez.stat().st_size,
                    "sha256": compute_sha256(out_gamez),
                    "summary": f"{placed_count} custom visual entities placed",
                }
            )

        # 2. Build Reader archive with custom Spawns and Objectives
        with tempfile.TemporaryDirectory() as td:
            temp_reader = Path(td) / "reader"
            shutil.copytree(op_reader_cache, temp_reader)

            # Update location.zrd with player and enemy spawns
            loc_path = temp_reader / "location.zrd.json"
            if loc_path.is_file():
                player_spawn = next(
                    (
                        a
                        for a in project.assets
                        if a.asset_type == "spawn" and a.faction == "player"
                    ),
                    None,
                )
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
                player_spawn = next(
                    (
                        a
                        for a in project.assets
                        if a.asset_type == "spawn" and a.faction == "player"
                    ),
                    None,
                )
                nav_able = next(
                    (
                        a
                        for a in project.assets
                        if a.asset_type == "nav"
                        and "able" in a.name.lower()
                        or "alpha" in a.name.lower()
                    ),
                    None,
                )
                nav_baker = next(
                    (
                        a
                        for a in project.assets
                        if a.asset_type == "nav"
                        and "baker" in a.name.lower()
                        or "beta" in a.name.lower()
                    ),
                    None,
                )

                # Iterate through waynet entries
                for i in range(0, len(waynet_data[0]), 2):
                    key = waynet_data[0][i]
                    val = waynet_data[0][i + 1]
                    if (
                        key == "node_00"
                        and player_spawn
                        and isinstance(val, list)
                        and len(val) >= 2
                    ):
                        val[1] = [
                            float(player_spawn.x),
                            float(player_spawn.y),
                            float(player_spawn.z),
                        ]
                    elif key == "node_01" and nav_able and isinstance(val, list) and len(val) >= 2:
                        val[1] = [float(nav_able.x), float(nav_able.y), float(nav_able.z)]
                    elif key == "node_02" and nav_baker and isinstance(val, list) and len(val) >= 2:
                        val[1] = [float(nav_baker.x), float(nav_baker.y), float(nav_baker.z)]

                waynet_path.write_text(json.dumps(waynet_data, indent=2), encoding="utf-8")

            out_reader = zbd_folder / "reader.zbd"
            pack_reader_zbd(temp_reader, out_reader)

            rel_reader = f"zbd/{op}/reader.zbd"
            redirects[rel_reader] = out_reader
            modified_records.append(
                {
                    "target": rel_reader,
                    "size_bytes": out_reader.stat().st_size,
                    "sha256": compute_sha256(out_reader),
                    "summary": "Custom player spawn, waypoints, and objective markers",
                }
            )

        # 3. Write Map Pack Manifest
        manifest_file = pack_folder / "manifest.json"
        triggers_list = [
            {
                "asset_id": a.asset_id,
                "type": a.asset_type,
                "name": a.name,
                "x": a.x,
                "y": a.y,
                "z": a.z,
                "radius": a.trigger_radius,
                "action": a.trigger_action,
                "message": a.trigger_message,
            }
            for a in project.assets
            if a.asset_type.startswith("trig_")
        ]
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
                "time_of_day": project.lighting.time_of_day,
                "sun_azimuth": project.lighting.azimuth,
                "sun_elevation": project.lighting.elevation,
                "weather": {
                    "rain": project.lighting.rain_intensity,
                    "wetness": project.lighting.wet_reflection,
                    "lightning": project.lighting.has_lightning,
                    "dust": project.lighting.dust_intensity,
                    "smog": project.lighting.smog_intensity,
                    "is_interior": project.lighting.is_interior,
                },
            },
            "objectives_summary": {
                "primary_count": len(project.objectives.get("primary", [])),
                "secondary_count": len(project.objectives.get("secondary", [])),
                "triggers_count": len(triggers_list),
            },
            "drop_summary": {
                "mech": project.drop_config.get("player_mech", "mech_madcat"),
                "drop_type": project.drop_config.get("drop_type", "orbital_drop_pod"),
                "lance_size": 1 + len(project.drop_config.get("lancemates", [])),
            },
            "total_placed_assets": len(project.assets),
            "files": modified_records,
        }
        manifest_file.write_text(json.dumps(manifest_content, indent=2), encoding="utf-8")

        # 4. Save Project, Objectives, and Drop Config JSONs
        project_json_file = pack_folder / "project.json"
        project_json_file.write_text(json.dumps(project.to_dict(), indent=2), encoding="utf-8")

        objectives_data = dict(project.objectives)
        objectives_data["triggers"] = triggers_list
        objectives_file = pack_folder / "objectives.json"
        objectives_file.write_text(json.dumps(objectives_data, indent=2), encoding="utf-8")

        drop_config_file = pack_folder / "drop_config.json"
        drop_config_file.write_text(json.dumps(project.drop_config, indent=2), encoding="utf-8")

        # 5. Compile MW34ENV1 Native Binary Lighting & Weather Catalog
        env_file = pack_folder / "environment.json"
        env_file.write_text(json.dumps(project.lighting.to_dict(), indent=2), encoding="utf-8")

        mission_lighting_bin = pack_folder / "mission-lighting.bin"
        mission_ident = f"{project.base_operation}m1"
        try:
            raw_env_bytes = encode_mw34env1(mission_ident, project.lighting)
            mission_lighting_bin.write_bytes(raw_env_bytes)
            modified_records.append({
                "target": "mission-lighting.bin",
                "size_bytes": len(raw_env_bytes),
                "sha256": compute_sha256(mission_lighting_bin),
                "summary": f"MW34ENV1 binary catalog ({project.lighting.preset_name}, ToD {project.lighting.time_of_day:.1f}h)",
            })
        except Exception as e:
            print(f"Warning: could not encode MW34ENV1 catalog: {e}")

        # 6. Generate Tactical Briefing Text Dossier
        briefing_file = pack_folder / "briefing.txt"
        pri_objs = "\n".join(f"  [ ] {i+1}. {o.get('desc', '')}" for i, o in enumerate(project.objectives.get("primary", [])))
        sec_objs = "\n".join(f"  [ ] {i+1}. {o.get('desc', '')}" for i, o in enumerate(project.objectives.get("secondary", [])))
        weapons_summary = "\n".join(f"    - {k.replace('_', ' ').title()}: {v}" for k, v in project.drop_config.get("weapons", {}).items())
        lance_summary = "\n".join(f"    - {m.get('name', '')}: {m.get('mech', '')} ({m.get('orders', '')})" for m in project.drop_config.get("lancemates", []))

        briefing_content = f"""======================================================================
MECHWARRIOR 3: COMBAT MISSION BRIEFING DOSSIER
OPERATION: {project.base_operation.upper()}  |  MAP PACK: {project.pack_id}
AUTHOR: {project.author}  |  VERSION: {project.version}
======================================================================

MISSION TITLE:
  {project.pack_title}

INTEL BRIEFING:
  {project.objectives.get('briefing_text', project.description)}

PRIMARY OBJECTIVES:
{pri_objs if pri_objs else '  - None specified'}

SECONDARY OBJECTIVES:
{sec_objs if sec_objs else '  - None specified'}

DROP FORCE & COMBAT CONFIGURATION:
  Player Chassis: {project.drop_config.get('player_mech', 'mech_madcat')} ({project.drop_config.get('tonnage', 75)}T)
  Insertion Type: {project.drop_config.get('drop_type', 'orbital_drop_pod')}
  Armor: {project.drop_config.get('armor_tons', 14)} Tons | Heat Sinks: {project.drop_config.get('heatsinks', 16)} | Jump Jets: {project.drop_config.get('jump_jets', 0)}
  Weapon Hardpoints:
{weapons_summary if weapons_summary else '    - Standard Loadout'}
  Lancemate Support:
{lance_summary if lance_summary else '    - Solo Drop (No lancemates)'}
======================================================================
"""
        briefing_file.write_text(briefing_content, encoding="utf-8")

        # 6. Build Engine Redirect Banks (merged with existing texture packs)
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
                        alen, blen = struct.unpack("<II", bdata[cur : cur + 8])
                        cur += 8
                        akey = bdata[cur : cur + alen].decode("ascii")
                        cur += alen
                        bval = bdata[cur : cur + blen].decode("ascii")
                        cur += blen
                        merged_redirects[akey] = Path(bval)
            except Exception:
                pass
        merged_redirects.update(redirects)
        build_bank_file(merged_redirects, mod_banks_bin)

        # 8. Generate Play Map Runner Command Script
        run_cmd = pack_folder / f"Play Map - {project.pack_id}.cmd"
        cmd_content = f"""@echo off
setlocal
set "MAP_DIR=%~dp0"
cd /d "%MAP_DIR%..\\..\\.."
echo ======================================================================
echo   MECHWARRIOR 3 - CUSTOM MISSION LAUNCH
echo   Map Title: {project.pack_title} [{project.pack_id}]
echo   Operation: {project.base_operation.upper()} | Biome: {project.terrain.biome}
echo   Atmosphere: {project.lighting.preset_name.upper()} | Time: {project.lighting.time_of_day:.1f}h
echo ======================================================================
echo.
type "%MAP_DIR%briefing.txt"
echo.
echo Initializing native Vulkan engine redirect banks and atmosphere...
set "MW34_REMASTER_BANKS=%MAP_DIR%map-banks.bin"
set "MW34_MISSION_ENVIRONMENTS=%MAP_DIR%mission-lighting.bin"
set "MW34_WEATHER=1"
set "MW34_SUN_AZIMUTH={project.lighting.azimuth}"
set "MW34_SUN_ELEVATION={project.lighting.elevation}"
set "MW34_SUN_STRENGTH={project.lighting.sun_strength}"
set "MW34_SUN_AMBIENT={project.lighting.ambient_strength}"

call "launchers\\Play MW3Remaster.cmd" --profile "local\\effect-lighting-r1\\launcher.json" --registry "local\\material-authoring-r1\\normal-registry.json" %*
if errorlevel 1 (
    echo.
    echo Map launch exited with code %errorlevel%.
    pause
)
"""
        run_cmd.write_text(cmd_content, encoding="utf-8")

        return pack_folder
