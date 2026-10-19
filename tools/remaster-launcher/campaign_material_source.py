"""Read a pinned upgraded RGB565/alpha bank entry without altering its color.

Alpha entries have a separate coverage plane; their runtime color identities
may be RGB565, ARGB1555 or ARGB4444. Preserve the actual layout for relief work.
"""
import hashlib
import struct

import numpy as np
from PIL import Image


def converted_color(words, alpha, format_):
    if format_ == 1:
        return words.astype('<u2').tobytes()
    if alpha is None:
        raise ValueError('Alpha source required for alpha format')
    if format_ == 2:
        value = ((words >> 1) & 0x7fe0) | (words & 31) | ((alpha >= 128).astype('uint16') << 15)
    elif format_ == 3:
        value = ((words >> 4) & 0xf00) | ((words >> 3) & 0xf0) | ((words >> 1) & 15) | ((alpha.astype('uint16') >> 4) << 12)
    else:
        raise ValueError('Unsupported runtime color format')
    return value.astype('<u2').tobytes()


def read_variant(variant, digest):
    with open(variant['bank'], 'rb') as stream:
        stream.seek(variant['offset'])
        flags, w, h, reserved, palette, stretch = struct.unpack('<IHHIHH', stream.read(16))
        if flags not in (5, 37, 11, 43) or reserved or palette or not 0 < w <= 4096 or not 0 < h <= 4096:
            raise ValueError('Unsupported upgraded campaign bank entry')
        raw = stream.read(w * h * 2)
        if len(raw) != w * h * 2:
            raise ValueError('Truncated campaign color plane')
        coverage = stream.read(w * h) if flags in (11, 43) else None
    if coverage is not None and len(coverage) != w * h:
        raise ValueError('Truncated campaign coverage plane')
    if hashlib.sha256(raw).hexdigest() != variant['source_rgb565_sha256']:
        raise ValueError('Upgraded campaign source color changed')
    if coverage is not None and hashlib.sha256(coverage).hexdigest() != variant['source_alpha_sha256']:
        raise ValueError('Upgraded campaign source coverage changed')
    words = np.frombuffer(raw, dtype='<u2').reshape(h, w).astype('uint32')
    alpha = np.frombuffer(coverage, dtype='uint8').reshape(h, w) if coverage is not None else None
    colour = converted_color(words, alpha, variant['key'][2])
    if [w, h, variant['key'][2], digest(colour)] != variant['key']:
        raise ValueError('Full upgraded campaign source identity differs')
    if hashlib.sha256(colour).hexdigest() != variant['converted_colour_sha256']:
        raise ValueError('Converted campaign color differs')
    rgb = np.stack(((words >> 11) * 255 // 31, ((words >> 5) & 63) * 255 // 63,
                    (words & 31) * 255 // 31), axis=-1).astype('uint8')
    return Image.fromarray(rgb), (Image.fromarray(alpha) if alpha is not None else None)
