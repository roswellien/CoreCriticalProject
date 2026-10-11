"""One admitted canonical read: exact MFC hook transitions, no verifier run."""
from pathlib import Path
import hashlib, importlib.util, json, re, struct, sys, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/m4-138-validation-review/mfc-transition-r1'
assert not OUT.exists(); OUT.mkdir(parents=True)
files={}; rows=[]; reader=None; passed=False; patches=[]
def pin(p,h=None):
    p=Path(p).resolve()
    with p.open('rb') as f:v=hashlib.file_digest(f,'sha256').hexdigest()
    assert h is None or h==v, str(p)
    assert str(p) not in files or files[str(p)]==v
    files[str(p)]=v;return p
def read(p):return json.loads(pin(ROOT/p).read_text(encoding='utf-8-sig'))
try:
    prep=read('reports/m4-startup138-original/preparation-r7/report.json')
    run=read('reports/m4-startup138-original/original-execution-r1/report.json')
    source=pin(ROOT/'reports/m4-startup138-original/preparation-r7/reference.cpp',prep['files'][str(ROOT/'reports/m4-startup138-original/preparation-r7/reference.cpp')]).read_text()
    bindings=read('reports/m4-startup138-original/preparation-r7/fs-hook-bindings.json')
    review=read('reports/m4-tree-review/original138-prelaunch-r5/report.json')
    obs=read('reports/m4-tree-review/original138-prelaunch-r5/compiled-observers.json')
    for path,value in review['files'].items():pin(path,value)
    resolutions={}
    for section in obs:
        for rel in section['relocations']:
            if rel['symbol_section']==0 and rel['resolution_kind']=='virtual address':
                name,value=rel['symbol'],rel['actual_symbol_address']
                assert name not in resolutions or resolutions[name]==value
                resolutions[name]=value
    reader_path=pin(ROOT/'tools/m4-crt-allocation-root/run_storage.py')
    spec=importlib.util.spec_from_file_location('transition_direct_reader',reader_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    print('Opening exactly one admitted canonical reader',flush=True)
    reader=module.DirectSet(run['original_capture'],pin)
    print('Canonical reader authenticated; inspecting twelve narrow transitions',flush=True)
    actual_crt=reader.data('crt-image.bin');physical_crt=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL').read_bytes();assert actual_crt==physical_crt
    sys.path.insert(0,str(ROOT/'tools/analysis'));from pe import PEImage
    crt=PEImage(physical_crt)
    targets=struct.unpack('<8I',reader.data('crt-api-targets.bin'))
    cells=(0x7802e094,0x7802e090,0x7802e1dc,0x7802e0b4,0x7802e03c,0x7802e044,0x7802e048,0x7802e040)
    names=('HeapAlloc','HeapFree','HeapSize','HeapReAlloc','InitializeCriticalSection','EnterCriticalSection','LeaveCriticalSection','DeleteCriticalSection')
    imports={crt.image_base+r['iat_rva']:r['name'] for g in crt.imports() for r in g['symbols']}
    for i,(cell,name) in enumerate(zip(cells,names)):
        assert imports[cell]==name
        patches.append(dict(pc=cell,kind='registry-IAT',symbol='_registry_API_'+str(i),named_API=name,
            original_hex=struct.pack('<I',targets[i]).hex(),instrumented_hex=struct.pack('<I',resolutions['_registry_API_'+str(i)]).hex()))
    for hook in bindings:
        if hook['PC']<0x78000000:continue
        raw=bytes.fromhex(hook['raw_bytes']); pc=hook['PC'];symbol='_'+hook['declared_observer']
        off,_=crt.rva_range(pc-crt.image_base,len(raw));assert crt.data[off:off+len(raw)]==raw
        patches.append(dict(pc=pc,kind='CRT-FS',symbol=symbol,original_hex=raw.hex(),instrumented_hex=(b'\xe9'+struct.pack('<I',(resolutions[symbol]-pc-5)&0xffffffff)+b'\x90'*(len(raw)-5)).hex()))
    nulls=re.search(r'const std::array<NullHook,2> null_hooks\{\{(.*?)\}\};',source).group(1)
    for pc,symbol,raw in re.findall(r'\{(0x[0-9a-f]+),&(\w+),\{([^}]+)\}\}',nulls):
        pc=int(pc,16);raw=bytes(int(b,16) for b in raw.split(','));symbol='_'+symbol
        off,_=crt.rva_range(pc-crt.image_base,len(raw));assert crt.data[off:off+len(raw)]==raw
        patches.append(dict(pc=pc,kind='CRT-NULLfree',symbol=symbol,original_hex=raw.hex(),instrumented_hex=(b'\xe9'+struct.pack('<I',(resolutions[symbol]-pc-5)&0xffffffff)).hex()))
    whole=read('reports/m4-startup138-original/validation-preparation-r1/page-order.json')['whole_source_pages']; fixed=prep['observed_pages'];pages=sorted(set(whole)|set(range(0x78000000,0x78040000,4096)))
    def endpoint(seq,phase,side):
        record=reader.data(f'phase/{seq}/{phase}.bin');assert len(record)==356992
        values={}
        for page in pages:
            if 0x78000000<=page<0x78040000:values[page]=reader.data(f'phase/{seq}/{phase}/CRT-{side}/{page}.bin')
            elif page in fixed:
                offset=(2276 if side=='before' else 178404)+fixed.index(page)*4096;values[page]=record[offset:offset+4096]
            else:values[page]=reader.data(f'phase/{seq}/{phase}/extra-{side}/{page}.bin')
            assert len(values[page])==4096
        return values
    for seq in range(6):
        for previous,current,install in ((12,13,False),(13,14,True)):
            before=endpoint(seq,previous,'after');after=endpoint(seq,current,'before')
            for page in pages:
                if page==0x20001000:continue
                expected=bytearray(before[page]);owned=[]
                for patch in patches:
                    if patch['pc']&~4095 != page:continue
                    offset=patch['pc']&4095
                    a=bytes.fromhex(patch['original_hex' if install else 'instrumented_hex']);z=bytes.fromhex(patch['instrumented_hex' if install else 'original_hex'])
                    assert before[page][offset:offset+len(a)]==a,(seq,current,hex(patch['pc']),'actual prior owner bytes')
                    expected[offset:offset+len(z)]=z;owned.append(patch)
                differences=[dict(address=page+i,before=a,after=z) for i,(a,z) in enumerate(zip(before[page],after[page])) if a!=z]
                row=dict(sequence=seq,previous_phase=previous,current_phase=current,page=page,install=install,patches=owned,differences=differences,whole4096_matches_expected=bytes(expected)==after[page])
                rows.append(row)
                if differences:
                    stem=f'seq{seq}-phase{previous}after-phase{current}before-{page:08x}'
                    for label,data in (('previous',before[page]),('actual',after[page]),('expected',bytes(expected))):
                        path=OUT/(stem+'-'+label+'.bin');path.write_bytes(data);pin(path)
                assert row['whole4096_matches_expected'],(seq,current,hex(page),'unexplained byte transition')
    passed=True
except Exception:
    (OUT/'failure.txt').write_text(traceback.format_exc());raise
finally:
    if reader is not None:reader.close()
    pin(__file__)
    path=OUT/'relations.json';path.write_text(json.dumps(rows,indent=2)+'\n');pin(path)
    patchpath=OUT/'patch-identities.json';patchpath.write_text(json.dumps(patches,indent=2)+'\n');pin(patchpath)
    report=dict(passed=passed,scope='Only actual phase12AFTER->13BEFORE and13AFTER->14BEFORE across six sequences, whole source69 plus CRT64 union excluding source stack',
        one_canonical_reader_opened=reader is not None,reader_closed=True,validation_executed=False,native_executed=False,initializer_credit=0,
        patches=len(patches),whole_page_relations=len(rows),changed_pages=sum(bool(row['differences']) for row in rows),
        recommendation='Reconstruct exact expected whole page from prior raw page and physically proven owning hook spans; require actual prior patch bytes then exact4096 equality, including every untouched byte. Apply only transitions into phase13 and14.',files=files)
    path=OUT/'report.json';path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),patches=len(patches),relations=len(rows))),flush=True)
