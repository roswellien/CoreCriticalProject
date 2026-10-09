"""Root original-BEFORE-only oracle for compiled shared numeric-max replay.

No author executor/comparator/model is imported or run. Hardware AFTER and
debugger observations are checked against an independent input oracle; they
are never execution inputs or native result predictions.
"""
import hashlib,importlib.util,itertools,json,mmap,struct,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
STRIDE=46680;VIEW=4084;OS=35764;FRAME=0x20001800;RET=0x410a80
BASES=(0x5bb000,0x78115000,0x60b000,0x20001000)

def need(ok,why):
    if not ok:raise ValueError(why)

def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def pin(p,want=None):
    p=Path(p).resolve();h=sha(p);need(want is None or h==want,'Exact original/native source identity '+str(p));PINS[str(p)]=h;return p

def own(path,name,h):
    p=pin(path,h);spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def word(b,o=0):return struct.unpack_from('<H',b,o)[0]
def put(b,o,v,n=4):b[o:o+n]=v.to_bytes(n,'little')

def before_state(o,case,old):
    rep,inp,depth,sticky,cw,top,entry=case;s=old.seed_state(case);put(s,2168,0x7ffde000)
    s[2768:3280]=o[120:632];sw=word(o,122)
    for p,bit in ((2737,8),(2739,9),(2741,10),(2743,14),(2745,5),(2747,4),(2749,3),(2751,2),(2753,1),(2755,0),(2757,6)):s[p]=(sw>>bit)&1
    for p,off,n in ((2774,2186,2),(2776,2180,4),(2780,2184,2),(2784,2188,4),(2788,2192,2)):s[p:p+n]=o[off:off+n]
    for i in range(8):s[2486+16*i:2496+16*i]=o[152+16*i:162+16*i];s[16+64*i:32+64*i]=o[280+16*i:296+16*i]
    # The independently checked original BEFORE CPU is the declared fixed tuple.
    need(words(o,40,10)==tuple(words(s,p)[0] for p in (2216,2248,2264,2232,2312,2328,2280,2296))+(0x202,entry),'Original BEFORE tuple drives seed')
    return s

def effect(sb,bits,old,persistent):
    v=persistent.view(sb);f0=v[3544:4056];e0=v[4056:4084];top=(word(f0,2)>>11)&7;newtop=(top-1)&7
    raw,exception,classification,output,finite=old.ORACLE.widen(bits)
    sw=word(f0,2)|exception;lf=bytearray(f0);put(lf,2,(sw&~0x3800)|(newtop<<11),2);lf[4]|=1<<newtop
    for i,value in enumerate([raw]+[f0[32+j*16:42+j*16] for j in range(7)]):lf[32+i*16:42+i*16]=value
    le=bytearray(e0);put(le,4,0xffff0000|word(lf,2));put(le,8,(word(e0,8)&~(3<<(newtop*2)))|(classification<<(newtop*2)),2);put(le,12,0x780c10f0);put(le,18,0x105,2);put(le,20,0x78115004)
    c=list(persistent.cpu(sb));c[4]=FRAME-12;c[5]=FRAME-12;c[9]=0x4c1a09;cp=old.observed_state(sb,struct.pack('<10I',*c),lf,le)
    af=bytearray(f0);put(af,2,sw,2)
    for i,value in enumerate([f0[32+j*16:42+j*16] for j in range(7)]+[raw]):af[32+i*16:42+i*16]=value
    ae=bytearray(e0);put(ae,4,0xffff0000|sw);put(ae,12,0x4c1a09);put(ae,18,0x11d,2);put(ae,20,0x60b368)
    c=list(persistent.cpu(sb));c[4]=FRAME+4;c[9]=RET;sa=old.observed_state(sb,struct.pack('<10I',*c),af,ae)
    need(persistent.view(cp)[3544:]==bytes(lf)+bytes(le) and persistent.view(sa)[3544:]==bytes(af)+bytes(ae),'Whole independently predicted FP views from native State')
    return sa,cp,output,finite

def events(memory,bits,output):
    m=bytearray(memory);ev=[]
    def off(a):need(a&~4095 in BASES,'Bounded event page');return BASES.index(a&~4095)*4096+(a&4095)
    def read(pc,a):v=words(m,off(a))[0];ev.append((pc,a,v,4,0));return v
    def write(pc,a,v):put(m,off(a),v);ev.append((pc,a,v,4,1))
    write(0x4c19f0,FRAME-4,0x92837465);write(0x4c19f3,FRAME-8,0x4c19f8);write(0x4c1a00,FRAME-12,FRAME-4);read(0x4c1a03,0x5bb4fc);write(0x4c1a03,FRAME-16,0x4c1a09)
    need(read(0x780c10f0,0x78115004)==bits,'Exact independent ORIGINAL BEFORE source word');read(0x780c10f6,FRAME-16);write(0x4c1a09,0x60b368,output)
    for i in range(10):write(0x4c1a0f+10*i,0x60b36c+4*i,0)
    for pc,a in ((0x4c1a73,FRAME-12),(0x4c1a74,FRAME-8),(0x4c19f8,FRAME-4),(0x4c19f9,FRAME)):read(pc,a)
    return bytes(m),b''.join(struct.pack('<5I',*e) for e in ev)

def observe(o,leaf,n,case,index,raw_iat,old,persistent):
    old.ORACLE.observe(o,case);leafcase=case[:-1]+(0x780c10f0,);old.ORACLE.observe(leaf,leafcase)
    need(len(n)==STRIDE and words(n,0,10)==old.ORACLE.expected_tag(case) and words(n,40,2)==(index,0),'Exact replayed wrapper tags/original index/no persistent phase')
    sb=before_state(o,case,old);bits=words(o,2280+4096+4)[0];sa,cp,output,finite=effect(sb,bits,old,persistent)
    need(n[48:4132]==persistent.view(sb),'Entire3504 original-BEFORE-derived native State/CPU/FX/ENV')
    need(n[4132:8216]==persistent.view(sa),'Entire3504 input/source-predicted native result and views')
    need(n[8216:12300]==persistent.view(cp),'Entire3504 provider-return checkpoint source model')
    memory=bytearray(o[2280:18664]);need(words(memory,0x4fc)[0]==0x780c10f0 and words(memory,12288+0x800)[0]==0x10000100,'Exact frozen original instrumentation inputs')
    put(memory,0x4fc,raw_iat);put(memory,12288+0x800,RET);ma,ev=events(memory,bits,output)
    need(n[12300:28684]==memory and n[28684:45068]==ma,'All four pages; only explicit IAT/frame BEFORE projections')
    original_after=bytearray(o[18664:35048]);put(original_after,0x4fc,raw_iat);put(original_after,12288+0x800,RET)
    need(original_after==ma,'Independently predicted native pages equal original AFTER with same two fixture projections')
    need(n[4132+3544:4132+4084]==o[632:1144]+o[2196:2224],'Complete software FX/ENV equals actual hardware observation in declared field domain')
    # Actual debugger FX observes the live return; zero metadata is unobserved.
    debug=o[35048+204:35048+716];nativefx=n[8216+3544:8216+4056]
    need(old.fxparts(nativefx)==old.fxparts(debug),'Actual original stopped CONTEXT architectural FX/raw80/SIMD checkpoint')
    need(n[8216+4056:8216+4084]==leaf[2196:2224],'Checkpoint legacy metadata from separately captured paired leaf, not debugger metadata')
    persistent.host_boundary(n,case[4])
    need(n[46148:46588]==ev,'All22 source-PC/address/value/width/op events')
    need(words(n,46588,15)==(RET,0x4c19f0,RET,0,1,0x4c19f3,0x4c1a00,0x4c19f8,0,1,0x4c1a03,0x5bb4fc,0x4c1a09,1,1),'All3 complete shared-r9 CALL/RET routes')
    need(words(n,46648,8)==(22,1,0,0,3,1,1,2),'Complete source/owner/commit counts')
    return finite

def main(build,out):
    need(build.is_relative_to(ROOT/'reports/m4-fp-numeric-max-host-boundary') and out.is_relative_to(ROOT/'reports/m4-fp-numeric-max-host-boundary') and not out.exists(),'Fresh independent paired raw review')
    out.mkdir(parents=True);(out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py')
    try:
        old=own(ROOT/'tools/m4-fp-numeric-max-independent/native_review.py','root_original_numeric_reviewer','6837acea5209e45ac6f2821b37f4d941bdd522c9ddbe320c9184378d609a5643')
        persistent_path=ROOT/'tools/m4-fp-numeric-max-host-boundary-independent/persistent_model.py'
        persistent=own(persistent_path,'root_native_persistent_model','86fa5de668633b1073415ebfc6cbbabc82557df4d677fe308ad5df13d1d364a8')
        pe=own(ROOT/'tools/analysis/pe.py','root_paired_pe','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
        game_path=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');game=pe.PEImage(game_path.read_bytes());raw_iat=game.rva_u32(0x5bb4fc-game.image_base)
        streams=[];controls=[];total=finite_count=0
        for mode,inputs,count,expected in (('default',range(1),864,'a643a6e00bbdd8b074c544791ce030dfb9f4e0d380a354aabfc4374482c1d314'),('directed',range(16),13824,'c1c0a09274f1d12b4b89701ab0ceaaeb75ad67a4dfd748e3ae8d2e0a34691e61')):
            original_path=pin(ROOT/'reports/m4-fp-numeric-max/original-r5-normal-windows'/f'{mode}.bin',expected)
            cases=list(itertools.product(range(2),inputs,(0,1,7),range(3),old.ORACLE.CWS,(0,7),(0x780c10f0,0x4c19f0)))
            for level in ('O0','O2'):
                native_path=pin(build/f'replay-{mode}-{level}/replay.bin')
                with original_path.open('rb') as of,native_path.open('rb') as nf,mmap.mmap(of.fileno(),0,access=mmap.ACCESS_READ) as original,mmap.mmap(nf.fileno(),0,access=mmap.ACCESS_READ) as native:
                    need(struct.unpack_from('<8s4I',original)==(b'MW4NMO01',1,count,OS,4) and len(original)==24+count*OS,'Complete frozen original stream')
                    need(struct.unpack_from('<8s4I',native)==(b'MW4NMI01',1,count//2,STRIDE,4) and len(native)==24+(count//2)*STRIDE,'Complete native replay stream')
                    for j,index in enumerate(range(1,count,2)):
                        o=original[24+index*OS:24+(index+1)*OS];leaf=original[24+(index-1)*OS:24+index*OS];n=native[24+j*STRIDE:24+(j+1)*STRIDE];case=cases[index]
                        finite_count+=observe(o,leaf,n,case,index,raw_iat,old,persistent);total+=1
                        if j in (0,count//2-1):
                            for offset in (0,40,48+40+2168,48+3544+28,4132+40+2486,4132+40+2737,4132+3544+2,8216+40+2472,8216+3544+32,12300+0x4fc,12300+12288+0x800,28684+8192+0x368,45580,46120,46148,46588,46648):
                                bad=bytearray(n);bad[offset]^=1
                                try:observe(o,leaf,bad,case,index,raw_iat,old,persistent)
                                except (ValueError,struct.error) as ex:controls.append(dict(mode=mode,level=level,record=j,offset=offset,rejected=True,reason=str(ex)))
                                else:raise ValueError('Observer accepted corrupted native replay '+str(offset))
                streams.append(dict(mode=mode,level=level,native_records=count//2,original_sha256=expected,native_sha256=sha(native_path)))
        for p,h in old.PINS.items():pin(p,h)
        report=dict(passed=True,scope='Independent original-BEFORE-derived paired shared numeric-max raw State/source/value/page/checkpoint/route review; compiled/source final closure pending',native_records=total,original_wrapper_records=total//2,paired_original_leaf_records=total//2,finite_exact_promotions=finite_count,special_promotions_observed_defined_payload_and_undefined_condition_policy=total-finite_count,complete_native_events=total*22,complete_shared_r9_routes=total*3,streams=streams,own_observer_controls=controls,actual_runtime_r9_unchanged=True,original_process_executed=False,author_executor_or_model_imported=False,whole_M4_complete=False,limitations=['Declared16binary32/12maskedCW/TOP0or7/live0or1or7/sticky0orDEorDEPE; depth8 denied','Native softwareState/FX/ENV vs original actual hardware outputs/checkpoint; original softwareState/access events unobserved','Original AFTER/checkpoint used only for independent checks, never native seed/result predictions','Resolved reference IAT and outer broker return word/PC explicitly projected to raw game IAT/sharedRX broker, no other memory/output normalization','Native checkpointENV inferred from separate original paired leaf observation; original stopped debugger metadatazeros unobserved','CC/deadraw80 representative/observations stay limited to declaredfixtures, source/toolhashes post-build associations notfullprocessattestation','Direct numerical host/fullENV preservation through invoke observed before cleanup; volatileSIMD/reserved FX are raw observations without equality credit'])
        rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');pin(rp);pin(Path(__file__))
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,native_records=total,controls=len(controls),report_sha256=sha(rp),pins_sha256=sha(out/'pins.json'))))
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
