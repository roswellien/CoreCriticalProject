"""Rebase admitted original decoder data without loading or executing the DLL."""
import hashlib
import struct

from translate import need

SOURCE_SHA256 = '56760e0ea8c8709f4a0c34bee7289a87188aedd8bddfd05f8f62bee2f3f91238'
OUTPUT_SHA256 = '9d066dbdb0b9903c2afb07284d609c7d3ed3278245040490e9805d4cd717958f'


def rebase(source):
    need(hashlib.sha256(source).hexdigest() == SOURCE_SHA256, 'Unsupported original decoder')
    image = bytearray(source)

    def read(offset, count, fmt):
        need(0 <= offset <= len(image)-count, 'Decoder PE range is unbacked')
        return struct.unpack_from(fmt, image, offset)[0]

    u16 = lambda p: read(p, 2, '<H')
    u32 = lambda p: read(p, 4, '<I')
    need(u16(0) == 0x5a4d, 'Decoder MZ header missing')
    pe = u32(0x3c)
    need(u32(pe) == 0x4550 and u16(pe+4) == 0x14c, 'Decoder must be PE32 x86')
    optional, optional_size, sections = pe+24, u16(pe+20), u16(pe+6)
    need(optional_size >= 144 and u16(optional) == 0x10b and u32(optional+92) >= 6 and 1 <= sections <= 96,
         'Incomplete decoder relocation headers')
    table = optional+optional_size
    need(table+40*sections <= len(image), 'Decoder section table truncated')

    def offset(address, count):
        matches = []
        for i in range(sections):
            row = table+40*i
            start, size, raw = u32(row+12), u32(row+16), u32(row+20)
            if start <= address and address-start+count <= size:
                position = raw+address-start
                need(position+count <= len(image), 'Decoder relocation outside raw data')
                matches.append(position)
        need(len(matches) == 1, 'Decoder relocation must have one backed section')
        return matches[0]

    rva, size = u32(optional+136), u32(optional+140)
    need(rva > 0 and size > 0, 'Decoder relocation directory missing')
    position = offset(rva, size)
    end = position+size
    delta = (0x11000000-u32(optional+28)) & 0xffffffff
    while position < end:
        need(end-position >= 8, 'Truncated decoder relocation block')
        page, block = u32(position), u32(position+4)
        if not page and not block and not any(image[position:end]):
            break
        need(8 <= block <= end-position and block % 2 == 0, 'Invalid decoder relocation block')
        for index in range(8, block, 2):
            entry = u16(position+index)
            kind = entry >> 12
            if kind == 0:
                continue
            need(kind == 3 and page+(entry & 0xfff) <= 0xffffffff, 'Unsupported decoder relocation')
            target = offset(page+(entry & 0xfff), 4)
            struct.pack_into('<I', image, target, (u32(target)+delta) & 0xffffffff)
        position += block
    struct.pack_into('<I', image, optional+28, 0x11000000)
    need(hashlib.sha256(image).hexdigest() == OUTPUT_SHA256, 'Generated decoder identity mismatch')
    return bytes(image)
