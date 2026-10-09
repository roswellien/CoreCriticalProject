"""Independent raw observer for persistent selected27 original/native records.

This consumes records only. It imports pinned earlier independent observers,
never an execution bridge or a primary comparator, and never runs guest code.
Original AFTER observations are comparison oracles, not executor inputs.
"""
from pathlib import Path
import argparse, collections, hashlib, importlib.util, json, mmap, struct, sys, traceback
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-joint-startup27'
PINS = {}
PAGES = (0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000)
ENTRIES = (0x410910,0x410940,0x4133c0,0x43aec0,0x43aee0,0x43af00,0x43af20,0x43af40,0x43af60,0x43af80,0x43afa0,0x467490,0x4674b0,0x4674d0,0x4adb50,0x4b5af0,0x4b5b20,0x4b7020,0x4c19f0,0x4c78f0,0x4c7940,0x4c79d0,0x4ce5a0,0x4ce5c0,0x4ce5e0,0x4ce600,0x4cfef0)
COMMON, NATIVE, SUMMARY = 116964, 132636, 122824
SB, SA, COUNTS, EVENTS, ROUTES = 116964, 120468, 123972, 124012, 127852
MEM0, MEM1 = 2276, 59620
FRAME, BROKER = 0x20001800, 0x410a80
NUMERIC, IAT, LEAF = 0x4c19f0, 0x5bb4fc, 0x780c10f0

def need(ok, why):
    if not ok: raise ValueError(why)

def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()

def pin(p, expected=None):
    p=Path(p).resolve(); actual=sha(p)
    need(expected is None or actual==expected, 'Pinned identity '+str(p))
    need(str(p) not in PINS or PINS[str(p)]==actual, 'Stable read identity '+str(p))
    PINS[str(p)]=actual
    return p

def own(p,name,expected):
    spec=importlib.util.spec_from_file_location(name,pin(p,expected))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return m

def words(b,o,n=1): return struct.unpack_from('<'+'I'*n,b,o)
def u16(b,o=0): return struct.unpack_from('<H',b,o)[0]
def put(b,o,v): struct.pack_into('<I',b,o,v)
def memory(b,after=False): return b[MEM1:COMMON] if after else b[MEM0:MEM1]
def state(b,after=False): return b[SA:COUNTS] if after else b[SB:SA]
def mo(a):
    page=a&~4095;need(page in PAGES,'Observed source-owned page')
    return PAGES.index(page)*4096+(a&4095)

def models():
    mixed=own(ROOT/'reports/m4-mixed-startup/independent-review-r1/review.py','joint27_independent26','53832a5587972840620254c792bcd732d805f411553386822ca0afb2530795c3')
    carry=own(ROOT/'tools/m4-fp-numeric-max-carry-independent/carry_model.py','joint27_independent_numeric','a108b2308a6c939ca2553320f0452442a734ed700ff7254be5d23c0c237f82ca')
    mixed.PAGES=list(PAGES)
    extraction=json.loads(pin(ROOT/'reports/m4-mixed-startup/original-extract-original-build-r2/extraction.json','62983322b91c6b446ddee5562248614ad3a22512dc1c256f1c0bfea56fcf6b97').read_text())
    lookup={i['pc']:i for i in extraction['instructions']}
    inst={g['entry']:[lookup[pc] for pc in sorted(g['instruction_pcs'])] for g in extraction['graphs']}
    schedule=json.loads(pin(ROOT/'reports/m4-startup/next-initializer-410940-events/report.json','cabc667bc4bad34e57a47093fc82aeba981d354dad6390eeb1a082c4a153c82b').read_text())['memory_events']
    return mixed,carry,inst,schedule

def cpu_equal(actual,expected,mask,why):
    need(actual[:8]==tuple(expected[:8]) and actual[9]==expected[9] and not((actual[8]^expected[8])&mask),why)
    need(actual[8]&0x202==0x202 and not actual[8]&~0xed7,'Bounded measured CPU flags')

def numeric_host(fx):
    return (fx[:5],fx[24:28],*(fx[32+16*i:42+16*i] for i in range(8)))

def outer_host(summary):
    need(numeric_host(summary[48:560])==numeric_host(summary[560:1072]),'Direct outside-return numerical host preservation')
    need(summary[1072:1100]==summary[1100:1128],'Direct outside-return legacyENV preservation')

def projection(m,row,s,after=False):
    fx,env=m.proj(s); fx=bytearray(fx);fx[6:24]=bytes(18)
    offset=628 if after else 116; eo=2192 if after else 2164
    need(row[offset:offset+512]==fx and row[eo:eo+28]==env,'Full native State FX/ENV projection')
    need(words(row,76 if after else 36,10)==tuple(m.u32(s,x) for x in m.GPR)+(0x202|sum(s[x]<<bit for bit,x in m.AF),m.u32(s,2472)),'Full native State CPU projection')

def original_projection(original,raw_iat):
    b=bytearray(original[:COMMON])
    for offset in (MEM0,MEM1):
        need(words(b,offset+mo(IAT))[0]==LEAF,'Only declared source owning original IAT relocation')
        put(b,offset+mo(IAT),raw_iat)
    return bytes(b)

def source_receipts(original_path,native_run,pe,game,raw_iat):
    receipt_path=original_path.parent/'report.json';receipt=json.loads(pin(receipt_path).read_text())
    need(receipt['passed'] and receipt['direct_primary'] and not receipt['debugger_secondary'],'Primary actual original execution receipt')
    for p,h in json.loads(pin(original_path.parent/'pins.json').read_text())['files'].items():pin(p,h)
    build_path=BASE/'original-build-r2/build.json';build=json.loads(pin(build_path).read_text())
    need(build['passed'] and build['direct_primary'] and build['original_record_size']==117684,'Exact original build schema')
    for p,h in build['sources'].items():pin(p,h)
    original_worker=pin(build['worker'],build['worker_sha256']).read_bytes();peoff=words(original_worker,60)[0]
    need(u16(original_worker,peoff+4)==0x14c,'Actual original worker I386')
    need(receipt['commands'][0]['arguments'][0]==str(Path(build['worker'])) and receipt['commands'][0]['exit_code']==0,'Actual successful original worker association')
    for p,h in json.loads(pin(native_run/'pins.json').read_text())['files'].items():pin(p,h)
    native=json.loads(pin(ROOT/'reports/m4-joint27-startup/build-only-r1/build.json','695be2d5fc34e6f134a076f1457a2687867c9d3f13e07e0bfcbd9ddcbc25f5b5').read_text())
    for group in ('sources','tools','artifacts'):
        for p,h in native[group].items():pin(p,h)
    for level,objects in native['objects'].items():
        for p,h in objects.items():pin(p,h)
    for command in json.loads(pin(native_run/'report.json').read_text())['commands']:
        worker=pin(command['arguments'][0],command['worker_sha256']).read_bytes();off=words(worker,60)[0]
        need(u16(worker,off+4)==0x8664 and command['exit_code']==0,'Actual native worker AMD64 and successful invocation')
    exdir=BASE/'original-extraction-r1';ex=json.loads(pin(exdir/'extraction.json','ab17dafad44ef706d7dc9b79bbf51a16c1ae9fb3e98e29bc77dba261003d015e').read_text())
    need(tuple(ex['observed_pages'])==PAGES and ex['IAT_relocation']=={'cell':IAT,'raw_file':raw_iat,'actual_provider_leaf':LEAF,'reason':'One declared loader-equivalent owning service relocation only'},'Exact source transport association')
    provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes()
    pack=pin(exdir/'pages.bin',ex['pack_sha256']).read_bytes();need(pack[:8]==b'MW4J27P1' and len(pack)==12+26*4104 and words(pack,8)[0]==26,'Exact sparse original pack')
    pages={}
    for i,fact in enumerate(ex['pages']):
        off=12+i*4104;address,perm=words(pack,off,2);b=pack[off+8:off+4104]
        need((address,perm)==(fact['address'],fact['permissions']) and hashlib.sha256(b).hexdigest()==fact['sha256'],'Whole original packed page association');pages[address]=b
    for span in ex['bindings']:
        pc,size,off,origin=(span[k] for k in ('pc','size','image_offset','origin'));source=provider if origin else game
        need(pages[pc&~4095][pc&4095:(pc&4095)+size]==source[off:off+size],'Whole original instruction slice association')
        if not origin:
            fileoff,_=pe.rva_range(pc-0x400000,size);need(fileoff==off,'Actual game source VA/file offset')
    need(pages[0x780c1000]==provider[0x1000:0x2000] and pages[0x78115000]==provider[0x54c00:0x55c00],'Entire unchanged numeric provider code/data source pages')
    initial=bytearray()
    for page in PAGES:
        expected=bytearray(4096)
        if page==0x20001000:expected[:]=bytes([0xa5])*4096
        elif page==0x780c1000:expected[:]=provider[0x1000:0x2000]
        elif page==0x78115000:expected[:]=provider[0x54c00:0x55c00]
        else:
            for sec in pe.sections:
                lo=max(page,0x400000+sec['virtual_address']);hi=min(page+4096,0x400000+sec['virtual_address']+sec['raw_size'])
                if hi>lo:
                    off=sec['raw_offset']+lo-0x400000-sec['virtual_address'];expected[lo-page:hi-page]=game[off:off+hi-lo]
        original_expected=bytearray(expected)
        if page==0x5bb000:put(original_expected,IAT-page,LEAF)
        need(pages[page]==original_expected,'Exact initial page provenance, one owning IAT relocation only')
        if page==0x20001000:put(expected,FRAME-page,BROKER)
        initial.extend(expected)
    return bytes(initial)

def paired_fx(m,o,n,sb,sa):
    for off,env,s in ((116,2164,sb),(628,2192,sa)):
        fx,_=m.proj(s)
        need(m.hardwarefx(fx)==o[off:off+512],'Whole portable hardware FX observation with declared metadata/mask projection')
        need(o[env:env+28]==n[env:env+28],'Whole hardware legacyENV observation')

def original_phase(m,o,tag,cpu,mem,goal,previous):
    need(len(o)>=COMMON and words(o,0,9)==tag,'Original order/domain/complete/restored tags')
    mask=0xcd5 if tag[2]<=2 else 0xcc5
    cpu_equal(words(o,36,10),cpu,mask,'Original CPU carry')
    cpu_equal(words(o,76,10),goal['after'],mask,'Original source CPU/RET effects')
    need(memory(o)==mem and memory(o,True)==goal['pages'],'Original complete14pages and source effects')
    m.hostcheck(o,False)
    if previous is not None:
        need(o[116:628]==previous[628:1140] and o[2164:2192]==previous[2192:2220],'Actual hardware FX/ENV carried between bodies')
    if tag[4] not in m.FP and tag[4]!=NUMERIC:
        need(o[116:628]==o[628:1140] and o[2164:2192]==o[2192:2220],'Integer-only original preserves hardware FP')
    for off,env in ((116,2164),(628,2192)):
        need(u16(o,off)==tag[5] and u16(o,off+2)&0x3800==tag[6]<<11 and o[off+4]==0 and words(o,off+24)[0]==0x1f80,'Original bounded persistent FP domain')
        need(u16(o,env)==tag[5] and u16(o,env+4)==u16(o,off+2) and u16(o,env+8)==0xffff,'Original separate legacyENV domain')

def native_phase(m,c,n,tag,cpu,mem,goal,sb,sa,original,checkpoint=None,pc_events=None):
    need(len(n)==NATIVE and words(n,0,8)==tag[:8],'Native exact phase order/domain/status')
    mask=0xcd5 if tag[2]<=2 else 0xcc5
    cpu_equal(words(n,36,10),cpu,mask,'Native CPU BEFORE')
    cpu_equal(words(n,76,10),goal['after'],mask,'Native source CPU/RET effects')
    need(memory(n)==mem and memory(n,True)==goal['pages'],'Native complete14pages and independently sourced effects')
    need(state(n)==sb and state(n,True)==sa,'Entire3504native State before/after including opaque storage')
    projection(m,n,sb);projection(m,n,sa,True);paired_fx(m,original,n,sb,sa)
    need(words(n,COUNTS,10)==goal['counts'],'Actual source event/test/return/route counts')
    expected_events=b''.join(struct.pack('<IQII',*e) for e in goal['events'])
    need(n[EVENTS:ROUTES]==expected_events+bytes(3840-len(expected_events)),'All source-ordered events and inactive storage')
    if tag[4]==NUMERIC:
        need(words(n,132628,2)==(1,2),'Numeric phase/raw host observation label')
        need(n[128044:132128]==c.P.view(checkpoint),'Entire numeric provider-return checkpoint from BEFORE oracle')
        need(n[132128:132568]==pc_events,'All22numeric source-PC events')
        need(n[ROUTES:128044]==bytes(192),'Numeric ordinary route storage inactive')
        need(words(n,132568,15)==(BROKER,NUMERIC,BROKER,0,1,0x4c19f3,0x4c1a00,0x4c19f8,0,1,0x4c1a03,IAT,0x4c1a09,1,1),'Actual three nested numeric Runtime routes')
        # These are observations INSIDE the whole-loop host boundary. They do
        # not promise per-phase volatile SIMD or numerical host restoration.
    else:
        need(words(n,132628,2)==(0,1) and n[128044:132568]==bytes(4524),'Non-numeric phase schema and inactive numeric observations')
        need(words(n,132568,15)==(BROKER,tag[4],BROKER,0,1)+(0,)*10,'Actual completed single Runtime root route')
        need(words(n,32)[0]==1,'Non-numeric inner host restoration fact');m.hostcheck(n,True)
        for i,route in enumerate(goal['routes']):
            off=ROUTES+i*96;need(words(n,off,4)==route[:4],'Actual helper route contract')
            cpu_equal(words(n,off+16,10),route[4],mask,'Actual helper route BEFORE')
            cpu_equal(words(n,off+56,10),route[5],mask,'Actual helper route AFTER')
        need(n[ROUTES+len(goal['routes'])*96:128044]==bytes(192-len(goal['routes'])*96),'Inactive helper route storage')

def numeric_goal(c,sb,mem):
    parts=b''.join(mem[PAGES.index(p)*4096:(PAGES.index(p)+1)*4096] for p in c.P.BASES)
    bits=words(parts,4096+4)[0];need(bits==0x7f7fffff,'Exact unchanged provider source data')
    sa,cp,output,_=c.effects(sb,bits);ma,events=c.R.events(parts,bits,output)
    after=bytearray(mem)
    for i,page in enumerate(c.P.BASES): off=PAGES.index(page)*4096;after[off:off+4096]=ma[i*4096:(i+1)*4096]
    packed=[(a,v,w,op) for pc,a,v,w,op in struct.iter_unpack('<5I',events)]
    return dict(after=c.P.cpu(sa),pages=bytes(after),events=packed,routes=[],counts=(22,7,15,1,1,3,0,0,1,0)),sa,cp,events

def corruptions(fn,raw,offsets,label):
    controls=[]
    for off in offsets:
        b=bytearray(raw);b[off]^=1
        try: fn(bytes(b))
        except (ValueError,AssertionError,struct.error,IndexError): controls.append(dict(case=label,offset=off,rejected=True))
        else: raise ValueError('Independent corruption accepted '+label+' '+str(off))
    return controls

def main(original_path,native_run,out,original_stride):
    need(out.parent==BASE and out.name.startswith('independent-') and not out.exists(),'Fresh private independent receipt directory')
    out.mkdir(parents=True);(out/'review-source.py').write_bytes(Path(__file__).read_bytes())
    counts=collections.Counter();controls=[]
    try:
        m,c,inst,schedule=models()
        game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes()
        pe=own(ROOT/'tools/analysis/pe.py','joint27_pe','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638').PEImage(game)
        def readva(a,size): off,_=pe.rva_range(a-0x400000,size);return game[off:off+size]
        table=[(0x5e0000+i*4,words(readva(0x5e0000+i*4,4),0)[0]) for i in range(145)]
        selected=[(slot,e) for slot,e in table if e in ENTRIES]
        need(tuple(e for slot,e in selected)==ENTRIES and selected[18]==(0x5e016c,NUMERIC),'Actual selected27table ownership/order')
        for entry,instructions in inst.items():
            for i in instructions: need(readva(i['pc'],i['size'])==bytes.fromhex(i['bytes']),'Frozen source instruction association')
        raw_iat=words(readva(IAT,4),0)[0];initial_memory=source_receipts(original_path,native_run,pe,game,raw_iat)
        files=[]
        for name,path,stride,magic in [('original',original_path,original_stride,None),('O0',native_run/'O0/native.bin',NATIVE,b'MW4J27N1'),('O2',native_run/'O2/native.bin',NATIVE,b'MW4J27N1')]:
            f=pin(path).open('rb'); mm=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);files.append((f,mm))
            need(words(mm,8,6)==(1,48,27,1296,14,stride) and len(mm)==32+1296*stride,'Complete exact joint raw header/extent '+name)
            need(mm[:8]==(magic or b'MW4J27O1'),'Exact primary versus native framing')
        original,zero,two=[v[1] for v in files]
        summaries=[]
        for level in ('O0','O2'):
            f=pin(native_run/level/'sequences.bin').open('rb');mm=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);files.append((f,mm));summaries.append(mm)
            need(mm[:8]==b'MW4J27S1' and words(mm,8,4)==(1,48,SUMMARY,14) and len(mm)==24+48*SUMMARY,'Complete outer summary')
        for sequence in range(48):
            repeat=sequence//24;cw=m.CW[(sequence%24)//2];top=(sequence%2)*7;previous_o=None;previous_s=[None,None];previous_mem=None
            for level,summary_raw in zip(('O0','O2'),summaries):
                summary=summary_raw[24+sequence*SUMMARY:24+(sequence+1)*SUMMARY]
                need(words(summary,0,12)==(sequence,repeat,cw,top,1,27,0,0,0,0,0,0),'Complete outside summary');outer_host(summary)
            for phase,(slot,entry) in enumerate(selected):
                idx=sequence*27+phase;literal=original[32+idx*original_stride:32+(idx+1)*original_stride]
                need(literal[COMMON:]==bytes(720),'Direct primary has no debugger checkpoint fields')
                o=original_projection(literal,raw_iat)
                tag=(sequence,repeat,phase,slot,entry,cw,top,0,1);cpu=words(o,36,10)
                if previous_o is not None:
                    want=list(words(previous_o,76,10));want[4]=FRAME;want[9]=entry
                    cpu_equal(cpu,want,0xcd5 if phase<=2 else 0xcc5,'Actual original CPU persistent carry');need(memory(o)==previous_mem,'Actual14page persistent carry')
                else:
                    need(cpu==(0x13579bdf,0x2468ace0,0x81726354,0x10293847,FRAME,0x92837465,0x56473829,0xaabbccdd,0x202,entry),'Authored initial original CPU')
                    need(memory(o)==initial_memory,'Whole14 initial pages predicted independently from owned images and explicit frame')
                mem=memory(o)
                for k,(level,raw,summary_raw) in enumerate(zip(('O0','O2'),(zero,two),summaries)):
                    n=raw[32+idx*NATIVE:32+(idx+1)*NATIVE];ncpu=words(n,36,10)
                    if phase==0: sb=bytes(m.seed(ncpu,repeat,cw,top))
                    elif entry==NUMERIC:
                        carried=bytearray(previous_s[k]);m.statecpu(carried,ncpu);sb=bytes(carried)
                    else: sb=bytes(m.beforestate(previous_s[k],ncpu,entry))
                    projection(m,n,sb)
                    checkpoint=events=None
                    if entry==NUMERIC: goal,sa,checkpoint,events=numeric_goal(c,sb,mem)
                    else:
                        goal=m.phasegoal(entry,cpu,mem,memory(o,True),inst[entry],schedule)
                        sa=bytes(m.afterstate(sb,words(n,76,10),entry,o,inst[entry]))
                    original_phase(m,o,tag,cpu,mem,goal,previous_o)
                    native_phase(m,c,n,tag,cpu,mem,goal,sb,sa,o,checkpoint,events)
                    if phase==0:
                        summary=summary_raw[24+sequence*SUMMARY:24+(sequence+1)*SUMMARY]
                        initial=bytearray(summary[1128:4632]);m.statecpu(initial,ncpu)
                        initial=bytes(m.beforestate(initial,ncpu,entry));need(sb==initial,'Whole seed-to-first-CALL State association')
                        sm=bytearray(summary[8136:65480]);put(sm,mo(FRAME),BROKER);need(mem==sm,'Whole initial14pages against sequence boundary')
                    if phase==26:
                        summary=summary_raw[24+sequence*SUMMARY:24+(sequence+1)*SUMMARY]
                        need(summary[4632:8136]==sa and summary[65480:SUMMARY]==goal['pages'],'Whole final State/pages versus outside summary')
                    if sequence in (0,23,47) and phase in (0,1,2,3,17,18,19,20,26):
                        fn=lambda b:native_phase(m,c,b,tag,cpu,mem,goal,sb,sa,o,checkpoint,events)
                        offsets=[0,36,76,92,112,MEM0,MEM1,SB+3433,SA+3433,SA+2220,SA+2776,SA+2745,628+2,2192+12,EVENTS,EVENTS+4,EVENTS+12,EVENTS+16,COUNTS,COUNTS+16,ROUTES,132568]
                        if entry==NUMERIC:offsets.extend([128044+40+2739,132128,132628])
                        else:offsets.extend([1652+400,2248,132628])
                        controls.extend(corruptions(fn,n,offsets,level+f'/s{sequence}/p{phase}'))
                        if k==0:
                            def original_pair(b):
                                changed=original_projection(b,raw_iat)
                                original_phase(m,changed,tag,cpu,mem,goal,previous_o)
                                native_phase(m,c,n,tag,cpu,mem,goal,sb,sa,changed,checkpoint,events)
                                need(b[COMMON:]==bytes(720),'Direct debugger fields inactive')
                            controls.extend(corruptions(original_pair,literal,[0,36,76,92,112,MEM0,MEM1,116,2164+12,1652+32,1652+160,2248,108,628,630,632,652,628+32,628+8,2192+12,2192+18,COMMON],f'original/s{sequence}/p{phase}'))
                    previous_s[k]=sa;counts['native_phases']+=1;counts['source_events']+=len(goal['events']);counts['runtime_root_routes']+=3 if entry==NUMERIC else 1;counts['native_State_carry_boundaries']+=int(phase!=0)
                previous_o=o;previous_mem=memory(o,True);counts['original_phases']+=1;counts['hardware_carry_boundaries']+=int(phase!=0)
            counts['complete_sequences']+=1
        for f,mm in files:mm.close();f.close()
        for dep in (c,c.P,c.R,c.O):
            for p,h in dep.PINS.items():pin(p,h)
        report=dict(passed=True,scope='Independent connected27 actual original/native full State/page/event/route comparison; fault controls require separate receipt',counts=dict(counts),corruption_rejections=len(controls),original_IAT_projection=dict(address=IAT,original=LEAF,native_raw=raw_iat,bytes=4),source_models='Frozen separately independent26 instruction/raw observer plus numeric BEFORE oracle; no primary comparator or executor imported',FP_scope='RawFX metadata/mask transport declared; full separateENV observed. Final condition bits/dead80 storage are observations. Outer direct numerical/legacyENV restoration; numeric phase host fields are inner observations.',original_software_State_unobserved=True,source_fault_controls_accepted=False,whole_M4_complete=False)
        (out/'corruptions.json').write_text(json.dumps(controls,indent=2)+'\n');(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        for p in out.iterdir():
            if p.is_file():pin(p)
        pin(__file__);(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(report))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());(out/'partial.json').write_text(json.dumps(dict(counts=dict(counts),corruption_rejections=len(controls),pins=PINS),indent=2)+'\n');raise

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('original',type=Path);p.add_argument('native_run',type=Path);p.add_argument('output',type=Path);p.add_argument('--original-stride',type=int,default=117684);a=p.parse_args();main(a.original.resolve(),a.native_run.resolve(),a.output.resolve(),a.original_stride)
