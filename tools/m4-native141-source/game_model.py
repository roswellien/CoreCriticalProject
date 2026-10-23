"""Independent constructor game/provider interpreter from complete own BEFORE.

No native code, host allocator, observed root AFTER, or predicted heap capacity
is used.  External Win32 facts are finite scalar/initial-buffer inputs; MFC,
CRT rounding, list publication, getter routing, FS and _onexit remain literal.
"""
from pathlib import Path
import copy, hashlib, importlib.util, json, struct, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
sp = importlib.util.spec_from_file_location('constructor_source_parent130', R/'reports/m4-fps-original/source-preparation-r4/game_model.py')
G = importlib.util.module_from_spec(sp); sp.loader.exec_module(G)
I = G.I
ROOTS = (0x4103f0, 0x410440, 0x459b40)
READ_FLAGS = {'je':('ZF',),'jne':('ZF',),'sete':('ZF',),'setne':('ZF',),
              'jb':('CF',),'jae':('CF',),'jbe':('CF','ZF'),'ja':('CF','ZF'),
              'jl':('SF','OF'),'jge':('SF','OF'),'jle':('SF','OF','ZF'),
              'jg':('SF','OF','ZF'),'js':('SF',),'jns':('SF',),
              'jp':('PF',),'jnp':('PF',),'sbb':('CF',),'adc':('CF',)}
BITS = dict(CF=0,PF=2,AF=4,ZF=6,SF=7,DF=10,OF=11)

def checked(path, digest):
    raw=Path(path).read_bytes(); I.need(hashlib.sha256(raw).hexdigest()==digest,'Exact constructor source preparation input'); return json.loads(raw)

def source_program(preparation):
    d=json.loads(Path(preparation).read_bytes()); I.need(d['passed'] and not d['native_executed'],'Source-only preparation')
    rows=checked(d['instructions'],d['instructions_sha256'])['instructions']
    cb=checked(d['callbacks'],d['callbacks_sha256'])['State_offsets_by_original_PC']
    program,callbacks=G.source_program()
    for row in rows:
        pc=row['pc']
        if pc in program: I.need((program[pc]['width'],program[pc]['bytes_hex'])==(row['width'],row['bytes_hex']),'Whole identical shared constructor source bytes')
        program[pc]=row
    for pc, offsets in cb.items():
        pc=int(pc); offsets=tuple(offsets); I.need(pc not in callbacks or callbacks[pc]==offsets,'Same literal undefined callback order'); callbacks[pc]=offsets
    return program, callbacks

class Machine(G.Machine):
    def __init__(self,*args,owner_roles=None,source_imports=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.constructor_root=None; self.constructor_active=False
        self.constructor_owners=copy.deepcopy(owner_roles or [])
        self.constructor_imports=source_imports or {}
        self.constructor_FS=[]; self.constructor_FS_events=[]; self.constructor_FS_serial=0
        self.constructor_getters=[]; self.constructor_calls=[]; self.constructor_publications=[]
        self.constructor_flag_consumers=[]; self.arch_undefined={}; self.root_starts=[]
        self.initial_flags=struct.unpack_from('<I',self.cpu,32)[0]
    def begin_constructor(self,root):
        I.need(not self.constructor_active and root in ROOTS and self.cursor==root,'True selected constructor entry')
        I.need(self.word(I.BASE['ds'])==self.word(I.BASE['es'])==self.word(I.BASE['ss'])==0 and not self.flag('DF'),'Actual flat forward source constructor domain')
        self.constructor_root=root; self.constructor_active=True
        self.root_starts.append(dict(root=root,PC_index=len(self.PCs),access_index=len(self.accesses),CPU=self.projected_cpu(),FS_head=int.from_bytes(self.bytes(self.word(I.BASE['fs']),4),'little')))
    def end_constructor(self):
        I.need(self.constructor_active and not self.constructor_FS,'Literal whole constructor and normal source FS scopes returned')
        self.constructor_active=False; self.constructor_root=None
    def owner(self,address,size):
        matches=[o for o in self.constructor_owners if o.get('live',True) and o['guest']<=address and address+size<=o['guest']+o['extent']]
        I.need(len(matches)==1,'Exactly one current measured/actual source MFC owner extent')
        o=matches[0]; I.need(o['requested']<=o['extent'] and len(bytes.fromhex(o['initial_hex']))==o['extent'],'Whole initial actual HeapAlloc extent and distinct request')
        return o
    def add_owner(self,owner):
        I.need(not any(o['guest']==owner['guest'] or o['generation']==owner['generation'] for o in self.constructor_owners if o.get('live',True)),'Distinct current source allocation occurrence')
        self.constructor_owners.append(copy.deepcopy(owner)); self.owner(owner['guest'],owner['requested'])
    def projected_cpu(self):
        flags=self.initial_flags
        for name,bit in BITS.items(): flags=(flags&~(1<<bit))|(int(bool(self.flag(name)))<<bit)
        return tuple(self.reg(k) for k in ('eax','ecx','edx','ebx','esp','ebp','esi','edi'))+(flags,self.cursor)
    def read(self,address,size=4,domain='source',pc=None):
        site=self.word(2472) if pc is None else pc
        value=super().read(address,size,domain,pc)
        if not self.constructor_active or domain!='source': return value
        if address==self.word(I.BASE['fs']):
            I.need(size==4,'Complete source FS head read'); self.constructor_FS_events.append(dict(root=self.constructor_root,PC=site,kind='read',head=value,depth=len(self.constructor_FS),source_access_index=len(self.accesses)-1))
        if size==4 and (site,address)==(0x5abd1a,0x5bb4c8):
            I.need(value==0x80000339,'Physical game ordinal825 import'); self.import_projections.append((6,site,address,value,0x5f401782,0,0,0)); return 0x5f401782
        fact=self.constructor_imports.get((site,address))
        if fact is not None:
            I.need(size==4 and value==fact['raw'],'Exact own branch loaded/raw named source import')
            return fact['target']
        return value
    def write(self,address,value,size=4,domain='source',pc=None):
        site=self.word(2472) if pc is None else pc
        old_head=int.from_bytes(self.bytes(address,size),'little') if self.constructor_active and domain=='source' and address==self.word(I.BASE['fs']) else None
        result=super().write(address,value,size,domain,pc)
        if not self.constructor_active or domain!='source': return result
        if old_head is not None:
            I.need(size==4,'Complete source FS head write')
            if self.constructor_FS and value==self.constructor_FS[-1]['previous']:
                f=self.constructor_FS.pop(); raw=self.bytes(f['frame'],12)
                I.need(old_head==f['frame'] and struct.unpack('<I',raw[:4])[0]==f['previous'],'Actual complete source FS LIFO restoration')
                kind='restore'
            else:
                I.need(value==self.reg('esp') and int.from_bytes(self.bytes(value,4),'little')==old_head,'Literal actual current ESP source FS installation')
                self.constructor_FS_serial+=1; f=dict(frame=value,previous=old_head,invocation=self.constructor_FS_serial); self.constructor_FS.append(f); kind='install'
            self.constructor_FS_events.append(dict(root=self.constructor_root,PC=site,kind=kind,frame=f['frame'],previous=f['previous'],raw12_hex=self.bytes(f['frame'],12).hex(),invocation=f['invocation'],depth=len(self.constructor_FS),source_access_index=len(self.accesses)-1))
        for owner in self.constructor_owners:
            if owner.get('live',True) and owner['guest']<=address and address+size<=owner['guest']+owner['extent']:
                I.need(address+size<=owner['guest']+owner['requested'],'Literal writes never fabricate capacity/tail bytes')
                self.constructor_publications.append(dict(root=self.constructor_root,PC=site,address=address,width=size,value=value,owner=owner['guest'],generation=owner['generation'],source_access_index=len(self.accesses)-1))
        return result
    def getter(self):
        receiver=self.reg('ecx'); vptr=int.from_bytes(self.bytes(receiver,4),'little')
        I.need(receiver==0x604008 and self.reg('edx')==vptr==0x5bcc68 and int.from_bytes(self.bytes(vptr+0x18,4),'little')==0x40a850,'Actual source getter receiver/held vptr/physical readonly target')
        header=int.from_bytes(self.bytes(0x603fdc,4),'little'); count=int.from_bytes(self.bytes(0x603fe0,4),'little')
        I.need(header and count<256,'Carried genuine shared list, never an invented zero list')
        node=header; seen=set(); matches=[]; graph=[]
        while True:
            I.need(node not in seen and len(seen)<256,'Finite distinct whole cyclic source list'); seen.add(node)
            own=self.owner(node,12); raw=self.bytes(node,own['extent']); nxt,prev,payload=struct.unpack_from('<3I',raw)
            I.need(int.from_bytes(self.bytes(nxt+4,4),'little')==node and int.from_bytes(self.bytes(prev,4),'little')==node,'Whole current literal forward/backlinks')
            graph.append(dict(owner=node,generation=own['generation'],next=nxt,previous=prev,payload=payload,whole_hex=raw.hex()))
            if node!=header and payload==receiver: matches.append(node)
            node=nxt
            if node==header: break
        I.need(len(seen)==count+1 and len(matches)==1,'Exactly one published non-sentinel getter owner')
        self.constructor_getters.append(dict(root=self.constructor_root,PC=0x58b183,frame=self.reg('esp'),receiver=receiver,vptr=vptr,slot=vptr+0x18,target=0x40a850,header=header,count=count,graph=graph,published_owner=matches[0],source_access_index=len(self.accesses)))
    def step(self):
        if not self.constructor_active: return super().step()
        pc=self.cursor; I.need(pc!=0x56fea0,'Cold recursive constructor frontier is explicitly unadmitted')
        row=self.program.get(pc); I.need(row is not None,'Current literal constructor source closure')
        op=row['mnemonic']
        flags=READ_FLAGS.get(op,())
        I.need(not any(f in self.arch_undefined for f in flags),'No architecturally undefined flag can select a constructor source effect')
        if flags: self.constructor_flag_consumers.append(dict(PC=pc,flags=list(flags),values={f:self.flag(f) for f in flags},source_instruction_index=len(self.PCs),all_architecturally_defined=True))
        if pc==0x58b183: self.getter()
        if op=='setne':
            self.steps+=1; self.word(2472,pc); self.PCs.append(pc); self.emit('instruction-before',row=row); self.cursor=pc+row['width']; self.destination(row['decoded_operands'][0],not self.flag('ZF')); self.emit('instruction-after',row=row)
        else: super().step()
        defined=set()
        if op in ('cmp','add','sub','sbb','neg'): defined=set(I.FLAGS)-{'DF'}
        elif op in ('inc','dec'): defined=set(I.FLAGS)-{'CF','DF'}
        elif op in ('test','and','or','xor'): defined={'CF','PF','ZF','SF','OF'}; self.arch_undefined['AF']=pc
        elif op in ('sar','shr','shl'):
            # Count is immediate or CL in this finite corpus; neither is changed
            # by the source shift.  A zero count preserves every prior flag.
            count=self.operand(row['decoded_operands'][1])&31
            if count:
                defined={'CF','PF','ZF','SF'}; self.arch_undefined['AF']=pc
                if count==1: defined.add('OF')
                else: self.arch_undefined['OF']=pc
        for flag in defined: self.arch_undefined.pop(flag,None)
        return self
    def result(self):
        d=super().result(); d.update(constructor_FS=self.constructor_FS_events,constructor_getters=self.constructor_getters,constructor_owned_writes=self.constructor_publications,constructor_flag_consumers=self.constructor_flag_consumers,constructor_owners=self.constructor_owners,undefined_architectural_flags=dict(self.arch_undefined),whole_undefined_flags_equality_claim=False,HeapSize_capacity_inferred=False); return d

class ActualAPIs:
    """Finite measured Win32 responses after full literal frame/argument checks.

    fact owns {site,target,argc,args,before_cpu,after_cpu,initial_allocations,
    input_buffers,output_buffers}. Only EAX/ECX/EDX/EFLAGS and documented API
    buffers cross the API seam; no source State/CPU/FX AFTER is installed.
    """
    def __init__(self,facts): self.facts=copy.deepcopy(facts); self.index=0
    def __call__(self,m,target):
        I.need(self.index<len(self.facts),'Finite actual source API exhaustion')
        f=self.facts[self.index]; site=m.PCs[-1]; frame=m.reg('esp')
        I.need((site,target)==(f['site'],f['target']) and f['argc']==len(f['args']),'Exact owning source API site/target/arity')
        ret=int.from_bytes(m.bytes(frame,4),'little'); args=struct.unpack('<'+'I'*f['argc'],m.bytes(frame+4,f['argc']*4))
        I.need(tuple(f['args'])==args,'Complete source-derived actual API arguments')
        before=list(m.projected_cpu()); observed=f['before_cpu']
        I.need(before[:8]==observed[:8] and frame==observed[4],'Whole API entry GPR/true caller frame')
        for name,bit in BITS.items():
            if name not in m.arch_undefined: I.need(((before[8]^observed[8])>>bit)&1==0,'Defined source API entry flag')
        for b in f.get('input_buffers',[]): I.need(m.bytes(b['address'],b['bytes'])==bytes.fromhex(b['hex']),'Whole measured actual API input')
        for a in f.get('initial_allocations',[]):
            raw=bytes.fromhex(a['initial_hex']); I.need(len(raw)==a['extent'] and not any(p<a['guest']+a['mapped_bytes'] and a['guest']<p+len(b) for p,b in m.memory.items()),'Fresh disjoint full actual source allocation backing')
            tail=bytes.fromhex(a['mapped_tail_hex']); I.need(len(raw)+len(tail)==a['mapped_bytes'],'Complete own branch mapping tail input')
            m.memory[a['guest']]=bytearray(raw+tail); m.add_owner(a)
        outputs=[(b['address'],bytes.fromhex(b['hex'])) for b in f.get('output_buffers',[])]
        after=f['after_cpu']; I.need(after[4]==frame+4*(f['argc']+1) and after[9]==ret and after[3:4]+after[5:8]==observed[3:4]+observed[5:8],'Actual API normal stdcall/nonvolatile return')
        m.api_return(site,f['argc'],after[0],outputs); m.reg('ecx',after[1]); m.reg('edx',after[2])
        for name,bit in BITS.items(): m.flag(name,(after[8]>>bit)&1)
        m.arch_undefined.clear(); self.index+=1
    def complete(self): I.need(self.index==len(self.facts),'Every actual API occurrence consumed exactly once')
