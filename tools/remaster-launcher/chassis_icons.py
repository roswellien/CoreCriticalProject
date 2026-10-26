"""Portable chassis silhouette masks and original-compatible named UI images.

Masks are authored pack data. Original image-bank members are retained byte for
byte; four tinted additions use the retail icon_<resource>_<state> lookup.
"""
import re
import struct

WIDTH, HEIGHT = 41, 50
MAGIC = b'MW3ICON1'
COLORS = {'green': (0, 255, 0), 'grey': (128, 128, 128),
          'red': (255, 0, 0), 'yellow': (255, 255, 0)}


def mask(data):
    if (not isinstance(data, bytes) or len(data) != 16 + WIDTH * HEIGHT
            or data[:8] != MAGIC or struct.unpack_from('<II', data, 8) != (WIDTH, HEIGHT)
            or not any(data[16:])):
        raise ValueError('Chassis silhouette must be a nonempty 41x50 MW3ICON1 mask')
    return data[16:]


def image(mask_bytes, color):
    pixels = bytearray()
    for intensity in mask_bytes:
        r, g, b = (c * intensity // 255 for c in color)
        word = ((r * 31 // 255) << 11) | ((g * 63 // 255) << 5) | (b * 31 // 255)
        pixels += struct.pack('<H', word)
    return struct.pack('<IHHIHH', 3, WIDTH, HEIGHT, 0, 0, 0) + pixels


def append_icons(original, additions):
    """Rebuild the table with relocated original spans, then append named masks."""
    if len(original) < 24 or len(original) > 64 * 1024**2:
        raise ValueError('Invalid original UI image bank')
    header = list(struct.unpack_from('<6I', original)); count = header[3]
    end = 24 + 40 * count
    if header != [0, 1, 0, count, 0, 0] or not 1 <= count <= 4096 or end > len(original):
        raise ValueError('Unsupported original UI image table')
    records, names, previous = [], set(), end - 1
    for i in range(count):
        raw, offset, marker = struct.unpack_from('<32sII', original, 24 + i * 40)
        name = raw.split(b'\0', 1)[0].decode('ascii')
        if not name or name in names or not previous < offset <= len(original) - 16:
            raise ValueError('Invalid original UI image entry')
        records.append((raw, offset, marker)); names.add(name); previous = offset
    if not additions or count + 4 * len(additions) > 4096 or records[0][1] != end:
        raise ValueError('Invalid silhouette additions or original image gap')
    extra = []
    for resource, data in sorted(additions.items()):
        if not re.fullmatch(r'c[0-9a-f]{12}', resource):
            raise ValueError('Invalid additional chassis image identity')
        pixels = mask(data)
        for state, color in COLORS.items():
            name = 'icon_' + resource + '_' + state
            if name in names: raise ValueError('Additional silhouette collides with original artwork')
            names.add(name); extra.append((name.encode().ljust(32, b'\0'), image(pixels, color)))
    shift = 40 * len(extra); header[3] += len(extra)
    table = bytearray(struct.pack('<6I', *header))
    for raw, offset, marker in records: table += struct.pack('<32sII', raw, offset + shift, marker)
    payload = bytearray(original[end:]); offset = len(original) + shift
    for raw, data in extra:
        table += struct.pack('<32sII', raw, offset, 0xffffffff)
        payload += data; offset += len(data)
    return bytes(table + payload)
