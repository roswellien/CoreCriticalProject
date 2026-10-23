"""ROOT-only whole ordinary replay dependency preparation, no imports/readers.

Conservative physical dependency union. This never mints ROOT admission or
substitutes retained source results for current original141 replay outcomes.
"""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(configuration,configuration_sha,control_closure,control_sha,name):
 out=R/'reports/m4-original141-source'/name;assert not out.exists();out.mkdir();files={};deferred={};sources=[]
 def ordinary(p):return p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
 def pin(p,h=None):
  p=Path(p).resolve();assert ordinary(p);v=sha(p);assert h is None or v==h;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 C=read(configuration,configuration_sha);assert C['schema']=='mw34-original141-source-input-contract-v1';V=read(C['validation']['path'],C['validation']['sha256']);assert V['passed']and V['reader_closed']and V['counts']['phases']==846
 export=V['paired_exports'][0];allowed={str(Path(export[k]).resolve())for k in('index_path','payload_path')};assert export['branch']=='original'
 def absorb(mapping):
  for p,h in mapping.items():
   q=Path(p).resolve()
   if not ordinary(q)or(not q.is_relative_to(R)and str(q)not in allowed):deferred[p]=h
   else:pin(q,h)
 # Current TREE union includes all current strict ordinary observation files and
 # sealed index/payload. It is a physical input union, never a model outcome.
 treeunion=read(R/'reports/m4-original141-tree-source/admission-recipe-r3/current-ordinary-input-union.json','38614651c6c64bb99cd649a4952dfb211cc535619e62afe148c8e8653e2d7e9d');absorb(treeunion['files'])
 control=read(control_closure,control_sha);absorb(read(control['required_ordinary_files'],control['required_ordinary_files_sha256']))
 for rel,h in [('reports/m4-startup138-original/inherited-source-r5/report.json','7024af25138f109143adfd72db01b58f3bd58e9a22d8c772fda0e983d18d3eb4'),('reports/m4-startup138-original/widget-complete-source-r1/report.json','4f9e1d0a8fc80f4780bf9e6ce50fe5bf1df3dcc02b42581fa369fe0c6e889684')]:
  # Exact path/hash identities are immutable recipe requirements. If the widget
  # receipt lives at a different known frozen path, ROOT must prepare a new tool,
  # not use an identity search or fallback during this admission stage.
  p=R/rel;q=read(p,h);assert q['passed'];absorb(q['files']);sources.append(dict(path=str(p),sha256=h))
 for rel in ['readiness-r1','source-preparation-r1','family-preparation-r2','old4-preparation-r1','controller-preparation-r3','controls-preparation-r1','root-static-review-r1','root-cleanup-review-r1']:
  p=R/'reports/m4-original141-source'/rel/'report.json';q=read(p);absorb(q['files'])
 for key,value in C.items():
  if isinstance(value,dict)and set(('path','sha256'))<=set(value):
   q=read(value['path'],value['sha256'])
   if 'files'in q:absorb(q['files'])
 # Explicit current aggregate/children and all own direct model helpers.
 for rel in ['replay_original141_v3.py','constructor_replay141_v1.py','constructor_input141_v1.py','derive_source141_v1.py','game_model141_v1.py','observer_shadow141_v1.py','retained_corpus141_v1.py','format_source141_v1.py','old4_source141_v1.py','mfc_source141_v1.py','widget_source141_v3.py']:pin(R/'tools/m4-original141-source'/rel)
 for key in('index_path','payload_path'):pin(export[key],export[key.replace('_path','_sha256')])
 pin(__file__);required=out/'required-ordinary-files.json';required.write_text(json.dumps(files,indent=2)+'\n')
 q=out/'report.json';q.write_text(json.dumps(dict(prepared_only=True,configuration_sha256=configuration_sha,imports_executed=False,source_execution=False,canonical_reader_opened=False,ordinary_export_opened=False,ROOT_admission_minted=False,initializer_credit=0,conservative_dependency_union=True,retained_receipts_are_physical_dependencies_only=sources,required_ordinary_files=str(required),required_ordinary_files_sha256=sha(required),deferred_capture_or_external_identities=deferred,files={str(Path(configuration).resolve()):configuration_sha,str(Path(control_closure).resolve()):control_sha,str(required):sha(required),str(Path(__file__).resolve()):sha(Path(__file__))}),indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),ordinary_files=len(files))))
if __name__=='__main__':main(*sys.argv[1:])
