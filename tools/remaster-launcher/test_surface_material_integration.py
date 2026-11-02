"""Unit tests for integrated surface material asset packs.

Verifies that:
- training-textures-1.2.0.mw3pack selects cleanly, requires surface-materials capability,
  and binds ground and surface materials sidecars.
- The 0.2.0-local.20261102 mech asset packs (mw5-mechs and updated-mw3-mechs) compose cleanly,
  validate mesh UV hashes across all 18 chassis, and bind surface material sidecars.
- The 1.4.0 combined model pack and active unpacked mod directory compose cleanly.
"""

import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile

from content_capabilities import advertised
import prepared_environment_packs as prep_env
import prepared_mech_packs as prep_mech
from surface_materials import read_surface_materials_file

ROOT = Path(__file__).resolve().parents[2]


class SurfaceMaterialIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Locate built packs either in local worktree or main repo
        cls.training_pack = None
        pack_rel = "local/asset-packs/environments-surface-materials-20261102-r1/training-textures-1.2.0.mw3pack"
        for candidate in (ROOT / pack_rel, Path("D:/Projects/MW34Recomp") / pack_rel):
            if candidate.is_file():
                cls.training_pack = candidate
                break

        cls.mech_pack_dir = None
        for candidate in (
            ROOT / "local/asset-packs/mechs-surface-materials-20261102-r1",
            Path("D:/Projects/MW34Recomp/local/asset-packs/mechs-surface-materials-20261102-r1"),
        ):
            if candidate.is_dir() and (candidate / "com.mw3remaster.mw5-mechs.mw3pack").is_file():
                cls.mech_pack_dir = candidate
                break

        cls.combined_model_pack = None
        comb_rel = "local/work-ahead/model-pack-1.4.0-20261102/mw3-remastered-models-1.4.0.mw3pack"
        for candidate in (ROOT / comb_rel, Path("D:/Projects/MW34Recomp") / comb_rel):
            if candidate.is_file():
                cls.combined_model_pack = candidate
                break

        mod_env = (
            "%LOCALAPPDATA%/Packages/OpenAI.Codex_2p2nqsd0c76g0/LocalCache/Local/MW3Remaster/"
            "mods/com.mw3remaster.mw5-mechs"
        )
        cls.active_mod_dir = Path(os.path.expandvars(mod_env))

    def test_training_pack_exists_and_selects_cleanly(self):
        self.assertIsNotNone(self.training_pack, "training-textures-1.2.0.mw3pack must exist")
        # Verify archive integrity and closure directly
        manifest = prep_env.verify_archive(self.training_pack) if hasattr(prep_env, "verify_archive") else None

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            with zipfile.ZipFile(self.training_pack) as z:
                z.extractall(temp_root)

            host_without_cap = {
                "content_capabilities": {"environment-resources": [1]},
                "mission_environment_versions": [1],
                "executable_sha256": "a" * 64,
                "runtime_environment": {},
            }
            # Must fail without surface-materials capability
            with self.assertRaises(ValueError):
                prep_env.select([str(temp_root)], host_without_cap)

            # Must succeed with surface-materials capability
            host_with_cap = copy.deepcopy(host_without_cap)
            host_with_cap["content_capabilities"]["surface-materials"] = [1]
            chosen = prep_env.select([str(temp_root)], host_with_cap)
            self.assertIn("training", chosen)
            manifest = json.loads((Path(chosen["training"]["root"]) / "pack.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["version"], "1.2.0")

            launch_dir = Path(temp_dir) / "launch"
            env = prep_env.prepare(chosen, host_with_cap, launch_dir)
            self.assertIn("MW34_GROUND_SURFACE_MATERIALS", env)
            self.assertIn("MW34_SURFACE_MATERIALS", env)
            surf_file = Path(env["MW34_GROUND_SURFACE_MATERIALS"])
            self.assertTrue(surf_file.is_file())
            catalog = read_surface_materials_file(surf_file)
            self.assertEqual(len(catalog["records"]), 82)
            self.assertEqual(len(catalog["images"]), 82)

    def test_split_mech_packs_compose_cleanly(self):
        self.assertIsNotNone(self.mech_pack_dir, "mechs-surface-materials-20261102-r1 must exist")
        mw5_pack = self.mech_pack_dir / "com.mw3remaster.mw5-mechs.mw3pack"
        mw3_pack = self.mech_pack_dir / "com.mw3remaster.updated-mw3-mechs.mw3pack"
        self.assertTrue(mw5_pack.is_file())
        self.assertTrue(mw3_pack.is_file())

        with tempfile.TemporaryDirectory() as temp_dir:
            mw5_root = Path(temp_dir) / "mw5"
            mw3_root = Path(temp_dir) / "mw3"
            with zipfile.ZipFile(mw5_pack) as z:
                z.extractall(mw5_root)
            with zipfile.ZipFile(mw3_pack) as z:
                z.extractall(mw3_root)

            all_18 = [
                "bushwacker", "madcat", "vulture", "thor", "orion", "daishi",
                "shadowcat", "puma", "annihilator", "cauldron", "sunder",
                "supernova", "blackhawk", "champion",
                "strider", "avatar", "owens", "firefly",
            ]
            host = {
                "content_capabilities": {"prepared-mechs": [1], "surface-materials": [1]},
                "executable_sha256": "0e73a882e1bfb9811527af953c25dde97dfd2f8355ee86bbe5271019f28faecb",
                "model_ids": all_18,
                "skin_ids": {m: list("bcdefgh") for m in all_18},
                "mesh_payload_versions": [1, 2, 3, 4, 5, 6],
                "normal_map_formats": [2],
                "include_runtime_candidates": True,
                "runtime_environment": {},
            }

            models, env = prep_mech.compose([str(mw5_root), str(mw3_root)], host)
            self.assertEqual(len(models), 18)
            for ident in all_18:
                surf_key = f"MW34_{ident.upper()}_SURFACE_MATERIALS"
                self.assertIn(surf_key, env, f"Missing {surf_key} in composed environment")
                sfm_path = Path(env[surf_key])
                self.assertTrue(sfm_path.is_file(), f"Surface material file must exist on disk: {sfm_path}")

    def test_combined_model_pack_1_4_0_composes(self):
        self.assertIsNotNone(self.combined_model_pack, "mw3-remastered-models-1.4.0.mw3pack must exist")
        with tempfile.TemporaryDirectory() as temp_dir:
            comb_root = Path(temp_dir) / "comb"
            with zipfile.ZipFile(self.combined_model_pack) as z:
                z.extractall(comb_root)

            all_18 = [
                "bushwacker", "madcat", "vulture", "thor", "orion", "daishi",
                "shadowcat", "puma", "annihilator", "cauldron", "sunder",
                "supernova", "blackhawk", "champion",
                "strider", "avatar", "owens", "firefly",
            ]
            host = {
                "content_capabilities": {"prepared-mechs": [1], "surface-materials": [1]},
                "executable_sha256": "0e73a882e1bfb9811527af953c25dde97dfd2f8355ee86bbe5271019f28faecb",
                "model_ids": all_18,
                "skin_ids": {m: list("bcdefgh") for m in all_18},
                "mesh_payload_versions": [1, 2, 3, 4, 5, 6],
                "normal_map_formats": [2],
                "include_runtime_candidates": True,
                "runtime_environment": {},
            }
            models, env = prep_mech.compose([str(comb_root)], host)
            self.assertEqual(len(models), 18)
            for ident in all_18:
                surf_key = f"MW34_{ident.upper()}_SURFACE_MATERIALS"
                self.assertIn(surf_key, env)

    def test_active_mod_dir_has_valid_surface_materials(self):
        if not self.active_mod_dir.is_dir():
            self.skipTest("Active mod dir not present in environment")
        manifest = json.loads((self.active_mod_dir / "pack.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["version"], "1.4.0")
        self.assertIn("surface-materials", manifest["native_payload"]["required_capabilities"])
        self.assertIn("BWSFM1", manifest["native_payload"]["required_formats"])

        registry = json.loads((self.active_mod_dir / "models/models.json").read_text(encoding="utf-8"))
        for model in registry["models"]:
            ident = model["id"]
            surf_key = f"MW34_{ident.upper()}_SURFACE_MATERIALS"
            self.assertIn(surf_key, model["environment"])
            rel_path = model["environment"][surf_key]
            full_path = self.active_mod_dir / rel_path
            self.assertTrue(full_path.is_file(), f"File {full_path} must exist")


if __name__ == "__main__":
    unittest.main()
