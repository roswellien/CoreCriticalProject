"""Mission Data Loader.

Recovers top-down map calibration, terrain bounds, world object placements,
spawn locations, and trigger regions from game archives.
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from .formats import unpack_reader_zbd, unpack_gamez_zbd, extract_single_texture
from ..config import cache_directory


@dataclass
class MapCalibration:
    name: str
    bitmap_name: str
    mpp: float  # Meters per pixel
    offset_x: float  # World X corresponding to center of map image
    offset_y: float
    offset_z: float  # World Z corresponding to center of map image
    image_width: int = 640
    image_height: int = 480
    image_path: Optional[Path] = None

    def world_to_pixel(self, world_x: float, world_z: float) -> Tuple[float, float]:
        """Convert 3D world coordinates (X, Z) to 2D map bitmap pixel coordinates."""
        # The center of the bitmap (image_width/2, image_height/2) corresponds to (offset_x, offset_z).
        # In MW3 coordinates, positive X is East, negative X is West.
        # Positive Z is South (down on map), negative Z is North (up on map).
        # When mpp is negative (Operations 3 & 4), the scale handles axis reflection.
        if abs(self.mpp) < 1e-6:
            return (self.image_width / 2.0, self.image_height / 2.0)
        px = (self.image_width / 2.0) + (world_x - self.offset_x) / self.mpp
        pz = (self.image_height / 2.0) + (world_z - self.offset_z) / self.mpp
        return (px, pz)

    def pixel_to_world(self, pixel_x: float, pixel_y: float) -> Tuple[float, float]:
        """Convert 2D map bitmap pixel coordinates to 3D world coordinates (X, Z)."""
        wx = self.offset_x + (pixel_x - (self.image_width / 2.0)) * self.mpp
        wz = self.offset_z + (pixel_y - (self.image_height / 2.0)) * self.mpp
        return (wx, wz)


@dataclass
class PlacedObject:
    """One source node's editable placement, using world units and radian rotations.

    node_index is the stable index in this loaded archive, not a global model ID.
    yaw_degrees is a UI conversion of rot_y; both describe the same rotation.
    Unknown recovered fields stay attached rather than being assigned semantics.
    """

    node_index: int
    name: str
    x: float
    y: float
    z: float
    rot_x: float = 0.0
    rot_y: float = 0.0  # Yaw in radians
    rot_z: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    scale_z: float = 1.0
    model_index: int = -1
    active: bool = True
    parent_indices: List[int] = field(default_factory=list)
    child_indices: List[int] = field(default_factory=list)
    flags: Dict[str, Any] = field(default_factory=dict)
    unresolved_fields: Dict[str, Any] = field(default_factory=dict)

    @property
    def yaw_degrees(self) -> float:
        return math.degrees(self.rot_y)

    @yaw_degrees.setter
    def yaw_degrees(self, deg: float) -> None:
        self.rot_y = math.radians(deg)


@dataclass
class SpawnPoint:
    """Named reader-document location with a heading expressed in degrees."""

    name: str
    x: float
    y: float
    z: float
    yaw_degrees: float


@dataclass
class TriggerRegion:
    name: str
    version: int
    points: List[Tuple[float, float, float]]  # (x, y, z)
    connections: List[Tuple[int, int]] = field(default_factory=list)


@dataclass
class TerrainBounds:
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    min_z: float
    max_z: float

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def depth(self) -> float:
        return self.max_z - self.min_z


@dataclass
class MissionData:
    """Loaded view plus private extraction paths needed to preserve source records.

    UI commands mutate the placement objects. raw_nodes_json_path/raw_reader_dir
    identify the unedited cached documents; they are not alternate game installs.
    """

    operation: str
    mission_id: str
    game_root: Path
    terrain_bounds: TerrainBounds
    calibration: MapCalibration
    placed_objects: List[PlacedObject]
    spawn_points: List[SpawnPoint]
    trigger_regions: List[TriggerRegion]
    raw_nodes_json_path: Path
    raw_reader_dir: Path
    unresolved_archive_metadata: Dict[str, Any] = field(default_factory=dict)


class MissionLoader:
    """Read an installation and keep converter products in a separate writable cache.

    Existing extracted documents are reused by filename. This is not content-hash
    invalidation: refreshing or replacing the source installation requires care.
    Missing calibration/format fields retain the explicit fallback/unresolved
    handling below; a useful editor view does not establish native acceptance.
    """

    def __init__(self, game_root: Path, cache_dir: Optional[Path] = None):
        self.game_root = Path(game_root)
        # Caches belong to the tools workspace, never beside a user's game install.
        self.cache_dir = Path(cache_dir) if cache_dir else cache_directory()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._maps_catalog: Dict[str, Dict[str, Any]] = {}
        self._load_maps_catalog()

    def _load_maps_catalog(self) -> None:
        """Read maps.zrd from zbd/reader.zbd to populate map calibrations."""
        global_reader_zbd = self.game_root / "zbd/reader.zbd"
        if not global_reader_zbd.is_file():
            return
        dest_dir = self.cache_dir / "global_reader"
        maps_json = dest_dir / "maps.zrd.json"
        if not maps_json.is_file():
            unpack_reader_zbd(global_reader_zbd, dest_dir)
        if maps_json.is_file():
            try:
                data = json.loads(maps_json.read_text(encoding="utf-8"))
                for item in data[0][1]:
                    m_dict = {}
                    for i in range(0, len(item), 2):
                        m_dict[item[i]] = item[i + 1]
                    name = m_dict.get("name", [""])[0]
                    if name:
                        self._maps_catalog[name.lower()] = {
                            "name": name,
                            "bitmap": m_dict.get("bitmap", [name])[0],
                            "mpp": float(m_dict.get("mpp", [3.5])[0]),
                            "offset": [float(x) for x in m_dict.get("offset", [0.0, 0.0, 0.0])],
                        }
            except Exception as e:
                print(f"Warning: could not parse maps.zrd: {e}")

    def list_available_missions(self) -> List[Tuple[str, str, str]]:
        """List all discoverable missions: (operation_id, mission_id, display_label)."""
        missions = []
        zbd_dir = self.game_root / "zbd"
        if not zbd_dir.is_dir():
            return missions
        for op_dir in sorted(zbd_dir.iterdir()):
            if not op_dir.is_dir():
                continue
            op = op_dir.name.lower()
            if not (op.startswith("c") or op.startswith("t")):
                continue
            # Look for readerm*.zbd and readeria*.zbd
            for r_file in sorted(op_dir.glob("reader*.zbd")):
                stem = r_file.stem.lower()
                if stem == "reader":
                    continue
                # e.g. readerm1 -> c1m1, readeria1 -> c1ia1
                if stem.startswith("readerm"):
                    m_num = stem.replace("readerm", "")
                    m_id = f"{op}m{m_num}"
                    label = f"Campaign {op.upper()} Mission {m_num}"
                    missions.append((op, m_id, label))
                elif stem.startswith("readeria"):
                    ia_num = stem.replace("readeria", "")
                    m_id = f"{op}ia{ia_num}"
                    label = f"Instant Action {op.upper()} Map {ia_num}"
                    missions.append((op, m_id, label))
        return missions

    def load_mission(self, operation: str, mission_id: str) -> MissionData:
        """Load and parse the full mission environment."""
        op_lower = operation.lower()
        m_lower = mission_id.lower()
        op_dir = self.game_root / f"zbd/{op_lower}"
        if not op_dir.is_dir():
            raise FileNotFoundError(f"Operation directory not found: {op_dir}")

        # 1. Unpack or locate GameZ data
        gamez_zbd = op_dir / "gamez.zbd"
        if not gamez_zbd.is_file():
            raise FileNotFoundError(f"Missing {gamez_zbd}")
        gamez_cache = self.cache_dir / f"{op_lower}_gamez"
        nodes_json_path = gamez_cache / "nodes.json"
        if not nodes_json_path.is_file():
            unpack_gamez_zbd(gamez_zbd, gamez_cache)
        nodes = json.loads(nodes_json_path.read_text(encoding="utf-8"))

        # 2. Extract terrain bounds & placed entities from nodes
        terrain_nodes = [n for n in nodes if n.get("flags", {}).get("terrain") is True]
        min_x, max_x = float("inf"), float("-inf")
        min_y, max_y = float("inf"), float("-inf")
        min_z, max_z = float("inf"), float("-inf")
        for n in nodes:
            bbox = n.get("node_bbox")
            if bbox:
                a, b = bbox.get("a", {}), bbox.get("b", {})
                if a and b:
                    min_x = min(min_x, a.get("x", 0.0), b.get("x", 0.0))
                    max_x = max(max_x, a.get("x", 0.0), b.get("x", 0.0))
                    min_y = min(min_y, a.get("y", 0.0), b.get("y", 0.0))
                    max_y = max(max_y, a.get("y", 0.0), b.get("y", 0.0))
                    min_z = min(min_z, a.get("z", 0.0), b.get("z", 0.0))
                    max_z = max(max_z, a.get("z", 0.0), b.get("z", 0.0))
        if min_x == float("inf"):
            min_x, max_x, min_y, max_y, min_z, max_z = (
                -4000.0,
                4000.0,
                -100.0,
                500.0,
                -4000.0,
                4000.0,
            )
        terrain_bounds = TerrainBounds(min_x, max_x, min_y, max_y, min_z, max_z)

        # Recover placed objects
        placed_objects = []
        for idx, node in enumerate(nodes):
            name = node.get("name", "")
            data = node.get("data")
            pos, rot, scale = None, None, None
            if isinstance(data, dict) and "Object3d" in data:
                obj3d = data["Object3d"]
                if isinstance(obj3d, dict):
                    tr = obj3d.get("transform")
                    if isinstance(tr, dict) and "RotateTranslateScale" in tr:
                        rts = tr["RotateTranslateScale"]
                        if isinstance(rts, dict):
                            pos = rts.get("translate")
                            rot = rts.get("rotate")
                            scale = rts.get("scale")
            if pos is not None:
                # Capture unresolved fields explicitly for documentation & lossless roundtrip
                unresolved = {
                    "update_flags": node.get("update_flags"),
                    "field192": node.get("field192"),
                    "field196": node.get("field196"),
                    "field200": node.get("field200"),
                    "field204": node.get("field204"),
                    "active_bbox": node.get("active_bbox"),
                    "data_ptr": node.get("data_ptr"),
                    "parent_array_ptr": node.get("parent_array_ptr"),
                    "child_array_ptr": node.get("child_array_ptr"),
                }
                placed_objects.append(
                    PlacedObject(
                        node_index=idx,
                        name=name,
                        x=float(pos["x"]),
                        y=float(pos["y"]),
                        z=float(pos["z"]),
                        rot_x=float(rot.get("x", 0.0)) if rot else 0.0,
                        rot_y=float(rot.get("y", 0.0)) if rot else 0.0,
                        rot_z=float(rot.get("z", 0.0)) if rot else 0.0,
                        scale_x=float(scale.get("x", 1.0)) if scale else 1.0,
                        scale_y=float(scale.get("y", 1.0)) if scale else 1.0,
                        scale_z=float(scale.get("z", 1.0)) if scale else 1.0,
                        model_index=node.get("model_index", -1),
                        active=node.get("flags", {}).get("active", True),
                        parent_indices=node.get("parent_indices", []),
                        child_indices=node.get("child_indices", []),
                        flags=node.get("flags", {}),
                        unresolved_fields=unresolved,
                    )
                )

        # 3. Load Map Calibration & Map Image
        map_meta = self._maps_catalog.get(m_lower)
        if not map_meta:
            # Fallback to operation default or Instant Action
            map_meta = self._maps_catalog.get(
                f"{op_lower}ia",
                {"name": m_lower, "bitmap": m_lower, "mpp": 3.476, "offset": [0.0, 0.0, 0.0]},
            )
        calibration = MapCalibration(
            name=map_meta["name"],
            bitmap_name=map_meta["bitmap"],
            mpp=map_meta["mpp"],
            offset_x=map_meta["offset"][0],
            offset_y=map_meta["offset"][1],
            offset_z=map_meta["offset"][2],
        )

        # Extract map bitmap from rimage.zbd
        rimage_zbd = self.game_root / "zbd/rimage.zbd"
        if rimage_zbd.is_file():
            img_cache = self.cache_dir / f"maps/{calibration.bitmap_name}.png"
            if not img_cache.is_file():
                extract_single_texture(rimage_zbd, calibration.bitmap_name, img_cache)
            if img_cache.is_file():
                calibration.image_path = img_cache

        # 4. Load Spawn Points from op reader.zbd -> location.zrd.json
        spawn_points = []
        op_reader_zbd = op_dir / "reader.zbd"
        op_reader_cache = self.cache_dir / f"{op_lower}_reader"
        loc_json = op_reader_cache / "location.zrd.json"
        if not loc_json.is_file() and op_reader_zbd.is_file():
            unpack_reader_zbd(op_reader_zbd, op_reader_cache)
        if loc_json.is_file():
            try:
                loc_data = json.loads(loc_json.read_text(encoding="utf-8"))
                for i in range(0, len(loc_data[0]), 2):
                    sp_name = loc_data[0][i]
                    sp_coords = loc_data[0][i + 1]
                    # Format: [[x, y, z], yaw]
                    pos = sp_coords[0]
                    yaw = sp_coords[1] if len(sp_coords) > 1 else 0.0
                    spawn_points.append(
                        SpawnPoint(
                            name=sp_name,
                            x=float(pos[0]),
                            y=float(pos[1]),
                            z=float(pos[2]),
                            yaw_degrees=float(yaw),
                        )
                    )
            except Exception as e:
                print(f"Warning: could not parse location.zrd: {e}")

        # 5. Load Trigger Regions & Nav Networks from mission reader
        # Determine reader file name: e.g. readerm1.zbd or readeria1.zbd
        reader_stem = "reader"
        if "m" in m_lower:
            m_part = m_lower.split("m")[-1]
            reader_stem = f"readerm{m_part}"
        elif "ia" in m_lower:
            ia_part = m_lower.split("ia")[-1]
            reader_stem = f"readeria{ia_part}"
        mission_reader_zbd = op_dir / f"{reader_stem}.zbd"
        mission_reader_cache = self.cache_dir / f"{op_lower}_{reader_stem}"
        if not mission_reader_cache.is_dir() and mission_reader_zbd.is_file():
            unpack_reader_zbd(mission_reader_zbd, mission_reader_cache)

        trigger_regions = []
        # Search both op_reader_cache and mission_reader_cache for reg_*.zrd.json
        search_dirs = [d for d in [mission_reader_cache, op_reader_cache] if d.is_dir()]
        for sdir in search_dirs:
            for reg_file in sdir.glob("reg_*.zrd.json"):
                try:
                    reg_data = json.loads(reg_file.read_text(encoding="utf-8"))
                    reg_dict = {}
                    for i in range(0, len(reg_data[0]), 2):
                        reg_dict[reg_data[0][i]] = reg_data[0][i + 1]
                    reg_name = reg_dict.get("name", [reg_file.stem])[0]
                    reg_version = int(reg_dict.get("version", [108])[0])
                    # Extract polygon nodes
                    nodes_list = []
                    for k in sorted(reg_dict.keys()):
                        if k.startswith("node_"):
                            # node format: [12, [x, y, z], [connected_indices]]
                            val = reg_dict[k]
                            if len(val) >= 2 and isinstance(val[1], list):
                                coords = val[1]
                                nodes_list.append(
                                    (float(coords[0]), float(coords[1]), float(coords[2]))
                                )
                    if nodes_list:
                        trigger_regions.append(
                            TriggerRegion(name=reg_name, version=reg_version, points=nodes_list)
                        )
                except Exception as e:
                    print(f"Warning: error parsing {reg_file.name}: {e}")

        return MissionData(
            operation=op_lower,
            mission_id=m_lower,
            game_root=self.game_root,
            terrain_bounds=terrain_bounds,
            calibration=calibration,
            placed_objects=placed_objects,
            spawn_points=spawn_points,
            trigger_regions=trigger_regions,
            raw_nodes_json_path=nodes_json_path,
            raw_reader_dir=(
                mission_reader_cache if mission_reader_cache.is_dir() else op_reader_cache
            ),
        )
