"""Independent raw native projection review; no author observer imports.

This intermediate raw pass requires a separate immutable build/identity and
compiled causal closure before game-control integration acceptance.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import traceback

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];GATE=ROOT/'reports/m4-crt-control-integration';PINS={}

def need(ok,why):
    if not ok:raise ValueError(why)

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def bind(p,h=None):
    p=Path(p).resolve();got=sha(p);need(h is None or got==h,'Exact native-model identity '+str(p))
    need(str(p) not in PINS or PINS[str(p)]==got,'Conflicting native-model identity');PINS[str(p)]=got;return p

def u32(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def put(b,o,v,n=4):b[o:o+n]=v.to_bytes(n,'little')
original_pins=json.loads(bind(GATE/'independent-original-model-r1/pins.json','2b939c9c10246918deb349d00e20a44c7022c981d71f9200efcd7959abd689fe').read_text())
model_path=bind(ROOT/'tools/m4-crt-control-integration-independent/original_model.py',original_pins['files'][str(ROOT/'tools/m4-crt-control-integration-independent/original_model.py')])
spec=importlib.util.spec_from_file_location('own_root_connected_original_model',model_path);ORIGINAL=importlib.util.module_from_spec(spec);spec.loader.exec_module(ORIGINAL)

def initial_state(original,index):
    state=bytearray((i*13+index+7)&255 for i in range(3504));cpu=u32(original,12,10)
    for at,v in ((2120,0),(2168,0x7ffde000),(2184,0)):put(state,at,v)
    for at,v in zip((2216,2248,2264,2232,2312,2328,2280,2296,2472),cpu[:8]+(cpu[9],)):put(state,at,v)
    put(state,2080,cpu[8],8)
    for at,bit in ((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11)):state[at]=(cpu[8]>>bit)&1
    state[2736:2760]=bytes(24);state[2768:3280]=original[92:604];env=original[2140:2168]
    for at,offset,n in ((2774,18,2),(2776,12,4),(2780,16,2),(2784,20,4),(2788,24,2)):state[at:at+n]=env[offset:offset+n]
    for i in range(8):
        state[2486+i*16:2496+i*16]=original[124+i*16:134+i*16];state[16+i*64:32+i*64]=original[252+i*16:268+i*16]
    return state

def observe(original,native,index,program,raw_iat):
    model=ORIGINAL.observe(original,index,program);after,stack,cw,provider_events,_=model;after=list(after);after[9]=0x5ac436
    need(len(native)==17764 and native[:52]==original[:52],'Full native tag and original before-only CPU')
    need(u32(native,52,10)==tuple(after),'Native complete exit CPU/defined ADD flags and actual outer PC')
    need(native[92:1116]==original[92:1116] and native[1116:1172]==original[2140:2196],'Complete native FX512/separate legacy ENV28 projections')
    state=initial_state(original,index);need(native[1172:4676]==state,'Independent entire seeded3504 connected State')
    for at,v in zip((2216,2248,2264,2232,2312,2328,2280,2296,2472),after[:8]+[after[9]]):put(state,at,v)
    for at,bit in ((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11)):state[at]=(after[8]>>bit)&1
    put(state,2768,cw,2);need(native[4676:8180]==state,'Independent entire projected/protected3504 connected State')
    need(native[8180:12276]==original[2252:6348] and native[12276:16372]==stack,'Full native4096 input/source-derived result stack')
    sp=u32(original,12+16)[0]
    events=((1,0x5ac5a0,sp,0x5ac436),(3,0x5ac5d6,sp-12,0x5ac5af),(4,raw_iat,sp-12,0x5ac5af),
        *provider_events,(5,0x5ac5af,sp-8,0x5ac5af),(2,0x5ac436,sp+4,0x5ac436))
    need(len(events)==13 and u32(native,16372)[0]==13,'Actual13 source/supervisor phases')
    encoded=b''.join(struct.pack('<4I',*event) for event in events)
    need(native[16376:16632]==encoded+bytes(256-len(encoded)),'Exact provider/frame/import-tail phase log and zero unused entries')
    need(native[16632:17144]==native[17144:17656] and native[17656:17684]==native[17684:17712],'Complete native actual host FX512/ENV28 restoration')
    need(u32(native,17712)[0]==2,'Exactly two completed r9 records')
    records=struct.pack('<12I',0x5ac431,0x5ac5a0,0x5ac436,0,1,0,0x5ac5aa,0x5bb578,0x5ac5af,1,1,1)
    need(native[17716:17764]==records,'Real admitted outer and typed import r9 records')
    return len(events)

def main(out):
    need(not out.exists() and out.is_relative_to(GATE),'Fresh private connected native raw model')
    out.mkdir(parents=True);(out/'model-source.py').write_bytes(Path(__file__).read_bytes());bind(out/'model-source.py')
    try:
        program,_=ORIGINAL.CRT.decode(out);op=bind(GATE/'original-normal-windows-r2/original.bin','4dfcd09eac41e6323150701e2cf85693719eb397aecfb81b0a4962fe31adfabf');original=op.read_bytes()
        game=bind(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes()
        pe=u32(game,0x3c)[0];raw_iat=None
        for i in range(struct.unpack_from('<H',game,pe+6)[0]):
            at=pe+24+struct.unpack_from('<H',game,pe+20)[0]+40*i;vs,rva,rs,ro=u32(game,at+8,4)
            if rva<=0x1bb578<rva+rs:raw_iat=u32(game,ro+0x1bb578-rva)[0]
        need(raw_iat==1961354,'Independently read original raw game control IAT DWORD')
        levels=[];controls=[]
        for level,h in (('O0','4d65ee1fc03b41128d8ff37d090b9c08822c775df07703fe4a7fd0a91fe9aaf9'),('O2','9712a6d436765160a76c632db1cf71fce0da542d653d3a30bb1735b3fb5eeb74')):
            path=bind(GATE/f'native-run-r1/native-{level}.bin',h);native=path.read_bytes()
            need(native[:8]==b'MW4CIN01' and u32(native,8,4)==(1,192,17764,3504) and len(native)==3410712,'Complete native header/final extent')
            count=0
            for i in range(192):count+=observe(original[24+i*10444:24+(i+1)*10444],native[24+i*17764:24+(i+1)*17764],i,program,raw_iat)
            row=native[24:24+17764];o=original[24:24+10444]
            for offset in (0,12,44,52,68,84,88,92,604,606,608,636,764,1116,1144,1172,1172+3400,1172+2168,4676,4676+2472,4676+2768,4676+3400,4676+2486,4676+16,8180,12276,12276+0xf4,16372,16376,16380,16384,16388,16376+12*16,16632,17144,17656,17684,17712,17716,17720,17724,17728,17732,17736,17740,17744,17748,17752,17756,17760):
                changed=bytearray(row);changed[offset]^=1
                try:observe(o,changed,0,program,raw_iat)
                except (ValueError,struct.error) as e:controls.append({'level':level,'offset':offset,'rejected':True,'diagnostic':str(e)})
                else:raise ValueError('Independent native observer accepted corruption '+str(offset))
            levels.append({'level':level,'records':192,'phase_events':count,'r9_records':384,'passed':True})
        PINS.update(ORIGINAL.PINS);PINS.update(ORIGINAL.CRT.PINS)
        report={'passed':True,'scope':'Independent complete raw connected control original/native projection; immutable build/identity and compiled causal review still required before acceptance',
            'levels':levels,'native_records':384,'observer_controls':controls,'raw_native_IAT':raw_iat,'whole_M4_complete':False,
            'instrumentation':'Only original final capture PC10000100 projects to actual native return5AC436. Tail r9 convention rewrites the same existing5AC5AF word at the same address; no additional original guest CALL is claimed.',
            'shared_context_scope':'Persistent admitted r9 CPU/FX/State/memory across wrapper and complete provider, serial trusted Context. Following numerical callbacks and full CRT are unexecuted.'}
        p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');bind(p);bind(Path(__file__))
        (out/'pins.json').write_text(json.dumps({'files':dict(sorted(PINS.items()))},indent=2)+'\n')
        print(json.dumps({'passed':True,'native_records':384,'controls':len(controls),'report_sha256':sha(p),'pins_sha256':sha(out/'pins.json')}))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
