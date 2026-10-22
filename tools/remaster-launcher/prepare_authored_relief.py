"""Replace explicit world keys with normal data derived from reviewed height inputs.

Original/upgraded colour banks remain read-only. AI-assisted height candidates
must pass per-variant UV review; correlation is a screening aid, not art approval.
"""

from pathlib import Path
import argparse
import hashlib
import json
import shutil
import struct
import numpy as np
from PIL import Image, ImageFilter
import normal_materials as catalog
from prepare_world_normals import accelerated_hash


def sha(path):
    """Stream an input or output file's SHA-256 without loading its full contents."""
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def periodic_height(value):
    """Subtract the smooth boundary mismatch from a 2-D floating height field.

    Opposite-edge differences supply a discrete Poisson solve in Fourier space.
    The zero-frequency component is forced to zero, preserving the input mean.
    This reduces wrap seams without removing broad interior height features.
    """
    h, w = value.shape
    border = np.zeros_like(value)
    border[0] = value[-1] - value[0]
    border[-1] = -border[0]
    column_mismatch = value[:, -1] - value[:, 0]
    border[:, 0] += column_mismatch
    border[:, -1] -= column_mismatch
    laplacian_eigenvalues = (
        2 * np.cos(2 * np.pi * np.arange(w) / w)[None, :]
        + 2 * np.cos(2 * np.pi * np.arange(h) / h)[:, None]
        - 4
    )
    laplacian_eigenvalues[0, 0] = 1
    smooth_spectrum = np.fft.fft2(border) / laplacian_eigenvalues
    smooth_spectrum[0, 0] = 0
    return value - np.fft.ifft2(smooth_spectrum).real


def normals_from_height(image, size, depth_ratio, slope_limit, *, repeat=True):
    """Return (width, height, RGBA bytes) and slope statistics from grayscale height.

    Heights are filtered after resizing. Repeating surfaces use a corrected
    periodic field and wrapped central differences; other surfaces use ordinary
    gradients. Scale derivatives by image dimensions and depth_ratio, cap their
    combined slope, then encode negative stored-U/V derivatives as unit normals.
    """
    image = image.convert("L").resize(size, Image.Resampling.LANCZOS)
    height_field = np.asarray(image.filter(ImageFilter.GaussianBlur(1.2)), dtype=np.float64) / 255.0
    if repeat:
        height_field = periodic_height(height_field)
        dx = (np.roll(height_field, -1, 1) - np.roll(height_field, 1, 1)) * 0.5
        dy = (np.roll(height_field, -1, 0) - np.roll(height_field, 1, 0)) * 0.5
    else:
        dy, dx = np.gradient(height_field)
    dx *= size[0] * depth_ratio
    dy *= size[1] * depth_ratio
    slopes = np.sqrt(dx * dx + dy * dy)
    slope_scale = np.minimum(1.0, slope_limit / np.maximum(slopes, 1e-12))
    unit_normals = np.stack((-dx * slope_scale, -dy * slope_scale, np.ones_like(dx)), axis=-1)
    unit_normals /= np.linalg.norm(unit_normals, axis=-1, keepdims=True)
    rgba = np.empty((*height_field.shape, 4), dtype="uint8")
    rgba[:, :, :3] = np.rint(np.clip(unit_normals * 0.5 + 0.5, 0, 1) * 255).astype("uint8")
    rgba[:, :, 3] = 255
    stats = dict(
        median_slope=float(np.median(slopes * slope_scale)),
        p95_slope=float(np.percentile(slopes * slope_scale, 95)),
        max_slope=float((slopes * slope_scale).max()),
        clipped_fraction=float(np.mean(slopes > slope_limit)),
    )
    return (*size, rgba.tobytes()), stats


def alignment(colour, height):
    """Screen color/height alignment using a fixed 256-square comparison grid.

    Compare blurred luminance over the interior at shifts of -8 to +8 pixels
    in four-pixel steps. Return zero-shift correlation and the greatest
    (correlation, x shift, y shift) tuple. Correlation is a review aid, not proof
    of UV correctness; a constant comparison is rejected rather than scored.
    """
    size = (256, 256)
    colour_luminance = np.asarray(
        colour.convert("L").resize(size).filter(ImageFilter.GaussianBlur(2)), dtype=float
    )
    height_luminance = np.asarray(
        height.convert("L").resize(size).filter(ImageFilter.GaussianBlur(2)), dtype=float
    )
    interior = colour_luminance[12:-12, 12:-12].ravel()
    scores = []
    for y in (-8, -4, 0, 4, 8):
        for x in (-8, -4, 0, 4, 8):
            shifted = np.roll(height_luminance, (y, x), (0, 1))[12:-12, 12:-12].ravel()
            score = float(np.corrcoef(interior, shifted)[0, 1])
            if not np.isfinite(score):
                raise ValueError("Height/colour alignment has no variation")
            scores.append((score, x, y))
    return dict(zero=next(s[0] for s in scores if s[1:] == (0, 0)), best=max(scores))


def prepare(config_path, output, hash_library):
    """Replace selected normal bindings in a fresh local catalog candidate.

    Receipts pin the source catalog and base pages. Shared pixel aliases must
    select at most one recipe; each selected recipe must match a surface and
    pass alignment/slope screening. Untouched pages are copied byte for byte.
    The final manifest is written after the pages and receipt; failure can leave
    partial output. Reusing an output directory is deliberately rejected.
    """
    if output.exists():
        raise ValueError("Choose a fresh output")
    config = json.loads(config_path.read_text())
    base = Path(config["base"])
    receipt_path = base / "receipt.json"
    if sha(receipt_path) != config["base_receipt_sha256"]:
        raise ValueError("Base candidate changed")
    source = json.loads(Path(config["source_receipt"]).read_text())
    if sha(config["source_receipt"]) != config["source_receipt_sha256"]:
        raise ValueError("Source catalog changed")
    base_receipt = json.loads(receipt_path.read_text())
    edits = {tuple(e["key"]): e for e in source["registrations"]}
    # This script selects the process-wide catalog hash implementation. The
    # caller supplies a trusted local library, checked against reference vectors.
    catalog.pixel_hash = accelerated_hash(hash_library)
    recipes = {e["name"]: e for e in config["materials"]}
    loaded = {}
    pins = {}
    reports = []
    pages = []
    for name, spec in recipes.items():
        path = Path(spec["height"])
        if sha(path) != spec["height_sha256"]:
            raise ValueError("Authored height changed")
        with Image.open(path) as image:
            loaded[name] = image.convert("L").copy()
    output.mkdir(parents=True)
    (output / "normals").mkdir()
    for page in base_receipt["pages"]:
        path = base / page["name"]
        if sha(path) != page["sha256"]:
            raise ValueError("Base page changed")
        entries = catalog.read_surface_bindings(path.read_bytes())
        changed = False
        result = []
        for key, normal in entries:
            original = edits[key]
            names = {a["name"].lower() for a in original["aliases"]}
            selected = names.intersection(recipes)
            if len(selected) > 1:
                raise ValueError("Conflicting height recipes for shared pixels")
            if selected:
                name = selected.pop()
                spec = recipes[name]
                alias = original["aliases"][0]
                bank = Path(source["banks"][alias["bank"]]["path"])
                if str(bank) not in pins:
                    pins[str(bank)] = sha(bank)
                    if pins[str(bank)] != source["banks"][alias["bank"]]["sha256"]:
                        raise ValueError("Upgraded colour bank changed")
                with bank.open("rb") as stream:
                    stream.seek(alias["offset"])
                    flags, w, h, reserved, palette, stretch = struct.unpack(
                        "<IHHIHH", stream.read(16)
                    )
                    raw = stream.read(w * h * 2)
                if (w, h) != key[:2] or flags not in (5, 37) or reserved or palette:
                    raise ValueError("Unsupported selected colour format")
                words = np.frombuffer(raw, dtype="<u2").reshape(h, w).astype("uint32")
                rgb = np.stack(
                    (
                        (words >> 11) * 255 // 31,
                        ((words >> 5) & 63) * 255 // 63,
                        (words & 31) * 255 // 31,
                    ),
                    axis=-1,
                ).astype("uint8")
                review = alignment(Image.fromarray(rgb), loaded[name])
                if review["zero"] < spec["minimum_correlation"] or review["best"][1:] != (0, 0):
                    raise ValueError(
                        "Variant requires separate UV authoring review: " + str((name, key, review))
                    )
                ratio = min(1.0, spec["longest_side"] / max(w, h))
                size = (round(w * ratio), round(h * ratio))
                # Recipes are tiled by default. Keep height filtering and normal
                # orientation consistent across every pixel variant of a recipe.
                normal, stats = normals_from_height(
                    loaded[name], size, spec["depth_ratio"], spec["slope_limit"]
                )
                if stats["clipped_fraction"] > spec.get("maximum_clipped_fraction", 0.05):
                    raise ValueError(
                        "Authored height gain flattens excessive slopes at the cap; recalibrate "
                        + name
                    )
                filename = f"{name}-{key[3]:016x}.png"
                Image.frombytes("RGBA", size, normal[2]).save(output / "normals" / filename)
                reports.append(
                    dict(
                        name=name,
                        key=key,
                        normal_size=size,
                        height_sha256=spec["height_sha256"],
                        alignment=review,
                        normal_sha256=hashlib.sha256(normal[2]).hexdigest(),
                        stats=stats,
                    )
                )
                changed = True
            result.append((key, normal))
        target = output / page["name"]
        if changed:
            target.write_bytes(catalog.pack_surface_bindings(result))
        else:
            shutil.copyfile(path, target)
        if target.stat().st_size > 16 * 1024 * 1024:
            raise ValueError("Edited page exceeds byte limit")
        pages.append(
            dict(
                name=target.name,
                sha256=sha(target),
                bytes=target.stat().st_size,
                bindings=len(result),
            )
        )
    if sum(x["bytes"] for x in pages) > 512 * 1024 * 1024:
        raise ValueError("Edited package exceeds existing byte budget")
    if set(e["name"] for e in reports) != set(recipes):
        raise ValueError("A selected height never matched a surface")
    for path, pin in pins.items():
        if sha(path) != pin:
            raise ValueError("Colour bank changed during preparation")
    receipt = dict(
        status="AI-assisted authored height candidate; native/art review required",
        config_sha256=sha(config_path),
        source_pins=pins,
        height_inputs=config["materials"],
        pages=pages,
        bytes=sum(x["bytes"] for x in pages),
        edits=reports,
        unchanged_keys_preserved=True,
        normal_y="negative stored-V height derivative",
        boundary_method="periodic-plus-smooth height decomposition",
        strength_baked=False,
    )
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    (output / "world-normals.txt").write_text(
        "MW34SNP1\n" + "\n".join(p["name"] for p in pages) + "\n"
    )
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("config", "output", "hash-library"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    r = prepare(args.config, args.output, args.hash_library)
    print(json.dumps(dict(edited_bindings=len(r["edits"]), bytes=r["bytes"]), indent=2))
