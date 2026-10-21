"""Automated Verification Suite for the MW3 Map & Mission Editor Slice.

Validates format round-trips, mission data extraction, undo/redo mechanics,
project serialization, isolated export packaging, and manifest integrity.
"""

import filecmp
import json
import shutil
import tempfile
from pathlib import Path
import sys

# Ensure editor package is in import path
TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT))

from editor.core.formats import verify_tools_available
from editor.core.mission_loader import MissionLoader
from editor.core.project import (
    ModProject,
    CommandHistory,
    MoveObjectCommand,
    RotateObjectCommand,
    ToggleObjectActiveCommand,
)
from editor.core.exporter import ModExporter

ROOT = TOOLS_ROOT.parents[2]


def test_format_tools():
    print("[1/6] Verifying format conversion tools...")
    assert verify_tools_available(), "Mech3AX unzbd/rezbd tools must be present"
    print("  -> unzbd and rezbd available.")


def test_mission_loading():
    print("[2/6] Verifying mission loading and top-down map recovery...")
    loader = MissionLoader(ROOT / "MW3")
    missions = loader.list_available_missions()
    assert len(missions) >= 20, f"Expected at least 20 missions, found {len(missions)}"

    # Load C1M1
    m1 = loader.load_mission("c1", "c1m1")
    assert m1.terrain_bounds.width > 2000.0, "Invalid terrain width"
    assert m1.terrain_bounds.depth > 2000.0, "Invalid terrain depth"
    assert len(m1.placed_objects) > 500, f"Expected world objects, found {len(m1.placed_objects)}"
    assert len(m1.spawn_points) >= 1, "Expected spawn points in location.zrd"
    assert len(m1.trigger_regions) >= 1, "Expected trigger regions in reg_*.zrd"
    assert (
        m1.calibration.image_path and m1.calibration.image_path.is_file()
    ), "Map image should be extracted"
    print(
        f"  -> C1M1 loaded: {len(m1.placed_objects)} objects, {len(m1.spawn_points)} spawns, {len(m1.trigger_regions)} trigger regions."
    )


def test_undo_redo_and_editing():
    print("[3/6] Verifying object property editing and undo/redo mechanics...")
    loader = MissionLoader(ROOT / "MW3")
    m1 = loader.load_mission("c1", "c1m1")
    history = CommandHistory()

    obj = m1.placed_objects[0]
    orig_x, orig_y, orig_z = obj.x, obj.y, obj.z
    orig_yaw = obj.yaw_degrees

    # Test move
    cmd_move = MoveObjectCommand(obj, orig_x + 100.0, orig_y, orig_z - 50.0)
    history.execute(cmd_move)
    assert (obj.x, obj.z) == (orig_x + 100.0, orig_z - 50.0)

    # Test rotate
    cmd_rot = RotateObjectCommand(obj, orig_yaw + 45.0)
    history.execute(cmd_rot)
    assert abs(obj.yaw_degrees - (orig_yaw + 45.0)) < 0.01

    # Test undo rotate
    history.undo()
    assert abs(obj.yaw_degrees - orig_yaw) < 0.01
    assert (obj.x, obj.z) == (orig_x + 100.0, orig_z - 50.0)

    # Test undo move
    history.undo()
    assert (obj.x, obj.z) == (orig_x, orig_z)

    # Test redo move
    history.redo()
    assert (obj.x, obj.z) == (orig_x + 100.0, orig_z - 50.0)
    print("  -> Undo/Redo stack verified.")


def test_project_serialization():
    print("[4/6] Verifying project saving and loading...")
    with tempfile.TemporaryDirectory() as td:
        proj_file = Path(td) / "test.mw3mod"
        proj = ModProject(
            project_name="Unit Test Project",
            target_operation="c1",
            target_mission="c1m1",
            author="CI Test",
        )
        proj.modified_objects[7968] = {"name": "test_turret", "x": 100.0, "y": 20.0, "z": -500.0}
        proj.save(proj_file)
        assert proj_file.is_file(), "Project file was not created"

        loaded = ModProject.load(proj_file)
        assert loaded.project_name == "Unit Test Project"
        assert loaded.target_mission == "c1m1"
        assert loaded.modified_objects[7968]["x"] == 100.0
    print("  -> Project serialization verified.")


def test_unchanged_export_roundtrip():
    print("[5/6] Verifying unchanged export byte-exact round-trip...")
    with tempfile.TemporaryDirectory() as td:
        exporter = ModExporter(output_root=Path(td))
        loader = MissionLoader(ROOT / "MW3")
        m1 = loader.load_mission("c1", "c1m1")
        clean_proj = ModProject(
            project_name="Clean Export", target_operation="c1", target_mission="c1m1"
        )
        receipt = exporter.export(clean_proj, m1)

        orig_gamez = ROOT / "MW3/zbd/c1/gamez.zbd"
        exported_gamez = receipt.mod_dir / "zbd/c1/gamez.zbd"
        assert exported_gamez.is_file(), "Exported gamez.zbd missing"
        assert filecmp.cmp(
            orig_gamez, exported_gamez, shallow=False
        ), "Unchanged export must be byte-exact"
        assert receipt.manifest_path.is_file(), "manifest.json missing"
        assert receipt.redirect_bank_path.is_file(), "mod-banks.bin missing"
    print("  -> Unchanged byte-exact export verified.")


def test_intentional_edit_export():
    print("[6/6] Verifying intentional placement edit export and manifest...")
    with tempfile.TemporaryDirectory() as td:
        exporter = ModExporter(output_root=Path(td))
        loader = MissionLoader(ROOT / "MW3")
        m1 = loader.load_mission("c1", "c1m1")
        proj = ModProject(project_name="Edited Mod", target_operation="c1", target_mission="c1m1")

        # Edit rbunk01 (node 4790)
        proj.modified_objects[4790] = {
            "name": "rbunk01_modded",
            "x": -1000.0,
            "y": 16.6,
            "z": -900.0,
            "active": True,
        }
        receipt = exporter.export(proj, m1)
        exported_gamez = receipt.mod_dir / "zbd/c1/gamez.zbd"
        orig_gamez = ROOT / "MW3/zbd/c1/gamez.zbd"

        assert exported_gamez.is_file(), "Modified gamez.zbd missing"
        assert not filecmp.cmp(
            orig_gamez, exported_gamez, shallow=False
        ), "Modified file must differ from original"
        assert (
            orig_gamez.stat().st_size == exported_gamez.stat().st_size
        ), "Header/archive size parity expected"

        manifest = json.loads(receipt.manifest_path.read_text(encoding="utf-8"))
        assert manifest["name"] == "Edited Mod"
        assert len(manifest["modified_files"]) == 1
        assert manifest["modified_files"][0]["target"] == "zbd/c1/gamez.zbd"
    print("  -> Intentional edit export and manifest verified.")


if __name__ == "__main__":
    print("Running MW3 Mod Tools Automated Test Suite...\n")
    test_format_tools()
    test_mission_loading()
    test_undo_redo_and_editing()
    test_project_serialization()
    test_unchanged_export_roundtrip()
    test_intentional_edit_export()
    print("\nALL 6 TEST PHASES PASSED SUCCESSFULLY!")
