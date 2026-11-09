"""Local paths shared by editor setup and archive readers.

Settings contain user paths only and live under ignored local/mod-tools.
No module creates files in the original installation. Missing configuration
retains the existing development layout; explicit invalid settings fail visibly.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional, List

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
    configured = load_settings().get("game_root")
    if configured:
        return Path(configured).resolve()

    detected = detect_game_directory()
    if detected:
        return detected

    return configured_path("game_root", PROJECT_ROOT / "MW3")


def is_game_installed() -> bool:
    """Check if the currently configured or detected game directory contains zbd/."""
    try:
        gdir = game_directory()
        return (gdir / "zbd").is_dir() or (gdir / "ZBD").is_dir()
    except Exception:
        return False


def detect_game_directory() -> Optional[Path]:
    """Search for a valid MechWarrior 3 installation directory containing zbd/."""
    candidates = [
        PROJECT_ROOT / "MW3",
        Path.cwd() / "MW3",
        Path.cwd().parent / "MW3",
        Path("C:/Games/MechWarrior 3"),
        Path("C:/Games/MW3"),
        Path("D:/Games/MechWarrior 3"),
        Path("D:/Games/MW3"),
        Path("C:/Program Files (x86)/MicroProse/MechWarrior 3"),
    ]
    for c in candidates:
        if (c / "zbd").is_dir() or (c / "ZBD").is_dir():
            return c.resolve()
    return None


def set_game_directory(path: Path) -> bool:
    """Validate and persist the selected game root directory into settings.json."""
    resolved = path.resolve()
    if not (resolved / "zbd").is_dir() and not (resolved / "ZBD").is_dir():
        if resolved.name.lower() == "zbd" and resolved.parent.is_dir():
            resolved = resolved.parent
        else:
            raise ValueError(f"Directory {resolved} does not contain a 'zbd' folder.")

    spath = settings_path()
    spath.parent.mkdir(parents=True, exist_ok=True)
    settings = {}
    if spath.is_file():
        try:
            settings = json.loads(spath.read_text(encoding="utf-8"))
        except Exception:
            settings = {}
    settings["schema_version"] = 1
    settings["game_root"] = str(resolved)
    spath.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return True


def tool_directory() -> Path:
    """Return the externally supplied Mech3AX executable directory."""
    configured = load_settings().get("mech3ax_dir")
    if configured:
        return Path(configured).resolve()

    # Check for bundled bin directory (e.g. in packaged standalone distribution)
    package_bin = (Path(__file__).resolve().parents[2] / "bin").resolve()
    if (package_bin / "unzbd.exe").is_file():
        return package_bin

    root_bin = (PROJECT_ROOT / "bin").resolve()
    if (root_bin / "unzbd.exe").is_file():
        return root_bin

    return configured_path("mech3ax_dir", DEFAULT_TOOL_DIR)


def cache_directory() -> Path:
    """Return the writable extraction cache, distinct from original game files."""
    return configured_path("cache_dir", PROJECT_ROOT / "local/mod-cache")
