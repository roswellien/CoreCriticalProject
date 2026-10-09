"""Independent source extension for the actual matherr caller composition.

Only frozen root source observers are imported. All three added provider pages
come from exact PE file-backed section pages, never standalone fixture patterns.
"""
import copy,hashlib,importlib.util,json,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();v=sha(p);assert h is None or v==h,str(p)
    assert str(p) not in PINS or PINS[str(p)]==v
    PINS[str(p)]=v;return p
spec=importlib.util.spec_from_file_location('root_frozen_entry_data',pin(ROOT/'tools/m4-crt-entry-data-review/observe.py','6f65958d1c7603e4c508ef560dcc443437f0ab551319989f926723bcecbe486e'))
D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
F=D.F;R=D.R;N=D.N
MATH_PAGES=(0x7800b000,0x78039000,0x7803b000)
MATH_ENTRY=0x7800b38f;ZERO=0x780392b8;CALLBACK=0x7803b0c4

class Entry(D.Entry):
    def __init__(self,program,providers,math_program,state,memory,control=0):
        super().__init__(program,providers,state,memory,control)
        self.math_program=math_program;self.math_events=[];self.math_PCs=[];self.math_before=None;self.math_projected=None;self.math_after=None
        self.math_status=[0x5bb50c,F.word(memory[0x5bb000],0x50c),0,0,0,0,0,0,0,0,0,0]
        self.service_cpu=None
        if control==13:F.put(self.mem[0x7800b000],0x38f,0)
        if control==14:F.put(self.mem[0x5bb000],0x50c,self.math_status[1]^1)
        if control==22:F.put(self.mem[0x78039000],0x2b8,F.word(self.mem[0x78039000],0x2b8)^1)
        if control==23:F.put(self.mem[0x7803b000],0xc4,F.word(self.mem[0x7803b000],0xc4)^1)
        self.projected=(bytes(self.state),bytes(self.runtime_cpu),copy.deepcopy(self.mem))
    def store(self,a,v,event=True):
        super().store(a,v,event)
        if self.control==17 and self.pc==0x5ac423:self.raw_store(a,v^1)
    def math_deny(self,pc,address):
        self.math_status[8]=1;self.math_status[10]=pc;self.math_status[11]=address
        self.project(pc);raise D.Stop()
    def math_after_event(self):
        step=self.math_status[5]
        if step==4 and self.control==18:self.raw_store(self.r['esp'],0x5ac42e^1)
        if step==4 and self.control in (19,20):
            register='ebx' if self.control==19 else 'eax'
            self.r[register]^=1
            F.put(self.state,F.OFF[F.REGS.index(register)],self.r[register])
        if step==1 and self.control==21:self.math_status[5]=4
    def math_load(self,a):
        if self.control==21 and a==ZERO:self.math_deny(self.math_pc,a)
        v=self.raw_load(a)
        if a==self.math_status[2] and v!=0x5ac42e:self.math_deny(self.math_pc,a)
        if not self.math_events:self.math_status[4]=v
        self.math_events.append((a,v,4,0));self.math_status[5]+=1;self.math_after_event();return v
    def math_store(self,a,v):
        if (self.control==15 and a==ZERO) or (self.control==16 and a==CALLBACK):self.math_deny(self.math_pc,a)
        self.raw_store(a,v);self.math_events.append((a,v&0xffffffff,4,1));self.math_status[5]+=1;self.math_after_event()
    def run_matherr(self):
        # Runtime already holds the actual CALL-pushed return. The admitted
        # service projects that CPU only; all FP/opaque fields remain carried.
        self.project(MATH_ENTRY,flat=True)
        self.math_status[2]=self.r['esp'];self.math_status[3]=0x5ac42e;self.math_status[6]=1
        self.math_projected=(bytes(self.state),self.service_cpu,copy.deepcopy(self.mem))
        if self.control==24:raise D.Stop()
        pc=MATH_ENTRY
        for _ in range(4):
            size,op,args=self.math_program[pc];self.math_PCs.append(pc)
            self.math_pc=pc
            self.project(pc)
            if op=='mov' and args==['eax','dword ptr [esp + 0x4]']:
                self.r['eax']=self.math_load(self.r['esp']+4)
            elif op=='and' and args==['dword ptr [0x780392b8]','0x0']:
                self.math_load(ZERO)
                self.math_store(ZERO,0)
                self.flags=(self.flags&~0x8d5)|0x44
            elif op=='mov' and args==['dword ptr [0x7803b0c4]','eax']:
                self.math_store(CALLBACK,self.r['eax'])
            elif op=='ret' and not args:
                nxt=self.math_load(self.r['esp']);self.r['esp']+=4;assert nxt==0x5ac42e
                self.project(nxt)
                if self.control in (19,20):self.math_deny(nxt,0)
                self.math_status[9]=1
                self.runtime_cpu=struct.pack('<10I',*[self.r[k] for k in F.REGS],self.flags,nxt)
                self.math_after=(bytes(self.state),self.runtime_cpu,copy.deepcopy(self.mem))
                return
            else:raise AssertionError('Unreviewed source matherr instruction')
            pc+=size
        raise AssertionError('Four-instruction matherr source did not return')
    def run(self):
        super().run()
        if self.control and self.pc!=0x5ac428:return self
        assert self.pc==0x5ac428 and self.r['esp']==D.FRAME-144
        if self.control==14:return self
        self.service_cpu=struct.pack('<10I',*[self.r[k] for k in F.REGS],self.flags,0x5bb50c)
        self.math_before=(bytes(self.state),self.service_cpu,copy.deepcopy(self.mem))
        if self.control in (13,17,22,23):
            self.math_after=(bytes(self.state),self.service_cpu,copy.deepcopy(self.mem));self.runtime_cpu=self.service_cpu
            self.routes.append(dict(site=0x5ac428,target=0x5bb50c,return_pc=0x5ac42e,import_=True,completed=False));return self
        try:self.run_matherr()
        except D.Stop:
            self.math_after=(bytes(self.state),self.service_cpu,copy.deepcopy(self.mem));self.runtime_cpu=self.service_cpu
            self.routes.append(dict(site=0x5ac428,target=0x5bb50c,return_pc=0x5ac42e,import_=True,completed=False));return self
        self.routes.append(dict(site=0x5ac428,target=0x5bb50c,return_pc=0x5ac42e,import_=True,completed=True))
        self.project(0x5ac42e,flat=True)
        self.pc=0x5ac42e;self.visited.append(self.pc)
        size,op,args=self.program[self.pc];assert (op,args)==('add',['esp','0x4'])
        a=self.r['esp'];v=(a+4)&0xffffffff
        bits=int(a+4>0xffffffff)|(int((v&255).bit_count()%2==0)<<2)|(int(bool((a^4^v)&0x10))<<4)|(int(v==0)<<6)|(int(bool(v&0x80000000))<<7)|(int(bool((~(a^4)&(a^v))&0x80000000))<<11)
        self.flags=(self.flags&~0x8d5)|bits;self.r['esp']=v
        self.pc+=size;self.visited.append(self.pc)
        size,op,args=self.program[self.pc];assert (op,args)==('call',['0x5ac5a0'])
        self.push(self.pc+size);self.project(0x5ac5a0)
        regs=[self.r[k] for k in F.REGS];regs[4]+=4
        self.runtime_cpu=struct.pack('<10I',*regs,self.flags,self.pc)
        return self

def source_material(out):
    game_path=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
    provider_path=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    game=N.PE.PEImage(game_path.read_bytes());provider=N.PE.PEImage(provider_path.read_bytes())
    tool=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe','a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
    program,entry_command=D.E.decode(tool,game,game_path,0x5ac3a0,0x5ac436,out,'entry-source')
    leaf,leaf_command=D.E.decode(tool,game,game_path,0x5ac5c0,0x5ac5c1,out,'leaf-source');program.update(leaf)
    providers,provider_command=D.E.decode(tool,provider,provider_path,0x78004625,0x7800463b,out,'three-provider-source')
    math_program,math_command=D.E.decode(tool,provider,provider_path,MATH_ENTRY,MATH_ENTRY+17,out,'matherr-source')
    assert len(math_program)==4
    source_pages={a:D.mapped(game,a) for a in (0x736000,0x9a1000)}
    source_pages[0x5ac3a0]=game.read(game.rva_range(0x5ac3a0-game.image_base,430)[0],430)
    source_pages.update({a:D.mapped(provider,a) for a in MATH_PAGES})
    source_pages[MATH_ENTRY]=provider.read(provider.rva_range(MATH_ENTRY-provider.image_base,17)[0],17)
    assert hashlib.sha256(source_pages[MATH_ENTRY]).hexdigest()=='db28fc73ef336b9925b6cd56a37615599cc224d6a38cdd3b3cf5851c72e77bc9'
    return program,providers,math_program,source_pages,[entry_command,leaf_command,provider_command,math_command]
