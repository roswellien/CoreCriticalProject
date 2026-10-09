"""Root independent carry model. Only frozen root review code is imported.

Original numerical outputs are measured hardware observations. This stage
models the complete native State, access events, frames and carry; separate
source/build/compiled causal closure remains necessary for acceptance.
"""
import collections, hashlib, importlib.util, json, struct, sys, traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-control-carry'
PINS={};CPU=struct.Struct('<10I');OS=92388;NS=104808
FRAME=0x20001800;CAP=0x410a80
RFX0=103468;RFX1=103980;CECOUNT=104492;CE=104496;RCOUNT=104752;ROUTE=104756;INITIAL=104804
ENT=(0x5ac5a0,0x410910,0x410940,0x4133c0,0x43aec0,0x43aee0,0x43af00,
     0x43af20,0x43af40,0x43af60,0x43af80,0x43afa0,0x467490,0x4674b0,
     0x4674d0,0x4adb50,0x4b5af0,0x4b5b20,0x4b7020,0x4c78f0,0x4c7940,
     0x4c79d0,0x4ce5a0,0x4ce5c0,0x4ce5e0,0x4ce600,0x4cfef0)
CWS=(0x7f,0x47f,0x87f,0xc7f,0x27f,0x67f,0xa7f,0xe7f,0x37f,0x77f,0xb7f,0xf7f)
COUNTS=collections.Counter();CONTROLS=[]

def need(ok,why):
    if not ok:raise ValueError(why)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,want=None):
    p=Path(p).resolve();got=sha(p)
    need(want is None or got==want,'Frozen identity '+str(p))
    need(str(p) not in PINS or PINS[str(p)]==got,'Conflicting identity')
    PINS[str(p)]=got;return p
def read(p):return json.loads(pin(p).read_text(encoding='utf-8-sig'))
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def load(name,path,want):
    spec=importlib.util.spec_from_file_location(name,pin(path,want));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def absorb(m):
    for p,h in m.PINS.items():pin(p,h['sha256'] if isinstance(h,dict) else h)
def initial_state(o,sequence,m):
    s=bytearray((i*13+sequence+7)&255 for i in range(3504));cpu=CPU.unpack_from(o,36)
    for off,val in ((2120,0),(2168,0x7ffde000),(2184,0)):m.put32(s,off,val)
    m.statecpu(s,cpu);s[2736:2760]=bytes(24);s[2768:3280]=o[116:628]
    env=o[2164:2192]
    for off,src,size in ((2774,18,2),(2776,12,4),(2780,16,2),(2784,20,4),(2788,24,2)):s[off:off+size]=env[src:src+size]
    for off,val in ((2090,0x2b),(2106,0x2b),(2110,0x23)):m.put16(s,off,val)
    for i in range(8):s[2486+i*16:2496+i*16]=o[148+i*16:158+i*16];s[16+i*64:32+i*64]=o[276+i*16:292+i*16]
    return s
def state_cpu(s,m):
    flags=m.u32(s,2080)&~0xcd5
    for bit,off in m.AF:need(s[off] in (0,1),'Boolean actual arithmetic flag');flags|=s[off]<<bit
    return tuple(m.u32(s,off) for off in m.GPR)+(flags,m.u32(s,2472))
def host(r):
    # FXSAVE does not initialize the software-reserved tail416..511. This
    # capture has distinct pre/post buffers; those bytes are not a host restore
    # observation. All captured architectural storage, XMM0..15 and ENV match.
    need(r[1140:1556]==r[1652:2068] and r[2220:2248]==r[2248:2276],'Actual host FX architectural storage/XMM0..15/ENV28 restoration')
def samecpu(actual,expected,mask,why):
    need(actual[:8]==tuple(expected[:8]) and actual[9]==expected[9] and not ((actual[8]^expected[8])&mask) and actual[8]&0x202==0x202,why)
def routes(n,expected):
    need(words(n,RCOUNT)==(len(expected),),'Actual r9 route count')
    encoded=b''.join(struct.pack('<6I',*r) for r in expected)
    need(n[ROUTE:INITIAL]==encoded+bytes(48-len(encoded)),'Complete actual r9 route ledger')

def check(o,n,sequence,phase,previous_original,previous_native,selected,insts,initial,schedule,m,control,program):
    need(len(o)==OS and len(n)==NS,'Complete phase framing')
    cw=CWS[sequence%12];entry=ENT[phase]
    tag=(sequence,sequence//12,phase,0 if not phase else selected[phase-1]['slot'],entry,cw,0,0,1)
    need(words(o,0,9)==words(n,0,9)==tag,'Real table slot and exact persistent sequence tags')
    need(words(n,INITIAL)==(cw,),'Original incoming CW tag retained')
    host(o);host(n)
    oc=CPU.unpack_from(o,36);nc=CPU.unpack_from(n,36)
    bm=0xcd5 if phase<=4 else 0xcc5;am=0xcd5 if phase<4 else 0xcc5
    if not phase:
        need(oc==(0x13579bdf,0x2468ace0,0x81726354,0x10293847,FRAME,0x92837465,0x56473829,0xaabbccdd,0x202,entry),'Actual initial original CPU')
        memory=bytearray(initial);m.put32(memory,10*4096+0x800,0x5ac436)
        need(o[2276:47332]==memory,'Original initial PE pages plus authored outer frame')
        need(m.u16(o,116)==cw and m.u16(o,118)==0 and o[120]==0 and words(o,140,2)==(0x1f80,0x2ffff),'Actual initial masked empty TOP0 FP domain')
        sb=initial_state(o,sequence,m)
        after,stack,newcw,provider_events,_=control.source_model(program,oc,o[2276+40960:47332],cw)
        ca=list(after);ca[9]=CAP;need(CPU.unpack_from(o,76)==tuple(ca),'Original full control source CPU/ADD-defined AF')
        na=list(after);na[9]=0x5ac436;need(CPU.unpack_from(n,76)==tuple(na),'Native actual full control source CPU/outer return')
        memory[40960:45056]=stack;need(o[47332:92388]==memory,'Full source-derived control eleven-page writes')
        fx=bytearray(o[116:628]);m.put16(fx,0,newcw);env=bytearray(o[2164:2192]);m.put16(env,0,newcw)
        need(o[628:1140]==fx and o[2192:2220]==env and newcw==(cw&~0x300)|0x200,'Control source changes only normalized CW')
        sa=bytearray(sb);m.statecpu(sa,na,False);m.put16(sa,2768,newcw)
        events=((1,entry,FRAME,0x5ac436),(3,0x5ac5d6,FRAME-12,0x5ac5af),(4,1961354,FRAME-12,0x5ac5af),*provider_events,(5,0x5ac5af,FRAME-8,0x5ac5af),(2,0x5ac436,FRAME+4,0x5ac436))
        need(len(events)==13 and words(n,CECOUNT)==(13,),'Thirteen real compiled control phases')
        encoded=b''.join(struct.pack('<4I',*e) for e in events)
        need(n[CE:RCOUNT]==encoded+bytes(256-len(encoded)),'Entire source-derived control event log')
        need(words(n,99396,10)==(0,0,0,0,0,0,0,0,1,0) and n[99436:103468]==bytes(4032),'No fabricated initializer events/routes for control')
        routes(n,((0x5ac431,entry,0x5ac436,0,1,0),(0x5ac5aa,0x5bb578,0x5ac5af,1,1,1)))
    else:
        expected=list(CPU.unpack_from(previous_original,76));expected[4]=FRAME;expected[9]=entry
        need(oc==tuple(expected),'Complete original preceding CPU carry')
        memory=bytearray(previous_original[47332:92388]);m.put32(memory,40960+0x800,CAP)
        need(o[2276:47332]==memory,'Original full pages carried except caller return-word setup')
        need(o[116:628]==previous_original[628:1140] and o[2164:2192]==previous_original[2192:2220],'Original whole hardware FX/legacy carry')
        expected=list(CPU.unpack_from(previous_native,76));expected[4]=FRAME;expected[9]=entry
        need(nc==tuple(expected),'Complete native preceding CPU carry including native undefined AF representative')
        sb=m.beforestate(previous_native[95892:99396],nc,entry)
        goal=m.phasegoal(entry,oc,memory,o[47332:92388],insts[entry],schedule)
        samecpu(CPU.unpack_from(o,76),goal['after'],am,'All defined original output CPU bits')
        samecpu(CPU.unpack_from(n,76),goal['after'],am,'All defined native output CPU bits')
        need(o[47332:92388]==goal['pages'],'Full eleven-page original integer/FP instruction access model')
        if entry not in m.FP:need(o[628:1140]==o[116:628] and o[2192:2220]==o[2164:2192],'Integer phase preserves original FP/legacy')
        sa=m.afterstate(sb,CPU.unpack_from(n,76),entry,o,insts[entry])
        need(words(n,99396,10)==goal['counts'],'Actual initializer per-operation counts')
        encoded=b''.join(struct.pack('<IQII',*e) for e in goal['events'])
        need(n[99436:103276]==encoded+bytes(3840-len(encoded)),'Complete ordered checked initializer events/inactive storage')
        for i,route in enumerate(goal['routes']):
            off=103276+96*i;need(words(n,off,4)==route[:4],'Actual helper call/tail route facts')
            samecpu(CPU.unpack_from(n,off+16),route[4],am,'Complete helper route before CPU')
            samecpu(CPU.unpack_from(n,off+56),route[5],am,'Complete helper route after CPU')
        need(n[103276+96*len(goal['routes']):103468]==bytes(192-96*len(goal['routes'])),'Unused helper route bytes')
        need(words(n,CECOUNT)==(0,) and n[CE:RCOUNT]==bytes(256),'No control phases fabricated in selected callback')
        routes(n,((0x5ac436 if phase==1 else CAP,entry,CAP,0,1,phase+1),))
        need(n[2276:47332]==memory and n[RFX0:RFX0+512]==previous_native[RFX1:RFX1+512],'Native full pages/RuntimeFX carry')
        need(n[116:628]==previous_native[628:1140] and n[2164:2192]==previous_native[2192:2220],'Native full software FP/legacy carry')
    samecpu(nc,oc,bm,'All defined original/native incoming CPU bits')
    need(n[2276:47332]==o[2276:47332] and n[47332:92388]==o[47332:92388],'Complete actual original/native eleven pages')
    need(n[92388:95892]==sb and n[95892:99396]==sa,'Entire modeled3504-byte resident State before/after')
    need(state_cpu(sb,m)==nc and state_cpu(sa,m)==CPU.unpack_from(n,76),'Exact CPU/flags projection from whole State')
    for off,s,env_off,ro in ((116,sb,2164,RFX0),(628,sa,2192,RFX1)):
        fx,env=m.proj(s)
        need(n[off:off+512]==fx and n[env_off:env_off+28]==env,'Complete software FX/legacy projection from actual State')
        need(m.hardwarefx(fx)==o[off:off+512] and env==o[env_off:env_off+28],'Complete separate original hardware FX512/legacyENV28 observation')
        need(n[ro:ro+512]==m.hardwarefx(fx),'Exact RuntimeFX projection retains capability/reserved/raw storage')
        need(m.u32(s,2796)==0x2ffff,'Resident State capability mask preserved')
        effective=cw if not phase and off==116 else (cw&~0x300)|0x200
        need(m.u16(fx)==effective and m.u16(fx,2)&0x3800==0 and fx[4]==0,'Result of actual control reaches every integer/numerical phase')

def corrupt(label,fn,row,off,bit=1):
    b=bytearray(row);b[off]^=bit
    try:fn(bytes(b))
    except (ValueError,struct.error) as ex:CONTROLS.append(dict(case=label,rejected=True,reason=str(ex)))
    else:raise ValueError('Independent observer accepted corruption '+label)

def main(out):
    need(not out.exists() and out.is_relative_to(BASE),'Fresh independent carry output required')
    out.mkdir(parents=True);(out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py')
    try:
        oldpins=read(ROOT/'reports/m4-mixed-startup/independent-review-r1/pins.json')
        path=ROOT/'reports/m4-mixed-startup/independent-review-r1/review.py'
        m=load('frozen_root_selected26_model',path,oldpins['files'][str(path)]['sha256'])
        cpins=read(ROOT/'reports/m4-crt-control-integration/independent-original-model-r1/pins.json')
        path=ROOT/'tools/m4-crt-control-integration-independent/original_model.py'
        control=load('frozen_root_control_model',path,cpins['files'][str(path)])
        program,commands=control.CRT.decode(out)
        extraction=read(ROOT/'reports/m4-mixed-startup/original-extract-original-build-r2/extraction.json')
        selected,insts,initial=m.staticaudit(extraction,None)
        schedule=read(ROOT/'reports/m4-startup/next-initializer-410940-events/report.json')['memory_events']
        pin(BASE/'independent-original-carry-r1/report.json','3e4732e90ade5a46509cc76a3f46c67931ca5cea4f171aeb05e142e35dea8d61')
        raw=pin(BASE/'original-run-r1/original.bin','30661de67975c894b4f8d3216a688a46621c63f6734d11b08249562253d5b549').read_bytes()
        need(raw[:8]==b'MW4CCO01' and words(raw,8,6)==(1,24,27,648,11,OS) and len(raw)==32+648*OS,'Complete original stream')
        build=read(BASE/'native-build-r4/build.json');need(build['passed'] and build['original_raw_sha256']==sha(BASE/'original-run-r1/original.bin'),'Actual positive current build')
        repeat={};levels=[]
        for level in ('O0','O2'):
            path=BASE/f'native-build-r4/native-{level}.bin';native=pin(path,build['artifacts'][str(path)]).read_bytes()
            need(native[:8]==b'MW4CCN01' and words(native,8,6)==(1,24,27,648,11,NS) and len(native)==32+648*NS,'Complete native stream')
            for seq in range(24):
                po=pn=None
                for phase in range(27):
                    index=seq*27+phase;o=raw[32+index*OS:32+(index+1)*OS];n=native[32+index*NS:32+(index+1)*NS]
                    fn=lambda a,b:check(a,b,seq,phase,po,pn,selected,insts,initial,schedule,m,control,program)
                    fn(o,n);COUNTS['native_phases']+=1
                    if phase:
                        COUNTS['initializer_access_events']+=words(n,99396)[0];COUNTS['helper_routes']+=words(n,99424)[0];COUNTS['native_State_carry_boundaries']+=1
                    else:COUNTS['control_phase_events']+=13
                    key=(seq%12,phase,level);observed=n[36:1140]+n[2164:2220]+n[2276:92388]
                    if seq<12:repeat[key]=observed
                    else:need(repeat[key]==observed,'Repeated actual guest CPU/FX/ENV/pages');COUNTS['native_repeat_pairs']+=1
                    if seq==0 and phase in (0,1,2,3,4,15,17,18,19,20,21,26):
                        offsets=[('tag',0),('CPU-before',36),('CPU-after',76),('SP-after',92),('PC-after',112),('State-before',92388+3433),('State-after',95892+3433),('State-FS',95892+2168),('State-upperGPR',95892+2220),('State-CW',95892+2768),('State-capability',95892+2796),('State-legacy',95892+2776),('State-dead-ST7-padding',95892+2486+7*16+10),('State-high-vector',95892+16+8*64),('whole-before-page',2276),('whole-after-page',47332),('FX-status',630),('FX-raw80',660),('ENV-legacy',2204),('host-XMM15',2052),('host-ENV',2248),('counts',99396),('event/inactive',99436),('helper/inactive',103276),('RuntimeFX-before',RFX0+28),('RuntimeFX-after',RFX1+28),('control-count',CECOUNT),('control-event/inactive',CE+4),('r9-count',RCOUNT),('r9-site',ROUTE),('r9-completed',ROUTE+16),('initial-CW',INITIAL)]
                        for name,off in offsets:corrupt(f'{level}/{phase}/{name}',lambda b:fn(o,b),n,off)
                        for off in (0,36,76,108,112,116,628,1140,1652,2164,2192,2220,2248,2276,47332):corrupt(f'original/{level}/{phase}/{off}',lambda b:fn(b,n),o,off)
                        if phase==4:
                            b=bytearray(n);b[108]^=0x10;b[95892+2069]^=1;b[103276+56+32]^=0x10
                            fn(o,bytes(b))
                            CONTROLS.append(dict(case=f'{level}/isolated_coherent_undefined_AF',rejected=False,accepted=True,scope='One phase record only; actual native CPU/State/helper-route representative matches. Whole subsequent carry is still required.'))
                    po,pn=o,n
            levels.append(dict(level=level,phases=648,passed=True))
        absorb(m);absorb(control);absorb(control.CRT)
        report=dict(passed=True,scope='Independent full raw control-result CW carry through actual selected26 persistent callbacks',levels=levels,original_phases=648,counts=dict(COUNTS),independent_observer_controls=CONTROLS,commands=commands,primary_comparator_or_model_imported=False,reviewer_original_native_execution=False,acceptance_requires_separate_source_build_compiled_causal_closure=True,whole_M4_complete=False,limitations=['Twelve masked incoming CW, empty TOP0/SW0/FTW0 and actual default-image operands only; no unmasked/live-tag/full-table/fullCRT/menu claim.','Original State/events/routes are unobserved. Native entire3504State, per-access events and routes are independently modeled against actual original CPU/pages/FX512/legacyENV28.','Original numerical results/status/dead raw80 are hardware observations; there is no independent numerical/condition-code architecture oracle claim.','Undefined AF is excluded only after the first XOR; native representative and full State/CPU projection/carry remain checked.','Host FXSAVE tail416..511 is uninitialized reserved capture storage; architectural bytes0..415 and entireENV28 are checked, including native XMM0..15.','Only original control outer RET observation PC projects to410A80; native returns5AC436. Subsequent caller setup changes the same one return word to410A80.','Current source/build hashes are post-build associations, not an execution-time process trace.'])
        rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');pin(rp);pin(Path(__file__))
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,counts=dict(COUNTS),controls=len(CONTROLS),report_sha256=sha(rp),pins_sha256=sha(out/'pins.json'))))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());(out/'partial.json').write_text(json.dumps(dict(counts=dict(COUNTS),controls=CONTROLS),indent=2));raise

if __name__=='__main__':main(Path(sys.argv[1]).resolve())
