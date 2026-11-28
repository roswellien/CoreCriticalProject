"""Where the runner keeps its settings, catalog, saved setups and batches.

Shared by the window (arena_runner.py) and the command line (run_batch.py),
so both find the same game folder, mw3.exe and catalog.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

HOME = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "CoreCritical" / "arena-runner"
SETTINGS = HOME / "settings.json"
PILOTS = Path(__file__).resolve().parent / "pilots.json"


def load_settings() -> dict:
    try:
        return json.loads(SETTINGS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_settings(settings: dict) -> None:
    HOME.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(settings, indent=1), encoding="utf-8")
