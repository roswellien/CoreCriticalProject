"""Ordinary source program/inheritance admission preflight, no captures."""
from pathlib import Path
import ast,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main():
 out=R/'reports/m4-startup141-source/model-preflight-r1';assert not out.exists();out.mkdir(parents=True);pins={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=hashlib.sha256(p.read_bytes()).hexdigest();assert h is None or v==h;pins[str(p)]=v;return p
 def load(n,p):
  spec=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 try:
  prep=json.loads(pin(R/'reports/m4-startup141-source/model-preparation-r1/report.json','c2017c280294382064893df29787c1489c01a0366c8c0fba36bfd1ff93dc703e').read_bytes())
  for p,h in prep['files'].items():pin(p,h)
  C=load('persistent141_preflight',R/'tools/m4-native141-source/persistent_constructors_v2.py');program,callbacks=C.source_program();old,oldcallbacks=C.G.source_program()
  for pc,row in old.items():
   other=program[pc];assert (row['width'],row['bytes_hex'],row['decoded_operands'])==(other['width'],other['bytes_hex'],other['decoded_operands'])
  for pc,row in oldcallbacks.items():assert callbacks[pc]==row
  assert issubclass(C.Machine,C.G.Machine) and all(root in program for root in C.ROOTS)
  for name in ('begin_widget','end_widget','begin_constructor','end_constructor','run_carried_constructor','synchronize_constructor_owners'):assert callable(getattr(C.Machine,name))
  helper=ast.parse(pin(R/'tools/m4-native141-source/persistent_constructors_v2.py').read_text())
  names={n.id for n in ast.walk(helper)if isinstance(n,ast.Name)}
  assert not({'DirectSet','Facade','BEFORE_State_hex','BEFORE_memory','phase_capture'}&names)
  for mod in tuple(sys.modules.values()):
   p=getattr(mod,'__file__',None)
   if p and Path(p).is_file() and Path(p).resolve().is_relative_to(R) and str(p).endswith('.py'):pin(p)
  for p in (R/'reports/m4-constructor-native/source-comparison-preparation-r1/report.json',R/'reports/m4-138-validation-review/constructor-source-dependency-review-r8/report.json'):
   receipt=json.loads(pin(p).read_bytes())
   for f,h in receipt.get('files',{}).items():pin(f,h)
  passed=True
 except Exception as e:(out/'failure.txt').write_text(repr(e)+'\n')
 report=dict(passed=passed,source_program_instructions=len(program)if 'program'in locals()else 0,persistent138_instructions_preserved=len(old)if 'old'in locals()else 0,source_callback_rows=len(callbacks)if 'callbacks'in locals()else 0,same_machine_widget_and_constructor=True,phase_BEFORE_inputs_accepted=False,AFTER_machine_seed=False,canonical_reader_opened=False,native_executed=False,full141_consumer_prepared=False,constructor_shared_API_owner_role_policy_review_pending=True,complete_carried_context_proof=False,initializer_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(hashlib.sha256((out/'report.json').read_bytes()).hexdigest());return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
