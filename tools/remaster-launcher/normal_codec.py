"""Lossless RGBA8 normal transport: channel deltas followed by bounded byte runs.

Each channel is predicted from its previous pixel (initially zero). Channels
are stored consecutively. Tokens 0..127 contain token+1 literal bytes; tokens
128..191 repeat the next byte (token&63)+1 times. Tokens 192..255 contain
(token&63)+1 signed four-bit deltas, high nibble first (unused low nibble zero).
No color conversion occurs.
"""


def encode(pixels):
    if not pixels or len(pixels) % 4:
        raise ValueError("Expected complete RGBA pixels")
    delta = bytearray(len(pixels))
    count = len(pixels) // 4
    for channel in range(4):
        previous = 0
        for index, value in enumerate(pixels[channel::4]):
            delta[channel * count + index] = (value - previous) & 255
            previous = value
    output = bytearray()
    cursor = 0
    while cursor < len(delta):
        run = 1
        while run < 64 and cursor + run < len(delta) and delta[cursor + run] == delta[cursor]:
            run += 1
        if run >= 3:
            output.extend((128 | (run - 1), delta[cursor]))
            cursor += run
            continue
        small = 0
        while small < 64 and cursor + small < len(delta):
            value = delta[cursor + small]
            if not (value < 8 or value >= 248):
                break
            if small and cursor + small + 2 < len(delta) and delta[cursor + small] == delta[cursor + small + 1] == delta[cursor + small + 2]:
                break
            small += 1
        if small >= 4:
            output.append(192 | (small - 1))
            for i in range(0, small, 2):
                high = delta[cursor + i] & 15
                low = delta[cursor + i + 1] & 15 if i + 1 < small else 0
                output.append(high << 4 | low)
            cursor += small
            continue
        start = cursor
        cursor += 1
        while cursor - start < 128 and cursor < len(delta):
            if cursor + 2 < len(delta) and delta[cursor] == delta[cursor + 1] == delta[cursor + 2]:
                break
            if cursor + 3 < len(delta) and all(v < 8 or v >= 248 for v in delta[cursor:cursor + 4]):
                break
            cursor += 1
        output.append(cursor - start - 1)
        output.extend(delta[start:cursor])
    return bytes(output)


def decode(encoded, pixel_bytes):
    if not pixel_bytes or pixel_bytes % 4 or pixel_bytes > 256 * 1024**2:
        raise ValueError("Invalid decoded normal size")
    if not encoded or len(encoded) > pixel_bytes * 2:
        raise ValueError("Invalid encoded normal size")
    delta = bytearray()
    cursor = 0
    while cursor < len(encoded):
        token = encoded[cursor]
        cursor += 1
        count = (token & (63 if token & 128 else 127)) + 1
        if len(delta) + count > pixel_bytes:
            raise ValueError("Normal run exceeds decoded size")
        if token >= 192:
            packed_count = (count + 1) // 2
            if cursor + packed_count > len(encoded):
                raise ValueError("Truncated normal nibble deltas")
            if count % 2 and encoded[cursor + packed_count - 1] & 15:
                raise ValueError("Nonzero normal nibble padding")
            for i in range(count):
                value = (encoded[cursor + i // 2] >> (0 if i % 2 else 4)) & 15
                delta.append(value if value < 8 else value + 240)
            cursor += packed_count
        elif token & 128:
            if cursor == len(encoded):
                raise ValueError("Truncated normal repeat")
            delta.extend(bytes([encoded[cursor]]) * count)
            cursor += 1
        else:
            if cursor + count > len(encoded):
                raise ValueError("Truncated normal literal")
            delta.extend(encoded[cursor:cursor + count])
            cursor += count
    if len(delta) != pixel_bytes:
        raise ValueError("Incomplete normal pixels")
    output = bytearray(pixel_bytes)
    count = pixel_bytes // 4
    for channel in range(4):
        previous = 0
        for index, value in enumerate(delta[channel * count:(channel + 1) * count]):
            previous = (previous + value) & 255
            output[index * 4 + channel] = previous
    return bytes(output)
