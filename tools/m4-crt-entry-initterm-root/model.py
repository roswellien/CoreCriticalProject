"""Independent source model of the actual first null initializer interval."""
import copy,hashlib,importlib.util,json,re,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();v=sha(p);assert h is None or h==v,str(p)
    assert str(p) not in PINS or PINS[str(p)]==v
    PINS[str(p)]=v;return p
def module(name,path,h):
    spec=importlib.util.spec_from_file_location(name,pin(path,h));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
M=module('frozen_control_composition_source',ROOT/'tools/m4-crt-entry-control-root/model.py','da9c2cf73fdc0db5832412bd66f3fd128c4366cc70485ddf4d5bde30f687110f')
D,F,R,N,C=M.D,M.F,M.R,M.N,M.C
THUNK=0x5ac598;SLOT=0x5bb510;PROVIDER=0x780014f8;BEGIN=0x5e0248;END=0x5e024c
NEW_PAGES=(0x5e0000,0x78001000)

class Entry(M.Entry):
    def __init__(self,program,providers,maths,ctrl,init,state,memory,fx,control=0,level='O0'):
        super().__init__(program,providers,maths,ctrl,state,memory,fx,control)
        self.init_program=init;self.init_level=level;self.init_phases={};self.init_accesses=[];self.init_events=[];self.init_undefined=[];self.init_PCs=[]
        self.init_job=[SLOT,0x1ded12,*([0]*14)];self.init_reason='';self.init_frame=0;self.init_ret=0;self.init_first=0;self.init_last=0;self.init_failed=False;self.init_complete=False;self.init_used=False;self.init_step=0
        mutation={37:(0x78001000,0x4f8,0),38:(THUNK,0,0),39:(0x5bb000,0x510,0x1ded12^1),40:(0x5e0000,0x248,0x51e7b0)}.get(control)
        if mutation:
            a,o,value=mutation;F.put(self.mem[a],o,value)
        self.projected=(bytes(self.state),bytes(self.runtime_cpu),copy.deepcopy(self.mem))
    def store(self,a,value,event=True):
        super().store(a,value,event)
        if self.control==47 and self.pc==0x5ac43b:self.raw_store(a,value^1)
    def init_snapshot(self,tag):
        self.init_phases[tag]=(bytes(self.state),bytes(self.runtime_cpu),copy.deepcopy(self.mem),bytes(self.fx))
    def init_event(self,kind,pc,address,value):self.init_events.append((kind,pc,address,value))
    def init_commit(self,pc=None):
        self.project(self.init_pc if pc is None else pc)
    def init_deny(self,why,address=0,pc=None):
        if not self.init_failed:
            self.init_failed=True;self.init_reason=why;self.init_fault_pc=self.init_pc if pc is None else pc;self.init_fault_address=address
        self.init_commit();raise D.Stop()
    def init_access(self,a,value,write):
        pc=self.init_pc
        self.init_accesses.append((pc,a,value,4,write))
        if pc!=THUNK:self.init_step+=1
        if self.control==43 and pc==0x780014f9:
            self.r['esp']=0x20001ffc;self.init_commit()
        if self.control==44 and pc==0x78001512:self.raw_store(self.init_frame,self.init_ret^1)
        if self.control==45 and pc==0x78001513:
            self.r['esi']^=1;self.init_commit()
        if self.control==48 and pc==0x78001502 and self.init_step==3:self.raw_store(self.init_frame+8,END+4)
    def init_read(self,a):
        pc=self.init_pc;stack=lambda v:0x20001000<=v<=0x20001ffc
        allowed=(pc==THUNK and a==SLOT) or (pc==0x780014f9 and a==self.r['esp']+8 and stack(a)) or (pc==0x78001502 and a==self.r['esp']+12 and stack(a)) or (pc==0x78001508 and a==BEGIN) or (pc==0x78001512 and a==self.init_frame-4) or (pc==0x78001513 and a==self.init_frame)
        if not allowed:self.init_deny('Required initterm read outside exact current source operand',a)
        value=self.raw_load(a)
        if pc==0x78001513 and value!=self.init_ret:self.init_deny('Initterm actual return word changed',a)
        self.init_access(a,value,0)
        if pc==0x78001508:self.init_event(7 if value else 4,pc,a,value)
        return value
    def init_write(self,a,value):
        pc=self.init_pc
        assert (pc==PROVIDER and a==self.init_frame-4 and value==self.init_nonvol[2]) or (pc==0x7800150e and a==self.r['esp']-4 and value==0x78001510)
        if self.control==42:self.init_deny('Required checked initterm write fault',a)
        self.raw_store(a,value);self.init_access(a,value,1)
    def init_operand(self,operand):
        if operand.startswith('dword ptr '):
            address=self.address(operand)
            # Mode43 is an injected observer mutation, outside architectural
            # source equivalence. The O2 artifact holds the post-PUSH ESP SSA
            # operand across MOV's read callback; O0 reloads mutated StateESP.
            # Both fail the current-State operand guard before a CMP read.
            if self.control==43 and self.init_pc==0x78001502 and self.init_level=='O2':address=self.init_frame+8
            return self.init_read(address)
        return self.read(operand)
    def null_provider(self):
        for _ in range(32):
            pc=self.init_pc;self.init_PCs.append(pc);self.init_commit()
            size,op,args=self.init_program[pc];nxt=pc+size
            if op=='push':
                address=(self.r['esp']-4)&0xffffffff;value=self.init_operand(args[0])
                self.init_write(address,value);self.r['esp']=address
            elif op=='mov':self.r[args[0]]=self.init_operand(args[1])
            elif op=='cmp':C.X86.arithmetic(self,'cmp',self.init_operand(args[0]),self.init_operand(args[1]),4)
            elif op=='test':
                self.init_undefined.append(pc);C.X86.arithmetic(self,'test',self.init_operand(args[0]),self.init_operand(args[1]),4)
            elif op=='add':
                a,b=self.init_operand(args[0]),self.init_operand(args[1]);self.flags=M.add_flags(self.flags,a,b);self.r[args[0]]=(a+b)&0xffffffff
            elif op=='jmp':nxt=self.init_operand(args[0])
            elif op=='jae':
                if not self.flags&1:nxt=self.init_operand(args[0])
            elif op=='je':
                if self.flags&0x40:nxt=self.init_operand(args[0])
            elif op=='pop':
                address=self.r['esp'];self.r['esp']+=4;self.init_commit()
                self.r[args[0]]=self.init_read(address)
            elif op=='call':
                target=self.init_operand(args[0]);address=(self.r['esp']-4)&0xffffffff
                self.init_write(address,nxt);self.r['esp']=address;self.init_pc=target;self.init_commit()
                self.init_deny('Required initterm callback remains unreviewed',target,pc)
            elif op=='ret':
                value=self.init_read(self.r['esp']);self.r['esp']+=4;self.init_pc=value;self.init_commit()
                if tuple(self.r[x] for x in ('ebx','ebp','esi','edi'))!=self.init_nonvol:self.init_deny('Actual initterm RET/nonvolatile/stack closure')
                self.init_event(5,value,self.r['esp'],value);return
            else:raise AssertionError('Unreviewed initterm source operation '+op)
            self.init_pc=nxt
        raise AssertionError('Null interval did not reach actual RET')
    def finish_init_job(self):
        self.init_job=[SLOT,0x1ded12,self.init_frame,self.init_ret,self.init_first,self.init_last,len(self.init_accesses),self.init_step,len(self.init_events),0,int(self.init_used),0,int(self.init_failed),int(self.init_complete),getattr(self,'init_fault_pc',0),getattr(self,'init_fault_address',0)]
        return self
    def run(self):
        super().run()
        if not self.control_status[7]:return self
        assert self.pc==0x5ac440
        self.runtime_cpu=struct.pack('<10I',*[self.r[k] for k in F.REGS],self.flags,THUNK)
        self.init_snapshot('initterm-thunk-before');self.project(THUNK,flat=True)
        self.init_frame=self.r['esp'];self.init_ret=self.raw_load(self.init_frame);self.init_first=self.raw_load(self.init_frame+4);self.init_last=self.raw_load(self.init_frame+8);self.init_used=True
        self.init_nonvol=tuple(self.r[x] for x in ('ebx','ebp','esi','edi'));self.init_pc=THUNK
        self.routes.append(dict(site=0x5ac440,target=THUNK,return_pc=0x5ac445,import_=False,completed=False))
        try:
            if self.control==47:raise D.Stop()
            if self.control in (37,38):self.init_deny('Exact initterm thunk/provider source identity')
            self.init_snapshot('initterm-thunk-projected');self.init_event(1,THUNK,self.init_frame,self.init_ret)
            raw=self.init_read(SLOT);self.init_pc=raw;self.init_commit()
            if self.control==39:self.init_deny('Actual initterm import tail/raw IAT/frame rejected')
            self.init_event(2,raw,self.init_frame,self.init_ret)
            self.runtime_cpu=struct.pack('<10I',*[self.r[k] for k in F.REGS],self.flags,SLOT)
            self.routes.append(dict(site=THUNK,target=SLOT,return_pc=0x5ac445,import_=True,completed=False))
            self.init_snapshot('initterm-before')
            try:
                if self.control==40:raise D.Stop()
                self.project(SLOT,flat=True);self.init_pc=PROVIDER;self.init_commit();self.init_snapshot('initterm-projected')
                if self.control==41:self.raw_store(BEGIN,0x51e7b0)
                if self.control==46:raise D.Stop()
                self.init_event(3,PROVIDER,self.init_frame,self.init_ret);self.null_provider()
                self.runtime_cpu=D.cpu(self.state);self.init_snapshot('initterm-after')
            except D.Stop:
                self.init_snapshot('initterm-after')
                self.init_deny('Required actual initterm provider route fault',SLOT)
            self.routes[-1]['completed']=True;self.init_event(6,0x5ac445,self.init_frame+4,self.init_ret)
            self.init_complete=True;self.routes[-2]['completed']=True
            self.runtime_cpu=D.cpu(self.state);self.init_snapshot('initterm-thunk-after')
        except D.Stop:
            self.init_snapshot('initterm-thunk-after');return self.finish_init_job()
        self.project(0x5ac445,flat=True);self.pc=0x5ac445
        for _ in range(14):
            size,op,args=self.program[self.pc];self.visited.append(self.pc);nxt=self.pc+size
            if op=='add':
                a,b=self.read(args[0]),self.read(args[1]);self.flags=M.add_flags(self.flags,a,b);self.write(args[0],a+b)
            elif op=='mov':self.write(args[0],self.read(args[1]))
            elif op=='lea':self.write(args[0],self.address('dword ptr '+args[1]))
            elif op=='push':self.push(self.read(args[0]))
            elif op=='call':
                target=self.read(args[0]);self.push(nxt);self.project(target)
                registers=[self.r[k] for k in F.REGS];registers[4]+=4
                self.runtime_cpu=struct.pack('<10I',*registers,self.flags,self.pc)
                return self.finish_init_job()
            else:raise AssertionError('Unreviewed entry continuation '+op)
            self.project(self.pc);self.pc=nxt
        raise AssertionError('Actual __getmainargs boundary was not reached')

def source_material(out):
    program,providers,maths,ctrl,pages,commands=M.source_material(out)
    game_path=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
    provider_path=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    game=N.PE.PEImage(game_path.read_bytes());provider=N.PE.PEImage(provider_path.read_bytes())
    tool=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe','a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
    continued,c1=D.E.decode(tool,game,game_path,0x5ac445,0x5ac46e,out,'entry-initterm-continuation');program.update(continued)
    thunk,c2=D.E.decode(tool,game,game_path,THUNK,THUNK+6,out,'initterm-thunk-source')
    init,c3=D.E.decode(tool,provider,provider_path,PROVIDER,PROVIDER+28,out,'initterm-provider-source')
    assert thunk=={THUNK:(6,'jmp',['dword ptr [0x5bb510]'])}
    assert continued[0x5ac468]==(6,'call',['dword ptr [0x5bb514]'])
    pages[THUNK]=bytearray(game.read(game.rva_range(THUNK-game.image_base,6)[0],6))
    pages[0x5e0000]=bytearray(D.mapped(game,0x5e0000))
    pages[0x78001000]=bytearray(D.mapped(provider,0x78001000))
    assert F.word(pages[0x5e0000],BEGIN&4095)==0
    assert sha(pin(game_path))=='95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'
    return program,providers,maths,ctrl,init,pages,commands+[c1,c2,c3]
