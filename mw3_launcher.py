"""MW3 D7VK (Vulkan) launcher for the isolated private profile.

Features:
  * Resolution:
      - 4:3 High-Res Equivalents: 1024x768 (Native), 1440x1080 (1080p eq),
        1920x1440 (1440p eq), 2880x2160 (4K eq) - presented cleanly pillarboxed.
      - Widescreen (16:9 / 21:9): 1920x1080, 2560x1440, 3440x1440, 3840x2160 -
        rendered widescreen with verified in-engine 3D camera FOV correction
        to prevent image stretching.
      - Safe Retail InGameVMode: retail engine is clamped to mode 7 (or 5/6)
        to prevent surface-loss crash at 0x00577648 when entering 3D.
  * Anti-aliasing: D7VK ddraw.emulateFSAA=forced + ddraw.fsaaSamples (MSAA 2x, 4x, 8x).
  * Anisotropic filtering: DXVK d3d9.samplerAnisotropy (2x, 4x, 8x, 16x).
  * AI textures: verified cumulative AI .zbd banks via fast NTFS hard-links
    with automatic TextureMemory_HW = 6 configuration.
  * Isolation: Original MW3 folder is untouched; registry settings restored on exit.
"""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes as w
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import winreg

ROOT = Path(r"D:\Projects\MW34Recomp")
WORK = ROOT / "local/work-ahead"
WRAPPER = WORK / "mw3-d7vk-wrapper"
GAME = WRAPPER / "game"
GAME_EXE = GAME / "Mech3.exe"
ORIGINAL_INSTALL = ROOT / "MW3"
ORIGINAL_BANK_CACHE = WRAPPER / "original-banks"
AI_MANIFEST = WORK / "texture-launcher-audit-v2/configured-banks.json"
AI_MANIFEST_INSTALL = WORK / "training-terrain-game-test/install"
SETTINGS_FILE = WRAPPER / "launcher-settings.json"
HASH_CACHE_FILE = WRAPPER / "launcher-hash-cache.json"
RUNS = WRAPPER / "runs/launcher"

EXE_SHA256 = "95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf"
DDRAW_SHA256 = os.environ.get("MW34_D7VK_DDRAW_SHA256", "")
DDRAW_SHA256_FILE = WRAPPER / "launcher-ddraw.sha256"

# Widescreen camera FOV fix components
FOV_ASI_SOURCE = ROOT / "local/tools/mw3-fov-v1.6/MechWarrior3FOVFix.asi"
FOV_ASI_EXPECTED_HASH = "57afb226033790cafa36f6409ee036c03dc38e42b6cc1fe8d62880b03be2205d"
FOV_LAUNCHER_EXE = ROOT / "build/widescreen-test/Release/mw34_fov_launcher.exe"
FOV_BOOTSTRAP_DLL = ROOT / "build/widescreen-test/Release/mw34_fov_bootstrap.dll"

REG_PATH = r"Software\MicroProse\MechWarrior 3\1.0"
AI_TEXTURE_MEMORY_MODE = 6  # bank 2; avoids rainbow artifacts with high-res banks

RESOLUTION_PROFILES = {
    # 4:3 Aspect Ratio (Pillarboxed on modern widescreen displays; unstretched native geometry)
    "1024x768 (Native 4:3)": {
        "width": 1024, "height": 768, "aspect": "4:3", "widescreen": False, "vmode": 7,
        "note": "Native retail 4:3 presentation (pillarboxed on widescreen displays)",
    },
    "1440x1080 (1080p 4:3 Equivalent)": {
        "width": 1440, "height": 1080, "aspect": "4:3", "widescreen": False, "vmode": 7,
        "note": "1080p height in 4:3 proportions (pillarboxed on 16:9 displays)",
    },
    "1920x1440 (1440p 4:3 Equivalent)": {
        "width": 1920, "height": 1440, "aspect": "4:3", "widescreen": False, "vmode": 7,
        "note": "1440p height in 4:3 proportions (pillarboxed on 16:9 displays)",
    },
    "2880x2160 (4K 4:3 Equivalent)": {
        "width": 2880, "height": 2160, "aspect": "4:3", "widescreen": False, "vmode": 7,
        "note": "4K/2160p height in 4:3 proportions (pillarboxed on 16:9 displays)",
    },
    # Widescreen (16:9 / 21:9 - Unstretched 3D via verified camera FOV injection)
    "1920x1080 (1080p Widescreen 16:9)": {
        "width": 1920, "height": 1080, "aspect": "16:9", "widescreen": True, "vmode": 7,
        "note": "Full HD 1080p widescreen with corrected 3D camera FOV (unstretched)",
    },
    "2560x1440 (1440p Widescreen 16:9)": {
        "width": 2560, "height": 1440, "aspect": "16:9", "widescreen": True, "vmode": 7,
        "note": "QHD 1440p widescreen with corrected 3D camera FOV (unstretched)",
    },
    "3440x1440 (Ultrawide 21:9)": {
        "width": 3440, "height": 1440, "aspect": "21:9", "widescreen": True, "vmode": 7,
        "note": "Ultrawide 21:9 with corrected 3D camera FOV (unstretched)",
    },
    "3840x2160 (4K Widescreen 16:9)": {
        "width": 3840, "height": 2160, "aspect": "16:9", "widescreen": True, "vmode": 7,
        "note": "4K UHD 2160p widescreen with corrected 3D camera FOV (unstretched)",
    },
    # Legacy modes
    "800x600 (Legacy 4:3)": {
        "width": 800, "height": 600, "aspect": "4:3", "widescreen": False, "vmode": 6,
        "note": "Legacy 800x600 mode",
    },
    "640x480 (Legacy 4:3)": {
        "width": 640, "height": 480, "aspect": "4:3", "widescreen": False, "vmode": 5,
        "note": "Original default 640x480 mode",
    },
}

AA_LEVELS = {"Off": 0, "2x MSAA": 2, "4x MSAA": 4, "8x MSAA": 8}
AF_LEVELS = {"Game default": -1, "2x": 2, "4x": 4, "8x": 8, "16x": 16}

DEFAULTS = {
    "resolution": "1024x768 (Native 4:3)",
    "aa": "Off",
    "af": "Game default",
    "ai_textures": False,
}

FIXED_CONF = [
    "d3d9.maxFrameRate = 30",
    "ddraw.forceLegacyPresent = True",
    "ddraw.emulateFrontBuffer = True",
]


class LauncherError(RuntimeError):
    pass


# ---------------------------------------------------------------- hashing

def _load_cache() -> dict:
    try:
        return json.loads(HASH_CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


_cache = None


def sha256(path: Path) -> str:
    global _cache
    if _cache is None:
        _cache = _load_cache()
    st = path.stat()
    key = str(path.resolve()).lower()
    rec = _cache.get(key)
    if rec and rec["size"] == st.st_size and rec["mtime_ns"] == st.st_mtime_ns:
        return rec["sha256"]
    with path.open("rb") as f:
        digest = hashlib.file_digest(f, "sha256").hexdigest()
    _cache[key] = {"size": st.st_size, "mtime_ns": st.st_mtime_ns, "sha256": digest}
    return digest


def save_cache() -> None:
    if _cache is not None:
        HASH_CACHE_FILE.write_text(json.dumps(_cache, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- processes

def running_mech3() -> list[str]:
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='Mech3.exe'\" | ForEach-Object { $_.ExecutablePath }"],
        capture_output=True, text=True, check=False).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


# ---------------------------------------------------------------- textures

def load_ai_banks() -> list[dict]:
    try:
        rows = json.loads(AI_MANIFEST.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise LauncherError(f"AI texture manifest unreadable (it may be mid-update): {exc}")
    banks = []
    for row in rows:
        target = Path(row["target"])
        try:
            rel = target.relative_to(AI_MANIFEST_INSTALL)
        except ValueError:
            raise LauncherError(f"Unexpected AI bank target outside texture install: {target}")
        banks.append({"rel": rel, "source": Path(row["source"]), "sha256": row["expected_sha256"].lower()})
    if not banks:
        raise LauncherError("AI texture manifest is empty")
    return banks


def ensure_original_cache(rel: Path, log) -> Path:
    """Verified private copy of the user's original bank (never links into MW3/)."""
    src = ORIGINAL_INSTALL / rel
    if not src.is_file():
        raise LauncherError(f"Original bank missing from MW3 installation: {src}")
    cached = ORIGINAL_BANK_CACHE / rel
    want = sha256(src)
    if not cached.is_file() or sha256(cached) != want:
        cached.parent.mkdir(parents=True, exist_ok=True)
        log(f"Caching original {rel}")
        tmp = cached.with_suffix(cached.suffix + ".tmp")
        shutil.copyfile(src, tmp)
        if sha256(tmp) != want:
            tmp.unlink()
            raise LauncherError(f"Copy verification failed for original {rel}")
        os.replace(tmp, cached)
    return cached


def place(source: Path, dest: Path, want: str) -> bool:
    """Hard-link source at dest unless dest already has the wanted content."""
    if dest.is_file() and sha256(dest) == want:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".lnk-tmp")
    if tmp.exists():
        tmp.unlink()
    os.link(source, tmp)
    os.replace(tmp, dest)  # replaces only the profile's directory entry
    if sha256(dest) != want:
        raise LauncherError(f"Post-placement verification failed: {dest}")
    return True


def apply_textures(ai: bool, log) -> dict:
    banks = load_ai_banks()
    changed = 0
    for bank in banks:
        dest = GAME / bank["rel"]
        if ai:
            if not bank["source"].is_file():
                raise LauncherError(f"AI bank source missing: {bank['source']}")
            if sha256(bank["source"]) != bank["sha256"]:
                raise LauncherError(f"AI bank source hash mismatch (manifest may be updating): {bank['source']}")
            source, want = bank["source"], bank["sha256"]
        else:
            source = ensure_original_cache(bank["rel"], log)
            want = sha256(source)
        if place(source, dest, want):
            changed += 1
    save_cache()
    log(f"Textures: {'AI' if ai else 'original'} ({len(banks)} banks verified, {changed} switched)")
    return {"mode": "ai" if ai else "original", "banks": len(banks), "switched": changed}


# ---------------------------------------------------------------- config / registry

def write_dxvk_conf(aa: int, af: int) -> list[str]:
    lines = ["# Generated by mw3_launcher.py (isolated MW3 D7VK profile)"] + FIXED_CONF
    if aa:
        lines += ["ddraw.emulateFSAA = forced", f"ddraw.fsaaSamples = {aa}"]
    else:
        lines += ["ddraw.emulateFSAA = False"]
    lines.append(f"d3d9.samplerAnisotropy = {af}")
    (GAME / "dxvk.conf").write_text("\n".join(lines) + "\n", encoding="ascii")
    return lines


def read_reg(names: list[str]) -> dict:
    out = {}
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH) as key:
        for n in names:
            try:
                value, kind = winreg.QueryValueEx(key, n)
                out[n] = {"value": value, "type": kind}
            except FileNotFoundError:
                out[n] = None
    return out


def write_reg(values: dict) -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
        for n, rec in values.items():
            if rec is None:
                try:
                    winreg.DeleteValue(key, n)
                except FileNotFoundError:
                    pass
            else:
                winreg.SetValueEx(key, n, 0, rec["type"], rec["value"])


# ---------------------------------------------------------------- launch

class STARTUPINFOW(ctypes.Structure):
    _fields_ = [("cb", w.DWORD), ("lpReserved", w.LPWSTR), ("lpDesktop", w.LPWSTR), ("lpTitle", w.LPWSTR),
                ("dwX", w.DWORD), ("dwY", w.DWORD), ("dwXSize", w.DWORD), ("dwYSize", w.DWORD),
                ("dwXCountChars", w.DWORD), ("dwYCountChars", w.DWORD), ("dwFillAttribute", w.DWORD),
                ("dwFlags", w.DWORD), ("wShowWindow", w.WORD), ("cbReserved2", w.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", w.HANDLE), ("hStdOutput", w.HANDLE),
                ("hStdError", w.HANDLE)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", w.HANDLE), ("hThread", w.HANDLE), ("dwProcessId", w.DWORD), ("dwThreadId", w.DWORD)]


def cleanup_fov_staging() -> None:
    for name in ("MechWarrior3FOVFix.asi", "MechWarrior3FOVFix.ini", "MechWarrior3FOVFix.log"):
        (GAME / name).unlink(missing_ok=True)


def stage_fov_fix(width: int, height: int, log) -> Path:
    if not FOV_ASI_SOURCE.is_file():
        raise LauncherError(f"FOV plugin missing: {FOV_ASI_SOURCE}")
    if sha256(FOV_ASI_SOURCE) != FOV_ASI_EXPECTED_HASH:
        raise LauncherError(f"FOV plugin hash mismatch: {FOV_ASI_SOURCE}")
    if not FOV_LAUNCHER_EXE.is_file() or not FOV_BOOTSTRAP_DLL.is_file():
        raise LauncherError("Widescreen FOV launcher binaries missing in build/widescreen-test/Release")

    asi_dest = GAME / "MechWarrior3FOVFix.asi"
    shutil.copyfile(FOV_ASI_SOURCE, asi_dest)
    ini_dest = GAME / "MechWarrior3FOVFix.ini"
    ini_content = (
        "[FOVFix]\r\n"
        "Enabled=true\r\n\r\n"
        "[Settings]\r\n"
        f"Width={width}\r\n"
        f"Height={height}\r\n"
        "FOVFactor=1.0\r\n"
    )
    ini_dest.write_text(ini_content, encoding="ascii")
    log(f"Staged camera FOV fix for {width}x{height} unstretched widescreen")
    return asi_dest


def start_game_direct(diagnostic: bool) -> tuple[int, int]:
    cleanup_fov_staging()
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    si = STARTUPINFOW()
    si.cb = ctypes.sizeof(si)
    si.lpDesktop = "WinSta0\\Default"
    pi = PROCESS_INFORMATION()
    env = os.environ.copy()
    env["D7VK_LOG_LEVEL"] = "debug" if diagnostic else "info"
    env_buf = ctypes.create_unicode_buffer("".join(f"{k}={v}\0" for k, v in env.items()) + "\0")
    cmd = ctypes.create_unicode_buffer(f'"{GAME_EXE}"')
    if not k32.CreateProcessW(str(GAME_EXE), cmd, None, None, False, 0x00000400,
                              ctypes.byref(env_buf), str(GAME), ctypes.byref(si), ctypes.byref(pi)):
        raise LauncherError(f"CreateProcessW failed: {ctypes.get_last_error()}")
    k32.CloseHandle(pi.hThread)
    return int(pi.hProcess), int(pi.dwProcessId)


def start_game_fov(run_dir: Path, width: int, height: int, diagnostic: bool, log) -> tuple[int, int]:
    asi_path = stage_fov_fix(width, height, log)
    evidence_log = run_dir / "fov-bootstrap.log"
    env = os.environ.copy()
    env["MW34_FOV_FILE"] = str(asi_path)
    env["D7VK_LOG_LEVEL"] = "debug" if diagnostic else "info"

    cmd = [str(FOV_LAUNCHER_EXE), str(GAME_EXE), str(FOV_BOOTSTRAP_DLL), str(evidence_log)]
    proc = subprocess.run(cmd, env=env, cwd=str(GAME), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        err_msg = proc.stderr.strip() or proc.stdout.strip() or f"exit code {proc.returncode}"
        raise LauncherError(f"FOV hook launcher failed: {err_msg}")

    m = re.search(r"PID=(\d+)", proc.stdout)
    if not m:
        raise LauncherError(f"Could not parse PID from FOV launcher output: {proc.stdout}")
    pid = int(m.group(1))

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    SYNCHRONIZE = 0x00100000
    PROCESS_QUERY_INFORMATION = 0x0400
    handle = k32.OpenProcess(SYNCHRONIZE | PROCESS_QUERY_INFORMATION, False, pid)
    if not handle:
        raise LauncherError(f"OpenProcess for game PID {pid} failed: {ctypes.get_last_error()}")
    return int(handle), pid


def wait_exit(handle: int) -> int:
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.WaitForSingleObject(w.HANDLE(handle), 0xFFFFFFFF)
    code = w.DWORD()
    k32.GetExitCodeProcess(w.HANDLE(handle), ctypes.byref(code))
    k32.CloseHandle(w.HANDLE(handle))
    return int(code.value)


def expected_ddraw_hash() -> str:
    if DDRAW_SHA256:
        return DDRAW_SHA256.lower()
    if DDRAW_SHA256_FILE.is_file():
        return DDRAW_SHA256_FILE.read_text(encoding="ascii").split()[0].lower()
    raise LauncherError("No admitted launcher ddraw.dll hash configured")


def summarize_log(path: Path) -> dict:
    keys = ("Effective configuration", "ddraw.", "d3d9.", "SetDisplayMode", "Back buffer size",
            "MSAA", "Found device", "Creating device", "err:")
    lines = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if any(k in line for k in keys):
                lines.append(line.strip())
    return {"lines": lines[:200]}


def launch(settings: dict, log, diagnostic: bool = False, auto_close_sec: float = 0.0) -> int:
    if (running := running_mech3()):
        raise LauncherError(f"Mech3.exe is already running: {running}")
    if sha256(GAME_EXE) != EXE_SHA256:
        raise LauncherError("Profile Mech3.exe is not the admitted US 1.2 executable")
    if sha256(GAME / "ddraw.dll") != expected_ddraw_hash():
        raise LauncherError("Profile ddraw.dll is not the admitted launcher D7VK build")

    res_key = normalize_resolution(settings["resolution"])
    prof = RESOLUTION_PROFILES[res_key]
    res_mode = prof["vmode"]
    aa = AA_LEVELS[settings["aa"]]
    af = AF_LEVELS[settings["af"]]
    run_dir = RUNS / datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)

    tex = apply_textures(settings["ai_textures"], log)
    conf = write_dxvk_conf(aa, af)

    reg_names = ["InGameVMode", "TextureMemory_HW"]
    before = read_reg(reg_names)
    (run_dir / "registry-before.json").write_text(json.dumps(before, indent=2), encoding="utf-8")
    new = {"InGameVMode": {"value": res_mode, "type": winreg.REG_DWORD}}
    if settings["ai_textures"]:
        new["TextureMemory_HW"] = {"value": AI_TEXTURE_MEMORY_MODE, "type": winreg.REG_DWORD}
    for log_name in ("Mech3_ddraw.log", "mech3.out", "mech3.err"):
        (GAME / log_name).unlink(missing_ok=True)

    record = {
        "settings": settings,
        "profile": prof,
        "in_game_vmode": res_mode,
        "dxvk_conf": conf,
        "textures": tex,
        "ddraw_sha256": expected_ddraw_hash(),
        "exe_sha256": EXE_SHA256,
    }
    write_reg(new)
    try:
        if prof["widescreen"]:
            handle, pid = start_game_fov(run_dir, prof["width"], prof["height"], diagnostic, log)
        else:
            handle, pid = start_game_direct(diagnostic)
        record["pid"] = pid
        log(f"Started Mech3.exe PID {pid}: {res_key}, AA {settings['aa']}, "
            f"AF {settings['af']}, {'AI' if settings['ai_textures'] else 'original'} textures")
        if diagnostic:
            def capture():
                import time
                time.sleep(4.0)
                try:
                    sys.path.insert(0, str(WRAPPER))
                    from inspect_live_process import enum_modules
                    mods = [m for m in enum_modules(pid)
                            if any(n in str(m).lower() for n in ("ddraw", "d3dimm", "vulkan", "d3d9", "dgvoodoo", "fov"))]
                    (run_dir / "live-modules.json").write_text(json.dumps(mods, indent=2), encoding="utf-8")
                except Exception as exc:
                    (run_dir / "live-modules-error.txt").write_text(repr(exc), encoding="utf-8")
            threading.Thread(target=capture, daemon=True).start()
        if auto_close_sec > 0.0:
            def auto_close():
                import time
                time.sleep(auto_close_sec)
                deadline = time.time() + 25.0
                WM_CLOSE = 0x0010
                try:
                    u32 = ctypes.WinDLL("user32", use_last_error=True)
                    u32.OpenDesktopW.argtypes = [w.LPCWSTR, w.DWORD, w.BOOL, w.DWORD]
                    u32.OpenDesktopW.restype = w.HANDLE
                    u32.SetThreadDesktop.argtypes = [w.HANDLE]
                    u32.SetThreadDesktop.restype = w.BOOL
                    hdesk = u32.OpenDesktopW("Default", 0, False, 0x10000000)
                    if hdesk:
                        u32.SetThreadDesktop(hdesk)

                    posted = 0
                    def enum_proc(hwnd, _):
                        nonlocal posted
                        proc_id = w.DWORD()
                        u32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc_id))
                        if proc_id.value == pid:
                            u32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
                            posted += 1
                        return True

                    WNDENUMPROC = ctypes.WINFUNCTYPE(w.BOOL, w.HWND, w.LPARAM)
                    while time.time() < deadline:
                        u32.EnumWindows(WNDENUMPROC(enum_proc), 0)
                        if posted > 0:
                            break
                        time.sleep(0.5)
                    (run_dir / "auto-close.txt").write_text(f"Posted WM_CLOSE to {posted} windows\n", encoding="utf-8")
                except Exception as e:
                    (run_dir / "auto-close-error.txt").write_text(str(e), encoding="utf-8")
            threading.Thread(target=auto_close, daemon=True).start()
        record["exit_code"] = wait_exit(handle)
    finally:
        after_game = read_reg(reg_names)
        write_reg(before)
        record["registry_after_game"] = after_game
        record["registry_restored"] = read_reg(reg_names) == before
        for log_name in ("Mech3_ddraw.log", "mech3.out", "mech3.err", "MechWarrior3FOVFix.log"):
            src_log = GAME / log_name
            if src_log.is_file():
                shutil.copy2(src_log, run_dir / log_name)
        cleanup_fov_staging()
        record["d7vk_log_summary"] = summarize_log(run_dir / "Mech3_ddraw.log")
        (run_dir / "session.json").write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")
    log(f"Game exited ({record['exit_code']}); registry restored={record['registry_restored']}; record {run_dir}")
    return record["exit_code"]


# ---------------------------------------------------------------- settings / UI

def normalize_resolution(name: str) -> str:
    if name in RESOLUTION_PROFILES:
        return name
    legacy_map = {
        "1024x768": "1024x768 (Native 4:3)",
        "800x600": "800x600 (Legacy 4:3)",
        "640x480": "640x480 (Legacy 4:3)",
        "1920x1080": "1920x1080 (1080p Widescreen 16:9)",
        "2560x1440": "2560x1440 (1440p Widescreen 16:9)",
        "3440x1440": "3440x1440 (Ultrawide 21:9)",
        "3840x2160": "3840x2160 (4K Widescreen 16:9)",
        "1440x1080": "1440x1080 (1080p 4:3 Equivalent)",
        "1920x1440": "1920x1440 (1440p 4:3 Equivalent)",
        "2880x2160": "2880x2160 (4K 4:3 Equivalent)",
        "1600x1200": "1920x1440 (1440p 4:3 Equivalent)",
    }
    return legacy_map.get(name, DEFAULTS["resolution"])


def load_settings() -> dict:
    s = dict(DEFAULTS)
    try:
        s.update(json.loads(SETTINGS_FILE.read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    s["resolution"] = normalize_resolution(s.get("resolution", ""))
    if s["aa"] not in AA_LEVELS: s["aa"] = DEFAULTS["aa"]
    if s["af"] not in AF_LEVELS: s["af"] = DEFAULTS["af"]
    return s


def gui() -> int:
    import tkinter as tk
    from tkinter import ttk, messagebox

    s = load_settings()
    root = tk.Tk()
    root.title("MechWarrior 3 - Vulkan (D7VK)")
    root.resizable(False, False)
    frm = ttk.Frame(root, padding=14)
    frm.grid()
    vars_ = {}

    # Resolution row
    ttk.Label(frm, text="Resolution").grid(row=0, column=0, sticky="w", pady=4)
    res_var = tk.StringVar(value=s["resolution"])
    res_cb = ttk.Combobox(frm, textvariable=res_var, values=list(RESOLUTION_PROFILES), state="readonly", width=36)
    res_cb.grid(row=0, column=1, sticky="ew", pady=4)
    vars_["resolution"] = res_var

    # Aspect / description hint label
    hint_var = tk.StringVar()
    ttk.Label(frm, textvariable=hint_var, foreground="#555", font=("Segoe UI", 8), wraplength=320).grid(
        row=1, column=1, sticky="w", pady=(0, 4))

    def on_res_change(*_):
        p = RESOLUTION_PROFILES.get(res_var.get())
        if p:
            hint_var.set(p.get("note", ""))
        else:
            hint_var.set("")
    res_var.trace_add("write", on_res_change)
    on_res_change()

    # AA row
    ttk.Label(frm, text="Anti-aliasing").grid(row=2, column=0, sticky="w", pady=4)
    aa_var = tk.StringVar(value=s["aa"])
    ttk.Combobox(frm, textvariable=aa_var, values=list(AA_LEVELS), state="readonly", width=36).grid(
        row=2, column=1, sticky="ew", pady=4)
    vars_["aa"] = aa_var

    # AF row
    ttk.Label(frm, text="Anisotropic filtering").grid(row=3, column=0, sticky="w", pady=4)
    af_var = tk.StringVar(value=s["af"])
    ttk.Combobox(frm, textvariable=af_var, values=list(AF_LEVELS), state="readonly", width=36).grid(
        row=3, column=1, sticky="ew", pady=4)
    vars_["af"] = af_var

    # AI textures checkbutton
    ai = tk.BooleanVar(value=bool(s["ai_textures"]))
    ttk.Checkbutton(frm, text="Load AI-upscaled textures (39 banks)", variable=ai).grid(
        row=4, column=0, columnspan=2, sticky="w", pady=6)

    ttk.Label(frm, text="Frame cap: 30 FPS ceiling (fixed for game physics)", foreground="#666").grid(
        row=5, column=0, columnspan=2, sticky="w")

    status = tk.StringVar(value="Ready")
    ttk.Label(frm, textvariable=status, wraplength=400).grid(
        row=7, column=0, columnspan=2, sticky="w", pady=(8, 0))

    btn = ttk.Button(frm, text="Launch MechWarrior 3")
    btn.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    def log(msg):
        root.after(0, status.set, msg)

    def work(cur):
        try:
            root.after(0, root.withdraw)
            launch(cur, log)
        except Exception as exc:
            root.after(0, root.deiconify)
            root.after(0, messagebox.showerror, "Launch failed", str(exc))
            log(f"Failed: {exc}")
        finally:
            root.after(0, root.deiconify)
            root.after(0, btn.state, ["!disabled"])

    def on_launch():
        cur = {k: v.get() for k, v in vars_.items()}
        cur["ai_textures"] = bool(ai.get())
        SETTINGS_FILE.write_text(json.dumps(cur, indent=2), encoding="utf-8")
        btn.state(["disabled"])
        status.set("Preparing (first AI-texture switch verifies ~11 GB of banks)...")
        threading.Thread(target=work, args=(cur,), daemon=True).start()

    btn.configure(command=on_launch)
    root.mainloop()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--no-gui", action="store_true")
    p.add_argument("--resolution", choices=list(RESOLUTION_PROFILES))
    p.add_argument("--aa", choices=list(AA_LEVELS))
    p.add_argument("--af", choices=list(AF_LEVELS))
    p.add_argument("--textures", choices=["ai", "original"])
    p.add_argument("--diagnostic", action="store_true", help="debug D7VK log + live module capture")
    p.add_argument("--prepare-only", action="store_true", help="apply textures/config without launching")
    p.add_argument("--auto-close-sec", type=float, default=0.0, help="automated exit delay for testing")
    a = p.parse_args()
    if not a.no_gui:
        return gui()
    s = load_settings()
    if a.resolution: s["resolution"] = a.resolution
    if a.aa: s["aa"] = a.aa
    if a.af: s["af"] = a.af
    if a.textures: s["ai_textures"] = a.textures == "ai"
    try:
        if a.prepare_only:
            if running_mech3():
                raise LauncherError("Mech3.exe is running")
            print(apply_textures(s["ai_textures"], print))
            print("\n".join(write_dxvk_conf(AA_LEVELS[s["aa"]], AF_LEVELS[s["af"]])))
            return 0
        return launch(s, print, a.diagnostic, a.auto_close_sec)
    except LauncherError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
