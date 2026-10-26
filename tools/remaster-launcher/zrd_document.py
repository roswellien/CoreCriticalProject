"""Bounded MW3 typed reader documents for authored content definitions.

Lists store their element count plus one; they have no serialized terminator.
The original reader represents an empty list as null. This codec preserves
integer versus float words and raw single-byte text. It supplies data to the
original definition reader; it does not construct guest objects or grant new
runtime chassis support.
"""
import math
import struct

MAX_BYTES = 4 * 1024 * 1024
MAX_NODES = 65536
MAX_DEPTH = 64


def decode(data):
    if len(data) > MAX_BYTES:
        raise ValueError('Reader document exceeds byte limit')
    position = 0
    nodes = 0

    def take(size):
        nonlocal position
        if size > len(data) - position:
            raise ValueError('Truncated reader document')
        value = data[position:position + size]
        position += size
        return value

    def read(depth):
        nonlocal nodes
        nodes += 1
        if nodes > MAX_NODES or depth > MAX_DEPTH:
            raise ValueError('Reader document exceeds node/depth limit')
        kind, word = struct.unpack('<II', take(8))
        if kind == 1:
            return struct.unpack('<i', struct.pack('<I', word))[0]
        if kind == 2:
            value = struct.unpack('<f', struct.pack('<I', word))[0]
            if not math.isfinite(value):
                raise ValueError('Nonfinite reader float')
            return value
        if kind == 3:
            value = take(word)
            if b'\0' in value:
                raise ValueError('Embedded null in reader string')
            return value.decode('latin1')
        if kind == 4:
            if not 1 <= word <= MAX_NODES - nodes + 1:
                raise ValueError('Invalid reader list count')
            return [read(depth + 1) for _ in range(word - 1)] if word > 1 else None
        raise ValueError('Unknown reader node type')

    result = read(0)
    if position != len(data):
        raise ValueError('Trailing reader data')
    return result


def encode(document):
    result = bytearray()
    nodes = 0

    def write(value, depth):
        nonlocal nodes
        nodes += 1
        if nodes > MAX_NODES or depth > MAX_DEPTH:
            raise ValueError('Reader document exceeds node/depth limit')
        if value is None:
            result.extend(struct.pack('<II', 4, 1))
        elif type(value) is list:
            if len(value) >= MAX_NODES:
                raise ValueError('Invalid reader list count')
            result.extend(struct.pack('<II', 4, len(value) + 1))
            for child in value:
                write(child, depth + 1)
        elif type(value) is int:
            if not -(2**31) <= value < 2**31:
                raise ValueError('Reader integer is outside signed 32-bit range')
            result.extend(struct.pack('<Ii', 1, value))
        elif type(value) is float:
            if not math.isfinite(value):
                raise ValueError('Nonfinite reader float')
            try:
                result.extend(struct.pack('<If', 2, value))
            except OverflowError as exc:
                raise ValueError('Reader float is outside 32-bit range') from exc
        elif type(value) is str:
            try:
                raw = value.encode('latin1')
            except UnicodeEncodeError as exc:
                raise ValueError('Reader text requires single-byte characters') from exc
            if b'\0' in raw or len(raw) > MAX_BYTES:
                raise ValueError('Invalid reader string')
            result.extend(struct.pack('<II', 3, len(raw)))
            result.extend(raw)
        else:
            raise ValueError('Unsupported reader value type')
        if len(result) > MAX_BYTES:
            raise ValueError('Reader document exceeds byte limit')

    write(document, 0)
    return bytes(result)
