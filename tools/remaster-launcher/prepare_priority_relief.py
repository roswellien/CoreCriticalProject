"""Prepare material-specific relief drafts from pinned upgraded world colours.

These remain colour-derived authoring candidates, not recovered physical height.
Exports editable height/normal PNGs and a bounded replacement world catalog.
"""

from pathlib import Path
import argparse
import hashlib
import json
import re
import struct
import numpy as np
from PIL import Image, ImageFilter
import normal_materials as catalog
from prepare_world_normals import accelerated_hash


def sha(path):
    """Stream a source or candidate file's SHA-256 for provenance checks."""
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def profile(name, reasons):
    """Select draft filter weights, resolution, slope and boundary treatment.

    Rules are ordered: a rock-name match precedes vehicle membership, then
    ground-name matching, then the structure default. These are offline draft
    heuristics, not recovered material semantics or runtime binding identities.
    """
    # Named rock families preserve their broad erosion channels. World strength
    # remains separate: no 2x multiplier is baked into these image samples.
    if re.search(
        r"cliff|clifwall|wallface|^txwall0[16]$|mesa|mount|rockmono|rocktrim|rockcliff", name
    ):
        return dict(
            kind="rock", size=512, macro=0.85, meso=0.55, micro=0.15, slope=0.65, repeat=True
        )
    if "vehicle_all_materials" in reasons:
        return dict(
            kind="vehicle", size=512, macro=0.12, meso=0.45, micro=0.25, slope=0.28, repeat=False
        )
    if re.search(r"gter|grass|sand|mud|dirt|gravel|beach|und.?wat|lava", name):
        return dict(
            kind="ground", size=256, macro=0.30, meso=0.55, micro=0.25, slope=0.40, repeat=True
        )
    return dict(
        kind="structure", size=256, macro=0.10, meso=0.45, micro=0.20, slope=0.25, repeat=False
    )


def relief(rgb, settings):
    """Return a normal-map tuple and editable 16-bit color-derived height array.

    Resize without upscaling, separate luminance into three spatial bands, and
    combine them using the selected profile. Repeating surfaces wrap; other
    atlases clamp and receive flat normal borders. Height is a draft estimate.
    """
    rgb = rgb.convert("RGB")
    ratio = min(1.0, settings["size"] / max(rgb.size))
    size = tuple(max(1, round(x * ratio)) for x in rgb.size)
    color = np.asarray(rgb.resize(size, Image.Resampling.LANCZOS), dtype=np.float32) / 255.0
    luminance = color @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)

    def blur(radius):
        # Extended borders keep clamped atlases from wrapping unrelated panels.
        pad = max(2, int(radius * 3))
        padded = np.pad(luminance, pad, mode="wrap" if settings["repeat"] else "edge")
        image = Image.fromarray(np.rint(padded * 255).astype("uint8")).filter(
            ImageFilter.GaussianBlur(radius)
        )
        return np.asarray(image, dtype=np.float32)[pad:-pad, pad:-pad] / 255.0

    fine, medium, broad, illumination = [blur(x) for x in (0.7, 2.5, 10.0, 36.0)]
    height = (
        (broad - illumination) * settings["macro"]
        + (medium - broad) * settings["meso"]
        + (fine - medium) * settings["micro"]
    )
    # Chroma-only painted markings should not become deep grooves. This mask is
    # a conservative draft aid; masks still require material-specific review.
    if settings["kind"] in ("vehicle", "structure"):
        chroma = color.max(axis=2) - color.min(axis=2)
        height *= np.clip(1.0 - chroma * 0.7, 0.3, 1.0)
    if settings["repeat"]:
        dx = (np.roll(height, -1, 1) - np.roll(height, 1, 1)) * 0.5
        dy = (np.roll(height, -1, 0) - np.roll(height, 1, 0)) * 0.5
    else:
        dy, dx = np.gradient(height)
    # Normalize across the whole tile, retaining relative macro/micro relief.
    unscaled_slopes = np.sqrt(dx * dx + dy * dy)
    # One gain brings the 95th-percentile slope toward the profile target.
    # The later per-pixel cap bounds outliers at 1.5 times that target.
    gain = min(
        256.0 if settings["kind"] == "rock" else 32.0,
        settings["slope"] / max(float(np.percentile(unscaled_slopes, 95)), 1e-6),
    )
    dx *= gain
    dy *= gain
    scaled_slopes = np.sqrt(dx * dx + dy * dy)
    slope_scale = np.minimum(1.0, settings["slope"] * 1.5 / np.maximum(scaled_slopes, 1e-6))
    unit_normals = np.stack((-dx * slope_scale, -dy * slope_scale, np.ones_like(dx)), axis=-1)
    unit_normals /= np.linalg.norm(unit_normals, axis=-1, keepdims=True)
    rgba = np.empty((*height.shape, 4), dtype="uint8")
    rgba[:, :, :3] = np.rint((unit_normals * 0.5 + 0.5) * 255).astype("uint8")
    rgba[:, :, 3] = 255
    if not settings["repeat"]:
        rgba[:2, :, :3] = rgba[-2:, :, :3] = [128, 128, 255]
        rgba[:, :2, :3] = rgba[:, -2:, :3] = [128, 128, 255]
    editable = np.rint(np.clip(0.5 + height, 0, 1) * 65535).astype("uint16")
    return (*size, rgba.tobytes()), editable


def prepare(priorities, base, output, hash_library):
    """Build a fresh draft catalog from priority names and registered bank pixels.

    Base-page bindings and receipt registrations must have the same key order.
    Selected aliases share one generated normal per source/profile kind; other
    bindings retain their previous normal data. Missing priority names are
    reported as unavailable rather than fabricated. Outputs remain local drafts.
    """
    if output.exists():
        raise ValueError("Preserve previous candidates: select a fresh output")
    ranks = json.loads(priorities.read_text())
    receipt = json.loads((base / "receipt.json").read_text())
    choices = {x["name"]: x for x in ranks["authoring_queue"]}
    output.mkdir(parents=True)
    (output / "editable").mkdir()
    digest = accelerated_hash(hash_library)
    catalog.pixel_hash = digest
    pins = {}
    for bank in receipt["banks"]:
        path = Path(bank["path"])
        actual = sha(path)
        if actual != bank["sha256"]:
            raise ValueError("Upgraded source bank changed: " + str(path))
        pins[str(path)] = actual
    reports = []
    pages = []
    batch = []
    batch_bytes = 0
    cache = {}
    found = set()
    total = 0

    def flush():
        """Write one pending page and reset its binding and pixel-byte counters."""
        nonlocal batch, batch_bytes, total
        if not batch:
            return
        data = catalog.pack_surface_bindings(batch)
        if len(data) > 16 * 1024 * 1024:
            raise ValueError("Page exceeds runtime byte budget")
        name = f"page-{len(pages):03d}.bin"
        (output / name).write_bytes(data)
        pages.append(
            dict(name=name, sha256=sha(output / name), bindings=len(batch), bytes=len(data))
        )
        total += len(data)
        batch = []
        batch_bytes = 0

    registrations = receipt["registrations"]
    at = 0
    for old_page in receipt["pages"]:
        path = base / old_page["name"]
        if sha(path) != old_page["sha256"]:
            raise ValueError("Baseline page changed")
        for key, normal in catalog.read_surface_bindings(path.read_bytes()):
            entry = registrations[at]
            at += 1
            if list(key) != entry["key"]:
                raise ValueError("Registration/page order mismatch")
            names = sorted({a["name"].lower() for a in entry["aliases"]})
            selected = [n for n in names if n in choices]
            selected = [n for n in selected if n not in ranks["dedicated_water_exclusions"]]
            if selected:
                # A shared colour identity needs one interpretation. Prefer a
                # vehicle alias as the profile name; profile() still applies its
                # rock-name rule before the vehicle-membership rule.
                reasons = {r for n in selected for r in choices[n]["reasons"]}
                name = next(
                    (n for n in selected if "vehicle_all_materials" in choices[n]["reasons"]),
                    selected[0],
                )
                settings = profile(name, reasons)
                source = entry["aliases"][0]
                identity = (source["bank"], source["offset"], settings["kind"])
                if identity not in cache:
                    bank = Path(receipt["banks"][source["bank"]]["path"])
                    w, h = key[:2]
                    with bank.open("rb") as stream:
                        stream.seek(source["offset"])
                        flags, bw, bh, reserved, palette, stretch = struct.unpack(
                            "<IHHIHH", stream.read(16)
                        )
                        if (
                            (bw, bh) != (w, h)
                            or flags not in (5, 0x25, 11, 0x2B)
                            or reserved
                            or palette
                        ):
                            raise ValueError("Unsupported upgraded colour descriptor")
                        words = (
                            np.frombuffer(stream.read(w * h * 2), dtype="<u2")
                            .reshape(h, w)
                            .astype("uint32")
                        )
                    rgb = np.stack(
                        (
                            (words >> 11) * 255 // 31,
                            ((words >> 5) & 63) * 255 // 63,
                            (words & 31) * 255 // 31,
                        ),
                        axis=-1,
                    ).astype("uint8")
                    normal, height = relief(Image.fromarray(rgb), settings)
                    stem = f"{name}-{at:04d}"
                    Image.fromarray(height).save(output / "editable" / (stem + "-height.png"))
                    Image.frombytes("RGBA", normal[:2], normal[2]).save(
                        output / "editable" / (stem + "-normal.png")
                    )
                    cache[identity] = (normal, stem)
                normal, stem = cache[identity]
                found.update(selected)
                reports.append(
                    dict(
                        key=key,
                        names=names,
                        settings=settings,
                        editable=stem,
                        normal_sha256=hashlib.sha256(normal[2]).hexdigest(),
                        normal_size=normal[:2],
                    )
                )
            # This conservative batching estimate counts repeated pixel data.
            # flush() separately checks the actual encoded page byte limit.
            size = len(normal[2]) if normal else 0
            if len(batch) >= 64 or batch_bytes + size > 8 * 1024 * 1024:
                flush()
            batch.append((key, normal))
            batch_bytes += size
        print("Read", old_page["name"], "draft bindings", len(reports), flush=True)
    flush()
    if total > 512 * 1024 * 1024 or len(pages) > 256:
        raise ValueError(
            f"Candidate exceeds installed world budget: {total} bytes / {len(pages)} pages; no manifest published"
        )
    for bank, pin in pins.items():
        if sha(bank) != pin:
            raise ValueError("Upgraded bank changed during generation")
    report = dict(
        schema_version=1,
        status="material-specific colour-derived drafts; individual art review required",
        preparer_sha256=sha(Path(__file__)),
        priorities_sha256=sha(priorities),
        baseline_receipt_sha256=sha(base / "receipt.json"),
        banks=pins,
        pages=pages,
        bytes=total,
        upgraded_bindings=len(reports),
        upgraded_names=len(found),
        selected_names=len(choices),
        unavailable_names=sorted(set(choices) - found),
        edits=reports,
        method="Separate broad/medium/fine relief bands; material-specific slope and atlas borders; upgraded colour only; no global-strength baking",
        dependencies=dict(numpy=np.__version__),
    )
    (output / "receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    (output / "world-normals.txt").write_text(
        "MW34SNP1\n" + "\n".join(p["name"] for p in pages) + "\n"
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("priorities", "base", "output", "hash-library"):
        parser.add_argument("--" + key, type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.priorities, args.base, args.output, args.hash_library)
    print(
        json.dumps(
            {
                k: result[k]
                for k in ("bytes", "upgraded_bindings", "upgraded_names", "unavailable_names")
            },
            indent=2,
        )
    )
