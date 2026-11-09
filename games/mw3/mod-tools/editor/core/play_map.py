#!/usr/bin/env python3
"""Run a compiled MechWarrior 3 map pack with automatic backup and restoration.

Safely installs map pack ZBD files into the configured MW3 game directory,
launches Mech3.exe, and restores original files upon game exit.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent
TOOLS_ROOT = CORE_DIR.parents[1]
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

try:
    from editor.config import game_directory, is_game_installed
except ImportError:
    def is_game_installed():
        return False
    def game_directory():
        return None


def run_map(pack_dir: Path) -> int:
    manifest_path = pack_dir / "manifest.json"
    if not manifest_path.is_file():
        print(f"Error: manifest.json not found in {pack_dir}")
        return 1

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"Error reading manifest: {e}")
        return 1

    pack_title = manifest.get("title", pack_dir.name)
    pack_id = manifest.get("pack_id", pack_dir.name)
    base_op = manifest.get("base_operation", "c1")
    if base_op == "flat":
        base_op = "t1"

    print("=" * 70)
    print(f"  LAUNCHING CUSTOM MAP: {pack_title} [{pack_id}]")
    print(f"  Base Operation: {base_op.upper()}")
    print("=" * 70)

    # 1. Locate game directory
    game_root = None
    if is_game_installed():
        game_root = game_directory()

    # Search common fallbacks if unset
    if not game_root or not game_root.is_dir():
        candidates = [
            TOOLS_ROOT.parents[2] / "MW3",
            TOOLS_ROOT.parents[2] / "local/work-ahead/mw3-d7vk-wrapper/game",
            Path("C:/Games/MechWarrior 3"),
            Path("C:/Games/MW3"),
            Path("D:/Games/MechWarrior 3"),
            Path("D:/Games/MW3"),
            Path("C:/Program Files (x86)/MicroProse/MechWarrior 3"),
        ]
        for c in candidates:
            if (c / "Mech3.exe").is_file():
                game_root = c.resolve()
                break

    if not game_root or not (game_root / "Mech3.exe").is_file():
        print("\nERROR: Could not locate Mech3.exe!")
        print("Please set your MechWarrior 3 directory in the Mod Studio settings,")
        print("or verify that MechWarrior 3 is installed.\n")
        input("Press Enter to close...")
        return 1

    game_exe = game_root / "Mech3.exe"
    print(f"[Mod Runner] Game folder: {game_root}")
    print(f"[Mod Runner] Game executable: {game_exe}")

    # 2. Check for mod files to install
    mod_op_zbd = pack_dir / f"zbd/{base_op}"
    mod_global_reader = pack_dir / "zbd/reader.zbd"

    game_op_zbd = game_root / f"zbd/{base_op}"
    game_op_zbd.mkdir(parents=True, exist_ok=True)

    backups = {}
    installed_files = []

    try:
        # Install gamez.zbd
        mod_gamez = mod_op_zbd / "gamez.zbd"
        if mod_gamez.is_file():
            target_gamez = game_op_zbd / "gamez.zbd"
            backup_gamez = game_op_zbd / "gamez.zbd.mw3orig"
            if target_gamez.is_file() and not backup_gamez.is_file():
                print(f"[Mod Runner] Backing up original {target_gamez.name} -> {backup_gamez.name}")
                shutil.copy2(target_gamez, backup_gamez)
                backups[backup_gamez] = target_gamez
            shutil.copy2(mod_gamez, target_gamez)
            installed_files.append(target_gamez)
            print(f"[Mod Runner] Installed custom {mod_gamez.name} ({mod_gamez.stat().st_size:,} bytes)")

        # Install reader.zbd for operation
        mod_reader = mod_op_zbd / "reader.zbd"
        if mod_reader.is_file():
            target_reader = game_op_zbd / "reader.zbd"
            backup_reader = game_op_zbd / "reader.zbd.mw3orig"
            if target_reader.is_file() and not backup_reader.is_file():
                print(f"[Mod Runner] Backing up original {target_reader.name} -> {backup_reader.name}")
                shutil.copy2(target_reader, backup_reader)
                backups[backup_reader] = target_reader
            shutil.copy2(mod_reader, target_reader)
            installed_files.append(target_reader)
            print(f"[Mod Runner] Installed custom {mod_reader.name} ({mod_reader.stat().st_size:,} bytes)")

        # Install global reader.zbd if present
        if mod_global_reader.is_file():
            target_global = game_root / "zbd/reader.zbd"
            backup_global = game_root / "zbd/reader.zbd.mw3orig"
            if target_global.is_file() and not backup_global.is_file():
                print(f"[Mod Runner] Backing up original global reader.zbd -> {backup_global.name}")
                shutil.copy2(target_global, backup_global)
                backups[backup_global] = target_global
            shutil.copy2(mod_global_reader, target_global)
            installed_files.append(target_global)
            print(f"[Mod Runner] Installed custom global reader.zbd ({mod_global_reader.stat().st_size:,} bytes)")

        print("\n" + "=" * 70)
        print("  STARTING MECHWARRIOR 3 WITH CUSTOM MISSION...")
        print(f"  To play your map: Select '{base_op.upper()}' in Instant Action or Campaign Mission 1.")
        print("=" * 70 + "\n")

        # Launch the game process
        proc = subprocess.run([str(game_exe)], cwd=str(game_root))
        return proc.returncode

    except Exception as e:
        print(f"\n[Mod Runner] Launch error: {e}")
        return 1

    finally:
        # Restore backups cleanly
        print("\n[Mod Runner] Game session finished. Restoring original game archives...")
        for backup_file, orig_file in backups.items():
            try:
                if backup_file.is_file():
                    shutil.move(backup_file, orig_file)
                    print(f"[Mod Runner] Restored {orig_file.name}")
            except Exception as e:
                print(f"[Mod Runner] Warning restoring {orig_file}: {e}")
        print("[Mod Runner] Restoration complete. Game directory is clean.\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python play_map.py <path_to_map_pack_folder>")
        sys.exit(1)

    pack_dir = Path(sys.argv[1]).resolve()
    rc = run_map(pack_dir)
    sys.exit(rc)


if __name__ == "__main__":
    main()
