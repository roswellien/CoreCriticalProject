"""Pack explicitly registered linear OpenGL normal maps for native materials.

BWNRM2 uses material names, explicit unperturbed batch bindings and full-pixel
FNV-1a identities. Colour conversion, strength baking and normal-Y inversion
are deliberately absent. Optional BWNRM3/BWSNR3 transport compresses identical
pixels losslessly; callers must select a reader supporting that format. Existing
writers retain version 2 by default. Inputs and generated sidecars stay local.
"""

from pathlib import Path
import struct
import io
from functools import lru_cache

NO_NORMAL = 0xFFFFFFFF


class DecodedSurfaceBudgetExceeded(ValueError):
    """Raised before a surface page decodes beyond its caller's memory budget."""


def uncached_pixel_hash(data):
    """Return the renderer's 64-bit FNV-1a identity without retaining pixel bytes."""
    value = 0xCBF29CE484222325
    for byte in data:
        value = ((value ^ byte) * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return value


@lru_cache(maxsize=8)
def pixel_hash(data):
    """Return the renderer's 64-bit FNV-1a identity over every supplied pixel byte.

    This format key is not a cryptographic authenticity check. The small cache
    retains byte strings during preparation; native_assets clears it before play.
    """
    return uncached_pixel_hash(data)


def normal_environment(texture_environment):
    """Derive the paired MW34_*_NORMALS name from a validated texture binding."""
    if not texture_environment.startswith("MW34_") or not texture_environment.endswith("_TEXTURES"):
        raise ValueError("Normal maps require a MW34_*_TEXTURES binding")
    return texture_environment[:-9] + "_NORMALS"


def pack_normals(batch_materials, images, *, compressed=False, cache_hashes=True):
    """Encode BWNRM2 batch bindings and explicitly supplied linear normal pixels.

    ``images`` maps names to (width, height, raw RGBA bytes), or None. None writes
    NO_NORMAL, preserving an unperturbed material instead of inventing a texture.
    Batch order is significant; unused images are omitted. Counts, dimensions,
    names and the total pixel budget are checked before returning the bytes.
    """
    if not batch_materials or len(batch_materials) > 256 or len(images) > 256:
        raise ValueError("Invalid normal material/batch count")
    if set(batch_materials) - images.keys():
        raise ValueError("Every batch needs an explicit normal-map or disabled binding")
    used = {name for name in batch_materials if images[name] is not None}
    names = [name for name in images if name in used]
    if len(names) > 64:
        raise ValueError("Invalid normal image count")
    indices = {name: i for i, name in enumerate(names)}
    bindings = [indices.get(name, NO_NORMAL) for name in batch_materials]
    hash_pixels = pixel_hash if cache_hashes else uncached_pixel_hash
    out = bytearray((b"BWNRM3\0\0" if compressed else b"BWNRM2\0\0") + struct.pack("<II", len(bindings), len(names)))
    out.extend(struct.pack("<" + "I" * len(bindings), *bindings))
    total = 0
    for name in names:
        encoded = name.encode("ascii")
        if not encoded or len(encoded) > 31 or b"\0" in encoded:
            raise ValueError("Invalid normal material name")
        width, height, pixels = images[name]
        total += len(pixels)
        if (
            not 0 < width <= 4096
            or not 0 < height <= 4096
            or len(pixels) != width * height * 4
            or total > 256 * 1024 * 1024
        ):
            raise ValueError("Invalid normal image size")
        out.extend(encoded.ljust(32, b"\0"))
        out.extend(struct.pack("<IIQ", width, height, hash_pixels(pixels)))
        if compressed:
            from normal_codec import encode
            encoded_pixels = encode(pixels)
            out.extend(struct.pack("<Q", len(encoded_pixels)))
            out.extend(encoded_pixels)
        else:
            out.extend(pixels)
    return bytes(out)


def load_images(root, normal_textures):
    """Load linear channel values as RGBA, vertically flipped for native UVs.

    None remains an explicit disabled map. Do not add albedo colour conversion,
    strength adjustment or green-channel inversion to this transport step.
    """
    from PIL import Image

    images = {}
    for name, relative in normal_textures.items():
        if relative is None:
            images[name] = None
            continue
        with Image.open(Path(root) / relative) as source:
            # Preserve channel values and resolution; normal maps are linear data.
            image = source.convert("RGBA").transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            images[name] = (*image.size, image.tobytes())
    return images


def pack_surface_normals(entries):
    """entries: (source width, height, 16-bit format, packed colour bytes, normal image).

    Normal images are (width,height,RGBA bytes) or None. No short texture
    signatures, map-specific names, or process addresses enter the contract.
    """
    keys = []
    for width, height, format_, colour, normal in entries:
        if (
            not 0 < width <= 4096
            or not 0 < height <= 4096
            or format_ not in (1, 2, 3)
            or len(colour) != width * height * 2
        ):
            raise ValueError("Invalid source texture identity")
        keys.append(((width, height, format_, pixel_hash(colour)), normal))
    return pack_surface_bindings(keys)


def pack_surface_bindings(entries, *, compressed=False, cache_hashes=True):
    """Pack validated full-content keys, sharing byte-identical normal images.

    Up to 256 original surfaces can reference up to 64 images. A key supplied
    here must come from hashing every source color byte, or a validated catalog.
    """
    if not 0 < len(entries) <= 256:
        raise ValueError("Invalid surface binding count")
    header = bytearray((b"BWSNR3\0\0" if compressed else b"BWSNR2\0\0") + struct.pack("<I", len(entries)))
    images = {}
    keys = set()
    names = []
    shared = {}
    for key, normal in entries:
        width, height, format_, hash_ = key
        if (
            not 0 < width <= 4096
            or not 0 < height <= 4096
            or format_ not in (1, 2, 3)
            or not 0 <= hash_ < 1 << 64
        ):
            raise ValueError("Invalid source texture identity")
        if key in keys:
            raise ValueError("Ambiguous duplicate surface identity")
        keys.add(key)
        # The entire immutable image tuple participates in equality; a hash
        # collision alone cannot conflate different normal images.
        if normal not in shared:
            name = "surface" + str(len(images))
            shared[normal] = name
            images[name] = normal
        name = shared[normal]
        names.append(name)
        header.extend(struct.pack("<IIIQ", *key))
        header.extend(name.encode().ljust(32, b"\0"))
    return bytes(header) + pack_normals(
        names, images, compressed=compressed, cache_hashes=cache_hashes
    )


def read_surface_bindings(
    data,
    *,
    max_decoded_bytes=256 * 1024 * 1024,
    max_working_bytes=None,
    retained_decoded_bytes=0,
    cache_hashes=True,
):
    """Read an existing BWSNR2 catalog for a validated, lossless extension."""
    if type(max_decoded_bytes) is not int or not 0 <= max_decoded_bytes <= 256 * 1024 * 1024:
        raise ValueError("Invalid decoded surface budget")
    invalid_working_budget = max_working_bytes is not None and (
        type(max_working_bytes) is not int or max_working_bytes < 0
    )
    invalid_retained_budget = (
        type(retained_decoded_bytes) is not int or retained_decoded_bytes < 0
    )
    if invalid_working_budget or invalid_retained_budget:
        raise ValueError("Invalid decoded working memory budget")
    hash_pixels = pixel_hash if cache_hashes else uncached_pixel_hash
    stream = io.BytesIO(data)

    def read(size):
        value = stream.read(size)
        if len(value) != size:
            raise ValueError("Truncated surface catalog")
        return value

    def u32():
        return struct.unpack("<I", read(4))[0]

    def name():
        raw = read(32)
        if not raw[0] or raw[-1]:
            raise ValueError("Invalid surface material name")
        return raw.split(b"\0")[0].decode("ascii")

    surface_magic = read(8)
    if surface_magic not in (b"BWSNR2\0\0", b"BWSNR3\0\0"):
        raise ValueError("Unsupported surface catalog")
    count = u32()
    if not 0 < count <= 256:
        raise ValueError("Invalid surface binding count")
    bindings = []
    keys = set()
    for _ in range(count):
        key = struct.unpack("<IIIQ", read(20))
        material = name()
        w, h, format_, _ = key
        if not 0 < w <= 4096 or not 0 < h <= 4096 or format_ not in (1, 2, 3) or key in keys:
            raise ValueError("Invalid or duplicate surface key")
        keys.add(key)
        bindings.append((key, material))
    normal_magic = read(8)
    if normal_magic != (b"BWNRM3\0\0" if surface_magic == b"BWSNR3\0\0" else b"BWNRM2\0\0") or u32() != count:
        raise ValueError("Invalid surface normal payload")
    image_count = u32()
    if image_count > 64:
        raise ValueError("Invalid normal image count")
    indices = [u32() for _ in range(count)]
    images = []
    names = set()
    total = 0
    for _ in range(image_count):
        material = name()
        w, h, hash_ = struct.unpack("<IIQ", read(16))
        image_bytes = w * h * 4
        if material in names or not 0 < w <= 4096 or not 0 < h <= 4096:
            raise ValueError("Invalid normal image")
        if total + image_bytes > max_decoded_bytes:
            raise DecodedSurfaceBudgetExceeded("Surface page exceeds decoded memory budget")
        if max_working_bytes is not None:
            # The compressed decoder holds its delta buffer, output buffer and
            # returned bytes together at peak.
            decoder_peak_bytes = image_bytes * (
                3 if normal_magic == b"BWNRM3\0\0" else 1
            )
            if retained_decoded_bytes + total + decoder_peak_bytes > max_working_bytes:
                raise DecodedSurfaceBudgetExceeded(
                    "Surface page exceeds decoded working memory budget"
                )
        total += image_bytes
        names.add(material)
        if normal_magic == b"BWNRM3\0\0":
            from normal_codec import decode
            encoded_size = struct.unpack("<Q", read(8))[0]
            if not 0 < encoded_size <= w * h * 8:
                raise ValueError("Invalid encoded normal size")
            pixels = decode(read(encoded_size), w * h * 4)
        else:
            pixels = read(w * h * 4)
        if hash_pixels(pixels) != hash_:
            raise ValueError("Normal image hash mismatch")
        images.append((material, (w, h, pixels)))
    if stream.read(1):
        raise ValueError("Trailing surface catalog data")
    result = []
    for (key, material), index in zip(bindings, indices):
        if index == NO_NORMAL:
            normal = None
        elif index >= len(images) or images[index][0] != material:
            raise ValueError("Normal material binding mismatch")
        else:
            normal = images[index][1]
        result.append((key, normal))
    return result
