"""Losslessly group identical normal images across bounded world catalog pages.

Source bindings and full image bytes are preserved. No renderer limits, normal
strengths, source colors, or image resolutions change. Outputs must be fresh.
"""

from pathlib import Path
import argparse
import hashlib
import json

import normal_materials as catalog

PAGE_BYTES = 16 * 1024 * 1024
PACKAGE_BYTES = 512 * 1024 * 1024


def pages_for(entries):
    """Yield pages grouped by identical image tuples without changing bindings.

    Keys remain unique across the package. Image equality includes dimensions
    and every pixel byte; None is an explicit absent image. Page accounting
    follows the catalog headers, key/index metadata and shared pixel payload.
    """
    groups = {}
    seen = set()
    for key, image in entries:
        if key in seen:
            raise ValueError("Duplicate source identity")
        seen.add(key)
        groups.setdefault(image, []).append(key)
    page = []
    images = set()
    pixel_bytes = 0
    for image, keys in groups.items():
        for key in keys:
            adds_image = image not in images
            extra_pixel_bytes = len(image[2]) if adds_image and image is not None else 0
            # BWSNR2 header + keys + BWNRM2 header/indices/image metadata.
            projected_bytes = (
                28
                + (len(page) + 1) * 56
                + (len(images) + adds_image) * 48
                + pixel_bytes
                + extra_pixel_bytes
            )
            # Keep equal images together where possible, but an alias group may
            # span pages when its keys reach the per-page runtime limit.
            if page and (
                len(page) == 256 or len(images) + adds_image > 64 or projected_bytes > PAGE_BYTES
            ):
                yield page
                page = []
                images = set()
                pixel_bytes = 0
                adds_image = True
                extra_pixel_bytes = len(image[2]) if image is not None else 0
            if 28 + 56 + 48 + extra_pixel_bytes > PAGE_BYTES:
                raise ValueError("Single image exceeds world page limit")
            page.append((key, image))
            if adds_image:
                images.add(image)
                pixel_bytes += extra_pixel_bytes
    if page:
        yield page


def repack(manifest, output):
    """Losslessly repack a manifest into a fresh directory and return its receipt.

    Each encoded page is decoded immediately, and the combined binding map must
    equal the source map. Rehash inputs before publishing the final manifest;
    interrupted writes may leave pages, but no completed manifest for loading.
    """
    if output.exists():
        raise ValueError("Choose a fresh output directory")
    lines = manifest.read_text().splitlines()
    if not lines or lines[0] != "MW34SNP1":
        raise ValueError("Unsupported world catalog")
    entries = []
    pins = {}
    source_bytes = 0
    for name in filter(None, lines[1:]):
        path = manifest.parent / name
        if path.parent.resolve() != manifest.parent.resolve():
            raise ValueError("World page outside manifest directory")
        data = path.read_bytes()
        pins[name] = hashlib.sha256(data).hexdigest()
        source_bytes += len(data)
        entries.extend(catalog.read_surface_bindings(data))
    pages = list(pages_for(entries))
    if len(pages) > 256:
        raise ValueError("Too many world pages")
    output.mkdir(parents=True)
    result = []
    repacked_bindings = {}
    for index, page in enumerate(pages):
        data = catalog.pack_surface_bindings(page)
        if len(data) > PAGE_BYTES:
            raise ValueError("Packed page exceeds limit")
        readback = catalog.read_surface_bindings(data)
        if readback != page:
            raise ValueError("Page roundtrip differs")
        name = f"world-{index:03}.bin"
        (output / name).write_bytes(data)
        repacked_bindings.update(readback)
        result.append(dict(name=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    total_bytes = sum(page["bytes"] for page in result)
    if total_bytes > PACKAGE_BYTES or total_bytes > source_bytes:
        raise ValueError("Repack increased storage or exceeded budget")
    if repacked_bindings != dict(entries):
        raise ValueError("Repack changed a source binding or normal image")
    for name, pin in pins.items():
        if hashlib.sha256((manifest.parent / name).read_bytes()).hexdigest() != pin:
            raise ValueError("Source changed during repack")
    receipt = dict(
        source_manifest=str(manifest),
        source_pages=pins,
        pages=result,
        bindings=len(entries),
        before_bytes=source_bytes,
        bytes=total_bytes,
        saved_bytes=source_bytes - total_bytes,
        all_bindings_byte_identical=True,
    )
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    (output / "world-normals.txt").write_text(
        "MW34SNP1\n" + "\n".join(p["name"] for p in result) + "\n"
    )
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--hash-library", type=Path, required=True)
    args = parser.parse_args()
    from prepare_world_normals import accelerated_hash

    catalog.pixel_hash = accelerated_hash(args.hash_library)
    result = repack(args.manifest, args.output)
    print(json.dumps({k: result[k] for k in ("bindings", "before_bytes", "bytes", "saved_bytes")}))
