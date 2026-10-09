"""Independent root numeric effect and whole serialized sequence carry.

The other26 functions retain their prior accepted component credit and need
the separate independent complete-sequence reviewer. This observer predicts
the new numeric function from its actual BEFORE input, never its AFTER bytes.
"""
import argparse,hashlib,importlib.util,json,mmap,pathlib,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2];PINS={}
PAGES=(0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000)
STRIDE=132636;SEQSTRIDE=122824
INTEGER_ROOTS={0x410910,0x410940,0x43aec0,0x43aee0,0x43af00,0x43af20,0x43af40,0x43af60,0x43af80,0x43afa0,0x467490,0x4674b0,0x4674d0,0x4b5b20,0x4c7940,0x4cfef0}
def sha(p):
    with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=pathlib.Path(p).resolve();v=sha(p);assert h is None or v==h,str(p)
    assert str(p) not in PINS or PINS[str(p)]==v;PINS[str(p)]=v;return p
def module(p,name,h):
    spec=importlib.util.spec_from_file_location(name,pin(p,h));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
C=module(ROOT/'tools/m4-fp-numeric-max-carry-independent/carry_model.py','root_joint_numeric','a108b2308a6c939ca2553320f0452442a734ed700ff7254be5d23c0c237f82ca')
P=C.P;R=C.R;put=P.put
def words(b,o,n):return struct.unpack_from('<'+'I'*n,b,o)
def state(row,after=False):return row[120468:123972] if after else row[116964:120468]
def memory(row,after=False):return row[59620:116964] if after else row[2276:59620]
def projection(row,s,after=False):
    view=P.view(s);base=76 if after else 36;fx=628 if after else 116;env=2192 if after else 2164
    assert row[base:base+40]==view[:40] and row[fx:fx+512]==view[3544:4056] and row[env:env+28]==view[4056:4084]
def external(before,entry):
    s=bytearray(before);put(s,2312,P.FRAME);put(s,2472,entry);put(s,2080,P.cpu(before)[8],8)
    if entry in INTEGER_ROOTS:
        # Existing accepted integer adapters import the carried Runtime FX
        # projection into its duplicate State alias, retaining legacy metadata.
        # Logical ST/vector storage is already the projection's source.
        fx=P.view(before)[3544:4056];metadata=before[2774:2792]
        s[2768:3280]=fx;s[2774:2792]=metadata;sw=P.word(fx,2)
        for offset,bit in C.SW:s[offset]=sw>>bit&1
    return bytes(s)
def numerical_boundary(row):
    before=row[48:560];after=row[560:1072]
    assert C.numerical(before)==C.numerical(after) and row[1072:1100]==row[1100:1128],'Direct outside-return numerical/ENV preserved before harness cleanup'
def numeric(row):
    sb=state(row);mb=memory(row);assert words(row,16,1)==(0x4c19f0,) and words(row,28,1)==(0,)
    assert words(row,132628,2)==(1,2)
    assert words(sb,2328,1)==(0x92837465,),'Declared inherited EBP preserved by earlier roots'
    for offset,_ in C.SW:assert sb[offset] in (0,1)
    parts=b''.join(mb[PAGES.index(p)*4096:(PAGES.index(p)+1)*4096] for p in P.BASES)
    bits=words(parts,4096+4,1)[0];assert bits==0x7f7fffff,'Literal owning provider maximum remains unchanged'
    after,checkpoint,output,_=C.effects(sb,bits);ma,events=R.events(parts,bits,output)
    assert state(row,True)==after and row[128044:132128]==P.view(checkpoint),'Whole numeric State and provider checkpoint from actual BEFORE only'
    expected=bytearray(mb)
    for i,page in enumerate(P.BASES):at=PAGES.index(page)*4096;expected[at:at+4096]=ma[i*4096:(i+1)*4096]
    assert memory(row,True)==expected,'All14 pages, including independently predicted four-page numeric effects'
    projection(row,sb);projection(row,after,True)
    assert row[132128:132568]==events,'All22 source-PC memory events'
    packed=b''.join(struct.pack('<IQII',address,value,width,operation) for _,address,value,width,operation in struct.iter_unpack('<5I',events))
    assert row[124012:127852]==packed+bytes(3840-len(packed)) and row[127852:128044]==bytes(192)
    assert words(row,123972,10)==(22,7,15,1,1,3,0,0,1,0)
    assert words(row,132568,15)==(P.RET,0x4c19f0,P.RET,0,1,0x4c19f3,0x4c1a00,0x4c19f8,0,1,0x4c1a03,0x5bb4fc,0x4c1a09,1,1)
    return P.word(P.view(sb),3546)
def main(run,out):
    assert run.parent==ROOT/'reports/m4-joint27-startup' and out.parent==run.parent and not out.exists();out.mkdir();(out/'review-source.py').write_bytes(pathlib.Path(__file__).read_bytes())
    try:
        for prior in sorted(out.parent.glob('root-numeric-carry-r*')):
            if prior==out:continue
            for path in prior.iterdir():
                if path.is_file():pin(path)
        receipt=json.loads(pin(run/'report.json').read_text(encoding='utf-8-sig'));assert receipt['passed']
        for p,h in json.loads(pin(run/'pins.json').read_text(encoding='utf-8-sig'))['files'].items():pin(p,h)
        pe=module(ROOT/'tools/analysis/pe.py','root_joint27_table','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
        game=pe.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
        offset,_=game.rva_range(0x5e0000-game.image_base,0x244);table=struct.unpack_from('<145I',game.data,offset)
        roots={0x410910,0x410940,0x4133c0,0x43aec0,0x43aee0,0x43af00,0x43af20,0x43af40,0x43af60,0x43af80,0x43afa0,0x467490,0x4674b0,0x4674d0,0x4adb50,0x4b5af0,0x4b5b20,0x4b7020,0x4c19f0,0x4c78f0,0x4c7940,0x4c79d0,0x4ce5a0,0x4ce5c0,0x4ce5e0,0x4ce600,0x4cfef0}
        order=[(0x5e0000+4*i,target) for i,target in enumerate(table) if target in roots];assert len(order)==27
        numeric_index=next(i for i,x in enumerate(order) if x[1]==0x4c19f0);assert order[numeric_index-1][1]==0x4b7020 and order[numeric_index+1][1]==0x4c78f0
        statuses=[];controls=0;carry=0
        for level in ('O0','O2'):
            # Runner commits fresh files in its O0/O2 output directories.
            directory=run/f'unit-{level}'
            if not directory.exists():directory=run/level
            raw_path=pin(directory/'native.bin');seq_path=pin(directory/'sequences.bin')
            with raw_path.open('rb') as f,seq_path.open('rb') as sf,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw,mmap.mmap(sf.fileno(),0,access=mmap.ACCESS_READ) as summaries:
                assert raw[:8]==b'MW4J27N1' and words(raw,8,6)==(1,48,27,1296,14,STRIDE) and len(raw)==32+1296*STRIDE
                assert summaries[:8]==b'MW4J27S1' and words(summaries,8,4)==(1,48,SEQSTRIDE,14) and len(summaries)==24+48*SEQSTRIDE
                for sequence in range(48):
                    repeat=sequence//24;cw=C.O.ORACLE.CWS[(sequence%24)//2];top=(sequence%2)*7
                    summary=summaries[24+sequence*SEQSTRIDE:24+(sequence+1)*SEQSTRIDE];assert words(summary,0,12)==(sequence,repeat,cw,top,1,27,0,0,0,0,0,0);numerical_boundary(summary)
                    previous=None
                    for phase,(slot,entry) in enumerate(order):
                        index=sequence*27+phase;row=raw[32+index*STRIDE:32+(index+1)*STRIDE]
                        assert words(row,0,8)==(sequence,repeat,phase,slot,entry,cw,top,0)
                        projection(row,state(row));projection(row,state(row,True),True)
                        assert words(row,132628,2)==((1,2) if entry==0x4c19f0 else (0,1))
                        if previous is not None:
                            assert state(row)==external(state(previous,True),entry),'Whole3504 carry with explicit external CALL CPU and existing integer FX-alias projection'
                            assert memory(row)==memory(previous,True),'All14pages persistent carry'
                            carry+=1
                        else:
                            assert state(row)==external(summary[1128:4632],entry)
                            before=bytearray(summary[8136:65480]);put(before,PAGES.index(0x20001000)*4096+0x800,P.RET);assert memory(row)==before
                        if entry==0x4c19f0:
                            statuses.append({'level':level,'sequence':sequence,'incoming_SW':numeric(row)})
                            if sequence in (0,23,47):
                                for at in (28,120468+2739,120468+2486,59620+9*4096+0x368,128044+40+2739,132128,132568,123972):
                                    changed=bytearray(row);changed[at]^=1;rejected=False
                                    try:numeric(changed)
                                    except (AssertionError,ValueError,struct.error):rejected=True
                                    assert rejected,'Own numeric observer mutation';controls+=1
                        previous=row
                    assert summary[4632:8136]==state(previous,True) and summary[65480:122824]==memory(previous,True)
                    if sequence in (0,47):
                        for at in (48+2,560+24,560+32,1100+12):
                            changed=bytearray(summary);changed[at]^=1;rejected=False
                            try:numerical_boundary(changed)
                            except AssertionError:rejected=True
                            assert rejected;controls+=1
        for m in (C,C.P,C.R,C.O):
            for p,h in m.PINS.items():pin(p,h)
        (out/'incoming-numeric-states.json').write_text(json.dumps({'rows':statuses},indent=2)+'\n')
        report={'passed':True,'scope':'Independent root actual numeric BEFORE effect, complete serialized State/page carry and direct outside-return numerical boundary; other26 semantic/failure closure separate',
                'numeric_records':len(statuses),'whole3504_carry_boundaries':carry,'State_carry_projection':'External CALL CPU overlay; existing integer adapters copy carried Runtime FX into duplicate State FX alias, retaining legacy metadata. Every other byte carried.',
                'complete_pages_carried':14,'numeric_source_events':len(statuses)*22,'numeric_runtime_routes':len(statuses)*3,
                'own_corruption_rejects':controls,'input_status_values':sorted({x['incoming_SW'] for x in statuses}),'numeric_actual_table_slot':0x5e016c,
                'actual_initializer_sequence_roots':27,'complete_other26_source_semantics_reviewed_by_this_observer':False,'author_comparator_or_fixture_imported':False,
                'original_executed':False,'native_executed_by_reviewer':False,'joint27_independent_failure_closure_complete':False,'whole_M4_complete':False}
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(__file__)
        for p in out.iterdir():
            if p.is_file():pin(p)
        (out/'pins.json').write_text(json.dumps({'files':dict(sorted(PINS.items()))},indent=2)+'\n')
        print(json.dumps({'passed':True,'numeric_records':len(statuses),'carry':carry,'controls':controls,'report_sha256':sha(out/'report.json'),'pins_sha256':sha(out/'pins.json')}))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('run',type=pathlib.Path);p.add_argument('output',type=pathlib.Path);a=p.parse_args();main(a.run.resolve(),a.output.resolve())
