"""Prepare-only record for review_completed_composite_v4; runs no production review.

Proves the exact v4 -> v3 inverse and exercises the ACTUAL v4 audit-hook source
text (extracted by AST, not retyped): a .pyc open outside the expander measured()
frame is refused, the same open inside a function carrying measured's code object
is allowed, and an empty registration refuses everything. Opens no inventory.
"""
from pathlib import Path
import ast,hashlib,json,sys,tempfile,textwrap,types
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
T=R/'tools/m4-controls-terminal-composite'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def hook_factory(source):
 """Return (hook, measured_code) built from v4's own source_only text."""
 tree=ast.parse(source);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main')
 nodes=[n for n in main.body if(isinstance(n,ast.Assign)and any(getattr(t,'id',None)=='measured_code'for t in n.targets))or(isinstance(n,ast.FunctionDef)and n.name=='source_only')]
 assert len(nodes)==2,'measured_code list and source_only hook present'
 code=textwrap.dedent('\n'.join(ast.get_source_segment(source,n)for n in nodes))
 ns={'sys':sys,'Path':Path};exec(compile(code,'v4-hook-extract','exec'),ns);return ns['source_only'],ns['measured_code']
def main():
 v3=T/'review_completed_composite_v3.py';v4=T/'review_completed_composite_v4.py';gen=Path(__file__)
 s3=v3.read_bytes().decode().replace('\r\n','\n');s4=v4.read_bytes().decode().replace('\r\n','\n')
 load_old="E=load(R/'tools/m4-controls-terminal-composite/expand_composite_inventory_v3.py','sealed_composite_expander',HELPER_SHA);"
 hook_old=(" def source_only(event,args):\n"
  "  if event=='open'and args and isinstance(args[0],(str,bytes))and Path(args[0]).suffix.lower()=='.pyc':raise FileNotFoundError('ROOT-sealed source imports; no cached bytecode')\n")
 hook_new=(" measured_code=[]\n def source_only(event,args):\n"
  "  if event=='open'and args and isinstance(args[0],(str,bytes))and Path(args[0]).suffix.lower()=='.pyc':\n"
  "   frame=sys._getframe(1)\n   while frame is not None:\n    if measured_code and frame.f_code is measured_code[0]:return\n    frame=frame.f_back\n"
  "   raise FileNotFoundError('ROOT-sealed source imports; no cached bytecode')\n")
 doc_end=s4.index('"""\n',3)+4;doc_old='"""UNEXECUTED ROOT-pre-admitted whole composite and typed45 source review."""\n'
 inverse=doc_old+s4[doc_end:]
 assert inverse.count(hook_new)==1 and inverse.count(load_old+"measured_code.append(E.measured.__code__);")==1
 inverse=inverse.replace(hook_new,hook_old).replace(load_old+"measured_code.append(E.measured.__code__);",load_old)
 assert inverse==s3,'Exact v4 -> v3 inverse (docstring, hook, registration only)'
 hook,registry=hook_factory(s4)
 controls=[]
 with tempfile.TemporaryDirectory()as d:
  pyc=Path(d)/'x.cpython-314.pyc';pyc.write_bytes(b'data')
  # 1. Import-style open (not inside measured) refused.
  def importer():hook('open',(str(pyc),'rb',0))
  try:importer()
  except FileNotFoundError:controls.append('import_style_pyc_open_refused_before_registration')
  else:raise AssertionError('pyc open admitted without registration')
  # 2. Register a function standing in for measured(); its code object is the key.
  def measured(p):hook('open',(str(p),'rb',0));return hashlib.sha256(Path(p).read_bytes()).hexdigest()
  registry.append(measured.__code__)
  assert measured(pyc)==hashlib.sha256(b'data').hexdigest();controls.append('measured_frame_pyc_data_read_allowed')
  try:importer()
  except FileNotFoundError:controls.append('import_style_pyc_open_still_refused_after_registration')
  else:raise AssertionError('import pyc admitted after registration')
  # 3. A different function with identical body text is not the registered code object.
  def impostor(p):hook('open',(str(p),'rb',0))
  try:impostor(pyc)
  except FileNotFoundError:controls.append('lookalike_function_refused')
  else:raise AssertionError('impostor admitted')
  # 4. Non-.pyc opens are untouched.
  hook('open',(str(Path(d)/'x.py'),'rb',0));controls.append('non_pyc_open_unaffected')
 out=R/'reports/m4-controls-terminal-composite/reviewer-v4-preparation-r1';assert not out.exists();out.mkdir()
 value=dict(prepared_only=True,production_review_executed=False,inventory_opened=False,defect_observed_in='reports/m4-controls-terminal-composite/completed-composite-review-r1/failure.txt',
  declared_pyc_physical_rows=['tools/analysis/__pycache__/pe.cpython-314.pyc','tools/m4-onexit-source/__pycache__/game_model.cpython-314.pyc','tools/m4-pipeline/__pycache__/manifests.cpython-314.pyc','tools/m4-pipeline/__pycache__/paths.cpython-314.pyc'],
  exact_v4_v3_inverse=True,adverse_controls=controls,accepted_function_credit=0,files={str(p.resolve()):sha(p)for p in(v3,v4,gen)})
 q=out/'report.json';q.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(dict(path=str(q),sha256=sha(q),controls=controls)))
if __name__=='__main__':main()
