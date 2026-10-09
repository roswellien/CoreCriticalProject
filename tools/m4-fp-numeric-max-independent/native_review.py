"""Independent standalone native review; imports only earlier root-owned reviewers.

The author's comparator, model, repair and adapter are read as evidence, never
executed. Numerical predictions come from the separate input-derived oracle.
Every run uses a fresh directory and preserves its own source and diagnostics.
"""
from contextlib import ExitStack
import hashlib
import importlib.util
import itertools
import json
import mmap
import ctypes
from pathlib import Path
import re
import struct
import subprocess
import sys
import traceback

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
GATE=ROOT/'reports/m4-fp-numeric-max'
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
PINS={}

def need(v,w):
    if not v:raise ValueError(w)

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def bind(p,h=None):
    p=Path(p).resolve();got=sha(p)
    need(h is None or got==h,'Physical identity '+str(p))
    need(str(p) not in PINS or PINS[str(p)]==got,'Conflicting binding')
    PINS[str(p)]=got
    return p

def read(p,h=None):return json.loads(bind(p,h).read_text(encoding='utf-8-sig'))
def u32(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def u16(b,o=0):return struct.unpack_from('<H',b,o)[0]
def put(b,o,v,n=4):b[o:o+n]=v.to_bytes(n,'little')

def own_module(path,name,expected):
    p=bind(path,expected);spec=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

ORACLE=own_module(ROOT/'tools/m4-fp-numeric-max-independent/original_model.py',
    'root_original_numeric_model','68fadd880cedfb4f18463b7428ebbf3a153334f730190a917fcb5753de50d148')
def layout_model(text):
    """Calculate this gate's ABI, including its explicit i128:64 host layout.

    An earlier CRT gate used i128:128. Query only scalar ABI alignment from
    the bound tool; all structure offsets and sizes are computed here.
    """
    datalayout=re.search(r'^target datalayout = "([^\"]+)"',text,re.M)[1]
    dll=bind(LLVM/'LLVM-C.dll','34142667abdc41941b37b3ecb3ff85d6593b9fb183873634016348d5181c57cb')
    api=ctypes.CDLL(str(dll));pointer=ctypes.c_void_p
    api.LLVMContextCreate.restype=pointer
    api.LLVMCreateTargetData.argtypes=[ctypes.c_char_p];api.LLVMCreateTargetData.restype=pointer
    api.LLVMIntTypeInContext.argtypes=[pointer,ctypes.c_uint];api.LLVMIntTypeInContext.restype=pointer
    api.LLVMABIAlignmentOfType.argtypes=[pointer,pointer];api.LLVMABIAlignmentOfType.restype=ctypes.c_uint
    api.LLVMDisposeTargetData.argtypes=[pointer];api.LLVMContextDispose.argtypes=[pointer]
    context=api.LLVMContextCreate();data=api.LLVMCreateTargetData(datalayout.encode())
    try:
        alignments={f'i{n}':api.LLVMABIAlignmentOfType(data,api.LLVMIntTypeInContext(context,n)) for n in (8,16,32,64,128)}
    finally:api.LLVMDisposeTargetData(data);api.LLVMContextDispose(context)
    need(alignments=={'i8':1,'i16':2,'i32':4,'i64':8,'i128':8},'Actual scalar alignment for this gate')
    types=dict(re.findall(r'^(%[\w.]+) = type (.+)$',text,re.M));cache={}
    def align(n,a):return (n+a-1)//a*a
    def calc(t):
        t=t.strip()
        if t in cache:return cache[t]
        if t in types:result=calc(types[t])
        elif t in alignments:result=(int(t[1:])//8,alignments[t],())
        elif m:=re.fullmatch(r'\[(\d+) x (.+)\]',t):
            size,a,_=calc(m[2]);result=(int(m[1])*align(size,a),a,())
        elif t.startswith('{ ') and t.endswith(' }'):
            cursor=0;alignment=1;offsets=[]
            for field in t[2:-2].split(', '):
                size,a,_=calc(field);cursor=align(cursor,a);offsets.append(cursor);cursor+=size;alignment=max(alignment,a)
            result=(align(cursor,alignment),alignment,tuple(offsets))
        else:raise ValueError('Unsupported independent layout '+t)
        cache[t]=result;return result
    for name in types:calc(name)
    need(cache['%struct.State'][:2]==(3504,8),'Complete State ABI3504/8 in this gate')
    return types,cache

def run(command,out):
    cp=subprocess.run([str(x) for x in command],capture_output=True)
    out.write_bytes(cp.stdout);out.with_suffix(out.suffix+'.stderr').write_bytes(cp.stderr)
    bind(out);bind(out.with_suffix(out.suffix+'.stderr'))
    need(cp.returncode==0,'Reviewer tool failed '+str(command[0]))
    return cp.stdout.decode('utf-8-sig')

class PE:
    def __init__(self,path,expected):
        self.path=bind(path,expected);self.bytes=self.path.read_bytes();b=self.bytes
        pe=u32(b,0x3c)[0];need(b[:2]==b'MZ' and b[pe:pe+4]==b'PE\0\0' and u16(b,pe+4)==0x14c,'Own x86 PE identity')
        self.optional=pe+24;need(u16(b,self.optional)==0x10b,'Own PE32 optional header')
        self.base=u32(b,self.optional+28)[0];count=u16(b,pe+6);self.sections=[]
        for i in range(count):
            at=pe+24+u16(b,pe+20)+i*40
            vs,rva,rs,ro=u32(b,at+8,4);flags=u32(b,at+36)[0]
            self.sections.append((rva,vs,ro,rs,flags))
    def offset(self,address,n=1,flags=None):
        rva=address-self.base;found=[]
        for start,vs,ro,rs,f in self.sections:
            if start<=rva and rva+n<=start+rs:
                need(flags is None or f&0xe0000000==flags,'Own exact PE protection')
                found.append(ro+rva-start)
        need(len(found)==1,'Own unique file-backed PE slice');return found[0]
    def fetch(self,a,n,flags=None):
        o=self.offset(a,n,flags);return self.bytes[o:o+n]
    def text(self,rva):
        o=self.offset(self.base+rva);end=self.bytes.index(0,o);return self.bytes[o:end].decode('ascii')
    def imports(self):
        rva,size=u32(self.bytes,self.optional+104,2);result={};o=self.offset(self.base+rva,size)
        for pos in range(o,o+size,20):
            original,_,_,name,iat=u32(self.bytes,pos,5)
            if not any((original,name,iat)):break
            lib=self.text(name);j=0
            while True:
                value=u32(self.fetch(self.base+(original or iat)+j*4,4))[0]
                if not value:break
                symbol=value&0xffff if value&0x80000000 else self.text(value+2)
                result[self.base+iat+j*4]=(lib,symbol);j+=1
        return result
    def exports(self):
        rva,size=u32(self.bytes,self.optional+96,2);o=self.offset(self.base+rva,40)
        first,count,names,table,name_table,ord_table=u32(self.bytes,o+16,6);result={}
        for i in range(names):
            name=self.text(u32(self.fetch(self.base+name_table+4*i,4))[0])
            index=u16(self.fetch(self.base+ord_table+2*i,2))
            address=self.base+u32(self.fetch(self.base+table+4*index,4))[0]
            result[name]=(first+index,address)
        return result

def body(text,entry):
    m=re.search(r'^define [^\n]*@sub_'+f'{entry:x}'+r'\([^\n]+\) [^\n]*\{\n(.*?)^\}',text,re.M|re.S)
    need(m is not None,'Exact one lifted body');return m[1]

def canonical(text):
    text=re.sub(r'^(\d+):',r'%\1:',text,flags=re.M)
    text=re.sub(r' #[0-9]+','',text);names={}
    def replace(m):
        value=m[0]
        if value.startswith(('%struct.','%union.')):return value
        if value not in names:names[value]=f'%v{len(names)}'
        return names[value]
    return re.sub(r'\s+',' ',re.sub(r'%[A-Za-z0-9_.]+',replace,text)).strip()

def reverse_host(b,entry,repaired):
    counts={}
    if entry==0x780c10f0:
        b,n=re.subn(r'(%\d+) = call x86_fp80 @llvm.experimental.constrained.fpext.f80.f32\(float (%\d+), metadata !"fpexcept.strict"\)',r'\1 = fpext float \2 to x86_fp80',b);need(n==1,'Single exact strict extension');counts['strict_fpext']=n
    if entry==0x4c1a00:
        b,n=re.subn(r'(%\d+) = call float @llvm.experimental.constrained.fptrunc.f32.f80\(x86_fp80 (%\d+), metadata !"round.dynamic", metadata !"fpexcept.strict"\)',r'\1 = fptrunc x86_fp80 \2 to float',b);need(n==1,'Single exact dynamic strict truncation');counts['strict_fptrunc']=n
        b,n=re.subn(r'^  %\d+ = call ptr @mw34_numeric_body_entry\(ptr %state, i32 %program_counter, ptr %memory\)\n','',b,flags=re.M);need(n==1,'Exact typed body observation');counts['body_observer']=n
    if repaired and entry in (0x780c10f0,0x4c1a00):
        kind='fld' if entry==0x780c10f0 else 'fstp'
        b,n=re.subn(r'^  call void @mw34_numeric_'+kind+r'_commit\(ptr %state, ptr %memory\)\n','',b,flags=re.M);need(n==1,'Exact physical tag commit only');counts['tag_commit']=n
    if repaired and entry==0x4c1a00:
        pattern=r'  %numeric_prior_de = load i8, ptr (%\d+), align 1\n  %numeric_sticky_de = or i8 (%\d+), %numeric_prior_de\n  store i8 %numeric_sticky_de, ptr \1, align 1'
        b,n=re.subn(pattern,r'  store i8 \2, ptr \1, align 1',b);need(n==1,'Exact sticky DE repair only');counts['sticky_de']=n
    return b,counts

def source_review(out):
    game=PE(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
    provider=PE(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a')
    need(u32(game.fetch(0x5e016c,4))[0]==0x4c19f0,'Actual table root')
    imp=game.imports()[0x5bb4fc]
    need(imp[0].casefold()=='msvcp50.dll' and isinstance(imp[1],str),'Owning MSVCP50 named IAT')
    need(provider.exports()[imp[1]]==(1545,0x780c10f0),'Actual named ordinal1545 export')
    need(provider.fetch(0x78115004,4)==struct.pack('<I',ORACLE.WORDS[0]),'Actual default maximum f32 literal')
    specs=((game,0x4c19f0,10),(game,0x4c1a00,117),(provider,0x780c10f0,7));decoded=[];layout_report=[]
    expected=((0x4c19f0,1),(0x4c19f1,2),(0x4c19f3,5),(0x4c19f8,1),(0x4c19f9,1),
        (0x4c1a00,1),(0x4c1a01,2),(0x4c1a03,6),(0x4c1a09,6),
        *((0x4c1a0f+10*i,10) for i in range(10)),(0x4c1a73,1),(0x4c1a74,1),(0x780c10f0,6),(0x780c10f6,1))
    tool=bind(LLVM/'llvm-objdump.exe')
    for image,entry,size in specs:
        text=run([tool,'--disassemble','--x86-asm-syntax=intel',f'--start-address={entry}',f'--stop-address={entry+size}',image.path],out/f'source-{entry:x}.txt')
        rows=[]
        for line in text.splitlines():
            m=re.match(r'^\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([^\s]+)\s*(.*)$',line)
            if m:
                pc=int(m[1],16);raw=bytes.fromhex(m[2]);need(raw==image.fetch(pc,len(raw),0x60000000),'Source decode literal equality')
                rows.append((pc,len(raw)));decoded.append({'pc':pc,'size':len(raw),'bytes':raw.hex(),'mnemonic':m[3],'operands':m[4]})
        guest=bind(GATE/f'recovery-r1/{entry:x}.ll').read_text();host=bind(GATE/f'repaired-r2/{entry:x}-host.ll').read_text();repaired=bind(GATE/f'repaired-r2/{entry:x}-repaired.ll').read_text()
        pcs=tuple(int(x) for x in re.findall(r'; ([0-9]+):',guest))
        # Remill blocks print hexadecimal addresses in the instruction comments.
        if not pcs:pcs=tuple(int(x,16) for x in re.findall(r'; 0x([0-9a-f]+):',guest))
        types,layouts=layout_model(guest);h_types,h_layouts=layout_model(host)
        need(types==h_types and layouts==h_layouts,'Independent all34 guest/host type layouts')
        adapter=read(GATE/f'repaired-r2/{entry:x}-adapter.json')
        need(set(adapter['layouts'])=={x[1:] for x in types},'Complete author layout inventory')
        for name in types:
            size_,alignment,offsets=layouts[name]
            need(adapter['layouts'][name[1:]]=={'size':size_,'alignment':alignment,'offsets':list(offsets)},'Independent exact ABI layout '+name)
        plain,c1=reverse_host(body(host,entry),entry,False);fixed,c2=reverse_host(body(repaired,entry),entry,True)
        need(canonical(plain)==canonical(body(guest,entry)),'Exact guest-to-host body reversal')
        need(canonical(fixed)==canonical(body(guest,entry)),'Exact measured repair reversal')
        for candidate in (host,repaired):
            need(not re.search(r'\b(?:inttoptr|ptrtoint|fast|nnan|ninf|reassoc)\b',candidate),'No unreviewed pointer casts or relaxed FP')
            attrs={m[1]:m[2] for m in re.finditer(r'^attributes #(\d+) = \{([^\n]+)\}',candidate,re.M)}
            for declaration in re.findall(r'^(?:define|declare)[^\n]+@(?:sub_[a-f0-9]+|__remill_[a-z0-9_]+|mw34_numeric_[a-z0-9_]+)\([^\n]*\)[^\n]*',candidate,re.M):
                a=re.search(r'#(\d+)',declaration);flags=attrs[a[1]] if a else ''
                need('nounwind' not in flags and 'willreturn' not in flags,'Required guest/bridge fault escape attributes')
        layout_report.append({'entry':entry,'types':len(types),'layouts_equal':True,'host_changes':c1,'repaired_changes':c2,'IR_instruction_comments':len(pcs)})
    need(tuple((x['pc'],x['size']) for x in decoded)==expected,'Complete exact23-instruction schedule')
    need(decoded[2]['mnemonic']=='call' and decoded[7]['mnemonic']=='call' and decoded[8]['mnemonic']=='fstp' and decoded[-2]['mnemonic']=='fld','Actual required control and FP operations')
    (out/'source-decoder.json').write_text(json.dumps(decoded,indent=2)+'\n');bind(out/'source-decoder.json')
    return layout_report

def seed_state(case):
    rep,inp,depth,sticky,cw,top,entry=case
    state=bytearray((i*29+rep*71+inp*11+(i>>8)*7)&255 for i in range(3504))
    state[2112:2208]=bytes(96)
    for p,v in ((2090,0x2b),(2106,0x2b),(2110,0x23)):put(state,p,v,2)
    for p,v in zip((2216,2248,2264,2232,2312,2328,2280,2296,2472),
        (0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xaabbccdd,entry)):put(state,p,v)
    put(state,2080,0x202,8)
    for p in (2065,2067,2069,2071,2073,2075,2077):state[p]=0
    fx=bytearray(512);put(fx,0,cw,2);put(fx,2,(top<<11)|(0,2,34)[sticky],2);fx[4]=ORACLE.tags(top,depth)[0];put(fx,24,0x1f80)
    for i in range(8):fx[32+16*i:42+16*i]=struct.pack('<QH',(1<<63)+(i<<56),0x4000|(0x8000 if i&1 else 0))
    state[2768:3280]=fx
    for p,v,n in ((2774,0x11d,2),(2776,0x11223344,4),(2780,0x23,2),(2784,0x55667788,4),(2788,0x2b,2)):put(state,p,v,n)
    for p,bit in ((2737,8),(2739,9),(2741,10),(2743,14),(2745,5),(2747,4),(2749,3),(2751,2),(2753,1),(2755,0),(2757,6)):state[p]=(u16(fx,2)>>bit)&1
    for i in range(8):
        state[2486+16*i:2496+16*i]=fx[32+16*i:42+16*i];state[16+64*i:32+64*i]=bytes(16)
    return state

def observed_state(seed,cpu,fx,env):
    state=bytearray(seed);c=u32(cpu,0,10)
    for p,v in zip((2216,2248,2264,2232,2312,2328,2280,2296,2472),c[:8]+(c[9],)):put(state,p,v)
    sw=u16(fx,2);put(state,2770,(u16(state,2770)&~0x3800)|(sw&0x3800),2);state[2772]=fx[4]
    for p,bit in ((2737,8),(2739,9),(2741,10),(2743,14),(2745,5),(2747,4),(2749,3),(2751,2),(2753,1),(2755,0),(2757,6)):state[p]=(sw>>bit)&1
    for i in range(8):state[2486+16*i:2496+16*i]=fx[32+16*i:42+16*i]
    for p,o,n in ((2774,18,2),(2776,12,4),(2780,16,2),(2784,20,4),(2788,24,2)):state[p:p+n]=env[o:o+n]
    return state

def fxparts(b):return (b[:5],b[24:28],*(b[32+i*16:42+i*16] for i in range(8)),b[160:288])
def frame_cpu(esp,ebp,pc):return struct.pack('<10I',0x13579bdf,0x2468ace0,0x81726354,0x10293847,esp,ebp,0x56473829,0xaabbccdd,0x202,pc)

def events_and_routes(original,case):
    memory=bytearray(original[2280:18664]);trace=[];leaf=case[-1]==0x780c10f0
    def offset(a):
        bases=(0x5bb000,0x78115000,0x60b000,0x20001000);need(a&~4095 in bases,'Bounded event page');return bases.index(a&~4095)*4096+(a&4095)
    def read_(a):
        value=u32(memory,offset(a))[0];trace.append((a,value,4,0));return value
    def write(a,v):put(memory,offset(a),v);trace.append((a,v,4,1))
    if leaf:read_(0x78115004);read_(0x20001800);routes=bytes(192)
    else:
        write(0x200017fc,0x92837465);write(0x200017f8,0x4c19f8);write(0x200017f4,0x200017fc)
        need(read_(0x5bb4fc)==0x780c10f0,'Owning literal projected provider address');write(0x200017f0,0x4c1a09)
        value=read_(0x78115004);read_(0x200017f0);write(0x60b368,ORACLE.widen(value)[3])
        for a in range(0x60b36c,0x60b394,4):write(a,0)
        for a in (0x200017f4,0x200017f8,0x200017fc,0x20001800):read_(a)
        routes=(struct.pack('<4I',0x4c1a00,0x4c19f8,0,1)+frame_cpu(0x200017f8,0x200017fc,0x4c1a00)+frame_cpu(0x200017fc,0x200017fc,0x4c19f8)
            +struct.pack('<4I',0x780c10f0,0x4c1a09,0,1)+frame_cpu(0x200017f0,0x200017f4,0x780c10f0)+frame_cpu(0x200017f4,0x200017f4,0x4c1a09))
    need(memory==original[18664:35048],'Source event replay produces complete actual pages')
    packed=b''.join(struct.pack('<4I',*x) for x in trace)
    return packed+bytes(352-len(packed)),routes,len(trace)

def observe_native(original,native,case,paired_leaf,pack):
    need(len(native)==47432,'Complete native record extent');ORACLE.observe(original,case)
    need(native[:120]==original[:120],'All tag/CPU/FLAGS/return bytes')
    for o in (120,632):
        need(fxparts(native[o:o+512])==fxparts(original[o:o+512]),'Native architectural FX/raw80/XMM projection')
        need(native[o+6:o+24]==bytes(18),'Explicit hardware metadata zero projection')
    need(native[2168:2224]==original[2168:2224],'Complete separate legacy metadata')
    need(native[2280:35048]==original[2280:35048],'Complete native before/after four pages')
    before=bytearray().join(pack[12+i*4104+8:12+(i+1)*4104] for i in (3,4,5,6))
    put(before,4096+4,ORACLE.WORDS[case[1]]);before[8192+0x368:8192+0x394]=bytes([0xa5])*44;put(before,12288+0x800,0x10000100)
    need(original[2280:18664]==before,'Exact pack-derived complete input pages')
    need(fxparts(native[1144:1656])==fxparts(native[1656:2168]) and native[2224:2252]==native[2252:2280],'Native host FP/raw80/legacy restoration')
    need(native[1304:1560]==native[1816:2072],'All16 native host XMM restoration')
    need(native[35048:35764]==bytes(716),'Native does not counterfeit original CONTEXT')
    seed=seed_state(case);need(native[35764:39268]==seed,'Independent entire seeded3504 State')
    expected=observed_state(seed,original[80:120],original[632:1144],original[2196:2224])
    need(native[39268:42772]==expected,'Independent complete projected/protected3504 State')
    leaf=case[-1]==0x780c10f0
    if leaf:need(native[42772:46856]==bytes(4084),'Unused native checkpoint wholly zero')
    else:
        need(paired_leaf is not None,'Actual immediately paired provider observation')
        context=original[35048:35764];cpu=frame_cpu(0x200017f4,0x200017f4,0x4c1a09)
        need(native[42772:42812]==cpu,'Actual provider-return checkpoint CPU')
        fx=context[204:716]
        need(fxparts(native[42812:43324])==fxparts(fx),'Actual connected debugger FX/raw80/XMM checkpoint')
        env=paired_leaf[2196:2224]
        need(native[43324:43352]==env,'Checkpoint legacy metadata paired-leaf inference only')
        need(native[43352:46856]==observed_state(seed,cpu,fx,env),'Independent complete connected checkpoint State')
    need(u32(native,46856,8)==((2,2,0,0,0,1,0,0) if leaf else (22,7,15,1,1,3,2,0)),'All eight actual bridge counters')
    trace,routes,count=events_and_routes(original,case)
    need(native[46888:47240]==trace,'Exact ordered memory address/value/width/operation events plus padding')
    need(native[47240:47432]==routes,'Complete actual CALL/RET routes and CPU frames')
    return count,0 if leaf else 2

def mutations(o,n,case,paired,pack):
    results=[]
    for offset in (0,40,80,120,632,634,636,664,792,2168,2196,2280,18664,35048,35764,35764+42,35764+2216,35764+2772,39268,39268+2472,39268+2486,39268+2737,39268+2770,39268+2772,42772,42812,42816,42844,43324,43352,43352+2312,43352+2486,46856,46860,46888,46892,46896,46900,47240,47244,47252,47256,47336,47392):
        changed=bytearray(n);changed[offset]^=1
        try:observe_native(o,changed,case,paired,pack)
        except ValueError as e:results.append({'offset':offset,'rejected':True,'diagnostic':str(e)})
        else:raise ValueError('Independent native observer accepted offset '+str(offset))
    return results

def audit_author(out):
    seal=read(GATE/'author-review-r1/report.json','93e1d9f1ffb72592a2d36bbcaad934e8a9af98af2884a7280ba71b418c662563')
    pins=read(GATE/'author-review-r1/pins.json','3c8b64b263c4674e5b4e2683979eed3609405520ae52545959434b3e6b9b7db0')
    for row in pins['bindings']:bind(row['path'],row['sha256'])
    need(len(pins['bindings'])==2390,'Complete2390 physical author bindings')
    for row in seal['source_copies']:
        info=row['preserved'];bind(info['path'],info['sha256'])
    for row in seal['historical_binding_resolutions']:
        bind(row['physical_path'],row['sha256'])
    decodes=[]
    for i,row in enumerate(seal['actual_COFF_decodes']):
        obj=bind(row['object']['path'],row['object']['sha256'])
        text=run([bind(LLVM/'llvm-objdump.exe'),'--disassemble','--reloc','--x86-asm-syntax=intel',obj],out/f'object-{i}.txt')
        need(bool(re.search(r'^\s*[0-9a-f]+:',text,re.M)),'Actual COFF instruction decode')
        if i<2:
            need('mw34_numeric_fld_commit' in text and 'mw34_numeric_fstp_commit' in text and '__remill_function_call' in text and 'fstp' in text and 'fld' in text,'Actual compiled FP/typed repair/route object')
        decodes.append({'path':str(obj),'object_sha256':sha(obj),'review_decode':str(out/f'object-{i}.txt')})
    build=read(seal['final_build']['path'],seal['final_build']['sha256'])
    # Every recorded identity map entry is checked; historical identities must
    # have an explicit literal association in the author seal rather than use
    # whichever live source happens to exist today.
    resolutions={}
    for row in seal['historical_binding_resolutions']:
        resolutions[(str(Path(row['original_path']).resolve()).casefold(),row['sha256'])]=row['physical_path']
    for key in ('sources','bindings'):
        for p,h in build.get(key,{}).items():
            if Path(p).is_file() and sha(p)==h:bind(p,h)
            else:need((str(Path(p).resolve()).casefold(),h) in resolutions,'Explicit historical final-build binding')
    return {'author_files':len(pins['bindings']),'source_copies':len(seal['source_copies']),'object_decodes':decodes,'author_scope':seal['scope']}

def main(out):
    need(out.is_relative_to(GATE) and not out.exists(),'Fresh independent native review')
    out.mkdir(parents=True);(out/'review-source.py').write_bytes(Path(__file__).read_bytes());bind(out/'review-source.py')
    try:
        static=source_review(out);author=audit_author(out)
        pack=bind(GATE/'recovery-r1/pages.bin','8948ef612175ae87a78fb8fdf5222154ea101bd44f8c89f42acd4d3110cd1381').read_bytes()
        comparisons=[];controls=[]
        for mode in ('default','directed'):
            cases=list(itertools.product(range(2),range(16 if mode=='directed' else 1),(0,1,7),range(3),ORACLE.CWS,(0,7),(0x780c10f0,0x4c19f0)))
            op=bind(GATE/f'original-r5-normal-windows/{mode}.bin')
            for level in ('O0','O2'):
                np=bind(GATE/f'repaired-r2/{mode}-{level}.bin');event_count=route_count=0
                with ExitStack() as stack:
                    of=stack.enter_context(op.open('rb'));nf=stack.enter_context(np.open('rb'))
                    original=stack.enter_context(mmap.mmap(of.fileno(),0,access=mmap.ACCESS_READ));native=stack.enter_context(mmap.mmap(nf.fileno(),0,access=mmap.ACCESS_READ))
                    need(original[:8]==b'MW4NMO01' and u32(original,8,4)==(1,len(cases),35764,4) and len(original)==24+len(cases)*35764,'Own complete original framing')
                    need(native[:8]==b'MW4NMN01' and u32(native,8,4)==(1,len(cases),47432,4) and len(native)==24+len(cases)*47432,'Own complete native framing')
                    for i,case in enumerate(cases):
                        o=original[24+i*35764:24+(i+1)*35764];n=native[24+i*47432:24+(i+1)*47432]
                        paired=original[24+(i-1)*35764:24+i*35764] if case[-1]==0x4c19f0 else None
                        ec,rc=observe_native(o,n,case,paired,pack);event_count+=ec;route_count+=rc
                    controls+=mutations(original[24+35764:24+2*35764],native[24+47432:24+2*47432],cases[1],original[24:24+35764],pack)
                comparisons.append({'mode':mode,'level':level,'records':len(cases),'events':event_count,'routes':route_count,'passed':True})
                print(json.dumps(comparisons[-1]),flush=True)
        report={'passed':True,'scope':'Independent bounded standalone numeric-max source/host/native/observation gate. Shared Runtime/MSVCP50 services and full M4 remain open.',
            'comparisons':comparisons,'observer_controls':controls,'static_review':static,'author_identity_review':author,
            'native_records':sum(x['records'] for x in comparisons),'native_ordered_events':sum(x['events'] for x in comparisons),'native_routes':sum(x['routes'] for x in comparisons),
            'shared_runtime_integrated':False,'whole_M4_complete':False,
            'limitations':['Only declared 16 f32 words,12 masked CWs,TOP0/7,depth0/1/7,sticky0/DE/DE+PE and serial fixed mappings/frames. No unmasked/pending/overflow/general live-stack admission.',
                'Original complete Remill State and event log are unobserved; entire native seeded/protected State and events are independently projected from inputs, hardware observations and exact23 source instructions.',
                'Checkpoint legacy metadata is explicitly paired actual leaf FNSTENV plus no-FP integer route inference, separate from literal zero-metadata Windows debugger CONTEXT.',
                'Finite exact values and C1=0 are proved in the bounded domain; special C1,C0/C2/C3 and dead raw80 remain actual observations.',
                'Tool/source/object identities establish recorded post-build association, not historical per-instruction tool execution attestation. Sequential ordinary private directories only.']}
        rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');bind(rp);bind(Path(__file__))
        (out/'pins.json').write_text(json.dumps({'files':dict(sorted(PINS.items()))},indent=2)+'\n')
        print(json.dumps({'passed':True,'report_sha256':sha(rp),'pins_sha256':sha(out/'pins.json'),'bindings':len(PINS),'native_records':report['native_records']}),flush=True)
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
