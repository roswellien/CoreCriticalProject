"""Run the full-graphics arena benchmark using the native Play launch planner."""

import argparse
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_ROOT = ROOT / "local" / "benchmark"
FIXTURES = ROOT / "tools" / "benchmark" / "fixtures"
SUITE_SCENES = ("c1mp1", "c2mp2", "c3mp1", "c4mp2")
BLOCK_ORDER = ("A1", "B1", "B2", "A2")
sys.path.insert(0, str(ROOT / "tools" / "remaster-launcher"))
from mw3_re_launch import plan_launch

PACK_FIELDS = {
    "prepared-native-v1": "model_packs",
    "prepared-skins-v1": "skin_packs",
    "prepared-environment-v1": "environment_packs",
    "prepared-ui-v1": "ui_packs",
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_packs(data_root, active):
    """Keep Play?s active pack order, with Updated MW3 wins for shared chassis."""
    installed = {}
    mod_root = (data_root / "mods").resolve(strict=True)
    if not mod_root.is_relative_to(data_root.resolve()):
        raise ValueError("Installed pack directory leaves the launcher data root")
    for path in sorted(mod_root.iterdir()):
        if path.name.startswith(".") or not (path / "pack.json").is_file():
            continue
        if not path.resolve().is_relative_to(mod_root):
            raise ValueError(f"Installed pack leaves the mods directory: {path}")
        manifest = read_json(path / "pack.json")
        profile = (manifest.get("native_payload") or {}).get("profile")
        if manifest.get("schema_version") != 2 or profile not in {
            *PACK_FIELDS,
            "additional-chassis-v1",
        }:
            continue
        pack_id = manifest["id"]
        if pack_id in installed:
            raise ValueError(f"Duplicate installed pack ID: {pack_id}")
        installed[pack_id] = (path, profile)
    order = [pack_id for pack_id in dict.fromkeys(active) if pack_id in installed]
    updated = "com.mw3remaster.updated-mw3-mechs"
    mw5 = "com.mw3remaster.mw5-mechs"
    # The full profile needs both families. MW5 also supplies all four chassis
    # in the updated MW3 pack, so the update takes precedence on those four.
    if updated in order and mw5 in order and order.index(updated) > order.index(mw5):
        order.remove(updated)
        order.insert(order.index(mw5), updated)
    return [installed[pack_id] for pack_id in order]


WINDOW_MODES = {
    "windowed": "windowed",
    "fullscreen": "fullscreen",
    "fullscreen_windowed": "borderless",
    "borderless": "borderless",
}
TOGGLES = ("DynamicLighting", "Shadows", "Headlights", "WaterDetail", "CloudDetail")
OPTIONS = {
    "aa": "AntiAliasing",
    "af": "AnisotropicFiltering",
    "draw-distance": "DrawDistance",
    "fog-distance": "FogDistance",
    "resolution": "Resolution",
    "window-mode": "WindowMode",
    "flare-style": "FlareStyle",
    "render-thread": "RenderThread",
    "headlights": "Headlights",
    "dynamic-lighting": "DynamicLighting",
    "shadows": "Shadows",
    "water-detail": "WaterDetail",
    "cloud-detail": "CloudDetail",
    "active-packs": "ActivePacks",
    "game-dir": "GamePath",
}


def effective_settings(saved, overrides):
    settings = dict(saved)
    for field, value in overrides.items():
        if value is not None:
            settings[field] = value
    if "Resolution" in settings:
        width, separator, height = settings.pop("Resolution").lower().partition("x")
        if (
            not separator
            or not width.isascii()
            or not height.isascii()
            or not width.isdecimal()
            or not height.isdecimal()
        ):
            raise ValueError("Resolution must be WxH")
        settings["Width"], settings["Height"] = int(width), int(height)
    for field in ("Width", "Height", "AnisotropicFiltering", "DrawDistance", "FogDistance"):
        if type(settings.get(field)) is not int:
            raise ValueError(f"Expected integer launcher setting {field}")
    for field in (*TOGGLES, "RenderThread"):
        if type(settings.get(field)) is not bool:
            raise ValueError(f"Expected Boolean launcher setting {field}")
    packs = settings.get("ActivePacks")
    if not isinstance(packs, list) or any(not isinstance(pack, str) for pack in packs):
        raise ValueError("ActivePacks must be an ordered list of pack IDs")
    if settings["WindowMode"] not in WINDOW_MODES:
        raise ValueError("Unknown Play window mode")
    if overrides.get("RenderThread") is False:
        raise ValueError("Benchmark requires the render thread")
    settings["RenderThread"] = True
    mandatory = {
        "Renderer": "vulkan-wsi",
        "VSync": False,
        "PresentMode": "immediate",
        "DiskCache": False,
    }
    for key, expected in mandatory.items():
        if key in overrides and overrides[key] is not None and overrides[key] != expected:
            raise ValueError(f"Benchmark requires {key}={expected}")
        settings[key] = expected
    return {
        key: settings[key]
        for key in (
            "Width",
            "Height",
            *[field for field in OPTIONS.values() if field != "Resolution"],
            *mandatory,
        )
    }


def resolve_game(settings):
    path = Path(settings["GamePath"])
    if not (path / "zbd" / "reader.zbd").is_file():
        raise ValueError(f"GamePath lacks zbd/reader.zbd: {path}")
    return path.resolve(strict=True)


def build_launch(
    definition_path, scene_id, output, profile, data_root, launcher_runtime, executable, settings
):
    definition = read_json(definition_path)
    matches = [scene for scene in definition["scenes"] if scene["id"] == scene_id]
    if len(matches) != 1:
        raise ValueError(f"Expected one benchmark scene named {scene_id}")
    installed = read_packs(data_root, settings["ActivePacks"])
    preview = {field: [] for field in PACK_FIELDS.values()}
    for path, kind in installed:
        if kind in PACK_FIELDS:
            preview[PACK_FIELDS[kind]].append(str(path))
    preview.update(
        draw_distance=settings["DrawDistance"],
        fog_distance=settings["FogDistance"],
        hud="core-critical" if preview["ui_packs"] else None,
        hud_text=False if preview["ui_packs"] else None,
        dynamic_lighting=settings["DynamicLighting"],
        shadows=settings["Shadows"],
        headlights=settings["Headlights"] and settings["DynamicLighting"],
        water_detail=settings["WaterDetail"],
        cloud_detail=settings["CloudDetail"],
        stock_headlight_catalog=str(launcher_runtime / "resources" / "stock-headlights.bin"),
        headlight_bindings=str(data_root / "mw3-re/profiles/native-preview/mw3-headlights.txt"),
    )
    stock_effect = launcher_runtime / "resources" / "stock-effect-lights.bin"
    if stock_effect.is_file():
        preview["stock_effect_catalog"] = str(stock_effect)
    scene = matches[0]
    descriptor = read_json(launcher_runtime / "runtime.json")
    request = {
        "schema_version": 4,
        "engine": "mw3-re",
        "runtime_root": str(launcher_runtime),
        "executable": str(launcher_runtime / descriptor["roles"]["executable"]),
        "game_dir": str(settings["GamePath"]),
        "write_dir": str(profile),
        "renderer": "vulkan-wsi",
        "width": settings["Width"],
        "height": settings["Height"],
        "aa": settings["AntiAliasing"],
        "af": settings["AnisotropicFiltering"],
        "window_mode": WINDOW_MODES[settings["WindowMode"]],
        "render_thread": True,
        "lighting": "normal",
        "flare_style": settings["FlareStyle"],
        "disk_cache": False,
        "assets": [],
        "visuals": {"pom": True},
        "preview": preview,
    }
    plan = plan_launch(request)
    if not plan["ok"]:
        raise ValueError("; ".join(plan["reasons"]))
    # The installed runtime supplies Play's declared resources. Run the local build
    # under test so the benchmark and the generated files stay in this worktree.
    argv = plan["argv"]
    argv[0] = str(executable)
    argv.extend(
        (
            "--seed",
            str(scene["seed"]),
            "--benchmark",
            str(definition_path),
            "--benchmark-scene",
            scene_id,
            "--benchmark-resolution",
            f"{settings['Width']}x{settings['Height']}",
            "--benchmark-window-mode",
            request["window_mode"],
            "--benchmark-out",
            str(output),
            "--no-vfw-helper",
        )
    )
    for path, _ in installed:
        argv.extend(("--benchmark-pack", str(path)))
    plan["working_directory"] = str(executable.parent)
    plan["launcher_settings"] = settings
    return plan


def launch_scene(plan):
    return subprocess.call(
        plan["argv"], cwd=plan["working_directory"], env={**os.environ, **plan["environment"]}
    )


def run_scene(definition, scene, output, profile, data_root, runtime, executable, settings):
    profile.mkdir(parents=True)
    plan = build_launch(
        definition, scene, output, profile, data_root, runtime, executable, settings
    )
    (profile / "launch-plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    for item in plan.get("skipped_packs", []):
        print(f"Play planner left out {item['root']}: {item['reason']}", file=sys.stderr)
    print(f"Benchmark scene {scene}\n" + json.dumps(settings, indent=2), flush=True)
    argv = plan["argv"]
    toggles = {}
    for flag in (
        "--cc-dynamic-lighting",
        "--cc-sun-shadows",
        "--cc-fixture-lights",
        "--cc-water-detail",
        "--cc-cloud-detail",
        "--cc-pom",
    ):
        toggles[flag] = flag in argv and argv[argv.index(flag) + 1] == "1"
    for flag in ("--cc-effect-lights", "--cc-mech-headlights"):
        toggles[flag] = flag in argv
    print("Resolved Play features:\n" + json.dumps(toggles, indent=2), flush=True)
    return launch_scene(plan)


def run_suite(definition, output, label, data_root, runtime, executable, settings):
    definition_hash = sha256(definition)
    document = read_json(definition)
    scenes = tuple(scene["id"] for scene in document["scenes"])
    if document["version"] != 1 or scenes != SUITE_SCENES:
        raise ValueError(f"Suite must list these scenes in order: {', '.join(SUITE_SCENES)}")
    output.mkdir(parents=True)
    manifest = {
        "version": 1,
        "label": label,
        "host": socket.gethostname(),
        "definition_sha256": definition_hash,
        "started_ns": time.time_ns(),
        "scenes": [],
    }

    def run_entry(scene, directory):
        if sha256(definition) != definition_hash:
            raise ValueError("Definition changed during the suite")
        profile = output / "profiles" / directory
        started = time.time_ns()
        code = run_scene(
            definition, scene, output / directory, profile, data_root, runtime, executable, settings
        )
        if code:
            raise ValueError(f"{directory} ({scene}) exited with status {code}")
        summary = output / directory / "summary.json"
        result = read_json(summary)
        if result.get("valid") is not True or result.get("scene_id") != scene:
            raise ValueError(f"Invalid scene result: {summary}")
        return {
            "id": scene,
            "summary": summary.relative_to(output).as_posix(),
            "summary_sha256": sha256(summary),
            "profile": profile.relative_to(output).as_posix(),
            "started_ns": started,
            "finished_ns": time.time_ns(),
        }

    if label == "A1":
        manifest["conditioning"] = run_entry(SUITE_SCENES[0], "conditioning")
    for scene in scenes:
        manifest["scenes"].append(run_entry(scene, scene))
    if sha256(definition) != definition_hash:
        raise ValueError("Definition changed during the suite")
    manifest["finished_ns"] = time.time_ns()
    (output / "suite.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in OPTIONS:
        if flag in {"af", "draw-distance", "fog-distance"}:
            parser.add_argument(f"--{flag}", type=int)
        elif flag in {
            "render-thread",
            "headlights",
            "dynamic-lighting",
            "shadows",
            "water-detail",
            "cloud-detail",
        }:
            parser.add_argument(f"--{flag}", choices=("on", "off"), nargs="?", const="on")
        else:
            parser.add_argument(f"--{flag}")
    parser.add_argument("--renderer")
    parser.add_argument("--vsync", choices=("on", "off"))
    parser.add_argument("--present-mode")
    parser.add_argument("--disk-cache", choices=("on", "off"))
    parser.add_argument(
        "--launcher-runtime",
        type=Path,
        required=True,
        help="Installed Play launcher's NativePreview directory",
    )
    parser.add_argument("--exe", type=Path, default=BENCHMARK_ROOT / "build/Release/mw3.exe")
    parser.add_argument("--definition", type=Path)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--scene")
    selection.add_argument("--suite", action="store_true")
    parser.add_argument("--run-label", choices=(*BLOCK_ORDER, "smoke"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.suite != (args.run_label is not None):
            raise ValueError("--suite and --run-label must be supplied together")
        data_root = (Path(os.environ["LOCALAPPDATA"]) / "MW3Remaster").resolve(strict=True)
        overrides = {
            field: getattr(args, flag.replace("-", "_")) for flag, field in OPTIONS.items()
        }
        for field in (*TOGGLES, "RenderThread"):
            if overrides[field] is not None:
                overrides[field] = overrides[field] == "on"
        if overrides["ActivePacks"] is not None:
            overrides["ActivePacks"] = [
                p.strip() for p in overrides["ActivePacks"].split(",") if p.strip()
            ]
        overrides.update(
            Renderer=args.renderer,
            PresentMode=args.present_mode,
            VSync=None if args.vsync is None else args.vsync == "on",
            DiskCache=None if args.disk_cache is None else args.disk_cache == "on",
        )
        settings = effective_settings(read_json(data_root / "settings.json"), overrides)
        game = resolve_game(settings)
        settings["GamePath"] = str(game)
        launcher_runtime = args.launcher_runtime.resolve(strict=True)
        executable = args.exe.resolve(strict=True)
        output = args.out.resolve()
        profile = None if args.suite else output.with_name(output.name + "-profile")
        write_paths = (output,) if profile is None else (output, profile)
        for path in write_paths:
            if not path.is_relative_to(BENCHMARK_ROOT.resolve()) or path.exists():
                raise ValueError(f"Expected a fresh path under local/benchmark: {path}")
            if any(path.is_relative_to(root) for root in (data_root, game, launcher_runtime)):
                raise ValueError(f"Benchmark write path overlaps a read-only input: {path}")
        default_name = "suite-benchmark.json" if args.suite else "c1mp1-benchmark.json"
        definition = (args.definition or FIXTURES / default_name).resolve(strict=True)
        if profile is None:
            return run_suite(
                definition,
                output,
                args.run_label,
                data_root,
                launcher_runtime,
                executable,
                settings,
            )
        return run_scene(
            definition,
            args.scene or "c1mp1",
            output,
            profile,
            data_root,
            launcher_runtime,
            executable,
            settings,
        )
    except (OSError, KeyError, ValueError) as error:
        print(f"benchmark: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
