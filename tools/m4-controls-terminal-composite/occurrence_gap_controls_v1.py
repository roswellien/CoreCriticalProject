"""Pure extracted-source controls: expose v3 cardinality versus ownership gap.

No production main, module imports, source evaluators, archives or raw payloads.
"""
from pathlib import Path
import ast, copy, hashlib, json, sys
R=Path(__file__).resolve().parents[2]
SOURCE=R/'tools/m4-controls-terminal-composite/build_v3.py'
EXPECTED='45fb1c34ecf0bb8a623197089cd82fb95cd544aee472e73160de16d1df73f1a4'
FIELDS={'whole_intended_protected_IAT_mutation_repairs':2,'whole_diagnostic_only_delta':1,'whole_authored_public_faults':12,'whole_true_source_entry_observer':1,'actual_compiler_TLS_cells':56,'whole_linked_control_functions':7,'entry_observer_inlined_in_whole_MFC_entry':1}
def need(value,message):
 if not value:raise ValueError(message)
class DeclaredCurrent8:
 # This is the exact weakness: production accepts any declared edge, without
 # asking whether it belongs to a legacy12 source inverse/body/entry hook.
 def execute(self,query,parameters):
  assert query.startswith('SELECT 1 FROM edges')
  return self
 def fetchone(self):return (1,)
def run(name):
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==EXPECTED
 text=raw.decode();start=text.index("  pre=reports['legacy_prelaunch_complete_review'];")
 end=text.index("  limits=reports['current8_scope_review']",start)
 # Compile ONLY the production occurrence-check statements, dedented once.
 code='\n'.join(line[2:] for line in text[start:end].splitlines())
 compiled=compile(ast.parse(code),'<exact v3 extracted occurrence block>','exec')
 current8=str(R/'reports/m4-138-controls-review/synthetic-current8-only.cpp')
 base=dict(legacy_preparation_sha256='legacy12',legacy_build_sha256='legacy12-build',all_seven_named_fields_physically_reviewed=True,counts=copy.deepcopy(FIELDS),physical_occurrences={k:[dict(identity=f'{k}-{i}',owning_source='current8 unrelated source',whole_physical_derivation='unproven description',files={current8:'0'*64})for i in range(n)]for k,n in FIELDS.items()})
 def check(value):
  scope=dict(reports={'legacy_prelaunch_complete_review':value},LEGACY_PREP='legacy12',LEGACY_BUILD='legacy12-build',need=need,Path=Path,db=DeclaredCurrent8(),cases=[dict(mode=m)for m in range(1,13)])
  try:exec(compiled,scope);return True
  except (ValueError,KeyError):return False
 rows=[];assert check(base)
 rows.append(dict(control='All seven cardinalities with unrelated current8-only declared file and invented source strings',actual_accepted_by_v3=True,required_for_physical_admission=False,gap_demonstrated=True))
 for label,mutate in [('Boolean int count',lambda v:v['counts'].__setitem__('whole_true_source_entry_observer',True)),('Missing one field',lambda v:v['counts'].pop('whole_diagnostic_only_delta')),('Wrong cardinality',lambda v:v['physical_occurrences']['whole_intended_protected_IAT_mutation_repairs'].pop()),('Duplicate identity',lambda v:v['physical_occurrences']['whole_intended_protected_IAT_mutation_repairs'][1].update(identity=v['physical_occurrences']['whole_intended_protected_IAT_mutation_repairs'][0]['identity'])),('Empty file proof',lambda v:v['physical_occurrences']['whole_diagnostic_only_delta'][0].update(files={})),('Wrong actual fault extent',lambda v:v['counts'].update(whole_authored_public_faults=8))]:
  candidate=copy.deepcopy(base);mutate(candidate);assert not check(candidate);rows.append(dict(control=label,rejected=True))
 out=R/'reports/m4-controls-terminal-composite'/name;assert not out.exists();out.mkdir()
 report=dict(synthetic_controls_completed=True,source_extracted_block_sha256=hashlib.sha256(code.encode()).hexdigest(),source_sha256=EXPECTED,controls=rows,physical_admission_gap_proven=True,builder_admissible=False,canonical_reader_opened=False,production_composer_main_executed=False,source_evaluator_executed=False,accepted_function_credit=0)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':run(sys.argv[1])
