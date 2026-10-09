"""Original-byte sizing-prefix interpreter; no native AFTER expectation seed.

This gate ends before reading locale classification. Logical AF representatives
match the separately declared concrete translation policy; they do not assert
original x86 values for architecturally undefined flags.
"""
import copy
import struct
from consumer import F, M, OLD, STATE_REG

BEGIN = 0x7800bc48
TABLE = 0x780379e1
BUFFER = 0x33000000
SIZE = 436
SOURCE_SHA = 'b372b4c114b8ecb170208ad508f2541c73262c3b44cfa2e7626e06a5be61fd8b'


def source_material(out):
    provider_path = F.pin(F.ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',
                         '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    provider = M.N.PE.PEImage(provider_path.read_bytes())
    tool = F.pin(F.ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe',
                 'a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
    program, command = M.D.E.decode(tool, provider, provider_path, BEGIN, BEGIN + SIZE,
                                   out, 'parser-prefix-original-source')
    F.require(program[0x7800bce6] == (7, 'test', ['byte ptr [ebx + 0x780379e1]', '0x4']),
              'Original nonquoted first locale classification instruction')
    F.require(program[0x7800bc87] == (7, 'test', ['byte ptr [edx + 0x780379e1]', '0x4']),
              'Original quoted first locale classification instruction')
    return program, command


def predict(entry, program, host_bytes, deny_before=None):
    state, memory = bytearray(entry.state), copy.deepcopy(entry.mem)
    fx, cpu = bytes(entry.fx), bytes(entry.runtime_cpu)
    r = {name: struct.unpack_from('<I', state, off)[0] for name, off in STATE_REG.items()}
    flags = struct.unpack_from('<I', M.D.cpu(state), 32)[0]
    pc, accesses, pcs, phases = BEGIN, [], [], {}
    if not host_bytes or len(host_bytes) > 131072 or host_bytes[-1] != 0 or 0 in host_bytes[:-1]:
        raise ValueError('One measured immutable NUL-inclusive input required')
    # This native gate admits the real unquoted worker launch domain only.
    if host_bytes[0] in (0, 0x22):
        raise ValueError('Empty or quoted input is outside this native prefix domain')

    def commit():
        for name, off in STATE_REG.items():
            struct.pack_into('<I', state, off, r[name])
        struct.pack_into('<I', state, 2472, pc)
        for offset, bit in M.F.FLAGS:
            state[offset] = (flags >> bit) & 1

    def snapshot(tag):
        commit()
        phases[tag] = OLD.stage(state, fx, cpu, memory)

    def checked(address, width, write=False):
        if deny_before and deny_before(pc, address, width, write):
            raise PermissionError((pc, address, width, write))
        if width not in (1, 4) or not 0 <= address <= 0xffffffff - width + 1:
            raise ValueError('Source access width or address wrap')

    def read(address, width):
        checked(address, width)
        if BUFFER <= address < BUFFER + len(host_bytes):
            if address + width > BUFFER + len(host_bytes):
                raise ValueError('Read outside complete owned command-line extent')
            value = int.from_bytes(host_bytes[address - BUFFER:address - BUFFER + width], 'little')
        else:
            if address & ~4095 != 0x20001000 or (address & 4095) + width > 4096:
                raise ValueError('Unadmitted non-input parser read')
            value = int.from_bytes(memory[0x20001000][address & 4095:(address & 4095) + width], 'little')
        accesses.append((pc, address, value, width, 0))
        return value

    def write(address, value):
        checked(address, 4, True)
        if address & ~4095 != 0x20001000 or (address & 4095) + 4 > 4096:
            raise ValueError('Unadmitted parser stack/count store')
        struct.pack_into('<I', memory[0x20001000], address & 4095, value & 0xffffffff)
        accesses.append((pc, address, value & 0xffffffff, 4, 1))

    def logical(value, width=32):
        mask = (1 << width) - 1
        value &= mask
        return (flags & ~0x8d5) | ((value == 0) << 6) | \
               (((value >> (width - 1)) & 1) << 7) | (((value & 255).bit_count() % 2 == 0) << 2)

    def increment(before):
        after = (before + 1) & 0xffffffff
        value = (flags & ~0x8d4) | ((after == 0) << 6) | ((after >> 31) << 7) | \
                (((after & 255).bit_count() % 2 == 0) << 2) | \
                ((((before ^ after) >> 4) & 1) << 4) | ((before == 0x7fffffff) << 11)
        return after, value

    snapshot('parser-before')
    snapshot('parser-projected')
    for _ in range(64):
        commit()
        pcs.append(pc)
        size, op, operands = program[pc]
        nxt = pc + size
        if pc == 0x7800bce6:
            F.require((size, op, operands) == (7, 'test', ['byte ptr [ebx + 0x780379e1]', '0x4']),
                      'First classification read is source qualified')
            address = TABLE + r['ebx']
            snapshot('parser-locale-before')
            # No memory read, flag result, table identity-as-initialization,
            # source RET or sizing completion is invented here.
            snapshot('parser-after')
            return dict(state=state, memory=memory, fx=fx, cpu=cpu,
                        accesses=accesses, PCs=pcs, phases=phases,
                        stop_PC=pc, stop_address=address, locale_read_completed=False)
        if op == 'push':
            F.require(pc in (BEGIN, 0x7800bc51, 0x7800bc52, 0x7800bc59), 'Actual saved-register PUSH')
            address = (r['esp'] - 4) & 0xffffffff
            write(address, r[operands[0]])
            r['esp'] = address  # Published only after successful source store.
        elif op == 'mov':
            if pc == 0x7800bc49:
                F.require(operands == ['ebp', 'esp'], 'Actual EBP frame setup')
                r['ebp'] = r['esp']
            elif pc in (0x7800bc4b, 0x7800bc4e, 0x7800bc56, 0x7800bc5a, 0x7800bc63):
                dest, displacement = {0x7800bc4b: ('ecx', 24), 0x7800bc4e: ('eax', 20),
                    0x7800bc56: ('esi', 16), 0x7800bc5a: ('edi', 12), 0x7800bc63: ('eax', 8)}[pc]
                F.require(operands == [dest, f'dword ptr [ebp + 0x{displacement:x}]'], 'Actual source argument read')
                r[dest] = read((r['ebp'] + displacement) & 0xffffffff, 4)
            elif pc == 0x7800bc5d:
                F.require(operands == ['dword ptr [eax]', '0x1'], 'Actual argument-slot initialization')
                write(r['eax'], 1)
            elif pc == 0x7800bce0:
                F.require(operands == ['dl', 'byte ptr [eax]'], 'Actual source input byte')
                value = read(r['eax'], 1)
                r['edx'] = (r['edx'] & 0xffffff00) | value
            else:
                raise ValueError(f'Unadmitted MOV {pc:x}')
        elif pc == 0x7800bc53:
            F.require((op, operands) == ('and', ['dword ptr [ecx]', '0x0']), 'Actual count AND read/store')
            read(r['ecx'], 4)
            write(r['ecx'], 0)
            flags = logical(0)  # After both accesses; a failed store retains previous flags.
        elif pc in (0x7800bc66, 0x7800bcd7):
            reg = 'edi' if pc == 0x7800bc66 else 'esi'
            F.require((op, operands) == ('test', [reg, reg]), 'Actual null-output TEST')
            flags = logical(r[reg])  # AF=0 is the declared translation representative.
        elif pc == 0x7800bc72:
            F.require((op, operands) == ('cmp', ['byte ptr [eax]', '0x22']), 'Actual quote decision')
            before = read(r['eax'], 1)
            after = (before - 0x22) & 255
            flags = (flags & ~0x8d5) | (before < 0x22) | ((after == 0) << 6) | \
                    (after & 128) | ((after.bit_count() % 2 == 0) << 2) | \
                    ((((before ^ 0x22 ^ after) >> 4) & 1) << 4) | \
                    ((((before ^ 0x22) & (before ^ after) & 128) != 0) << 11)
        elif pc in (0x7800bc68, 0x7800bc75, 0x7800bcd9):
            target = {0x7800bc68: 0x7800bc72, 0x7800bc75: 0x7800bcd5, 0x7800bcd9: 0x7800bce0}[pc]
            kind = 'jne' if pc == 0x7800bc75 else 'je'
            F.require((op, operands) == (kind, [hex(target)]), 'Actual conditional source edge')
            taken = bool(flags & 64) != (kind == 'jne')
            if taken:
                nxt = target
        elif pc == 0x7800bcd5:
            F.require((op, operands) == ('inc', ['dword ptr [ecx]']), 'Actual count increment read/store')
            before = read(r['ecx'], 4)
            value, next_flags = increment(before)
            write(r['ecx'], value)
            flags = next_flags
        elif pc == 0x7800bce2:
            F.require((op, operands) == ('inc', ['eax']), 'Actual input pointer increment')
            r['eax'], flags = increment(r['eax'])
        elif pc == 0x7800bce3:
            F.require((op, operands) == ('movzx', ['ebx', 'dl']), 'Actual lead-byte index')
            r['ebx'] = r['edx'] & 255
        else:
            raise ValueError(f'Unadmitted parser prefix instruction {pc:x}')
        pc = nxt
    raise ValueError('Bounded original prefix did not reach its declared dependency')
