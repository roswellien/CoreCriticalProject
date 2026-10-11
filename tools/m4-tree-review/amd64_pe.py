"""Minimal bounded AMD64 PE image reader for physical linked-byte review."""
import struct


class PEImage:
    def __init__(self, data):
        self.data = data
        assert data[:2] == b'MZ'
        nt = struct.unpack_from('<I', data, 60)[0]
        assert data[nt:nt + 4] == b'PE\0\0'
        self.machine, count, _, _, _, optional, _ = struct.unpack_from('<HHIIIHH', data, nt + 4)
        assert self.machine == 0x8664 and optional >= 112
        opt = nt + 24
        assert struct.unpack_from('<H', data, opt)[0] == 0x20b
        self.image_base = struct.unpack_from('<Q', data, opt + 24)[0]
        self.sections = []
        for index in range(count):
            start = opt + optional + index * 40
            virtual_size, virtual_address, size, raw = struct.unpack_from('<IIII', data, start + 8)
            flags = struct.unpack_from('<I', data, start + 36)[0]
            assert raw + size <= len(data)
            self.sections.append(dict(virtual_address=virtual_address, virtual_size=virtual_size,
                                      raw_offset=raw, raw_size=size, executable=bool(flags & 0x20000000)))

    def rva_range(self, rva, size):
        for section in self.sections:
            relative = rva - section['virtual_address']
            if 0 <= relative and relative + size <= section['raw_size']:
                start = section['raw_offset'] + relative
                return start, section['raw_offset'] + section['raw_size']
        raise ValueError(('No complete physical AMD64 RVA backing', rva, size))
