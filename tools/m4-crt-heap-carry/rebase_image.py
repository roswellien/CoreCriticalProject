"""Rebase a 32-bit PE image the way the Windows loader relocates a DLL whose preferred base is taken.

Applies every IMAGE_REL_BASED_HIGHLOW (type 3) base relocation with delta = new_base - preferred_base,
skips IMAGE_REL_BASED_ABSOLUTE padding, refuses any other relocation type, and sets OptionalHeader.ImageBase.
The output is derived from original code and stays local (never commit it).
Usage: python -B rebase_image.py INPUT.dll OUTPUT.dll NEW_BASE_HEX
"""
import struct
import sys
from pathlib import Path


def rebase(data: bytes, new_base: int) -> bytes:
    b = bytearray(data)
    pe = struct.unpack_from('<I', b, 0x3c)[0]
    opt = pe + 24
    if struct.unpack_from('<H', b, opt)[0] != 0x10b:
        raise SystemExit('PE32 image required')
    old_base = struct.unpack_from('<I', b, opt + 28)[0]
    delta = (new_base - old_base) & 0xffffffff
    count = struct.unpack_from('<H', b, pe + 6)[0]
    soh = struct.unpack_from('<H', b, pe + 20)[0]
    sections = [struct.unpack_from('<IIII', b, opt + soh + 40 * i + 8) for i in range(count)]

    def offset(rva):
        for vsize, va, rawsize, raw in sections:
            if va <= rva < va + max(vsize, rawsize):
                if rva - va >= rawsize:
                    raise SystemExit('Relocation target outside raw data: 0x%x' % rva)
                return raw + rva - va
        raise SystemExit('RVA outside sections: 0x%x' % rva)

    reloc_rva, reloc_size = struct.unpack_from('<II', b, opt + 96 + 5 * 8)
    if not reloc_rva:
        raise SystemExit('Image has no base relocations')
    pos, end, applied = offset(reloc_rva), offset(reloc_rva) + reloc_size, 0
    while pos < end:
        page, block = struct.unpack_from('<II', b, pos)
        if block < 8:
            break
        for k in range((block - 8) // 2):
            entry = struct.unpack_from('<H', b, pos + 8 + 2 * k)[0]
            kind, off = entry >> 12, entry & 0xfff
            if kind == 0:
                continue
            if kind != 3:
                raise SystemExit('Unsupported relocation type %d' % kind)
            at = offset(page + off)
            struct.pack_into('<I', b, at, (struct.unpack_from('<I', b, at)[0] + delta) & 0xffffffff)
            applied += 1
        pos += block
    struct.pack_into('<I', b, opt + 28, new_base)
    print('rebased 0x%x -> 0x%x: %d relocations' % (old_base, new_base, applied))
    return bytes(b)


if __name__ == '__main__':
    src, dst, base = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3], 16)
    if dst.exists():
        raise SystemExit('Fresh output required')
    dst.write_bytes(rebase(Path(src).read_bytes(), base))
