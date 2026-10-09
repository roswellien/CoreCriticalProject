"""Continue the computed source selector return through its genuine caller RET."""
import importlib.util
import struct
from consumer import F, M, STATE_REG
from before import stage

path = F.pin(F.ROOT/'tools/m4-crt-heap-version-root/prefix.py',
    '894c0b674fbc1b2c625e5ff10dd74931d349b70a51b07d754a889cefe96de066')
spec = importlib.util.spec_from_file_location('heap_return_fixed_version_prefix', path)
prior = importlib.util.module_from_spec(spec); spec.loader.exec_module(prior)
FRAGMENT, SOURCE_CALL, SOURCE_RETURN = prior.FRAGMENT, prior.SOURCE_CALL, prior.SOURCE_RETURN
ENTRY, API_CALL, API_SLOT, API_RETURN, RAW_API = prior.ENTRY, prior.API_CALL, prior.API_SLOT, prior.API_RETURN, prior.RAW_API
MODE_CALL, MODE_ENTRY, MODE_RETURN = prior.MODE_CALL, prior.MODE_ENTRY, prior.MODE_RETURN
PROBE_CALL, PROBE_RETURN, PROBE_RET = prior.PROBE_CALL, prior.PROBE_RETURN, prior.PROBE_RET
QUERY_CALL, QUERY_SLOT, QUERY_RETURN, RAW_QUERY = prior.QUERY_CALL, prior.QUERY_SLOT, prior.QUERY_RETURN, prior.RAW_QUERY
QUERY_POINTER, QUERY_FRAME, QUERY_BYTES = prior.QUERY_POINTER, prior.QUERY_FRAME, prior.QUERY_BYTES
ENV_CALL, ENV_SLOT, ENV_RETURN, SELECTOR_RET = prior.ENV_CALL, prior.ENV_SLOT, prior.ENV_RETURN, prior.SELECTOR_RET
MODE_GLOBAL, INITIALIZER_RET = 0x78035004, 0x78003a0b
CONTINUATION_PCS = (0x780039e8, 0x780039eb, 0x780039f0, 0x780039f6, 0x780039f9,
                    0x78003a08, 0x78003a0a, INITIALIZER_RET)


def source_material(out):
    program, pages, commands = prior.source_material(out)
    wanted = {
        0x780039e8: (3, 'cmp', ['eax', '0x3']),
        0x780039eb: (5, 'mov', ['dword ptr [0x78035004]', 'eax']),
        0x780039f0: (6, 'je', ['0x7800cdc0']),
        0x780039f6: (3, 'cmp', ['eax', '0x2']),
        0x780039f9: (2, 'jne', ['0x78003a08']),
        0x78003a08: (2, 'push', ['0x1']),
        0x78003a0a: (1, 'pop', ['eax']),
        INITIALIZER_RET: (1, 'ret', [])}
    F.require(all(program[pc] == instruction for pc, instruction in wanted.items()),
              'Eight authentic caller/return instructions already in the full77-byte provider')
    F.require(sum(program[pc][0] for pc in CONTINUATION_PCS) == 23,
              '23 newly executed bytes, no extra source identity or translation')
    return program, pages, commands


def predict(entry, program, token, response):
    result = prior.predict(entry, program, token, response)
    result['initializer_RET'] = False
    result['initializer_result'] = None
    result['heap_mode_value'] = 0
    if not result['selector_returned']:
        return result
    phases = result['phases']; phases.pop('heap-create-after')
    state, memory, fx, cpu = result['state'], result['memory'], result['fx'], result['cpu']
    r = {name: struct.unpack_from('<I', state, offset)[0] for name, offset in STATE_REG.items()}
    flags = struct.unpack_from('<I', M.D.cpu(state), 32)[0]; pc = MODE_RETURN
    F.require(r['eax'] == 1 and r['esp'] == 0x20001858 and
              struct.unpack_from('<I', memory[MODE_GLOBAL & ~4095], MODE_GLOBAL & 4095)[0] == 0,
              'Source-derived live selector result and unexecuted original mode store')
    def commit():
        for name, offset in STATE_REG.items(): struct.pack_into('<I', state, offset, r[name])
        struct.pack_into('<I', state, 2472, pc)
        for offset, bit in M.F.FLAGS: state[offset] = (flags >> bit) & 1
    def snapshot(tag):
        commit(); phases[tag] = stage(state, fx, cpu, memory)
    def read(address):
        F.require(address in (0x20001854, 0x20001858), 'Exact original initializer stack read')
        value = struct.unpack_from('<I', memory[address & ~4095], address & 4095)[0]
        result['accesses'].append((pc, address, value, 4, 0)); return value
    def write(address, value):
        F.require((pc, address, value) in ((0x780039eb, MODE_GLOBAL, 1), (0x78003a08, 0x20001854, 1)),
                  'Only literal source mode publication and success PUSH')
        struct.pack_into('<I', memory[address & ~4095], address & 4095, value)
        result['accesses'].append((pc, address, value, 4, 1))
    def subtract(a, b):
        value = (a-b) & 0xffffffff
        changed = ((a < b) | (((value & 255).bit_count() % 2 == 0) << 2) |
            ((((a ^ b ^ value) >> 4) & 1) << 4) | ((value == 0) << 6) | ((value >> 31) << 7) |
            ((((a ^ b) & (a ^ value)) >> 31) << 11))
        return (flags & ~0x8d5) | changed
    for expected_pc in CONTINUATION_PCS:
        F.require(pc == expected_pc, 'Authentic qualifying source continuation order')
        commit(); result['PCs'].append(pc); size, op, args = program[pc]; nxt = pc+size
        if op == 'cmp': flags = subtract(r['eax'], int(args[1], 0))
        elif op == 'mov':
            snapshot('heap-return-mode-store-before'); write(MODE_GLOBAL, r['eax'])
            result['heap_mode_published'] = True; result['heap_mode_value'] = r['eax']
            snapshot('heap-return-mode-store-after')
        elif op == 'je':
            F.require(not flags & 64, 'Real selector1 does not choose mode3 allocator')
        elif op == 'jne':
            F.require(not flags & 64, 'Real selector1 bypasses mode2 allocator')
            nxt = int(args[0], 0)
        elif op == 'push': write(r['esp']-4, 1); r['esp'] -= 4
        elif op == 'pop':
            address = r['esp']; r['esp'] += 4; commit()
            r['eax'] = read(address); F.require(r['eax'] == 1, 'Literal source success value')
        elif op == 'ret':
            snapshot('heap-return-initializer-return-before')
            target = read(r['esp']); F.require(target == SOURCE_RETURN, 'Genuine original initializer CALL return')
            r['esp'] += 4; pc = target; result['initializer_RET'] = True; result['initializer_result'] = r['eax']
            snapshot('heap-return-initializer-return-after'); break
        else: raise ValueError('Unadmitted initializer continuation '+op)
        pc = nxt
    F.require(len(result['PCs']) == 59 and len(result['accesses']) == 35 and len(result['routes']) == 5
              and flags & 0x8d5 == 0x95 and r['eax'] == 1 and r['esp'] == 0x2000185c
              and pc == SOURCE_RETURN, 'Exact source mode1 initializer return and final defined flags')
    F.require(struct.unpack_from('<I', memory[0x20001000], 0x85c)[0] == 1,
              'Original cdecl argument remains; caller cleanup and TEST have not run')
    snapshot('heap-create-after')
    result.update(state=state, memory=memory, phases=phases, terminal_EIP=pc, terminal_ESP=r['esp'],
        fault_PC=INITIALIZER_RET, fault_address=SOURCE_RETURN, heap_initialized=False,
        post_initializer_caller_executed=False, mode2_or_mode3_allocator_executed=False)
    return result
