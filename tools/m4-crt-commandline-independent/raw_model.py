"""Independent byte/source model. Imports no author executor, comparator or oracle."""
import hashlib, json, pathlib, re, struct, sys

ROOT=pathlib.Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-commandline-native'
WRITER=0x7800188c; IAT=0x7802e034; GLOBAL=0x78037174; GAMEIAT=0x5bb518
RETURN=WRITER+6; CAPTURE=0x10000100; SERVICE=0x10000200; FRAME=0x20001800; BUFFER=0x33000000
CW=(0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f)
INITIAL=(0x13579bdf,0x2468ace0,0x81726354,0x10293847,FRAME,0x92837465,0x56473829,0xaabbccdd,0x202,WRITER)
GPR=(2216,2248,2264,2232,2312,2328,2280,2296,2472)
AF=((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11))
RECORD=56456

def need(value, reason):
    if not value: raise ValueError(reason)
def u(b,o,n=1): return struct.unpack_from('<'+str(n)+'I',b,o)
def h(b,o): return struct.unpack_from('<H',b,o)[0]
def q(b,o): return struct.unpack_from('<Q',b,o)[0]
def put(b,o,v,n=4): b[o:o+n]=v.to_bytes(n,'little')
def sha(path):
    with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(path):return json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig'))

class PE:
    def __init__(self,path):
        self.path=pathlib.Path(path);self.b=self.path.read_bytes();p=u(self.b,0x3c)[0]
        need(self.b[:2]==b'MZ' and self.b[p:p+4]==b'PE\0\0','Actual PE identity')
        self.machine=h(self.b,p+4);count=h(self.b,p+6);size=h(self.b,p+20);o=p+24;self.magic=h(self.b,o)
        need(self.magic in (0x10b,0x20b),'Actual PE optional header')
        self.base=u(self.b,o+28)[0] if self.magic==0x10b else q(self.b,o+24)
        self.directory=o+(96 if self.magic==0x10b else 112);self.sections=[]
        for i in range(count):
            s=o+size+40*i;vs,rva,raw,off=u(self.b,s+8,4);flags=u(self.b,s+36)[0]
            need(off+raw<=len(self.b),'Actual PE raw bounds');self.sections.append((rva,vs,raw,off,flags))
    def offset(self,rva,size):
        for r,vs,raw,off,flags in self.sections:
            if r<=rva and rva+size<=r+raw:return off+rva-r
        raise ValueError('Required source RVA not file-backed')
    def bytes(self,va,size):return self.b[self.offset(va-self.base,size):self.offset(va-self.base,size)+size]
    def string(self,rva):
        result=bytearray()
        for i in range(4096):
            x=self.b[self.offset(rva+i,1)]
            if not x:return result.decode('ascii')
            result.append(x)
        raise ValueError('Actual PE string bound')
    def exports(self):
        rva=u(self.b,self.directory)[0];o=self.offset(rva,40);count,names,funcs,strings,ords=u(self.b,o+20,5)
        need(count<=65536 and names<=count,'Actual export bounds');result={}
        for i in range(names):
            name=self.string(u(self.b,self.offset(strings+4*i,4))[0]);slot=h(self.b,self.offset(ords+2*i,2))
            need(slot<count and name not in result,'Unique actual export');result[name]=u(self.b,self.offset(funcs+4*slot,4))[0]
        return result
    def imports(self):
        rva,size=u(self.b,self.directory+8,2);result=[]
        for i in range(size//20):
            o=self.offset(rva+20*i,20);oft,ts,forward,name,iat=u(self.b,o,5)
            if not any((oft,ts,forward,name,iat)):return result
            library=self.string(name)
            for j in range(8192):
                v=u(self.b,self.offset((oft or iat)+4*j,4))[0]
                if not v:break
                result.append((self.base+iat+4*j,library,None if v&0x80000000 else self.string(v+2),v))
            else:raise ValueError('Import terminator')
        raise ValueError('Descriptor terminator')

def source_contract():
    provider=PE(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL');game=PE(ROOT/'MW3/Mech3.exe')
    code=provider.bytes(WRITER,11)
    need(code[:2]==bytes((0xff,0x15)) and u(code,2)==(IAT,) and code[6]==0xa3 and u(code,7)==(GLOBAL,), 'Independent literal two-instruction decode')
    need([row for row in provider.imports() if row[0]==IAT]==[(IAT,'KERNEL32.dll','GetCommandLineA',214062)],'Actual provider owner/raw thunk')
    need([row[:3] for row in game.imports() if row[0]==GAMEIAT]==[(GAMEIAT,'MSVCRT.dll','_acmdln')],'Actual game data owner')
    need(provider.exports()['_acmdln']+provider.base==GLOBAL and provider.bytes(GLOBAL,4)==bytes(4),'Actual data export identity, not inferred initialized value')
    pack=(BASE/'static-r1/pack.bin').read_bytes();need(pack[:8]==b'MW4CNPK1' and len(pack)==12324 and u(pack,8)==(3,),'Private pack extent')
    pages=[]
    for i,(addr,flags)in enumerate(((0x78001000,5),(0x7802e000,1),(0x78037000,3))):
        o=12+4104*i;need(u(pack,o,2)==(addr,flags),'Source page roles');pages.append(pack[o+8:o+4104])
    need(pages[0][0x88c:0x897]==code and pages[0][0x897]==0xe9 and (0x7800189c+u(pages[0],0x898)[0])&0xffffffff==CAPTURE,'Authored capture jump following exact original bytes')
    need(pages[1]==provider.bytes(0x7802e000,4096) and pages[2]==provider.bytes(0x78037000,4096),'Literal RO/RW source pages')
    # Resolve the original instrumented CALL return through independent COFF
    # relocation matching against the actual final executable, not a record guess.
    obj=next((ROOT/'build/m4-crt-commandline-native-original-build-r3').rglob('original_x86*.obj'))
    b=obj.read_bytes();count=h(b,2);symoff,ns=u(b,8,2);strings=symoff+18*ns;symbols={};i=0
    while i<ns:
        off=symoff+18*i;name=b[off:off+8]
        if name[:4]==bytes(4):
            at=strings+u(name,4)[0];end=b.index(0,at);name=b[at:end]
        else:name=name.rstrip(b'\0')
        val=u(b,off+8)[0];section=h(b,off+12);aux=b[off+17];symbols[i]=(name.decode(),val,section);i+=1+aux
    service=next(v for v in symbols.values() if v[0]=='_cmd_service');end=next(v[1] for v in symbols.values() if v[0]=='_crt_restore');section=20+40*(service[2]-1)
    raw,roff,reloff=u(b,section+16,3);nr=h(b,section+32);text=bytearray(b[roff+service[1]:roff+end]);mask=bytearray(b'\xff'*len(text));call=None
    for i in range(nr):
        a,sy=u(b,reloff+10*i,2)
        if service[1]<=a<end:
            local=a-service[1];mask[local:local+4]=bytes(4)
            if symbols[sy][0]=='_cmd_api':need(text[local-2:local]==bytes((0xff,0x15)),'Actual indirect API CALL relocation');call=local-2
    need(call is not None,'Actual cmd_api relocation present')
    exe=PE(ROOT/'build/m4-crt-commandline-native-original-build-r3/Release/commandline_original.exe');matches=[]
    for r,vs,raw,off,flags in exe.sections:
        if flags&0x20000000:
            region=exe.b[off:off+raw]
            # The first six nonrelocated opcodes narrow candidates cheaply.
            for a in range(len(region)-len(text)+1):
                if region[a]==text[0] and all(not m or region[a+j]==text[j] for j,m in enumerate(mask)):
                    matches.append(exe.base+r+a)
    need(len(matches)==1,'Unique complete linked assembler body/relocation match')
    inner_return=matches[0]+call+6
    return provider,game,pages,inner_return,exe,obj

def seed_fx(cw,top,native):
    b=bytearray(512);put(b,0,cw,2);put(b,2,top<<11,2);put(b,24,0x1f80)
    if not native:put(b,28,0x2ffff)
    for i in range(8):
        for j in range(10):b[32+16*i+j]=(17+13*i+7*j)&255
    for i in range(128):b[160+i]=(19*i+3)&255
    if native:
        put(b,6,0x11d,2);put(b,8,0x11223344);put(b,12,0x23,2);put(b,16,0x55667788);put(b,20,0x2b,2)
    return bytes(b)
def seed_env(cw,top):return struct.pack('<7I',0xffff0000|cw,0xffff0000|(top<<11),0xffffffff,0x11223344,0x11d0023,0x55667788,0xffff002b)
def state_seed(cw,top,repeat):
    b=bytearray((i*29+cw+repeat*3571+(i>>8)*7)&255 for i in range(3504));b[2112:2208]=bytes(96);put(b,2168,0x7ffde000)
    for o,v in ((2090,0x2b),(2094,0x2b),(2106,0x2b),(2110,0x23)):put(b,o,v,2)
    fx=seed_fx(cw,top,True);b[2768:3280]=fx
    for i in range(8):b[2486+16*i:2496+16*i]=fx[32+16*i:42+16*i];b[16+64*i:32+64*i]=fx[160+16*i:176+16*i]
    for i in range(11):b[2737+2*i]=0
    for offset,value in zip(GPR,INITIAL[:8]+(WRITER,)):put(b,offset,value)
    put(b,2080,0x202,8)
    for offset,bit in AF:b[offset]=(0x202>>bit)&1
    return bytes(b)
def state_project(b):
    fx=bytearray(b[2768:3280])
    for i in range(8):fx[32+16*i:42+16*i]=b[2486+16*i:2496+16*i];fx[160+16*i:176+16*i]=b[16+64*i:32+64*i]
    env=struct.pack('<7I',0xffff0000|h(fx,0),0xffff0000|h(fx,2),0xffffffff,u(fx,8)[0],h(fx,12)|(h(fx,6)<<16),u(fx,16)[0],0xffff0000|h(fx,20))
    return bytes(fx),env

def host_restore(a,b,e,f,native):
    need(a[:5]==b[:5] and a[24:28]==b[24:28] and e==f,'Host CW/SW/FTW/MXCSR/legacy restoration')
    for i in range(8):need(a[32+16*i:42+16*i]==b[32+16*i:42+16*i],'Host complete raw80 restoration')
    need(a[160:160+(256 if native else 128)]==b[160:160+(256 if native else 128)],'Host full applicable SIMD restoration')

def api(b,native,bindings):
    target,named,owner,owner_named=struct.unpack_from('<4Q',b);region=struct.unpack_from('<3Q4I',b,32)
    need(target==named==owner_named and target>=owner and region[0]<=target<region[0]+region[1] and region[2]==owner,'Actual target/named owner/address range identity')
    need(region[3]==0x1000 and region[4]==0x1000000 and region[5]&0xf0 and not region[5]&0x101,'Actual API executable image protection')
    rawpath=b[136:2184];n=rawpath.find(b'\0\0',1)
    if n&1:n+=1
    need(n>=0 and not any(rawpath[n:]),'Bounded zero-terminated UTF16 module path');path=pathlib.Path(rawpath[:n].decode('utf-16le'))
    # x86 disk open from the measured process redirects logical System32.
    physical=path if native else pathlib.Path(str(path).replace('System32','SysWOW64').replace('system32','SysWOW64'))
    pe=PE(physical);need(pe.machine==(0x8664 if native else 0x14c),'Actual associated module machine')
    need(b[72:136].decode()==sha(physical) and pe.exports()['GetCommandLineA']==target-owner,'Actual disk identity and direct named export RVA')
    bindings[str(physical.resolve())]=sha(physical)
    return region

def row_check(r,regions,owned,observed,index,native,context):
    provider,game,pages,inner_return,exe,obj=context
    tags=u(r,0,13);cw=CW[(index%24)//2];top=(index%2)*7;repeat=index//24
    need(tags[:7]==(index,repeat,cw,top,int(native),0,1) and tags[7]==len(observed) and tags[8]==len(regions) and tags[9]==GLOBAL and tags[12]==1,'Directed domain and actual successful capture tags')
    pointer=q(r,212);guest=BUFFER if native else pointer
    need(pointer and pointer==context.process_pointer and (native or pointer<=0xffffffff) and tags[10]==guest,'Distinct stable actual host/guest pointer domains across each process')
    need(owned==observed and owned[-1:]==b'\0' and b'\0' not in owned[:-1] and len(owned)<=131072,'Complete owning NUL-terminated input bytes')
    end=pointer+len(owned)
    covered=pointer
    for base,size,allocation,state,typ,prot,aprot in regions:
        need(state==0x1000 and size and base<=covered<base+size and not prot&0x101 and prot&(2|4|8|32|64|128),'Actual borrowed input readable ownership extent')
        covered=min(end,base+size)
    need(covered==end,'Complete borrowed pointer readable coverage')
    api(r[220:2404],native,context.bindings);api(r[2404:4588],native,context.bindings)
    need(r[220:2404]==r[2404:4588],'API identity stable across actual own query')
    before,after,sbefore,safter=[u(r,o,10) for o in (52,92,132,172)]
    need(before==INITIAL,'Actual complete initial CPU')
    s=list(before);s[4]-=4;s[9]=SERVICE;need(sbefore==tuple(s),'Actual compiled CALL service-entry full CPU/frame')
    if native:
        s[0]=BUFFER;s[4]=FRAME;s[9]=RETURN;need(safter==tuple(s),'Typed service representative full CPU return')
        s[9]=CAPTURE;need(after==tuple(s),'Full CPU through compiled MOV and authored capture')
    else:
        need(safter[0]==pointer and safter[4]==FRAME-4 and safter[9]==SERVICE and tuple(safter[i]for i in (3,5,6,7))==tuple(before[i]for i in (3,5,6,7)),'Actual service output/nonvolatiles and instrumented call extent')
        s=list(safter);s[4]+=4;s[9]=CAPTURE;need(after==tuple(s),'Complete writer output CPU derived from actual hardware service observation')
    need(u(r,55796,5)==(SERVICE,RETURN,FRAME-4,FRAME,1),'Actual complete CALL/stdcall0 return route')
    fx0,fx1=r[4588:5100],r[5100:5612];e0,e1=r[7660:7688],r[7688:7716]
    need(fx0==seed_fx(cw,top,native) and e0==seed_env(cw,top),'Independent whole raw80/empty allTOP/CW/FX/ENV seed model')
    if native:need(fx1==fx0 and e1==e0,'Complete representative software FP preservation')
    else:
        # No numerical x87 instruction occurs in the source; the observed actual
        # Windows call's independent snapshots establish this bounded result.
        need(fx0[:5]==fx1[:5] and fx0[24:]==fx1[24:] and e0==e1,'Observed original complete FP raw/metadata preservation')
    host_restore(r[5612:6124],r[6124:6636],r[7716:7744],r[7744:7772],native)
    if not native:
        need(r[6636:7148]==fx0 and r[7148:7660]==fx1 and r[7772:7800]==e0 and r[7800:7828]==e1,'Actual service before/after hardware FP captured independently')
    mb,ma=r[7828:28308],r[28308:48788]
    wanted=bytearray(b''.join(pages)+game.bytes(0x5bb000,4096)+b'\xa5'*4096)
    if not native:put(wanted,4096+0x34,SERVICE)
    put(wanted,4*4096+0x800,CAPTURE)
    need(mb==wanted,'Five complete original/native owned initial pages and raw IAT distinction')
    put(wanted,2*4096+0x174,guest);put(wanted,4*4096+0x7fc,RETURN)
    if not native:put(wanted,4*4096+0x7f8,inner_return)
    need(ma==wanted,'Five complete source-derived output pages including exact actual instrumented inner return')
    if native:
        s0=state_seed(cw,top,repeat);need(r[48788:52292]==s0,'Entire dirty 3504-byte native State entry model')
        s1=bytearray(s0);put(s1,GPR[0],BUFFER);put(s1,GPR[4],FRAME);put(s1,GPR[8],CAPTURE)
        need(r[52292:55796]==s1,'Complete State output/protected storage source model')
        need(state_project(s0)==(fx0,e0) and state_project(s1)==(fx1,e1),'Independent physical/logical FP projections of whole State')
        events=((WRITER,IAT,214062,4,0),(WRITER,FRAME-4,RETURN,4,1),(WRITER,FRAME-4,RETURN,4,0),(WRITER,BUFFER,0,len(owned),2),(RETURN,GLOBAL,BUFFER,4,1))
        need(tags[11]==5 and r[55816:56456]==b''.join(struct.pack('<5I',*e)for e in events)+bytes(540),'Five actual ordered compiled/adapter events with complete zero unused storage')
    else:need(tags[11]==0 and not any(r[48788:55796]) and not any(r[55816:]),'Original State/events explicitly unobserved, not invented')

class Context(tuple):pass

def parse(path,native):
    b=pathlib.Path(path).read_bytes();magic,version,count,size,pages,supplied_n,actual_n=struct.unpack_from('<8s6I',b)
    need(magic==(b'MW4CMNN1' if native else b'MW4CMNO1') and (version,count,size,pages)==(1,48,RECORD,5),'Independent packed record header')
    need(supplied_n<=131072 and 0<actual_n<=131072,'Serialized actual input bound')
    supplied=b[32:32+supplied_n];observed=b[32+supplied_n:32+supplied_n+actual_n];at=32+supplied_n+actual_n;rows=[]
    for i in range(count):
        r=b[at:at+RECORD];need(len(r)==RECORD,'Complete row');at+=RECORD;nr=u(r,32)[0];need(0<nr<=32,'Actual host region bound')
        regions=[struct.unpack_from('<3Q4I',b,at+40*j) for j in range(nr)];at+=40*nr;owned=b[at:at+actual_n];at+=actual_n;rows.append((r,regions,owned))
    need(at==len(b),'No trailing or missing actual records')
    return supplied,observed,rows

def main(out):
    need(not out.exists() and out.is_relative_to(BASE),'Fresh private independent raw report required')
    context=Context(source_contract());context.bindings={};capture=read(BASE/'capture-repaired-normal-r1/capture.json');files={};counts={'original':0,'native':0};controls=[];streams=[]
    for command in capture['commands']:
        native=command['kind']!='original';path=pathlib.Path(command['result']);need(command['exit']==0 and sha(command['executable'])==command['executable_sha256'],'Actual capture command/build association')
        supplied,observed,rows=parse(path,native)
        context.process_pointer=q(rows[0][0],212)
        need(supplied==command['supplied_logical_commandline'].encode('ascii'),'Supplied authored bytes are distinct provenance input')
        for i,(row,regions,owned) in enumerate(rows):row_check(row,regions,owned,observed,i,native,context)
        files[str(path)]=sha(path);files[command['executable']]=sha(command['executable']);streams.append({'path':str(path),'kind':command['kind'],'records':len(rows),'observed_sha256':hashlib.sha256(observed).hexdigest(),'logical_equal_observed':supplied+b'\0'==observed})
        counts['native' if native else 'original']+=len(rows)
        # Independent corruptions touch observation families and fail this source
        # model directly, without an author's comparator or expected calls.
        row,regions,owned=rows[0]
        offsets=[0,8,12,16,24,28,36,40,48,52,92,132,172,212,220,252,292,356,2404,4588,5100,5612,6124,7660,7688,7716,7744,7828,28308,55796]
        if native:offsets += [48788+x for x in (0,2065,2080,2090,2112,2168,2216,2737,2768,2792,3280,3503)]+[52292+x for x in (0,2168,2216,2472,2768,3280,3503)]+[55816+x for x in (0,4,8,12,16,20,60,80,100,639)]
        else:offsets += [48788,55816,28308+4*4096+0x7f8]
        for offset in offsets:
            changed=bytearray(row);changed[offset]^=1
            try:row_check(changed,regions,owned,observed,0,native,context)
            except (ValueError,struct.error,UnicodeError,KeyError,FileNotFoundError) as error:controls.append({'kind':command['kind'],'fixture':command['index'],'offset':offset,'rejected':True,'reason':str(error)});continue
            raise ValueError('Independent model accepted mutation '+str((command['kind'],offset)))
        for kind in ('owned-byte','region-coverage'):
            mutation=bytearray(owned);mutation[0]^=1;regions_changed=list(regions);regions_changed[0]=(regions[0][0]+0x100000,)+regions[0][1:]
            try:row_check(row,regions,mutation,observed,0,native,context) if kind=='owned-byte' else row_check(row,regions_changed,owned,observed,0,native,context)
            except ValueError as error:controls.append({'kind':command['kind'],'fixture':command['index'],'mutation':kind,'rejected':True,'reason':str(error)});continue
            raise ValueError('Accepted independent buffer/ownership mutation')
    need(counts=={'original':384,'native':768},'Complete actual accepted corpus extent')
    # Cross-process equality concerns source bytes, not host pointers or original
    # after-state as execution input. The policy-equivalent writer stores each
    # process's own strong guest address/native input bytes.
    for fixture in range(8):
        values=[parse(BASE/'capture-repaired-normal-r1'/f'{kind}-{fixture}.bin',kind!='original')[1] for kind in ('original','O0','O2')]
        need(values[0]==values[1]==values[2],'Actual independently supplied original/native OS string observations')
    files.update(context.bindings)
    for path in (context[0].path,context[1].path,context[4].path,context[5],BASE/'static-r1/pack.bin',BASE/'capture-repaired-normal-r1/capture.json',pathlib.Path(__file__).resolve(),ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/include/remill/Arch/X86/Runtime/State.h',ROOT/'tools/m4-crt/probe_common.hpp'):
        files[str(path)]=sha(path)
    out.mkdir();rp=out/'report.json';report={'passed':True,'scope':'Independent source/raw command-line writer and owning input model; source/build and compiled causal closure still pending',
          'actual_records':counts,'streams':streams,'observer_controls':controls,'actual_inner_instrumentation_CALL_return':context[3],
          'imported_primary_models':False,'full_native_State_bytes':3504,'whole_owned_pages':5,'actual_native_events':768*5,'source_instructions':2,
          'API_volatile_CPU_policy':'Original writer output is derived from complete measured service-after CPU; native preserves unspecified software State fields. No full GetCommandLineA implementation equivalence or ABI volatility restriction is invented.',
          'limitations':['Original software State and per-instruction events are not observed','Current on-disk API export/module association is checked, including x86 System32 redirection; arbitrary loaded hotpatching is not admitted',
                         'Eight ASCII inputs, empty TOP0/7 and twelve masked CWs only; no complete DllMain/process attach/startup/menu','Independent compiled causal/build closure pending'],
          'whole_M4_complete':False}
    rp.write_text(json.dumps(report,indent=2)+'\n');files[str(rp)]=sha(rp);pp=out/'pins.json';pp.write_text(json.dumps({'files':dict(sorted(files.items()))},indent=2)+'\n')
    print('Independent raw command-line source model passed',counts,len(controls),'mutations',sha(rp),sha(pp))

if __name__=='__main__':main(pathlib.Path(sys.argv[1]).resolve())
