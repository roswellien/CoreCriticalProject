"""Automated Regressions for Objectives, Triggers, Terrain Textures, and MechLab Drop Config.

Verifies:
1. Authentic terrain textures extracted from MW3 archives are present and valid PNGs.
2. Mission Objectives and Trigger Volumes serialize and export cleanly to objectives.json.
3. Custom MechLab drop configuration and lancemates serialize and export cleanly to drop_config.json.
4. Tactical briefing dossier (briefing.txt) is generated with objectives and lance rosters.
5. Command runner script correctly embeds briefing and engine launch parameters.
"""

import json
import os
import shutil
import sys
import unittest
from pathlib import Path

# Ensure editor package is in import path
TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT))

from editor.core.map_pack import (
    MapPackProject,
    MapAsset,
    MapPackBuilder,
    TerrainConfig,
    LightingConfig,
)

ROOT = Path(__file__).resolve().parents[4]


class TestObjectivesAndDropConfig(unittest.TestCase):
    def setUp(self):
        self.test_pack_id = "test_objectives_unit_pack"
        self.packs_dir = ROOT / "mods" / "map-packs"
        self.test_pack_dir = self.packs_dir / self.test_pack_id
        if self.test_pack_dir.exists():
            shutil.rmtree(self.test_pack_dir, ignore_errors=True)

    def tearDown(self):
        if self.test_pack_dir.exists():
            shutil.rmtree(self.test_pack_dir, ignore_errors=True)

    def test_authentic_terrain_textures_exist(self):
        """Verify authentic textures extracted from texture.zbd for all biomes."""
        texture_dir = ROOT / "games" / "mw3" / "mod-tools" / "editor" / "web" / "static" / "assets" / "textures" / "terrains"
        self.assertTrue(texture_dir.is_dir(), f"Missing texture directory: {texture_dir}")

        expected_textures = [
            "c1_txgter_1.png",  # Op 1 Coastal grass
            "c1_ltsand.png",    # Op 1 Light sand
            "c2_ggter_1.png",   # Op 2 Canyon floor
            "c2_rocks1.png",    # Op 2 Canyon rocks
            "c3_gter_1.png",    # Op 3 Volcanic basalt
            "c4_gter_1.png",    # Op 4 Alpine soil
            "t1_ggter1.png",    # Training grounds soil
        ]

        for tex_name in expected_textures:
            tex_file = texture_dir / tex_name
            self.assertTrue(tex_file.is_file(), f"Missing authentic terrain texture: {tex_name}")
            data = tex_file.read_bytes()
            # PNG signature check
            self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"), f"File is not a valid PNG: {tex_name}")
            self.assertGreater(len(data), 1000, f"Texture is suspiciously small: {tex_name}")

    def test_map_pack_project_roundtrip(self):
        """Verify project serialization with objectives, drop_config, and triggers."""
        proj = MapPackProject(
            pack_id=self.test_pack_id,
            pack_title="Assault on Tranquil Basin",
            author="Test Modder",
            base_operation="c1",
            objectives={
                "primary": [
                    {"id": "obj_1", "desc": "Neutralize Command Bunker", "target": "bunker", "completed": False},
                    {"id": "obj_2", "desc": "Proceed to NAV BAKER", "target": "trig_evac", "completed": False},
                ],
                "secondary": [
                    {"id": "sec_1", "desc": "Destroy fuel silos", "target": "fuel_tank", "completed": False}
                ],
                "briefing_text": "Clan garrison sighted in Sector 4. Strike hard and fast.",
                "audio_track": "action_theme_1",
            },
            drop_config={
                "player_mech": "mech_madcat",
                "drop_type": "orbital_drop_pod",
                "tonnage": 75.0,
                "armor_tons": 14.5,
                "heatsinks": 18,
                "jump_jets": 0,
                "weapons": {
                    "left_arm": "ER PPC",
                    "right_arm": "Clan Gauss Rifle",
                    "left_torso": "Clan LRM-20",
                    "right_torso": "Clan LRM-20",
                    "center_torso": "Medium Pulse Laser",
                },
                "lancemates": [
                    {"name": "Lt. Alan Mattila", "mech": "mech_bushwacker", "orders": "escort"},
                    {"name": "Sgt. Epona Rhi", "mech": "mech_shadowcat", "orders": "free_fire"},
                ],
            },
            assets=[
                MapAsset(
                    asset_id="spawn_player",
                    asset_type="spawn",
                    name="Drop Zone Alpha",
                    x=-650.0,
                    y=5.0,
                    z=-700.0,
                    faction="player",
                ),
                MapAsset(
                    asset_id="trig_evac",
                    asset_type="trig_evac",
                    name="Extraction Dust-Off Zone",
                    x=-350.0,
                    y=5.0,
                    z=-900.0,
                    faction="player",
                    trigger_radius=50.0,
                    trigger_action="evac_complete",
                    trigger_message="Dropship inbound!",
                ),
                MapAsset(
                    asset_id="trig_ambush",
                    asset_type="trig_ambush",
                    name="Canyon Ambush Line",
                    x=-480.0,
                    y=5.0,
                    z=-720.0,
                    faction="enemy",
                    trigger_radius=70.0,
                    trigger_action="spawn_ambush",
                    trigger_message="Clan patrol sighted!",
                ),
            ],
        )

        d = proj.to_dict()
        restored = MapPackProject.from_dict(d)

        self.assertEqual(restored.pack_id, self.test_pack_id)
        self.assertEqual(restored.objectives["briefing_text"], "Clan garrison sighted in Sector 4. Strike hard and fast.")
        self.assertEqual(len(restored.objectives["primary"]), 2)
        self.assertEqual(restored.drop_config["weapons"]["right_arm"], "Clan Gauss Rifle")
        self.assertEqual(len(restored.drop_config["lancemates"]), 2)

        evac_asset = next(a for a in restored.assets if a.asset_type == "trig_evac")
        self.assertEqual(evac_asset.trigger_radius, 50.0)
        self.assertEqual(evac_asset.trigger_action, "evac_complete")

    def test_builder_exports_all_dossiers_and_configs(self):
        """Verify MapPackBuilder writes objectives.json, drop_config.json, briefing.txt, and updated cmd."""
        proj = MapPackProject(
            pack_id=self.test_pack_id,
            pack_title="Tranquil Basin Incursion",
            author="Delta Lance",
            base_operation="c1",
            objectives={
                "primary": [
                    {"id": "p1", "desc": "Demolish Smoke Jaguar Radar Array", "target": "comm_center"},
                    {"id": "p2", "desc": "Extract at NAV BAKER", "target": "trig_evac"},
                ],
                "secondary": [
                    {"id": "s1", "desc": "Preserve Marine Dock", "target": "dock"}
                ],
                "briefing_text": "Operation Bulldog continuation: Secure the littoral basin and deny Clan intelligence assets.",
                "audio_track": "action_theme_2",
            },
            drop_config={
                "player_mech": "mech_thor",
                "drop_type": "dropship_insertion",
                "tonnage": 70.0,
                "armor_tons": 13.0,
                "heatsinks": 15,
                "jump_jets": 3,
                "weapons": {
                    "left_arm": "Large Pulse Laser",
                    "right_arm": "Ultra AC/20",
                    "left_torso": "Clan LRM-20",
                    "right_torso": "None",
                    "center_torso": "ER Medium Laser",
                },
                "lancemates": [
                    {"name": "Lt. Alan Mattila", "mech": "mech_bushwacker", "orders": "escort"}
                ],
            },
            assets=[
                MapAsset(
                    asset_id="trig_evac_1",
                    asset_type="trig_evac",
                    name="Extraction Zone",
                    x=-400.0,
                    y=3.0,
                    z=-800.0,
                    trigger_radius=55.0,
                    trigger_action="evac_complete",
                    trigger_message="Dustoff available at NAV BAKER",
                ),
            ],
        )

        builder = MapPackBuilder(self.packs_dir)
        exported_path = builder.build(proj)
        self.assertTrue(exported_path.is_dir())

        # 1. Check objectives.json
        obj_file = exported_path / "objectives.json"
        self.assertTrue(obj_file.is_file(), "objectives.json was not generated")
        obj_data = json.loads(obj_file.read_text(encoding="utf-8"))
        self.assertEqual(len(obj_data["primary"]), 2)
        self.assertEqual(obj_data["primary"][0]["desc"], "Demolish Smoke Jaguar Radar Array")
        self.assertEqual(len(obj_data["triggers"]), 1)
        self.assertEqual(obj_data["triggers"][0]["radius"], 55.0)

        # 2. Check drop_config.json
        drop_file = exported_path / "drop_config.json"
        self.assertTrue(drop_file.is_file(), "drop_config.json was not generated")
        drop_data = json.loads(drop_file.read_text(encoding="utf-8"))
        self.assertEqual(drop_data["player_mech"], "mech_thor")
        self.assertEqual(drop_data["weapons"]["right_arm"], "Ultra AC/20")
        self.assertEqual(drop_data["jump_jets"], 3)

        # 3. Check briefing.txt
        briefing_file = exported_path / "briefing.txt"
        self.assertTrue(briefing_file.is_file(), "briefing.txt was not generated")
        briefing_text = briefing_file.read_text(encoding="utf-8")
        self.assertIn("COMBAT MISSION BRIEFING DOSSIER", briefing_text)
        self.assertIn("Demolish Smoke Jaguar Radar Array", briefing_text)
        self.assertIn("Ultra AC/20", briefing_text)
        self.assertIn("Lt. Alan Mattila", briefing_text)

        # 4. Check manifest.json
        manifest_file = exported_path / "manifest.json"
        manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
        self.assertEqual(manifest_data["objectives_summary"]["primary_count"], 2)
        self.assertEqual(manifest_data["objectives_summary"]["triggers_count"], 1)
        self.assertEqual(manifest_data["drop_summary"]["mech"], "mech_thor")

        # 5. Check runner script
        runner_file = exported_path / f"Play Map - {self.test_pack_id}.cmd"
        self.assertTrue(runner_file.is_file(), "Play Map cmd was not generated")
        runner_text = runner_file.read_text(encoding="utf-8")
        self.assertIn('type "%MAP_DIR%briefing.txt"', runner_text)


if __name__ == "__main__":
    unittest.main()
