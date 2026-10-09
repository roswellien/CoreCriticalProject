"""Independent serialized native API association checks; no guest execution.

Disk exports/RX sections associate recorded ASLR-relative targets with the
recorded file hash. This does not attest the past process's loaded image bytes.
"""
from pathlib import Path
import hashlib, struct

API_BYTES, MODULE_BYTES, LOOKUP_BYTES = 2184, 2160, 6556
LOOKUPS_OFFSET, RECORD_BYTES = 88072, 107740
NAMES = ('GetModuleHandleA', 'GetProcAddress', 'IsProcessorFeaturePresent')
TOKENS = (0x11001000, 0x11000300, 0x11000300)

def need(ok, reason):
    if not ok:
        raise ValueError(reason)

def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

class DiskPE:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.bytes = self.path.read_bytes()
        b = self.bytes
        need(len(b) <= 32 * 1024 * 1024 and b[:2] == b'MZ', 'Bounded host PE')
        pe = self.u32(0x3c)
        need(b[pe:pe+4] == b'PE\0\0', 'Host PE signature')
        machine, count, _, _, _, opt_size, flags = struct.unpack_from('<HHIIIHH', b, pe+4)
        o = pe + 24
        need(machine == 0x8664 and self.u16(o) == 0x20b and flags & 0x2000,
             'Actual AMD64 host DLL image')
        self.size = self.u32(o+56)
        self.header_bytes = self.u32(o+60)
        need(self.u32(o+108) >= 1 and opt_size >= 120, 'Host export directory')
        self.export_rva, self.export_size = struct.unpack_from('<II', b, o+112)
        self.sections = []
        for i in range(count):
            s = o + opt_size + i*40
            virtual_bytes, rva, file_bytes, file_offset = struct.unpack_from('<4I', b, s+8)
            rights = self.u32(s+36)
            need(file_offset+file_bytes <= len(b), 'Host section file bound')
            self.sections.append((rva, virtual_bytes, file_offset, file_bytes, rights))
        e = self.offset(self.export_rva, 40)
        _, _, _, _, _, ordinal, functions, names, address_table, name_table, ordinal_table = \
            struct.unpack_from('<IIHHIIIIIII', b, e)
        need(functions <= 65536 and names <= 65536, 'Bounded named host exports')
        self.exports = {}
        for i in range(names):
            name_rva = self.u32(self.offset(name_table+i*4, 4))
            name = self.string(name_rva)
            index = self.u16(self.offset(ordinal_table+i*2, 2))
            need(index < functions and name not in self.exports, 'Unique host export name')
            target = self.u32(self.offset(address_table+index*4, 4))
            value = self.string(target) if self.export_rva <= target < self.export_rva+self.export_size else target
            self.exports[name] = value
        self.sha = hashlib.sha256(b).hexdigest()

    def u16(self, o):
        need(o >= 0 and o+2 <= len(self.bytes), 'PE word bound')
        return struct.unpack_from('<H', self.bytes, o)[0]

    def u32(self, o):
        need(o >= 0 and o+4 <= len(self.bytes), 'PE DWORD bound')
        return struct.unpack_from('<I', self.bytes, o)[0]

    def offset(self, rva, width):
        if rva+width <= self.header_bytes and rva+width <= len(self.bytes):
            return rva
        candidates = [file_offset+rva-start for start, _, file_offset, file_bytes, _ in self.sections
                      if start <= rva and rva+width <= start+file_bytes]
        need(len(candidates) == 1, 'Unique host file-backed RVA')
        return candidates[0]

    def string(self, rva):
        o = self.offset(rva, 1)
        end = self.bytes.find(b'\0', o, min(len(self.bytes), o+65536))
        need(end >= o, 'Bounded host export string')
        return self.bytes[o:end].decode('ascii')

    def executable(self, rva):
        candidates = [s for s in self.sections if s[0] <= rva < s[0]+s[1]]
        need(len(candidates) == 1 and candidates[0][4] & 0x60000000 == 0x60000000,
             'Named target owns one host RX section')
        self.offset(rva, 1)

class APIModel:
    def __init__(self):
        self.images = {}
        self.image_pins = {}
        self.records = 0

    def image(self, path, sha):
        p = str(Path(path).resolve())
        if p not in self.images:
            self.images[p] = DiskPE(p)
        image = self.images[p]
        need(image.sha == sha, 'Recorded host owner disk SHA identity')
        self.image_pins[p] = sha
        return image

    @staticmethod
    def text(b):
        need(len(b) == 2048, 'Serialized path extent')
        words = struct.unpack('<1024H', b)
        need(0 in words, 'Serialized path termination')
        n = words.index(0)
        need(n and not any(words[n:]), 'Serialized path has owned zero tail')
        return b[:2*n].decode('utf-16le')

    def module(self, b):
        need(len(b) == MODULE_BYTES, 'Module identity extent')
        handle, base, size, allocation, state, kind, protect, allocation_protect = \
            struct.unpack_from('<4Q4I', b)
        sha = b[48:112].decode('ascii')
        image = self.image(self.text(b[112:]), sha)
        need(handle and base == allocation == handle and size > 0 and
             state == 0x1000 and kind == 0x1000000 and
             not protect & 0x101 and image.path.name.casefold() == 'kernel32.dll',
             'Returned named borrowed KERNEL32 image identity')
        return handle, image

    def api(self, b, module, name):
        need(len(b) == API_BYTES, 'API identity extent')
        address, named, owner, owner_named, base, size, allocation, state, kind, protect, _ = \
            struct.unpack_from('<7Q4I', b)
        image = self.image(self.text(b[136:]), b[72:136].decode('ascii'))
        need(address and address == named == owner_named and owner == allocation and
             owner <= base <= address < base+size <= owner+image.size and
             state == 0x1000 and kind == 0x1000000 and not protect & 0x101 and
             protect & 0xf0, 'Recorded actual named executable target/region ownership')
        rva = address-owner
        need(image.exports.get(name) == rva, 'Owner exact case-sensitive named export RVA')
        image.executable(rva)
        module_base, module_image = module
        target = module_image.exports.get(name)
        if isinstance(target, int):
            need(module_image.sha == image.sha and module_base == owner and target == rva,
                 'Named issuing module direct export target association')
        else:
            need(isinstance(target, str) and '.' in target, 'Explicit named export forwarding')
            library, forwarded = target.rsplit('.', 1)
            need(library.casefold()+'.dll' == image.path.name.casefold() and forwarded == name,
                 'Recorded owner matches direct named forwarder')
        return address

    def record(self, b):
        need(len(b) == RECORD_BYTES, 'Independent complete record framing')
        need(struct.unpack_from('<3I', b, 16) == (97, 3, 3), 'Actual writer lookup extent')
        lookups = [b[LOOKUPS_OFFSET+i*LOOKUP_BYTES:LOOKUPS_OFFSET+(i+1)*LOOKUP_BYTES] for i in range(3)]
        modules = []
        addresses = []
        results = []
        for i, lookup in enumerate(lookups):
            kind, token, argument, result, last_error, host_result = struct.unpack_from('<5IQ', lookup)
            need(kind == i+1 and token == TOKENS[i] and argument == 0, 'Actual typed lookup identity')
            before = lookup[28:2212]
            after = lookup[2212:4396]
            need(before == after, 'Actual API before/after raw identity stable')
            module_bytes = lookup[4396:]
            module = self.module(module_bytes)
            addresses.append(self.api(before, module, NAMES[i]))
            modules.append(module_bytes)
            results.append((result, host_result))
        need(modules[0] == modules[1] == modules[2], 'Stable issuing borrowed module physical identity')
        module = self.module(modules[0])
        need(results[0] == (0, module[0]) and results[1] == (0, addresses[2]) and
             results[2][0] == results[2][1], 'Actual module/export/query output association')
        self.records += 1

    def stream(self, b):
        need(b[:8] == b'MW4FDIN2' and struct.unpack_from('<4I', b, 8) == (2, 24, RECORD_BYTES, 9)
             and len(b) == 24+24*RECORD_BYTES, 'Independent raw stream framing')
        for i in range(24):
            self.record(b[24+i*RECORD_BYTES:24+(i+1)*RECORD_BYTES])

    def controls(self, record):
        # Cause-specific coherent or isolated metadata changes, always fresh.
        controls = []
        def write(label, offset, value, fmt='<Q', second=None):
            x = bytearray(record)
            struct.pack_into(fmt, x, offset, value)
            if second is not None:
                struct.pack_into(fmt, x, second, value)
            controls.append((label, x))
        start = LOOKUPS_OFFSET
        api = start+28
        write('lookup kind', start, 4, '<I')
        write('unissued token', start+4, 0, '<I')
        write('wrong query argument', start+2*LOOKUP_BYTES+8, 1, '<I')
        write('module host result', start+20, 1)
        write('procedure host result', start+LOOKUP_BYTES+20, 1)
        write('query result distinction', start+2*LOOKUP_BYTES+12, 1, '<I')
        for label, field, value in [('named target',8,1), ('owner target',24,1),
                                     ('owner allocation',48,1), ('MEM_IMAGE',60,0),
                                     ('MEM_COMMIT',56,0), ('exec protection',64,4),
                                     ('guard protection',64,0x120), ('region extent',40,1)]:
            fmt = '<I' if field in (56,60,64) else '<Q'
            write(label, api+field, value, fmt, api+API_BYTES+field)
        for label, field in [('disk hash',72), ('path file',136)]:
            x = bytearray(record);x[api+field] ^= 1;x[api+API_BYTES+field] ^= 1;controls.append((label,x))
        addr = struct.unpack_from('<Q', record, api)[0]+1
        x = bytearray(record)
        for off in (api, api+API_BYTES):
            for field in (0,8,24):struct.pack_into('<Q',x,off+field,addr)
        controls.append(('coherent wrong named export RVA',x))
        write('returned module handle', start+4396, 1)
        write('returned module image kind', start+4396+36, 0, '<I')
        write('lookup count', 24, 2, '<I')
        rejected = []
        for label, x in controls:
            try:self.record(x)
            except (ValueError, UnicodeError, OSError):rejected.append(label)
            else:raise ValueError('Independent API observer accepted corruption: '+label)
        return rejected
