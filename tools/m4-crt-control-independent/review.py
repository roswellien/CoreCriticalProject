"""Independent bounded review: standard library only, no author observer imports.

The x86 model executes decoded, byte-verified provider instructions. It predicts
registers, all stack bytes, normalized CW, and CALL/RET events from BEFORE data.
Private evidence is written to a fresh directory, including failed attempts.
"""
from __future__ import annotations
import collections
import hashlib
import json
import mmap
from pathlib import Path
import re
import struct
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / 'reports/m4-crt-control'
LLVM = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
ENTRIES = (0x780042E1, 0x780042F7, 0x7800432C, 0x7800439F)
CWS = (0x7F, 0x47F, 0x87F, 0xC7F, 0x27F, 0x67F, 0xA7F, 0xE7F, 0x37F, 0x77F, 0xB7F, 0xF7F)
REGS = ('eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi')
GPRS = (2216, 2248, 2264, 2232, 2312, 2328, 2280, 2296, 2472)
AFIELDS = ((2065, 0), (2067, 2), (2069, 4), (2071, 6), (2073, 7), (2075, 10), (2077, 11))
COUNT, OS, NS = 3264, 10456, 17596
PINS: dict[str, str] = {}

def demand(ok, reason):
    if not ok:
        raise ValueError(reason)

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def bind(path, expected=None):
    path = Path(path)
    digest = sha(path)
    demand(expected is None or digest == expected, 'Physical identity: ' + str(path))
    demand(str(path) not in PINS or PINS[str(path)] == digest, 'Conflicting identity')
    PINS[str(path)] = digest
    return path

def read_json(path, expected=None):
    return json.loads(bind(path, expected).read_text())

def u32(b, offset=0, count=1):
    return struct.unpack_from('<' + 'I' * count, b, offset)

def u16(b, offset=0):
    return struct.unpack_from('<H', b, offset)[0]

def put(b, offset, value, size=4):
    b[offset:offset+size] = (value & ((1 << (size*8))-1)).to_bytes(size, 'little')

def cases(index):
    if index < 4:
        return ((0, 0), (0, 0xFFFFFFFF), (0xFFFFFFFF, 0xFFFFFFFF), (0x35AB96D2, 0x8C75EA31))[index]
    bit = 1 << ((index-4)//2)
    return (0 if index & 1 else bit, bit)

def pe_reader(path):
    data = bind(path, '2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes()
    pe = u32(data, 0x3C)[0]
    demand(data[pe:pe+4] == b'PE\0\0' and u16(data, pe+4) == 0x14C, 'Exact x86 provider PE')
    opt_size = u16(data, pe+20)
    demand(u16(data, pe+24) == 0x10B and u32(data, pe+24+28)[0] == 0x78000000, 'Provider base')
    regions = []
    for i in range(u16(data, pe+6)):
        s = pe+24+opt_size+i*40
        regions.append((*u32(data, s+12, 3), u32(data, s+36)[0]))
    def fetch(address, size):
        rva = address-0x78000000
        for va, extent, offset, permissions in regions:
            if va <= rva and rva+size <= va+extent:
                demand(permissions & 0x20000000, 'Provider instructions must be file-backed RX')
                return data[offset+rva-va:offset+rva-va+size]
        raise ValueError('Unfilebacked provider instruction')
    return fetch

def decode(out):
    provider = ROOT / 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL'
    fetch = pe_reader(provider)
    program = {}
    commands = []
    for label, start, stop in (('hot', 0x780042E1, 0x78004410), ('cold', 0x7801129B, 0x78011318)):
        args = [str(LLVM/'llvm-objdump.exe'), '-d', '--x86-asm-syntax=intel', f'--start-address={start}', f'--stop-address={stop}', str(provider)]
        bind(args[0])
        result = subprocess.run(args, capture_output=True, check=False)
        log = out/(label+'-disassembly.txt')
        log.write_bytes(result.stdout+result.stderr)
        bind(log)
        demand(result.returncode == 0, 'Fresh provider decode failed')
        commands.append({'arguments': args, 'exit_code': result.returncode, 'log': str(log)})
        for line in result.stdout.decode().splitlines():
            m = re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*([a-z]+)\s*(.*?)\s*$', line)
            if not m:
                continue
            pc = int(m[1], 16)
            code = bytes.fromhex(m[2])
            demand(start <= pc < stop and fetch(pc, len(code)) == code, 'Fresh decoded source bytes')
            operands = re.sub(r'\s*<[^>]*>', '', m[4]).strip()
            demand(pc not in program, 'Duplicate source PC')
            program[pc] = (len(code), m[3], [x.strip() for x in operands.split(',')] if operands else [])
    demand(len(program) == 148, 'Complete hot/cold original source PC count')
    demand({v[1] for v in program.values()} == {'mov','and','push','call','pop','ret','wait','fnstcw','not','or','fldcw','leave','xor','test','je','movzx','jne','cmp','jmp'}, 'Exact bounded source instruction domain')
    return program, commands

class X86:
    """Serial scalar original-instruction model; x87 transfers only."""
    def __init__(self, program, before, memory, cw):
        self.program = program
        self.r = dict(zip(REGS, before[:8]))
        self.flags, self.pc = before[8:]
        self.memory = bytearray(memory)
        self.cw = cw
        self.events = []
        self.frames = []
        self.visited = set()
        self.enter()

    def width(self, operand):
        if operand.startswith('byte ptr '): return 1
        if operand.startswith('word ptr '): return 2
        if operand.startswith('dword ptr '): return 4
        if operand in self.r: return 4
        if operand in ('ax','bx','cx','dx','sp','bp','si','di'): return 2
        if operand in ('al','ah','bl','bh','cl','ch','dl','dh'): return 1
        return 4

    def address(self, operand):
        inside = re.fullmatch(r'(?:byte|word|dword) ptr \[([a-z]+)(?: ([+-]) (0x[0-9a-f]+))?\]', operand)
        demand(inside is not None, 'Unknown memory expression ' + operand)
        value = self.r[inside[1]]
        if inside[3]: value += (1 if inside[2] == '+' else -1)*int(inside[3], 16)
        offset = (value & 0xFFFFFFFF)-0x20001000
        demand(0 <= offset <= 4096-self.width(operand), 'Model operand outside declared stack')
        return offset

    def read(self, operand):
        if operand in self.r: return self.r[operand]
        if operand.startswith(('byte ptr ', 'word ptr ', 'dword ptr ')):
            offset = self.address(operand)
            return int.from_bytes(self.memory[offset:offset+self.width(operand)], 'little')
        if operand[0].isdigit() or operand[0] == '-': return int(operand, 0) & 0xFFFFFFFF
        if self.width(operand) == 2: return self.r['e'+operand] & 0xFFFF
        demand(self.width(operand) == 1, 'Unknown read operand '+operand)
        return (self.r['e'+operand[0]+'x'] >> (8 if operand[1]=='h' else 0)) & 0xFF

    def write(self, operand, value):
        size = self.width(operand)
        value &= (1 << (size*8))-1
        if operand in self.r: self.r[operand] = value
        elif operand.startswith(('byte ptr ', 'word ptr ', 'dword ptr ')):
            put(self.memory, self.address(operand), value, size)
        else:
            reg = 'e'+operand if size == 2 else 'e'+operand[0]+'x'
            shift = 8 if size == 1 and operand[1] == 'h' else 0
            mask = ((1 << (size*8))-1) << shift
            self.r[reg] = (self.r[reg] & ~mask) | (value << shift)

    def push(self, value):
        self.r['esp'] = (self.r['esp']-4)&0xFFFFFFFF
        put(self.memory, self.r['esp']-0x20001000, value)

    def pop(self):
        offset = self.r['esp']-0x20001000
        demand(0 <= offset <= 4092, 'Model POP stack bound')
        result = u32(self.memory, offset)[0]
        self.r['esp'] += 4
        return result

    def nonvol(self):
        return tuple(self.r[x] for x in ('ebx','ebp','esi','edi'))

    def enter(self):
        ret = u32(self.memory, self.r['esp']-0x20001000)[0]
        self.frames.append((self.pc, self.r['esp'], ret, self.nonvol()))
        self.events.append((1, self.pc, self.r['esp'], ret))

    def arithmetic(self, opcode, a, b, width):
        mask = (1 << (width*8))-1
        sign = 1 << (width*8-1)
        if opcode == 'cmp':
            result = (a-b)&mask
            cf, of, af = int(a < b), int(bool((a^b)&(a^result)&sign)), int(bool((a^b^result)&0x10))
        else:
            result = (a & b) if opcode in ('and','test') else (a|b) if opcode == 'or' else (a^b)
            result &= mask
            cf = of = af = 0 # AF undefined, excluded from original comparison.
        bits = cf | (int((result&255).bit_count()%2 == 0)<<2) | (af<<4) | (int(result==0)<<6) | (int(bool(result&sign))<<7) | (of<<11)
        self.flags = (self.flags & ~0x8D5) | bits
        return result

    def run(self):
        for _ in range(512):
            if self.pc == 0x10000100:
                demand(not self.frames, 'Model return frame residue')
                return tuple(self.r[x] for x in REGS)+(self.flags,self.pc), bytes(self.memory), self.cw, tuple(self.events), set(self.visited)
            demand(self.pc in self.program, 'Model unsupported PC '+hex(self.pc))
            self.visited.add(self.pc)
            length, op, operands = self.program[self.pc]
            next_pc = self.pc+length
            if op in ('mov','movzx'): self.write(operands[0], self.read(operands[1]))
            elif op in ('xor','and','or','test','cmp'):
                result = self.arithmetic(op, self.read(operands[0]), self.read(operands[1]), self.width(operands[0]))
                if op not in ('test','cmp'): self.write(operands[0], result)
            elif op == 'not': self.write(operands[0], ~self.read(operands[0]))
            elif op == 'push': self.push(self.read(operands[0]))
            elif op == 'pop': self.write(operands[0], self.pop())
            elif op == 'call':
                self.push(next_pc)
                next_pc = self.read(operands[0])
                demand(next_pc in ENTRIES, 'Unreviewed provider CALL')
                self.pc = next_pc
                self.enter()
            elif op == 'ret':
                frame = self.frames.pop()
                next_pc = self.pop()
                demand(self.r['esp']==frame[1]+4 and next_pc==frame[2] and self.nonvol()==frame[3], 'Model actual cdecl/nonvolatile return')
                self.events.append((2,next_pc,self.r['esp'],next_pc))
            elif op == 'leave':
                self.r['esp'] = self.r['ebp']
                self.r['ebp'] = self.pop()
            elif op == 'fnstcw': self.write(operands[0], self.cw)
            elif op == 'fldcw': self.cw = (self.read(operands[0])&0x1F3F)|0x40
            elif op == 'wait': pass # Admitted SW0, empty tags, TOP0, no pending exception.
            elif op in ('je','jne'):
                if bool(self.flags&0x40) == (op == 'je'): next_pc = self.read(operands[0])
            elif op == 'jmp': next_pc = self.read(operands[0])
            else: raise ValueError('Unknown source instruction '+op)
            self.pc = next_pc
        raise ValueError('Model instruction bound exceeded')

def expected_tag(index):
    repeat = index//1632
    entry = (index//816)%2
    case = (index//12)%68
    return (repeat, entry, case, CWS[index%12], *cases(case))

def original_model(program, row, index):
    demand(len(row)==OS and u32(row,0,6)==expected_tag(index), 'Original exact corpus/tag order')
    tag = expected_tag(index)
    before = u32(row,24,10)
    demand(before==(0x13579BDF,0x2468ACE0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xAABBCCDD,0x202,ENTRIES[tag[1]]), 'Original exact entry CPU')
    memory = bytearray([0xA5]*4096)
    struct.pack_into('<3I', memory, 0x800, 0x10000100, *tag[4:])
    demand(row[2264:6360]==memory, 'Original full authored input stack')
    f0, f1 = row[104:616], row[616:1128]
    e0, e1 = row[2152:2180], row[2180:2208]
    demand(u16(f0)==tag[3] and u16(f0,2)==0 and f0[4]==0 and u32(f0,24)[0]==0x1F80 and u16(e0,8)==0xFFFF, 'Original admitted FP domain')
    after, stack, cw, events, visited = X86(program,before,memory,tag[3]).run()
    observed = u32(row,64,10)
    demand(observed[:8]+observed[9:]==after[:8]+after[9:] and ((observed[8]^after[8])&~0x10)==0, 'Independent original CPU/source model')
    demand(row[6360:]==stack, 'Independent complete original source stack model')
    ef, ee = bytearray(f0), bytearray(e0)
    put(ef,0,cw,2); put(ee,0,cw,2)
    demand(f1==ef and e1==ee, 'Independent original normalized CW/source model and FP preservation')
    demand(row[1128:1640]==row[1640:2152] and row[2208:2236]==row[2236:2264], 'Original full captured host FX/ENV restoration')
    return after, stack, cw, events, visited

def state_before(row, index):
    state = bytearray((13*j+index+7)&255 for j in range(3504))
    for at,v in ((2120,0),(2168,0x7FFDE000),(2184,0)): put(state,at,v)
    cpu = u32(row,24,10)
    for at,v in zip(GPRS,cpu[:8]+cpu[9:]): put(state,at,v)
    put(state,2080,cpu[8],8)
    for at,bit in AFIELDS: state[at]=(cpu[8]>>bit)&1
    state[2736:2760]=bytes(24)
    state[2768:3280]=row[104:616]
    env=row[2152:2180]
    for target,source,length in ((2774,18,2),(2776,12,4),(2780,16,2),(2784,20,4),(2788,24,2)):
        state[target:target+length]=env[source:source+length]
    for i in range(8):
        state[2486+i*16:2496+i*16]=row[136+i*16:146+i*16]
        state[16+i*64:32+i*64]=row[264+i*16:280+i*16]
    return state

def native_model(program, original, native, index, model=None):
    if model is None: model=original_model(program, original, index)
    after, stack, cw, events, _=model
    demand(len(native)==NS and native[:64]==original[:64], 'Native full input tag/CPU')
    demand(u32(native,64,10)==after, 'Independent complete native source CPU/defined FLAGS')
    demand(native[104:1128]==original[104:1128] and native[1128:1184]==original[2152:2208], 'Native separate observed FX512/ENV28')
    state=state_before(original,index)
    demand(native[1184:4688]==state, 'Independent native full3504 prestate construction')
    for at,v in zip(GPRS,after[:8]+after[9:]): put(state,at,v)
    for at,bit in AFIELDS: state[at]=(after[8]>>bit)&1
    put(state,2768,cw,2)
    demand(native[4688:8192]==state, 'Independent native complete3504 source writes and hidden preservation')
    demand(native[8192:12288]==original[2264:6360] and native[12288:16384]==stack, 'Independent native full4096 source stack model')
    demand(u32(native,16384)[0]==len(events), 'Native actual complete route count')
    encoded=b''.join(struct.pack('<4I',*event) for event in events)
    demand(native[16388:16516]==encoded+bytes(128-len(encoded)), 'Independent native source CALL/RET route/cleanup/nonvolatile ledger')
    demand(native[16516:17028]==native[17028:17540] and native[17540:17568]==native[17568:17596], 'Native full actual host FX/ENV restoration')

def mutations(program,o,n):
    checks=[]
    # Full State and physical/logical FP banks each receive their own corruption.
    locations=[('original',0),('original',24),('original',64),('original',616),('original',2180),('original',6360+0x800),('original',1640),('original',2236)]
    locations += [('native',x) for x in (0,24,64,68,72,76,80,84,88,92,100,104,616,618,620,640,1128,1156,1168,1174,1176,1184,4688+3400,4688+2168,4688+2768,8192,12288,12288+0x7DC,16384,16388,16392,16396,16400,17028,17568)]
    locations += [('native',96+(bit//8)) for bit in (0,2,6,7,10,11)]
    for base,stride in ((616+32,16),(616+160,16),(4688+2486,16),(4688+16,64),(4688+2768+32,16),(4688+2768+160,16),(17028+32,16),(17028+160,16)):
        locations += [('native',base+i*stride) for i in range(8)]
    for side,offset in locations:
        oo,nn=bytearray(o),bytearray(n)
        (oo if side=='original' else nn)[offset]^=1
        try:
            model=original_model(program,oo,0)
            native_model(program,oo,nn,0,model)
        except ValueError as e:
            checks.append({'side':side,'offset':offset,'rejected':True,'diagnostic':str(e)})
        else: raise ValueError('Independent observer accepted corruption '+str((side,offset)))
    changed=bytearray(o); changed[96]^=0x10
    native_model(program,changed,n,0)
    checks.append({'side':'original','offset':96,'undefined_AF':True,'accepted_only_explicit_exclusion':True})
    return checks

def strip_body(text):
    result={}
    for m in re.finditer(r'^define[^\n]*@([\w.]+)\([^\n]*\)[^\n]*\{\n(.*?)^}',text,re.M|re.S):
        result[m[1]]=m[2]
    return result

def canonical(body):
    body=re.sub(r'\s*;[^\n]*','',body)
    body=re.sub(r' #\d+\b','',body)
    # LLVM printing closes unnamed SSA/block-number gaps after the three exact
    # transfer removals. Resolve every definition first, including forward edges;
    # preserve operands and connectivity under a bijective alpha renaming.
    identifiers=[]
    for match in re.finditer(r'^\s*(?:(\d+):|%(\d+) =)',body,re.M):
        name=match[1] or match[2]
        demand(name not in identifiers,'Duplicate unnamed SSA/block definition')
        identifiers.append(name)
    mapping={name:'v'+str(i) for i,name in enumerate(identifiers)}
    def rename(match):
        number=match[1]
        if number in mapping: return '%'+mapping[number]
        demand(number=='0','Unresolved numeric SSA operand')
        return '%0' # The independently checked identity-helper formal argument.
    body=re.sub(r'%(\d+)\b',rename,body)
    body=re.sub(r'^(\s*)(\d+):',lambda m:m[1]+mapping[m[2]]+':',body,flags=re.M)
    return '\n'.join(x.strip() for x in body.splitlines() if x.strip())

def layout_model(text):
    types=dict(re.findall(r'^(%[\w.]+) = type (.+)$',text,re.M))
    cache={}
    def align(n,a): return (n+a-1)//a*a
    def calc(t):
        t=t.strip()
        if t in cache: return cache[t]
        if t in types: result=calc(types[t])
        elif re.fullmatch(r'i(?:8|16|32|64|128)',t):
            n=int(t[1:])//8; result=(n,n,())
        elif m:=re.fullmatch(r'\[(\d+) x (.+)\]',t):
            size,a,_=calc(m[2]); result=(int(m[1])*align(size,a),a,())
        elif t.startswith('{ ') and t.endswith(' }'):
            fields=t[2:-2].split(', ')
            cursor=0; alignment=1; offsets=[]
            for field in fields:
                size,a,_=calc(field);cursor=align(cursor,a); offsets.append(cursor);cursor+=size;alignment=max(alignment,a)
            result=(align(cursor,alignment),alignment,tuple(offsets))
        else: raise ValueError('Unreviewed layout type '+t)
        cache[t]=result;return result
    for name in types: calc(name)
    demand(calc('%struct.State')[:2]==(3504,16), 'Independent complete State ABI3504/16')
    return types,cache

def cfg_model(body, entry):
    """Resolve original PCs from the lifted block edges, not author annotations."""
    blocks={'entry':[]};current='entry'
    for raw in body.splitlines():
        line=raw.split(';',1)[0].strip()
        if not line: continue
        if re.fullmatch(r'[\w.]+:',line):
            current=line[:-1];demand(current not in blocks,'Duplicate IR block');blocks[current]=[]
        else: blocks[current].append(line)
    pending=[('entry',entry)];reached={};addresses={};calls=[]
    while pending:
        block,pc=pending.pop()
        if block in reached:
            demand(reached[block]==pc,'Conflicting original IR block PC');continue
        reached[block]=pc
        values={'%program_counter':entry};cells={'%NEXT_PC':pc};instruction=None
        for line in blocks[block]:
            if m:=re.fullmatch(r'(%[\w.]+) = load i32, ptr (%[\w.]+), align \d+',line):
                values[m[1]]=cells.get(m[2]);continue
            if m:=re.fullmatch(r'(%[\w.]+) = (add|sub) i32 (%[\w.]+), (-?\d+)',line):
                a=values.get(m[3]);values[m[1]]=((a+(1 if m[2]=='add' else -1)*int(m[4]))&0xFFFFFFFF) if isinstance(a,int) else None;continue
            if m:=re.fullmatch(r'(%[\w.]+) = select i1 %[\w.]+, i32 (%[\w.]+), i32 (%[\w.]+)',line):
                values[m[1]]=(values.get(m[2]),values.get(m[3]));continue
            if m:=re.fullmatch(r'store i32 (%[\w.]+|\d+), ptr (%[\w.]+), align \d+',line):
                value=int(m[1]) if m[1].isdigit() else values.get(m[1]);cells[m[2]]=value
                if m[2]=='%PC' and instruction is None and isinstance(value,int):
                    instruction=value;addresses[block]=value
            if m:=re.search(r'call ptr @sub_([0-9a-f]+)\(',line):
                demand(instruction is not None,'Direct CALL instruction not bound');calls.append((instruction,int(m[1],16)))
        terminal=blocks[block][-1]
        if terminal.startswith('ret ptr '): continue
        successors=re.findall(r'label %([\w.]+)',terminal)
        demand(terminal.startswith('br ') and len(successors) in (1,2),'Complete bounded IR terminator')
        next_pc=cells.get('%NEXT_PC')
        targets=next_pc if len(successors)==2 else (next_pc,)
        demand(isinstance(targets,tuple) and len(targets)==len(successors) and all(isinstance(x,int) for x in targets),'Complete exact PC successor resolution')
        pending.extend(zip(successors,targets))
    demand(set(reached)==set(blocks),'All original lifted blocks statically reachable')
    return set(addresses.values()), calls

def state_store_audit(body,types,layout):
    pointers={'%state':0};allocas=set();stores=collections.Counter();undefined=[]
    def struct_fields(t):
        return types[t][2:-2].split(', ')
    def gep_offset(t,indices):
        demand(indices and indices[0]==0,'Nonzero whole-State GEP')
        offset=0
        for index in indices[1:]:
            definition=types.get(t,t)
            if definition.startswith('{ '):
                fields=struct_fields(t);demand(0<=index<len(fields),'Exact State field index')
                offset+=layout[t][2][index];t=fields[index]
            elif m:=re.fullmatch(r'\[(\d+) x (.+)\]',definition):
                demand(0<=index<int(m[1]),'Exact State array index')
                size,alignment,_=layout[m[2]];offset+=index*((size+alignment-1)//alignment*alignment);t=m[2]
            else: raise ValueError('Unreviewed typed State GEP traversal')
        return offset
    for raw in body.splitlines():
        line=raw.split(';',1)[0].strip()
        if m:=re.match(r'(%[\w.]+) = alloca ',line): allocas.add(m[1])
        if m:=re.fullmatch(r'(%[\w.]+) = getelementptr (?:inbounds )?(?:nuw )?([^,]+), ptr (%[\w.]+), (.+)',line):
            demand(m[3] in pointers,'Unknown GEP provenance')
            indices=[int(x) for x in re.findall(r'i(?:32|64) (-?\d+)',m[4])]
            demand(len(indices)==len(m[4].split(', ')),'Dynamic or incomplete State GEP')
            offset=indices[0] if m[2]=='i8' and len(indices)==1 else gep_offset(m[2],indices)
            pointers[m[1]]=pointers[m[3]]+offset
        if m:=re.fullmatch(r'store (i\d+|ptr) (.+), ptr (%[\w.]+), align \d+',line):
            destination=m[3]
            if destination in pointers:
                demand(m[1]!='ptr','No host pointer may enter guest State')
                offset=pointers[destination];width=int(m[1][1:])//8
                demand(0<=offset and offset+width<=3504,'State store bound')
                stores[(offset,width)]+=1
            else: demand(destination in allocas,'Unresolved store destination')
        if m:=re.match(r'(%[\w.]+) = call(?: zeroext)? i8 @__remill_undefined_8\(\)',line): undefined.append(m[1])
    for value in undefined:
        uses=[x.strip() for x in body.splitlines() if value in re.findall(r'%[\w.]+',x) and not x.strip().startswith(value+' =')]
        demand(len(uses)==1,'Undefined value used beyond one AF store')
        match=re.fullmatch(r'store i8 '+re.escape(value)+r', ptr (%[\w.]+), align 1',uses[0])
        demand(match and pointers.get(match[1])==2069,'Undefined value reaches only AF')
    allowed={*(x for x in GPRS),*(x for x,_ in AFIELDS),2217}
    demand(set(x for x,_ in stores)<=allowed,'No hidden State writes in compiled integer bodies')
    return {'all_destinations_resolved':True,'stores':[{'offset':o,'width':w,'count':n} for (o,w),n in sorted(stores.items())],'undefined_AF_terminal_count':len(undefined)}

def static_review(out,program):
    folder=GATE/'research-r1'
    guest=bind(folder/'guest.ll').read_text(); candidate=bind(folder/'candidate.ll').read_text(); host=bind(folder/'host.ll').read_text()
    g,c,h=map(strip_body,(guest,candidate,host))
    names={f'sub_{e:x}' for e in ENTRIES}
    demand(set(g)==names and set(c)==names and names<=set(h), 'Exactly four complete original static provider definitions')
    demand('__remill_missing_block' not in guest and not re.search(r'\b(?:inttoptr|ptrtoint|x86_fp80|float|double|volatile|atomic|poison|undef)\b',guest), 'Original complete bounded IR domain')
    # Independent exact reversal of the three transfers, preserving all other IR.
    control=c['sub_780042f7']
    reverse=[('  %cf_wait = call ptr @mw34_cf_wait(ptr %state, i32 %43, ptr %45)\n  store ptr %cf_wait, ptr %MEMORY, align 4',
              '  %46 = call i32 @__remill_fpu_exception_test(i32 noundef 127) #4\n  call void @__remill_fpu_exception_clear(i32 noundef %46) #4\n  store ptr %45, ptr %MEMORY, align 4'),
             ('  %57 = call ptr @mw34_cf_store_cw(ptr %state, i32 %53, ptr %54)',
              '  %55 = getelementptr inbounds nuw i8, ptr %state, i32 2768\n  %56 = load i16, ptr %55, align 16\n  %57 = call noundef ptr @__remill_write_memory_16(ptr noundef %54, i32 noundef %53, i16 noundef zeroext %56) #3'),
             ('  %cf_load = call ptr @mw34_cf_load_cw(ptr %state, i32 %265, ptr %266)\n  store ptr %cf_load, ptr %MEMORY, align 4',
              '  %267 = getelementptr inbounds nuw i8, ptr %state, i32 2768\n  %268 = call noundef zeroext i16 @__remill_read_memory_16(ptr noundef %266, i32 noundef %265) #3\n  store i16 %268, ptr %267, align 16\n  %269 = lshr i16 %268, 10\n  %270 = and i16 %269, 3\n  %271 = zext nneg i16 %270 to i32\n  call void @__remill_fpu_set_rounding(i32 noundef %271) #4\n  store ptr %266, ptr %MEMORY, align 4')]
    for new,old in reverse:
        demand(control.count(new)==1, 'Exactly one reviewed FP transfer replacement')
        control=control.replace(new,old)
    for name in names:
        demand(canonical(control if name=='sub_780042f7' else c[name])==canonical(g[name]), 'Exact candidate reversal retains complete integer/CALL/RET body '+name)
        clean=h[name].replace('  %checked_entry = call ptr @mw34_cf_enter(ptr %state, i32 %program_counter, ptr %memory)\n','')
        demand(h[name].count('@mw34_cf_enter(')==1 and canonical(clean)==canonical(c[name]), 'Exact host body and one actual checked entry '+name)
    gt,gl=layout_model(guest); ht,hl=layout_model(host)
    demand(gt==ht and gl==hl, 'Independent all34 complete guest/host named layouts')
    pc_union=set();direct_calls=[];state_writes={}
    for name in names:
        addresses,calls=cfg_model(g[name],int(name[4:],16));pc_union|=addresses;direct_calls+=calls
        state_writes[name]=state_store_audit(h[name],ht,hl)
    demand(pc_union==set(program),'Independent exact complete148 source-to-lift PC equality')
    demand(sorted(direct_calls)==[(0x780042EF,0x780042F7),(0x78004303,0x7800432C),(0x7800431A,0x7800439F)],'Exact source direct CALL sites/targets')
    attrs=dict(re.findall(r'^attributes #(\d+) = \{([^\n]*)\}',host,re.M))
    required=names|{'__remill_read_memory_32','__remill_write_memory_32','__remill_function_return','mw34_cf_enter','mw34_cf_wait','mw34_cf_store_cw','mw34_cf_load_cw'}
    for line in host.splitlines():
        callee=re.search(r'@([\w.]+)\(',line)
        if not callee or callee[1] not in required: continue
        if line.startswith(('define ','declare ')) or 'call ' in line:
            groups=re.findall(r'#(\d+)',line);attributes=' '.join(attrs[x] for x in groups)
            demand(not re.search(r'\b(nounwind|willreturn)\b',line+' '+attributes),'Required fault-propagation boundary promises invalid nonlocal return')
    helpers={k:v for k,v in h.items() if k not in names}
    for name,body in helpers.items():
        demand(name.startswith(('__remill_flag_','__remill_compare_')) or name=='__remill_undefined_8', 'Unreviewed helper definition')
        demand(canonical(body) == ('identity:\nret i8 0' if name=='__remill_undefined_8' else 'identity:\nret i1 %0'), 'Scalar identity or explicit undefined AF helper')
    demand(not any('@'+x in host for x in ('__remill_fpu_exception_clear','__remill_fpu_exception_test','__remill_fpu_set_rounding','__remill_read_memory_16','__remill_write_memory_16')), 'No host-global FP helper remains')
    ctx=bind(ROOT/'tools/m4-crt-control/native_context.hpp').read_text()
    demand('void deny(const char*why){' in ctx and 'std::longjmp(boundary,1)' in ctx and 'void deny(const char*why)noexcept' not in ctx, 'Causal non-noexcept Windows longjmp escape')
    worker=bind(ROOT/'tools/m4-crt-control/native_worker.cpp').read_text()
    demand('const auto*before_fx=r+104' in worker and 'const auto*before_env=r+2152' in worker and 'const auto*before_mem=r+2264' in worker, 'Actual original BEFORE projection')
    demand(not re.search(r'\br\s*\+\s*(64|616|2180|6360)\b',worker), 'Original AFTER not used as native result')
    return {'complete_provider_instruction_PCs':len(program),'exact_original_source_to_lift_PC_equality':True,'compiled_definitions':4,'exact_mechanical_FP_transfers':3,'all_integer_and_CALL_RET_IR_preserved':True,'all_complete_named_layouts':len(gt),'State_bytes':3504,'State_alignment':16,'checked_entry_hooks':4,'helper_definitions':len(helpers),'host_State_write_audit':state_writes,'typed_State_only_CW':True,'generic_Context_owner_API_claim':False}

def audit_builds(out):
    author=read_json(GATE/'author-review-r1/report.json','18fc8d660ea4482724dd9e88e8f398219e2f4bbcf9a2f6c8b032f51306c032e3')
    pins=read_json(GATE/'author-review-r1/pins.json','b7e7552abd81514a76d9dd8089209bd6e251acbea6ae8d465624809271974b9e')['files']
    demand(author['passed'] and len(pins)==1039, 'Exact frozen complete author aggregate')
    for path,digest in pins.items(): bind(path,digest)
    preservation=read_json(GATE/'pre-denial-escape-repair/manifest.json','5651743026363b3c205306f5f0b286fe09e645baca5d9163b879724bcf0080b5')
    for row in preservation['literal_source_copies']:
        bind(row['preserved_path'],row['sha256'])
    for row in preservation['historical_source_resolutions']:
        mapping=read_json(row['historical_map'],row['historical_map_sha256'])
        demand(mapping[row['group']][row['original_path']]==row['recorded_sha256']==row['physical_sha256'], 'Explicit exact historical logical-to-literal association')
        bind(row['physical_path'],row['recorded_sha256'])
    commands=[]; artifacts=[]
    for label in ('original-build-r1','native-build-r3','context-build-r2'):
        build=read_json(GATE/label/'build.json')
        demand(build['passed'], 'Actual final build '+label)
        for group in ('source_files','tool_files','artifacts'):
            for path,digest in build[group].items(): bind(path,digest)
        for row in build['literal_source_copies']:
            demand(build['source_files'][row['original_path']]==row['sha256'], 'Actual build source-to-literal identity')
            bind(row['preserved_path'],row['sha256'])
        for command in build['commands']:
            demand(command['exit_code']==0,'Actual successful build command')
        artifacts+=list(build['artifacts'])
    objpaths=[p for p in artifacts if p.endswith('.obj') and not any(x in p for x in ('ShowIncludes','CompilerId'))]
    for i,path in enumerate(dict.fromkeys(objpaths)):
        args=[str(LLVM/'llvm-objdump.exe'),'-d','-r','--x86-asm-syntax=intel',path]
        result=subprocess.run(args,capture_output=True)
        log=out/f'object-{i:02d}.txt';log.write_bytes(result.stdout+result.stderr);bind(log)
        demand(result.returncode==0 and result.stdout, 'Actual bound object fresh decode')
        commands.append({'arguments':args,'exit_code':result.returncode,'log':str(log)})
    context=GATE/'context-build-r2/ctest.log'
    text=context.read_text()
    demand(text.count('27 authored compiled-provider routing/fault controls passed')==2 and '100% tests passed' in text, 'Actual27 compiled controls per level')
    diagnosis=preservation['diagnosis']
    old=bind(GATE/'pre-denial-escape-repair/sources/tools/m4-crt-control/native_context.hpp').read_text()
    new=bind(ROOT/'tools/m4-crt-control/native_context.hpp').read_text()
    demand(old.replace('void deny(const char*why)noexcept','void deny(const char*why)')==new, 'Exact narrow deny noexcept repair, all other Context source identical')
    return {'author_physical_bindings':len(pins),'historical_literal_substitutions':len(preservation['historical_source_resolutions']),'literal_pre_repair_sources':len(preservation['literal_source_copies']),'actual_fresh_object_decodes':len(commands),'compiled_controls_per_level':27,'diagnosis':diagnosis,'commands':commands}

def main(out):
    demand(out.is_relative_to(GATE) and not out.exists(), 'Fresh private independent evidence directory')
    out.mkdir(parents=True)
    (out/'review-source.py').write_bytes(Path(__file__).read_bytes())
    try:
        program,decode_commands=decode(out)
        static=static_review(out,program)
        build=audit_builds(out)
        prior_attempts=[]
        for label in ('independent-review-r1','independent-review-r2','independent-review-r3'):
            previous=GATE/label
            if previous==out or not previous.exists(): continue
            for path in previous.rglob('*'):
                if path.is_file(): bind(path)
            prior_attempts.append({'directory':str(previous),'source_sha256':sha(previous/'review-source.py'),'failed':(previous/'failure.txt').exists()})
            if (previous/'pins.json').exists():
                prior=read_json(previous/'pins.json')['files']
                for path,digest in prior.items():
                    if Path(path)==Path(__file__):
                        bind(previous/'review-source.py',digest)
                    else: bind(path,digest)
        original_report=read_json(GATE/'original-run-r1/report.json')
        native_report=read_json(GATE/'native-run-r2/report.json')
        original_path=bind(original_report['raw']['path'],original_report['raw']['sha256'])
        demand(original_report['passed'] and native_report['passed'] and len(original_report['actual_controls'])==8 and len(native_report['actual_controls'])==16, 'Actual worker controls8+16')
        models=[];coverage=set();counts=collections.Counter();corruptions=[]
        with original_path.open('rb') as f, mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as original:
            demand(len(original)==24+COUNT*OS and original[:8]==b'MW4CFC01' and u32(original,8,4)==(1,COUNT,OS,4096),'Exact original stream header/extent')
            for i in range(COUNT):
                row=original[24+i*OS:24+(i+1)*OS]
                model=original_model(program,row,i);models.append(model);coverage|=model[4]
                counts['original_model_records']+=1
            for i in range(1632):
                a=original[24+i*OS:24+(i+1)*OS];b=original[24+(i+1632)*OS:24+(i+1633)*OS]
                demand(a[4:96]==b[4:96] and ((u32(a,96)[0]^u32(b,96)[0])&~0x10)==0 and a[100:1128]==b[100:1128] and a[2152:2208]==b[2152:2208] and a[2264:]==b[2264:], 'Actual exact original repeat; undefined AF excluded')
            for level in ('O0','O2'):
                info=native_report['raws'][level];path=bind(info['path'],info['sha256'])
                with path.open('rb') as nf,mmap.mmap(nf.fileno(),0,access=mmap.ACCESS_READ) as native:
                    demand(len(native)==24+COUNT*NS and native[:8]==b'MW4CFN01' and u32(native,8,4)==(1,COUNT,NS,3504),'Exact native stream header/extent')
                    for i in range(COUNT):
                        row=native[24+i*NS:24+(i+1)*NS]
                        native_model(program,original[24+i*OS:24+(i+1)*OS],row,i,models[i])
                        counts[level+'_native_records']+=1;counts[level+'_actual_route_events']+=len(models[i][3])
                    corruptions+=mutations(program,original[24:24+OS],native[24:24+NS])
        report={'passed':True,'scope':'Independent complete static CRT control provider with measured empty TOP0/SW0 domain; shared runtime integration remains open','original_records':COUNT,'native_records':COUNT*2,'differences':0,'source_model':{'instruction_domain_PCs':148,'executed_corpus_PCs':len(coverage),'exact_model_source_PC_coverage':sorted(coverage),'unexecuted_static_PCs':[hex(x) for x in sorted(set(program)-coverage)],'source_derived_stack_and_CW':True,'AF_undefined_exclusion_only':0x10},'static':static,'counts':dict(counts),'own_observer_controls':corruptions,'build_and_preservation':build,'decode_commands':decode_commands,'prior_own_attempts':prior_attempts,'whole_M4_complete':False,'shared_Runtime_provider_integration':False,'limitations':['Serial trusted stable Context, no generic thread-owner or one-use admission.','Only 12 measured incoming CWs, empty physical x87 tags, SW0/TOP0 and MXCSR1F80; no pending exceptions or numerical operation after changed CW.','The two incoming-IC-set decoder PCs are statically retained but not executed by this 12-CW corpus.','Actual original full CPU and stack compared against source instruction model; Remill full3504 State is native-only observed representation.','Empty-register raw80/XMM contents and final hardware metadata are preservation observations, not occupied-stack numerical semantics.','OS/tool execution metadata and present hashes retained; no generic process attestation or concurrency/reparse publisher assurance.']}
        path=out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n');bind(path);bind(__file__);bind(out/'review-source.py')
        (out/'pins.json').write_text(json.dumps({'files':dict(sorted(PINS.items()))},indent=2)+'\n')
        print(json.dumps({'passed':True,'original_records':COUNT,'native_records':COUNT*2,'source_model_PCs_observed':len(coverage),'own_controls':len(corruptions),'bindings':len(PINS),'report_sha256':sha(path),'pins_sha256':sha(out/'pins.json')}))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc())
        raise

if __name__=='__main__':
    demand(len(sys.argv)==2,'Usage: independent-review fresh-private-output')
    main(Path(sys.argv[1]).resolve())
