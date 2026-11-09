import unittest
import json
import tempfile
import shutil
from pathlib import Path

from editor.core.map_pack import bake_terrain_heights, MapPackBuilder, MapPackProject, TerrainConfig, MapAsset
from editor.config import cache_directory


class TestTerrainBaking(unittest.TestCase):
    def setUp(self):
        self.cache_dir = cache_directory()
        self.c1_gamez = self.cache_dir / "c1_gamez"

    def test_bake_terrain_heights_empty(self):
        with tempfile.TemporaryDirectory() as td:
            count = bake_terrain_heights(Path(td), {})
            self.assertEqual(count, 0)

    def test_bake_terrain_heights_modifies_vertices(self):
        if not (self.c1_gamez / "models.json").is_file() or not (self.c1_gamez / "nodes.json").is_file():
            self.skipTest("c1_gamez cache not available")

        with tempfile.TemporaryDirectory() as td:
            temp_gamez = Path(td) / "gamez"
            shutil.copytree(self.c1_gamez, temp_gamez)

            # Test coordinates corresponding to authentic c1 terrain vertices
            height_mods = {
                "-1839.0,-1964.7": 55.5,
                "-1861.3,-1983.9": 62.0,
            }

            modified_count = bake_terrain_heights(temp_gamez, height_mods)
            self.assertGreaterEqual(modified_count, 2)

            # Verify in saved models.json
            models = json.loads((temp_gamez / "models.json").read_text(encoding="utf-8"))
            m1089 = models[1089]
            # Vertex 0 should be close to 55.5
            v0 = m1089["vertices"][0]
            self.assertAlmostEqual(v0["y"], 55.5, delta=0.5)

    def test_full_pack_build_with_terrain_baking(self):
        if not self.c1_gamez.is_dir():
            self.skipTest("c1_gamez cache not available")

        with tempfile.TemporaryDirectory() as td:
            builder = MapPackBuilder(packs_root=Path(td))
            project = MapPackProject(
                pack_id="terrain_bake_pack",
                pack_title="Terrain Bake Test",
                base_operation="c1",
                terrain=TerrainConfig(
                    biome="coastal",
                    height_modifications={
                        "-1839.0,-1964.7": 40.0,
                    },
                ),
                assets=[
                    MapAsset("sp1", "spawn", "Player Spawn", -1800, 10, -1900, faction="player")
                ],
            )
            pack_dir = builder.build(project)
            self.assertTrue((pack_dir / "zbd/c1/gamez.zbd").is_file())
            self.assertGreater((pack_dir / "zbd/c1/gamez.zbd").stat().st_size, 1000000)

            manifest = json.loads((pack_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["terrain_summary"]["sculpted_vertices_count"], 1)
            gamez_entry = next((f for f in manifest["files"] if "gamez.zbd" in f["target"]), None)
            self.assertIsNotNone(gamez_entry)
            self.assertIn("sculpted terrain vertices baked", gamez_entry["summary"])


if __name__ == "__main__":
    unittest.main()
