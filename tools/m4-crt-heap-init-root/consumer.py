"""Independent exact-source consumer oracle; no candidate output is its seed.

The caller supplies the BEFORE-derived machine, plus the declared native OS
command-line input. This executes only BBD6..BBF7 and refuses at parser entry.
"""
import copy
import hashlib
import importlib.util
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
FILENAME_SHA = '405797301b25103cdc27dd0635e93e169a4ef86f415afb7c8a431da23703733e'
path = ROOT / 'tools/m4-crt-filename-root/observe.py'
if hashlib.sha256(path.read_bytes()).hexdigest() != FILENAME_SHA:
    raise ValueError('Frozen root filename oracle changed')
spec = importlib.util.spec_from_file_location('carry_frozen_filename_oracle', path)
F = importlib.util.module_from_spec(spec)
spec.loader.exec_module(F)
M, OLD = F.M, F.OLD

BEGIN, END = 0x7800bbd6, 0x7800bbfc
GLOBAL, BUFFER, PROGRAM = 0x78037174, 0x33000000, 0x7803b3e0
PARSER, CALL = 0x7800bc48, 0x7800bbf7
STATE_REG = dict(zip(M.F.REGS, M.F.OFF))
# These offsets are independently inherited from the accepted Remill State
# projection, rather than inferred from current candidate AFTER observations.

def predict(entry, program, host_bytes, deny_before=None):
    state = bytearray(entry.state)
    memory = copy.deepcopy(entry.mem)
    fx, cpu = bytes(entry.fx), bytes(entry.runtime_cpu)
    r = {name: struct.unpack_from('<I', state, off)[0]
         for name, off in STATE_REG.items()}
    # The actual aflag fields can override rflag after translated arithmetic.
    flags = M.D.cpu(state)[32:36]
    flags = struct.unpack('<I', flags)[0]
    pc, accesses, pcs, phases = BEGIN, [], [], {}
    if not host_bytes or len(host_bytes) > 131072 or host_bytes[-1] != 0 or 0 in host_bytes[:-1]:
        raise ValueError('Measured single NUL-terminated host bytes required')

    def commit():
        for name, off in STATE_REG.items():
            struct.pack_into('<I', state, off, r[name])
        struct.pack_into('<I', state, 2472, pc)
        for offset, bit in M.F.FLAGS:
            state[offset] = (flags >> bit) & 1

    def snapshot(tag):
        commit()
        phases[tag] = OLD.stage(state, fx, cpu, memory)

    def read32(address):
        value = struct.unpack_from('<I', memory[address & ~4095], address & 4095)[0]
        accesses.append((pc, address, value, 4, 0))
        return value

    def write32(address, value):
        if deny_before and deny_before(pc, address):
            raise PermissionError((pc, address))
        struct.pack_into('<I', memory[address & ~4095], address & 4095, value)
        accesses.append((pc, address, value, 4, 1))

    while pc < END:
        pcs.append(pc)
        commit()
        size, op, operands = program[pc]
        nxt = pc + size
        if pc == BEGIN:
            assert (size, op, operands) == (5, 'mov', ['eax', 'dword ptr [0x78037174]'])
            assert read32(GLOBAL) == BUFFER
            r['eax'] = BUFFER
        elif pc == 0x7800bbdb:
            assert (size, op, operands) == (6, 'mov', ['dword ptr [0x7803b3e0]', 'esi'])
            write32(PROGRAM, r['esi'])
        elif pc == 0x7800bbe1:
            assert (size, op, operands) == (2, 'mov', ['edi', 'esi'])
            r['edi'] = r['esi']
        elif pc == 0x7800bbe3:
            assert (size, op, operands) == (3, 'cmp', ['byte ptr [eax]', '0x0'])
            assert r['eax'] == BUFFER
            if deny_before and deny_before(pc, BUFFER):
                raise PermissionError((pc, BUFFER))
            byte = host_bytes[0]
            accesses.append((pc, BUFFER, byte, 1, 0))
            # CMP byte,0 leaves its value unchanged; AF/CF/OF are all zero.
            flags = (flags & ~0x8d5) | ((byte == 0) << 6) | (byte & 0x80) | (((byte.bit_count() & 1) == 0) << 2)
        elif pc == 0x7800bbe6:
            assert (size, op, operands) == (2, 'je', ['0x7800bbea'])
            if flags & 0x40:
                nxt = 0x7800bbea
        elif pc == 0x7800bbe8:
            assert (size, op, operands) == (2, 'mov', ['edi', 'eax'])
            r['edi'] = r['eax']
        elif pc in (0x7800bbea, 0x7800bbee):
            displacement = 8 if pc == 0x7800bbea else 4
            assert op == 'lea' and operands == ['eax', f'[ebp - 0x{displacement:x}]']
            r['eax'] = (r['ebp'] - displacement) & 0xffffffff
        elif op == 'push':
            assert pc in (0x7800bbed, 0x7800bbf1, 0x7800bbf2, 0x7800bbf4, 0x7800bbf6)
            value = r[operands[0]] if operands[0] in r else int(operands[0], 0)
            address = (r['esp'] - 4) & 0xffffffff
            write32(address, value)
            r['esp'] = address
        elif pc == CALL:
            assert (size, op, operands) == (5, 'call', ['0x7800bc48'])
            address = (r['esp'] - 4) & 0xffffffff
            write32(address, END)
            r['esp'], pc = address, PARSER
            snapshot('consumer-parser-before')
            break
        else:
            raise ValueError(f'Unadmitted literal consumer instruction {pc:x}')
        pc = nxt
    assert pc == PARSER and len(accesses) == 9 and len(pcs) == (13 if host_bytes[0] == 0 else 14)
    return dict(state=state, memory=memory, fx=fx, cpu=cpu,
                accesses=accesses, PCs=pcs, phases=phases,
                stop_PC=CALL, stop_address=PARSER)
