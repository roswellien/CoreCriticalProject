"""Exact local Pirate's Moon inputs for the existing translation pipeline.

This is an experimental target, not M4 admission or a compatibility claim.
Paths are resolved from an explicit installation root. No game code is executed.
"""
from __future__ import annotations

import hashlib
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/analysis"))
from pe import PEImage, UnsupportedBinaryError, load_manifest, read_binary, validate_identity

GAME = "mw3-pirates-moon"
CONFIG = ROOT / "games" / GAME / "config"


def load_target(installation: Path) -> dict:
    """Own and verify every input before returning a usable translation profile."""
    manifest = load_manifest(CONFIG / "supported-binaries.json", expected_game=GAME)
    profile = json.loads((CONFIG / "target.json").read_text(encoding="utf-8"))
    if profile.get("schema_version") != 1 or profile.get("target") != GAME:
        raise UnsupportedBinaryError("wrong experimental target profile")
    installation = installation.resolve(strict=True)
    modules = {}
    for name, pin in profile["modules"].items():
        path = (installation / pin["filename"]).resolve(strict=True)
        if not path.is_relative_to(installation):
            raise UnsupportedBinaryError(f"module escapes the installation: {name}")
        data = read_binary(path)
        if len(data) != pin["size_bytes"] or hashlib.sha256(data).hexdigest() != pin["sha256"]:
            raise UnsupportedBinaryError(f"wrong exact {name} image: {path}")
        image = PEImage(data)
        image.metadata()
        if image.image_base != pin["image_base"] or image.entry_point_rva != pin["entry_point_rva"]:
            raise UnsupportedBinaryError(f"{name} PE identity disagrees with target profile")
        modules[name] = dict(path=path, data=data, image=image, pin=pin)
    validate_identity(modules["game"]["data"], manifest, modules["game"]["image"])
    game_image = modules["game"]["image"]
    if profile["entry"] != game_image.image_base + game_image.entry_point_rva:
        raise UnsupportedBinaryError("target entry disagrees with exact game image")
    profile["inputs"] = modules
    profile["installation"] = installation
    return profile


def code_ranges(image: PEImage) -> list[tuple[int, int]]:
    return [(image.image_base + s["virtual_address"],
             image.image_base + s["virtual_address"] + max(s["virtual_size"], s["raw_size"]))
            for s in image.sections if s["executable"]]


def closure_images(target: dict) -> dict:
    """Adapter to mfc_closure.py; derive ranges rather than carrying MW3 PCs."""
    result = {}
    for name, module in target["inputs"].items():
        ranges = code_ranges(module["image"])
        if len(ranges) != 1:
            raise ValueError(f"closure scanner requires one code section: {name}")
        result[name] = (module["path"], module["pin"]["sha256"], module["image"].image_base,
                        *ranges[0])
    return result


def require_closure(target: dict, closure: dict) -> None:
    """Reject another target's spans before lifting any proprietary bytes."""
    pins = {k: v["pin"]["sha256"] for k, v in target["inputs"].items()}
    if closure.get("target") != GAME or closure.get("images") != pins:
        raise UnsupportedBinaryError("closure belongs to different target inputs")
    for row in closure["functions"]:
        module = target["inputs"].get(row["image"])
        if module is None or not any(lo <= row["entry"] < row["end"] <= hi
                                     for lo, hi in code_ranges(module["image"])):
            raise ValueError("closure span outside its exact executable image")


def summary(target: dict) -> dict:
    return dict(target=GAME, status="experimental", entry=hex(target["entry"]),
                modules={k: dict(path=str(v["path"]), sha256=v["pin"]["sha256"],
                                 code_ranges=code_ranges(v["image"]))
                         for k, v in target["inputs"].items()})


def verify_native_assets(installation: Path) -> int:
    """Only declare the recovered hardware component when its actual banks match."""
    manifest = json.loads((CONFIG / "native-assets.json").read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or manifest.get("target") != GAME or manifest.get("install_options") != 4:
        raise UnsupportedBinaryError("wrong native hardware asset manifest")
    installation = installation.resolve(strict=True)
    if not manifest.get("files"):
        raise UnsupportedBinaryError("empty hardware component inventory")
    for pin in manifest["files"]:
        path = (installation / pin["filename"]).resolve(strict=True)
        if not path.is_relative_to(installation):
            raise UnsupportedBinaryError("hardware asset escapes installation")
        data = read_binary(path)
        if len(data) != pin["size_bytes"] or hashlib.sha256(data).hexdigest() != pin["sha256"]:
            raise UnsupportedBinaryError(f"hardware component asset identity mismatch: {path}")
    return manifest["install_options"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("installation", type=Path)
    parser.add_argument("--native-assets", action="store_true")
    args = parser.parse_args()
    result = summary(load_target(args.installation))
    if args.native_assets:
        result["verified_install_options"] = verify_native_assets(args.installation)
    print(json.dumps(result, indent=2))
