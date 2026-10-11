"""Read-only physical frontier and bounded literal path review; no execution credit."""
from __future__ import annotations
import hashlib, importlib.util, json, re, struct, sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
TARGETS = (0x40F0E0, 0x4795F0, 0x47F5F0, 0x4B5220)
PINS: dict[str, str] = {}

def pin(name, expected=None):
    p = (ROOT / name).resolve()
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    if expected is not None:
        assert h == expected, (p, h)
    PINS[str(p)] = h
    return p

def load(name, expected=None):
    return json.loads(pin(name, expected).read_bytes())

spec = importlib.util.spec_from_file_location('review_pe', pin('tools/analysis/pe.py', 'bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638'))
PE = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PE)
image = PE.PEImage(pin('MW3/Mech3.exe', '95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())

def physical(a, n):
    off, _ = image.rva_range(a-image.image_base, n)
    return image.data[off:off+n]

def initial_byte(a):
    r = a-image.image_base
    for s in image.sections:
        d = r-s['virtual_address']
        if 0 <= d < max(s['raw_size'], s['virtual_size']):
            return image.data[s['raw_offset']+d] if d < s['raw_size'] else 0
    raise ValueError(f'unmapped initial byte {a:08X}')

def number(s):
    return int(s.strip(), 0)

class LiteralPrefix:
    """Integer path/geometry only. Stops BEFORE registration CALL, never substitutes an API."""
    def __init__(self, root, rows, seed=0):
        self.root, self.rows, self.pc = root, rows, root
        self.reg = {k: (0x13579BDF ^ (i*0x11111111) ^ seed) & 0xFFFFFFFF for i,k in enumerate(('eax','ebx','ecx','edx','esi','edi','ebp'))}
        self.reg['esp'] = 0x20001FFC
        self.mem = {}
        self.writes, self.reads, self.calls, self.rets, self.reached = [], [], [], [], []
        self.zf = False
        self.write(0x20001FFC, 4, 0x410A80, 'declared research frame')
        self.write(0x7FFDE000, 4, 0xFFFFFFFF, 'declared Runtime FS0')
        self.writes.clear()

    def address(self, text):
        q = re.search(r'\[([^]]+)\]', text).group(1).replace(' ', '')
        total = 0
        for term in re.findall(r'[+-]?[^+-]+', q):
            sign = -1 if term.startswith('-') else 1
            term = term.lstrip('+-')
            if '*' in term:
                a,b=term.split('*'); v=(self.reg[a] if a in self.reg else number(a))*(self.reg[b] if b in self.reg else number(b))
            else:
                v = self.reg[term] if term in self.reg else number(term)
            total += sign*v
        if 'fs:' in text: total += 0x7FFDE000
        return total & 0xFFFFFFFF

    def bits(self, text):
        return 1 if 'byte ptr' in text else 2 if 'word ptr' in text and 'dword ptr' not in text else 4

    def read(self, a, n):
        b = []
        for x in range(a,a+n):
            if x in self.mem: b.append(self.mem[x])
            elif 0x20001000 <= x < 0x20002000: b.append(0)
            else: b.append(initial_byte(x))
        v=int.from_bytes(bytes(b),'little')
        self.reads.append(dict(pc=self.pc,address=a,width=n,value=v))
        return v

    def write(self, a, n, v, label=None):
        v &= (1 << (8*n))-1
        self.mem.update({a+i:x for i,x in enumerate(v.to_bytes(n,'little'))})
        self.writes.append(dict(pc=self.pc,address=a,width=n,value=v,label=label))

    def get(self, text):
        text=text.strip()
        if '[' in text: return self.read(self.address(text),self.bits(text))
        if text in self.reg: return self.reg[text]
        if text in ('ax','bx','cx','dx','si','di','bp','sp'): return self.reg['e'+text] & 0xFFFF
        return number(text.split(' ')[0]) & 0xFFFFFFFF

    def put(self, text, value):
        text=text.strip()
        if '[' in text: return self.write(self.address(text),self.bits(text),value)
        if text in self.reg: self.reg[text]=value & 0xFFFFFFFF
        elif text in ('ax','bx','cx','dx','si','di','bp','sp'):
            r='e'+text;self.reg[r]=(self.reg[r]&0xFFFF0000)|(value&0xFFFF)
        else: raise ValueError(text)

    def push(self, value):
        self.reg['esp']-=4;self.write(self.reg['esp'],4,value)

    def pop(self):
        v=self.read(self.reg['esp'],4);self.reg['esp']+=4;return v

    def run(self):
        for _ in range(1024):
            row=self.rows[self.pc]; op=row['mnemonic']; operands=[x.strip() for x in row['operands'].split(',') if x.strip()]
            nextpc=self.pc+row['size']; self.reached.append(self.pc)
            if op=='call' and operands[0].startswith('0x5ac140'):
                self.registration=dict(pc=self.pc,callback=self.read(self.reg['esp'],4),frontier='before literal registration CALL')
                return
            if op=='mov': self.put(operands[0],self.get(operands[1]))
            elif op=='lea':self.put(operands[0],self.address(operands[1]))
            elif op=='push': self.push(self.get(operands[0]))
            elif op=='pop':self.put(operands[0],self.pop())
            elif op in ('xor','or','add'):
                a,b=self.get(operands[0]),self.get(operands[1]);v=a^b if op=='xor' else a|b if op=='or' else (a+b)&0xFFFFFFFF
                self.put(operands[0],v);self.zf=v==0
            elif op=='dec':v=(self.get(operands[0])-1)&0xFFFFFFFF;self.put(operands[0],v);self.zf=v==0
            elif op=='test': self.zf=(self.get(operands[0])&self.get(operands[1]))==0
            elif op in ('je','jne'):
                if self.zf == (op=='je'): nextpc=self.get(operands[0])
            elif op=='jmp':nextpc=self.get(operands[0])
            elif op=='call':
                target=self.get(operands[0]);slot=self.address(operands[0]) if '[' in operands[0] else None
                ecx=self.reg['ecx'];self.push(nextpc)
                self.calls.append(dict(pc=self.pc,target=target,slot=slot,ECX=ecx,frame=self.reg['esp'],return_pc=nextpc,argument=self.read(self.reg['esp']+4,4) if target in (0x40E820,0x59FF80) else None))
                nextpc=target
            elif op=='ret':
                frame=self.reg['esp'];nextpc=self.pop();cleanup=self.get(operands[0]) if operands else 0;self.reg['esp']+=cleanup
                self.rets.append(dict(pc=self.pc,frame=frame,return_pc=nextpc,cleanup=cleanup,ECX=self.reg['ecx'],EAX=self.reg['eax']))
            else:raise ValueError(f'Unsupported literal prefix operation {self.pc:08X}: {op}')
            self.pc=nextpc
        raise ValueError('bounded literal path exhausted')

def main(name):
    out=ROOT/'reports/m4-next-review'/name
    assert not out.exists();out.mkdir(parents=True)
    parent=load('reports/m4-joint-startup116-root/acceptance-r1/report.json','de76b4e006e5ad2ce0b90f634054379f2271abd14ecb8591643c24e72cc4c0e6')
    assert parent['passed'] and parent['connected_roots']==116 and not parent['whole_M4_complete']
    old=load('reports/m4-container-source/recovery-r3/instruction-contracts.json')
    selected=old['selected_order']; assert len(selected)==116
    table=[dict(slot=a,entry=struct.unpack('<I',physical(a,4))[0]) for a in range(0x5E0000,0x5E0244,4)]
    table=[r for r in table if r['entry']];assert len(table)==144 and all(r in table for r in selected)
    remaining=load('reports/m4-joint-startup116-root/next-frontier-r1/remaining-roots.json','d2faf2654877f203cef768634038254a7072bcdcdc4948bda3e9e93988ea3152')
    assert [dict(slot=r['slot'],entry=r['entry']) for r in remaining]==[r for r in table if r['entry'] not in {s['entry'] for s in selected}]
    graphs=load('reports/m4-service-initializers/static-r1/game-all-initializer-graphs.json','da2482873e1678a0a2493ed7f60421440447c43e63826b53f2d5b09cf573ba5a')
    known={}
    for r in remaining:
        for entry in r['local_entries']:
            for row in graphs[str(entry)]['instructions']:
                raw=bytes.fromhex(row['bytes']);assert physical(row['pc'],len(raw))==raw
                assert row['pc'] not in known or known[row['pc']]==raw
                known[row['pc']]=raw
    source=load('reports/m4-next-source/recovery-r1/report.json','99e59ac4b9adeb98f2227361f80db78e12eead87e35212d71b4147a8ba9effeb')
    fresh=load('reports/m4-next-source/recovery-r1/game-normal-graphs.json')
    interface=load('reports/m4-next-source/recovery-r1/indirect-call-inputs.json')
    frames=load('reports/m4-next-source/recovery-r1/FS-frame-contracts.json')
    assert {r['entry'] for r in source['roots']}==set(TARGETS)
    rows={}
    for graph in fresh.values():
        for row in graph['instructions']:
            assert physical(row['pc'],row['size'])==bytes.fromhex(row['bytes'])
            rows[row['pc']]=row
    assert len(rows)==184 and sum(r['size'] for r in rows.values())==596
    # Independently enumerated physical branch/code anchors, beyond supplied JSON geometry.
    anchors={0x59FDB3:'c706e0c05b00',0x59FF64:'8b11',0x59FF6E:'ff521c',0x59FF80:'8b44240485c07419',0x59FFA1:'c20400',0x59FBAB:'ff1514fd5c00',0x59FDC5:'ff1500c15b00'}
    for a,h in anchors.items():assert physical(a,len(bytes.fromhex(h)))==bytes.fromhex(h)
    cells={a:struct.unpack('<I',physical(a,4))[0] for a in (0x5CFD14,0x5BC100,0x5BC0FC,0x5F49B8)}
    assert cells=={0x5CFD14:0x40E820,0x5BC100:0x59FF00,0x5BC0FC:0x59FF80,0x5F49B8:12}
    results=[]
    for root in TARGETS:
        machines=[]
        for seed in (0,0xFFFFFF00):
            m=LiteralPrefix(root,rows,seed);m.run();machines.append(m)
        m=machines[0]
        actual=[]
        for call in m.calls:
            if call['slot'] is None:continue
            matching=[c for c in interface if c['root']==root and c['CALL_pc']==call['pc']]
            assert len(matching)==1;c=matching[0]
            for field,key in [('target','target'),('slot','slot'),('return_pc','return_pc'),('ECX','entry_ECX'),('argument','argument')]:assert call[field]==c[key],(root,field,call,c)
            rets=[r for r in m.rets if r['frame']==call['frame'] and r['return_pc']==call['return_pc']]
            assert len(rets)==1 and rets[0]['cleanup']==c['RET_cleanup']
            if call['pc']==0x59FF6E:
                prior=[s for s in m.writes if s['pc']==0x59FDB3 and s['address']==call['ECX']]
                assert len(prior)==1 and prior[0]['value']==0x5BC0E0
                assert not any(s['address']==call['ECX'] and s['pc']!=0x59FDB3 for s in m.writes[:m.writes.index(prior[0])])
                assert 0x59FF88 not in m.reached
            actual.append(dict(**call,RET=rets[0]))
        assert len(actual)==sum(c['root']==root for c in interface)
        assert m.registration['callback']==next(r['registration']['callback'] for r in source['roots'] if r['entry']==root)
        # Arbitrary incoming register patterns leave the same object effects and reached prefix.
        def gamewrites(x):return [v for v in x.writes if image.image_base<=v['address']<image.image_base+image.size_of_image]
        assert gamewrites(m)==gamewrites(machines[1]) and m.reached==machines[1].reached
        if root==0x47F5F0:
            assert len(frames)==1 and frames[0]['root']==root
            fswrites=[w for w in m.writes if w['address']==0x7FFDE000]
            assert [w['pc'] for w in fswrites]==[0x4824AE,0x4824ED] and fswrites[-1]['value']==0xFFFFFFFF
            assert m.read(fswrites[0]['value']+4,4)==0x5B41C8
            assert m.read(fswrites[0]['value'],4)==0xFFFFFFFF
            assert m.read(fswrites[0]['value']+8,4)==0
        results.append(dict(root=root,reached_prefix_instructions=len(m.reached),indirect_calls=actual,source_object_writes=gamewrites(m),registration_frontier=m.registration,FS_restored=True,nonzero59FF80_path_reached=False))
    fixtures=[]
    for stem in ('40e820','59ff00','4b64f0','5b7978','5b7898'):
        base=int(stem,16);p=pin(f'reports/m4-next-review/decoded-r1/{stem}.bin');assert physical(base,p.stat().st_size)==p.read_bytes()
        for ext in ('.s','.obj','.txt'):pin(f'reports/m4-next-review/decoded-r1/{stem}{ext}')
        fixtures.append(dict(base=base,extent=p.stat().st_size,physical_bytes_sha256=PINS[str(p)],execution=False))
    assert physical(0x4B64F0,5)==bytes.fromhex('e90b000000') and physical(0x4B6506,2)==bytes.fromhex('d9ff') and physical(0x4B6552,2)==bytes.fromhex('d9ff') and physical(0x4B6560,2)==bytes.fromhex('d9ff') and physical(0x4B6568,1)==b'\xc3'
    pin(__file__)
    (out/'literal-prefixes.json').write_text(json.dumps(results,indent=2)+'\n');pin(out/'literal-prefixes.json')
    report=dict(passed=True,scope='Independent physical frontier and integer path geometry review. Authored value interpreter stops before registry CALL; no imported API substitution, candidate execution, original execution, State/flags/FP equivalence or initializer acceptance.',counts=dict(remaining_roots=len(remaining),physical_inventory_rows=len(known),physical_inventory_bytes=sum(map(len,known.values())),reviewed_four_root_rows=len(rows),reviewed_four_root_bytes=sum(r['size'] for r in rows.values()),finite_indirect_calls=sum(len(r['indirect_calls']) for r in results),normal_FS_frames=1,incoming_register_patterns=2),recommended_immediate_roots=list(TARGETS),fixed_cells=[dict(address=a,page=a&~0xFFF,value=v) for a,v in cells.items()],normal_geometry_passed=True,new_imported_providers=0,new_allocations=0,nonzero59FF80_pointee_path_admitted=False,raw5F49B8_prefix_effect_required=True,minimum_execution_gates=['genuine original selected120 table sequence BEFORE-derived complete integer CPU/State/page prefixes','six literal raw-cell/frame/argument/RET observations with vptr source-store provenance','one normal12B FS install/scope/restore frame, handler dispatch excluded','complete persistent provider/owned backing and genuine registry growth/cleanup at O0/O2','compiled causal wrong-cell/vptr/argument/partial-store/private-witness refusal; caller hardware/retry/HeapDestroy closure'],deferred=dict(five_remaining_onexit_roots='Real callback arguments to vector constructor/destructor loops plus static vtable methods need exact call-frame/type/extent provenance, not broad dispatch. Fixed5CFD14 and5BC100 do not alone close all paths.',Lockit_family='Five inventory roots share MSVCP50 lock provider. Four small roots are a potential larger follow-on;4B7F70 additionally requires nine register-indirect call targets and reached closure.',MFC_graph_family='4103F0/410440/459B40 share existing allocator but require closed shared-node ownership and object/predicate callback provenance.',FCOS_4B64F0='Missing-boundary inventory is decoder artifact. Physical root JMP4B6500 contains3FCOS and3FSTP; numerical/status gate required, no credit now.',other_service_families='Three path/format roots plus combinedLockit root share new sprintf/strrchr; font/version/OS/library/codepage roots need genuine new-provider recovery and environment inputs.'),dynamic_control_categories=dict(fixed_game_cells=[0x5CFD14,0x5BC100],instance_vtable_slot=[0x5BC0FC],bounded_switch_table=dict(site=0x482979,table=0x4829E8,entries=10,requires_source_index_bound=True),constructor_frame_callback=dict(site=0x5AC2DB,requires_actual_function_argument_and_stride_extent=True),atexit_and_FS_handler_literals='Stored identities are not callback/unwind execution coverage.'),decoded_fixtures=fixtures,physical_fixture_vma_policy='COFF objdump prints offsets despite adjust-vma; only original base plus decoded offsets are original addresses. First RET/helper bounds exclude adjacent code.',native_executed=False,original_executed=False,initializer_credit=0,whole_M4_complete=False,files=PINS)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,report=str(out/'report.json'),sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest(),counts=report['counts'])))

if __name__=='__main__':main(sys.argv[1])
