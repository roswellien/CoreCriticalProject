"""Independent source selector/probe through the genuine version-query CALL."""
import importlib.util
import re
import struct
import types
from consumer import F,M,STATE_REG
from before import stage,PAGE,PROBE_PAGE,STACK_PAGE,SELECTOR,PROBE

path = F.pin(F.ROOT/'tools/m4-crt-heap-create-root/prefix.py',
    'd571c81396b6e54aa2b37ffd56b41aa394d2aec77bb5277afd05b3d57f4b2fff')
spec = importlib.util.spec_from_file_location('heap_mode_frozen_heap_prefix',path)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
first_prefix = types.FunctionType(prior.predict.__code__,dict(prior.predict.__globals__,stage=stage))
FRAGMENT,SOURCE_CALL,SOURCE_RETURN = prior.FRAGMENT,prior.SOURCE_CALL,prior.SOURCE_RETURN
ENTRY,API_CALL,API_SLOT,API_RETURN,RAW_API = prior.ENTRY,prior.API_CALL,prior.API_SLOT,prior.API_RETURN,prior.RAW_API
MODE_CALL,MODE_ENTRY,MODE_RETURN = prior.MODE_CALL,prior.MODE_ENTRY,prior.MODE_RETURN
PROBE_CALL,PROBE_RETURN,PROBE_RET = 0x78003a14,0x78003a19,0x780058cf
QUERY_CALL,QUERY_SLOT,QUERY_RETURN,RAW_QUERY = 0x78003a2b,0x7802e0a0,0x78003a31,0x34600


def source_material(out):
    program,pages,commands = prior.source_material(out)
    provider_path = F.pin(F.ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',
        '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    provider = M.N.PE.PEImage(provider_path.read_bytes())
    tool = F.pin(F.ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe',
        'a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
    for index,(start,end) in enumerate(((SELECTOR,QUERY_RETURN),(PROBE,0x780058e6))):
        decoded,command = M.D.E.decode(tool,provider,provider_path,start,end,out,'heap-mode-original-source-'+str(index))
        F.require(not set(program).intersection(decoded),'Disjoint exact selector and probe source')
        program.update(decoded)
        commands.append(command)
    F.require(program[PROBE_CALL] == (5,'call',['0x780058b5']) and
              program[QUERY_CALL] == (6,'call',['dword ptr [0x7802e0a0]']),
              'Original direct probe and version-query import CALLs')
    pages[PROBE_PAGE] = M.D.mapped(provider,PROBE_PAGE)
    return program,pages,commands


def predict(entry,program,token):
    result = first_prefix(entry,program,token)
    state,memory,fx,cpu = result['state'],result['memory'],result['fx'],result['cpu']
    phases = result['phases']
    phases.pop('heap-create-after')
    r = {name:struct.unpack_from('<I',state,off)[0] for name,off in STATE_REG.items()}
    pc,flags = MODE_ENTRY,struct.unpack_from('<I',M.D.cpu(state),32)[0]
    F.require(r['esp']==0x20001854 and len(result['accesses'])==10,
              'Source-published genuine selector CALL carries existing State')
    F.require(struct.unpack_from('<I',state,2120)[0]==0 and struct.unpack_from('<I',state,2184)[0]==0,
              'Carried flat SS and DS bases')

    def commit():
        for name,off in STATE_REG.items():
            struct.pack_into('<I',state,off,r[name])
        struct.pack_into('<I',state,2472,pc)
        for offset,bit in M.F.FLAGS:
            state[offset] = (flags>>bit)&1

    def snapshot(name):
        commit()
        phases[name] = stage(state,fx,cpu,memory)

    def read(address):
        F.require(address==QUERY_SLOT or STACK_PAGE<=address<=0x20001ffc,
                  'Exact admitted source stack or version-query IAT domain')
        value = struct.unpack_from('<I',memory[address&~4095],address&4095)[0]
        result['accesses'].append((pc,address,value,4,0))
        return value

    def write(address,value):
        F.require(STACK_PAGE<=address<=0x20001ffc,'Source-only owned stack store domain')
        struct.pack_into('<I',memory[address&~4095],address&4095,value&0xffffffff)
        result['accesses'].append((pc,address,value&0xffffffff,4,1))

    def address(text):
        if text.startswith('dword ptr '):
            text = text[10:]
        match = re.fullmatch(r'\[([a-z]+)(?: ([+-]) (0x[0-9a-f]+))?\]',text)
        if match:
            base,sign,delta = match.groups()
            return (r[base] + (int(delta,0) if sign=='+' else -int(delta,0)) if delta else r[base])&0xffffffff
        return int(text[1:-1],0)

    def operand(text):
        if text in r:
            return r[text]
        if '[' in text:
            return read(address(text))
        return int(text,0)&0xffffffff

    def subtraction(a,b):
        value = (a-b)&0xffffffff
        changed = ((a<b)|(((value&255).bit_count()%2==0)<<2)|
            ((((a^b^value)>>4)&1)<<4)|((value==0)<<6)|((value>>31)<<7)|
            ((((a^b)&(a^value))>>31)<<11))
        return value,(flags&~0x8d5)|changed

    returned = False
    for _ in range(64):
        F.require(pc in program and (SELECTOR<=pc<QUERY_RETURN or PROBE<=pc<0x780058e6),
                  'Only exact selector/probe prefix instructions admitted')
        commit()
        result['PCs'].append(pc)
        size,op,args = program[pc]
        nxt = pc+size
        if op=='push':
            value = operand(args[0])
            write(r['esp']-4,value)
            r['esp'] = (r['esp']-4)&0xffffffff
        elif op=='mov':
            value = operand(args[1])
            if args[0] in r:
                r[args[0]] = value
            else:
                write(address(args[0]),value)
        elif op=='lea':
            r[args[0]] = address(args[1])
        elif op in ('cmp','sub'):
            value,flags = subtraction(operand(args[0]),operand(args[1]))
            if op=='sub':
                r[args[0]] = value
        elif op=='test':
            F.require(pc in (0x780058db,0x780058c5),'Two exact probe TEST sites')
            value = operand(args[0])&operand(args[1])
            flags = (flags&~0x8d5)|(((value&255).bit_count()%2==0)<<2)|((value==0)<<6)|((value>>31)<<7)
            result['undefined'].append((pc,0))
        elif op in ('jae','jb'):
            if bool(flags&1)==(op=='jb'):
                nxt = int(args[0],0)
        elif op=='jmp':
            nxt = int(args[0],0)
        elif op=='ret':
            F.require(pc==PROBE_RET and not returned,'Only genuine probe RET is admitted')
            target = read(r['esp'])
            F.require(target==PROBE_RETURN and r['esp']==0x20000620,'Relocated genuine probe return frame')
            r['esp'] += 4
            nxt = target
            returned = True
            result['probe_return_access'] = result['accesses'][-1]
            pc = nxt
            snapshot('heap-mode-probe-after')
            continue
        elif op=='call':
            target = operand(args[0])
            write(r['esp']-4,nxt)
            r['esp'] -= 4
            result['routes'].append((pc,target,nxt))
            callsite = pc
            pc = target
            if callsite==PROBE_CALL:
                F.require(target==PROBE and r['eax']==0x122c and r['esp']==0x2000184c,
                          'Genuine stack-allocation probe CALL')
                snapshot('heap-mode-probe-before')
                continue
            F.require(callsite==QUERY_CALL and target==RAW_QUERY and returned and r['esp']==0x20000618,
                      'First genuine version-query CALL after actual probe RET')
            F.require(read_query_argument(memory)==0x200017b8 and
                      struct.unpack_from('<I',memory[0x20001000],0x7b8)[0]==0x94,
                      'Only original source publishes OSVERSIONINFOA header and query argument')
            snapshot('heap-mode-query-before')
            snapshot('heap-create-after')
            result.update(state=state,memory=memory,phases=phases,fault_PC=QUERY_CALL,
                fault_address=QUERY_SLOT,terminal_EIP=RAW_QUERY,terminal_ESP=r['esp'],
                stack_probe_returned=True,query_executed=False,mode_selected=False,
                initializer_RET=False,heap_initialized=False)
            F.require(len(result['PCs'])==39 and len(result['accesses'])==24 and
                      len(result['routes'])==5 and len(result['undefined'])==4,
                      'Complete bounded selector/probe/query source execution')
            return result
        else:
            raise ValueError('Unadmitted selector/probe opcode '+op)
        pc = nxt
    raise ValueError('Bounded source prefix failed to reach version-query CALL')


def read_query_argument(memory):
    return struct.unpack_from('<I',memory[STACK_PAGE],0x61c)[0]
