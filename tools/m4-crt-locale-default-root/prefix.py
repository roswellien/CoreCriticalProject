"""Independent original-byte default-selector prefix; no AFTER machine seeds."""
import copy
import struct
from consumer import F, M, OLD, STATE_REG
from before import stage

ENTRY, SETMBCP, LOCK = 0x78003dd2, 0x78003ddb, 0x78001055
MALLOC, CALL, RETURN, SLOT = 0x780012b3, 0x7800107b, 0x78001080, 0x7803708c
PAGE = 0x78003000
SPANS = ((ENTRY, ENTRY+9), (SETMBCP, SETMBCP+169), (LOCK, LOCK+91))
PCS = (0x78003dd2, 0x78003dd4, 0x78003ddb, 0x78003ddc, 0x78003dde,
       0x78003de1, 0x78003de2, 0x78003de3, 0x78003de4, 0x78003de6,
       0x78001055, 0x78001056, 0x78001058, 0x7800105b, 0x7800105c,
       0x78001064, 0x7800106b, 0x78001078, 0x78001079, 0x7800107b)


def source_material(out):
    path = F.pin(F.ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',
        '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    provider = M.N.PE.PEImage(path.read_bytes())
    tool = F.pin(F.ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe',
        'a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
    program, commands = {}, []
    for index, (start, end) in enumerate(SPANS):
        instructions, command = M.D.E.decode(tool, provider, path, start, end, out,
            'locale-original-source-'+str(index))
        F.require(not set(program).intersection(instructions), 'Distinct original locale source ranges')
        program.update(instructions)
        commands.append(command)
    F.require(program[CALL] == (5, 'call', ['0x780012b3']), 'Original malloc(24) source CALL')
    return program, M.D.mapped(provider, PAGE), commands


def predict(entry, program, deny_before=None):
    state = bytearray(entry.state)
    memory = copy.deepcopy(entry.mem)
    cpu, fx = bytes(entry.runtime_cpu), bytes(entry.fx)
    r = {name: struct.unpack_from('<I', state, off)[0] for name, off in STATE_REG.items()}
    flags = struct.unpack_from('<I', M.D.cpu(state), 32)[0]
    parent_frame = r['esp']
    F.require(parent_frame == 0x20001860 and struct.unpack_from('<I', cpu, 16)[0] == parent_frame and
              struct.unpack_from('<I', cpu, 36)[0] == M.SLOT, 'Actual carried mainargs Runtime frame')
    pc, accesses, pcs, routes, phases = ENTRY, [], [], [], {}

    def commit():
        for name, off in STATE_REG.items():
            struct.pack_into('<I', state, off, r[name])
        struct.pack_into('<I', state, 2472, pc)
        for offset, bit in M.F.FLAGS:
            state[offset] = (flags >> bit) & 1

    def snapshot(tag):
        commit()
        phases[tag] = stage(state, fx, cpu, memory)

    def checked(address, write):
        if not 0 <= address <= 0xfffffffc:
            raise ValueError('Source DWORD address overflow')
        if deny_before and deny_before(pc, address, 4, write):
            raise PermissionError((pc, address, write))

    def read(address):
        checked(address, False)
        F.require(address == SLOT or 0x20001000 <= address <= 0x20001ffc,
                  'Exact source lock-slot or owned stack read')
        value = struct.unpack_from('<I', memory[address & ~4095], address & 4095)[0]
        accesses.append((pc, address, value, 4, 0))
        return value

    def write(address, value, source=True):
        checked(address, True)
        F.require(0x20001000 <= address <= 0x20001ffc, 'Owned source/explicit scheduler stack DWORD')
        struct.pack_into('<I', memory[0x20001000], address & 4095, value & 0xffffffff)
        if source:
            accesses.append((pc, address, value & 0xffffffff, 4, 1))

    def arithmetic(a, b):
        result = (a-b) & 0xffffffff
        changed = ((a < b) | (((result & 255).bit_count() % 2 == 0) << 2) |
            ((((a ^ b ^ result) >> 4) & 1) << 4) | ((result == 0) << 6) |
            ((result >> 31) << 7) | ((((a ^ b) & (a ^ result)) >> 31) << 11))
        return result, (flags & ~0x8d5) | changed

    # One separately declared host scheduling store is not a source CALL.
    phases['locale-before'] = stage(state, fx, cpu, memory)
    frame = parent_frame-4
    write(frame, 0xfffffff0, source=False)
    scheduler = [(struct.unpack_from('<I', state, 2472)[0], frame, 0xfffffff0, 4, 1)]
    r['esp'] = frame
    snapshot('locale-projected')
    for expected_pc in PCS:
        F.require(pc == expected_pc, 'Exact original default/zero-slot source branch')
        commit()
        pcs.append(pc)
        size, op, operands = program[pc]
        nxt = pc+size
        if op == 'push':
            value = r[operands[0]] if operands[0] in r else int(operands[0], 0) & 0xffffffff
            address = r['esp']-4
            write(address, value)
            r['esp'] = address  # Source publication follows the checked store.
        elif op == 'call':
            target = int(operands[0], 0)
            address = r['esp']-4
            write(address, nxt)
            r['esp'] = address
            routes.append((pc, target, nxt))
            nxt = target
            if target in (SETMBCP, LOCK):
                pc = target
                snapshot('locale-setmbcp-before' if target == SETMBCP else 'locale-lock-before')
            if pc == CALL:
                pc = target
                snapshot('locale-malloc-before')
                snapshot('locale-after')
                F.require(len(accesses) == 15 and len(pcs) == 20 and len(routes) == 3,
                          'Full default-selector prefix and actual unexecuted allocator CALL')
                return dict(state=state, memory=memory, cpu=cpu, fx=fx, phases=phases,
                    accesses=accesses, PCs=pcs, routes=routes, scheduler=scheduler,
                    entry_frame=frame, parent_frame=parent_frame, stop_PC=CALL, target=MALLOC,
                    allocator_body_executed=False, locale_initialized=False)
        elif op == 'mov':
            if operands[1] == 'esp':
                F.require(operands == ['ebp', 'esp'], 'Exact source frame setup')
                r['ebp'] = r['esp']
            else:
                F.require(operands == ['eax', 'dword ptr [ebp + 0x8]'], 'Exact lock25 stack argument read')
                r['eax'] = read(r['ebp']+8)
        elif op == 'sub':
            F.require(operands == ['esp', '0x18'], 'Exact _setmbcp local stack allocation')
            r['esp'], flags = arithmetic(r['esp'], 0x18)
        elif op == 'cmp':
            F.require(operands == ['dword ptr [4*eax + 0x78037028]', '0x0'], 'Exact lock-slot operand')
            address = 0x78037028+4*r['eax']
            F.require(address == SLOT, 'Source selector25 lock slot')
            value = read(address)
            F.require(value == 0, 'Observed raw zero lock slot; no initialized lock credit')
            _, flags = arithmetic(value, 0)
        elif op == 'lea':
            F.require(operands == ['esi', '[4*eax + 0x78037028]'], 'Exact lock-slot address calculation')
            r['esi'] = 0x78037028+4*r['eax']
        elif op == 'je':
            F.require(flags & 0x40 and operands == ['0x78001078'], 'Actual lazy lock allocation branch')
            nxt = int(operands[0], 0)
        else:
            raise ValueError('Unadmitted original prefix instruction: '+op)
        pc = nxt
    raise ValueError('Original prefix did not stop before allocator body')
