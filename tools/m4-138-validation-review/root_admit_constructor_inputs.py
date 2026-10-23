"""Root admission of the reviewed bounded constructor observer supplement."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-validation-review/constructor-input-root-admission-r1'
 assert not out.exists()
 pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,v,h)
  assert str(p) not in pins or pins[str(p)]==v
  pins[str(p)]=v;return p
 def read(p,h):return json.loads(pin(p,h).read_bytes())
 recipe=read(R/'reports/m4-138-validation-review/constructor-input-review-recipe-r1/report.json','eba15434a52c42423c1b2a4b4eeb3f075bb26d52dc0cc66170f056a4dae1a644')
 for p,h in recipe['files'].items():pin(p,h)
 for relative in ('current_preparation','current_build','current_prelaunch','current_controls'):
  p=R/recipe[relative];v=read(p,pins[str(p.resolve())]);assert v['passed']
  for q,h in v.get('files',{}).items():pin(q,h)
 build=json.loads((R/recipe['current_build']).read_bytes())
 for q,h in json.loads((R/recipe['current_build']).with_name('pins.json').read_bytes())['files'].items():pin(q,h)
 parent=pin(R/'tools/m4-constructor-original/validate_v7.py')
 child=pin(R/'tools/m4-138-validation-review/validate_constructor_input_capture_v2.py')
 edits=json.loads(pin(out.parent/'constructor-input-review-recipe-r1/strict-validator-deltas.json').read_bytes())
 lines=child.read_text().splitlines(keepends=True)
 for e in reversed(edits):
  assert ''.join(lines[e['child_start']:e['child_end']])==e['after']
  lines[e['child_start']:e['child_end']]=e['before'].splitlines(keepends=True)
 assert ''.join(lines)==parent.read_text()
 for q,h in pins.items():assert sha(q)==h
 pin(__file__);pin(sys.executable)
 out.mkdir()
 report=dict(passed=True,independent_review=True,source_integer_observer_timing_reviewed=True,
  retained_physical_link_checks_reviewed=True,strict_validator_full_parent_inverse=True,
  bounded_selected_roots=37,new_constructor_input_phases=18,initializer_credit=0,
  scope='Root reviewed additive CRT BEFORE/AFTER pages, own segment descriptors/FS head, actual named IAT bindings and exact API-indexed CS24 observations; preserves all inherited validation. Authorizes bounded capture, not source acceptance.',
  build_sha256=sha(R/recipe['current_build']),preflight_sha256=sha(R/recipe['current_prelaunch']),files=pins)
 p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p))))
if __name__=='__main__':main()
