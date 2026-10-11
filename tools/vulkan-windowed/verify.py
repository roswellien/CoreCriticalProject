"""Verify windowed presentation receipts and GPU pixels; no live-gameplay credit."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def ppm(path):
    data = path.read_bytes()
    header = re.match(rb"P6\n([0-9]+) ([0-9]+)\n255\n", data)
    if not header:
        raise ValueError(f"Invalid RGB witness header: {path}")
    width, height = map(int, header.groups())
    pixels = data[header.end():]
    if not width or not height or len(pixels) != width * height * 3:
        raise ValueError(f"Invalid RGB witness extent: {path}")
    return width, height, pixels


def expected_image(source, width, height):
    """CPU oracle: centered aspect fit, black border, nearest source pixel centers."""
    sw, sh, pixels = source
    # Integer arithmetic independently determines the limiting axis.
    if width * sh <= height * sw:
        dw, dh = width, max(1, width * sh // sw)
    else:
        dw, dh = max(1, height * sw // sh), height
    left, top = (width - dw) // 2, (height - dh) // 2
    output = bytearray(width * height * 3)
    for y in range(dh):
        sy = min(sh - 1, (2 * y + 1) * sh // (2 * dh))
        for x in range(dw):
            sx = min(sw - 1, (2 * x + 1) * sw // (2 * dw))
            start = ((top + y) * width + left + x) * 3
            output[start:start + 3] = pixels[(sy * sw + sx) * 3:(sy * sw + sx) * 3 + 3]
    return bytes(output), [left, top, dw, dh]


def check_pixels(source, actual):
    width, height, pixels = actual
    expected, rectangle = expected_image(source, width, height)
    mismatches = sum(pixels[i:i + 3] != expected[i:i + 3] for i in range(0, len(pixels), 3))
    if mismatches:
        raise ValueError(f"Presentation image differs at {mismatches} pixels")
    return {"width": width, "height": height, "content_rectangle": rectangle,
            "checked_pixels": width * height, "mismatched_pixels": 0}


def verify(directory):
    report = read_json(directory / "report.json")
    launch = read_json(directory / "launch.json")
    package = read_json(directory / "scene.json")
    result = report.get("result") or {}
    text = (directory / "run.txt").read_text(encoding="utf-8-sig")
    if report.get("passed") is not True or "VALIDATION:" in text:
        raise ValueError("Failed run or validation diagnostic")
    if (report.get("native_gameplay") is not False or report.get("full_frame_equivalence") is not False
            or report.get("initializer_credit") != 0 or result.get("live_gameplay") is not False):
        raise ValueError("Capture replay scope overstated")
    if (result.get("validation_messages") != 0 or result.get("resources_released") is not True
            or result.get("window_destroyed") is not True or "WINDOW_VISIBLE: true" not in text):
        raise ValueError("Window/validation/teardown evidence incomplete")
    if report["files"] != launch["files"] or len(report["files"]) < 20:
        raise ValueError("Input hash manifest inconsistent")
    for filename, expected in report["files"].items():
        if digest(Path(filename)) != expected:
            raise ValueError(f"Executed input changed: {filename}")
    for name in ("viewer.cpp", "presenter.hpp", "run.ps1", "verify.py",
                 "mw34_vulkan_windowed.exe", "VkLayer_khronos_validation.dll"):
        if not any(Path(filename).name == name for filename in report["files"]):
            raise ValueError(f"Missing executed input hash: {name}")
    raw = (directory / "scene.replay").read_bytes()
    if raw[:8] != b"MW34SCN3":
        raise ValueError("Unexpected scene package")
    width, height, textures, draws = struct.unpack_from("<4I", raw, 8)
    capture = Path(report["capture"])
    if (package["package_sha256"] != digest(directory / "scene.replay")
            or package["package_bytes"] != len(raw)
            or package["manifest_sha256"] != digest(capture / "frame/capture.jsonl")
            or package["live"] is not True or package["filter_source"] != "legacy"
            or [width, height] != package["target_size"] or draws != package["draws"]
            or textures != package["textures"] or result["draws_per_pass"] != draws
            or [result["scene_width"], result["scene_height"]] != [width, height]):
        raise ValueError("Executed package/capture metadata inconsistent")
    frames = result["presented_frames"]
    if frames < 1 or result["render_passes"] != frames + 1 or result["present_fence_waits"] != frames:
        raise ValueError("Repeated raster execution or presentation completion incomplete")
    completion = [json.loads(line[len("WINDOWED_RESULT: "):]) for line in text.splitlines()
                  if line.startswith("WINDOWED_RESULT: ")]
    if completion != [result]:
        raise ValueError("Runtime result does not match wrapper result")
    generations = [json.loads(line[len("SWAPCHAIN: "):]) for line in text.splitlines()
                   if line.startswith("SWAPCHAIN: ")]
    if (len(generations) != result["swapchain_generations"]
            or [g["generation"] for g in generations] != list(range(1, len(generations) + 1))):
        raise ValueError("Swapchain lifecycle accounting inconsistent")
    if result["self_test"]:
        if len(generations) < 3 or not all(result[key] is True for key in
                                         ("minimize_observed", "restore_observed", "escape_observed")):
            raise ValueError("Resize/minimize/restore/Escape test incomplete")
    source = ppm(directory / "replay.ppm")
    reference = capture / "preview/vulkan-0.5.ppm"
    if source != ppm(reference):
        raise ValueError("Raster changed from the accepted offscreen replay")
    if source[:2] != (width, height):
        raise ValueError("Raster witness dimensions inconsistent")
    witnesses = []
    for generation in generations:
        path = directory / f"replay.ppm.presented-{generation['generation']}.ppm"
        actual = ppm(path)
        if actual[:2] != (generation["width"], generation["height"]) or generation["format"] not in (37, 44):
            raise ValueError("Presentation extent/format inconsistent")
        witness = check_pixels(source, actual)
        witness.update({"generation": generation["generation"], "sha256": digest(path)})
        witnesses.append(witness)
    # Independent rejection checks: corrupt a scene pixel, then a border pixel.
    controls = []
    for label, extent in (("scene_pixel_corruption", (width, height)),
                          ("letterbox_corruption", (width + 213, height))):
        expected, rectangle = expected_image(source, *extent)
        changed = bytearray(expected)
        offset = 0 if label.startswith("letterbox") else (
            (rectangle[1] + rectangle[3] // 2) * extent[0] + rectangle[0] + rectangle[2] // 2) * 3
        changed[offset] ^= 1
        try:
            check_pixels(source, (*extent, bytes(changed)))
        except ValueError:
            controls.append(label)
        else:
            raise ValueError(f"Negative control admitted: {label}")
    files = {str(path.resolve()): digest(path) for path in (
        directory / "report.json", directory / "launch.json", directory / "run.txt",
        directory / "scene.json", directory / "scene.replay", directory / "replay.ppm", reference)}
    return {"passed": True, "presented_frames": frames, "draws_per_pass": draws,
            "textures_including_white_fallback": textures,
            "offscreen_reference_exact": True, "witnesses": witnesses,
            "validation_messages": 0, "negative_controls_rejected": controls,
            "input_hashes_checked": len(report["files"]), "receipt_hashes": files,
            "native_gameplay": False, "full_frame_equivalence": False, "initializer_credit": 0,
            "scope": "Repeated saved scene raster and GPU swapchain images; static viewpoint, one captured scene interval"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = verify(args.directory)
    output = args.directory / "presentation-verification.json"
    if output.exists():
        if read_json(output) != result:
            raise ValueError("Existing verification receipt differs; preserve it and use a new run")
    else:
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "presented_frames": result["presented_frames"],
                      "witnesses": len(result["witnesses"]), "output": str(output)}, indent=2))


if __name__ == "__main__":
    main()
