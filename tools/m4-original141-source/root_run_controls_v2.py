"""ROOT admits complete ordinary closure then runs32 finite causal controls."""
from pathlib import Path
import hashlib,importlib.util,json,sys,time,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def main(name):
 started=time.monotonic();out=R/'reports/m4-original141-source'/name;assert not out.exists();files={};reads=set()
 def sha(p):
  with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
 def initial(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or v==h
  assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 base=R/'reports/m4-original141-source/root-control-closure-r2'
 closure=json.loads(initial(base/'report.json','5ed93baec69aba19626331754c3f1f86fe075fe964e92ce2ccbf33fb736dcdaa').read_bytes())
 for p,h in closure['files'].items():initial(p,h)
 required=json.loads(initial(base/'required-ordinary-files.json','4d0cde1b02c114bfc29ec79356b9e21b8d23dbed6aaa4c6957b0d09ae3d44fe9').read_bytes())
 for p,h in required.items():initial(p,h)
 for p,h in [('root-static-review-r1','574a1bed7b48de0d6cc706772495a8d493aff216c7e2331326f14f4df81c697b'),('root-cleanup-review-r1','56aae8864b3c31d11542f733c673deed5b00767b5f759f369442517aa0187fe9')]:initial(R/'reports/m4-original141-source'/p/'report.json',h)
 initial(__file__);initial(sys.executable)
 tool=R/'tools/m4-original141-source/source_controls141_v1.py'
 assert required[str(tool)]=='a981990cd3191bd0f213e60fab97dbcbf59f5c6de6ad8ab174eb3df28ff59dea'
 out.mkdir();gate=dict(passed=True,independent_review=True,scope_identity='original141_bounded_source_controls',source_endpoint_execution_admitted=False,expected_controls=32,files=dict(files));(out/'ROOT-admission.json').write_text(json.dumps(gate,indent=2)+'\n')
 inside=False
 def audit(event,args):
  nonlocal inside
  if event!='open'or inside or not isinstance(args[0],(str,bytes)):return
  p=Path(args[0]).resolve();mode=args[1];flags=args[2]
  writing=isinstance(mode,str)and any(c in mode for c in 'wax+')or isinstance(flags,int)and bool(flags&(1|2|64|512|1024))
  if writing:assert p.is_relative_to(out);return
  assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
  if p.is_relative_to(out):return
  if p.suffix.lower()=='.pyc'and p.is_relative_to(R):raise FileNotFoundError('Use admitted source')
  if not p.is_relative_to(R):return
  assert str(p)in files,'Unadmitted project read '+str(p)
  inside=True
  try:assert sha(p)==files[str(p)]
  finally:inside=False
  reads.add(str(p))
 sys.addaudithook(audit)
 def pin(p,h=None):
  p=Path(p).resolve();assert str(p)in files;assert sha(p)==files[str(p)];assert h is None or h==files[str(p)];return p
 passed=False;result={}
 try:
  spec=importlib.util.spec_from_file_location('ROOT_current141_causal_controls',pin(tool));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  result=module.controls(pin);assert result['passed']is True and len(result['tests'])==32 and result['current_original141_execution_claim']is False and result['control_fixture_original141_input']is False
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  for p,h in files.items():assert sha(p)==h
  result.update(passed=passed,scope='32 bounded causal controls; legacy fixture only, no original141 endpoint/source acceptance',all_external_project_reads_admitted_before_open=True,actual_project_reads=len(reads),elapsed_seconds=time.monotonic()-started,files=files)
  q=out/'report.json';q.write_text(json.dumps(result,indent=2)+'\n');print(sha(q))
if __name__=='__main__':main(sys.argv[1])
