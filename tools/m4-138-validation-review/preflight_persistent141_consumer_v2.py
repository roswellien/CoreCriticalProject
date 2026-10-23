"""Ordinary import/API wiring preflight. Never constructs a capture reader."""
from pathlib import Path
import ast, hashlib, importlib.util, inspect, json, sys, traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'reports/m4-startup141-source/consumer-wiring-preflight-r1'
 assert not out.exists();out.mkdir(parents=True);pins={};passed=False;checks=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,h,v)
  assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def load(n,p):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  prep=R/'reports/m4-startup141-source/preparation-r2/report.json'
  receipt=json.loads(pin(prep).read_bytes());assert receipt['passed'] and receipt['exact_parent_inverse'] and receipt['canonical_reader_opened']is False
  for p,h in receipt['files'].items():pin(p,h)
  p=Path(receipt['entrypoint']);tree=ast.parse(pin(p).read_text());D=load('preflight141_consumer',p)
  # Every module attribute directly referenced by the main driver must exist.
  module_names={n for n,v in vars(D).items()if inspect.ismodule(v)}
  for node in ast.walk(tree):
   if isinstance(node,ast.Attribute) and isinstance(node.value,ast.Name) and node.value.id in module_names:
    module=getattr(D,node.value.id);assert hasattr(module,node.attr),(node.lineno,node.value.id,node.attr)
  checks.append('Every statically referenced imported module attribute exists')
  for name,count in (('checkpoint_index',2),('install_widget_observer',1),('constructor_phase',7),('partition_normal_FS',2),('prove_constructor_projections',2)):
   f=getattr(D.F,name);inspect.signature(f).bind(*[None]*count)
  inspect.signature(D.F.configure).bind(*[None]*6)
  inspect.signature(D.A.audit).bind(*[None]*3)
  checks.append('All new observer/continuity interface signatures bind exact driver arguments')
  C=load('preflight141_carried_models',R/'tools/m4-native141-source/persistent_constructors_v4.py')
  program,callbacks=C.source_program();old,oldcallbacks=C.G.source_program()
  assert len(program)==8480 and len(callbacks)==475
  for pc,row in old.items():assert (program[pc]['width'],program[pc]['bytes_hex'],program[pc]['decoded_operands'])==(row['width'],row['bytes_hex'],row['decoded_operands'])
  for pc,row in oldcallbacks.items():assert callbacks[pc]==row
  assert all(root in program for root in C.ROOTS)
  for name in ('begin_widget','end_widget','begin_constructor','end_constructor','run_carried_constructor','synchronize_constructor_owners','admit_constructor_imports'):
   assert callable(getattr(C.Machine,name))
  checks.append('Merged8480 physical instruction rows/475 callbacks retain every inherited source row and widget interface')
  NI=load('preflight141_normalized_execution',R/'tools/m4-native141-source/execution_input_v1.py')
  current=NI.load(R/'reports/m4-startup141-root/execution-r2/report.json',R/'reports/m4-startup141-root/validation-r1/report.json','00406b1d901fe996e0d15f9281048ff6222d6bae5ceaf1d3e721b5d0f271d610',pin)
  build=json.loads(pin(current['build_path'],current['build_sha256']).read_bytes())
  prepared=json.loads(pin(build['preparation'],build['preparation_sha256']).read_bytes())
  assert len(prepared['selected_order'])==141
  legacy=json.loads(pin(R/'reports/m4-joint-startup138/preparation-r4/report.json','a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a').read_bytes())
  assert [row for row in prepared['selected_order']if row['entry']not in C.ROOTS]==legacy['selected_order']
  assert [prepared['selected_order'][n]['entry']for n in(13,14,39)]==list(C.ROOTS)
  checks.append('Actual O0/O2 writer and closed strict gate exact bindings; removing only3 constructor slots recovers complete138 schedule')
  assert not any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=='main'for n in ast.walk(tree))
  # Import/source_program calls above read ordinary physical contracts only.
  # No DirectSet construction or Export.copy call is made by this preflight.
  for mod in tuple(sys.modules.values()):
   path=getattr(mod,'__file__',None)
   if path and Path(path).is_file()and Path(path).resolve().is_relative_to(R)and str(path).endswith('.py'):pin(path)
  for source in (R/'reports/m4-constructor-native/source-comparison-preparation-r1/report.json',R/'reports/m4-138-validation-review/constructor-source-dependency-review-r8/report.json'):
   bound=json.loads(pin(source).read_bytes())
   for path,h in bound.get('files',{}).items():pin(path,h)
  pin(__file__);passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc())
 report=dict(passed=passed,checks=checks,prepared_only=True,consumer_executed=False,canonical_reader_opened=False,worker_launched=False,whole_source_equivalence=False,initializer_credit=0,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(sha(out/'report.json'));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
