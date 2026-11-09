"""Unit tests for MW3 Campaign Project and CampaignBuilder."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_ROOT))

from editor.core.campaign import (
    CampaignBuilder,
    CampaignMission,
    CampaignProject,
    campaign_directory,
)


class TestCampaignBuilder(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.campaigns_root = self.root / "mods/campaign-packs"
        self.map_packs_root = self.root / "mods/map-packs"
        self.game_root = self.root / "MW3"
        self.builder = CampaignBuilder(
            campaigns_root=self.campaigns_root,
            map_packs_root=self.map_packs_root,
            game_root=self.game_root,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_campaign_directory_validation(self):
        valid = campaign_directory(self.campaigns_root, "operation_tranquil")
        self.assertEqual(valid.name, "operation_tranquil")

        with self.assertRaises(ValueError):
            campaign_directory(self.campaigns_root, "../evil_path")

        with self.assertRaises(ValueError):
            campaign_directory(self.campaigns_root, "invalid characters!@#")

    def test_campaign_build_and_validation(self):
        m1 = CampaignMission(
            mission_id="m01_recon",
            pack_id="c1_recon_pack",
            title="Operation Damocles: Recon Probe",
            briefing_text="Scout enemy Clan radar stations in Sector 4.",
            next_mission_id="m02_strike",
        )
        m2 = CampaignMission(
            mission_id="m02_strike",
            pack_id="c1_strike_pack",
            title="Operation Damocles: Main Assault",
            briefing_text="Engage Clan Smoke Jaguar command post.",
            next_mission_id=None,
            branch_conditions={"bonus_intel_gathered": "m02_strike"},
        )

        campaign = CampaignProject(
            campaign_id="damocles_campaign",
            campaign_title="Operation Damocles",
            author="Test Pilot",
            version="1.0.0",
            description="2-mission test campaign",
            missions=[m1, m2],
        )

        out_dir = self.builder.build(campaign)
        self.assertTrue(out_dir.is_dir())

        # Check campaign.json
        campaign_json = out_dir / "campaign.json"
        self.assertTrue(campaign_json.is_file())
        data = json.loads(campaign_json.read_text(encoding="utf-8"))
        self.assertEqual(data["campaign_id"], "damocles_campaign")
        self.assertEqual(len(data["missions"]), 2)

        # Check manifest.json
        manifest_json = out_dir / "manifest.json"
        self.assertTrue(manifest_json.is_file())
        man_data = json.loads(manifest_json.read_text(encoding="utf-8"))
        self.assertEqual(man_data["total_missions"], 2)
        self.assertEqual(man_data["mission_ids"], ["m01_recon", "m02_strike"])

        # Check generated launcher script
        launcher = out_dir / "Play Campaign - damocles_campaign.cmd"
        self.assertTrue(launcher.is_file())
        cmd_text = launcher.read_text(encoding="utf-8")
        self.assertIn("Operation Damocles", cmd_text)
        self.assertIn("m01_recon", cmd_text)
        self.assertIn("m02_strike", cmd_text)

    def test_campaign_validation_errors(self):
        # Empty missions
        empty_c = CampaignProject(campaign_id="empty_c", campaign_title="Empty", missions=[])
        with self.assertRaises(ValueError):
            self.builder.validate_campaign(empty_c)

        # Duplicate mission IDs
        m1 = CampaignMission(mission_id="m01", pack_id="p1", title="M1")
        m2 = CampaignMission(mission_id="m01", pack_id="p2", title="M2 Duplicate")
        dup_c = CampaignProject(campaign_id="dup_c", campaign_title="Dup", missions=[m1, m2])
        with self.assertRaises(ValueError):
            self.builder.validate_campaign(dup_c)

        # Invalid next_mission_id
        m_bad = CampaignMission(mission_id="m01", pack_id="p1", title="M1", next_mission_id="nonexistent_id")
        bad_next_c = CampaignProject(campaign_id="bad_c", campaign_title="Bad", missions=[m_bad])
        with self.assertRaises(ValueError):
            self.builder.validate_campaign(bad_next_c)


if __name__ == "__main__":
    unittest.main()
