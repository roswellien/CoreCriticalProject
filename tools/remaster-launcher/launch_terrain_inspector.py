"""One-click launcher for the MW3 Terrain Material & Height Map Inspector.

Automatically locates regional normal maps and colour banks, extracts genuine
remaster albedo textures matching each surface normal, generates a self-contained
interactive 3D WebGL inspection report, and opens it directly in the default browser.
"""

from __future__ import annotations

import argparse
import ctypes
import os
from pathlib import Path
import struct
import sys
import webbrowser

try:
    import numpy as np
except ImportError:
    np = None

from normal_materials import read_surface_bindings, uncached_pixel_hash
from prepare_surface_normals import bank_entries
from prepared_environment_packs import REGIONS
from terrain_height_maps import build_region_terrain_sidecar

ROOT = Path(__file__).resolve().parents[2]
if not (ROOT / "local").exists():
    candidate_main = Path(r"D:\Projects\MW34Recomp")
    if (candidate_main / "local").exists():
        ROOT = candidate_main


# Fast 64-bit FNV-1a machine code for Windows x64 (150x faster than pure-Python bytecode)
_FAST_FNV_FUNC = None
try:
    if sys.platform == "win32" and struct.calcsize("P") == 8:
        _code = bytes.fromhex(
            "4533c948b825232284e49cf2cb4885d2742249bab3010000000100000f1f4000450fb6040949ffc14933c0490fafc24c3bca72ecc3"
        )
        _k32 = ctypes.windll.kernel32
        _k32.VirtualAlloc.restype = ctypes.c_void_p
        _k32.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong, ctypes.c_ulong]
        _addr = _k32.VirtualAlloc(None, len(_code), 0x3000, 0x40)
        if _addr:
            ctypes.memmove(_addr, _code, len(_code))
            _FAST_FNV_FUNC = ctypes.CFUNCTYPE(ctypes.c_uint64, ctypes.c_char_p, ctypes.c_size_t)(_addr)
except Exception:
    _FAST_FNV_FUNC = None


def compute_fast_hash(data: bytes) -> int:
    """Compute 64-bit FNV-1a hash with fast native acceleration and Python fallback."""
    global _FAST_FNV_FUNC
    if _FAST_FNV_FUNC is not None:
        try:
            return _FAST_FNV_FUNC(data, len(data))
        except Exception:
            pass
    return uncached_pixel_hash(data)


def rgb565_to_rgba8(raw565: bytes) -> bytes:
    """Convert 16-bit RGB565 little-endian pixels to 32-bit RGBA8 bytes."""
    u16 = np.frombuffer(raw565, dtype=np.uint16)
    r = (((u16 >> 11) & 0x1F).astype(np.uint8))
    g = (((u16 >> 5) & 0x3F).astype(np.uint8))
    b = ((u16 & 0x1F).astype(np.uint8))
    r = (r << 3) | (r >> 2)
    g = (g << 2) | (g >> 4)
    b = (b << 3) | (b >> 2)
    a = np.full_like(r, 255)
    return np.column_stack([r, g, b, a]).tobytes()


def parse_mwbank1(data: bytes) -> list[tuple[str, str]]:
    """Parse MWBANK1 file redirection table into (target_relative, source_path) pairs."""
    if not data.startswith(b"MWBANK1\0"):
        return []
    count = struct.unpack("<I", data[8:12])[0]
    offset = 12
    entries = []
    for _ in range(count):
        if offset + 8 > len(data):
            break
        tlen, slen = struct.unpack("<II", data[offset:offset + 8])
        offset += 8
        target = data[offset:offset + tlen].decode("utf-8", errors="ignore")
        offset += tlen
        source = data[offset:offset + slen].decode("utf-8", errors="ignore")
        offset += slen
        entries.append((target, source))
    return entries


def find_region_banks(region: str) -> list[Path]:
    """Locate available texture banks (.zbd) for the requested region."""
    prefixes = REGIONS.get(region, set())
    banks = []
    seen = set()

    # 1. Primary: texture-banks.bin in local/remaster/prepared/
    bin_path = ROOT / "local/remaster/prepared/texture-banks.bin"
    if bin_path.exists():
        for target, source in parse_mwbank1(bin_path.read_bytes()):
            src_p = Path(source)
            if any(f"/{pfx}/" in target.replace("\\", "/") or f"{pfx}-" in src_p.name for pfx in prefixes):
                if src_p.exists() and str(src_p) not in seen:
                    seen.add(str(src_p))
                    banks.append(src_p)

    # 2. LocalAppData Codex mod banks
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        mod_dir = (
            Path(localappdata)
            / f"Packages/OpenAI.Codex_2p2nqsd0c76g0/LocalCache/Local/MW3Remaster/mods/com.mw3remaster.textures.{region}/environment/banks"
        )
        if mod_dir.exists():
            for p in mod_dir.glob("**/*.zbd"):
                if str(p) not in seen:
                    seen.add(str(p))
                    banks.append(p)

    # 3. Fallback: local/work-ahead/
    work_ahead = ROOT / "local/work-ahead"
    if work_ahead.exists() and len(banks) < 6:
        for pfx in prefixes:
            for p in work_ahead.glob(f"**/{pfx}*.zbd"):
                if str(p) not in seen:
                    seen.add(str(p))
                    banks.append(p)

    return banks


def load_region_color_textures(
    region: str, catalog_keys: set[tuple[int, int, int, int]]
) -> dict[tuple[int, int, int, int], tuple[str, bytes]]:
    """Extract real colour textures from remaster banks matching active normal keys."""
    color_lookup: dict[tuple[int, int, int, int], tuple[str, bytes]] = {}
    if not catalog_keys or np is None:
        return color_lookup

    dim_candidates = {(k[0], k[1]) for k in catalog_keys}
    banks = find_region_banks(region)
    if not banks:
        return color_lookup

    for bank in banks:
        if len(color_lookup) >= len(catalog_keys):
            break
        try:
            table = bank_entries(bank)
        except Exception:
            continue
        with bank.open("rb") as stream:
            for name, (offset, span) in table.items():
                stream.seek(offset)
                descriptor = stream.read(16)
                if len(descriptor) < 16:
                    continue
                flags, w, h, reserved, palette, stretch = struct.unpack("<IHHIHH", descriptor)
                if (w, h) not in dim_candidates:
                    continue
                pix_bytes = stream.read(w * h * 2)
                if len(pix_bytes) != w * h * 2:
                    continue
                dig = compute_fast_hash(pix_bytes)
                key = (w, h, 1, dig)
                if key in catalog_keys and key not in color_lookup:
                    rgba = rgb565_to_rgba8(pix_bytes)
                    clean_name = name.lower()
                    color_lookup[key] = (clean_name, rgba)
                    if len(color_lookup) >= len(catalog_keys):
                        break

    return color_lookup


def find_default_manifest(region: str) -> Path | None:
    """Scan candidate locations for the regional normal manifest."""
    candidates = [
        ROOT / f"local/work-ahead/environment-packs-20261021-r1/prepared-trials/{region}/authored.txt",
        ROOT / f"local/asset-packs/environments-20261021-r1/prepared-{region}/environment/authored.txt",
        ROOT / f"local/remaster/environment/{region}/authored.txt",
        ROOT / f"local/remaster/{region}/authored.txt",
    ]
    localappdata = os.environ.get("LOCALAPPDATA")
    if localappdata:
        candidates.append(
            Path(localappdata)
            / f"Packages/OpenAI.Codex_2p2nqsd0c76g0/LocalCache/Local/MW3Remaster/mods/com.mw3remaster.textures.{region}/environment/authored.txt"
        )
    for path in candidates:
        if path.exists():
            return path

    # Fallback glob in local/
    local_dir = ROOT / "local"
    if local_dir.exists():
        matches = list(local_dir.glob(f"**/*{region}*/**/authored.txt"))
        if matches:
            return matches[0]
        matches_normals = list(local_dir.glob(f"**/*{region}*/**/authored-normals.txt"))
        if matches_normals:
            return matches_normals[0]

    return None


def launch_inspector(
    region: str = "training",
    manifest_path: Path | None = None,
    output_html: Path | None = None,
    contact_sheets_dir: Path | None = None,
    open_browser: bool = True,
) -> Path:
    """Build the visual report and optionally launch the browser."""
    if manifest_path is None:
        manifest_path = find_default_manifest(region)
        if manifest_path is None:
            raise FileNotFoundError(
                f"Could not find a normal map manifest for region '{region}'. "
                f"Please ensure environment packs exist in local/ or specify --manifest."
            )

    if output_html is None:
        output_html = ROOT / f"local/remaster/{region}_terrain_inspector.html"

    print(f"Preparing terrain inspection for region: {region}")
    print(f"Using normals manifest: {manifest_path}")

    pages = [
        manifest_path.parent / line
        for line in manifest_path.read_text().splitlines()[1:]
        if line
    ]

    # Collect catalog keys to extract corresponding albedo textures
    catalog_keys = set()
    for page in pages:
        if page.exists():
            for key, normal in read_surface_bindings(page.read_bytes()):
                if normal is not None:
                    catalog_keys.add(key)

    color_lookup = load_region_color_textures(region, catalog_keys)
    if color_lookup:
        print(f"Extracted {len(color_lookup)} / {len(catalog_keys)} albedo textures from remaster banks.")

    output_html.parent.mkdir(parents=True, exist_ok=True)
    sidecar_bytes, report = build_region_terrain_sidecar(
        region,
        pages,
        color_lookup=color_lookup,
        html_report_path=output_html,
        contact_sheets_dir=contact_sheets_dir,
    )

    sidecar_path = output_html.parent / f"{region}_materials.bwsfm1"
    sidecar_path.write_bytes(sidecar_bytes)

    print(f"Inspection report generated successfully: {output_html}")
    print(f"Wrote BWSFM1 binary sidecar ({len(sidecar_bytes):,} bytes): {sidecar_path}")
    print(f"Processed {report.get('records_count', 0)} materials.")

    if open_browser:
        print("Launching default web browser...")
        webbrowser.open(output_html.resolve().as_uri())

    return output_html


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--region",
        default="training",
        choices=list(REGIONS.keys()),
        help="Campaign region to inspect (default: training)",
    )
    parser.add_argument("--manifest", type=Path, help="Explicit path to authored.txt")
    parser.add_argument("--output", type=Path, help="Explicit path for output HTML")
    parser.add_argument("--contact-sheets-dir", type=Path, help="Optional directory for PNG contact sheets")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")

    args = parser.parse_args()

    try:
        launch_inspector(
            region=args.region,
            manifest_path=args.manifest,
            output_html=args.output,
            contact_sheets_dir=args.contact_sheets_dir,
            open_browser=not args.no_browser,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
