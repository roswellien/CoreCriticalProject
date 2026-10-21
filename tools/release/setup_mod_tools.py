"""Configure the separate Windows Mod Tools source preview.

The user's installation is read-only. This command writes only the tools'
local settings and isolated Python environment. It does not import media,
extract geometry, build a game host, or claim that map export/play is ready.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import struct
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "games/mw3/mod-tools"
sys.path.insert(0, str(TOOLS))
from editor.config import load_settings, settings_path  # noqa: E402

TOOL_HASHES = {
    "unzbd.exe": "51cb49e53323b8d5a2f12fce3929c6aad134d72287f2545db9847626f1a20f0a",
    "rezbd.exe": "ea4d569ace35aaee699bd45f78e73c9c9b988d53a167400f167389c7318f99d1",
}


def validate_inputs(game_root: Path, tool_dir: Path) -> None:
    """Check required archives and the observed Mech3AX build without running it.

    This is editor archive setup, not native executable admission. Exact native
    input identity is a separate unresolved Game / Launcher release boundary.
    """
    missing = [
        name for name in ("zbd/reader.zbd", "zbd/rimage.zbd") if not (game_root / name).is_file()
    ]
    if missing:
        raise ValueError("Selected installation is missing: " + ", ".join(missing))
    for name, expected in TOOL_HASHES.items():
        path = tool_dir / name
        if not path.is_file():
            raise ValueError(
                f"Missing {name}; select the extracted Mech3AX v0.7.0-rc3 Windows x64 folder."
            )
        with path.open("rb") as stream:
            actual = hashlib.file_digest(stream, "sha256").hexdigest()
        if actual != expected:
            raise ValueError(
                f"{name} does not match the recorded v0.7.0-rc3 build. See docs/setup-mod-tools.md."
            )


def write_settings(path: Path, data: dict) -> None:
    """Replace only our settings atomically, preserving them on a failed write."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False, suffix=".tmp"
        ) as stream:
            temporary = Path(stream.name)
            stream.write(json.dumps(data, indent=2) + "\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    """Validate inputs, prepare dependencies and publish settings after success.

    --check reads existing configuration and probes its environment without
    installing packages or writing settings. A normal setup may leave a partial
    virtual environment on failure, but preserves the previous settings file.
    The cache key distinguishes installation paths, not changing archive contents.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, help="Your original MW3 installation (read-only)")
    parser.add_argument(
        "--mech3ax-dir", type=Path, help="Folder containing unzbd.exe and rezbd.exe"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check existing settings/dependencies without installing or writing",
    )
    args = parser.parse_args(argv)
    try:
        if (
            os.name != "nt"
            or struct.calcsize("P") != 8
            or not (3, 11) <= sys.version_info[:2] <= (3, 14)
        ):
            raise ValueError("This preview setup requires Windows and Python 3.11–3.14 (64-bit).")
        saved = load_settings()
        game = args.game_root or saved.get("game_root")
        tools = args.mech3ax_dir or saved.get("mech3ax_dir")
        if not game or not tools:
            parser.error(
                "Supply --game-root and --mech3ax-dir on first setup; see docs/setup-mod-tools.md."
            )
        game_root, tool_dir = Path(game).resolve(), Path(tools).resolve()
        validate_inputs(game_root, tool_dir)
        # Every writable setup path must stay outside the selected installation.
        environment = ROOT / ".venv-mod-tools"
        settings_file = settings_path()
        # Separate installations must not reuse one another's extracted archives.
        installation_key = hashlib.sha256(str(game_root).casefold().encode("utf-8")).hexdigest()[
            :16
        ]
        cache_dir = ROOT / "local/mod-tools/cache" / installation_key
        for destination in (environment, settings_file, cache_dir):
            if destination.resolve().is_relative_to(game_root):
                raise ValueError(
                    "Extract the tools outside your original installation before running setup."
                )
        python = environment / "Scripts/python.exe"
        if not args.check:
            # Dependency installation belongs to our venv. Ignore personal pip
            # configuration and require exact wheel hashes from the reviewed list.
            venv.EnvBuilder(with_pip=True).create(environment)
            subprocess.run(
                [
                    str(python),
                    "-m",
                    "pip",
                    "--isolated",
                    "install",
                    "--index-url",
                    "https://pypi.org/simple",
                    "--only-binary=:all:",
                    "--require-hashes",
                    "-r",
                    str(Path(__file__).with_name("mod-tools-requirements.txt")),
                ],
                check=True,
            )
        if not python.is_file():
            raise ValueError(
                "The Mod Tools Python environment is missing. Run setup without --check first."
            )
        subprocess.run(
            [
                str(python),
                "-I",
                "-c",
                "import tkinter, PIL; from PIL import Image; "
                "assert PIL.__version__ == '12.3.0'; "
                "assert Image.new('RGB', (1, 1)).getpixel((0, 0)) == (0, 0, 0)",
            ],
            check=True,
        )
        if not args.check:
            write_settings(
                settings_file,
                {
                    "schema_version": 1,
                    "game_root": str(game_root),
                    "mech3ax_dir": str(tool_dir),
                    "cache_dir": str(cache_dir),
                },
            )
        print("Mod Tools dependencies verified. Desktop editor setup is ready.")
        print(
            "Studio preview geometry/cache generation and native map play need separate preparation."
        )
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Mod Tools setup failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
