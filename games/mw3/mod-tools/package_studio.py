#!/usr/bin/env python3
"""Build and package MechWarrior 3 Mod Studio for distribution to other PCs.

Creates a self-contained portable distribution folder and ZIP archive
ready to be unzipped and run on any Windows PC.

Usage:
    python package_studio.py [--mode standalone|lightweight] [--version 1.0.0]
"""

import argparse
import os
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = TOOLS_ROOT.parents[2]

sys.path.insert(0, str(TOOLS_ROOT))
from editor.config import tool_directory

# Python 3.11 official embeddable release for Windows x64
PYTHON_EMBED_URL = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip"


def clean_copytree(src: Path, dst: Path, ignore_patterns=None):
    """Copy directory tree excluding pycache and developer artifacts."""
    if ignore_patterns is None:
        ignore_patterns = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".git*")
    shutil.copytree(src, dst, ignore=ignore_patterns, dirs_exist_ok=True)


def download_python_embed(target_dir: Path) -> bool:
    """Download and extract official Windows 64-bit embeddable Python runtime."""
    target_dir.mkdir(parents=True, exist_ok=True)
    cache_zip = PROJECT_ROOT / "local/tools/python-3.11.9-embed-amd64.zip"
    cache_zip.parent.mkdir(parents=True, exist_ok=True)

    if not cache_zip.is_file():
        print(f"[Packaging] Downloading Python embeddable runtime from:\n  {PYTHON_EMBED_URL}")
        try:
            req = urllib.request.Request(PYTHON_EMBED_URL, headers={"User-Agent": "MW3-Mod-Tools-Packager/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(cache_zip, "wb") as f:
                shutil.copyfileobj(resp, f)
            print(f"[Packaging] Downloaded {cache_zip.stat().st_size:,} bytes")
        except Exception as e:
            print(f"[Packaging] Warning: Could not download embedded Python ({e}). Falling back to system Python mode.")
            return False

    print("[Packaging] Extracting embedded Python runtime...")
    with zipfile.ZipFile(cache_zip, "r") as z:
        z.extractall(target_dir)

    # Enable import site and root import in python311._pth
    pth_file = target_dir / "python311._pth"
    if pth_file.is_file():
        content = pth_file.read_text(encoding="utf-8")
        lines = content.splitlines()
        updated_lines = []
        for line in lines:
            if line.strip() == "#import site":
                updated_lines.append("import site")
            else:
                updated_lines.append(line)
        if ".." not in updated_lines:
            updated_lines.append("..")
        if "." not in updated_lines:
            updated_lines.append(".")
        pth_file.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")

    return True


def create_launcher_cmd(dest_file: Path):
    """Generate the 1-click Windows launcher batch script."""
    cmd_content = """@echo off
title MechWarrior 3 Mod Studio
cd /d "%~dp0"

echo ====================================================================
echo   MECHWARRIOR 3 - VISUAL 3D MOD STUDIO
echo ====================================================================

:: 1. Check for bundled embedded Python runtime
if exist "python\\python.exe" (
    echo [Mod Studio] Starting with bundled portable Python runtime...
    start "" "python\\python.exe" run_studio.py
    exit /b 0
)

:: 2. Check for system Python launcher (py -3)
where py >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [Mod Studio] Starting with system Python launcher (py -3)...
    start "" py -3 run_studio.py
    exit /b 0
)

:: 3. Check for python on PATH
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [Mod Studio] Starting with system Python...
    start "" python run_studio.py
    exit /b 0
)

echo.
echo ====================================================================
echo ERROR: Python 3 was not detected on this computer.
echo.
echo To run MechWarrior 3 Mod Studio:
echo   1. Install Python 3.9+ from https://www.python.org/downloads/
echo   2. Ensure "Add Python to PATH" is checked during installation.
echo   3. Run this script again.
echo ====================================================================
echo.
pause
exit /b 1
"""
    dest_file.write_text(cmd_content, encoding="utf-8")


def create_readme(dest_file: Path, version: str, mode: str):
    """Generate the user-facing README documentation."""
    readme_content = f"""====================================================================
  MECHWARRIOR 3 - VISUAL 3D MOD STUDIO v{version} ({mode.title()})
====================================================================

QUICK START:
1. Double-click "Launch-Mod-Studio.cmd".
2. Your default web browser will automatically open to:
   http://127.0.0.1:8080/
3. On first launch, if prompted, select or enter the path to your
   MechWarrior 3 game folder (e.g. C:\\Games\\MechWarrior 3).
4. Create, sculpt, customize, and export custom map packs and campaigns!

FEATURES INCLUDED:
- 2D Top-Down Tactical Orthographic Map & 3D Perspective Studio
- Real-Time Brush Terrain Sculpting & Mesh Baking (gamez.zbd)
- 24-Hour Atmosphere, Lighting & Dynamic Weather Studio (MW34ENV1)
- MechLab In-Game Drop Loadout & Hardpoint Compiler (reader.zbd)
- Multi-Mission Branching Campaign Builder & Standalone Launcher
- Built-in Mech3AX binary packers (unzbd.exe, rezbd.exe)

DISTRIBUTING YOUR MODS:
- Click "Export for Distribution" in the Studio to generate a .zip
  package that other players can extract into their MW3 folder and play
  instantly with 1 click.

SYSTEM REQUIREMENTS:
- Windows 10 / Windows 11 (64-bit)
- Modern WebGL browser (Chrome, Edge, Firefox, Brave)
- MechWarrior 3 game installation (or MW3 Recomp)
====================================================================
"""
    dest_file.write_text(readme_content, encoding="utf-8")


def package_studio(mode: str = "standalone", version: str = "1.0.0", output_dir: Path = None) -> Path:
    """Build the portable distribution package."""
    if output_dir is None:
        output_dir = PROJECT_ROOT / "dist"
    output_dir.mkdir(parents=True, exist_ok=True)

    folder_name = f"MW3-Mod-Studio-v{version}-{mode.title()}"
    staging_dir = output_dir / folder_name
    if staging_dir.is_dir():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n[Packaging] Building {folder_name}...")

    # 1. Copy run_studio.py
    shutil.copy2(TOOLS_ROOT / "run_studio.py", staging_dir / "run_studio.py")

    # 2. Copy editor/ package (core, ui, web, config.py)
    clean_copytree(TOOLS_ROOT / "editor", staging_dir / "editor")

    # 3. Copy binaries (unzbd.exe, rezbd.exe)
    bin_dir = staging_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    tool_src = tool_directory()
    if (tool_src / "unzbd.exe").is_file():
        shutil.copy2(tool_src / "unzbd.exe", bin_dir / "unzbd.exe")
        shutil.copy2(tool_src / "rezbd.exe", bin_dir / "rezbd.exe")
        print(f"[Packaging] Copied unzbd.exe and rezbd.exe from {tool_src} into bin/")
    else:
        print("[Packaging] Warning: unzbd.exe / rezbd.exe not found; check path.")

    # 4. Generate Launcher script and README
    create_launcher_cmd(staging_dir / "Launch-Mod-Studio.cmd")
    create_readme(staging_dir / "README.txt", version, mode)
    print("[Packaging] Generated Launch-Mod-Studio.cmd and README.txt")

    # 5. Standalone mode: bundle embedded Python runtime
    actual_mode = mode
    if mode == "standalone":
        success = download_python_embed(staging_dir / "python")
        if not success:
            actual_mode = "lightweight"

    # 6. Create ZIP archive
    zip_stem = output_dir / f"MW3-Mod-Studio-v{version}-{actual_mode.title()}"
    print(f"[Packaging] Compressing {folder_name} into ZIP archive...")
    zip_path = Path(shutil.make_archive(str(zip_stem), "zip", root_dir=str(output_dir), base_dir=folder_name))
    print(f"[Packaging] SUCCESS! Distribution package created at:\n  {zip_path} ({zip_path.stat().st_size:,} bytes)")

    return zip_path


def main():
    parser = argparse.ArgumentParser(description="Package MechWarrior 3 Mod Studio for distribution.")
    parser.add_argument(
        "--mode",
        choices=["standalone", "lightweight"],
        default="standalone",
        help="standalone (bundles embedded Python) or lightweight (requires system Python)",
    )
    parser.add_argument("--version", default="1.0.0", help="Release version string")
    parser.add_argument("--output-dir", default=None, help="Destination directory for distribution archives")
    args = parser.parse_args()

    out_p = Path(args.output_dir) if args.output_dir else None
    package_studio(mode=args.mode, version=args.version, output_dir=out_p)


if __name__ == "__main__":
    main()
