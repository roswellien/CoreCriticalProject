"""Exact ordinary-only guards on inherited tree pin and dependency union."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-original141-tree-source/ordinary-boundary-preparation-r1';out.mkdir();files={};deltas=[]
 def pin(p):
  p=Path(p).resolve();files[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return p
 parent=pin(R/'tools/m4-original141-tree-source/tree_source_v2.py');s=parent.read_text(encoding='utf-8')
 def edit(a,b):
  nonlocal s
  assert s.count(a)==1;s=s.replace(a,b);deltas.append(dict(old=a,new=b))
 edit('ROOT=Path(__file__).resolve().parents[2];PINS={};SHARED_READER=None','ROOT=Path(__file__).resolve().parents[2];PINS={};SHARED_READER=None;ORDINARY_EXPORT_PATHS=set()')
 edit("path=Path(path).resolve();digest=hashlib.sha256(path.read_bytes()).hexdigest()","path=Path(path).resolve();need(path.suffix.lower()not in('.mwb','.mwi','.zip')and path.name!='transport.json','No canonical archive or transport input');need(path.drive.upper()!='G:'or str(path)in ORDINARY_EXPORT_PATHS,'Only exact current ordinary export index/payload on G');digest=hashlib.sha256(path.read_bytes()).hexdigest()")
 anchor="validation_path=Path(validation_path).resolve();need(validation_path.parent.parent==ROOT/'reports/m4-original141','Exact original141 strict report namespace');validation=read(validation_path,validation_sha256);need(validation['passed']and validation['reader_closed']and validation['paired_export_readers_closed']and validation['callbacks']==111,'Genuine independently measured original141 prefix and closed export');need(0<=sequence<6,'Exact six measured original141 cases')"
 edit(anchor,anchor+"\n        global ORDINARY_EXPORT_PATHS\n        exports=validation['paired_exports'];need(len(exports)==1 and exports[0]['branch']=='original','Exact one current original ordinary export');ORDINARY_EXPORT_PATHS={str(Path(exports[0][k]).resolve())for k in('index_path','payload_path')};need(len(ORDINARY_EXPORT_PATHS)==2,'Distinct exact current ordinary index/payload')")
 edit("for dependency,identity in gate['files'].items():pin(dependency,identity)","for dependency,identity in gate['files'].items():\n                declared=Path(dependency).resolve()\n                if declared.suffix.lower()in('.mwb','.mwi','.zip')or declared.name=='transport.json'or (declared.drive.upper()=='G:'and str(declared)not in ORDINARY_EXPORT_PATHS):continue\n                pin(declared,identity)")
 reverse=s
 for row in reversed(deltas):assert reverse.count(row['new'])==1;reverse=reverse.replace(row['new'],row['old'])
 assert reverse==parent.read_text(encoding='utf-8');ast.parse(s);q=R/'tools/m4-original141-tree-source/tree_source_v3.py';assert not q.exists();q.write_text(s,encoding='utf-8');pin(q)
 old=pin(R/'tools/m4-original141-tree-source/run_ordinary_v1.py');v=old.read_text(encoding='utf-8');a='tree_source_v2.py';b='tree_source_v3.py';assert v.count(a)==1;v=v.replace(a,b);assert v.replace(b,a)==old.read_text(encoding='utf-8');q=old.with_name('run_ordinary_v2.py');assert not q.exists();ast.parse(v);q.write_text(v,encoding='utf-8');pin(q)
 prior=json.loads(pin(R/'reports/m4-original141-tree-source/preparation-r2/deltas.json').read_bytes());all_deltas=prior+deltas;rev=s
 for row in reversed(all_deltas):assert rev.count(row['new'])==1;rev=rev.replace(row['new'],row['old'])
 assert rev==pin(R/'tools/m4-startup138-original/tree_source_r5.py').read_text(encoding='utf-8')
 pin(__file__);p=out/'deltas.json';p.write_text(json.dumps(dict(tree=deltas,tree_composed=all_deltas,runner=[dict(old=a,new=b)]),indent=2)+'\n',encoding='utf-8');pin(p)
 p=out/'report.json';p.write_text(json.dumps(dict(passed=True,prepared_only=True,exact_four_tree_delta_inverse=True,exact_one_runner_binding_inverse=True,composed_fifteen_tree_delta_inverse=True,all_D_source_metadata_and_compiled_pins_retained=True,G_allowed_only_current_declared_ordinary_index_payload=True,canonical_reader_opened=False,ordinary_reader_opened=False,worker_launched=False,files=files),indent=2)+'\n',encoding='utf-8');print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main()
