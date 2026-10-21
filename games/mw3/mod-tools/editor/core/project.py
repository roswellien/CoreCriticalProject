"""Mod Project Data Model and Undo/Redo Engine.

Encapsulates project state, deltas against original game data,
and an undo/redo command stack for all editor operations.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple

from .mission_loader import PlacedObject, SpawnPoint, MissionData


class Command(ABC):
    """Abstract editor action that can be applied, undone, and redone."""

    @abstractmethod
    def execute(self) -> None:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass

    def redo(self) -> None:
        self.execute()

    @property
    @abstractmethod
    def description(self) -> str:
        pass


class MoveObjectCommand(Command):
    """Moves a placed world object to a new (x, y, z) position."""

    def __init__(self, obj: PlacedObject, new_x: float, new_y: float, new_z: float, on_update: Optional[Callable[[], None]] = None):
        self.obj = obj
        self.old_x, self.old_y, self.old_z = obj.x, obj.y, obj.z
        self.new_x, self.new_y, self.new_z = new_x, new_y, new_z
        self.on_update = on_update

    def execute(self) -> None:
        self.obj.x = self.new_x
        self.obj.y = self.new_y
        self.obj.z = self.new_z
        if self.on_update:
            self.on_update()

    def undo(self) -> None:
        self.obj.x = self.old_x
        self.obj.y = self.old_y
        self.obj.z = self.old_z
        if self.on_update:
            self.on_update()

    @property
    def description(self) -> str:
        return f"Move '{self.obj.name}' to ({self.new_x:.1f}, {self.new_y:.1f}, {self.new_z:.1f})"


class RotateObjectCommand(Command):
    """Rotates an object (yaw degrees/radians)."""

    def __init__(self, obj: PlacedObject, new_yaw_deg: float, on_update: Optional[Callable[[], None]] = None):
        self.obj = obj
        self.old_yaw_deg = obj.yaw_degrees
        self.new_yaw_deg = new_yaw_deg
        self.on_update = on_update

    def execute(self) -> None:
        self.obj.yaw_degrees = self.new_yaw_deg
        if self.on_update:
            self.on_update()

    def undo(self) -> None:
        self.obj.yaw_degrees = self.old_yaw_deg
        if self.on_update:
            self.on_update()

    @property
    def description(self) -> str:
        return f"Rotate '{self.obj.name}' to {self.new_yaw_deg:.1f}°"


class ToggleObjectActiveCommand(Command):
    """Toggles object active/enabled flag."""

    def __init__(self, obj: PlacedObject, new_active: bool, on_update: Optional[Callable[[], None]] = None):
        self.obj = obj
        self.old_active = obj.active
        self.new_active = new_active
        self.on_update = on_update

    def execute(self) -> None:
        self.obj.active = self.new_active
        if self.on_update:
            self.on_update()

    def undo(self) -> None:
        self.obj.active = self.old_active
        if self.on_update:
            self.on_update()

    @property
    def description(self) -> str:
        state = "Enable" if self.new_active else "Disable"
        return f"{state} '{self.obj.name}'"


class CommandHistory:
    """Manages undo and redo stacks with change notifications."""

    def __init__(self, max_depth: int = 100):
        self.max_depth = max_depth
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.change_callbacks: List[Callable[[], None]] = []

    def add_change_callback(self, cb: Callable[[], None]) -> None:
        self.change_callbacks.append(cb)

    def _notify(self) -> None:
        for cb in self.change_callbacks:
            try:
                cb()
            except Exception as e:
                print(f"Error in change callback: {e}")

    def execute(self, command: Command) -> None:
        command.execute()
        self.undo_stack.append(command)
        if len(self.undo_stack) > self.max_depth:
            self.undo_stack.pop(0)
        self.redo_stack.clear()
        self._notify()

    def undo(self) -> Optional[Command]:
        if not self.can_undo:
            return None
        cmd = self.undo_stack.pop()
        cmd.undo()
        self.redo_stack.append(cmd)
        self._notify()
        return cmd

    def redo(self) -> Optional[Command]:
        if not self.can_redo:
            return None
        cmd = self.redo_stack.pop()
        cmd.redo()
        self.undo_stack.append(cmd)
        self._notify()
        return cmd

    @property
    def can_undo(self) -> bool:
        return len(self.undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self.redo_stack) > 0

    @property
    def undo_description(self) -> str:
        return self.undo_stack[-1].description if self.undo_stack else ""

    @property
    def redo_description(self) -> str:
        return self.redo_stack[-1].description if self.redo_stack else ""

    def clear(self) -> None:
        self.undo_stack.clear()
        self.redo_stack.clear()
        self._notify()


@dataclass
class ModProject:
    """Represents an editable mod project with delta tracking."""

    project_name: str
    target_operation: str
    target_mission: str
    author: str = "MW3 Modder"
    description: str = "Authored using MW3 Map & Mission Editor"
    version: str = "1.0.0"
    project_file_path: Optional[Path] = None

    # Deltas: mapping node_index -> dict of modified properties
    modified_objects: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    # Deltas: spawn_name -> dict of modified properties
    modified_spawns: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Base file checksums for validation
    base_file_hashes: Dict[str, str] = field(default_factory=dict)

    # Runtime state
    dirty: bool = False

    def record_object_change(self, obj: PlacedObject) -> None:
        """Record modified properties for a placed object."""
        self.modified_objects[obj.node_index] = {
            "name": obj.name,
            "x": obj.x,
            "y": obj.y,
            "z": obj.z,
            "rot_y": obj.rot_y,
            "yaw_degrees": obj.yaw_degrees,
            "active": obj.active,
        }
        self.dirty = True

    def record_spawn_change(self, spawn: SpawnPoint) -> None:
        """Record modified coordinates/heading for a spawn point."""
        self.modified_spawns[spawn.name] = {
            "x": spawn.x,
            "y": spawn.y,
            "z": spawn.z,
            "yaw_degrees": spawn.yaw_degrees,
        }
        self.dirty = True

    def save(self, file_path: Path) -> None:
        """Save project state as a standalone JSON project file."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "format": "MW3MOD_PROJECT_V1",
            "name": self.project_name,
            "author": self.author,
            "description": self.description,
            "version": self.version,
            "target_operation": self.target_operation,
            "target_mission": self.target_mission,
            "base_file_hashes": self.base_file_hashes,
            "modified_objects": {str(k): v for k, v in self.modified_objects.items()},
            "modified_spawns": self.modified_spawns,
        }
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        self.project_file_path = file_path
        self.dirty = False

    @classmethod
    def load(cls, file_path: Path) -> "ModProject":
        """Load project state from a project JSON file."""
        file_path = Path(file_path)
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if data.get("format") != "MW3MOD_PROJECT_V1":
            raise ValueError(f"Invalid mod project format in {file_path}")
        mod_objs = {int(k): v for k, v in data.get("modified_objects", {}).items()}
        proj = cls(
            project_name=data.get("name", "Unnamed Mod"),
            target_operation=data.get("target_operation", "c1"),
            target_mission=data.get("target_mission", "c1ia1"),
            author=data.get("author", "MW3 Modder"),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            project_file_path=file_path,
            modified_objects=mod_objs,
            modified_spawns=data.get("modified_spawns", {}),
            base_file_hashes=data.get("base_file_hashes", {}),
            dirty=False,
        )
        return proj
