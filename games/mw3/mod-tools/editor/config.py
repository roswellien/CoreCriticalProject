"""Local paths shared by editor setup and archive readers.

Settings contain user paths only and live under ignored local/mod-tools.
No module creates files in the original installation. Missing configuration
retains the existing development layout; explicit invalid settings fail visibly.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_TOOL_DIR = PROJECT_ROOT / (
    "local/tools/mech3ax-v0.7.0-rc3-windows/" "mech3ax-v0.7.0-rc3-x86_64-pc-windows-msvc"
)


def settings_path() -> Path:
    """An override permits isolated setup/tests without changing live settings."""
    return Path(
        os.environ.get("MW34_MOD_TOOLS_CONFIG", PROJECT_ROOT / "local/mod-tools/settings.json")
    ).resolve()


def load_settings() -> dict:
    """Read schema-v1 local settings, or return an empty development configuration.

    A present but malformed settings file raises rather than silently redirecting
    the tools to another installation. This function does not create directories.
    """
    path = settings_path()
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError(f"Unsupported Mod Tools settings: {path}; rerun setup.")
    return data


def configured_path(name: str, default: Path) -> Path:
    """Resolve an absolute configured path, using default only when the key is absent.

    Resolution follows existing symlinks. Setup separately checks that writable
    destinations stay outside the selected original installation.
    """
    value = load_settings().get(name)
    if value is None:
        return default.resolve()
    if not isinstance(value, str) or not Path(value).is_absolute():
        raise ValueError(f"Mod Tools setting {name} must be an absolute path.")
    return Path(value).resolve()


def game_directory() -> Path:
    """Return the read-only installation root selected by setup."""
    return configured_path("game_root", PROJECT_ROOT / "MW3")


def tool_directory() -> Path:
    """Return the externally supplied Mech3AX executable directory."""
    return configured_path("mech3ax_dir", DEFAULT_TOOL_DIR)


def cache_directory() -> Path:
    """Return the writable extraction cache, distinct from original game files."""
    return configured_path("cache_dir", PROJECT_ROOT / "local/mod-cache")
