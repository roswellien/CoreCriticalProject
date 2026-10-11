"""Independent bounded AMD64 physical exports and emitted runtime identities.

This reader has no capture/archive dependency and never calls a native API.
An emitted identity remains evidence from the producing reader; the physical
named/forwarded RVA and file identity are independently established here.
"""
import hashlib
import struct
from pathlib import Path


def need(value, message):
    if not value:
        raise ValueError(message)


class Exports:
    def __init__(self, path, digest, pin):
        self.path = pin(Path(path), digest)
        self.raw = self.path.read_bytes()
        need(len(self.raw) <= 128 * 1024 * 1024, 'Bounded physical native PE')
        need(self.raw[:2] == b'MZ', 'Physical native DOS header')
        pe = self.u32(0x3c)
        need(self.part(pe, 4) == b'PE\0\0', 'Physical native PE header')
        need(self.u16(pe + 4) == 0x8664, 'Physical native AMD64 machine')
        optional = pe + 24
        optional_size = self.u16(pe + 20)
        need(optional_size >= 120 and self.u16(optional) == 0x20b,
             'Physical native PE32+ optional header')
        self.image_size = self.u32(optional + 56)
        self.headers_size = self.u32(optional + 60)
        self.directory, self.directory_size = self.u32(optional + 112), self.u32(optional + 116)
        count = self.u16(pe + 6)
        need(0 < count <= 96 and self.directory and self.directory_size >= 40,
             'Bounded physical native section/export tables')
        self.sections = []
        table = optional + optional_size
        for index in range(count):
            offset = table + index * 40
            virtual_size, address, raw_size, raw_offset = self.unpack('<4I', offset + 8)
            flags = self.u32(offset + 36)
            need(raw_offset + raw_size <= len(self.raw) and
                 address + max(virtual_size, raw_size) <= self.image_size,
                 'Bounded physical native section')
            self.sections.append((address, raw_size, raw_offset, flags))
        export = self.at(self.directory, 40)
        self.function_count = self.u32(export + 20)
        self.name_count = self.u32(export + 24)
        self.functions, self.names, self.ordinals = self.unpack('<3I', export + 28)
        need(0 < self.function_count <= 65536 and 0 < self.name_count <= 65536,
             'Bounded physical named exports')
        self.name_map = {}
        for index in range(self.name_count):
            name = self.text(self.u32(self.at(self.names + 4 * index, 4)))
            ordinal = self.u16(self.at(self.ordinals + 2 * index, 2))
            need(ordinal < self.function_count and name not in self.name_map,
                 'Unique physical export name and bounded ordinal index')
            self.name_map[name] = ordinal

    def part(self, offset, length):
        need(0 <= offset <= len(self.raw) and 0 <= length <= len(self.raw) - offset,
             'Bounded physical PE read')
        return self.raw[offset:offset + length]

    def unpack(self, pattern, offset):
        return struct.unpack(pattern, self.part(offset, struct.calcsize(pattern)))

    def u16(self, offset):
        return self.unpack('<H', offset)[0]

    def u32(self, offset):
        return self.unpack('<I', offset)[0]

    def at(self, address, length=1):
        if address < self.headers_size and address + length <= self.headers_size:
            self.part(address, length)
            return address
        hits = [raw + address - start for start, size, raw, flags in self.sections
                if start <= address and address + length <= start + size]
        need(len(hits) == 1, 'Unique file-backed physical native RVA')
        self.part(hits[0], length)
        return hits[0]

    def text(self, address):
        start = self.at(address)
        end = self.raw.find(b'\0', start, min(start + 4096, len(self.raw)))
        need(end >= start, 'Terminated bounded physical export text')
        self.at(address, end - start + 1)
        return self.raw[start:end].decode('ascii')

    def named(self, name):
        need(name in self.name_map, 'Actual requested named export exists')
        address = self.u32(self.at(self.functions + 4 * self.name_map[name], 4))
        need(address and address < self.image_size, 'Physical export lies inside image')
        if self.directory <= address < self.directory + self.directory_size:
            return address, self.text(address)
        need(any(start <= address < start + size and flags & 0x20000000
                 for start, size, raw, flags in self.sections),
             'Direct physical export lies in executable file-backed section')
        return address, ''


FORWARDS = {
    'HeapAlloc': 'RtlAllocateHeap', 'HeapSize': 'RtlSizeHeap',
    'HeapReAlloc': 'RtlReAllocateHeap',
    'InitializeCriticalSection': 'RtlInitializeCriticalSection',
    'EnterCriticalSection': 'RtlEnterCriticalSection',
    'LeaveCriticalSection': 'RtlLeaveCriticalSection',
    'DeleteCriticalSection': 'RtlDeleteCriticalSection',
}


def identity(words, module_path, module_sha, pin):
    need(len(words) == 11, 'Complete emitted actual 11Q native identity')
    address, named, owner, owner_named, base, size, allocation, state, kind, protect, alloc_protect = words
    need(address == named == owner_named and owner == allocation and
         base <= address < base + size and state == 0x1000 and kind == 0x1000000 and
         not protect & 0x101 and protect & 0xf0 and address > 0xffffffff,
         'Full-width actual named target is committed executable owner image')
    need(len(module_sha) == 64, 'Actual emitted module SHA256 extent')
    pin(module_path, module_sha)
    return address, owner, str(module_path), module_sha


def exported(raw, ident, requested, pin, cache):
    need(len(raw) == 4624, 'Complete emitted actual named/owner export witness')
    version, named_base, target, named, owner, owner_named = struct.unpack_from('<6Q', raw)
    def text(offset, length, codec='ascii'):
        part = raw[offset:offset + length]
        if codec == 'utf-16-le':
            need(len(part) % 2 == 0, 'Exact UTF16 module path extent')
            return part.decode(codec).split('\0', 1)[0]
        return part.split(b'\0', 1)[0].decode(codec)
    wanted, forward, alias = text(48, 32), text(80, 256), text(336, 64)
    named_sha, owner_sha = raw[400:464].decode('ascii'), raw[464:528].decode('ascii')
    named_path, owner_path = text(528, 2048, 'utf-16-le'), text(2576, 2048, 'utf-16-le')
    need(version == 1 and wanted == requested and target == named == owner_named == ident[0]
         and owner == ident[1] and owner_path == ident[2] and owner_sha == ident[3],
         'Whole emitted export witness joins exact actual identity')
    def physical(path, digest):
        key = str(path), digest
        if key not in cache:
            cache[key] = Exports(path, digest, pin)
        else:
            pin(path, digest)
        return cache[key]
    named_image, owner_image = physical(named_path, named_sha), physical(owner_path, owner_sha)
    named_rva, physical_forward = named_image.named(requested)
    need(forward == physical_forward, 'Literal physical export forwarding text')
    if forward:
        need(requested in FORWARDS and forward == 'NTDLL.' + FORWARDS[requested]
             and alias == FORWARDS[requested] and Path(owner_path).name.lower() == 'ntdll.dll',
             'Exact admitted native NTDLL forwarding name/alias/owner')
    else:
        need(alias == requested and named_base == owner and named_base + named_rva == target,
             'Direct physical native export RVA resolves full-width actual target')
    owner_rva, owner_forward = owner_image.named(alias)
    need(not owner_forward and owner + owner_rva == target,
         'Direct physical owning export RVA resolves same full-width actual target')
    return dict(requested=requested, target=target, named_module=named_path,
                named_sha256=named_sha, named_RVA=named_rva, forwarder=forward,
                owning_module=owner_path, owning_sha256=owner_sha, owning_alias=alias,
                owning_RVA=owner_rva, complete_witness_sha256=hashlib.sha256(raw).hexdigest())
