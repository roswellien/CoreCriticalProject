"""Read a pinned upgraded RGB565/alpha bank entry without altering its color.

Alpha entries have a separate coverage plane; their runtime color identities
may be RGB565, ARGB1555 or ARGB4444. Preserve the actual layout for relief work.
"""

import hashlib
import struct

import numpy as np
from PIL import Image


def converted_color(words, alpha, format_):
    """Encode RGB565 words and optional 8-bit coverage as runtime color bytes.

    Format IDs are 1: RGB565, 2: ARGB1555 and 3: ARGB4444. Preserve the upload
    conversion's bit truncation and 128 coverage threshold; these bytes form
    the runtime binding identity, rather than a display-quality conversion.
    """
    if format_ == 1:
        return words.astype("<u2").tobytes()
    if alpha is None:
        raise ValueError("Alpha source required for alpha format")
    if format_ == 2:
        value = ((words >> 1) & 0x7FE0) | (words & 31) | ((alpha >= 128).astype("uint16") << 15)
    elif format_ == 3:
        value = (
            ((words >> 4) & 0xF00)
            | ((words >> 3) & 0xF0)
            | ((words >> 1) & 15)
            | ((alpha.astype("uint16") >> 4) << 12)
        )
    else:
        raise ValueError("Unsupported runtime color format")
    return value.astype("<u2").tobytes()


def read_variant(variant, digest):
    """Validate one pinned bank entry and return RGB artwork plus optional coverage.

    ``digest`` implements the runtime pixel hash. Both the stored planes and
    converted upload bytes must match the registration before artwork is used.
    The returned images show the original RGB565 color and full 8-bit coverage,
    even when the registered runtime upload has lower alpha precision.
    """
    with open(variant["bank"], "rb") as stream:
        stream.seek(variant["offset"])
        flags, width, height, reserved, palette, stretch = struct.unpack("<IHHIHH", stream.read(16))
        if (
            flags not in (5, 37, 11, 43)
            or reserved
            or palette
            or not 0 < width <= 4096
            or not 0 < height <= 4096
        ):
            raise ValueError("Unsupported upgraded campaign bank entry")
        raw = stream.read(width * height * 2)
        if len(raw) != width * height * 2:
            raise ValueError("Truncated campaign color plane")
        coverage = stream.read(width * height) if flags in (11, 43) else None
    if coverage is not None and len(coverage) != width * height:
        raise ValueError("Truncated campaign coverage plane")
    if hashlib.sha256(raw).hexdigest() != variant["source_rgb565_sha256"]:
        raise ValueError("Upgraded campaign source color changed")
    if (
        coverage is not None
        and hashlib.sha256(coverage).hexdigest() != variant["source_alpha_sha256"]
    ):
        raise ValueError("Upgraded campaign source coverage changed")
    words = np.frombuffer(raw, dtype="<u2").reshape(height, width).astype("uint32")
    alpha = (
        np.frombuffer(coverage, dtype="uint8").reshape(height, width)
        if coverage is not None
        else None
    )
    colour = converted_color(words, alpha, variant["key"][2])
    if [width, height, variant["key"][2], digest(colour)] != variant["key"]:
        raise ValueError("Full upgraded campaign source identity differs")
    if hashlib.sha256(colour).hexdigest() != variant["converted_colour_sha256"]:
        raise ValueError("Converted campaign color differs")
    rgb = np.stack(
        ((words >> 11) * 255 // 31, ((words >> 5) & 63) * 255 // 63, (words & 31) * 255 // 31),
        axis=-1,
    ).astype("uint8")
    return Image.fromarray(rgb), (Image.fromarray(alpha) if alpha is not None else None)
