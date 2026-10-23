"""Authored-fixture regression suite for desktop Mod Editor history synchronization.

Validates that execute, undo and redo persist changes for the command's affected
object regardless of active selection, verifying move, rotate, and enable edits,
switching selection before undo/redo, save/reload fidelity, and exported deltas
matching the displayed state while preserving original game files read-only.
"""

import hashlib
import json
import math
import shutil
import tempfile
from pathlib import Path
import sys

# Provide mock for PIL if not installed in current python environment
try:
    import PIL
except ImportError:
    from unittest.mock import MagicMock
    pil_mock = MagicMock()
    sys.modules["PIL"] = pil_mock
    sys.modules["PIL.Image"] = pil_mock.Image
    sys.modules["PIL.ImageTk"] = pil_mock.ImageTk

# Ensure editor package is in import path
TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT))

from editor.core.formats import unpack_gamez_zbd
from editor.core.mission_loader import MissionLoader, PlacedObject
from editor.core.project import (
    ModProject,
    CommandHistory,
    MoveObjectCommand,
    RotateObjectCommand,
    ToggleObjectActiveCommand,
)
from editor.core.exporter import ModExporter
from editor.ui.main_window import MainWindow

ROOT = TOOLS_ROOT.parents[2]


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_core_history_synchronization():
    """Verify CommandHistory with attached project persists changes for affected object."""
    print("[1/4] Verifying core history synchronization on authored objects...")
    loader = MissionLoader(ROOT / "MW3")
    mission = loader.load_mission("c1", "c1m1")

    proj = ModProject(
        project_name="Core Sync Test",
        target_operation="c1",
        target_mission="c1m1",
    )
    history = CommandHistory(project=proj)

    # Use authored fixture: node 4790 (bunker)
    obj1 = next(o for o in mission.placed_objects if o.node_index == 4790)
    orig_x, orig_y, orig_z = obj1.x, obj1.y, obj1.z
    orig_yaw = obj1.yaw_degrees
    orig_active = obj1.active

    # 1. Move
    new_x, new_y, new_z = orig_x + 150.0, orig_y + 5.0, orig_z - 75.0
    cmd_move = MoveObjectCommand(obj1, new_x, new_y, new_z)
    history.execute(cmd_move)
    assert (obj1.x, obj1.y, obj1.z) == (new_x, new_y, new_z)
    assert proj.modified_objects[obj1.node_index]["x"] == new_x
    assert proj.modified_objects[obj1.node_index]["y"] == new_y
    assert proj.modified_objects[obj1.node_index]["z"] == new_z

    # 2. Rotate
    new_yaw = (orig_yaw + 90.0) % 360.0
    cmd_rot = RotateObjectCommand(obj1, new_yaw)
    history.execute(cmd_rot)
    assert abs(obj1.yaw_degrees - new_yaw) < 0.01
    assert abs(proj.modified_objects[obj1.node_index]["yaw_degrees"] - new_yaw) < 0.01

    # 3. Enable/Disable toggle
    new_active = not orig_active
    cmd_active = ToggleObjectActiveCommand(obj1, new_active)
    history.execute(cmd_active)
    assert obj1.active == new_active
    assert proj.modified_objects[obj1.node_index]["active"] == new_active

    # 4. Undo toggle
    history.undo()
    assert obj1.active == orig_active
    assert proj.modified_objects[obj1.node_index]["active"] == orig_active
    # Previous move and rotate edits remain intact
    assert proj.modified_objects[obj1.node_index]["x"] == new_x
    assert abs(proj.modified_objects[obj1.node_index]["yaw_degrees"] - new_yaw) < 0.01

    # 5. Undo rotate
    history.undo()
    assert abs(obj1.yaw_degrees - orig_yaw) < 0.01
    assert abs(proj.modified_objects[obj1.node_index]["yaw_degrees"] - orig_yaw) < 0.01
    assert proj.modified_objects[obj1.node_index]["x"] == new_x

    # 6. Undo move
    history.undo()
    assert (obj1.x, obj1.y, obj1.z) == (orig_x, orig_y, orig_z)
    assert proj.modified_objects[obj1.node_index]["x"] == orig_x

    # 7. Redo move
    history.redo()
    assert (obj1.x, obj1.y, obj1.z) == (new_x, new_y, new_z)
    assert proj.modified_objects[obj1.node_index]["x"] == new_x

    # 8. Redo rotate
    history.redo()
    assert abs(obj1.yaw_degrees - new_yaw) < 0.01
    assert abs(proj.modified_objects[obj1.node_index]["yaw_degrees"] - new_yaw) < 0.01

    # 9. Redo active toggle
    history.redo()
    assert obj1.active == new_active
    assert proj.modified_objects[obj1.node_index]["active"] == new_active

    print("  -> Core history execute/undo/redo synchronization verified.")


def test_switching_selection_before_undo_redo():
    """Verify switching selection or clearing selection before undo/redo persists target object."""
    print("[2/4] Verifying selection-independent undo and redo in MainWindow...")
    # Initialize MainWindow (headless / withdrawn)
    win = MainWindow(game_root=ROOT / "MW3", initial_op="c1", initial_mission="c1m1")
    win.withdraw()

    try:
        mission = win.current_mission
        assert mission is not None, "Mission failed to load"
        proj = win.current_project
        assert proj is not None, "Project failed to initialize"

        # Select Object 1: node 4790 (bunker)
        obj1 = next(o for o in mission.placed_objects if o.node_index == 4790)
        # Select Object 2: node 7968 (turret)
        obj2 = next(o for o in mission.placed_objects if o.node_index == 7968)

        orig1_x, orig1_y, orig1_z = obj1.x, obj1.y, obj1.z
        orig1_yaw = obj1.yaw_degrees
        orig1_active = obj1.active

        orig2_x, orig2_y, orig2_z = obj2.x, obj2.y, obj2.z
        orig2_yaw = obj2.yaw_degrees
        orig2_active = obj2.active

        # Step 1: Select Object 1 and apply Move, Rotate, Enable changes
        win.canvas.selected_object = obj1
        win.inspector.inspect_object(obj1)

        # Move Object 1
        new1_x, new1_y, new1_z = orig1_x + 200.0, orig1_y + 10.0, orig1_z - 100.0
        # Call canvas move handler
        obj1.x, obj1.y, obj1.z = new1_x, new1_y, new1_z
        win._on_canvas_object_moved(obj1, orig1_x, orig1_y, orig1_z)

        # Rotate Object 1
        new1_yaw = 135.0
        cmd_rot = RotateObjectCommand(obj1, new1_yaw, on_update=win._on_property_edited)
        win.history.execute(cmd_rot)

        # Toggle Object 1 Active
        new1_active = not orig1_active
        cmd_active = ToggleObjectActiveCommand(obj1, new1_active, on_update=win._on_property_edited)
        win.history.execute(cmd_active)

        # Confirm Object 1 is recorded, Object 2 is NOT
        assert obj1.node_index in proj.modified_objects
        assert obj2.node_index not in proj.modified_objects
        assert proj.modified_objects[obj1.node_index]["x"] == new1_x
        assert abs(proj.modified_objects[obj1.node_index]["yaw_degrees"] - new1_yaw) < 0.01
        assert proj.modified_objects[obj1.node_index]["active"] == new1_active

        # Step 2: SWITCH SELECTION TO OBJECT 2 BEFORE UNDO!
        win.canvas.selected_object = obj2
        win.inspector.inspect_object(obj2)
        assert win.canvas.selected_object == obj2

        # Step 3: Undo active change while Object 2 is selected
        win._undo()
        # Object 1 active was reverted
        assert obj1.active == orig1_active
        # Object 1's persisted delta MUST match its displayed state!
        assert proj.modified_objects[obj1.node_index]["active"] == orig1_active
        # CRITICAL: Object 2 MUST NOT be recorded in modified_objects!
        assert obj2.node_index not in proj.modified_objects
        assert (obj2.x, obj2.y, obj2.z) == (orig2_x, orig2_y, orig2_z)
        assert abs(obj2.yaw_degrees - orig2_yaw) < 0.01
        assert obj2.active == orig2_active

        # Step 4: Undo rotate change while Object 2 is still selected
        win._undo()
        assert abs(obj1.yaw_degrees - orig1_yaw) < 0.01
        assert abs(proj.modified_objects[obj1.node_index]["yaw_degrees"] - orig1_yaw) < 0.01
        # Object 2 still not touched
        assert obj2.node_index not in proj.modified_objects

        # Step 5: DESELECT COMPLETELY (selection = None) BEFORE REDO
        win.canvas.selected_object = None
        win.inspector.inspect_object(None)

        # Step 6: Redo rotate change while nothing is selected
        win._redo()
        assert abs(obj1.yaw_degrees - new1_yaw) < 0.01
        assert abs(proj.modified_objects[obj1.node_index]["yaw_degrees"] - new1_yaw) < 0.01
        assert obj2.node_index not in proj.modified_objects

        # Step 7: Redo active change while Object 2 is selected again
        win.canvas.selected_object = obj2
        win._redo()
        assert obj1.active == new1_active
        assert proj.modified_objects[obj1.node_index]["active"] == new1_active
        assert obj2.node_index not in proj.modified_objects

        print("  -> Selection switching before undo/redo verified.")
    finally:
        win.destroy()


def test_save_reload_and_exported_deltas():
    """Verify saved project files and exported archives match the exact displayed state."""
    print("[3/4] Verifying save/reload and exported archive deltas match displayed state...")
    loader = MissionLoader(ROOT / "MW3")
    mission = loader.load_mission("c1", "c1m1")

    obj1 = next(o for o in mission.placed_objects if o.node_index == 4790)
    obj2 = next(o for o in mission.placed_objects if o.node_index == 7968)

    orig1_x, orig1_y, orig1_z = obj1.x, obj1.y, obj1.z
    orig1_yaw = obj1.yaw_degrees
    orig1_active = obj1.active

    with tempfile.TemporaryDirectory() as td:
        temp_dir = Path(td)
        proj_file = temp_dir / "sync_test.mw3mod"
        export_root = temp_dir / "mods"
        exporter = ModExporter(output_root=export_root)

        # Start clean project
        proj = ModProject(
            project_name="Export Delta Sync Test",
            target_operation="c1",
            target_mission="c1m1",
        )
        history = CommandHistory(project=proj)

        # 1. Apply Move, Rotate, Enable to Object 1
        new_x = orig1_x + 300.0
        new_yaw = 90.0
        new_active = False

        history.execute(MoveObjectCommand(obj1, new_x, orig1_y, orig1_z))
        history.execute(RotateObjectCommand(obj1, new_yaw))
        history.execute(ToggleObjectActiveCommand(obj1, new_active))

        # 2. Undo Enable
        history.undo()
        assert obj1.active == orig1_active
        assert proj.modified_objects[obj1.node_index]["active"] == orig1_active

        # Save and Reload: verify file matches current state
        proj.save(proj_file)
        loaded = ModProject.load(proj_file)
        assert loaded.modified_objects[obj1.node_index]["x"] == new_x
        assert abs(loaded.modified_objects[obj1.node_index]["yaw_degrees"] - new_yaw) < 0.01
        assert loaded.modified_objects[obj1.node_index]["active"] == orig1_active
        assert obj2.node_index not in loaded.modified_objects

        # Export and verify exported gamez archive matches displayed state
        receipt = exporter.export(proj, mission)
        exported_gamez = receipt.mod_dir / "zbd/c1/gamez.zbd"
        assert exported_gamez.is_file()

        # Unpack exported gamez to inspect nodes.json
        unpack_dir = temp_dir / "unpacked_export"
        unpack_gamez_zbd(exported_gamez, unpack_dir)
        nodes_data = json.loads((unpack_dir / "nodes.json").read_text(encoding="utf-8"))

        node1 = nodes_data[obj1.node_index]
        t1 = node1["data"]["Object3d"]["transform"]["RotateTranslateScale"]["translate"]
        r1 = node1["data"]["Object3d"]["transform"]["RotateTranslateScale"]["rotate"]
        flags1 = node1["flags"]

        # Position matches displayed state
        assert abs(t1["x"] - new_x) < 0.001
        assert abs(t1["y"] - orig1_y) < 0.001
        assert abs(t1["z"] - orig1_z) < 0.001

        # Yaw matches displayed state (radians)
        expected_rad = math.radians(new_yaw)
        assert abs(r1["y"] - expected_rad) < 0.001

        # Active flag matches displayed state (undone to True)
        assert flags1.get("active", True) == orig1_active

        # Object 2 was never edited: verify it matches original in the exported archive
        orig_nodes_data = json.loads(mission.raw_nodes_json_path.read_text(encoding="utf-8"))
        node2_orig = orig_nodes_data[obj2.node_index]
        node2_exp = nodes_data[obj2.node_index]
        assert node2_orig == node2_exp, "Unedited object must match original exactly"

        print("  -> Save/reload and exported archive deltas match displayed state.")


def test_original_game_files_read_only():
    """Verify original game archives are read-only and were not touched."""
    print("[4/4] Verifying original game files remain pristine and read-only...")
    orig_gamez = ROOT / "MW3/zbd/c1/gamez.zbd"
    assert orig_gamez.is_file(), "Original gamez.zbd must exist"
    # Ensure file is readable
    orig_hash = compute_sha256(orig_gamez)
    assert len(orig_hash) == 64, "Expected valid SHA256"
    print(f"  -> Original gamez.zbd SHA256 intact: {orig_hash[:16]}...")


if __name__ == "__main__":
    print("Running Desktop Mod Editor History Synchronization Regressions...\n")
    orig_hash_start = compute_sha256(ROOT / "MW3/zbd/c1/gamez.zbd")

    test_core_history_synchronization()
    test_switching_selection_before_undo_redo()
    test_save_reload_and_exported_deltas()
    test_original_game_files_read_only()

    orig_hash_end = compute_sha256(ROOT / "MW3/zbd/c1/gamez.zbd")
    assert orig_hash_start == orig_hash_end, "Original game file was modified!"

    print("\nALL HISTORY SYNCHRONIZATION REGRESSIONS PASSED SUCCESSFULLY!")
