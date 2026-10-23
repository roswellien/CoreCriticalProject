"""ROOT source and pure controls review; no production inventory admission."""
from pathlib import Path
import ast,hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 base=R/'reports/m4-controls-terminal-composite';td=R/'tools/m4-controls-terminal-composite';pins={}
 ready=base/'composite-review-ready-r2/report.json';assert sha(ready)=='6ce177d6d056950c4db5f33bfb65531b2b4765d6662f143dfb549379eca384c2'
 Q=json.loads(ready.read_bytes());assert Q['prepared_only']and not Q['production_DB_opened']and not Q['review_runner_executed'];pins[str(ready)]=sha(ready);pins.update(Q['files'])
 prep2=base/'composite-review-preparation-r2/report.json';P=json.loads(prep2.read_bytes());assert sha(prep2)=='20cfa992c2f5e8068d27ac46b59d3192667cf66514f9d063d4c8b68d9b4e4023'
 text=(td/'review_completed_composite_v2.py').read_text()
 for c in reversed(P['changes']):assert text.count(c['after'])==1;text=text.replace(c['after'],c['before'])
 assert text==(td/'review_completed_composite_v1.py').read_text()
 prep3=base/'composite-review-preparation-r3/report.json';P3=json.loads(prep3.read_bytes());assert sha(prep3)=='d62a3b9872f20ea86c0da8966295a4e246e121235c5638c222551a56c76f41cb'
 text=(td/'review_completed_composite_v3.py').read_text();c=P3['exact_deltas'][1];assert text.count(c['after'])==1;text=text.replace(c['after'],c['before'])
 block=P3['exact_deltas'][0]['block'];needle='expanded=None;facets=None;final_conservation=None;stdlib_preloaded=[]\n';assert text.count(needle+block)==1
 text=text.replace(needle+block,needle);at=text.index(" db.execute('CREATE TABLE physical");text=text[:at]+block+text[at:]
 assert text==(td/'review_completed_composite_v2.py').read_text()
 for receipt in(P,P3):
  for p,h in receipt['files'].items():assert pins.setdefault(p,h)==h
 for name,expected in [('root-review-facet-controls-r1',20),('root-composite-conservation-controls-r1',3)]:
  p=base/name/'report.json';C=json.loads(p.read_bytes());assert C['passed']and len(C['adverse_controls'])==expected and not C.get('production_main_executed',False);pins[str(p)]=sha(p)
  for p,h in C['files'].items():assert pins.setdefault(p,h)==h
 pins[str(Path(__file__).resolve())]=sha(__file__)
 for p,h in pins.items():
  assert sha(p)==h
  if Path(p).suffix=='.py':ast.parse(Path(p).read_text())
 out=base/'root-composite-reviewer-source-review-r1';assert not out.exists();out.mkdir()
 q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Reviewed distinct composite independent reviewer source and pure adverses only',exact_v1_v2_v3_inverses=True,final_full_union_and_direct_input_conservation_reviewed=True,production_inventory_opened=False,actual_composite_admitted=False,criteria_delta_allowances_created=False,pure_domain_adverses=20,pure_final_mutation_adverses=3,accepted_function_credit=0,files=pins),indent=2)+'\n');print(sha(q))
if __name__=='__main__':main()
