"""Independent literal source model of the first argument-initialization prefix."""
import copy,hashlib,importlib.util,json,ntpath,struct,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(path,digest=None):
    path=Path(path)
    if not path.is_absolute():path=path.resolve()
    actual=sha(path);assert digest is None or actual==digest,str(path)
    key=ntpath.normcase(ntpath.normpath(str(path)))
    assert key not in PINS or PINS[key]==actual,key
    PINS[key]=actual;return path
def module(name,path,digest):
    spec=importlib.util.spec_from_file_location(name,pin(path,digest));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
M=module('frozen_null_initializer_source',ROOT/'tools/m4-crt-entry-initterm-root/model.py','b19863e5ab04f8a348c626601ce3086adfbcd8357b399eefb47c5439565707e1')
D,F,R,N,C=M.D,M.F,M.R,M.N,M.C
SLOT=0x5bb514;RAW=0x1ded02;PROVIDER=0x7800ba5e;BUILDER=0x7800bbbc
NEW_MODE=0x78037150;API_SLOT=0x7802e018;API_PC=0x7800bbd0;API_RETURN=0x7800bbd6

class Entry(M.Entry):
    def __init__(self,program,providers,maths,ctrl,init,args,argv,state,memory,fx,control=0,level='O0'):
        super().__init__(program,providers,maths,ctrl,init,state,memory,fx,control,level)
        self.args_program=args;self.argv_program=argv;self.args_phases={};self.args_accesses=[];self.args_events=[];self.args_PCs=[]
        self.args_frame=0;self.args_ret=0;self.args_values=[0]*6;self.args_failed=False;self.args_used=False;self.args_reached=False;self.args_stage=0;self.args_reason='';self.args_fault_pc=0;self.args_fault_address=0
        self.args_job=[SLOT,RAW,*([0]*18)]
    def args_snapshot(self,tag):
        self.args_phases[tag]=(bytes(self.state),bytes(self.runtime_cpu),copy.deepcopy(self.mem),bytes(self.fx))
    def args_commit(self):self.project(self.args_pc)
    def args_event(self,kind,pc,address,value):self.args_events.append((kind,pc,address,value))
    def args_deny(self,why,address=0,pc=None):
        if not self.args_failed:
            self.args_failed=True;self.args_reason=why;self.args_fault_pc=self.args_pc if pc is None else pc;self.args_fault_address=address
        self.args_commit();raise D.Stop()
    def args_access(self,address,value,write):
        self.args_accesses.append((self.args_pc,address,value,4,write))
        if self.control==55 and self.args_pc==0x7800ba99 and len(self.args_accesses)==6:self.raw_store(self.args_frame-8,0x7800ba9e^1)
    def args_read(self,address):
        expected={0x7800ba61:self.r['ebp']+24,0x7800ba64:self.r['ebp']+20,0x7800ba68:self.r['eax'],API_PC:API_SLOT}
        if self.args_pc not in expected or address!=expected[self.args_pc]:self.args_deny('Mainargs source read operand outside admitted prefix',address)
        if self.args_pc!=API_PC and not 0x20001000<=address<=0x20001ffc:self.args_deny('Mainargs source read outside owned stack',address)
        value=self.raw_load(address)
        if self.args_pc==API_PC and value!=0x343b0:self.args_deny('Actual named GetModuleFileNameA raw IAT changed',address)
        self.args_access(address,value,0);return value
    def args_write(self,address,value):
        if self.args_pc==0x7800ba6a:
            if address!=NEW_MODE:self.args_deny('Mainargs newmode operand outside owned global',address)
        elif self.args_pc in (PROVIDER,0x7800ba99,0x7800ba71,BUILDER,0x7800bbbf,0x7800bbc0,0x7800bbc1,0x7800bbc2,0x7800bbc8,0x7800bbcd,0x7800bbce,API_PC):
            if address!=((self.r['esp']-4)&0xffffffff) or not 0x20001000<=address<=0x20001ffc:self.args_deny('Mainargs PUSH/CALL outside exact owned stack',address)
        else:self.args_deny('Mainargs write outside admitted source prefix',address)
        if (self.control==53 and self.args_pc==0x7800ba6a) or (self.control==54 and self.args_pc==PROVIDER) or (self.control==60 and self.args_pc==BUILDER):self.args_deny('Required checked mainargs write fault',address)
        self.raw_store(address,value);self.args_access(address,value,1)
        if self.args_pc==0x7800ba6a and value!=0:self.args_deny('Required nonzero startup mode outside admitted zero domain',address)
    def args_operand(self,operand):
        return self.args_read(self.address(operand)) if operand.startswith('dword ptr ') else self.read(operand)
    def args_store(self,operand,value):
        if operand.startswith('dword ptr '):self.args_write(self.address(operand),value)
        else:self.r[operand]=value&0xffffffff
    def args_execute(self,program):
        for _ in range(32):
            pc=self.args_pc;self.args_PCs.append(pc);self.args_commit()
            size,op,operands=program[pc];nxt=pc+size
            if op=='push':
                value=self.args_operand(operands[0]);address=(self.r['esp']-4)&0xffffffff
                self.args_write(address,value);self.r['esp']=address
            elif op=='mov':self.args_store(operands[0],self.args_operand(operands[1]))
            elif op=='cmp':C.X86.arithmetic(self,'cmp',self.args_operand(operands[0]),self.args_operand(operands[1]),4)
            elif op=='je':
                if self.flags&0x40:nxt=self.args_operand(operands[0])
            elif op=='call':
                target=self.args_operand(operands[0]);address=(self.r['esp']-4)&0xffffffff
                self.args_write(address,nxt);self.r['esp']=address;self.args_pc=target;self.args_commit()
                if pc==0x7800ba99:
                    assert target==BUILDER and nxt==0x7800ba9e
                    if self.raw_load(address)!=nxt:self.args_deny('Actual mainargs E8 internal return frame rejected',address,pc)
                    self.args_event(2,pc,BUILDER,nxt)
                    self.args_snapshot('mainargs-builder-before');self.args_stage=2
                    self.args_snapshot('mainargs-builder-projected')
                    if self.control==50:
                        self.raw_store(BUILDER,0);self.args_deny('Exact mainargs/provider source and game IAT identity')
                    if self.control==52:self.raw_store(API_SLOT,0x343b0^1)
                    if self.control==58:self.args_deny('Exact current mainargs read token',API_SLOT)
                    self.args_event(3,BUILDER,self.args_frame-8,nxt)
                    self.args_execute(self.argv_program)
                    raise AssertionError('Argument builder unexpectedly returned')
                elif pc==API_PC:
                    self.args_event(4,pc,API_SLOT,target)
                    self.args_reached=True
                    self.args_deny('Required KERNEL32.dll!GetModuleFileNameA remains unresolved',API_SLOT,API_PC)
                else:
                    assert pc==0x7800ba71 and target==0x7800b3b4 and nxt==0x7800ba76
                    self.args_event(7,pc,target,nxt)
                    self.args_deny('Required mainargs helper remains outside admitted prefix',target,pc)
            else:raise AssertionError('Reached unadmitted argument operation '+op)
            self.args_pc=nxt
        raise AssertionError('Argument source did not reach its named import stop')
    def finish_args_job(self):
        self.args_job=[SLOT,RAW,self.args_frame,self.args_ret,*self.args_values,len(self.args_accesses),len(self.args_events),0,int(self.args_used),0,int(self.args_failed),int(self.args_reached),self.args_stage,self.args_fault_pc,self.args_fault_address]
        return self
    def run(self):
        super().run()
        if not self.init_complete or self.pc!=0x5ac468:return self
        self.args_frame=self.r['esp'];self.args_ret=self.raw_load(self.args_frame)
        self.runtime_cpu=struct.pack('<10I',*[self.r[k] for k in F.REGS],self.flags,SLOT)
        self.routes.append(dict(site=0x5ac468,target=SLOT,return_pc=0x5ac46e,import_=True,completed=False))
        self.args_snapshot('mainargs-before');self.args_used=True
        self.args_values=[self.raw_load(self.args_frame+4*i) for i in range(1,6)]
        self.args_values.append(self.raw_load(self.args_values[-1]));self.args_stage=1
        self.project(SLOT,flat=True);self.args_pc=PROVIDER;self.args_commit();self.args_snapshot('mainargs-projected')
        try:
            if self.control in (49,51):
                self.raw_store(PROVIDER if self.control==49 else SLOT,0 if self.control==49 else RAW^1)
                self.args_deny('Exact mainargs/provider source and game IAT identity')
            if self.control==56:self.raw_store(self.args_values[4],0x13579bdf)
            if self.control==57:self.raw_store(self.args_frame+16,1)
            if self.control==59:self.args_deny('Required mainargs observer or host fault')
            self.args_event(1,PROVIDER,self.args_frame,self.args_ret)
            self.args_execute(self.args_program)
        except D.Stop:
            if self.args_stage==2:self.args_snapshot('mainargs-builder-after')
            self.args_snapshot('mainargs-after');return self.finish_args_job()
        raise AssertionError('Argument prefix unexpectedly completed')

def source_material(out):
    program,providers,maths,ctrl,init,pages,commands=M.source_material(out)
    provider_path=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
    provider=N.PE.PEImage(provider_path.read_bytes())
    tool=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe','a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
    args,c1=D.E.decode(tool,provider,provider_path,PROVIDER,PROVIDER+66,out,'mainargs-provider-source')
    argv,c2=D.E.decode(tool,provider,provider_path,BUILDER,BUILDER+140,out,'argv-provider-source')
    assert len(args)==21 and len(argv)==56
    assert args[0x7800ba99]==(5,'call',['0x7800bbbc'])
    assert argv[API_PC]==(6,'call',['dword ptr [0x7802e018]'])
    return program,providers,maths,ctrl,init,args,argv,pages,commands+[c1,c2]
