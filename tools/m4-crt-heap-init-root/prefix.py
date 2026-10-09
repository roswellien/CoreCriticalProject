"""Independent literal PUSH1/CALL and heap initializer prefix to HeapCreate."""
import copy
import struct
from consumer import F, M, STATE_REG
from before import stage

FRAGMENT, SOURCE_CALL, SOURCE_RETURN = 0x7800183c, 0x7800183e, 0x78001843
ENTRY, API_CALL, API_SLOT, API_RETURN, RAW_API = 0x780039bf, 0x780039d0, 0x7802e0a8, 0x780039d6, 0x3461e
PCS = (FRAGMENT, SOURCE_CALL, ENTRY, 0x780039c1, 0x780039c3,
       0x780039c7, 0x780039cc, 0x780039cf, API_CALL)
SPANS = ((FRAGMENT, SOURCE_RETURN), (ENTRY, 0x78003a0c))


def source_material(out):
    path = F.pin(F.ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',
        '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    provider = M.N.PE.PEImage(path.read_bytes())
    tool = F.pin(F.ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe',
        'a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
    program, commands = {}, []
    for index, (start, end) in enumerate(SPANS):
        decoded, command = M.D.E.decode(tool, provider, path, start, end, out, 'heap-original-source-'+str(index))
        F.require(not set(program).intersection(decoded), 'Distinct exact source spans')
        program.update(decoded)
        commands.append(command)
    F.require(program[SOURCE_CALL] == (5, 'call', ['0x780039bf']), 'Original heap initializer CALL')
    F.require(program[API_CALL] == (6, 'call', ['dword ptr [0x7802e0a8]']), 'Original named HeapCreate indirect CALL')
    # The PE import inventory is separately independently reviewed. The literal
    # raw IAT value is source identity, not a host function address or API result.
    return program, M.D.mapped(provider, 0x78003000), commands


def predict(entry, program, deny_before=None):
    state, memory = bytearray(entry.state), copy.deepcopy(entry.mem)
    fx, cpu = bytes(entry.fx), bytes(entry.runtime_cpu)
    r = {name:struct.unpack_from('<I', state, off)[0] for name,off in STATE_REG.items()}
    flags = struct.unpack_from('<I', M.D.cpu(state), 32)[0]
    oldpc, oldsp = struct.unpack_from('<I', state, 2472)[0], r['esp']
    F.require(oldsp == 0x20001860 and struct.unpack_from('<I', cpu, 16)[0] == oldsp and
              struct.unpack_from('<I', cpu, 36)[0] == M.SLOT, 'Actual healthy carried mainargs boundary')
    F.require(struct.unpack_from('<I', state, 2120)[0] == 0, 'Independently established flat source SS base')
    phases = {'heap-before':stage(state, fx, cpu, memory)}
    pc, accesses, visited, routes, undefined = FRAGMENT, [], [], [], []

    def commit():
        for name, off in STATE_REG.items():
            struct.pack_into('<I', state, off, r[name])
        struct.pack_into('<I', state, 2472, pc)
        for offset, bit in M.F.FLAGS:
            state[offset] = (flags >> bit)&1

    def snapshot(tag):
        commit()
        phases[tag] = stage(state, fx, cpu, memory)

    def checked(address, write):
        F.require(0 <= address <= 0xfffffffc, 'Nonwrapping source DWORD')
        if deny_before and deny_before(pc, address, 4, write):
            raise PermissionError((pc, address, write))

    def read(address):
        checked(address, False)
        F.require(address == API_SLOT or 0x20001000 <= address <= 0x20001ffc, 'Exact stack or HeapCreate IAT read domain')
        value = struct.unpack_from('<I', memory[address&~4095], address&4095)[0]
        accesses.append((pc,address,value,4,0))
        return value

    def write(address, value):
        checked(address, True)
        F.require(0x20001000 <= address <= 0x20001ffc, 'Exact owned source stack DWORD store')
        struct.pack_into('<I', memory[address&~4095], address&4095, value&0xffffffff)
        accesses.append((pc,address,value&0xffffffff,4,1))

    def subtract(a, b):
        value = (a-b)&0xffffffff
        changed = ((a < b)|(((value&255).bit_count()%2 == 0)<<2)|
            ((((a^b^value)>>4)&1)<<4)|((value == 0)<<6)|((value>>31)<<7)|
            ((((a^b)&(a^value))>>31)<<11))
        return (flags&~0x8d5)|changed

    # This host seam changes only EIP. PUSH1 and both CALL stack words come
    # from genuine source instructions. No host guest-memory write is inserted.
    scheduler = (1, oldpc, oldsp, FRAGMENT, oldsp, 0, M.SLOT, oldsp)
    snapshot('heap-projected')
    for wanted in PCS:
        F.require(pc == wanted, 'Exact source fragment and heap prefix PC order')
        commit()
        visited.append(pc)
        size, op, operands = program[pc]
        nxt = pc+size
        if op == 'push':
            value = r[operands[0]] if operands[0] in r else int(operands[0],0)&0xffffffff
            address = r['esp']-4
            write(address,value)
            r['esp'] = address
        elif op == 'xor':
            F.require(operands == ['eax','eax'], 'Exact source zeroing XOR')
            r['eax'] = 0
            flags = (flags&~0x8d5)|0x44
            undefined.append((pc,0))  # Declared compiled AF representative only.
        elif op == 'cmp':
            F.require(operands == ['dword ptr [esp + 0x8]','eax'], 'Exact initializer argument read')
            value = read(r['esp']+8)
            F.require(value == 1 and r['eax'] == 0, 'Actual source PUSH1 argument and zeroed EAX')
            flags = subtract(value,r['eax'])
        elif op == 'sete':
            F.require(operands == ['al'], 'Exact source HeapCreate option computation')
            r['eax'] = (r['eax']&~255)|int(bool(flags&0x40))
        elif op == 'call':
            if pc == SOURCE_CALL:
                target = int(operands[0],0)
            else:
                F.require(pc == API_CALL, 'Only exact admitted indirect API CALL')
                target = read(API_SLOT)
                F.require(target == RAW_API, 'Exact original named HeapCreate raw IAT identity')
            address = r['esp']-4
            write(address,nxt)
            r['esp'] = address
            routes.append((pc,target,nxt))
            pc = target
            if target == ENTRY:
                snapshot('heap-provider-before')
                nxt = target
            else:
                F.require(target == RAW_API and len(accesses) == 8 and len(visited) == 9 and len(routes) == 2,
                          'Complete source to actual HeapCreate CALL; API not executed')
                snapshot('heap-api-before')
                snapshot('heap-after')
                return dict(state=state,memory=memory,fx=fx,cpu=cpu,phases=phases,
                    accesses=accesses,PCs=visited,routes=routes,scheduler=scheduler,undefined=undefined,
                    parent_frame=oldsp,initializer_frame=oldsp-8,API_frame=r['esp'],
                    fault_PC=API_CALL,fault_address=API_SLOT,API_executed=False,heap_initialized=False)
        else:
            raise ValueError('Unadmitted source heap-prefix instruction '+op)
        pc = nxt
    raise ValueError('Source prefix failed to reach the required API')
