"""Bounded caller/query observer. No original after data is used by a worker.

The full original volatile register/vector observations are retained. Cross-
implementation equality is required only for the reached caller's defined
outputs. Native representative-policy State is checked byte for byte separately.
"""
from pathlib import Path
import collections, hashlib, json, struct, sys, traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-spi-workarea'
SIZE = 36360
FRAME, OBJECT, OUTPUT = 0x20001800, 0x608f88, 0x608fa0
ENTRY, BROKER, CALL, RESUME, IAT = 0x482cf0, 0x482ff0, 0x482cdd, 0x482ce3, 0x5bb6dc
CW = (0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f)
GPR = (2216,2248,2264,2232,2312,2328,2280,2296)
AF = ((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def require(ok, why):
    if not ok: raise AssertionError(why)
def words(b,o,n): return struct.unpack_from('<'+'I'*n,b,o)
def put(b,o,v): struct.pack_into('<I',b,o,v & 0xffffffff)
def cpu(b,o): return words(b,o,10)
def equal(a,b,why):
    if a != b:
        if isinstance(a,(bytes,bytearray)) and len(a)==len(b):
            first = next(i for i,(x,y) in enumerate(zip(a,b)) if x!=y)
            why += f' (first byte {first})'
        raise AssertionError(why)
def initial(v):
    return (0x13579bdf+v,0x2468ace0+v,0x81726354+v,0x10293847+v,FRAME,0x92837465+v,0x56473829+v,0xaabbccdd+v,(0x202,0xad7,0x293)[v],ENTRY)
def initialfx(cw,top,v):
    b=bytearray(512);struct.pack_into('<HH',b,0,cw,top<<11);put(b,24,0x1f80)
    b[160:288]=bytes((i*13+v*17)&255 for i in range(128));return b
def env(cw,top): return struct.pack('<7I',0xffff0000|cw,0xffff0000|(top<<11),0xffffffff,0,0,0,0xffff0000)
def state_seed(cw,top,v,repeat):
    b=bytearray((i*29+cw+v*91+repeat*3571+(i>>8)*7)&255 for i in range(3504))
    b[2112:2208]=bytes(96);put(b,2168,0x7ffde000)
    for o in (2090,2094,2106): struct.pack_into('<H',b,o,0x2b)
    struct.pack_into('<H',b,2110,0x23)
    b[2768:3280]=initialfx(cw,top,v)
    for i in range(8):
        b[2486+16*i:2496+16*i]=bytes(10)
        b[16+64*i:32+64*i]=b[2928+16*i:2944+16*i]
    for o in (2737,2739,2741,2743,2745,2747,2749,2751,2753,2755,2757): b[o]=0
    c=initial(v)
    for o,value in zip(GPR,c[:8]): put(b,o,value)
    put(b,2472,c[9]);struct.pack_into('<Q',b,2080,c[8])
    for o,bit in AF: b[o]=(c[8]>>bit)&1
    return b
def state_after(cw,top,v,repeat):
    b=state_seed(cw,top,v,repeat);put(b,GPR[0],OBJECT);put(b,GPR[1],0);put(b,GPR[4],FRAME+4);put(b,2472,BROKER);return b
def memory_seed(source,v):
    b=bytearray(source)
    b+=bytes(4096) if v==0 else bytes((i*37+v*71+(i>>8)*5)&255 for i in range(4096))
    b+=bytes([0xa5])*4096;put(b,8192+FRAME-0x20001000,BROKER);return b
def event_model(source,rect,v):
    c=initial(v);events=[]
    def add(pc,a,val,op):events.append((pc,a,val,4,op))
    for pc,delta,val in ((0x482cc0,4,c[3]),(0x482cc3,8,c[6]),(0x482cc4,12,c[7]),(0x482cc8,16,0),(0x482cd6,20,OUTPUT),(0x482cd7,24,0),(0x482cd9,28,0x30)):
        add(pc,FRAME-delta,val,1)
    for i in range(6):
        val=words(source,i*4,1)[0];add(0x482cdb,0x5e6000+i*4,val,0);add(0x482cdb,OBJECT+i*4,val,1)
    add(CALL,FRAME-32,RESUME,1);add(CALL,IAT,0x1df20c,0)
    for i,val in enumerate((RESUME,0x30,0,OUTPUT,0)): add(CALL,FRAME-32+i*4,val,0)
    for i,val in enumerate(words(rect,0,4)): add(CALL,OUTPUT+i*4,val,1)
    for pc,delta,val in ((RESUME,12,c[7]),(0x482ce6,8,c[6]),(0x482ce7,4,c[3]),(0x482ce8,0,BROKER)):
        add(pc,FRAME-delta,val,0)
    require(len(events)==34,'Independent event model length');return events
def memory_after(source,rect,v):
    b=memory_seed(source,v)
    for pc,a,val,width,op in event_model(source,rect,v):
        if not op:continue
        if OBJECT<=a<OBJECT+40: o=4096+a-0x608000
        else:o=8192+a-0x20001000
        put(b,o,val)
    return b
def host_check(b,native):
    x,y=b[1140:1652],b[1652:2164]
    equal(x[:5],y[:5],'Host CW/SW/tag restoration')
    equal(x[24:28],y[24:28],'Host MXCSR restoration')
    for i in range(8):equal(x[32+16*i:42+16*i],y[32+16*i:42+16*i],'Host raw80 restoration')
    equal(x[160:160+(256 if native else 128)],y[160:160+(256 if native else 128)],'Host vector restoration')
    equal(b[2220:2248],b[2248:2276],'Host legacy ENV restoration')
def fx_env_check(fx,e,why):
    equal(fx[:4],e[:2]+e[4:6],why+' CW/SW representation')
def validate(b,index,native,source):
    require(len(b)==SIZE,'Record extent')
    repeat=(index//72);cw=CW[(index%72)//6];top=(0,7)[(index%6)//3];v=index%3
    equal(words(b,0,9),(index,repeat,cw,top,v,0,1,int(native),0x2f9),'Tag/case/domain/completion metadata')
    equal(cpu(b,36),initial(v),'Actual caller initial CPU')
    host_check(b,native)
    equal(b[2276:14564],memory_seed(source,v),'Whole initial pages')
    called,result,cleanup,physical_before,physical_after=words(b,35052,5)
    equal((called,cleanup),(1,16),'Actual one-query/stdcall contract')
    equal(words(b,35072,2),(34 if native else 0,1),'Events/completion contract')
    rect_before=b[35020:35036];rect=b[35036:35052]
    equal(rect_before,b[2276+4096+OUTPUT-0x608000:2276+4096+OUTPUT-0x608000+16],'RECT initial ownership')
    equal(b[14564:26852],memory_after(source,rect,v),'Whole final pages / actual RECT transport')
    c=list(initial(v));c[0]=OUTPUT;c[1]=0;c[3]=OBJECT;c[4]=FRAME-32;c[6]=0x5e6018;c[7]=OUTPUT;c[9]=CALL
    equal(cpu(b,33860),tuple(c),'Service actual incoming guest CPU')
    expected=list(c);expected[0]=result;expected[4]=FRAME-12;expected[9]=RESUME
    got=cpu(b,33900)
    for i in (0,3,4,5,6,7,9):equal(got[i],expected[i],'Service defined register/continuation')
    require(not(got[8]&0x400),'Service DF required clear')
    expected=list(initial(v));expected[0]=OBJECT;expected[4]=FRAME+4;expected[9]=BROKER
    if native:
        expected[1]=0
        equal(got,tuple(c[:0])+tuple([result,0,c[2],OBJECT,FRAME-12,c[5],0x5e6018,OUTPUT,c[8],RESUME]),'Native service representative CPU policy')
        equal((physical_before,physical_after),(0,0),'Native x86-provider stack fields unobserved')
        equal(b[26852:30356],state_seed(cw,top,v,repeat),'Full native3504 seeded State')
        equal(b[30356:33860],state_after(cw,top,v,repeat),'Full native3504 final State policy/opaque bytes')
        equal(b[116:628],initialfx(cw,top,v),'Native software FX before projection')
        equal(b[628:1140],initialfx(cw,top,v),'Native software FX after representative policy')
        for o in (2164,2192):equal(b[o:o+28],env(cw,top),'Native legacy ENV projection')
        events=[words(b,35080+i*20,5) for i in range(34)]
        equal(events,event_model(source,rect,v),'Actual ordered native memory events')
        equal(b[35080+34*20:],bytes(30*20),'Unused event storage')
    else:
        require(physical_before>0 and physical_after==physical_before+20,'Actual physical provider stdcall16 stack advance')
        expected[1]=got[1];expected[2]=got[2];expected[8]=got[8]
        equal(b[26852:33860],bytes(7008),'Original software State unobserved')
        equal(b[35080:],bytes(64*20),'Original events unobserved')
        f=initialfx(cw,top,v);f[28:32]=b[144:148]
        require(words(f,28,1)[0]!=0,'Actual original hardware MXCSR-mask observation')
        equal(b[116:628],f,'Original full hardware FX input observation')
        # All128 vector bytes remain actual observations, not cross-ABI outputs.
        equal(b[628:788],b[116:276],'Original observed non-vector FX unchanged')
        equal(b[916:1140],b[404:628],'Original observed FX reserved tail unchanged')
        for o in (2164,2192):equal(b[o:o+28],env(cw,top),'Original actual legacy ENV unchanged')
        equal(b[33940:34452],b[116:628],'Original provider incoming hardware FX')
        equal(b[34452:34964],b[628:1140],'Original provider returned hardware FX carried to caller')
        equal(b[34964:34992],b[2164:2192],'Original provider incoming actual legacy ENV')
        equal(b[34992:35020],b[2192:2220],'Original provider returned actual legacy ENV')
    equal(cpu(b,76),tuple(expected),'Actual final caller CPU / service volatility carry')
    for fx_off,env_off in ((33940,34964),(34452,34992)):
        fx_env_check(b[fx_off:fx_off+512],b[env_off:env_off+28],'Actual provider FP/ENV')
    return dict(result=result,rect=rect,variant=v,cw=cw,top=top)
def pair(original,native,index,source):
    a=validate(original,index,False,source);b=validate(native,index,True,source)
    equal((a['result'],a['rect']),(b['result'],b['rect']),'Same-environment actual query result/RECT')
    oc,nc=cpu(original,76),cpu(native,76)
    for i in (0,3,4,5,6,7,9):equal(oc[i],nc[i],'Cross-implementation defined caller CPU')
    equal(oc[8]&0x400,nc[8]&0x400,'Cross-implementation defined DF')
    equal(original[14564:26852],native[14564:26852],'Cross-implementation whole final pages')
    equal(original[2192:2220],native[2192:2220],'Observed unchanged x87 legacy ENV')
    return b
def stream(path,native):
    b=Path(path).read_bytes();equal(b[:8],b'MW4SPIN1' if native else b'MW4SPIO1','Stream magic')
    equal(words(b,8,4),(1,144,SIZE,3),'Stream framing');require(len(b)==24+144*SIZE,'Whole stream extent')
    return [b[24+i*SIZE:24+(i+1)*SIZE] for i in range(144)]
def controls(original,native,source):
    results=[]
    def reject(label,which,offset,bit=1,index=0):
        o=bytearray(original[index]);n=bytearray(native[index]);target=n if which=='native' else o;target[offset]^=bit
        try:pair(o,n,index,source)
        except AssertionError as e:results.append(dict(label=label,rejected=True,reason=str(e)));return
        raise AssertionError('Causal corruption accepted: '+label)
    for which in ('original','native'):
        for label,offset in (('initialCPU',36),('definedEAX',76),('nonvolatileEBX',88),('returnESP',92),('returnPC',112),('DF',109),('sourcePage',2276),('unrelatedObjectByte',14564+4096),('RECTTransport',14564+4096+OUTPUT-0x608000),('stackReturnWord',14564+8192+FRAME-0x20001000),('RECTOwnership',35020),('queryBOOL',35056),('cleanup16',35060),('serviceReturnPC',33936),('hostMXCSR',1652+24),('hostENV',2248),('completion',35076)):
            reject(which+'-'+label,which,offset,4 if label=='DF' else 1)
    for label,offset in (('opaqueState',30356+7),('upperGPR',30356+2220),('softwareVector',30356+16),('softwareCW',30356+2768),('softwareStatus',30356+2737),('flatFlags',30356+2080),('eventIATOwner',35080+20*20+4),('eventQueryArg',35080+22*20+8),('eventRECTWrite',35080+26*20+8),('eventOrder',35080),('unusedEvent',35080+34*20),('queryHostCWRepresentation',34992),('policyECX',80),('policyFlags',108),('eventCount',35072)):
        reject('native-'+label,'native',offset)
    reject('original-physicalStackAdvance','original',35068)
    reject('original-volatileCarry','original',80)
    reject('original-vectorCarry','original',628+160)
    positives=[]
    for label,fields in (('ECX',((33904,4),(80,4))),('EDX',((33908,4),(84,4))),('arithmeticFlag',((33932,0x40),(108,0x40)))):
        o=bytearray(original[0]);
        for offset,bit in fields:o[offset]^=bit
        pair(o,native[0],0,source);positives.append(label+' synchronized original volatility remains ABI-unspecified')
    o=bytearray(original[0]);o[628+160]^=1;o[34452+160]^=1
    pair(o,native[0],0,source);positives.append('Synchronized original SIMD observation remains unconsumed')
    return dict(rejected=len(results),negative=results,positive=len(positives),positive_cases=positives)
def main(build_path,capture_path,out):
    out=Path(out).resolve();out.relative_to(BASE);out.mkdir(parents=True,exist_ok=False)
    Path(out/'compare.py').write_bytes(Path(__file__).read_bytes())
    bindings={}
    def bind(p,h=None):
        p=Path(p).resolve();got=sha(p);require(h is None or got==h,'Input binding mismatch '+str(p));bindings[str(p)]=got
    try:
        build=json.loads(Path(build_path).read_text());capture=json.loads(Path(capture_path).read_text())
        require(build['passed'] and capture['passed'],'Passing input builds/capture required')
        bind(build_path,capture['build_sha256']);bind(capture_path)
        for group in ('sources','tools','artifacts'):
            for p,h in build[group].items():bind(p,h)
        for p,h in capture['artifacts'].items():bind(p,h)
        pack=Path(build['extraction'])/'pack.bin';bind(pack)
        pb=pack.read_bytes();equal(pb[:12],b'MW4SPIP1'+struct.pack('<I',5),'Private sparse pack framing')
        equal(words(pb,12+2*4104,2),(0x5e6000,0),'Read-only original template page')
        source=pb[12+2*4104+8:12+2*4104+4104]
        folder=Path(capture_path).parent;o=stream(folder/'original.bin',False)
        comparisons=collections.Counter();observed=collections.Counter();outputs=collections.Counter();native_records={}
        for level in ('O0','O2'):
            ns=stream(folder/(level+'.bin'),True);native_records[level]=ns
            for i,(a,b) in enumerate(zip(o,ns)):
                d=pair(a,b,i,source);comparisons['pairs']+=1;comparisons['native_events']+=34;comparisons['State_bytes']+=7008;comparisons['whole_page_bytes']+=24576
                outputs[str(struct.unpack('<4i',d['rect']))]+=1
        for b in o:
            for field,index in (('ECX',1),('EDX',2),('flags',8)):
                if cpu(b,76)[index]!=cpu(native_records['O0'][b[0]],76)[index]:observed[field+'_different']+=1
            for i in range(8):
                if b[116+160+i*16:116+176+i*16]!=b[628+160+i*16:628+176+i*16]:observed['XMM'+str(i)+'_changed']+=1
            observed['actual_BOOL_'+str(words(b,35056,1)[0])]+=1
        observers={level:controls(o,ns,source) for level,ns in native_records.items()}
        bind(__file__);bind(out/'compare.py')
        report=dict(passed=True,scope='Separate22-instruction hand-translated initializer and exact read-only host query; no connected startup/Remill/provider replacement credit',original=144,native=288,checks=dict(comparisons),observed_only=dict(observed),actual_environment_RECT_observations=dict(outputs),observer_controls=observers,defined_CPU='EAX/EBX/ESP/EBP/ESI/EDI/continuation, DF0; full original volatile values and original SIMD preserved as observations only',original_unobserved=['software State3504','per-access events'],native_policy='ECX0/EDXincoming/arithmetic flags/guest softwareFP/SIMD preserved; policy full3504 State checked separately, original after records never consumed by workers',transport='Actual x86 provider executes on real Windows stack; both physical ESP observations prove RET16; logical guest ESP is explicit transport projection',limits=['Actual query success cases only; no observed BOOLfalse route','Only12maskedCW and emptyTOP0/7 input fixtures','Native guestFP software projection is distinct from physical host-query FX/ENV snapshots','Current USER32 disk file identity checked after load; no complete Windows module execution-time closure','Environment-dependent RECT equality only for captured stable desktop','No original provider on synthetic guest-stack acceptance','Sequential ordinary private output paths; no concurrent publisher/reparse guarantee'],bindings=bindings)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,original=144,native=288,observers={k:v['rejected'] for k,v in observers.items()},report_sha256=sha(out/'report.json'))))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());(out/'bindings.json').write_text(json.dumps(bindings,indent=2)+'\n');raise
if __name__=='__main__':main(*sys.argv[1:])
