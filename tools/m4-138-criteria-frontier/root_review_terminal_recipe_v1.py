"""ROOT finite source inverse and pending typed frontier review; no acceptance."""
from pathlib import Path
import ast, hashlib, json, sys
R=Path(__file__).resolve().parents[2]

def main(name):
 out=R/'reports/m4-138-criteria-frontier'/name
 assert not out.exists()
 files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.is_relative_to(R) or p==Path(sys.executable).resolve()
  assert p.stat().st_size<32*1024*1024 and p.suffix.lower()not in('.mwb','.mwi','.zip')
  b=p.read_bytes();v=hashlib.sha256(b).hexdigest();assert h is None or h==v
  assert files.setdefault(str(p),v)==v;return b
 def read(p,h=None):return json.loads(pin(p,h))
 base=R/'reports/m4-138-criteria-frontier/terminal45-typed-recipe-r1'
 q=read(base/'report.json','df689843e4ddd9fa9310004608ca96f0213fe098cc19c19b5b7f970bc776f8ad')
 assert q['pending_fields']==45 and not q['configuration_created'] and not q['allowance_created']
 for p,h in q['files'].items():pin(p,h)
 parent=pin(R/'tools/m4-138-controls-review/acceptance138_semantics_v3.py').decode()
 child=pin(base/'acceptance138_semantics_composite_candidate_v1.py').decode()
 delta=read(base/'necessary-semantic-source-inverse.json');assert len(delta)==1
 d=delta[0];assert parent.count(d['before'])==child.count(d['after'])==1
 assert child.replace(d['after'],d['before'])==parent
 ast.parse(child)
 rows=read(base/'pending45-terminal-field-mapping.json')
 frontier=read(R/'reports/m4-138-controls-review/root-criterion-delta-proposal-r6/remaining-45-field-frontier.json', 'a369e7e75cee64f98fa5c64575d721eaff8d42ea0e815ced39849777a52b08d5')
 assert len(rows)==len(frontier)==45
 old={(x['gate'],x['baseline_field']):x for x in frontier}
 assert len(old)==45 and len({(x['gate'],x['baseline_field'])for x in rows})==45
 for x in rows:
  y=old[x['gate'],x['baseline_field']]
  assert type(x['baseline_expected'])is type(y['baseline_expected']) and x['baseline_expected']==y['baseline_expected']
  assert x['baseline_type']==type(y['baseline_expected']).__name__
  assert x['current_expected']is x['current_report_path']is x['current_report_sha256']is None
  assert x['no_allowance']is True and x['binding_status']=='pending_actual_composite_measurement'
 recipe=read(base/'ROOT-terminal-composition-recipe.json')
 assert recipe['rows']==45 and recipe['all841_baseline_types_and_values_must_remain_unchanged']is True
 assert recipe['all_other796_proposal_rows_must_remain_byte_equal']is True
 assert not recipe['acceptance_executed'] and not recipe['ROOT_allowance_created']
 pin(__file__);pin(sys.executable)
 for p,h in list(files.items()):pin(p,h)
 out.mkdir();p=out/'report.json'
 p.write_text(json.dumps(dict(passed=True,independent_ROOT_review=True,scope='Source inverse and pending typed recipe only; no terminal measurement, composite admission or acceptance',whole_semantic_inverse_hunks=1,pending_typed_rows=45,baseline_values_and_types_preserved=True,current_bindings_all_pending=True,semantic_checker_executed=False,large_union_read=False,configuration_created=False,allowance_created=False,accepted_function_credit=0,files=files),indent=2)+'\n')
 print(hashlib.sha256(p.read_bytes()).hexdigest())
if __name__=='__main__':main(sys.argv[1])
