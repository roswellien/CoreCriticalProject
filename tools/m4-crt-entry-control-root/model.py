"""Independent actual source model extending the frozen matherr entry gate."""
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
def module(name,path,h):
    spec=importlib.util.spec_from_file_location(name,pin(path,h));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
M=module('frozen_matherr_source',ROOT/'tools/m4-crt-entry-matherr-root/model.py','5bd21ddfc1ffef390a88891f60821ff055c32d73610fba7740d1f94688e0da32')
C=module('frozen_control_source',ROOT/'tools/m4-crt-control-independent/review.py','49eea1a0c6615d685acad629c4ef10bab32c6f14aa960a0c1e1d01c6750f6e61')
D,F,R,N=M.D,M.F,M.R,M.N
WRAPPER=0x5ac5a0;THUNK=0x5ac5d6;SLOT=0x5bb578;PROVIDER=0x780042e1

def cpu(state):return D.cpu(state)
def project(state,registers,flags,pc,flat=False):
    for o,r in zip(F.OFF,F.REGS):F.put(state,o,registers[r])
    for o,b in F.FLAGS:state[o]=(flags>>b)&1
    F.put(state,2472,pc)
    if flat:F.put(state,2080,flags,8)

class Provider(C.X86):
    """Same scalar source operations, carried State and exact memory accesses."""
    def __init__(self,program,state,memory,fx,control=0):
        self.state=bytearray(state);self.fx=bytearray(fx);self.source_events=[];self.pcs=[]
        self.control=control;self.denial=None
        before=struct.unpack('<10I',cpu(state));cw=F.word(state,2768,2)
        super().__init__(program,before,memory,cw)
    def commit(self,pc=None):project(self.state,self.r,self.flags,self.pc if pc is None else pc)
    def load(self,a,width):
        assert 0x20001000<=a<=0x20002000-width
        value=int.from_bytes(self.memory[a-0x20001000:a-0x20001000+width],'little')
        self.source_events.append((self.pc,a,value,width,0));return value
    def store(self,a,value,width):
        assert 0x20001000<=a<=0x20002000-width
        if self.control==33:self.deny('Required checked32-bit write fault',a)
        value&=(1<<(width*8))-1
        C.put(self.memory,a-0x20001000,value,width)
        self.source_events.append((self.pc,a,value,width,1))
    def read(self,operand):
        if operand.startswith(('byte ptr ','word ptr ','dword ptr ')):
            return self.load(self.address(operand)+0x20001000,self.width(operand))
        return super().read(operand)
    def write(self,operand,value):
        if operand.startswith(('byte ptr ','word ptr ','dword ptr ')):
            self.store(self.address(operand)+0x20001000,value,self.width(operand))
        else:super().write(operand,value)
    def push(self,value):
        # The preserved lifted PUSH calls the checked store before publishing
        # ESP. A denied store retains the preceding State ESP.
        address=(self.r['esp']-4)&0xffffffff
        self.store(address,value,4);self.r['esp']=address;self.commit()
    def pop(self):
        value=self.load(self.r['esp'],4);self.r['esp']+=4;return value
    def deny(self,reason,address=0,cw_fault=0,cw_address=0):
        self.commit();self.denial=(reason,self.pc,address,cw_fault,cw_address)
        raise D.Stop()
    def run(self):
        for _ in range(512):
            if self.pc==0x5ac5af:
                assert not self.frames
                self.commit();return self
            size,op,args=self.program[self.pc];self.pcs.append(self.pc);self.commit();nxt=self.pc+size
            if op in ('mov','movzx'):self.write(args[0],self.read(args[1]))
            elif op in ('xor','and','or','test','cmp'):
                value=self.arithmetic(op,self.read(args[0]),self.read(args[1]),self.width(args[0]))
                if op not in ('test','cmp'):self.write(args[0],value)
            elif op=='not':self.write(args[0],~self.read(args[0]))
            elif op=='push':self.push(self.read(args[0]))
            elif op=='pop':self.write(args[0],self.pop())
            elif op=='call':
                self.push(nxt);nxt=self.read(args[0]);assert nxt in C.ENTRIES
                self.pc=nxt;self.commit();self.enter()
            elif op=='ret':
                frame=self.frames.pop();nxt=self.pop()
                assert self.r['esp']==frame[1]+4 and nxt==frame[2] and self.nonvol()==frame[3]
                self.events.append((2,nxt,self.r['esp'],nxt))
            elif op=='leave':
                self.r['esp']=self.r['ebp'];self.commit();self.r['ebp']=self.pop()
            elif op=='fnstcw':
                if self.control==30:
                    a=self.address(args[0])+0x20001000
                    self.deny('Required connected typed FNSTCW fault',a,2,a)
                self.write(args[0],self.cw)
            elif op=='fldcw':
                self.cw=(self.read(args[0])&0x1f3f)|0x40
                F.put(self.state,2768,self.cw,2);F.put(self.fx,0,self.cw,2)
            elif op=='wait':
                if self.control in (31,32):self.deny('Unsupported connected FWAIT pending/nonempty state')
            elif op in ('je','jne'):
                if bool(self.flags&0x40)==(op=='je'):nxt=self.read(args[0])
            elif op=='jmp':nxt=self.read(args[0])
            else:raise AssertionError('Unreviewed provider source operation '+op)
            self.pc=nxt
        raise AssertionError('Bounded source control did not return')

class Entry(M.Entry):
    def __init__(self,program,providers,math_program,control_program,state,memory,fx,control=0):
        super().__init__(program,providers,math_program,state,memory,control)
        self.control_program=control_program;self.fx=bytearray(fx)
        self.control_before=None;self.control_projected=None;self.provider_before=None;self.provider_projected=None;self.provider_after=None;self.control_after=None
        self.control_events=[];self.control_source=[];self.control_pcs=[]
        self.control_status=[0x1ded8a,0,0,0,0,0,0,0,0,0,0,0];self.control_reason=''
        mutation={25:(WRAPPER,0),26:(THUNK,0),27:(0x5bb000,0x578),28:(0x78004000,0x2e1),29:(0x78011000,0x29b)}.get(control)
        if mutation:
            a,o=mutation;F.put(self.mem[a],o,0x1ded8a^1 if control==27 else 0)
        self.projected=(bytes(self.state),bytes(self.runtime_cpu),copy.deepcopy(self.mem))
    def read(self,operand):
        if self.control in (28,29) and operand=='dword ptr [0x5bb508]':
            D.E.Model.read(self,operand);self.project(self.pc);raise D.Stop()
        return super().read(operand)
    def control_snapshot(self):return bytes(self.state),bytes(self.runtime_cpu),copy.deepcopy(self.mem),bytes(self.fx)
    def denied(self,pc,reason,depth,address=0,cw_fault=0,cw_address=0):
        self.control_status=[0x1ded8a,len(self.control_events),len(self.control_source),depth,0,0,1,0,pc,address,cw_fault,cw_address]
        self.control_reason=reason;self.control_after=self.control_snapshot();return self
    def run(self):
        try:super().run()
        except D.Stop:return self
        if not self.math_status[9]:return self
        assert self.pc==0x5ac431 and self.r['esp']==D.FRAME-140
        if self.control==30:F.put(self.state,2768,F.word(self.state,2768,2)^0x100,2)
        if self.control==31:F.put(self.state,2770,1,2);self.fx[2]=1
        if self.control==32:self.state[2772]=1;self.fx[4]=1
        # Successful r9 admission reuses the compiled CALL's existing word.
        self.runtime_cpu=struct.pack('<10I',*[self.r[k] for k in F.REGS],self.flags,WRAPPER)
        self.control_before=self.control_snapshot()
        self.project(WRAPPER,flat=True);self.control_projected=self.control_snapshot()
        self.routes.append(dict(site=0x5ac431,target=WRAPPER,return_pc=0x5ac436,import_=False,completed=False))
        if self.control==36:
            self.control_after=self.control_snapshot();return self
        self.control_events.append((1,WRAPPER,self.r['esp'],0x5ac436))
        for pc,argument in ((0x5ac5a0,0x30000),(0x5ac5a5,0x10000)):
            self.pc=pc;self.project(pc);self.r['esp']-=4;self.project(pc)
            self.raw_store(self.r['esp'],argument);self.control_source.append((pc,self.r['esp'],argument,4,1))
            if self.control==34 and pc==0x5ac5a5:self.raw_store(self.r['esp'],argument^1)
        self.pc=0x5ac5aa;self.project(self.pc);self.r['esp']-=4;self.project(self.pc)
        self.raw_store(self.r['esp'],0x5ac5af);self.control_source.append((self.pc,self.r['esp'],0x5ac5af,4,1))
        self.project(THUNK)
        if self.control==34:return self.denied(THUNK,'Actual wrapper CALL/arguments/thunk frame rejected',1)
        self.control_events.append((3,THUNK,self.r['esp'],0x5ac5af))
        raw=self.raw_load(SLOT);assert raw==0x1ded8a or self.control==27
        self.control_source.append((THUNK,SLOT,raw,4,0));self.project(raw)
        if self.control==27:return self.denied(raw,'Actual import tail/raw-IAT/return-frame identity rejected',1)
        if self.control in (25,26):return self.denied(raw,'Exact game wrapper/thunk/outer CALL source changed',1)
        self.control_events.append((4,raw,self.r['esp'],0x5ac5af))
        self.routes.append(dict(site=0x5ac5aa,target=SLOT,return_pc=0x5ac5af,import_=True,completed=False))
        self.runtime_cpu=struct.pack('<10I',*[self.r[k] for k in F.REGS],self.flags,SLOT)
        self.provider_before=self.control_snapshot()
        self.project(PROVIDER)
        self.provider_projected=self.control_snapshot()
        p=Provider(self.control_program,self.state,self.mem[0x20001000],self.fx,self.control)
        try:p.run()
        except D.Stop:pass
        self.state=bytearray(p.state);self.fx=bytearray(p.fx);self.mem[0x20001000]=bytearray(p.memory)
        self.r=dict(p.r);self.flags=p.flags;self.control_events.extend(p.events);self.control_source.extend(p.source_events);self.control_pcs=p.pcs
        if p.denial:
            self.provider_after=self.control_snapshot()
            reason,pc,address,cwf,cwa=p.denial
            return self.denied(pc,reason,1+len(p.frames),address,cwf,cwa)
        self.runtime_cpu=cpu(self.state);self.provider_after=self.control_snapshot()
        self.routes[-1]['completed']=True
        self.control_events.append((5,0x5ac5af,self.r['esp'],0x5ac5af))
        if self.control==35:self.raw_store(D.FRAME-140,0x5ac436^1)
        self.pc=0x5ac5af
        self.flags=add_flags(self.flags,self.r['esp'],8)
        self.r['esp']+=8;self.project(self.pc)
        self.pc=0x5ac5b2;self.project(self.pc)
        ret=self.raw_load(self.r['esp']);self.control_source.append((self.pc,self.r['esp'],ret,4,0));self.r['esp']+=4
        self.project(ret)
        if self.control==35:return self.denied(ret,'Actual connected RET/nonvolatile/cleanup rejected',1)
        assert ret==0x5ac436;self.runtime_cpu=cpu(self.state)
        self.control_events.append((2,ret,self.r['esp'],ret));self.routes[-2]['completed']=True
        self.control_after=self.control_snapshot()
        self.control_status=[0x1ded8a,len(self.control_events),len(self.control_source),0,0,0,0,1,0,0,0,0]
        # The outer entry projects the returned CPU, retaining all FP fields.
        self.project(ret,flat=True)
        for pc,argument in ((0x5ac436,0x5e024c),(0x5ac43b,0x5e0248)):
            self.pc=pc;self.visited.append(pc);self.push(argument);self.project(pc)
        self.pc=0x5ac440;self.visited.append(self.pc);self.push(0x5ac445);self.project(0x5ac598)
        registers=[self.r[k] for k in F.REGS];registers[4]+=4
        self.runtime_cpu=struct.pack('<10I',*registers,self.flags,self.pc)
        return self

def add_flags(flags,a,b):
    total=a+b;v=total&0xffffffff
    bits=int(total>0xffffffff)|(int((v&255).bit_count()%2==0)<<2)|(int(bool((a^b^v)&16))<<4)|(int(v==0)<<6)|(int(bool(v&0x80000000))<<7)|(int(bool((~(a^b)&(a^v))&0x80000000))<<11)
    return (flags&~0x8d5)|bits

def source_material(out):
    program,providers,math_program,pages,commands=M.source_material(out)
    game_path=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
    game=N.PE.PEImage(game_path.read_bytes())
    tool=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe','a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
    continued,c1=D.E.decode(tool,game,game_path,0x5ac436,0x5ac445,out,'entry-control-continuation');program.update(continued)
    wrapper,c2=D.E.decode(tool,game,game_path,WRAPPER,WRAPPER+19,out,'control-wrapper-source')
    thunk,c3=D.E.decode(tool,game,game_path,THUNK,THUNK+6,out,'control-thunk-source')
    assert wrapper=={0x5ac5a0:(5,'push',['0x30000']),0x5ac5a5:(5,'push',['0x10000']),0x5ac5aa:(5,'call',['0x5ac5d6']),0x5ac5af:(3,'add',['esp','0x8']),0x5ac5b2:(1,'ret',[])}
    assert thunk=={THUNK:(6,'jmp',['dword ptr [0x5bb578]'])}
    assert continued=={0x5ac436:(5,'push',['0x5e024c']),0x5ac43b:(5,'push',['0x5e0248']),0x5ac440:(5,'call',['0x5ac598'])}
    control_program,c4=C.decode(out)
    pages[WRAPPER]=bytearray(game.read(game.rva_range(WRAPPER-game.image_base,19)[0],19))
    pages[THUNK]=bytearray(game.read(game.rva_range(THUNK-game.image_base,6)[0],6))
    return program,providers,math_program,control_program,pages,commands+[c1,c2,c3]+c4
