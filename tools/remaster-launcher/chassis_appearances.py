"""Validated appearance selection for an owned legacy chassis.

Selection never changes a registration, controller or gameplay resource. Normal
pages bind complete color pixels; content cannot register unrelated surfaces.
"""

import struct
from pathlib import Path

from legacy_chassis_resources import image
from normal_materials import pixel_hash, read_surface_bindings

CAPABILITY = "mech-appearances"
MODES = ("original", "upgraded", "new")
MAX_PAGE_BYTES = 128 * 1024**2
NATIVE_PAGE_BYTES = 256 * 1024**2
MAX_CATALOG_BYTES = 512 * 1024**2


def mode(value):
    if value is not None and (not isinstance(value, str) or value not in MODES):
        raise ValueError("Unknown mech appearance mode")
    return value or "original"


def references(appearances, texture_names):
    """Yield (role, texture name or None, path); do not read untrusted paths here."""
    if not isinstance(appearances, dict) or not appearances or set(appearances) - {"upgraded", "new"}:
        raise ValueError("Appearance v1 requires exactly the upgraded alternative")
    if "new" in appearances:
        from owned_chassis_visuals import references as owned_references
        list(owned_references(appearances["new"]))
    if "upgraded" not in appearances:
        return
    upgraded = appearances["upgraded"]
    if not isinstance(upgraded, dict) or set(upgraded) != {"textures", "normals"}:
        raise ValueError("Appearance may change only textures and normals")
    textures, pages = upgraded["textures"], upgraded["normals"]
    if (
        not isinstance(textures, dict)
        or not 1 <= len(textures) <= 512
        or not set(textures) <= set(texture_names)
    ):
        raise ValueError("Appearance names an unknown or empty texture set")
    if (
        not isinstance(pages, list)
        or len(pages) > 16
        or any(not isinstance(path, str) for path in pages)
        or len(set(pages)) != len(pages)
    ):
        raise ValueError("Invalid appearance normal page list")
    for name, path in textures.items():
        if not isinstance(path, str) or not path:
            raise ValueError("Invalid appearance texture path")
        yield "textures", name, path
    for path in pages:
        if not path:
            raise ValueError("Invalid appearance normal path")
        yield "normals", None, path


def validate(appearances, legacy, read):
    """Read already hash-verified resources, validating inactive alternatives too."""
    textures, pages, keys = {}, [], set()
    for role, name, path in references(appearances, legacy["textures"]):
        data = read(path, "BWSNR2" if role == "normals" else None)
        if role == "textures":
            if not 0 < len(data) <= 16 * 1024**2:
                raise ValueError("Appearance texture exceeds legacy resource limit")
            image(data)
            textures[name] = data
            flags, width, height = struct.unpack_from("<IHH", data)
            # V1 normal registration covers opaque RGB565 uploads. Alpha images
            # may be replaced, but their converted upload identities are not v1.
            if flags == 5:
                keys.add((width, height, 1, pixel_hash(data[16:])))
        else:
            if not 0 < len(data) <= MAX_PAGE_BYTES or data[:8] != b"BWSNR2\0\0":
                raise ValueError("Invalid appearance normal page")
            pages.append(data)
    if sum(map(len, pages)) > MAX_CATALOG_BYTES:
        raise ValueError("Appearance normal catalog exceeds resident budget")
    bindings = {}
    for page in pages:
        for key, normal in read_surface_bindings(page):
            if key not in keys:
                raise ValueError("Appearance normal does not match an upgraded opaque texture")
            if key in bindings:
                raise ValueError("Duplicate appearance normal key")
            bindings[key] = normal
    return {"textures": textures, "normal_pages": pages}


def choose(legacy, upgraded, requested=None):
    requested = mode(requested)
    selected = "upgraded" if requested != "original" and upgraded is not None else "original"
    result = dict(legacy)
    result["textures"] = dict(legacy["textures"])
    pages = []
    if selected == "upgraded":
        result["textures"].update(upgraded["textures"])
        pages = list(upgraded["normal_pages"])
    reason = None
    if requested != selected:
        reason = "new-model-unavailable" if requested == "new" else "upgrade-unavailable"
    return result, pages, {"requested": requested, "selected": selected, "reason": reason}


def inherited_pages(path):
    """Expand the trusted launch profile's bounded surface index, never pack paths."""
    path = Path(path).resolve()
    with path.open("rb") as stream:
        magic = stream.read(8)
    if magic in (b"BWSNR2\0\0", b"BWSNR3\0\0"):
        return [path]
    if path.stat().st_size > 4096:
        raise ValueError("Inherited surface normal index exceeds limit")
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    if not lines or lines[0] != "MW34SNA1" or not 1 <= len(lines) - 1 <= 16:
        raise ValueError("Invalid inherited surface normal index")
    if any(not line or "\0" in line for line in lines[1:]):
        raise ValueError("Invalid inherited surface normal page")
    return [(path.parent / line).resolve() for line in lines[1:]]


def compose_normals(records, environment, output):
    """Return only a new catalog binding; never enable lighting or normal maps."""
    pages = [data for row in records for data in row.get("appearance_normal_pages", [])]
    if not pages:
        return {}
    paths = (
        inherited_pages(environment["MW34_SURFACE_NORMALS"])
        if environment.get("MW34_SURFACE_NORMALS")
        else []
    )
    output = Path(output)
    output.mkdir(exist_ok=False)
    for index, data in enumerate(pages):
        path = output / f"chassis-{index}.bin"
        path.write_bytes(data)
        paths.append(path.resolve())
    paths = list(dict.fromkeys(paths))
    if len(paths) > 128 or sum(path.stat().st_size for path in paths) > MAX_CATALOG_BYTES:
        raise ValueError("Combined surface normal catalog exceeds source budget")
    for path in paths:
        if not 0 < path.stat().st_size <= NATIVE_PAGE_BYTES:
            raise ValueError("Surface normal page exceeds budget")
    from surface_catalog_composition import compose

    result = compose(paths, output / "composed")
    manifest = Path(result["manifest"])
    if len(result["output_sha256"]) > 16 or manifest.stat().st_size > 4096:
        raise ValueError("Combined surface normal catalog exceeds native page/index limit")
    # Composition expands inherited compressed pages to BWSNR2. Check the
    # actual output, not only the compressed source size, before binding it.
    outputs = [Path(path) for path in result["output_sha256"]]
    if sum(path.stat().st_size for path in outputs) > MAX_CATALOG_BYTES or any(
        path.stat().st_size > NATIVE_PAGE_BYTES for path in outputs
    ):
        raise ValueError("Combined surface normal catalog exceeds native resident budget")
    return {"MW34_SURFACE_NORMALS": str(manifest)}
