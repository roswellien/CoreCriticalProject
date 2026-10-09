"""Independent BEFORE/source model of native FDIV producer -> CRT consumer.

Imports frozen root observers only. Source data comes from exact PE files and
the preserved original BEFORE capture; native AFTER bytes are never seeds.
"""
import copy, hashlib, importlib.util, json, re, struct, subprocess, sys, traceback
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PINS = {}
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def pin(p, h=None):
    p = Path(p).resolve(); v = sha(p)
    assert h is None or v == h, str(p)
    assert str(p) not in PINS or PINS[str(p)] == v
    PINS[str(p)] = v; return p
def module(name, p, h):
    spec = importlib.util.spec_from_file_location(name, pin(p, h))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
R = module('root_frozen_fdiv_replay', ROOT/'tools/m4-crt-fdiv-independent/replay_model.py', 'eb77c8cf6b0f533b2cd2b50b3ce6d3bbb2c26be2ea5e844278a45ca5cb297b35')
E = module('root_frozen_entry_prefix', ROOT/'tools/m4-crt-entry/observe_prefix.py', 'c45c54dc62a805113b5e56142d577f4a46a89790c68acda339bbb5f4a2915af1')
N, F = R.N, E.F
PAGES = tuple(N.PAGES) + (0x736000, 0x9a1000)
FRAME = F.FRAME
def cpu(state):
    flags = F.word(state, 2080, 8) & ~0xcd5
    for o, b in F.FLAGS: flags |= state[o] << b
    return struct.pack('<10I', *[F.word(state, o) for o in F.OFF], flags, F.word(state, 2472))
def mapped(pe, a):
    rva = a-pe.image_base
    matches = [s for s in pe.sections if s['virtual_address'] <= rva and rva+4096 <= s['virtual_address']+((max(s['virtual_size'], s['raw_size'])+4095)&~4095)]
    assert len(matches) == 1
    s = matches[0]; d = rva-s['virtual_address']; n = max(0, min(4096, s['raw_size']-d))
    return pe.read(s['raw_offset']+d, n)+bytes(4096-n) if n else bytes(4096)
def read_stage(row, tag):
    return {p.name: pin(p).read_bytes() for p in (row/tag).glob('*.bin')}
def stage(state, fx, runtime_cpu, memory):
    d = {'state.bin': bytes(state), 'fx.bin': bytes(fx), 'runtime-cpu.bin': bytes(runtime_cpu), 'state-cpu.bin': cpu(state), 'crt-globals.bin': bytes(memory[0x78038ee8]), 'tib-0.bin': bytes(memory[0x7ffde000]), 'tib-4.bin': struct.pack('<2I', 0x20002000, 0x20001000), 'tib-24.bin': struct.pack('<I', 0x7ffde000), 'entry-source.bin':bytes(memory[0x5ac3a0])}
    for a in PAGES: d[f'page-{a}.bin'] = bytes(memory[a])
    return d
def equal(got, expected, message):
    assert got.keys() == expected.keys(), message+' key inventory'
    for name in got: assert got[name] == expected[name], message+' '+name
class Stop(Exception): pass
class Entry(E.Model):
    def __init__(self, program, providers, state, memory, control=0):
        self.program = program; self.provider_program = providers; self.control=control
        self.state = bytearray(state); self.mem = copy.deepcopy(memory)
        self.r = dict(zip(F.REGS, struct.unpack('<10I', cpu(state))[:8]))
        self.flags = struct.unpack('<10I', cpu(state))[8]; self.pc = 0x5ac3a0
        self.r['esp'] = FRAME; F.put(self.state, 2312, FRAME); F.put(self.state, 2472, self.pc)
        if control!=10:self.raw_store(FRAME, 0xfffffff0)
        self.events = []; self.visited = []; self.provider_PCs = []; self.data_routes = []
        self.routes = [dict(site=0xfffffff0, target=0x5ac3a0, return_pc=0xfffffff0, import_=False, completed=False)]
        self.runtime_cpu = struct.pack('<10I', *[self.r[k] for k in F.REGS], self.flags, self.pc)
        if control in (7,10):
            self.state=bytearray(state)
            regs=list(struct.unpack('<10I',cpu(state)));regs[4]=FRAME if control==7 else FRAME+4;regs[9]=self.pc if control==7 else 0xfffffff0
            self.runtime_cpu=struct.pack('<10I',*regs)
        if control==4:F.put(self.mem[0x78004000],0x254,0)
        if control==5:F.put(self.mem[0x7802e000],0x98,0)
        if control==6:F.put(self.mem[0x78037000],0xc2c,F.word(self.mem[0x78037000],0xc2c)^1)
        if control==7:F.put(self.mem[0x5ac3a0],0,0)
        if control==8:F.put(self.mem[0x5bb000],0x508,0x1ded32^1)
        if control==9:F.put(self.mem[0x5bb000],0x5a4,0)
        self.projected=(bytes(self.state),bytes(self.runtime_cpu),copy.deepcopy(self.mem))
    def store(self,a,v,event=True):
        if self.control==11 and a&~4095==0x9a1000:
            self.project(self.pc);raise Stop()
        return super().store(a,v,event)
    def read(self, s):
        v = super().read(s)
        if s == 'dword ptr [0x5bb508]':
            if self.control in (4,5,6,8):self.project(self.pc);raise Stop()
            assert self.pc == 0x5ac408 and v == 0x1ded32
            self.data_routes.append((self.pc, 0x5bb508, v, 0x78037c2c, self.raw_load(0x78037c2c)))
            return 0x78037c2c
        return v
    def run(self):
        if self.control in (7,10):return self
        imports = {0x5ac3cf:(0x5bb5a4,0x78004625), 0x5ac3ec:(0x5bb57c,0x7800462f), 0x5ac3fa:(0x5bb504,0x78004635)}
        for _ in range(64):
            size, op, args = self.program[self.pc]; self.visited.append(self.pc); nxt = self.pc+size
            if op == 'push': self.push(self.read(args[0]))
            elif op == 'mov': self.write(args[0], self.read(args[1]))
            elif op == 'add':
                a,b = self.read(args[0]),self.read(args[1]); v = (a+b)&0xffffffff
                bits = int(a+b>0xffffffff)|(int((v&255).bit_count()%2==0)<<2)|(int(bool((a^b^v)&0x10))<<4)|(int(v==0)<<6)|(int(bool(v&0x80000000))<<7)|(int(bool((~(a^b)&(a^v))&0x80000000))<<11)
                self.flags = (self.flags&~0x8d5)|bits; self.write(args[0],v)
            elif op == 'test':
                v = self.read(args[0])&self.read(args[1])
                # Remill's retained undefined-AF representative is zero.
                bits=(int((v&255).bit_count()%2==0)<<2)|(int(v==0)<<6)|(int(bool(v&0x80000000))<<7)
                self.flags=(self.flags&~0x8d5)|bits
            elif op == 'jne':
                if not self.flags&0x40: nxt=self.read(args[0])
            elif op == 'call':
                target=self.read(args[0]); self.push(nxt)
                if self.pc in imports:
                    slot, provider=imports[self.pc]; assert args==[f'dword ptr [{slot:#x}]']
                    if self.control in (9,12) and self.pc==0x5ac3cf:
                        self.project(target)
                        regs=[self.r[k] for k in F.REGS]
                        if self.control==9:regs[4]+=4;pc=self.pc
                        else:
                            regs[0]=self.raw_load(self.r['esp']+4);pc=slot
                            self.routes.append(dict(site=self.pc,target=slot,return_pc=nxt,import_=True,completed=False))
                        self.runtime_cpu=struct.pack('<10I',*regs,self.flags,pc)
                        return self
                    assert self.provider(provider)==nxt; self.project(nxt,flat=True)
                    self.runtime_cpu=struct.pack('<10I',*[self.r[k] for k in F.REGS],self.flags,nxt)
                    self.routes.append(dict(site=self.pc,target=slot,return_pc=nxt,import_=True,completed=True))
                elif self.pc==0x5ac415:
                    assert target==0x5ac5c0 and self.program[target]==(1,'ret',[])
                    self.project(target,flat=True); self.visited.append(target)
                    save=self.pc; self.pc=target; ret=self.load(self.r['esp']); self.r['esp']+=4; self.pc=save
                    assert ret==nxt; self.project(nxt,flat=True)
                    self.runtime_cpu=struct.pack('<10I',*[self.r[k] for k in F.REGS],self.flags,nxt)
                    self.routes.append(dict(site=save,target=target,return_pc=nxt,import_=False,completed=True))
                elif self.pc==0x5ac428:
                    assert target==self.raw_load(0x5bb50c) and args==['dword ptr [0x5bb50c]']
                    self.project(target)
                    regs=[self.r[k] for k in F.REGS]; regs[4]+=4
                    self.runtime_cpu=struct.pack('<10I',*regs,self.flags,self.pc)
                    return self
                else: raise AssertionError('Unreviewed source CALL')
            else: raise AssertionError('Unreviewed entry instruction '+op)
            self.pc=nxt
        raise AssertionError('Required missing matherr dependency not reached')
def host(before, after):
    assert len(before)==len(after)==544
    assert before[512:540]==after[512:540], 'Direct caller whole ENV28'
    for lo,hi in ((0,5),(24,28))+tuple((32+16*i,42+16*i) for i in range(8))+tuple((160+16*i,176+16*i) for i in range(6,16)):
        assert before[lo:hi]==after[lo:hi], 'Direct ABI numerical FP or XMM6..15'
def base_memory(payload,provider_pages,game_page,source_pages):
    m={a:bytearray(p) for a,p in zip(N.PAGES,provider_pages+[payload[604:4700],game_page])}
    m.update({a:bytearray(source_pages[a]) for a in (0x736000,0x9a1000,0x5ac3a0)})
    m.update({0x78038ee8:bytearray(12),0x7ffde000:bytearray(struct.pack('<I',0xffffffff))})
    return m
class PartialWriter(R.ReplayModel):
    def store(self,a,v,size):
        if a==0x78037c34:raise Stop()
        return super().store(a,v,size)
def causal(row,payload,writer_program,provider_pages,game_page,entry_program,providers,source_pages,control):
    result=json.loads(pin(row/'result.json').read_text())
    assert result['passed'] and result['control']==control and result['poisoned_retry']
    initial,fx,cpu0,cw,repeat=R.seed(payload);memory=base_memory(payload,provider_pages,game_page,source_pages)
    record=pin(row/'writer-record.bin').read_bytes()
    before={tag:read_stage(row,tag) for tag in ('writer-before','writer-after','retry-after')}
    if control<=3:
        if control==2:F.put(initial,2768,F.word(initial,2768,2)^0x100,2)
        equal(before['writer-before'],stage(initial,fx,struct.pack('<10I',*cpu0),memory),'Causal writer whole BEFORE')
        final=bytearray(initial);events=[]
        if control==3:
            model=PartialWriter(writer_program,b''.join(memory[a] for a in N.PAGES),cpu0,cw,0)
            try:model.run()
            except Stop:pass
            else:raise AssertionError('Failed writer required pointer store not reached')
            assert model.pc==0x78004270
            for o,n in zip(N.OFFSETS,N.REGS):F.put(final,o,model.r[n])
            F.put(final,2472,model.pc)
            for o,b in N.FLAGS:final[o]=(model.flags>>b)&1
            for i,a in enumerate(N.PAGES):memory[a]=model.memory[4096*i:4096*(i+1)]
            events=model.events
        expected=stage(final,fx,struct.pack('<10I',*cpu0),memory)
        equal(before['writer-after'],expected,'Causal writer exact stopped source prefix')
        equal(before['retry-after'],expected,'Causal writer terminal retry')
        assert len(record)==N.STRIDE and struct.unpack_from('<7I',record)==(0,0,cw,0,len(events),0,0)
        assert record[28:3532]==initial and record[3532:7036]==final and record[7036:7548]==record[7548:8060]==fx
        assert record[9140:46004]==b''.join(before['writer-before'][f'page-{a}.bin'] for a in N.PAGES)
        assert record[46004:82868]==b''.join(memory[a] for a in N.PAGES)
        expected_events=b''.join(struct.pack('<5I',*v) for v in events)
        assert record[82868:87988]==expected_events+bytes(5120-len(expected_events)) and record[87988:]==bytes(N.STRIDE-87988)
        faults={1:(5,0x78004254,0x5bb508),2:(3,0x78004254,0x78004254),3:(1,0x78004270,0x78037c34)}
    else:
        writer=R.observe(record,payload,writer_program,provider_pages,game_page)
        equal(before['writer-before'],stage(initial,fx,struct.pack('<10I',*cpu0),memory),'Causal entry unchanged source writer BEFORE')
        final=bytearray(initial)
        for o,n in zip(N.OFFSETS,N.REGS):F.put(final,o,writer.r[n])
        F.put(final,2472,writer.pc);F.put(final,2768,writer.cw,2);F.put(fx,0,writer.cw,2)
        for o,b in N.FLAGS:final[o]=(writer.flags>>b)&1
        for i,a in enumerate(N.PAGES):memory[a]=writer.memory[4096*i:4096*(i+1)]
        equal(before['writer-after'],stage(final,fx,cpu(final),memory),'Causal entry full source writer completion')
        pre_mem=copy.deepcopy(memory)
        mutation={4:(0x78004000,0x254,0),5:(0x7802e000,0x98,0),6:(0x78037000,0xc2c,F.word(memory[0x78037000],0xc2c)^1),7:(0x5ac3a0,0,0),8:(0x5bb000,0x508,0x1ded32^1),9:(0x5bb000,0x5a4,0)}.get(control)
        if mutation:a,o,v=mutation;F.put(pre_mem[a],o,v)
        pre_cpu=bytearray(cpu(final));F.put(pre_cpu,16,FRAME+4);F.put(pre_cpu,36,0xfffffff0)
        equal(read_stage(row,'entry-before-invoke'),stage(final,fx,pre_cpu,pre_mem),'Causal exact input mutation only')
        model=Entry(entry_program,providers,final,memory,control)
        try:model.run()
        except Stop:pass
        expected=stage(model.state,fx,model.runtime_cpu,model.mem)
        equal(read_stage(row,'entry-after-fault'),expected,'Causal exact stopped entry prefix')
        equal(before['retry-after'],expected,'Causal Runtime poisoned retry whole prefix')
        if control not in (7,10):
            projected_state,projected_cpu,projected_mem=model.projected
            equal(read_stage(row,'entry-projected'),stage(projected_state,fx,projected_cpu,projected_mem),'Causal actual projection before source')
        else:assert not (row/'entry-projected').exists()
        assert pin(row/'entry-events.bin').read_bytes()==b''.join(struct.pack('<5I',*v) for v in model.events)
        assert pin(row/'data-routes.bin').read_bytes()==pin(row/'undefined-events.bin').read_bytes()==b''
        calls=json.loads(pin(row/'calls.json').read_text());assert calls==[{('import' if k=='import_' else k):v for k,v in v.items()} for v in model.routes]
        assert result['source_events']==len(model.events) and result['writer_events']==97 and not result['data_routes']
        faults={4:(4,0x5ac400,0x5ac3a0),5:(4,0x5ac400,0x5ac3a0),6:(4,0x5ac400,0x5ac3a0),7:(4,0x5ac3a0,0x5ac3a0),8:(4,0x5ac400,0x5ac3a0),9:(2,0x5ac3cf,0x5bb5a4),10:(4,0xfffffff0,0x5ac3a0),11:(4,0x5ac3d5,0x5ac3a0),12:(4,0x5bb5a4,0x5bb5a4)}
    assert (result['fault_reason'],result['fault_site'],result['fault_target'])==faults[control],'Exact first fault attribution'
    for name in ('writer',)+(('entry',) if control>=4 else ()):host(pin(row/f'{name}-host-before.bin').read_bytes(),pin(row/f'{name}-host-after.bin').read_bytes())
    return dict(control=control,whole_source_prefix_predicted=True,first_fault=faults[control],terminal_retry=True)
def observe(row, payload, writer_program, provider_pages, game_page, entry_program, providers, source_pages, data=None, evidence=None):
    data=data or {tag:read_stage(row,tag) for tag in ('writer-before','writer-after','entry-before-invoke','entry-projected','entry-after-fault','retry-after')}
    assert pin(row/'input.bin').read_bytes()==payload, 'Only observed original BEFORE input'
    record=pin(row/'writer-record.bin').read_bytes()
    writer=R.observe(record,payload,writer_program,provider_pages,game_page)
    initial, fx, cpu0, _, _=R.seed(payload)
    before_mem=base_memory(payload,provider_pages,game_page,source_pages)
    equal(data['writer-before'],stage(initial,fx,struct.pack('<10I',*cpu0),before_mem),'Entire writer BEFORE')
    final=bytearray(initial)
    for o,name in zip(N.OFFSETS,N.REGS):F.put(final,o,writer.r[name])
    for o,b in N.FLAGS:final[o]=(writer.flags>>b)&1
    F.put(final,2472,writer.pc); F.put(final,2768,writer.cw,2); F.put(fx,0,writer.cw,2)
    after_mem=copy.deepcopy(before_mem)
    for i,a in enumerate(N.PAGES):after_mem[a]=writer.memory[4096*i:4096*(i+1)]
    equal(data['writer-after'],stage(final,fx,cpu(final),after_mem),'Entire source-predicted writer AFTER')
    entry_cpu=bytearray(cpu(final)); F.put(entry_cpu,16,FRAME+4); F.put(entry_cpu,36,0xfffffff0)
    equal(data['entry-before-invoke'],stage(final,fx,entry_cpu,after_mem),'Persistent carry plus declared outer CPU transition')
    entry=Entry(entry_program,providers,final,after_mem).run()
    projected_state, projected_cpu, projected_mem=entry.projected
    equal(data['entry-projected'],stage(projected_state,fx,projected_cpu,projected_mem),'Actual outer frame and only State ESP/EIP projection')
    expected=stage(entry.state,fx,entry.runtime_cpu,entry.mem)
    equal(data['entry-after-fault'],expected,'Whole stopped entry source prediction')
    equal(data['retry-after'],expected,'Poisoned retry retains whole stopped prefix')
    evidence=evidence or {name:pin(row/name).read_bytes() for name in ('entry-events.bin','data-routes.bin','calls.json','result.json','undefined-events.bin')}
    assert evidence['entry-events.bin']==b''.join(struct.pack('<5I',*v) for v in entry.events),'Every native consumer event'
    assert evidence['data-routes.bin']==b''.join(struct.pack('<5I',*v) for v in entry.data_routes),'Exact data ownership route'
    assert evidence['undefined-events.bin']==struct.pack('<I',0x5ac41f),'One exact undefined AF representative site'
    calls=json.loads(evidence['calls.json'])
    assert calls==[{('import' if k=='import_' else k):v for k,v in v.items()} for v in entry.routes],'Completed/incomplete call ledger'
    result=json.loads(evidence['result.json'])
    assert result['passed'] and result['writer_complete'] and result['entry_executed'] and result['fault_reason']==1 and result['fault_site']==0x5ac428 and result['fault_target']==0x5bb50c and result['poisoned_retry']
    assert result['source_events']==len(entry.events) and result['writer_events']==97 and result['data_routes']==1 and result['actual_query_BOOL']==entry.raw_load(0x78037c2c)
    for name in ('writer','entry'):host(pin(row/f'{name}-host-before.bin').read_bytes(),pin(row/f'{name}-host-after.bin').read_bytes())
    return entry,data
def main(build, capture, out):
    assert out.parent==ROOT/'reports/m4-crt-entry-data' and not out.exists();out.mkdir()
    (out/'review-source.py').write_bytes(Path(__file__).read_bytes())
    try:
        receipt=json.loads(pin(build/'build.json').read_text(encoding='utf-8-sig')); assert receipt['passed']
        for group in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
            for p,h in receipt[group].items():pin(p,h)
        game_path=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
        provider_path=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
        game=N.PE.PEImage(game_path.read_bytes());provider=N.PE.PEImage(provider_path.read_bytes())
        tool=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe','a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
        entry,command=E.decode(tool,game,game_path,0x5ac3a0,0x5ac42e,out,'entry-source')
        leaf,leaf_command=E.decode(tool,game,game_path,0x5ac5c0,0x5ac5c1,out,'leaf-source');entry.update(leaf)
        providers,provider_command=E.decode(tool,provider,provider_path,0x78004625,0x7800463b,out,'provider-source')
        writer_program,provider_pages,game_page=R.source_material()
        original=R.originals(pin(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin','cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2').read_bytes())
        payloads=[R.project(v) for v in original[:24]]
        source_pages={a:mapped(game,a) for a in (0x736000,0x9a1000)}
        source_pages[0x5ac3a0]=game.read(game.rva_range(0x5ac3a0-game.image_base,430)[0],430)
        rows=[]; controls=[]; causal_rows=[]
        for level in ('O0','O2'):
            root=capture/f'native-{level}';assert pin(root/'COMPLETE').read_bytes()==b'COMPLETE'
            for i,payload in enumerate(payloads):
                row=root/f'row-{i}';entry_model,data=observe(row,payload,writer_program,provider_pages,game_page,entry,providers,source_pages)
                rows.append(dict(level=level,id=i,whole_State=3504,whole_FX=512,whole_pages=11,writer_events=97,consumer_events=len(entry_model.events),source_PCs=entry_model.visited,provider_PCs=entry_model.provider_PCs))
                if i==0:
                    changes=[('writer-after','state.bin',3400),('entry-before-invoke','state.bin',2472),('entry-before-invoke','fx.bin',24),('entry-after-fault','state.bin',2065),('entry-after-fault','state.bin',2080),('entry-after-fault','state.bin',2472),('entry-after-fault','runtime-cpu.bin',36),('retry-after','state.bin',3400)]
                    changes += [('entry-after-fault',f'page-{a}.bin',0) for a in PAGES]
                    changes += [('entry-after-fault','page-10096640.bin',0x7e4),('entry-after-fault','crt-globals.bin',4),('entry-after-fault','tib-0.bin',0)]
                    for phase,file,offset in changes:
                        bad={k:dict(v) for k,v in data.items()};b=bytearray(bad[phase][file]);b[offset]^=1;bad[phase][file]=bytes(b)
                        try:observe(row,payload,writer_program,provider_pages,game_page,entry,providers,source_pages,bad)
                        except AssertionError:controls.append(dict(level=level,phase=phase,file=file,offset=offset,rejected=True))
                        else:raise AssertionError('Corrupted whole-state/page carry accepted')
                    evidence={name:pin(row/name).read_bytes() for name in ('entry-events.bin','data-routes.bin','calls.json','result.json','undefined-events.bin')}
                    for file in ('entry-events.bin','data-routes.bin','undefined-events.bin'):
                        bad=dict(evidence);v=bytearray(bad[file]);v[0]^=1;bad[file]=bytes(v)
                        try:observe(row,payload,writer_program,provider_pages,game_page,entry,providers,source_pages,evidence=bad)
                        except AssertionError:controls.append(dict(level=level,file=file,offset=0,rejected=True))
                        else:raise AssertionError('Corrupted source event/data ownership accepted')
                    for index,key in ((0,'completed'),(1,'target'),(4,'return_pc')):
                        bad=dict(evidence);v=json.loads(bad['calls.json']);v[index][key]=not v[index][key] if isinstance(v[index][key],bool) else v[index][key]^1;bad['calls.json']=json.dumps(v).encode()
                        try:observe(row,payload,writer_program,provider_pages,game_page,entry,providers,source_pages,evidence=bad)
                        except AssertionError:controls.append(dict(level=level,ledger=index,key=key,rejected=True))
                        else:raise AssertionError('Corrupted actual call ledger accepted')
            for i in range(24,36):
                row=root/f'row-{i}';v=causal(row,payloads[0],writer_program,provider_pages,game_page,entry,providers,source_pages,i-23);v['level']=level;causal_rows.append(v)
        PINS.update(R.PINS);PINS.update(N.PINS);PINS.update(E.PINS);PINS.update(F.PINS)
        pin(__file__);pin(sys.executable)
        report=dict(passed=True,scope='Independent BEFORE-only producer and source-decoded consumer composition at required matherr stop',records=len(rows),rows=rows,whole_State_bytes=3504,whole_FX_bytes=512,whole_pages=11,source_identity_bytes=430,original_BEFORE_rows=24,writer_events=len(rows)*97,consumer_events=sum(v['consumer_events'] for v in rows),observer_corruption_denials=controls,actual_compiled_causal_cases=causal_rows,host_direct_boundary_records=138,author_model_imported=False,AF_undefined_representative_generalized=False,source_commands=[command,leaf_command,provider_command],full_CRT=False,original_entry_executed=False,full_joint_startup=False,whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json')
        for p in out.iterdir():
            if p.is_file():pin(p)
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,records=len(rows),consumer_events=report['consumer_events'],corruptions=len(controls),report_sha256=sha(out/'report.json'))))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(*[Path(p).resolve() for p in sys.argv[1:]])
