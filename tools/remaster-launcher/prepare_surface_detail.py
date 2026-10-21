"""Prepare bounded water/surf/cloud normals from explicitly pinned upgraded banks.

Reads source banks without modifying albedo, animation, UVs or alpha. Selection
is explicit in a local config; no runtime name/address heuristics are used.
"""

from pathlib import Path
import argparse
import hashlib
import json
import struct
from normal_materials import pack_surface_bindings
from prepare_surface_normals import bank_entries
from prepare_world_normals import accelerated_hash


def sha(path):
    """Stream a local file's SHA-256 for source and output identities."""
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def rgb565(data, width, height):
    """Decode little-endian RGB565 words into an (H, W, 3) float array in [0, 1]."""
    import numpy as np

    packed_words = np.frombuffer(data, dtype="<u2").reshape(height, width)
    return np.stack(
        (
            (packed_words >> 11) / 31.0,
            ((packed_words >> 5) & 63) / 63.0,
            (packed_words & 31) / 31.0,
        ),
        axis=-1,
    )


def water_tile(size=128):
    """Create a periodic RGBA ripple tile; alpha initially permits full strength.

    Integer wave frequencies repeat over the tile. XY encodes exact neutral
    128 with a scale of 127; Z uses the full unsigned range. Keep this convention
    aligned with the detail shader rather than generic normal-map encoding.
    """
    import numpy as np

    y, x = np.mgrid[:size, :size] * (2 * np.pi / size)
    dx = np.zeros_like(x)
    dy = np.zeros_like(y)
    # Integer frequencies: a periodic field, identical for open water and surf.
    for kx, ky, amplitude, phase in [(2, 1, 0.055, 0), (1, -3, 0.032, 1.2), (4, 3, 0.012, 2.4)]:
        wave = np.cos(kx * x + ky * y + phase)
        dx -= amplitude * kx * wave
        dy -= amplitude * ky * wave
    unit_normals = np.stack((dx, dy, np.ones_like(dx)), axis=-1)
    unit_normals /= np.linalg.norm(unit_normals, axis=-1, keepdims=True)
    rgba = np.full((size, size, 4), 255, dtype="uint8")
    # XY uses exactly neutral128; shader decodes (byte-128)/127.
    rgba[..., :2] = np.rint(unit_normals[..., :2] * 127 + 128).clip(0, 255).astype("uint8")
    rgba[..., 2] = np.rint(unit_normals[..., 2] * 255).astype("uint8")
    return rgba


def normal_for(role, colour, w, h):
    """Return (width, height, RGBA bytes) for water, surf or the cloud path.

    Water and surf share one ripple field; surf alpha masks its strength using
    the reviewed atlas orientation. Cloud XY is a bounded color-derived slope
    estimate, with neutral borders and full alpha/Z. The caller validates roles.
    """
    import numpy as np
    from PIL import Image, ImageFilter

    rgb = rgb565(colour, w, h)
    if role in ("water", "surf"):
        result = water_tile()
        if role == "surf":
            # This orientation is explicitly reviewed for the C1 wave atlas.
            # Water occupies the right edge; neutral foam/warm sand stay flat.
            mask = np.clip(((rgb[..., 1] - rgb[..., 0]) * 255 - 3) / 12, 0, 1)
            mask *= np.clip((np.arange(w) / w - 0.60) / 0.12, 0, 1)[None, :]
            mask[np.min(rgb, axis=-1) > 140 / 255] = 0
            mask_image = Image.fromarray(np.rint(mask * 255).astype("uint8"))
            result[..., 3] = np.asarray(mask_image.resize((128, 128), Image.Resampling.BOX))
        return (128, 128, result.tobytes())
    # Broad, filtered cloud relief. This is a first-pass height estimate from
    # upgraded cloud colors, not volume scattering or geometric cloud height.
    size = (
        max(1, round(w * min(1, 256 / w, 256 / h))),
        max(1, round(h * min(1, 256 / w, 256 / h))),
    )
    luminance = rgb @ np.array([0.2126, 0.7152, 0.0722])
    image = (
        Image.fromarray(np.rint(luminance * 255).astype("uint8"))
        .resize(size, Image.Resampling.BOX)
        .filter(ImageFilter.GaussianBlur(2))
    )
    height_field = np.asarray(image, dtype=float) / 255
    dx = (np.roll(height_field, -1, 1) - np.roll(height_field, 1, 1)) * 3
    dy = (np.roll(height_field, -1, 0) - np.roll(height_field, 1, 0)) * 3
    xy_slopes = np.stack((-dx, -dy), axis=-1)
    xy_slopes *= np.minimum(
        1, 0.3 / np.maximum(np.linalg.norm(xy_slopes, axis=-1, keepdims=True), 1e-10)
    )
    result = np.full((size[1], size[0], 4), 255, dtype="uint8")
    result[..., :2] = np.rint(xy_slopes * 127 + 128).clip(0, 255).astype("uint8")
    # Flat borders avoid inventing a ridge where a non-periodic sky atlas meets.
    result[:3, :, :2] = result[-3:, :, :2] = [128, 128]
    result[:, :3, :2] = result[:, -3:, :2] = [128, 128]
    return (*size, result.tobytes())


def prepare(config, output, hash_library):
    """Write three role catalogs and a receipt from explicitly selected bank entries.

    Source hashes and entry spans are checked before use, then sources are
    rehashed before output. A complete-pixel identity cannot belong to two roles.
    Output must be fresh, but writes are sequential: failures can leave partial
    catalogs, so directory existence alone does not establish a complete package.
    """
    config = Path(config).resolve(strict=True)
    output = Path(output).resolve()
    if output.exists():
        raise ValueError("Choose a fresh detail output directory")
    selected = json.loads(config.read_text())
    digest = accelerated_hash(hash_library)
    roles = {role: {} for role in ("water", "surf", "cloud")}
    receipts = []
    config_sha = sha(config)
    for bank in selected["banks"]:
        path = Path(bank["path"]).resolve(strict=True)
        if bank.get("upgraded") is not True or sha(path) != bank["sha256"]:
            raise ValueError("Expected pinned upgraded source bank")
        table = bank_entries(path)
        with path.open("rb") as stream:
            for selection in bank["entries"]:
                name, role = selection["name"], selection["role"]
                if role not in roles:
                    raise ValueError("Unknown detail role")
                offset, span = table[name]
                stream.seek(offset)
                header = stream.read(16)
                flags, w, h, zero, palette, stretch = struct.unpack("<IHHIHH", header)
                if (
                    flags not in (5, 0x25)
                    or zero
                    or palette
                    or stretch not in (0, 1, 2, 3)
                    or not 0 < w <= 4096
                    or not 0 < h <= 4096
                    or span != 16 + w * h * 2
                ):
                    raise ValueError("Unsupported selected detail source layout")
                colour = stream.read(w * h * 2)
                # Bind to all stored RGB565 pixels, not a texture name or a
                # sample from the image. Detail alpha never changes bank coverage.
                key = (w, h, 1, digest(colour))
                normal = normal_for(role, colour, w, h)
                if key in roles[role] and roles[role][key] != normal:
                    raise ValueError("Ambiguous detail key")
                roles[role][key] = normal
                receipts.append(
                    dict(
                        bank=str(path),
                        bank_sha256=bank["sha256"],
                        name=name,
                        role=role,
                        key=key,
                        normal_sha256=hashlib.sha256(normal[2]).hexdigest(),
                    )
                )
        if sha(path) != bank["sha256"]:
            raise ValueError("Source bank changed while preparing")
    if any(
        set(roles[a]) & set(roles[b])
        for a, b in [("water", "surf"), ("water", "cloud"), ("surf", "cloud")]
    ):
        raise ValueError("Conflicting detail roles")
    if sha(config) != config_sha:
        raise ValueError("Registration changed while preparing")
    output.mkdir(parents=True)
    packs = {}
    for role, entries in roles.items():
        if not entries:
            raise ValueError("Empty detail role: " + role)
        data = pack_surface_bindings(list(entries.items()))
        if len(data) > 16 * 1024 * 1024:
            raise ValueError("Detail role exceeds 16 MiB")
        path = output / (role + "-normals.bin")
        path.write_bytes(data)
        packs[role] = dict(path=str(path), sha256=sha(path), bindings=len(entries), bytes=len(data))
    report = dict(
        status="prepared; native validation required",
        scope=selected["scope"],
        config_sha256=config_sha,
        hash_library_sha256=sha(hash_library),
        packs=packs,
        registrations=receipts,
    )
    (output / "receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--hash-library", type=Path, required=True)
    a = p.parse_args()
    r = prepare(a.config, a.output, a.hash_library)
    print(json.dumps(r["packs"], indent=2))
