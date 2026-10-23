"""ROOT typed original7 layout admission; no source models or raw readers."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 td=R/'tools/m4-startup141-paired';base=R/'reports/m4-startup141-paired'
 recipe=base/'original7-layout-consumer-preparation-r1/ROOT-review-recipe.json'
 assert sha(recipe)=='57f2d7a0273be95c2d8a6ccdc1d474d151d4e491f1ad13f07fe47bdb589ab947'
 M=json.loads(recipe.read_bytes());pins=dict(M['required_files']);assert len(pins)==70
 pins[str(recipe)]=sha(recipe)
 # Repeat the exact reviewed pure controls in fresh ROOT output namespaces.
 for leaf,old,new,count in [('prepare_original7_child_view_v3.py','original7-child-view-preparation-r2','root-original7-child-view-controls-r1',28),('prepare_original7_layout_consumer_v1.py','original7-layout-consumer-preparation-r1','root-original7-layout-controls-r1',20)]:
  p=td/leaf;text=p.read_text();ast.parse(text);pins[str(p)]=sha(p)
  before="out=R/'reports/m4-startup141-paired/"+old+"'";after="out=R/'reports/m4-startup141-paired/"+new+"'";assert text.count(before)==1
  ns={'__file__':str(p),'__name__':'ROOT_exact_pure_controls'};exec(compile(text.replace(before,after),str(p),'exec'),ns);ns['main']()
  q=base/new/'preparation-only.json';C=json.loads(q.read_bytes());assert C['prepared_only']and C['pure_controls']==count
  pins[str(q)]=sha(q)
  for p,h in C['files'].items():assert pins.setdefault(p,h)==h
 for p,h in pins.items():
  p=Path(p).resolve();assert p.is_relative_to(R)and p.suffix.lower()in('.json','.py')and p.name!='transport.json'and sha(p)==h
  if p.suffix=='.py':ast.parse(p.read_text())
 pins[str(Path(__file__).resolve())]=sha(__file__)
 out=base/'ROOT-original7-layout-admission-r1';assert not out.exists();out.mkdir()
 A=dict(passed=True,independent_review=True,scope_identity=M['scope_identity'],original7_sha256=M['original7_sha256'],selected_order_sha256=M['selected_order_sha256'],stream_parser_sha256=M['stream_parser_sha256'],whole_ordinary_inputs_physically_authenticated=True,pure_child_controls=28,pure_parser_path_controls=20,source_models_executed=False,export_reader_opened=False,complete_paired141_gate=False,accepted_function_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(A,indent=2)+'\n');print(sha(q))
if __name__=='__main__':main()
