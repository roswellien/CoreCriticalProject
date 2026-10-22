"""Refine pinned upgraded campaign materials with explicit UV/material recipes.

Preserves other world bindings and reviewed earlier work. Grain estimates remain
estimates; only explicit feature coordinates author structural height. Coverage
and paint masks prevent transparency/reflections from becoming raised detail.
"""

from pathlib import Path
import argparse
import json
import hashlib

import numpy as np
from PIL import Image, ImageFilter

import normal_materials as catalog
from campaign_material_source import read_variant
from feature_relief import feature_relief
from prepare_authored_relief import sha
from prepare_world_normals import accelerated_hash
from repack_world_normals import pages_for, PAGE_BYTES, PACKAGE_BYTES


def prepare(config_path, output, hash_library):
    """Refine explicitly selected source variants in a fresh local world catalog.

    Require pinned inventory, manifest and variant review inputs. Preserve flat
    exclusions and previously reviewed bindings; structural features additionally
    require coarse-layout approval or an explicit per-key manual review. Repack
    pages and verify decoded bindings before writing the final manifest.
    """
    if output.exists():
        raise ValueError("Choose a fresh candidate output")
    config = json.loads(config_path.read_text())
    source_path = Path(config["source_inventory"])
    if sha(source_path) != config["source_inventory_sha256"]:
        raise ValueError("Source inventory changed")
    source = json.loads(source_path.read_text())
    recipes = config["materials"]
    pixel_digest = accelerated_hash(hash_library)
    catalog.pixel_hash = pixel_digest
    for bank, pin in source["source_bank_pins"].items():
        if sha(bank) != pin:
            raise ValueError("Upgraded source bank changed")
    manifest = Path(config["base_manifest"])
    if sha(manifest) != config["base_manifest_sha256"]:
        raise ValueError("Base normal manifest changed")
    lines = manifest.read_text().splitlines()
    if lines[0] != "MW34SNP1":
        raise ValueError("Unsupported base catalog")
    base_bindings = {}
    pins = {}
    for name in filter(None, lines[1:]):
        path = manifest.parent / name
        pins[str(path)] = sha(path)
        for key, normal in catalog.read_surface_bindings(path.read_bytes()):
            if key in base_bindings:
                raise ValueError("Ambiguous base identity")
            base_bindings[key] = normal
    selected = {}
    preserved = set()
    for name, recipe in recipes.items():
        for variant in source["sources"][name]["variants"]:
            key = tuple(variant["key"])
            if key not in base_bindings:
                raise ValueError("Campaign source absent from world catalog")
            if recipe.get("preserve_previous"):
                preserved.add(key)
                continue
            if key in selected and selected[key][0] != name:
                raise ValueError("Conflicting material recipes for shared pixels")
            selected[key] = (name, variant)
    review_path = Path(config["variant_review"])
    if sha(review_path) != config["variant_review_sha256"]:
        raise ValueError("Variant review changed")
    reviews = {tuple(row["key"]): row for row in json.loads(review_path.read_text())["rows"]}
    output.mkdir(parents=True)
    (output / "editable").mkdir()
    updated_bindings = dict(base_bindings)
    edits = []
    for key, (name, variant) in selected.items():
        recipe = dict(recipes[name])
        if base_bindings[key] is None:
            continue  # An explicit flat exclusion remains authoritative.
        if (
            recipe["features"]
            and not reviews[key]["coarse_layout_pass"]
            and list(key) not in recipe.get("manually_reviewed_keys", [])
        ):
            raise ValueError("UV structure needs separate variant review: " + name)
        image, alpha = read_variant(variant, pixel_digest)
        size = base_bindings[key][:2]
        longest = recipe.get("minimum_longest_side", 0)
        if max(size) < longest:
            ratio = min(longest, max(image.size)) / max(size)
            size = (max(8, round(size[0] * ratio)), max(8, round(size[1] * ratio)))
        image = image.resize(size, Image.Resampling.LANCZOS)
        rgb = np.asarray(image, dtype=float) / 255.0
        # Grain permission affects color-derived microdetail only. Coverage
        # exclusions also flatten final normals after structural features run.
        grain_allowed = np.ones((size[1], size[0]), dtype=bool)
        if recipe["material"] == "metal":
            # Suppress only shallow color grain in strongly painted/emissive
            # regions. Authored frame/seam geometry remains independent of hue.
            saturation = (rgb.max(axis=-1) - rgb.min(axis=-1)) / np.maximum(rgb.max(axis=-1), 0.001)
            paint = Image.fromarray((saturation > 0.45).astype("uint8") * 255).filter(
                ImageFilter.MaxFilter(7)
            )
            grain_allowed &= np.asarray(paint) == 0
        invisible = np.zeros_like(grain_allowed)
        if alpha is not None:
            coverage = np.asarray(alpha.resize(size, Image.Resampling.NEAREST))
            invisible = (
                np.asarray(
                    Image.fromarray((coverage < 128).astype("uint8") * 255).filter(
                        ImageFilter.MaxFilter(5)
                    )
                )
                > 0
            )
            grain_allowed &= ~invisible
        # Calibrate a private recipe copy so one difficult variant cannot reduce
        # the configured depth for every later variant in the material family.
        for attempt in range(12):
            normal, height, stats = feature_relief(image, recipe, grain_mask=grain_allowed)
            if stats["clipped_fraction"] <= 0.05:
                break
            recipe["depth_ratio"] *= 0.8
        else:
            raise ValueError("Excessive clipped relief: " + name)
        pixels = np.frombuffer(normal[2], dtype="uint8").reshape(size[1], size[0], 4).copy()
        pixels[invisible, :3] = [128, 128, 255]
        normal = (*size, pixels.tobytes())
        stem = f"{name}-{key[3]:016x}-{key[2]}"
        height.save(output / "editable" / (stem + "-height.png"))
        Image.frombytes("RGBA", size, normal[2]).save(output / "editable" / (stem + "-normal.png"))
        updated_bindings[key] = normal
        edits.append(
            dict(
                name=name,
                key=key,
                method=recipe["method"],
                size=size,
                structural_features=len(recipe["features"]),
                stats=stats,
                depth_ratio=recipe["depth_ratio"],
                coverage_guard_pixels=int(invisible.sum()),
                masked_grain_pixels=int((~grain_allowed).sum()),
                normal_sha256=hashlib.sha256(normal[2]).hexdigest(),
            )
        )
    if set(base_bindings) != set(updated_bindings):
        raise ValueError("World key set changed")
    # Both untouched keys and explicit preserve_previous keys must retain their
    # complete normal image tuples, including an absent image where recorded.
    for key in set(base_bindings) - set(selected) | preserved:
        if base_bindings[key] != updated_bindings[key]:
            raise ValueError("Unselected or previously reviewed normal changed")
    pages = []
    decoded_bindings = {}
    for index, entries in enumerate(pages_for(updated_bindings.items())):
        data = catalog.pack_surface_bindings(entries)
        if len(data) > PAGE_BYTES:
            raise ValueError("World page budget exceeded")
        name = f"world-{index:03}.bin"
        (output / name).write_bytes(data)
        decoded_bindings.update(catalog.read_surface_bindings(data))
        pages.append(dict(name=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    package_bytes = sum(page["bytes"] for page in pages)
    if package_bytes > PACKAGE_BYTES or len(pages) > 256 or decoded_bindings != updated_bindings:
        raise ValueError("World package budget or readback failed")
    for bank, pin in {**source["source_bank_pins"], **pins}.items():
        if sha(bank) != pin:
            raise ValueError("Source changed during preparation")
    receipt = dict(
        status="Campaign 1 mixed structural authoring and material-grain refinement candidate; native art review required",
        config_sha256=sha(config_path),
        source_pins=source["source_bank_pins"],
        base_page_pins=pins,
        bindings=len(updated_bindings),
        edits=edits,
        pages=pages,
        bytes=package_bytes,
        preserved_prior_keys=len(preserved),
        other_bindings_byte_identical=True,
        strength_baked=False,
        albedo_unchanged=True,
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
    result = prepare(args.config, args.output, args.hash_library)
    print(
        json.dumps(
            dict(
                bytes=result["bytes"],
                edits=len(result["edits"]),
                families=len({e["name"] for e in result["edits"]}),
            )
        )
    )
