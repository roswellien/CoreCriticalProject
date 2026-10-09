"""Author validation from exact source instructions and raw native observations.

No root/independent oracles or primary comparators are imported. Windows query
results are inputs from actual provenance records, not invented expected BOOLs.
"""
import argparse, hashlib, json, pathlib, re, struct

ROOT=pathlib.Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-fdiv'
STRIDE=107740
PAGES=(0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000)
GPR=dict(zip(('eax','ecx','edx','ebx','esp','ebp','esi','edi','eip'),(2216,2248,2264,2232,2312,2328,2280,2296,2472)))
AF=((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11))
CW=(0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f)
ENTRIES=(0x78004254,0x7800426b,0x780042a3,0x780042cf,0x780042e1,0x780042f7,0x7800432c,0x7800439f)

def need(ok,why):
    if not ok:raise ValueError(why)
def u(b,o,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def h(b,o):return struct.unpack_from('<H',b,o)[0]
def q(b,o):return struct.unpack_from('<Q',b,o)[0]
def put(b,o,v,width=4):b[o:o+width]=int(v).to_bytes(width,'little')
def sha(p):
    with open(p,'rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))

class PE:
    def __init__(self,path):
        self.path=pathlib.Path(path);self.b=self.path.read_bytes();p=u(self.b,0x3c)[0]
        need(self.b[:2]==b'MZ'and self.b[p:p+4]==b'PE\0\0','PE identity');self.machine=h(self.b,p+4);o=p+24;self.magic=h(self.b,o)
        need(self.magic in(0x10b,0x20b),'PE optional header');self.base=u(self.b,o+28)[0]if self.magic==0x10b else q(self.b,o+24);self.directory=o+(96 if self.magic==0x10b else 112);self.sections=[]
        for i in range(h(self.b,p+6)):
            s=o+h(self.b,p+20)+40*i;vs,r,raw,off=u(self.b,s+8,4);need(off+raw<=len(self.b),'PE raw section bounds');self.sections.append((r,vs,raw,off,u(self.b,s+36)[0]))
    def offset(self,rva,n):
        for r,vs,raw,off,flags in self.sections:
            if r<=rva and rva+n<=r+min(vs,raw):return off+rva-r
        raise ValueError('Complete file-backed source range required')
    def bytes(self,va,n):o=self.offset(va-self.base,n);return self.b[o:o+n]
    def string(self,rva):
        x=bytearray()
        for i in range(4096):
            c=self.b[self.offset(rva+i,1)]
            if not c:return x.decode('ascii')
            x.append(c)
        raise ValueError('Bounded PE string')
    def exports(self):
        d=u(self.b,self.directory)[0];o=self.offset(d,40);count,names,funcs,strings,ords=u(self.b,o+20,5);need(count<=65536 and names<=count,'Bounded PE exports');result={}
        for i in range(names):
            name=self.string(u(self.b,self.offset(strings+4*i,4))[0]);index=h(self.b,self.offset(ords+2*i,2));need(index<count and name not in result,'Unique named exports');result[name]=u(self.b,self.offset(funcs+4*index,4))[0]
        return result,d,u(self.b,self.directory+4)[0]

def path_field(b):
    words=struct.unpack('<1024H',b);n=words.index(0);need(not any(words[n:]),'Terminated owned module path');return pathlib.Path(b[:2*n].decode('utf-16le'))

def module(b,bindings):
    handle=q(b,0);region=struct.unpack_from('<3Q4I',b,8);path=path_field(b[112:2160]);pe=PE(path)
    need(handle==region[0]==region[2]and region[3:5]==(0x1000,0x1000000),'Returned module actual mapped image/base ownership')
    need(pe.machine==0x8664 and sha(path)==b[48:112].decode('ascii'),'Actual returned module current file/machine identity');bindings[str(path)]=sha(path);return handle,pe

def api(b,name,module_pe,bindings):
    target,named,owner,owner_named=struct.unpack_from('<4Q',b);region=struct.unpack_from('<3Q4I',b,32);path=path_field(b[136:2184]);pe=PE(path)
    need(target==named==owner_named and region[0]<=target<region[0]+region[1]and owner==region[2],'Actual named API target/range/owner')
    need(region[3:5]==(0x1000,0x1000000)and region[5]&0xf0 and not region[5]&0x101,'Actual executable loaded image region')
    need(pe.machine==0x8664 and sha(path)==b[72:136].decode('ascii'),'Actual loaded API owner current disk association');exports,d,n=pe.exports();need(name in exports and not d<=exports[name]<d+n,'Owner exact non-forwarded named export');need(target==owner+exports[name],'Owner named export runtime address')
    # The named KERNEL32 provider may forward to KernelBase. Preserve both owners.
    named_exports,nd,nn=module_pe.exports();need(name in named_exports,'Issued module contains exact named API');r=named_exports[name]
    if nd<=r<nd+nn:need(module_pe.string(r).rsplit('.',1)[-1]==name,'Exact named forwarded API export')
    bindings[str(path)]=sha(path);return target

class Model:
    def __init__(self,state,pages,fx,instructions,feature):
        self.state=bytearray(state);self.pages=bytearray(pages);self.fx=bytearray(fx);self.reg={k:u(state,o)[0]for k,o in GPR.items()};self.flags={bit:state[o]for o,bit in AF};self.ins=instructions;self.events=[];self.routes=[];self.feature=feature;self.executed=[]
    def event(self,kind,pc,address,value,width):self.events.append((kind,pc,address,value,width))
    def pos(self,address,n):
        for i,p in enumerate(PAGES):
            if p<=address and address+n<=p+4096:return i*4096+address-p
        raise ValueError('Model checked owned page bounds')
    def load(self,address,n,pc,event=True):
        value=int.from_bytes(self.pages[self.pos(address,n):self.pos(address,n)+n],'little')
        if event:self.event(0,pc,address,value,n)
        return value
    def store(self,address,value,n,pc):put(self.pages,self.pos(address,n),value&((1<<(8*n))-1),n);self.event(1,pc,address,value&((1<<(8*n))-1),n)
    def alias(self,name):
        if name in self.reg:return name,0,32
        if name in('ax','bx','cx','dx','si','di','sp','bp'):return 'e'+name,0,16
        need(name in('al','ah','bl','bh','cl','ch','dl','dh'),'Exact supported source register');return 'e'+name[0]+'x',8 if name[1]=='h'else 0,8
    def operand(self,op):
        op=op.split(' <')[0].strip()
        if'ptr ['in op:
            width={'byte':1,'word':2,'dword':4}[op.split()[0]];expr=op[op.index('[')+1:op.index(']')].replace(' ','');terms=re.findall(r'[+-]?[^+-]+',expr);address=0
            for term in terms:
                sign=-1 if term.startswith('-')else 1;term=term.lstrip('+-');address+=sign*(self.reg[term]if term in self.reg else int(term,0))
            return 'mem',address&0xffffffff,width*8
        if op.startswith('0x')or op.isdecimal():return 'imm',int(op,0),32
        name,shift,bits=self.alias(op);return 'reg',(name,shift),bits
    def val(self,op,pc):
        kind,arg,bits=self.operand(op)
        if kind=='mem':return self.load(arg,bits//8,pc),bits
        if kind=='imm':return arg,bits
        name,shift=arg;return(self.reg[name]>>shift)&((1<<bits)-1),bits
    def assign(self,op,value,pc):
        kind,arg,bits=self.operand(op);value&=(1<<bits)-1
        if kind=='mem':self.store(arg,value,bits//8,pc)
        else:
            need(kind=='reg','Writable exact source destination');name,shift=arg;mask=((1<<bits)-1)<<shift;self.reg[name]=(self.reg[name]&~mask)|(value<<shift)
    def logic(self,value,bits):
        value&=(1<<bits)-1
        for bit,x in((0,0),(2,(value&255).bit_count()%2==0),(4,0),(6,value==0),(7,(value>>(bits-1))&1),(11,0)):self.flags[bit]=int(x)
    def subtract(self,a,b,bits):
        mask=(1<<bits)-1;r=(a-b)&mask;self.logic(r,bits);self.flags[0]=int(a<b);self.flags[4]=((a^b^r)>>4)&1;self.flags[11]=((a^b)&(a^r)>>(bits-1))&1
        # Parenthesize the architectural sign-bit expression explicitly.
        self.flags[11]=int(bool(((a^b)&(a^r))&(1<<(bits-1))))
    def push(self,value,pc):self.reg['esp']-=4;self.store(self.reg['esp'],value,4,pc)
    def run(self):
        pc=0x78004254;self.event(2,pc,self.reg['esp'],self.load(self.reg['esp'],4,pc,False),4);steps=0
        while pc!=0x78004232:
            steps+=1;need(steps<1024 and pc in self.ins,'Complete bounded reached source CFG');self.executed.append(pc);i=self.ins[pc];mn=i['mnemonic'];ops=i['operands'].split(', ');nextpc=pc+i['size']
            if mn in('mov','movzx'):self.assign(ops[0],self.val(ops[1],pc)[0],pc)
            elif mn=='push':self.push(self.val(ops[0],pc)[0],pc)
            elif mn=='pop':v=self.load(self.reg['esp'],4,pc);self.reg['esp']+=4;self.assign(ops[0],v,pc)
            elif mn in('and','or','xor','test','cmp'):
                a,bits=self.val(ops[0],pc);b,_=self.val(ops[1],pc)
                if mn=='cmp':self.subtract(a,b,bits)
                else:
                    v=a&b if mn in('and','test')else a|b if mn=='or'else a^b;self.logic(v,bits)
                    if mn!='test':self.assign(ops[0],v,pc)
            elif mn=='not':v,bits=self.val(ops[0],pc);self.assign(ops[0],v^((1<<bits)-1),pc)
            elif mn in('je','jne','jmp'):
                if mn=='jmp'or(bool(self.flags[6])if mn=='je'else not self.flags[6]):nextpc=self.val(ops[0],pc)[0]
            elif mn=='call':
                target=self.val(ops[0],pc)[0]
                if pc in(0x780042a8,0x780042bc):
                    slot=0x7802e098 if pc==0x780042a8 else 0x7802e0d0;target=0x11000100 if pc==0x780042a8 else 0x11000200;self.event(6,pc,slot,target,4)
                self.push(nextpc,pc)
                if pc in(0x780042a8,0x780042bc,0x780042cc):
                    need(target in(0x11000100,0x11000200,0x11000300),'Actually issued native service token');entry=self.reg['esp'];args=8 if pc==0x780042bc else 4;self.reg['eax']=0x11001000 if pc==0x780042a8 else 0x11000300 if pc==0x780042bc else self.feature;self.reg['esp']+=4+args;self.routes.append((pc,target,nextpc,entry,self.reg['esp'],args,1));self.event(4,pc,target,self.reg['eax'],args)
                else:need(target in ENTRIES,'Exact compiled direct source target');nextpc=target;self.event(2,target,self.reg['esp'],self.load(self.reg['esp'],4,pc,False),4)
            elif mn=='ret':nextpc=self.load(self.reg['esp'],4,pc);self.reg['esp']+=4;self.event(3,nextpc,self.reg['esp'],nextpc,4)
            elif mn=='leave':self.reg['esp']=self.reg['ebp'];self.reg['ebp']=self.load(self.reg['esp'],4,pc);self.reg['esp']+=4
            elif mn=='wait':pass
            elif mn=='fnstcw':self.store(self.operand(ops[0])[1],h(self.fx,0),2,pc)
            elif mn=='fldcw':v=self.load(self.operand(ops[0])[1],2,pc);v=(v&0x1f3f)|0x40;put(self.fx,0,v,2);put(self.state,2768,v,2)
            elif mn=='fnclex':need(h(self.fx,2)==0,'Positive writer SW0 domain');self.event(5,pc,0,0,2)
            else:raise ValueError('Unsupported actually reached instruction '+mn)
            pc=nextpc
        self.reg['eip']=pc
        for name,offset in GPR.items():put(self.state,offset,self.reg[name])
        for offset,bit in AF:self.state[offset]=self.flags[bit]
        return bytes(self.state),bytes(self.pages),bytes(self.fx),self.events,self.routes,self.executed

def record(b,instructions,bindings):
    ident,repeat,cw,status,events,routes,lookups=u(b,0,7);need(ident<24 and repeat==ident%2 and cw==CW[ident//2]and status==1 and routes==lookups==3 and events<256,'Exact native record identity/count/domain')
    state0=b[28:3532];state1=b[3532:7036];fx0=b[7036:7548];fx1=b[7548:8060];host0=b[8060:8572];host1=b[8572:9084];env0=b[9084:9112];env1=b[9112:9140];pages0=b[9140:46004];pages1=b[46004:82868]
    need(host0==host1 and env0==env1,'Whole observed host FX512/ENV28 restored');need(h(fx0,0)==cw and h(fx0,2)==0 and fx0[4]==0,'Empty observed supported guest FP domain')
    need(state0[2768:2774]==fx0[:6]and state0[2792:2796]==fx0[24:28]and state0[2774:2792]!=fx0[6:24],'Distinct live State legacy metadata/separateFX retained')
    rawlookups=b[88072:107740];feature=None;modulehandles=[]
    for index,name in enumerate(('GetModuleHandleA','GetProcAddress','IsProcessorFeaturePresent')):
        l=rawlookups[index*6556:(index+1)*6556];kind,token,arg,result,error=u(l,0,5);host=q(l,20);need(kind==index+1 and arg==0,'Exact observed Windows lookup kind/feature0')
        handle,pe=module(l[4396:6556],bindings);modulehandles.append(handle);before=l[28:2212];after=l[2212:4396];need(before==after,'Actual stable API identity before/after service');target=api(before,name,pe,bindings)
        if index==0:need(host==handle and token==0x11001000 and result==0,'Actual module result owns opaque token')
        elif index==1:
            need(host and token==0x11000300 and result==0,'Actual non-null export owns function token');exports,d,n=pe.exports();r=exports['IsProcessorFeaturePresent'];need(d<=r<d+n or host==handle+r,'Actual returned exact feature export target');feature_target=host
        else:need(host==result and token==0x11000300 and target==feature_target,'Actual invoked looked-up feature target/BOOL observation');feature=result
    need(len(set(modulehandles))==1,'All lookups share exact actual borrowed module')
    expected=Model(state0,pages0,fx0,instructions,feature).run();need(state1==expected[0]and pages1==expected[1]and fx1==expected[2],'Complete3504 State/nine pages/separateFX exact source-instruction/native-policy model')
    actual=[u(b,82868+i*20,5)for i in range(events)];need(actual==expected[3],'All actual ordered access/call/FNCLEX events match source instruction model');need(not any(b[82868+events*20:87988]),'Zero unused event storage');need([u(b,87988+i*28,7)for i in range(3)]==expected[4],'Exact compiled indirect stdcall cleanup/continuations');return expected[5]

def main(build,out):
    build=pathlib.Path(build).resolve();out=pathlib.Path(out).resolve();need(build.parent.parent==out.parent==BASE and not out.exists(),'Fresh private validation output');out.mkdir();bindings={};m=read(build);need(m['passed']and not m['whole_M4_complete'],'Actual frozen native-only build pass required')
    for group in('sources','tools','artifacts'):
        for p,v in m[group].items():need(sha(p)==v,'Current exact build identity '+p);bindings[p]=v
    recovery=BASE/'source-recovery-r1/report.json';source=read(recovery);provider=PE(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL');instructions={}
    for graph in source['complete_graphs']:
        for i in graph['instructions']:
            need(provider.bytes(i['address'],i['size']).hex()==i['bytes_hex'],'Every recovered instruction byte agrees with actual provider')
            if i['address']in instructions:need(instructions[i['address']]==i,'Duplicate CFG node agrees')
            instructions[i['address']]=i
    need(len(instructions)==204,'Complete original dependency instruction union retained');allpcs=set();count=0;mutations=0
    for level in('O0','O2'):
        p=build.parent/f'native-{level}.bin';b=p.read_bytes();need(len(b)==24+24*STRIDE and struct.unpack_from('<8s4I',b)==(b'MW4FDIN2',2,24,STRIDE,9),'Exact complete native raw schema')
        for index in range(24):
            row=b[24+index*STRIDE:24+(index+1)*STRIDE];allpcs.update(record(row,instructions,bindings));count+=1
            # Causal observers cover each full State/page/FP region and all routes.
            offsets=(3532,3532+2768,3532+3280,7548,8060,9084,9112,46004,46004+6*4096+0xc2c,46004+7*4096+0x7dc,82868,87988,88072+20,88072+28,88072+4396)
            for offset in offsets:
                bad=bytearray(row);bad[offset]^=1
                try:record(bad,instructions,{})
                except(Exception):mutations+=1
                else:raise ValueError('Required raw observer mutation accepted '+str(offset))
    for p in(recovery,provider.path,pathlib.Path(__file__).resolve(),build):bindings[str(p)]=sha(p)
    report={'passed':True,'scope':'Native-only actual successful Windows-query writer; source/native representative validation, no original differential acceptance','native_records':count,'observed_events':sum(u((build.parent/'native-O0.bin').read_bytes(),24+i*STRIDE+16)[0]for i in range(24))*2,'original_dependency_PCs':204,'actual_reached_PCs':sorted(allpcs),'observer_controls':mutations,'complete_State_bytes':3504,'whole_owned_pages':9,'FNCLEX_defined_mask':'80FF','FNCLEX_CC_policy':'Preserve incoming as undefined native representative','dynamic_API_volatility':'Native preserves ECX/EDX/flags; future originals must retain actual unspecified residual halfwords','unsupported':'Actual NULL branches enter an explicit arithmetic-fallback denial; no OS NULL path measured','whole_M4_complete':False}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');bindings[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(bindings,indent=2)+'\n');print(json.dumps({'passed':True,'records':count,'controls':mutations,'reached_PCs':len(allpcs),'report_sha256':sha(out/'report.json')}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build',required=True);p.add_argument('--out',required=True);a=p.parse_args();main(a.build,a.out)
