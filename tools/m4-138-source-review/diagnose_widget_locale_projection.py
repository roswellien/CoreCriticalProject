"""Selective strict bundle diagnostic, no source machine or workers."""
from pathlib import Path
import hashlib,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle_storage import CaptureBundle

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=ROOT/'reports/m4-joint-startup138-source'/name;assert not out.exists();out.mkdir();pins={};readers=[];closed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 er=pin(ROOT/'reports/m4-joint-startup138-root/execution-r3/report.json','2203162c6c12c3f4c4b35009c39f2ddaaf52bea3abca9a8823d36237d7f0a4f6');e=json.loads(er.read_bytes())
 fail=ROOT/'reports/m4-joint-startup138-source/combined-source-provider-r4';pin(fail/'report.json','351e22b907e033f673f843edd1cde193b32d7e58e34c5c1b76966547d63d10af')
 expected=[tuple(v['borrowed_provider']['borrowed_projection'])for v in json.loads(pin(fail/'Widget-source-derivations.json').read_bytes())];assert len(expected)==7
 rows=[];indices=[]
 try:
  for level in e['levels']:
   manifest=Path(level['capture']);m=json.loads(pin(manifest,e['files'][str(manifest)]).read_bytes());assert m['passed'] and m['format']=='mw34.capture.direct.v1'
   target='sequence-0/selected/locale-research-projections.bin';found=[]
   # Search only authenticated bounded strict indices. Whole chosen part is then fully verified by the unchanged CaptureBundle.
   for part in m['parts']:
    p=manifest.parent/part['bundle'];assert p.name==part['bundle'] and p.suffix=='.mwb'
    with p.open('rb')as f:
     head=f.read(48);magic,n,h=struct.unpack('<8sQ32s',head);assert magic==b'MW34CAP1'and n==part['index_bytes']and h.hex()==part['index_sha256']and n<=64*1024*1024
     rawindex=f.read(n);assert len(rawindex)==n and hashlib.sha256(rawindex).digest()==h
    idx=json.loads(rawindex);assert idx['format']=='mw34.capture.v1' and len(idx['files'])==part['logical_files']
    indices.append(dict(level=level['level'],bundle=part['bundle'],index_sha256=h.hex(),index_bytes=n))
    matches=[v for v in idx['files']if v['path']==target]
    if matches:found.append((p,part,matches))
   assert len(found)==1 and len(found[0][2])==1
   p,part,matches=found[0];pin(p,part['sha256']);assert p.stat().st_size==part['bundle_bytes']
   reader=CaptureBundle(p,part['sha256']);readers.append(reader);assert len(reader.names())==part['logical_files']
   raw=reader.read_bytes(target);actual=[tuple(v)for v in struct.iter_unpack('<8I',raw)if v[0]==9];assert actual==expected
   q=out/(level['level']+'-locale-projections.bin');q.write_bytes(raw);pin(q);rows.append(dict(level=level['level'],target=target,actual=actual,expected=expected,chosen_bundle=part['bundle'],chosen_part_sha256=part['sha256'],total_rows=len(raw)//32))
   reader.close();readers.remove(reader)
 finally:
  for reader in readers:reader.close()
  closed=True
 pin(__file__);pin(sys.executable);pin(ROOT/'tools/m4-pipeline/capture_bundle_storage.py');pin(ROOT/'tools/m4-pipeline/paths_capture_storage.py')
 for p,h in pins.items():assert sha(p)==h
 result=dict(passed=True,scope='Exact current selected locale ledger tag9 rows only; selective full strict chosen parts',reader_closed=closed,canonical_reader_opened=True,whole_capture_union_revalidated=False,strict_selected_parts_fully_validated=True,initializer_credit=0,source_execution_performed=False,rows=rows,authenticated_indices=indices,files=pins)
 q=out/'report.json';q.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(q),rows=rows,reader_closed=closed)))
if __name__=='__main__':main(sys.argv[1])
