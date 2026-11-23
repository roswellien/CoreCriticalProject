"""Compose authored normal catalogs without changing their selected image pixels.

Identical duplicate bindings collapse. Conflicting images require an explicit
full-content key -> source catalog choice; input order never resolves a conflict.
All inputs remain read-only, and the output manifest is published last.
"""
import hashlib
from pathlib import Path

from normal_materials import pack_surface_bindings, read_surface_bindings

MAX_WORKING_BYTES = 512 * 1024**2
MAX_NATIVE_PAGE_BYTES = 256 * 1024**2
MAX_BINDINGS_PER_PAGE = 256
MAX_IMAGES_PER_PAGE = 64
MAX_IMAGE_BYTES_PER_PAGE = 256 * 1024**2


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _decoded_page(path, retained_decoded_bytes):
    entries = read_surface_bindings(
        path.read_bytes(),
        max_working_bytes=MAX_WORKING_BYTES,
        retained_decoded_bytes=retained_decoded_bytes,
        cache_hashes=False,
    )
    retained_images = {id(normal): normal for _, normal in entries if normal is not None}
    decoded_bytes = sum(len(normal[2]) for normal in retained_images.values())
    return entries, decoded_bytes


def _packed_pages(entries):
    pages = []
    current = []
    images = set()
    image_bytes = 0

    def page_size(binding_count, image_count, total_image_bytes):
        return 28 + 56 * binding_count + 48 * image_count + total_image_bytes

    def exceeds_page_budget(normal):
        is_new_image = normal is not None and normal not in images
        added_image_bytes = len(normal[2]) if is_new_image else 0
        exceeds = (
            len(current) >= MAX_BINDINGS_PER_PAGE
            or (is_new_image and len(images) >= MAX_IMAGES_PER_PAGE)
            or image_bytes + added_image_bytes > MAX_IMAGE_BYTES_PER_PAGE
            or page_size(
                len(current) + 1,
                len(images) + int(is_new_image),
                image_bytes + added_image_bytes,
            )
            > MAX_NATIVE_PAGE_BYTES
        )
        return exceeds, is_new_image, added_image_bytes

    def finish_page():
        nonlocal current, images, image_bytes
        if current:
            pages.append(current)
            current, images, image_bytes = [], set(), 0

    for entry in entries:
        _key, normal = entry
        exceeds_limits, is_new_image, added_image_bytes = exceeds_page_budget(normal)
        if current and exceeds_limits:
            finish_page()
            exceeds_limits, is_new_image, added_image_bytes = exceeds_page_budget(normal)
        if exceeds_limits:
            raise ValueError("One surface binding exceeds the native page budget")
        current.append(entry)
        if is_new_image:
            images.add(normal)
            image_bytes += added_image_bytes
    finish_page()
    return pages


def compose(paths, output, *, overrides=None):
    paths = [Path(path).resolve() for path in paths]
    if not paths or len(paths) > 128 or len(set(paths)) != len(paths):
        raise ValueError("Invalid source catalog list")
    choices = {key: Path(path).resolve() for key, path in (overrides or {}).items()}
    output = Path(output)
    if output.exists():
        raise ValueError("Use a fresh composition directory")
    pins = {path: sha(path) for path in paths}
    pages = []
    retained_decoded_bytes = 0
    for path in paths:
        entries, decoded_bytes = _decoded_page(path, retained_decoded_bytes)
        pages.append(entries)
        retained_decoded_bytes += decoded_bytes
    candidates = {}
    duplicate_count = 0
    conflicts = set()
    for path, entries in zip(paths, pages):
        for key, image in entries:
            if key in candidates:
                duplicate_count += 1
            candidates.setdefault(key, []).append((path, image))
    selected = {}
    for key, variants in candidates.items():
        if all(image == variants[0][1] for _, image in variants):
            selected[key] = variants[0]
            continue
        conflicts.add(key)
        winner = choices.get(key)
        matches = [variant for variant in variants if variant[0] == winner]
        if not matches:
            raise ValueError("Conflicting surface images require an explicit source choice: " + str(key))
        selected[key] = matches[0]
    if set(choices) != conflicts:
        raise ValueError("Source choices must name exactly the conflicting full-content keys")
    output.mkdir(parents=True)
    catalogs = []
    selected_entries = [(key, image) for key, (_source, image) in selected.items()]
    for index, page in enumerate(_packed_pages(selected_entries)):
        encoded = pack_surface_bindings(page, cache_hashes=False)
        # Round-trip checks the existing binary format and exact selected images.
        if read_surface_bindings(
            encoded,
            max_working_bytes=MAX_WORKING_BYTES,
            retained_decoded_bytes=retained_decoded_bytes,
            cache_hashes=False,
        ) != page:
            raise ValueError("Composed surface catalog changed selected image data")
        target = output / f"page-{index:03}.bin"
        target.write_bytes(encoded)
        catalogs.append(target.resolve())
    if any(sha(path) != pin for path, pin in pins.items()):
        raise ValueError("Source catalog changed during composition")
    manifest = output / "surface-normals.txt"
    manifest.write_text("MW34SNA1\n" + "\n".join(map(str, catalogs)) + "\n", encoding="utf-8")
    return dict(manifest=str(manifest.resolve()), input_sha256={str(p): h for p, h in pins.items()},
                bindings=len(selected), duplicates=duplicate_count, resolved_conflicts=len(conflicts),
                output_sha256={str(p): sha(p) for p in catalogs})
