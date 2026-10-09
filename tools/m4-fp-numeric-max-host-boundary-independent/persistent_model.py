"""Root input-derived native persistent State/page/event model, not a runner.

Only frozen root-owned reviewers are imported. No original process or author
fixture generator, comparator, adapter or expected-output model is executed.
"""
import hashlib,importlib.util,itertools,json,struct,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
VIEW=4084;STRIDE=46680;FRAME=0x20001800;RET=0x410a80
BASES=(0x5bb000,0x78115000,0x60b000,0x20001000)

def need(ok,why):
    if not ok:raise ValueError(why)

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def pin(p,want=None):
    p=Path(p).resolve();h=sha(p);need(want is None or h==want,'Exact raw/model identity '+str(p));PINS[str(p)]=h;return p

def own(path,name,h):
    p=pin(path,h);spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def word(b,o=0):return struct.unpack_from('<H',b,o)[0]
def put(b,o,v,n=4):b[o:o+n]=v.to_bytes(n,'little')

def cpu(s):
    flags=words(s,2080)[0]&~0xcd5
    for o,bit in ((2065,0),(2067,2),(2069,4),(2071,6),(2073,7),(2075,10),(2077,11)):
        need(s[o] in (0,1),'Boolean native flag');flags|=s[o]<<bit
    return tuple(words(s,o)[0] for o in (2216,2248,2264,2232,2312,2328,2280,2296))+(flags,words(s,2472)[0])

def view(s):
    fx=bytearray(s[2768:3280]);sw=word(fx,2)&0xb880
    for o,bit in ((2737,8),(2739,9),(2741,10),(2743,14),(2745,5),(2747,4),(2749,3),(2751,2),(2753,1),(2755,0),(2757,6)):
        need(s[o] in (0,1),'Boolean native status');sw|=s[o]<<bit
    put(fx,2,sw,2);fx[6:24]=bytes(18);tag=0xffff;top=(sw>>11)&7
    for i in range(8):
        raw=s[2486+16*i:2496+16*i];fx[32+16*i:42+16*i]=raw;fx[160+16*i:176+16*i]=s[16+64*i:32+64*i]
        physical=(top+i)&7
        if fx[4]&(1<<physical):
            m=struct.unpack_from('<Q',raw)[0];e=word(raw,8)&0x7fff
            t=1 if not e and not m else 2 if e==0x7fff or not e or not(m>>63) else 0
            tag=(tag&~(3<<(2*physical)))|(t<<(2*physical))
    env=struct.pack('<7I',0xffff0000|word(fx),0xffff0000|sw,0xffff0000|tag,words(s,2776)[0],word(s,2780)|(word(s,2774)<<16),words(s,2784)[0],0xffff0000|word(s,2788))
    return struct.pack('<10I',*cpu(s))+bytes(s)+bytes(fx)+env

def effect(sb,old):
    vb=view(sb);f0=vb[3544:4056];e0=vb[4056:4084];top=(word(f0,2)>>11)&7;newtop=(top-1)&7
    raw,exc,classification,output,finite=old.ORACLE.widen(0x7f7fffff);need(exc==0 and finite,'Exact finite maximum conversion')
    lf=bytearray(f0);put(lf,2,(word(f0,2)&~0x3800)|(newtop<<11),2);lf[4]|=1<<newtop
    for i,value in enumerate([raw]+[f0[32+j*16:42+j*16] for j in range(7)]):lf[32+i*16:42+i*16]=value
    le=bytearray(e0);put(le,4,(word(e0,4)&~0x3800)|(newtop<<11),2);put(le,8,(word(e0,8)&~(3<<(newtop*2)))|(classification<<(newtop*2)),2);put(le,12,0x780c10f0);put(le,18,0x105,2);put(le,20,0x78115004)
    c=list(cpu(sb));c[4]=FRAME-12;c[5]=FRAME-12;c[9]=0x4c1a09
    checkpoint=old.observed_state(sb,struct.pack('<10I',*c),lf,le)
    af=bytearray(f0)
    for i,value in enumerate([f0[32+j*16:42+j*16] for j in range(7)]+[raw]):af[32+i*16:42+i*16]=value
    ae=bytearray(e0);put(ae,12,0x4c1a09);put(ae,18,0x11d,2);put(ae,20,0x60b368)
    c=list(cpu(sb));c[4]=FRAME+4;c[9]=RET
    after=old.observed_state(sb,struct.pack('<10I',*c),af,ae)
    need(view(checkpoint)[3544:]==bytes(lf)+bytes(le),'Independent provider-return State/FX/ENV coherence')
    need(view(after)[3544:]==bytes(af)+bytes(ae),'Independent completed State/FX/ENV coherence')
    return after,checkpoint,output

def replay(memory,output):
    result=bytearray(memory);events=[]
    def off(a):need(a&~4095 in BASES,'Own bounded event address');return BASES.index(a&~4095)*4096+(a&4095)
    def read(pc,a):v=words(result,off(a))[0];events.append((pc,a,v,4,0));return v
    def write(pc,a,v):put(result,off(a),v);events.append((pc,a,v,4,1))
    write(0x4c19f0,FRAME-4,0x92837465);write(0x4c19f3,FRAME-8,0x4c19f8);write(0x4c1a00,FRAME-12,FRAME-4)
    read(0x4c1a03,0x5bb4fc);write(0x4c1a03,FRAME-16,0x4c1a09);need(read(0x780c10f0,0x78115004)==0x7f7fffff,'Actual default provider operand');read(0x780c10f6,FRAME-16)
    write(0x4c1a09,0x60b368,output)
    for i in range(10):write(0x4c1a0f+10*i,0x60b36c+4*i,0)
    for pc,a in ((0x4c1a73,FRAME-12),(0x4c1a74,FRAME-8),(0x4c19f8,FRAME-4),(0x4c19f9,FRAME)):read(pc,a)
    need(len(events)==22,'Complete source event extent')
    return bytes(result),b''.join(struct.pack('<5I',*e) for e in events)

def host_boundary(row,cw):
    before=row[45068:45580];after=row[45580:46092]
    env=row[46092:46120];env_after=row[46120:46148]
    need(before[:5]==struct.pack('<HHB',cw,0x3a20,0x81),'Input-derived caller CW/TOP7/PE/C1/two occupied physical tags')
    need(words(before,24)[0]==0x1f80,'Input-derived caller MXCSR')
    expected_env=struct.pack('<7I',0xffff0000|cw,0xffff3a20,0xffff3ffc,0x11223344,0x011d0023,0x55667788,0xffff002b)
    need(env==expected_env,'Complete independently derived nonzero caller legacy ENV input')
    for i in range(8):
        expected=struct.pack('<QH',(1<<63)+(i<<56),0x4000|(0x8000 if i&1 else 0))
        need(before[32+16*i:42+16*i]==expected,'All independently seeded caller raw80 storage')
        need(after[32+16*i:42+16*i]==expected,'Direct after-return caller raw80 before cleanup')
    need(after[:5]==before[:5] and after[24:28]==before[24:28] and env_after==env,'Direct owned invocation preserves numerical host state and complete legacy ENV before cleanup')
    # Full512-byte images remain unmodified observations. Volatile SIMD and
    # reserved padding equality are not numerical restoration requirements.

def observe(row,sequence,phase,case,sb,memory,old):
    depth,sticky,cw,top=case
    need(len(row)==STRIDE and words(row,0,12)==(phase,0,0x4c19f0,cw,top,depth,sticky,0,1,1,sequence,phase),'Whole record and persistent schedule')
    after,checkpoint,output=effect(sb,old);ma,events=replay(memory,output)
    need(row[48:48+VIEW]==view(sb),'Whole independently seeded/carried3504 State and coherent input views')
    need(row[4132:8216]==view(after),'Whole source/numerical output3504 State and views')
    need(row[8216:12300]==view(checkpoint),'Entire independently modeled provider-return checkpoint')
    need(row[12300:28684]==memory and row[28684:45068]==ma,'All four complete before/after pages from source and persistent carry')
    host_boundary(row,cw)
    need(row[46148:46588]==events,'All22 exact source-PC/address/value/width/direction events')
    routes=(RET,0x4c19f0,RET,0,1,0x4c19f3,0x4c1a00,0x4c19f8,0,1,0x4c1a03,0x5bb4fc,0x4c1a09,1,1)
    need(words(row,46588,15)==routes,'All3 complete actual r9 routes')
    need(words(row,46648,8)==(22,1,0,0,3,1,1,2),'Complete native execution/owner/commit counters')
    return after,ma

def main(build,out):
    need(build.is_relative_to(ROOT/'reports/m4-fp-numeric-max-host-boundary') and out.is_relative_to(ROOT/'reports/m4-fp-numeric-max-host-boundary') and not out.exists(),'Fresh independent native-only raw review')
    out.mkdir(parents=True);(out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py')
    try:
        old=own(ROOT/'tools/m4-fp-numeric-max-independent/native_review.py','root_old_numeric_seed','6837acea5209e45ac6f2821b37f4d941bdd522c9ddbe320c9184378d609a5643')
        pe=own(ROOT/'tools/analysis/pe.py','root_raw_numeric_pe','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
        game_path=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');provider_path=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a')
        game=pe.PEImage(game_path.read_bytes());provider=pe.PEImage(provider_path.read_bytes())
        def page(image,address):
            b=bytearray(4096);rva=address-image.image_base
            for s in image.sections:
                start=max(rva,s['virtual_address']);end=min(rva+4096,s['virtual_address']+s['raw_size'])
                if start<end:b[start-rva:end-rva]=image.read(s['raw_offset']+start-s['virtual_address'],end-start)
            return b
        first_memory=page(game,BASES[0])+page(provider,BASES[1])+page(game,BASES[2])+bytearray(4096);put(first_memory,12288+0x800,RET)
        cases=list(itertools.product((0,1,7),range(3),old.ORACLE.CWS,(0,7)));need(len(cases)==216,'Exact declared shared domain')
        controls=[];streams=[]
        for level in ('O0','O2'):
            path=pin(build/f'unit-{level}/persistent.bin');raw=path.read_bytes()
            need(struct.unpack_from('<8s4I',raw)==(b'MW4NMI01',1,432,STRIDE,4) and len(raw)==24+432*STRIDE,'Entire native stream framing')
            for sequence,case in enumerate(cases):
                depth,sticky,cw,top=case;sb=old.seed_state((0,0,depth,sticky,cw,top,0x4c19f0));put(sb,2168,0x7ffde000);memory=bytes(first_memory)
                for phase in range(2):
                    row=raw[24+(sequence*2+phase)*STRIDE:24+(sequence*2+phase+1)*STRIDE]
                    sa,ma=observe(row,sequence,phase,case,sb,memory,old)
                    if sequence in (0,1,215):
                        for offset in (0,40,48,48+40+2168,48+3544+4,4132,4132+40+2737,4132+40+2486,8216+40+2312,12300+0x4fc,28684+8192+0x368,45580,46120,46148,46588,46648):
                            changed=bytearray(row);changed[offset]^=1
                            try:observe(bytes(changed),sequence,phase,case,sb,memory,old)
                            except (ValueError,struct.error) as ex:controls.append(dict(level=level,sequence=sequence,phase=phase,offset=offset,rejected=True,reason=str(ex)))
                            else:raise ValueError('Own observer accepted corruption '+str(offset))
                    sb=bytearray(sa);put(sb,2312,FRAME);put(sb,2472,0x4c19f0);memory=ma
            streams.append(dict(level=level,path=str(path),sha256=sha(path),records=432,persistent_pairs=216))
        for p,h in old.PINS.items():pin(p,h)
        report=dict(passed=True,scope='Independent source/input-derived native-only shared numeric-max State/page/event/carry review; original replay and final compiled closure pending',native_records=864,persistent_pairs=432,State_carry_boundaries=432,complete_native_events=19008,complete_r9_routes=2592,streams=streams,own_observer_controls=controls,author_model_or_executor_imported=False,original_process_executed=False,whole_M4_complete=False,limitations=['Default exact finite binary32 provider operand only;12maskedCW/TOP0or7/live0or1or7/sticky0orDEorDEPE','Phase2 changes only external frame ESP/PC; everyother State/FX/ENV byte andallpages carry from phase1','Software FX capability field is explicit fixture0, not an extra hardware capability measurement','Original comparisons/checkpoints retain prior standalone credit only until a separately reviewed BEFORE-only replay','Dead raw80 and undefinedcondition representatives checked within declared fixtures; not broader architecture preservation','Host BEFORE independently derives TOP7/depth2/PE+C1/CW/nonzeroENV; AFTER measured before cleanup through owned invoke. Numerical spans/fullENV only; volatileSIMD and reserved padding are unmodified observations'])
        rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');pin(rp);pin(Path(__file__))
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,records=864,controls=len(controls),report_sha256=sha(rp),pins_sha256=sha(out/'pins.json'))))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
