"""Root independent offline paired native matherr CPU/State/access model.

Only the frozen root original model is imported. Whole native State derives
from original BEFORE fields and the four actual instructions/IR AF policy.
"""
import hashlib, importlib.util, json, struct, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-matherr';PINS={}
OS=26836;NS=33964;CPU=struct.Struct('<10I');GPR=(2216,2248,2264,2232,2312,2328,2280,2296)
AF=((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11))
SF=((2737,8),(2739,9),(2741,10),(2743,14),(2745,5),(2747,4),(2749,3),(2751,2),(2753,1),(2755,0),(2757,6))

def need(ok,why):
    if not ok:raise ValueError(why)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,want=None):
    p=Path(p).resolve();got=sha(p);need(want is None or got==want,'Frozen paired native identity '+str(p));need(str(p) not in PINS or PINS[str(p)]==got,'Conflicting identity');PINS[str(p)]=got;return p
def read(p):return json.loads(pin(p).read_text(encoding='utf-8-sig'))
def put(b,o,v,size=4):b[o:o+size]=v.to_bytes(size,'little')
def words(b,o,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def statecpu(s,c,flat):
    for off,val in zip(GPR,c[:8]):put(s,off,val)
    put(s,2472,c[9])
    if flat:put(s,2080,c[8],8)
    for off,bit in AF:s[off]=(c[8]>>bit)&1
def initial_state(o,index):
    s=bytearray((j*13+index+7)&255 for j in range(3504));s[2768:3280]=o[100:612]
    for off,source,size in ((2774,2166,2),(2776,2160,4),(2780,2164,2),(2784,2168,4),(2788,2172,2)):s[off:off+size]=o[source:source+size]
    sw=struct.unpack_from('<H',o,102)[0]
    for off,bit in SF:s[off]=(sw>>bit)&1
    for j in range(8):s[2486+j*16:2496+j*16]=o[132+j*16:142+j*16];s[16+j*64:32+j*64]=o[260+j*16:276+j*16]
    for off,val in ((2120,0),(2184,0),(2168,0x7ffde000)):put(s,off,val)
    statecpu(s,CPU.unpack_from(o,20),True);return s
def cpu_projection(s):
    flags=words(s,2080)[0]&~0xcd5
    for off,bit in AF:need(s[off] in (0,1),'Actual native flag boolean');flags|=s[off]<<bit
    return tuple(words(s,off)[0] for off in GPR)+(flags,words(s,2472)[0])
def observe(o,n,index,original):
    original.observe(o,index);need(len(n)==NS and n[:60]==o[:60],'Whole native framing/tags/original BEFORE CPU')
    cpu=list(CPU.unpack_from(o,20));arg=words(o,8)[0];cpu[0]=arg;cpu[4]=original.FRAME+4;cpu[8]=(cpu[8]&~0x8d5)|0x44;cpu[9]=original.RETURN
    need(CPU.unpack_from(n,60)==tuple(cpu),'Complete native CPU including fixed native AND-AF0 and actual RET')
    need(n[100:1124]==o[100:1124] and n[2148:2204]==o[2148:2204],'Whole native actual RuntimeFX and serialized legacy ENV match original hardware observation')
    need(n[1124:1636]==n[1636:2148] and n[2204:2232]==n[2232:2260],'Complete native actual host FX512/XMM0..15/ENV28 restoration')
    need(n[2260:26836]==o[2260:26836],'All three whole native pages match original instruction writes')
    sb=initial_state(o,index);need(n[26836:30340]==sb,'Entire3504 native input State from original BEFORE-only fields')
    sa=bytearray(sb);statecpu(sa,cpu,False);need(n[30340:33844]==sa,'Entire3504 native source/IR-derived result State and protected remainder')
    need(cpu_projection(sb)==CPU.unpack_from(n,20) and cpu_projection(sa)==tuple(cpu),'Native full State CPU/flags projection')
    # Native ENV-after is serialized from input, not separately measured guest
    # hardware. Actual whole-State equality proves the legacy metadata carry.
    for off,size in ((2736,24),(2768,512),(2480,128),(16,16)):
        need(sb[off:off+size]==sa[off:off+size],'Actual State FP/status/metadata/storage preserved')
    zero_before=words(o,2260+4096+0x2b8)[0]
    events=((original.FRAME+4,arg,4,0),(0x780392b8,zero_before,4,0),(0x780392b8,0,4,1),(0x7803b0c4,arg,4,1),(original.FRAME,original.RETURN,4,0))
    need(n[33844:33924]==b''.join(struct.pack('<4I',*e) for e in events),'All five actual compiled ordered read/write/RET events')
    need(words(n,33924,6)==(0x5ac428,0x5bb50c,original.RETURN,1,1,0),'Actual completed r9 named service route')
    need(words(n,33948,4)==(5,1,1,0),'Complete first-use five-event context closure')

def main(out):
    need(out.is_relative_to(BASE) and not out.exists(),'Fresh paired native independent output required')
    out.mkdir(parents=True);(out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py')
    try:
        path=ROOT/'tools/m4-crt-matherr-independent/original_model_safe.py';spec=importlib.util.spec_from_file_location('own_root_matherr_original_safe',pin(path,'432b687488372b857e08f169fa269b2acca9106a9e7f0c03eee5a7f639780e9b'));original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
        pin(BASE/'independent-original-model-r1/report.json','ba5941592ed4158a59a3e07a808a4244f1eafc7e3769e71b7b8e4515322a53e4')
        raw=pin(BASE/'paired-original-r1-normal-windows/original.bin','50adc9316afe26f0deb78cac3aeb737bc5c0810324897031c3bd548fec30c472').read_bytes()
        build=read(BASE/'paired-native-build-r7/build.json');need(build['passed'],'Actual native positive build')
        levels=[];controls=[]
        for level in ('O0','O2'):
            path=BASE/f'paired-native-build-r7/native-{level}.bin';native=pin(path,build['artifacts'][str(path)]).read_bytes()
            need(struct.unpack_from('<8s4I',native)==(b'MW4MPN01',1,1536,NS,3504) and len(native)==24+1536*NS,'Complete1536 native stream')
            for index in range(1536):observe(raw[24+index*OS:24+(index+1)*OS],native[24+index*NS:24+(index+1)*NS],index,original)
            for index in (0,1,4,63):
                o=raw[24+index*OS:24+(index+1)*OS];n=native[24+index*NS:24+(index+1)*NS]
                offsets=[0,20,52,60,76,92,96,100,612,614,616,644,1636,1636+400,2204,2232,2260,14548,14548+4096+0x2b8,14548+8192+0xc4,26836+3433,30340+3433,30340+2168,30340+2220,30340+2472,30340+2069,30340+2774,30340+2776,30340+2784,30340+2796,30340+2755,33844,33848,33852,33856,33844+16,33844+32,33844+48,33844+64,33924,33928,33932,33936,33940,33944,33948,33952,33956,33960]
                for j in range(8):offsets.extend((30340+2486+j*16,30340+2486+j*16+10,30340+16+j*64,30340+2800+j*16))
                for off in offsets:
                    b=bytearray(n);b[off]^=1
                    try:observe(o,bytes(b),index,original)
                    except (ValueError,struct.error) as ex:controls.append(dict(level=level,index=index,offset=off,rejected=True,reason=str(ex)))
                    else:raise ValueError('Native observer accepted corruption '+str((index,off)))
                b=bytearray(o);b[92]^=0x10;observe(bytes(b),n,index,original)
                controls.append(dict(level=level,index=index,case='original_AF_change_does_not_supply_native_AF',rejected=False,accepted=True))
            levels.append(dict(level=level,records=1536,events=7680,r9_routes=1536,passed=True))
        report=dict(passed=True,scope='Independent full native matherr source/State/event/route differential model; source/build/compiled causal closure remains required',original_records=1536,native_records=3072,levels=levels,independent_observer_controls=controls,original_or_native_executed_by_reviewer=False,primary_comparator_or_executor_imported=False,native_state_AF_from_original_output=False,callback_invoked=False,full_M4_complete=False,limitations=['Native ENV before/after fields are input serialization, not independently measured guest hardware; actual whole3504State separately proves legacy/status/raw80 preservation. Native RuntimeFX-after and hostFX/ENV are actual captured storage.','The static game CALL site is an authored r9 orchestration site here; exact same return word is repushed into its already authored frame. Full original CRT caller/PUSH/CALL and callback target remain unexecuted.','Fresh serial fixture contexts; no persistent multi-service/CRT composition or full startup/menu credit.','Original AF is undefined; native actualIR chooses0 and wholeState/CPU expected value is derived only from source/BEFORE input.'])
        rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');pin(rp);pin(Path(__file__))
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,native_records=3072,controls=len(controls),report_sha256=sha(rp),pins_sha256=sha(out/'pins.json'))))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
