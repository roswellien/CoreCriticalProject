"""Multi-Mission Campaign Architecture and Pack Compiler for MechWarrior 3.

Compiles branching or linear campaign projects into standalone campaign packs
under mods/campaign-packs/<campaign_id>/ with progression validation, salvage
continuity rules, pilot roster management, and a unified multi-stage launcher.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


def campaign_directory(campaigns_root: Path, campaign_id: str) -> Path:
    """Resolve one campaign directory safely within its root folder."""
    if not isinstance(campaign_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", campaign_id):
        raise ValueError("Campaign ID must be 1–64 ASCII letters, digits, hyphens or underscores.")
    root = campaigns_root.resolve()
    destination = (root / campaign_id).resolve()
    if not destination.is_relative_to(root):
        raise ValueError("Campaign directory resolves outside the campaigns folder.")
    return destination


@dataclass
class CampaignMission:
    """A single mission node within a linear or branching campaign graph."""

    mission_id: str
    pack_id: str
    title: str
    briefing_text: str = ""
    theater: str = "Tranquil"
    audio_track: str = "action_theme_1"
    video_intro: str = ""
    video_outro: str = ""
    primary_objectives: List[Dict[str, Any]] = field(default_factory=list)
    secondary_objectives: List[Dict[str, Any]] = field(default_factory=list)
    next_mission_id: Optional[str] = None
    branch_conditions: Dict[str, str] = field(default_factory=dict)
    salvage_config: Dict[str, Any] = field(
        default_factory=lambda: {
            "enabled": True,
            "carryover_chassis": True,
            "carryover_weapons": True,
            "repair_points": 500,
        }
    )
    pilot_roster: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "pack_id": self.pack_id,
            "title": self.title,
            "briefing_text": self.briefing_text,
            "theater": self.theater,
            "audio_track": self.audio_track,
            "video_intro": self.video_intro,
            "video_outro": self.video_outro,
            "primary_objectives": self.primary_objectives,
            "secondary_objectives": self.secondary_objectives,
            "next_mission_id": self.next_mission_id,
            "branch_conditions": self.branch_conditions,
            "salvage_config": self.salvage_config,
            "pilot_roster": self.pilot_roster,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CampaignMission:
        return cls(
            mission_id=data.get("mission_id", f"m_{int(id(data))}"),
            pack_id=data.get("pack_id", ""),
            title=data.get("title", "Untitled Mission"),
            briefing_text=data.get("briefing_text", ""),
            theater=data.get("theater", "Tranquil"),
            audio_track=data.get("audio_track", "action_theme_1"),
            video_intro=data.get("video_intro", ""),
            video_outro=data.get("video_outro", ""),
            primary_objectives=data.get("primary_objectives", []),
            secondary_objectives=data.get("secondary_objectives", []),
            next_mission_id=data.get("next_mission_id"),
            branch_conditions=data.get("branch_conditions", {}),
            salvage_config=data.get(
                "salvage_config",
                {
                    "enabled": True,
                    "carryover_chassis": True,
                    "carryover_weapons": True,
                    "repair_points": 500,
                },
            ),
            pilot_roster=data.get("pilot_roster", []),
        )


@dataclass
class CampaignProject:
    """Serializable campaign definition with multi-mission routing and continuity."""

    campaign_id: str
    campaign_title: str
    author: str = "Community Modder"
    version: str = "1.0.0"
    description: str = "Dynamic custom campaign for MechWarrior 3"
    faction: str = "Inner Sphere"  # Inner Sphere, Clan Smoke Jaguar, Mercenary
    theater: str = "Tranquil Sector"
    missions: List[CampaignMission] = field(default_factory=list)
    continuity_rules: Dict[str, Any] = field(
        default_factory=lambda: {
            "salvage_enabled": True,
            "loss_permitted": False,
            "shared_pilots": True,
            "starting_salvage_points": 1000,
        }
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format": "MW3_CAMPAIGN_V1",
            "campaign_id": self.campaign_id,
            "campaign_title": self.campaign_title,
            "author": self.author,
            "version": self.version,
            "description": self.description,
            "faction": self.faction,
            "theater": self.theater,
            "continuity_rules": self.continuity_rules,
            "missions": [m.to_dict() for m in self.missions],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CampaignProject:
        missions = [CampaignMission.from_dict(m) for m in data.get("missions", [])]
        return cls(
            campaign_id=data.get("campaign_id", "custom_campaign"),
            campaign_title=data.get("campaign_title", "Custom Campaign"),
            author=data.get("author", "Community Modder"),
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            faction=data.get("faction", "Inner Sphere"),
            theater=data.get("theater", "Tranquil Sector"),
            continuity_rules=data.get(
                "continuity_rules",
                {
                    "salvage_enabled": True,
                    "loss_permitted": False,
                    "shared_pilots": True,
                    "starting_salvage_points": 1000,
                },
            ),
            missions=missions,
        )


class CampaignBuilder:
    """Validates and packages a campaign project into an executable mod directory."""

    def __init__(self, campaigns_root: Path, map_packs_root: Path, game_root: Path):
        self.campaigns_root = Path(campaigns_root)
        self.map_packs_root = Path(map_packs_root)
        self.game_root = Path(game_root)

    def validate_campaign(self, campaign: CampaignProject) -> None:
        """Validate ID constraints, mission continuity, and branch references."""
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", campaign.campaign_id):
            raise ValueError(f"Invalid campaign ID format: {campaign.campaign_id}")

        if not campaign.missions:
            raise ValueError("Campaign must define at least one mission.")

        mission_ids = set()
        for idx, m in enumerate(campaign.missions):
            if not m.mission_id or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", m.mission_id):
                raise ValueError(f"Invalid mission ID format at index {idx}: {m.mission_id}")
            if m.mission_id in mission_ids:
                raise ValueError(f"Duplicate mission ID in campaign: {m.mission_id}")
            mission_ids.add(m.mission_id)

        # Validate branching and next mission pointers
        for m in campaign.missions:
            if m.next_mission_id and m.next_mission_id not in mission_ids:
                raise ValueError(
                    f"Mission '{m.mission_id}' points to unknown next_mission_id: '{m.next_mission_id}'"
                )
            for cond_name, target_id in m.branch_conditions.items():
                if target_id and target_id not in mission_ids:
                    raise ValueError(
                        f"Mission '{m.mission_id}' branch '{cond_name}' points to unknown target: '{target_id}'"
                    )

    def build(self, campaign: CampaignProject) -> Path:
        """Compile campaign manifest and generate multi-stage launcher."""
        self.validate_campaign(campaign)

        self.campaigns_root.mkdir(parents=True, exist_ok=True)
        out_dir = campaign_directory(self.campaigns_root, campaign.campaign_id)
        out_dir.mkdir(parents=True, exist_ok=True)

        # 1. Write campaign.json
        campaign_file = out_dir / "campaign.json"
        campaign_file.write_text(json.dumps(campaign.to_dict(), indent=2), encoding="utf-8")

        # 2. Write manifest.json
        manifest = {
            "format": "MW3_CAMPAIGN_MANIFEST_V1",
            "campaign_id": campaign.campaign_id,
            "campaign_title": campaign.campaign_title,
            "author": campaign.author,
            "version": campaign.version,
            "description": campaign.description,
            "faction": campaign.faction,
            "theater": campaign.theater,
            "total_missions": len(campaign.missions),
            "mission_ids": [m.mission_id for m in campaign.missions],
            "salvage_enabled": campaign.continuity_rules.get("salvage_enabled", True),
        }
        manifest_file = out_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        # 3. Generate multi-stage interactive launcher: Play Campaign - <id>.cmd
        launcher_file = out_dir / f"Play Campaign - {campaign.campaign_id}.cmd"
        self._generate_campaign_launcher(campaign, launcher_file)

        return out_dir

    def _generate_campaign_launcher(self, campaign: CampaignProject, launcher_path: Path) -> None:
        """Generate a Windows batch / PowerShell interactive campaign runner."""
        mission_menu_lines = []
        mission_dispatch_cases = []

        for idx, m in enumerate(campaign.missions, start=1):
            mission_menu_lines.append(f"echo   [{idx}] {m.title} ({m.mission_id})")
            # Batch case block
            mission_dispatch_cases.append(f"if \"%CHOICE%\"==\"{idx}\" goto run_m_{idx}")

        mission_launch_blocks = []
        for idx, m in enumerate(campaign.missions, start=1):
            pack_id = m.pack_id or campaign.campaign_id
            mission_launch_blocks.append(
                f"""
:run_m_{idx}
echo.
echo ===============================================================================
echo  Executing Mission {idx}: {m.title}
echo ===============================================================================
echo  Map Pack: {pack_id}
echo  Theater:  {m.theater}
echo.
set MW34_CAMPAIGN_ID={campaign.campaign_id}
set MW34_MISSION_ID={m.mission_id}
set MW34_MAP_PACK={pack_id}
set MW34_WEATHER=1

REM Find launcher for this mission's map pack
set PACK_LAUNCHER=%PROJECT_ROOT%\\mods\\map-packs\\{pack_id}\\Play Map - {pack_id}.cmd
if exist "%PACK_LAUNCHER%" (
    call "%PACK_LAUNCHER%"
) else (
    echo [ERROR] Map pack launcher not found: %PACK_LAUNCHER%
    echo Please export map pack '%pack_id%' from Map Studio before launching.
    pause
)
goto menu
"""
            )

        cmd_content = f"""@echo off
setlocal enabledelayedexpansion
title MechWarrior 3 Campaign - {campaign.campaign_title}

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\\..\\..
pushd "%PROJECT_ROOT%"

:menu
cls
echo ===============================================================================
echo  MECHWARRIOR 3 CAMPAIGN: {campaign.campaign_title.upper()}
echo  Author: {campaign.author}   Version: {campaign.version}
echo  Faction: {campaign.faction}   Theater: {campaign.theater}
echo ===============================================================================
echo.
echo Select Mission to Deploy:
echo.
{chr(10).join(mission_menu_lines)}
echo   [Q] Quit Campaign Launcher
echo.
set /p CHOICE="Enter mission choice (1-{len(campaign.missions)}) or Q: "

if /i "%CHOICE%"=="Q" goto done
{chr(10).join(mission_dispatch_cases)}

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto menu

{chr(10).join(mission_launch_blocks)}

:done
popd
exit /b 0
"""
        launcher_path.write_text(cmd_content.strip() + "\n", encoding="utf-8")
