"""Authenticate actual pre-audit helper identities without opening captures."""
from pathlib import Path
import ast,hashlib,importlib.util,json,sys,traceback
R=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-141-consumer-review/closure-controls-r1';assert not out.exists();out.mkdir(parents=True)
 pins={};checks=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v
  assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def reject(name,fn):
  try:fn()
  except (ValueError,AssertionError):checks.append(dict(name=name,rejected=True));return
  raise AssertionError('Expected rejection '+name)
 try:
  p=pin(R/'tools/m4-native141-source/final_observer141_v7.py')
  s=importlib.util.spec_from_file_location('review_pre_audit_observer7',p);F=importlib.util.module_from_spec(s);s.loader.exec_module(F)
  value=F.pin_current_inputs(pin);assert value['pinned_before_capture_open']and value['AFTER_seed']is False
  helpers=('constructor_journal141_v2.py','constructor_native_outputs141_v2.py','constructor_fs_union141_v1.py')
  assert all(str((R/'tools/m4-native141-source'/n).resolve())in pins for n in helpers)
  checks.append(dict(name='All three executed helper modules bind exact sealed paths/hashes before captures',passed=True))
  for helper in helpers:
   def refuse(path,h=None):
    if Path(path).name==helper:raise ValueError('Synthetic changed helper hash')
    return pin(path,h)
   reject('Changed helper hash refused: '+helper,lambda:F.pin_current_inputs(refuse))
  module=sys.modules[F.Association.__module__];old=module.__file__;module.__file__=str(R/'tools/m4-native141-source/constructor_journal141_v1.py')
  try:reject('Loaded helper identity outside declared sealed module refused',lambda:F.pin_current_inputs(pin))
  finally:module.__file__=old
  text=pin(R/'reports/m4-startup141-source/preparation-r4/compare_provider141.py').read_text();tree=ast.parse(text)
  main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
  current_calls=[n for n in ast.walk(main)if isinstance(n,ast.Call)]
  closure=next(n for n in current_calls if isinstance(n.func,ast.Attribute)and isinstance(n.func.value,ast.Name)and n.func.value.id=='F'and n.func.attr=='pin_current_inputs')
  readers=[n for n in current_calls if isinstance(n.func,ast.Attribute)and n.func.attr=='DirectSet']
  assert len(readers)==2 and all(closure.lineno<n.lineno for n in readers)
  checks.append(dict(name='Explicit current observer closure call precedes both original/native DirectSet constructions',passed=True))
  add=json.loads(pin(R/'reports/m4-141-consumer-review/closure-preparation-r2/observer-addition.json').read_bytes());assert len(add)==1
  assert p.read_text()==pin(add[0]['parent']).read_text()+add[0]['added']
  checks.append(dict(name='Observer7 retains entire observer5 semantic body; append-only closure function',passed=True))
  for source in (R/'reports/m4-141-consumer-review/closure-preparation-r2/report.json',R/'reports/m4-141-consumer-review/closure-wiring-r1/report.json',R/'reports/m4-141-consumer-review/review-r4/report.json'):
   d=json.loads(pin(source).read_bytes());assert d['passed']
   for path,h in d['files'].items():pin(path,h)
  pin(__file__);passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc())
 (out/'report.json').write_text(json.dumps(dict(passed=passed,checks=checks,canonical_reader_opened=False,consumer_executed=False,admitted=False,ROOT_independent_admission_required=True,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(out/'report.json'));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
