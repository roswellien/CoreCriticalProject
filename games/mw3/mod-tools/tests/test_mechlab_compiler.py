import unittest
import json
import tempfile
import shutil
from pathlib import Path

from editor.core.map_pack import compile_mech_loadout, MapPackBuilder, MapPackProject, MapAsset
from editor.config import cache_directory


class TestMechLabCompiler(unittest.TestCase):
    def setUp(self):
        self.cache_dir = cache_directory()
        self.global_reader = self.cache_dir / "global_reader"
        self.c1_reader = self.cache_dir / "c1_reader"

    def test_compile_mech_loadout_weapons_and_armor(self):
        if not (self.global_reader / "dfn_madcat.zrd.json").is_file():
            self.skipTest("dfn_madcat.zrd.json cache not available")

        with tempfile.TemporaryDirectory() as td:
            reader_dir = Path(td) / "reader"
            reader_dir.mkdir()
            shutil.copyfile(
                self.global_reader / "dfn_madcat.zrd.json",
                reader_dir / "dfn_madcat.zrd.json",
            )
            # Create a simple manifest.json
            (reader_dir / "manifest.json").write_text(json.dumps([
                {"name": "dfn_madcat.zrd", "flags": 25647, "info": {"Valid": {"comment": "", "datetime": "2026-11-02T12:00:00Z"}}}
            ]), encoding="utf-8")

            drop_config = {
                "player_mech": "mech_madcat",
                "tonnage": 75.0,
                "armor_tons": 16.5,
                "heatsinks": 22,
                "jump_jets": 4,
                "weapons": {
                    "left_arm": "ER PPC",
                    "right_arm": "Gauss Rifle",
                    "left_torso": "Clan LRM-20",
                    "right_torso": "Streak SRM-6",
                    "center_torso": "Medium Pulse Laser",
                },
            }

            summary = compile_mech_loadout(reader_dir, drop_config)
            self.assertIsNotNone(summary)
            self.assertIn("Madcat loadout", summary)
            self.assertIn("16.5T armor", summary)
            self.assertIn("22 HS", summary)
            self.assertIn("4 JJ", summary)

            # Inspect updated JSON
            dfn = json.loads((reader_dir / "dfn_madcat.zrd.json").read_text(encoding="utf-8"))
            lst = dfn[0] if isinstance(dfn[0], list) else dfn
            configs = None
            for i in range(0, len(lst), 2):
                if lst[i] == "configurations":
                    configs = lst[i + 1]
                    break
            self.assertIsNotNone(configs)

            primary = configs[1]
            primary_dict = {primary[j]: primary[j + 1] for j in range(0, len(primary), 2)}

            # Check weapons
            wpns = primary_dict.get("weapons", [])
            wpn_types = [w[0] for w in wpns]
            self.assertIn("ERPPC", wpn_types)
            self.assertIn("GaussRifle", wpn_types)
            self.assertIn("LRM20", wpn_types)
            self.assertIn("StreakSRM6", wpn_types)
            self.assertIn("PulseLaser_Medium", wpn_types)

            # Check armor mass
            armor = primary_dict.get("armor", [])
            armor_dict = {armor[j]: armor[j + 1] for j in range(0, len(armor), 2)}
            self.assertEqual(armor_dict.get("mass"), [16.5])

            # Check equipment (heatsinks + jumpjets)
            equipment = primary_dict.get("equipment", [])
            dsink_count = sum(1 for eq in equipment if eq[0] == "dsink")
            jumpjet_count = sum(1 for eq in equipment if eq[0] == "jumpjet")
            self.assertEqual(dsink_count, 22)
            self.assertEqual(jumpjet_count, 4)

    def test_full_pack_build_with_mech_drop(self):
        if not self.c1_reader.is_dir():
            self.skipTest("c1_reader cache not available")

        with tempfile.TemporaryDirectory() as td:
            builder = MapPackBuilder(packs_root=Path(td))
            project = MapPackProject(
                pack_id="mech_drop_pack",
                pack_title="Mech Drop Test",
                base_operation="c1",
                drop_config={
                    "player_mech": "mech_bushwacker",
                    "tonnage": 55.0,
                    "armor_tons": 11.5,
                    "heatsinks": 14,
                    "jump_jets": 0,
                    "weapons": {
                        "left_arm": "ER Medium Laser",
                        "right_arm": "AutoCannon/10",
                        "left_torso": "Clan LRM-10",
                        "right_torso": "None",
                        "center_torso": "Small Pulse Laser",
                    },
                },
                assets=[
                    MapAsset("sp1", "spawn", "Player Spawn", -1800, 10, -1900, faction="player")
                ],
            )
            pack_dir = builder.build(project)
            self.assertTrue((pack_dir / "zbd/c1/reader.zbd").is_file())
            self.assertGreater((pack_dir / "zbd/c1/reader.zbd").stat().st_size, 50000)

            manifest = json.loads((pack_dir / "manifest.json").read_text(encoding="utf-8"))
            reader_entry = next((f for f in manifest["files"] if "c1/reader.zbd" in f["target"]), None)
            self.assertIsNotNone(reader_entry)
            self.assertIn("Bushwacker loadout", reader_entry["summary"])


if __name__ == "__main__":
    unittest.main()
