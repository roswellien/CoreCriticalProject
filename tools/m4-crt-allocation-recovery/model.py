"""Independent affine source prediction; finite typed API outcomes are inputs.

This module never imports candidate expected-state code, runs native workers,
or obtains API results. Its memory argument is independently constructed BEFORE
owned storage, including the carried FS chain. External call-frame setup must
be recorded separately by the caller; it is not an original source CALL.
"""
import copy
import struct

REG={'eax':2216,'ecx':2248,'edx':2264,'ebx':2232,'esp':2312,'ebp':2328,'esi':2280,'edi':2296}
FLAGS={'CF':2065,'PF':2067,'AF':2069,'ZF':2071,'SF':2073,'DF':2075,'OF':2077}
FSBASE=2168


def need(value, why):
    if not value: raise ValueError(why)


class Affine:
    def __init__(self,state,fx,cpu,memory):
        need(len(state)==3504 and len(fx)==512 and len(cpu)==40,'Complete independent BEFORE machine')
        self.state=bytearray(state);self.fx=bytes(fx);self.cpu=bytes(cpu)
        self.memory=copy.deepcopy(memory);self.PCs=[];self.accesses=[];self.API_reads=[];self.routes=[];self.returns=[];self.phases={}
        self.undefined=[]
        need(self.word(2120)==self.word(2184)==0,'Declared flat carried SS/DS')
        self.fs=self.word(FSBASE)

    def word(self,offset): return struct.unpack_from('<I',self.state,offset)[0]
    def reg(self,name,value=None):
        if value is None:return self.word(REG[name])
        struct.pack_into('<I',self.state,REG[name],value&0xffffffff)
    def pc(self,address):
        struct.pack_into('<I',self.state,2472,address);self.PCs.append(address)
    def target(self,address):struct.pack_into('<I',self.state,2472,address)
    def location(self,address):
        owners=[(base,raw) for base,raw in self.memory.items() if isinstance(base,int) and
                base<=address and address+4<=base+len(raw)]
        need(len(owners)==1,'One independently owned DWORD extent '+hex(address))
        return owners[0][0],address-owners[0][0]
    def read(self,pc,address,wanted=None,API=False):
        base,off=self.location(address);value=struct.unpack_from('<I',self.memory[base],off)[0]
        need(wanted is None or value==wanted,'Exact source operand '+hex(pc))
        (self.API_reads if API else self.accesses).append((pc,address,value,4,0));return value
    def write(self,pc,address,value):
        base,off=self.location(address)
        if not isinstance(self.memory[base],bytearray):self.memory[base]=bytearray(self.memory[base])
        struct.pack_into('<I',self.memory[base],off,value&0xffffffff)
        self.accesses.append((pc,address,value&0xffffffff,4,1))
    def push(self,pc,value):
        address=self.reg('esp')-4;self.write(pc,address,value);self.reg('esp',address)
    def pop(self,pc,name):
        old=self.reg('esp');self.reg('esp',old+4) # Existing generated POP publishes ESP before checked read.
        self.reg(name,self.read(pc,old))
    def ret(self,pc,wanted):
        frame=self.reg('esp');target=self.read(pc,frame,wanted)
        self.target(target);self.reg('esp',frame+4);self.returns.append((pc,target,frame))
    def arithmetic(self,a,b,sub=True,width=32):
        mask=(1<<width)-1;a&=mask;b&=mask;result=(a-b if sub else a+b)&mask
        signed=lambda v:v if v<(1<<(width-1)) else v-(1<<width)
        full=signed(a)-signed(b) if sub else signed(a)+signed(b)
        values=dict(CF=int(a<b) if sub else int(a+b>mask),PF=int((result&255).bit_count()%2==0),
            AF=int((a&15)<(b&15)) if sub else int((a&15)+(b&15)>15),ZF=int(result==0),
            SF=result>>(width-1),OF=int(not -(1<<(width-1))<=full<(1<<(width-1))))
        for k,v in values.items():self.state[FLAGS[k]]=v
        return result
    def logic(self,pc,value,width=32):
        value&=(1<<width)-1
        for k,v in dict(CF=0,PF=int((value&255).bit_count()%2==0),AF=0,ZF=int(value==0),SF=value>>(width-1),OF=0).items():
            self.state[FLAGS[k]]=v
        self.undefined.append((pc,0))
    def snapshot(self,tag):
        self.phases[tag]=dict(state=bytes(self.state),fx=self.fx,cpu=self.cpu,memory=copy.deepcopy(self.memory),
                              source_accesses=len(self.accesses),API_reads=len(self.API_reads))
    def result(self):
        return dict(state=bytes(self.state),fx=self.fx,cpu=self.cpu,memory=self.memory,PCs=self.PCs,
                    accesses=self.accesses,API_return_reads=self.API_reads,routes=self.routes,returns=self.returns,
                    undefined=self.undefined,phases=self.phases)


def caller_cleanup(state,fx,cpu,memory):
    x=Affine(state,fx,cpu,memory)
    need(x.word(2472)==0x78001843 and x.reg('esp')==0x2000185c and x.reg('eax')==1,
         'Source initializer return, not a fabricated attach outcome')
    x.pc(0x78001843);x.logic(0x78001843,x.reg('eax'))
    x.pc(0x78001845);x.pop(0x78001845,'ecx');need(x.reg('ecx')==1,'Original initializer cdecl argument')
    x.pc(0x78001846);x.target(0x7800184c)
    need(x.reg('esp')==0x20001860,'Caller source argument cleanup')
    x.snapshot('caller-cleanup-after');return x.result()


def malloc_mode1(state,fx,cpu,memory,size,guest_result,return_word=0xffffffe0):
    x=Affine(state,fx,cpu,memory);M=x.reg('esp')
    need(x.word(2472)==0x780012b3 and M>=80 and 0<=size<=0xffffffe0 and
         isinstance(guest_result,int) and 0<=guest_result<=0xffffffff,'Explicit admitted external malloc ABI')
    need(x.read(0x780012b3,M,return_word,API=True)==return_word,'Declared external malloc return word')
    # Admission-frame validation is separate from actual API-return evidence.
    x.API_reads.clear()
    entry={k:x.reg(k) for k in ('ebp','ebx','esi','edi')};previous=struct.unpack_from('<I',x.memory[x.location(x.fs)[0]],x.location(x.fs)[1])[0]
    x.snapshot('malloc-before')
    x.pc(0x780012b3);newmode=x.read(0x780012b3,0x78037150,0);x.push(0x780012b3,newmode)
    x.pc(0x780012b9);n=x.read(0x780012b9,M+4,size);x.push(0x780012b9,n)
    x.pc(0x780012bd);x.push(0x780012bd,0x780012c2);x.routes.append((0x780012bd,0x780012c5,0x780012c2))
    x.pc(0x780012c5);n=x.read(0x780012c5,M-8,size);x.arithmetic(n,0xffffffe0)
    x.pc(0x780012ca)
    x.pc(0x780012d0);x.push(0x780012d0,x.read(0x780012d0,M-8,size))
    x.pc(0x780012d4);x.push(0x780012d4,0x780012d9);x.routes.append((0x780012d4,0x780012e3,0x780012d9))
    x.pc(0x780012e3);x.push(0x780012e3,entry['ebp'])
    x.pc(0x780012e4);x.reg('ebp',x.reg('esp'))
    for pc,value in ((0x780012e6,0xffffffff),(0x780012e8,0x7802e248),(0x780012ed,0x7800ef03)):
        x.pc(pc);x.push(pc,value)
    x.pc(0x780012f2);x.reg('eax',x.read(0x780012f2,x.fs,previous))
    x.pc(0x780012f8);x.push(0x780012f8,x.reg('eax'))
    x.pc(0x780012f9);x.write(0x780012f9,x.fs,x.reg('esp'));x.snapshot('malloc-SEH-installed')
    x.pc(0x78001300);x.reg('esp',x.arithmetic(x.reg('esp'),12))
    for pc,name in ((0x78001303,'ebx'),(0x78001304,'esi'),(0x78001305,'edi')):x.pc(pc);x.push(pc,entry[name])
    x.pc(0x78001306);x.reg('eax',x.read(0x78001306,0x78035004,1))
    x.pc(0x7800130b);x.arithmetic(x.reg('eax'),3);x.pc(0x7800130e)
    x.pc(0x78001314);x.arithmetic(x.reg('eax'),2);x.pc(0x78001317)
    x.pc(0x7800cc97);x.reg('eax',x.read(0x7800cc97,M-16,size))
    x.pc(0x7800cc9a);x.logic(0x7800cc9a,x.reg('eax'));x.pc(0x7800cc9c)
    if size==0:
        x.pc(0x7800cc9e);x.push(0x7800cc9e,1);x.pc(0x7800cca0);x.pop(0x7800cca0,'eax')
    x.pc(0x7800cca1);x.reg('eax',x.arithmetic(x.reg('eax'),15,sub=False))
    x.pc(0x7800cca4);low=(x.reg('eax')&255)&0xf0;x.logic(0x7800cca4,low,8);x.reg('eax',(x.reg('eax')&0xffffff00)|low)
    rounded=x.reg('eax');need(rounded==((max(size,1)+15)&0xfffffff0),'Exact source nonzero rounded extent')
    x.pc(0x7800cca6);x.push(0x7800cca6,rounded);x.pc(0x7800cca7)
    x.pc(0x78001377);x.push(0x78001377,0)
    x.pc(0x78001379);token=x.read(0x78001379,0x78035000,0x48450001);x.push(0x78001379,token)
    x.pc(0x7800137f);raw=x.read(0x7800137f,0x7802e094,0x345c6);x.push(0x7800137f,0x78001385)
    x.routes.append((0x7800137f,raw,0x78001385));x.target(raw);x.snapshot('malloc-HeapAlloc-before')
    # Only independently validated finite API output; no API internals, volatile or flag equivalence claim.
    api_frame=M-80;x.read(0x7800137f,api_frame,0x78001385,API=True)
    x.reg('eax',guest_result);x.reg('esp',M-64);x.target(0x78001385);x.snapshot('malloc-HeapAlloc-returned')
    x.pc(0x78001385)
    x.pc(0x78001367);x.reg('ecx',x.read(0x78001367,M-40,previous))
    x.pc(0x7800136a);x.write(0x7800136a,x.fs,x.reg('ecx'));x.snapshot('malloc-SEH-restored')
    for pc,name in ((0x78001371,'edi'),(0x78001372,'esi'),(0x78001373,'ebx')):x.pc(pc);x.pop(pc,name)
    x.pc(0x78001374);x.reg('esp',x.reg('ebp'));x.pop(0x78001374,'ebp')
    x.pc(0x78001375);x.ret(0x78001375,0x780012d9)
    x.pc(0x780012d9);x.logic(0x780012d9,x.reg('eax'))
    x.pc(0x780012db);x.pop(0x780012db,'ecx');x.pc(0x780012dc)
    if guest_result==0:
        x.pc(0x7800cc3f);x.arithmetic(x.read(0x7800cc3f,M-4,0),x.reg('eax'));x.pc(0x7800cc43)
    x.pc(0x780012e2);x.ret(0x780012e2,0x780012c2)
    x.pc(0x780012c2);x.pop(0x780012c2,'ecx');x.pc(0x780012c3);x.pop(0x780012c3,'ecx')
    x.pc(0x780012c4);x.ret(0x780012c4,return_word);x.snapshot('malloc-returned')
    need(all(x.reg(k)==v for k,v in entry.items()) and x.reg('esp')==M+4 and x.reg('eax')==guest_result,
         'Normal source malloc cdecl return and preserved nonvolatiles')
    result=x.result();result.update(size=size,rounded_bytes=rounded,entry_frame=M,api_frame=api_frame,
        SEH_frame=M-40,previous_SEH=previous,guest_result=guest_result,actual_API_executed=False,
        declared_API_result_only=True,original_SEH_dispatch_proved=False)
    return result


def free_mode1(state,fx,cpu,memory,guest_pointer,BOOL,return_word=0xffffffd0):
    x=Affine(state,fx,cpu,memory);F=x.reg('esp')
    need(x.word(2472)==0x78001390 and 0<guest_pointer<=0xffffffff and 0<=BOOL<=0xffffffff,
         'Explicit finite external free ABI; nullable free is separate')
    need(x.read(0x78001390,F,return_word,API=True)==return_word,'Declared external free return word');x.API_reads.clear()
    entry={k:x.reg(k) for k in ('ebp','ebx','esi','edi')};previous=struct.unpack_from('<I',x.memory[x.location(x.fs)[0]],x.location(x.fs)[1])[0]
    x.snapshot('free-before');x.pc(0x78001390);x.push(0x78001390,entry['ebp'])
    x.pc(0x78001391);x.reg('ebp',x.reg('esp'))
    for pc,value in ((0x78001393,0xffffffff),(0x78001395,0x7802e260),(0x7800139a,0x7800ef03)):
        x.pc(pc);x.push(pc,value)
    x.pc(0x7800139f);x.reg('eax',x.read(0x7800139f,x.fs,previous))
    x.pc(0x780013a5);x.push(0x780013a5,x.reg('eax'))
    x.pc(0x780013a6);x.write(0x780013a6,x.fs,x.reg('esp'));x.snapshot('free-SEH-installed')
    x.pc(0x780013ad);x.reg('esp',x.arithmetic(x.reg('esp'),24))
    for pc,name in ((0x780013b0,'ebx'),(0x780013b1,'esi'),(0x780013b2,'edi')):x.pc(pc);x.push(pc,entry[name])
    x.pc(0x780013b3);x.reg('esi',x.read(0x780013b3,F+4,guest_pointer))
    x.pc(0x780013b6);x.logic(0x780013b6,x.reg('esi'));x.pc(0x780013b8)
    x.pc(0x780013ba);x.reg('eax',x.read(0x780013ba,0x78035004,1))
    x.pc(0x780013bf);x.arithmetic(x.reg('eax'),3);x.pc(0x780013c2)
    x.pc(0x780013c8);x.arithmetic(x.reg('eax'),2);x.pc(0x780013cb)
    x.pc(0x7800cc39);x.push(0x7800cc39,x.reg('esi'));x.pc(0x7800cc3a)
    x.pc(0x78001428);x.push(0x78001428,0)
    x.pc(0x7800142a);token=x.read(0x7800142a,0x78035000,0x48450001);x.push(0x7800142a,token)
    x.pc(0x78001430);raw=x.read(0x78001430,0x7802e090,0x345ba);x.push(0x78001430,0x78001436)
    x.routes.append((0x78001430,raw,0x78001436));x.target(raw);x.snapshot('free-HeapFree-before')
    api_frame=F-72;x.read(0x78001430,api_frame,0x78001436,API=True)
    x.reg('eax',BOOL);x.reg('esp',F-56);x.target(0x78001436);x.snapshot('free-HeapFree-returned')
    x.pc(0x78001436);x.pc(0x78001416);x.reg('ecx',x.read(0x78001416,F-20,previous))
    x.pc(0x78001419);x.write(0x78001419,x.fs,x.reg('ecx'));x.snapshot('free-SEH-restored')
    for pc,name in ((0x78001420,'edi'),(0x78001421,'esi'),(0x78001422,'ebx')):x.pc(pc);x.pop(pc,name)
    x.pc(0x78001423);x.reg('esp',x.reg('ebp'));x.pop(0x78001423,'ebp')
    x.pc(0x78001424);x.ret(0x78001424,return_word);x.snapshot('free-returned')
    need(all(x.reg(k)==v for k,v in entry.items()) and x.reg('esp')==F+4,'Authentic free cdecl return')
    result=x.result();result.update(entry_frame=F,api_frame=api_frame,SEH_frame=F-20,previous_SEH=previous,
        guest_pointer=guest_pointer,raw_BOOL=BOOL,release_success=BOOL!=0,public_CRT_return_type='void',
        actual_API_executed=False,declared_API_result_only=True,original_SEH_dispatch_proved=False)
    return result
