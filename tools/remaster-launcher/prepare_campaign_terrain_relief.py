"""Refine explicitly selected upgraded campaign surfaces; preserve other bindings.

AI height inputs require per-variant alignment screening. Analytic recipes are
color-derived technical drafts, not recovered physical height or new albedo.
"""

from pathlib import Path
import argparse
import json
import shutil
import struct
import numpy as np
from PIL import Image, ImageFilter
import normal_materials as catalog
from prepare_authored_relief import alignment, normals_from_height, sha
from prepare_world_normals import accelerated_hash
from feature_relief import feature_relief


def atlas_relief(image, recipe):
    """Return normals, grayscale height preview and statistics for isolated panels.

    Panel rectangles use normalized coordinates with exclusive right/bottom
    edges after rounding to pixel bounds. Reject overlap and panels below eight
    pixels per side. Unselected regions and each panel's two-pixel guard stay flat.
    """
    image_width, image_height = image.size
    rgba = np.full((image_height, image_width, 4), [128, 128, 255, 255], dtype="uint8")
    height = Image.new("L", (image_width, image_height), 128)
    occupied = np.zeros((image_height, image_width), dtype=bool)
    reports = []
    for panel_bounds in recipe["panels"]:
        if len(panel_bounds) != 4 or not all(0 <= v <= 1 for v in panel_bounds):
            raise ValueError("Atlas panel outside normalized texture bounds")
        x0, y0, x1, y1 = [
            round(v * s)
            for v, s in zip(panel_bounds, (image_width, image_height, image_width, image_height))
        ]
        if x1 - x0 < 8 or y1 - y0 < 8 or occupied[y0:y1, x0:x1].any():
            raise ValueError("Atlas panels overlap or are too small")
        occupied[y0:y1, x0:x1] = True
        panel = image.crop((x0, y0, x1, y1)).convert("L")
        # Local shallow grain only: painted panels/window shades are not bulges.
        fine = np.asarray(panel.filter(ImageFilter.GaussianBlur(0.6)), dtype=float)
        broad = np.asarray(panel.filter(ImageFilter.GaussianBlur(2.0)), dtype=float)
        values = np.rint(np.clip(128 + (fine - broad) * 0.35, 0, 255)).astype("uint8")
        relief = Image.fromarray(values)
        normal, stats = normals_from_height(
            relief, panel.size, recipe["depth_ratio"], recipe["slope_limit"], repeat=False
        )
        panel_pixels = np.frombuffer(normal[2], dtype="uint8").reshape(y1 - y0, x1 - x0, 4).copy()
        panel_pixels[:2, :, :3] = panel_pixels[-2:, :, :3] = [128, 128, 255]
        panel_pixels[:, :2, :3] = panel_pixels[:, -2:, :3] = [128, 128, 255]
        rgba[y0:y1, x0:x1] = panel_pixels
        height.paste(relief, (x0, y0))
        reports.append(stats)
    if not reports:
        raise ValueError("No atlas panels selected")
    return (
        (image_width, image_height, rgba.tobytes()),
        height,
        dict(
            panels=reports,
            clipped_fraction=max(s["clipped_fraction"] for s in reports),
            excluded_pixels=int((~occupied).sum()),
        ),
    )


def analytic_height(image, kind):
    """Estimate an 8-bit height draft from filtered color luminance bands.

    Cliff recipes remove column lighting bias before filtering; transition
    recipes suppress broad painted color changes. Filters wrap with padding,
    and the neutral output height is centered at 0.5. This is not measured relief.
    """
    luminance = np.asarray(image.convert("L"), dtype=float) / 255.0
    # Remove the persistent left/right cliff lighting bias before interpreting
    # horizontal ledges. This remains an estimate from upgraded color artwork.
    if kind == "cliff":
        luminance -= luminance.mean(axis=0, keepdims=True) - luminance.mean()

    def blur(radius):
        # Extended borders avoid introducing wraparound detail during filtering.
        pad = max(4, int(radius * 3))
        padded = np.pad(luminance, pad, mode="wrap")
        filtered = Image.fromarray(np.rint(np.clip(padded, 0, 1) * 255).astype("uint8"))
        return (
            np.asarray(filtered.filter(ImageFilter.GaussianBlur(radius)), dtype=float)[
                pad:-pad, pad:-pad
            ]
            / 255.0
        )

    fine, medium, broad = [blur(x) for x in (0.7, 3.0, 24.0)]
    if kind == "cliff":
        height_field = 0.75 * (medium - broad) + 0.25 * (fine - medium)
    elif kind == "transition":
        # Do not turn the large painted sand-color transition into a height step.
        height_field = 0.10 * (medium - broad) + 0.65 * (fine - medium)
    else:
        height_field = 0.12 * (medium - broad) + 0.70 * (fine - medium)
    return Image.fromarray(np.rint(np.clip(0.5 + height_field, 0, 1) * 255).astype("uint8"))


def prepare(config_path, output, hash_library):
    """Refine selected C1 bank aliases and preserve all other world bindings.

    An optional per-recipe key list narrows name matching. The first eligible
    alias selects a recipe. Feature coordinates, panel grain, reviewed height
    images and analytic drafts have distinct preparation paths. Pinned source
    pixels, alignment checks and output readback guard this local candidate;
    the final manifest is published only after package checks complete.
    """
    if output.exists():
        raise ValueError("Preserve previous output: choose a fresh directory")
    config = json.loads(config_path.read_text())
    digest = accelerated_hash(hash_library)
    catalog.pixel_hash = digest
    source_path = Path(config["source_receipt"])
    if sha(source_path) != config["source_receipt_sha256"]:
        raise ValueError("Source registration changed")
    source = json.loads(source_path.read_text())
    manifest = Path(config["base_manifest"])
    if sha(manifest) != config["base_manifest_sha256"]:
        raise ValueError("Base manifest changed")
    registrations = {tuple(x["key"]): x for x in source["registrations"]}
    recipes = config["materials"]
    selected = {}
    pins = {}
    reports = []
    pages = []
    for key, entry in registrations.items():
        choices = [
            (a, recipes[a["name"].lower()])
            for a in entry["aliases"]
            if a["name"].lower() in recipes
            and Path(source["banks"][a["bank"]]["path"]).name.startswith("c1-")
            and (
                "keys" not in recipes[a["name"].lower()]
                or list(key) in recipes[a["name"].lower()]["keys"]
            )
        ]
        if choices:
            selected[key] = choices[0]
    output.mkdir(parents=True)
    (output / "editable").mkdir()
    seen = set()
    changed_keys = set()
    retained_bindings = 0
    lines = manifest.read_text().splitlines()
    if not lines or lines[0] != "MW34SNP1":
        raise ValueError("Unsupported world manifest")
    for filename in lines[1:]:
        if not filename:
            continue
        path = manifest.parent / filename
        source_page_sha256 = sha(path)
        page_bindings = []
        changed = False
        for key, normal in catalog.read_surface_bindings(path.read_bytes()):
            if key in seen:
                raise ValueError("Duplicate world identity")
            seen.add(key)
            if key not in selected:
                page_bindings.append((key, normal))
                retained_bindings += 1
                continue
            alias, recipe = selected[key]
            name = alias["name"].lower()
            bank = Path(source["banks"][alias["bank"]]["path"])
            if str(bank) not in pins:
                pins[str(bank)] = sha(bank)
                if pins[str(bank)] != source["banks"][alias["bank"]]["sha256"]:
                    raise ValueError("Upgraded source bank changed")
            with bank.open("rb") as stream:
                stream.seek(alias["offset"])
                flags, source_width, source_height, reserved, palette, stretch = struct.unpack(
                    "<IHHIHH", stream.read(16)
                )
                colour_bytes = stream.read(source_width * source_height * 2)
            if (
                flags not in (5, 37)
                or reserved
                or palette
                or (source_width, source_height, 1, digest(colour_bytes)) != key
            ):
                raise ValueError("Complete source identity mismatch")
            words = (
                np.frombuffer(colour_bytes, dtype="<u2")
                .reshape(source_height, source_width)
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
            image = Image.fromarray(rgb)
            ratio = min(1.0, recipe["longest_side"] / max(source_width, source_height))
            size = (round(source_width * ratio), round(source_height * ratio))
            review = None
            if "features" in recipe:
                reference = Path(recipe["layout_reference"])
                if sha(reference) != recipe["layout_reference_sha256"]:
                    raise ValueError("Authored feature layout reference changed")
                review = alignment(image, Image.open(reference))
                if review["zero"] < 0.88 or review["best"][1:] != (0, 0):
                    raise ValueError(
                        "Feature layout requires separate variant review: "
                        + str((name, key, review))
                    )
                normal, height, stats = feature_relief(
                    image.resize(size, Image.Resampling.LANCZOS), recipe
                )
            elif recipe.get("panels"):
                normal, height, stats = atlas_relief(
                    image.resize(size, Image.Resampling.LANCZOS), recipe
                )
            elif recipe.get("height"):
                height_path = Path(recipe["height"])
                if sha(height_path) != recipe["height_sha256"]:
                    raise ValueError("Reviewed height changed")
                height = Image.open(height_path).convert("L")
                review = alignment(image, height)
                if review["zero"] < 0.88 or review["best"][1:] != (0, 0):
                    raise ValueError(
                        "Height requires separate alignment review: " + str((name, key, review))
                    )
            else:
                height = analytic_height(
                    image.resize(size, Image.Resampling.LANCZOS), recipe["kind"]
                )
            if not recipe.get("panels") and "features" not in recipe:
                normal, stats = normals_from_height(
                    height, size, recipe["depth_ratio"], recipe["slope_limit"]
                )
            if stats["clipped_fraction"] > 0.05:
                raise ValueError("Excess clipped relief; recalibrate " + name)
            stem = f"{name}-{key[3]:016x}"
            height.save(output / "editable" / (stem + "-height.png"))
            Image.frombytes("RGBA", size, normal[2]).save(
                output / "editable" / (stem + "-normal.png")
            )
            page_bindings.append((key, normal))
            changed = True
            changed_keys.add(key)
            reports.append(
                dict(
                    name=name,
                    key=key,
                    recipe=recipe,
                    normal_size=size,
                    alignment=review,
                    stats=stats,
                )
            )
        target = output / filename
        if changed:

            def write_page(entries, name):
                """Recursively split an oversized changed page, then verify readback.

                Preserve entry order across the -a/-b children. A single binding
                that cannot fit is rejected; runtime page limits are not raised.
                """
                data = catalog.pack_surface_bindings(entries)
                if len(data) > 16 * 1024 * 1024:
                    if len(entries) < 2:
                        raise ValueError("A single normal binding exceeds page budget")
                    mid = len(entries) // 2
                    stem = Path(name).stem
                    write_page(entries[:mid], stem + "-a.bin")
                    write_page(entries[mid:], stem + "-b.bin")
                    return
                path_out = output / name
                path_out.write_bytes(data)
                if catalog.read_surface_bindings(data) != entries:
                    raise ValueError("Output roundtrip changed a binding")
                pages.append(dict(name=name, sha256=sha(path_out), bytes=len(data)))

            write_page(page_bindings, filename)
        else:
            shutil.copyfile(path, target)
            if catalog.read_surface_bindings(target.read_bytes()) != page_bindings:
                raise ValueError("Output roundtrip changed a binding")
            pages.append(dict(name=filename, sha256=sha(target), bytes=target.stat().st_size))
        if sha(path) != source_page_sha256:
            raise ValueError("Page source changed during preparation")
    if changed_keys != selected.keys() or {x["name"] for x in reports} != set(recipes):
        raise ValueError("Selected source identity absent from current manifest")
    package_bytes = sum(x["bytes"] for x in pages)
    if package_bytes > 512 * 1024 * 1024 or len(pages) > 256:
        raise ValueError("World package exceeds existing byte budget")
    for path, pin in pins.items():
        if sha(Path(path)) != pin:
            raise ValueError("Source bank changed during authoring")
    receipt = dict(
        status="Mixed AI-height candidate and material-specific analytic drafts; native art review required",
        config_sha256=sha(config_path),
        base_manifest=str(manifest),
        base_manifest_sha256=sha(manifest),
        source_pins=pins,
        pages=pages,
        bytes=package_bytes,
        bindings=len(seen),
        retained_bindings=retained_bindings,
        edits=reports,
        strength_baked=False,
        albedo_unchanged=True,
    )
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    (output / "world-normals.txt").write_text(
        "MW34SNP1\n" + "\n".join(x["name"] for x in pages) + "\n"
    )
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("config", "output", "hash-library"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.config, args.output, args.hash_library)
    print(
        json.dumps(
            dict(
                bytes=result["bytes"],
                edited_bindings=len(result["edits"]),
                retained_bindings=result["retained_bindings"],
            )
        )
    )
