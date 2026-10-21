"""MW3 format abstraction layer.

Wraps Mech3AX for byte-exact ZBD container conversions, providing
clean Python data structures for reader documents and GameZ scenes.
"""

import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[5]
DEFAULT_MECH3AX_DIR = ROOT / "local/tools/mech3ax-v0.7.0-rc3-windows/mech3ax-v0.7.0-rc3-x86_64-pc-windows-msvc"
UNZBD_EXE = DEFAULT_MECH3AX_DIR / "unzbd.exe"
REZBD_EXE = DEFAULT_MECH3AX_DIR / "rezbd.exe"


def verify_tools_available() -> bool:
    """Check that Mech3AX extraction and reconstruction tools are available."""
    return UNZBD_EXE.is_file() and REZBD_EXE.is_file()


def unpack_reader_zbd(zbd_path: Path, output_dir: Path) -> Path:
    """Extract a reader*.zbd archive into a directory of JSON documents.

    Returns the path to manifest.json or directory.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_zip = output_dir / "_temp_reader.zip"
    try:
        cmd = [str(UNZBD_EXE), "mw", "reader", str(zbd_path), str(temp_zip)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"unzbd reader failed for {zbd_path}: {res.stderr.strip()}")
        with zipfile.ZipFile(temp_zip, "r") as z:
            z.extractall(output_dir)
    finally:
        if temp_zip.exists():
            temp_zip.unlink()
    return output_dir


def pack_reader_zbd(source_dir: Path, output_zbd: Path) -> Path:
    """Reconstruct a reader*.zbd archive from a directory of JSON documents.

    Produces a byte-exact binary archive matching original structure.
    """
    output_zbd.parent.mkdir(parents=True, exist_ok=True)
    temp_zip = source_dir / "_temp_pack_reader.zip"
    try:
        with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(source_dir):
                for f in files:
                    if f.startswith("_temp_"):
                        continue
                    file_path = Path(root) / f
                    arcname = file_path.relative_to(source_dir).as_posix()
                    z.write(file_path, arcname)
        cmd = [str(REZBD_EXE), "mw", "reader", str(temp_zip), str(output_zbd)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"rezbd reader failed for {output_zbd}: {res.stderr.strip()}")
    finally:
        if temp_zip.exists():
            temp_zip.unlink()
    return output_zbd


def unpack_gamez_zbd(zbd_path: Path, output_dir: Path) -> Path:
    """Extract a gamez.zbd archive into JSON files (nodes, models, materials, textures)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_zip = output_dir / "_temp_gamez.zip"
    try:
        cmd = [str(UNZBD_EXE), "mw", "gamez", str(zbd_path), str(temp_zip)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"unzbd gamez failed for {zbd_path}: {res.stderr.strip()}")
        with zipfile.ZipFile(temp_zip, "r") as z:
            z.extractall(output_dir)
    finally:
        if temp_zip.exists():
            temp_zip.unlink()
    return output_dir


def pack_gamez_zbd(source_dir: Path, output_zbd: Path) -> Path:
    """Reconstruct a gamez.zbd archive from JSON files byte-for-byte."""
    output_zbd.parent.mkdir(parents=True, exist_ok=True)
    temp_zip = source_dir / "_temp_pack_gamez.zip"
    try:
        with zipfile.ZipFile(temp_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(source_dir):
                for f in files:
                    if f.startswith("_temp_"):
                        continue
                    file_path = Path(root) / f
                    arcname = file_path.relative_to(source_dir).as_posix()
                    z.write(file_path, arcname)
        cmd = [str(REZBD_EXE), "mw", "gamez", str(temp_zip), str(output_zbd)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"rezbd gamez failed for {output_zbd}: {res.stderr.strip()}")
    finally:
        if temp_zip.exists():
            temp_zip.unlink()
    return output_zbd


def extract_single_texture(rimage_zbd: Path, texture_name: str, output_png: Path) -> bool:
    """Extract a specific PNG image (e.g. map bitmap) from rimage.zbd without extracting all files."""
    output_png.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        temp_zip = Path(td) / "rimage.zip"
        cmd = [str(UNZBD_EXE), "mw", "textures", str(rimage_zbd), str(temp_zip)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0 or not temp_zip.is_file():
            return False
        with zipfile.ZipFile(temp_zip, "r") as z:
            # Case-insensitive search
            candidates = [n for n in z.namelist() if n.lower() == texture_name.lower() or n.lower() == f"{texture_name.lower()}.png"]
            if not candidates:
                return False
            data = z.read(candidates[0])
            output_png.write_bytes(data)
            return True
