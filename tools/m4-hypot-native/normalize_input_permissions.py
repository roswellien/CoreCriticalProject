"""Correct fresh provider permission tags without touching genuine BEFORE bytes."""
from pathlib import Path
import hashlib
import importlib.util
import json
import re
import struct
import sys
ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'reports/m4-hypot-native'


def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def main(name):
    assert re.fullmatch('inputs-r[1-9][0-9]*',name)
    out=AREA/name;assert not out.exists();out.mkdir(parents=True)
    pins={}
    def pin(p,h=None):
        p=Path(p).resolve();assert p.suffix.lower() not in ('.mwb','.zip')
        a=sha(p);assert h is None or a==h,p
        assert str(p) not in pins or pins[str(p)]==a;pins[str(p)]=a;return p
    old_path=AREA/'inputs-r3/report.json'
    old=json.loads(pin(old_path,'46e04c33ef7ca4f8ddcf8e59a4ecb1e6189f1f0410ad635fd471538c5458125d').read_bytes())
    assert old['passed'] and old['reader_closed'] and not old['numerical_results_seeded']
    for q,h in old['files'].items():
        if Path(q).suffix.lower() not in ('.mwb','.zip'):pin(q,h)
    def unpack(blob):
        assert blob[:8]==b'MW4J124P'
        n=struct.unpack_from('<I',blob,8)[0];assert len(blob)==12+n*4104
        rows={}
        for i in range(n):
            a=12+i*4104;page,k=struct.unpack_from('<2I',blob,a)
            assert page not in rows and page%4096==0 and k in (0,1,2)
            rows[page]=(i,k,blob[a+8:a+4104])
        return rows
    baseline=unpack(pin(ROOT/'reports/m4-hypot-original/prefix-preparation-r2/pages.bin',
        '84707163c2c7b1ad4ce3ea5e8b0b15c1da722dccff9ac07034f9ff9b5ca3fdd0').read_bytes())
    assert len(baseline)==119
    path=pin(ROOT/'tools/analysis/pe.py');spec=importlib.util.spec_from_file_location('hypot_permission_PE',path)
    pe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe)
    providers=[]
    for label,rel,digest in [
        ('CRT','local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'),
        ('MFC','local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8'),
        ('MSVCP','local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a')]:
        p=pin(ROOT/rel,digest);providers.append((label,p,pe.PEImage(p.read_bytes())))
    permission_rows=None;cases=[];changed_counts=[]
    for case in old['cases']:
        raw=pin(case['pack'],case['pack_sha256']).read_bytes();pages=unpack(raw);assert len(pages)==190
        assert set(baseline)<=set(pages)
        corrected=bytearray(raw);proof=[];changed=[]
        for page,(index,old_k,data) in sorted(pages.items()):
            if page in baseline:
                # These tags already use the inherited worker's legacy scheme.
                assert old_k==baseline[page][1],hex(page)
                new_k=old_k;row=dict(page=page,kind='Inherited legacy pack',old_tag=old_k,new_tag=new_k)
            else:
                owners=[v for v in providers if v[2].image_base<=page and page+4096<=v[2].image_base+v[2].size_of_image]
                assert len(owners)==1,hex(page)
                label,path,image=owners[0];rva=page-image.image_base
                sections=[s for s in image.sections if s['virtual_address']<=rva<s['virtual_address']+max(s['raw_size'],s['virtual_size'])]
                assert len(sections)<=1
                if not sections:
                    assert rva<min(s['virtual_address'] for s in image.sections)
                    old_expected=0;new_k=1;section='PE headers'
                else:
                    s=sections[0];old_expected=2 if s['writable'] else 1 if s['executable'] else 0
                    new_k=2 if s['writable'] else 0 if s['executable'] else 1;section=s['name']
                assert old_k==old_expected,hex(page)
                row=dict(page=page,kind='Fresh physical provider page',provider=label,path=str(path),
                    image_sha256=sha(path),RVA=rva,section=section,old_tag=old_k,new_tag=new_k,
                    effective_permissions={0:'read execute',1:'read',2:'read write'}[new_k])
                struct.pack_into('<I',corrected,12+index*4104+4,new_k)
                if old_k!=new_k:changed.append(12+index*4104+4)
            proof.append(row)
        assert len([p for p in proof if p['kind']=='Fresh physical provider page'])==71
        after=unpack(corrected)
        assert set(after)==set(pages) and all(after[p][2]==pages[p][2] for p in pages)
        allowed={b+j for b in changed for j in range(4)}
        assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(raw,corrected)))
        assert permission_rows is None or permission_rows==proof
        permission_rows=proof
        path=out/('input-'+str(case['sequence'])+'.bin');path.write_bytes(corrected);pin(path)
        new=dict(case,pack=str(path.resolve()),pack_sha256=sha(path));cases.append(new);changed_counts.append(len(changed))
    states=pin(AREA/'inputs-r3/input-state.bin').read_bytes();assert len(states)==3480
    (out/'input-state.bin').write_bytes(states)
    assert (out/'input-state.bin').read_bytes()==states
    (out/'page-permissions.json').write_text(json.dumps(permission_rows,indent=2)+'\n')
    (out/'input-mapping.json').write_text(json.dumps([(p['page'],p['new_tag']) for p in permission_rows],indent=2)+'\n')
    pin(__file__);pin(sys.executable)
    for p in out.iterdir():
        if p.is_file():pin(p)
    report=dict(passed=True,scope='Unified native permission encoding; genuine BEFORE payloads conserved exactly',
        parent_inputs=str(old_path.resolve()),parent_inputs_sha256=sha(old_path),cases=cases,state_input_bytes=3480,
        memory_pages_per_case=190,permission_encoding={'0':'read execute','1':'read','2':'read write'},
        counts=dict(inherited_pages=119,fresh_provider_pages=71,changed_permission_tags_per_case=changed_counts),
        complete_page_bytes_unchanged=True,complete_CPU_FX_ENV_input_unchanged=True,
        original_AFTER_bytes_seeded=0,numerical_results_seeded=False,literal_argument_cells_from_source_only=True,
        explicit_named_IAT_instrumentation_reconstruction=True,reader_closed=True,archive_reader_opened=False,
        native_executed=False,initializer_credit=0,files=pins)
    path=out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(passed=True,sha256=sha(path),counts=report['counts'])))


if __name__=='__main__':main(sys.argv[1])
