"""Root input-derived numeric carry observer, with separately declared FLD C1.

Only exact frozen root models are imported. No author fixture or comparator.
The source-defined absent-overflow FLD clears C1; every other numerical and
State/page/event expectation follows unchanged root predictions.
"""
import hashlib,importlib.util,itertools,json,mmap,struct,sys,traceback
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={};STRIDE=46688
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();v=sha(p);assert h is None or h==v,str(p)
    assert str(p) not in PINS or PINS[str(p)]==v;PINS[str(p)]=v;return p
def own(p,name,h):
    spec=importlib.util.spec_from_file_location(name,pin(p,h));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
P=own(ROOT/'tools/m4-fp-numeric-max-host-boundary-independent/persistent_model.py','root_carry_persistent','86fa5de668633b1073415ebfc6cbbabc82557df4d677fe308ad5df13d1d364a8')
R=own(ROOT/'tools/m4-fp-numeric-max-host-boundary-independent/replay_model.py','root_carry_replay','03f7f56f96988ad2e4109fdec9b86e888ea84ecd6059630b2e7489c40ff63b90')
O=own(ROOT/'tools/m4-fp-numeric-max-independent/native_review.py','root_carry_numeric','6837acea5209e45ac6f2821b37f4d941bdd522c9ddbe320c9184378d609a5643')
SW=((2737,8),(2739,9),(2741,10),(2743,14),(2745,5),(2747,4),(2749,3),(2751,2),(2753,1),(2755,0),(2757,6))
def seeded(case):
    rep,inp,depth,sticky,cw,top,c1=case;s=O.seed_state((rep,inp,depth,0,cw,top,0x4c19f0));P.put(s,2168,0x7ffde000)
    value=top<<11|sticky|c1<<9;P.put(s,2770,top<<11|sticky,2)
    for offset,bit in SW:s[offset]=value>>bit&1
    return bytes(s)
def effects(sb,bits):
    # This is the single independently enumerated source-defined C1 write.
    # The resulting complete outputs include all untouched input State bytes.
    loaded=bytearray(sb);loaded[2739]=0;P.put(loaded,2770,P.word(loaded,2770)&~0x200,2)
    return R.effect(bytes(loaded),bits,O,P)
def observe(row,seq,phase,case,sb,memory):
    rep,inp,depth,sticky,cw,top,c1=case
    assert len(row)==STRIDE and P.words(row,0,12)==(rep,inp,0x4c19f0,cw,top,depth,sticky,0,1,1,seq,phase),'Whole carry ordering/tag/extent'
    bits=O.ORACLE.WORDS[inp];after,checkpoint,output,_=effects(sb,bits);ma,events=R.events(memory,bits,output)
    assert row[48:4132]==P.view(sb),'Complete seeded or persistent3504 input State/CPU/FX/ENV'
    assert row[4132:8216]==P.view(after),'Entire predicted source/numerical AFTER'
    assert row[8216:12300]==P.view(checkpoint),'Entire predicted FLD checkpoint/C1 write'
    assert row[12300:28684]==memory and row[28684:45068]==ma,'Four complete pages and carried writes'
    assert row[46148:46588]==events,'All22 source memory events'
    assert P.words(row,46588,15)==(P.RET,0x4c19f0,P.RET,0,1,0x4c19f3,0x4c1a00,0x4c19f8,0,1,0x4c1a03,0x5bb4fc,0x4c1a09,1,1),'Three r9 source CALL/RET routes'
    assert P.words(row,46648,8)==(22,1,0,0,3,1,1,2),'Complete source/borrow/commit counts'
    incoming=P.word(P.view(sb),3546);assert P.words(row,46680,2)==(incoming>>9&1,incoming&0x3f),'Actual incoming C1/sticky—not original schedule when phase2 carries exceptions'
    P.host_boundary(row,cw)
    return after,ma
def numerical(fx):return [fx[:5],fx[24:28]]+[fx[32+16*i:42+16*i] for i in range(8)]
def main(build,out):
    assert not out.exists() and out.parent==ROOT/'reports/m4-fp-numeric-max-carry';out.mkdir();(out/'review-source.py').write_bytes(Path(__file__).read_bytes())
    try:
        PE=own(ROOT/'tools/analysis/pe.py','root_carry_PE','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
        game=PE.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
        provider=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
        def page(pe,a):
            b=bytearray(4096);rva=a-pe.image_base
            for s in pe.sections:
                left=max(rva,s['virtual_address']);right=min(rva+4096,s['virtual_address']+s['raw_size'])
                if left<right:b[left-rva:right-rva]=pe.read(s['raw_offset']+left-s['virtual_address'],right-left)
            return b
        memory0=page(game,P.BASES[0])+page(provider,P.BASES[1])+page(game,P.BASES[2])+bytearray(4096);P.put(memory0,12288+0x800,P.RET)
        receipt=json.loads(pin(build/'build.json','e50947fcf8c043d8f167e35c0e803f6a82b85e81313f4bab0339c9a7f1b3aa5b').read_text(encoding='utf-8-sig'));assert receipt['passed'] and not receipt['original_executed']
        for key in ('source_files','tools','artifacts'):
            for p,h in receipt[key].items():pin(p,h)
        rows=[];controls=[];positive=[];hardware_checks=0;total=0
        for level in ('O0','O2'):
            hw=pin(ROOT/f'reports/m4-fp-numeric-max-carry/hardware-build-r1/hardware-{level}.bin').read_bytes();assert struct.unpack_from('<8s4I',hw)==(b'MW4NMC01',1,18432,2736,0) and len(hw)==24+18432*2736
            for corpus,count,phase_count,inputs in (('carry',18432,1,range(16)),('persistent',2304,2,(0,))):
                path=pin(build/f'unit-{level}/{corpus}.bin');last=None;carry=0
                with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw:
                    assert struct.unpack_from('<8s4I',raw)==(b'MW4NMCI1',1,count,STRIDE,4) and len(raw)==24+count*STRIDE
                    i=0
                    for seq,case in enumerate(itertools.product(range(2),inputs,(0,1,7),(0,2,32,34),O.ORACLE.CWS,(0,7),(0,1))):
                        sb=seeded(case);memory=bytearray(memory0);P.put(memory,4096+4,O.ORACLE.WORDS[case[1]])
                        for phase in range(phase_count):
                            row=raw[24+i*STRIDE:24+(i+1)*STRIDE];after,ma=observe(row,seq,phase,case,sb,bytes(memory))
                            if corpus=='carry':
                                h=hw[24+seq*2736:24+(seq+1)*2736]
                                for no,(n,p) in enumerate(((48+3544,36),(8216+3544,548),(4132+3544,1060))):
                                    assert numerical(row[n:n+512])==numerical(h[p:p+512]),'Own raw authored hardware numeric checkpoint';hardware_checks+=1
                            if i in (0,1,count-1):
                                for off in (0,40,48+40+2739,48+3544+2,4132+40+2739,4132+40+2486,8216+40+2312,8216+4056+5,12300+4096+4,28684+8192+0x368,45580+2,46120+12,46148,46588,46648,46680):
                                    changed=bytearray(row);changed[off]^=1
                                    try:observe(bytes(changed),seq,phase,case,sb,bytes(memory))
                                    except (AssertionError,ValueError,struct.error):controls.append(dict(level=level,corpus=corpus,record=i,offset=off,rejected=True))
                                    else:raise AssertionError('Own carry corruption accepted')
                            last=(row,seq,phase,case,sb,bytes(memory));sb=bytearray(after);P.put(sb,2312,P.FRAME);P.put(sb,2472,0x4c19f0);memory=ma;i+=1;carry+=int(phase==1)
                    assert i==count;total+=count
                    for off in (45580+400,45580+5,45580+500):
                        changed=bytearray(last[0]);changed[off]^=1;observe(bytes(changed),*last[1:]);positive.append(dict(level=level,corpus=corpus,offset=off,scope='Raw volatile SIMD/reserved padding, not equality requirement'))
                    rows.append(dict(level=level,corpus=corpus,records=count,persistent_boundaries=carry,raw_sha256=sha(path)))
        for m in (O,P,R):
            for p,h in m.PINS.items():pin(p,h)
        for name in ('independent-carry-model-r1','independent-carry-model-r2'):
            for p in (ROOT/'reports/m4-fp-numeric-max-carry'/name).iterdir():
                if p.is_file():pin(p)
        pin(__file__);pin(sys.executable)
        for p in out.iterdir():
            if p.is_file():pin(p)
        report=dict(passed=True,scope='Independent input/source numerical carry and direct host-state observer; Boolean guard/compiled closure/joint startup separate',native_records=total,persistent_boundaries=2304,whole_State_bytes=3504,complete_pages_per_record=4,source_events=total*22,r9_routes=total*3,own_authored_hardware_checkpoint_comparisons=hardware_checks,rows=rows,own_corruption_rejects=controls,own_scope_positives=positive,physical_bindings=len(PINS),source_defined_delta='Absent-overflow FLD clears C1 before full checkpoint; inherited PE remains sticky. No other source numerical semantics change.',original_process_executed=False,author_comparator_or_fixture_imported=False,limitations=['Incoming0/DE/PE/DEPE and C1{0,1},depth0/1/7,TOP0/7,16binary32 and12maskedCW only','The additional hardware corpus executes authored FLD/FSTP checkpoints; it is not original game code or a complete initializer chain','Final FSTP C1 with no newly generated precision exception is a measured observation, not evidence that incoming sticky PE signals a new rounding event','Direct caller numerical/raw80/fullENV restoration before cleanup; volatile SIMD/reserved FX bytes retain raw observations','No compiled Boolean-admission/source ownership closure or actual joint27 initializer credit'],whole_M4_complete=False)
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,records=total,hardware_checkpoints=hardware_checks,corruption_rejects=len(controls),report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve())
