"""Append authored definition members to a copy of an original MW3 reader ZBD.

Existing payload bytes, directory order and per-record metadata are preserved.
No original member may be replaced. Output is local derived game data and must
remain outside version control. Native original parsing remains authoritative.
"""
import re
import struct

from zrd_document import decode

RECORD_BYTES = 148
MAX_BYTES = 64 * 1024**2


def _directory(data):
    if not 8 <= len(data) <= MAX_BYTES:
        raise ValueError('Invalid reader archive size')
    version, count = struct.unpack_from('<II', data, len(data) - 8)
    start = len(data) - 8 - count * RECORD_BYTES
    if version != 1 or not 1 <= count <= 4096 or start < 0:
        raise ValueError('Invalid reader archive directory')
    records, names = [], set()
    for i in range(count):
        record = data[start + i * RECORD_BYTES:start + (i + 1) * RECORD_BYTES]
        offset, size = struct.unpack_from('<II', record)
        field = record[8:72]
        end = field.find(b'\0')
        if end < 1:
            raise ValueError('Unterminated reader member name')
        try:
            name = field[:end].decode('ascii')
        except UnicodeDecodeError as exc:
            raise ValueError('Invalid reader member name') from exc
        if name.casefold() in names or offset > start or size > start - offset:
            raise ValueError('Colliding or out-of-range reader member')
        names.add(name.casefold())
        records.append((name, offset, size, record))
    return start, records


def add_definitions(original, definitions, *, metadata_template='dfn_madcat.zrd'):
    """Return a new archive. Names and document bytes are supplied by the caller."""
    if not isinstance(definitions, dict) or not 1 <= len(definitions) <= 128:
        raise ValueError('Expected 1..128 authored definitions')
    start, records = _directory(original)
    by_name = {name.casefold(): record for name, _, _, record in records}
    if metadata_template not in by_name:
        raise ValueError('Missing definition directory metadata template')
    if len(records) + len(definitions) > 4096:
        raise ValueError('Reader directory exceeds limit')
    result = bytearray(original[:start])
    added = []
    for name, payload in sorted(definitions.items()):
        if (not isinstance(name, str) or not re.fullmatch(r'dfn_[a-z0-9][a-z0-9._-]{0,23}\.zrd', name)
                or name.casefold() in by_name or not isinstance(payload, bytes)):
            raise ValueError('Colliding or invalid authored definition')
        decode(payload)  # Reject malformed typed documents before composing media.
        record = bytearray(by_name[metadata_template])
        struct.pack_into('<II', record, 0, len(result), len(payload))
        encoded = name.encode('ascii')
        record[8:72] = encoded + bytes(64 - len(encoded))
        added.append(record)
        result.extend(payload)
    for _, _, _, record in records:
        result.extend(record)
    for record in added:
        result.extend(record)
    result.extend(struct.pack('<II', 1, len(records) + len(added)))
    if len(result) > MAX_BYTES:
        raise ValueError('Composed reader archive exceeds size limit')
    _directory(result)
    return bytes(result)


def add_members(original, additions):
    """Append named data using an existing member's opaque directory metadata."""
    start, records = _directory(original)
    known = {name.casefold(): record for name, _, _, record in records}
    if not additions or len(records) + len(additions) > 4096:
        raise ValueError('Invalid additional archive member count')
    output = bytearray(original[:start])
    extra = []
    for name, (data, template) in sorted(additions.items()):
        if (not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{0,62}', name) or name in known
                or template not in known or not isinstance(data, bytes)):
            raise ValueError('Colliding or unsupported archive addition')
        record = bytearray(known[template])
        struct.pack_into('<II', record, 0, len(output), len(data))
        record[8:72] = name.encode('ascii').ljust(64, b'\0')
        output.extend(data)
        extra.append(record)
    for _, _, _, record in records:
        output.extend(record)
    for record in extra:
        output.extend(record)
    output.extend(struct.pack('<II', 1, len(records) + len(extra)))
    _directory(output)
    return bytes(output)
