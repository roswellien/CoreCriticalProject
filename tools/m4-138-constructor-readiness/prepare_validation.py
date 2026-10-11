"""Only update strict validator input paths to already admitted r8/r4 lineage."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-138-constructor-readiness'/name;assert not out.exists()
 child=R/'tools/m4-constructor-native/validate_fixture_v3.py';assert not child.exists()
 files={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,str(p);files[str(p)]=v;return p
 parent=pin(R/'tools/m4-constructor-native/validate_fixture_v2.py')
 original=parent.read_text();text=original;deltas=[]
 for before,after in [('fixture-preparation-r3/report.json','fixture-preparation-r4/report.json'),('fixture-build-r7/build.json','fixture-build-r8/build.json')]:
  assert text.count(before)==1;text=text.replace(before,after);deltas.append(dict(before=before,after=after))
 assert text.replace(deltas[1]['after'],deltas[1]['before']).replace(deltas[0]['after'],deltas[0]['before'])==original
 ast.parse(text)
 admitted=json.loads(pin(R/'reports/m4-constructor-native/admitted-controller-r1/report.json','f9a45fe0f08c3cbccdde1b5d8f01b406ffadc5d7a2ea7077bbb47a9e546c472b').read_bytes())
 for relative,h in [('reports/m4-constructor-native/fixture-preparation-r4/report.json',admitted['preparation_sha256']),('reports/m4-constructor-native/fixture-build-r8/build.json',admitted['build_sha256']),('reports/m4-tree-review/constructor-native37-prelaunch-r4/report.json',admitted['preflight_sha256']),('reports/m4-constructor-native/service-preparation-r5/report.json','61d3107f4003741e07c9c31b3c9b0b9c3911563fc4370df71743ae63e0e3e761'),('reports/m4-138-constructor-readiness/inputs-r1/report.json','85b8ba199e1a6abcda2a76f46e16279f82f13ae28550ff3e8c9cf0561704992e')]:pin(R/relative,h)
 pin(Path(admitted['controller_path']),admitted['controller_sha256'])
 pin(R/'tools/m4-crt-allocation-root/run_v2.py')
 pin(R/'reports/m4-constructor-source/preparation-r1/source-instructions.json')
 child.write_text(text);pin(child);pin(__file__);pin(sys.executable)
 d=dict(passed=True,scope='Unexecuted path-only strict constructor validator preparation for admitted r8/r4 lineage; every existing semantic/hardware/owner predicate unchanged',
  validator_path=str(child),validator_sha256=sha(child),parent_path=str(parent),parent_sha256=sha(parent),
  exact_delta_count=2,deltas=deltas,reverse_delta_recovers_exact_parent=True,ast_parsed=True,
  semantic_hardware_owner_gates_unchanged=True,source_attribution_algorithm_unchanged=True,
  current_service_revision='service-preparation-r5',service_frame_guard_relations='Inherited CRT admission retained plus five exact literal constructor FS forms; preparation only, does not claim those paths executed',
  native_execution_performed=False,canonical_reader_opened=False,validation_executed=False,initializer_credit=0,
  planned_argv=['C:\\Python314\\python.exe','-B',str(child),'CURRENT_R8_EXECUTION_REPORT','CURRENT_EXECUTION_SHA256','FRESH_VALIDATION_NAME'],
  limits='Strict observed gate remains separate from literal source evaluation, original pairing, fault controls, complete carried integration and accepted credit',files=files)
 out.mkdir(parents=True);q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),checker_sha256=sha(child))))
if __name__=='__main__':main(sys.argv[1])
