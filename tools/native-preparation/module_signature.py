"""Attach a pinned public Authenticode certificate to exact locally generated code.

Only certificate bytes and the two Authenticode-excluded header fields travel
in the source kit. No executable section bytes or publisher credentials do.
Windows validates the resulting signature; the signed source manifest pins both
the unsigned input and complete signed output hashes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import uuid


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fields(data):
    need(len(data) >= 256 and data[:2] == b'MZ', 'PE image required')
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    need(pe + 264 <= len(data) and data[pe:pe+4] == b'PE\0\0', 'Invalid PE headers')
    need(struct.unpack_from('<H', data, pe+4)[0] == 0x8664, 'AMD64 module required')
    optional = pe + 24
    need(struct.unpack_from('<H', data, optional)[0] == 0x20b, 'PE32+ module required')
    need(struct.unpack_from('<I', data, optional+108)[0] >= 5, 'Missing security directory')
    return optional + 64, optional + 112 + 4*8


def certificates(data):
    need(8 <= len(data) <= 2*1024**2, 'Bounded certificate table required')
    offset = 0
    while offset < len(data):
        need(offset+8 <= len(data), 'Truncated certificate')
        size, revision, kind = struct.unpack_from('<IHH', data, offset)
        need(size >= 8 and offset+size <= len(data) and revision == 0x200 and kind == 2,
             'Only PKCS signed-data certificates are supported')
        offset += (size+7) & ~7
    need(offset == len(data), 'Certificate alignment mismatch')


def export_signature(unsigned, signed, output):
    before = Path(unsigned).read_bytes(); after = Path(signed).read_bytes()
    checksum, security = fields(before)
    need(fields(after) == (checksum, security), 'Signing changed the PE layout')
    need(before[security:security+8] == b'\0'*8, 'Expected an unsigned input')
    offset, size = struct.unpack_from('<II', after, security)
    need(offset == (len(before)+7) & ~7 and len(after) == offset+size, 'Only an appended certificate is permitted')
    copy = bytearray(after[:len(before)])
    copy[checksum:checksum+4] = before[checksum:checksum+4]
    copy[security:security+8] = before[security:security+8]
    need(bytes(copy) == before and after[len(before):offset] == b'\0'*(offset-len(before)),
         'Signing changed executable bytes')
    blob = after[offset:]
    certificates(blob)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output/'module-certificates.bin').write_bytes(blob)
    metadata = dict(contract='mw3-detached-authenticode-v1', unsigned_sha256=digest(before),
        signed_sha256=digest(after), unsigned_bytes=len(before), certificate_sha256=digest(blob),
        checksum=after[checksum:checksum+4].hex(), unsigned_checksum=before[checksum:checksum+4].hex())
    (output/'module-signature.json').write_text(json.dumps(metadata, indent=2)+'\n')
    return metadata


def recover_unsigned(module, metadata):
    """Reuse identical generated code even when the previous release's signature differs."""
    try:
        module = Path(module)
        length = metadata['unsigned_bytes']
        need(length <= module.stat().st_size <= length+2*1024**2+7, 'Unexpected previous module size')
        data = module.read_bytes()
        if digest(data) == metadata['unsigned_sha256']:
            return data
        checksum, security = fields(data)
        offset, size = struct.unpack_from('<II', data, security)
        need(offset == (length+7)&~7 and len(data) == offset+size, 'Unexpected previous signature framing')
        certificates(data[offset:])
        original_checksum = bytes.fromhex(metadata['unsigned_checksum'])
        need(len(original_checksum) == 4, 'Invalid original checksum')
        before = bytearray(data[:length])
        before[checksum:checksum+4] = original_checksum
        before[security:security+8] = b'\0'*8
        need(digest(before) == metadata['unsigned_sha256'], 'Previous native code differs from this release')
        return bytes(before)
    except (OSError, ValueError, KeyError, struct.error):
        return None


def apply_signature(module, metadata, certificate, scratch_directory=None):
    module = Path(module)
    data = module.read_bytes()
    need(metadata['contract'] == 'mw3-detached-authenticode-v1' and
         len(data) == metadata['unsigned_bytes'] and digest(data) == metadata['unsigned_sha256'],
         'Generated module differs from the signed release')
    checksum, security = fields(data)
    need(data[security:security+8] == b'\0'*8, 'Generated module already has a signature')
    blob = Path(certificate).read_bytes()
    need(digest(blob) == metadata['certificate_sha256'], 'Certificate payload changed')
    certificates(blob)
    checksum_bytes = bytes.fromhex(metadata['checksum'])
    need(len(checksum_bytes) == 4, 'Invalid checksum field')
    result = bytearray(data)
    result[checksum:checksum+4] = checksum_bytes
    offset = (len(result)+7) & ~7
    result[security:security+8] = struct.pack('<II', offset, len(blob))
    result.extend(b'\0'*(offset-len(result)))
    result.extend(blob)
    need(digest(result) == metadata['signed_sha256'], 'Signed native module identity mismatch')
    scratch = Path(scratch_directory) if scratch_directory else module.parent
    temp = scratch / ('module-signing-'+uuid.uuid4().hex+'.tmp')
    with temp.open('xb') as stream:
        stream.write(result)
    os.replace(temp, module)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--unsigned', type=Path, required=True)
    parser.add_argument('--signed', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(export_signature(args.unsigned, args.signed, args.output))
