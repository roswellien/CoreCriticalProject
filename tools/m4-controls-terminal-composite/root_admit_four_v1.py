"""ROOT admission of four legacy physical facets; no composite or acceptance."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def main():
 P=R/'reports/m4-controls-terminal-composite/four-physical-preparation-r1';out=P.parent/'root-four-admission-r1';assert not out.exists();files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip','.mwc')and p.name!='transport.json'
  assert p.is_relative_to(R)or p.is_relative_to(Path(sys.prefix).resolve())or p.is_relative_to(Path('C:/Program Files/Microsoft Visual Studio/18/Community'))or p.is_relative_to(Path('C:/Program Files (x86)/Windows Kits/10'))
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v,(str(p),h,v);assert files.setdefault(str(p),v)==v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 q=read(P/'required-physical-inputs.json','0005b80d54f499cb9b3d261512c3c79337322ab2608859a2d88a2675cdd28db6');assert q['prepared']and not q['actual_physical_prover_executed']and not q['current_whole_input_rehash_performed']and len(q['files'])==q['declared_input_count']==1434
 for p,h in q['files'].items():pin(p,h)
 recipe=read(P/'independent-review-recipe.json','574ffd539a201d79928401173c9143562468dca33dee951cfbc9e3fd2ce1cdfd');assert recipe['build_v3_admissible']is False and recipe['accepted_function_credit']==0
 for rel,h in [('occurrence-gap-controls-r1','e885a40c70fb30d3fc275966bd5246859451cc7f2e02529cac66dceca987f583'),('physical-preflight-controls-r1','7ebb2a2473bb4e5b84e04a3619ef71fb5a44a6429d448887e7aa7ff64ba50bc2')]:read(P.parent/rel/'report.json',h)
 script=pin(R/'tools/m4-controls-terminal-composite/legacy_four_physical_v2.py','7498d5e8fdff5a5adc5f837a8fe69753d981db82edbc924ecd558ee80157cb67');ast.parse(script.read_text())
 pin(__file__);pin(sys.executable)
 for p,h in list(files.items()):pin(p,h)
 out.mkdir();report=out/'report.json';report.write_text(json.dumps(dict(passed=True,independent_review=True,legacy_four_physical_prover_admitted=True,scope='Exact legacy12 four static source/compiled facets only; complete7 and current16 runtime/composite remain pending',all_seven_fields_admitted=False,canonical_reader_opened=False,physical_prover_executed=False,accepted_function_credit=0,files=files),indent=2)+'\n')
 with report.open('rb')as f:print(json.dumps(dict(path=str(report),sha256=hashlib.file_digest(f,'sha256').hexdigest(),files=len(files))))
if __name__=='__main__':main()
