"""Prepare an isolated original-PM comparison experiment, never a native fallback.

Reuses the existing MW3 comparison hook with checked PM entry/RDTSC locations.
All original media, patched import-name copies and experiment sources stay local.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

from target import ROOT, load_target, verify_native_assets


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"comparison source changed: {old}")
    return text.replace(old, new)


def prepare(installation: Path, output: Path) -> None:
    target = load_target(installation)
    verify_native_assets(installation)
    output = output.resolve()
    if not output.is_relative_to((ROOT / "local/pirates-moon-comparison").resolve()):
        raise ValueError("original comparison must stay in local/pirates-moon-comparison/")
    if output.exists():
        raise FileExistsError(output)
    helper_path = ROOT / "tools/mw3-compare/prepare_runtime.py"
    spec = importlib.util.spec_from_file_location("mw3_compare_prepare", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    output.mkdir(parents=True)
    game, source = output / "game", output / "hook-source"
    game.mkdir()
    source.mkdir()
    installation = installation.resolve()
    for path in installation.iterdir():
        if path.is_dir():
            # Writable configuration/saves must never junction back into the install.
            if path.name.lower() in {"zbd", "music", "fonts"}:
                subprocess.run(["cmd", "/c", "mklink", "/J", str(game / path.name), str(path)],
                               check=True, capture_output=True)
            else:
                shutil.copytree(path, game / path.name)
        else:
            shutil.copyfile(path, game / path.name)
    record = {}
    for name in ("game", "mfc42", "msvcp60", "mech3msg"):
        module = target["inputs"][name]
        patched, at = helper.patch_import(module["data"])
        (game / module["path"].name).write_bytes(patched)
        record[name] = dict(source_sha256=module["pin"]["sha256"],
                            patched_sha256=hashlib.sha256(patched).hexdigest(), name_offset=at)
    shutil.copyfile(target["inputs"]["msvcrt"]["path"], game / "MSVCRZ.dll")
    for name in ("DDraw.dll", "D3DImm.dll", "dgVoodoo.conf"):
        shutil.copyfile(ROOT / "MW3" / name, game / name)
    shutil.copyfile(ROOT / "games/mw3-pirates-moon/config/native-registry.txt", game / "mw34-registry.txt")
    (game / "input.txt").write_text("# No scripted input; original-side menu baseline.\n")
    original = ROOT / "tools/mw3-compare"
    launcher = (original / "compare_launcher.cpp").read_text()
    launcher = launcher.replace('"../in-game-hook/identity.hpp"', json.dumps((ROOT / "tools/in-game-hook/identity.hpp").as_posix()))
    launcher = launcher.replace("0x5ac3a0", "0x5cefe8").replace("0x5ac3a1", "0x5cefe9")
    launcher = replace_once(launcher, "b28cdeaf6a05406dfd6b13818f8d0c6ab0d40636194396f2f8a132151035b54b", record["game"]["patched_sha256"])
    launcher = replace_once(launcher, 'auto command = L"\\\"" + game + L"\\\"";', 'auto command = L"\\\"" + game + L"\\\" -nofmv";')
    hook = (original / "compare_hook.cpp").read_text().replace("MSVCP50", "MSVCP60")
    hook = replace_once(hook, "rdtsc_sites{0x598964, 0x598991, 0x598b0e}", "rdtsc_sites{0x5b9cd2, 0x5b9d01, 0x5b9e8e}")
    hook = replace_once(hook, "w >= 0x5bb000", "w >= 0x5de000")
    hook = replace_once(hook, "reinterpret_cast<const void *>(0x5e0000), 1, 0x9a2000 - 0x5e0000",
                        "reinterpret_cast<const void *>(0x602000), 1, 0xb0f000 - 0x602000")
    # The three recovered instruction boundaries, not raw 0F31 byte matches.
    image = target["inputs"]["game"]["image"]
    for address in (0x5b9cd2, 0x5b9d01, 0x5b9e8e):
        at = image.rva_range(address - image.image_base, 2)[0]
        if target["inputs"]["game"]["data"][at:at + 2] != b"\x0f\x31":
            raise ValueError("PM timestamp instruction changed")
    (source / "compare_launcher.cpp").write_text(launcher)
    (source / "compare_hook.cpp").write_text(hook)
    for name in ("CMakeLists.txt", "exports.def"):
        shutil.copyfile(original / name, source / name)
    (output / "derivation.json").write_text(json.dumps(dict(
        target="mw3-pirates-moon", purpose="original-side research comparison only",
        modules=record, source_tools={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in original.iterdir() if p.is_file()}), indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--installation", type=Path, default=ROOT / "MW3-PiratesMoon")
    args = parser.parse_args()
    prepare(args.installation, args.output)
