"""Export exact captured widget source inputs/endpoints without a target writer."""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PINS={}
def need(v,s):
    if not v:raise ValueError(s)
def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
    p=Path(p).resolve();a=sha(p);need(h is None or h==a,'Exact physically immutable input '+str(p));need(str(p)not in PINS or PINS[str(p)]==a,'Stable input');PINS[str(p)]=a;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
    out=R/'reports/m4-widget-source'/name
    need(re.fullmatch('original-inputs-r[1-9][0-9]*',name)and not out.exists(),'Fresh owned source-input output')
    out.mkdir();capture=None;passed=False;index=[];phase_rows=[];descriptors=[]
    try:
        validation=read(R/'reports/m4-widget-original/validation-r1/report.json','2cf3792eeecce837f141dd7d1347c634ddd6e14e275189e5f56e1ed737ec996c')
        execution=read(validation['execution_path'],validation['execution_sha256'])
        review=read(R/'reports/m4-tree-review/widget-observations-r1/report.json','fadf0da1cc9cba760b0c6c10e7ce712ae419623621e9d37d347f11b50a63e852')
        need(validation['passed']and validation['reader_closed']and execution['passed']and review['passed'],'Exact closed actual original run/source observations')
        for receipt in(validation,execution,review):
            for p,h in receipt['files'].items():pin(p,h)
        tool=pin(R/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('widget_input_reader',tool);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        capture=module.DirectSet(Path(execution['original_capture']),pin)
        selected=sorted(capture.entries)
        for name_ in selected:
            # These complete raw boundary snapshots already have immutable
            # independent bounded exports; retain the logical source/hash edge
            # but do not duplicate their77 MiB payload.
            if name_.endswith('widget-snapshots.bin'):continue
            q=Path(name_);need(not q.is_absolute()and'..'not in q.parts,'Strict original relative capture name')
            target=out/'actual-capture'/q;target.parent.mkdir(parents=True,exist_ok=True)
            value=capture.data(name_);target.write_bytes(value);pin(target)
            index.append(dict(logical_capture_name=name_,bytes=len(value),export_path=str(target.resolve()),sha256=sha(target)))
        by_name={x['logical_capture_name']:x for x in index}
        prep=read(R/'reports/m4-widget-original/preparation-r9/report.json','ad3a1d2b6527a9ca19904743364273c366ea2a8565e627b9453a0d263c73ab6c')
        ordinary=prep['observed_pages'];extras=prep['external_pages'];need(len(ordinary)==43 and len(extras)==21 and len(set(ordinary+extras))==64,'Complete exact source page domains')
        for phase in range(5):
            stem=f'phase/0/{phase}/';record=capture.data(f'phase/0/{phase}.bin');need(len(record)==356992,'Exact root input ABI')
            rootdir=out/'actual-inputs'/f'phase-{phase}';rootdir.mkdir(parents=True)
            pages={}
            for side,offset in(('BEFORE',2276),('AFTER',178404)):
                d=rootdir/side;d.mkdir()
                for j,page in enumerate(ordinary):
                    q=d/f'{page}.bin';q.write_bytes(record[offset+j*4096:offset+(j+1)*4096]);pin(q);pages[side,page]=sha(q)
                for page in extras:
                    q=d/f'{page}.bin';q.write_bytes(capture.data(stem+f'extra-{side.lower()}/{page}.bin'));need(q.stat().st_size==4096,'Whole external source endpoint');pin(q);pages[side,page]=sha(q)
            need(len(pages)==128,'Both64 exact source page endpoints')
            segments=capture.data(stem+'widget-segments.bin');n=struct.unpack('<I',capture.data(stem+'widget-count.bin'))[0];need(len(segments)==40*n,'Complete actual descriptor ledger')
            for i in range(n):
                chunk=segments[i*40:(i+1)*40];w=struct.unpack_from('<4I',chunk);need(w[0]==i,'Exact actual selector occurrence')
                for j,label in enumerate(('DS','ES','SS')):
                    b=chunk[16+j*8:24+j*8];base=struct.unpack_from('<H',b,2)[0]|b[4]<<16|b[7]<<24;limit=struct.unpack_from('<H',b)[0]|(b[6]&15)<<16
                    if b[6]&128:limit=(limit<<12)|4095
                    need(base==0 and limit==0xffffffff and b[5]&128 and b[6]&64 and b[5]&16 and not b[5]&8 and b[5]&2,'Whole actual present flat32 readable/writable data descriptor')
                    descriptors.append(dict(phase=phase,index=i,segment=label,selector=w[j+1],descriptor_hex=b.hex(),base=base,effective_limit=limit))
            meta=capture.data(stem+'registry-before-meta.bin');before_backing=capture.data(stem+'registry-before-backing.bin');need(len(meta)==16 and len(before_backing)==struct.unpack_from('<I',meta,8)[0],'Actual complete current registry BEFORE ownership input')
            phase_rows.append(dict(phase=phase,root=struct.unpack_from('<I',record,16)[0],CPU_BEFORE_hex=record[36:76].hex(),FX_BEFORE_hex=record[116:628].hex(),ENV_BEFORE_hex=record[2164:2192].hex(),whole_source_BEFORE_pages=64,whole_source_AFTER_comparison_pages=64,CRT_BEFORE_pages=64,CRT_AFTER_comparison_pages=64,
                source_page_digest_rows=[dict(side=side,page=page,sha256=h)for(side,page),h in pages.items()],registry_BEFORE_metadata_hex=meta.hex(),registry_BEFORE_backing_sha256=hashlib.sha256(before_backing).hexdigest()))
        need(len(descriptors)==870,'All measured whole hardware descriptor sides independently decoded')
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        if capture is not None:
            capture.close();capture.entries.clear();capture.bundles.clear();capture=None
        pin(__file__);pin(sys.executable)
        for filename,data in(('logical-capture-export-index.json',index),('whole-original-inputs.json',phase_rows),('actual-flat-segment-descriptors.json',descriptors)):
            p=out/filename;p.write_text(json.dumps(data,indent=2)+'\n');pin(p)
        result=dict(passed=passed,scope='Exact actual captured source input and separate endpoint export only; no target execution or literal/native credit',validation_sha256='2cf3792eeecce837f141dd7d1347c634ddd6e14e275189e5f56e1ed737ec996c',
            counts=dict(phases=len(phase_rows),whole_source_BEFORE_pages=64*len(phase_rows),whole_source_AFTER_comparison_pages=64*len(phase_rows),whole_CRT_BEFORE_pages=64*len(phase_rows),whole_CRT_AFTER_comparison_pages=64*len(phase_rows),actual_flat_descriptor_rows=len(descriptors),raw_logical_capture_exports=len(index)),
            source_after_seed=False,predicted_values_supplied=False,initializer_credit=0,worker_launched=False,reader_closed=True,all_reader_aliases_closed=True,files=PINS)
        p=out/'report.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(p),sha256=sha(p),files=len(PINS),counts=result['counts'])))
if __name__=='__main__':main(sys.argv[1])
