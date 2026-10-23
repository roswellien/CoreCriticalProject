"""ROOT independent finite source admission; no model import or reader launch."""
from pathlib import Path
import ast, hashlib, json, sys, time
R=Path(__file__).resolve().parents[2]
def main(closure_path,closure_sha,name):
 started=time.monotonic();files={};out=R/'reports/m4-original141-source'/name;assert not out.exists()
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json'
  if not p.is_relative_to(R):
   assert any(p.is_relative_to(q)for q in (Path(sys.prefix).resolve(),Path('C:/Program Files/Microsoft Visual Studio/18/Community'),Path('C:/Program Files (x86)/Windows Kits/10')))or p in {Path('C:/Users/jcbla/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe'),*(Path('C:/Windows/SysWOW64')/n for n in ('kernel32.dll','ntdll.dll','apphelp.dll','gdi32.dll','user32.dll'))}or(p.parent==Path('G:/Projects/MW34Recomp-Captures/reports/m4-original141/root-capture-validation-r3/paired-exports/original')and p.name in('index.json','payload.bin'))
  with p.open('rb')as f:v=hashlib.file_digest(f,'sha256').hexdigest()
  assert h is None or h==v,(str(p),h,v);assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 base=R/'reports/m4-original141-source';closure=read(closure_path,closure_sha)
 assert closure['prepared_only']and not closure['source_execution']and not closure['ROOT_admission_minted']
 for p,h in closure['files'].items():pin(p,h)
 required=read(closure['required_ordinary_files'],closure['required_ordinary_files_sha256'])
 for p,h in required.items():pin(p,h)
 configpath=base/'configuration-preparation-r3/configuration.json';configsha='451d19e8a30e68cb76e266ef00df3c080c19ea590a091a2a8a072b4f5123f5b0'
 C=read(configpath,configsha);assert closure['configuration_sha256']==configsha
 checks=[]
 for rel,h in [('root-static-review-r1','574a1bed7b48de0d6cc706772495a8d493aff216c7e2331326f14f4df81c697b'),('root-cleanup-review-r1','56aae8864b3c31d11542f733c673deed5b00767b5f759f369442517aa0187fe9'),('root-causal-controls-r2','993d5215f9d0207d0e8aaa2f9f1f6f87099a053493be8c95b63b400c19de141b'),('root-current-inputs-r3','2c0269ded635cd63be7a417664f9254ee54920334391a7fdcd80ab5914feffbb')]:
  q=read(base/rel/'report.json',h);assert q['passed']is True
  for p,v in q['files'].items():pin(p,v)
  checks.append(dict(path=str(base/rel/'report.json'),sha256=h))
 control=read(base/'root-causal-controls-r2/report.json');assert len(control['tests'])==32
 tree=read(C['current_tree_source']['path'],C['current_tree_source']['sha256']);assert tree['passed']and tree['source_case_extent']==6 and tree['ordinary_reader_closed']and not tree['source_AFTER_seed']
 for p,h in tree['files'].items():pin(p,h)
 callbacks=read(C['callbacks']['path'],C['callbacks']['sha256']);assert len(callbacks['rows'])==111
 # Entire configuration code was independently read. Verify both exact edits
 # invert to that reviewed parent; actual111 byte predicates ran in preparation.
 parent=pin(R/'tools/m4-original141-source/prepare_configuration_v1.py').read_text()
 v2=pin(R/'tools/m4-original141-source/prepare_configuration_v2.py').read_text()
 v3=pin(R/'tools/m4-original141-source/prepare_configuration_v3.py').read_text()
 a=next(x for x in parent.splitlines()if x.startswith('  fact=authority[key];'))
 b='\n'.join(x for x in v2.splitlines()if x.startswith('  fact=authority[key];')or x.startswith('  assert wrapper=='))
 assert v2.count(b)==1 and v2.replace(b,a)==parent
 old='assert wrapper==5947712 and push_pc==call_pc-5 and return_pc==call_pc+5';new='assert wrapper==5947712 and push_pc<call_pc and return_pc==call_pc+5'
 assert v3.count(new)==1 and v3.replace(new,old)==v2
 for p in (R/'tools/m4-original141-source/replay_original141_v3.py',R/'tools/m4-original141-source/prepare_replay_closure_v1.py',Path(__file__)):
  ast.parse(pin(p).read_text())
 prep=read(base/'configuration-preparation-r3/report.json','b6c9ca69610a7752897ffb3396b2c192e78627e978a2863e9673e657f6c2cf9e')
 assert prep['current_callback_literal_PUSH_CALL_pairs']==111 and prep['configuration_sha256']==configsha
 for p,h in prep['files'].items():pin(p,h)
 pin(sys.executable)
 for p,h in list(files.items()):pin(p,h)
 out.mkdir();q=out/'report.json';q.write_text(json.dumps(dict(passed=True,independent_review=True,scope_identity='original141_finite_source_replay',configuration_sha256=configsha,checks=checks,source_execution=False,reader_opened=False,native_worker_launched=False,initializer_credit=0,accepted_function_credit=0,elapsed_seconds=time.monotonic()-started,files=files),indent=2)+'\n')
 print(json.dumps(dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),files=len(files))))
if __name__=='__main__':main(*sys.argv[1:])
