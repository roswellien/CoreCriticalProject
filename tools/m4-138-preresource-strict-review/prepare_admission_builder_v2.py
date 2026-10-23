"""Correct explicit-program location and empty constructor-refusal native domain."""
from pathlib import Path
import ast,hashlib,json,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-preresource-strict-review/admission-builder-preparation-r2';assert not out.exists();out.mkdir()
 parent=R/'tools/m4-138-preresource-strict-review/root_admission_builder_v1.py';s=parent.read_text();d=[]
 def change(a,b):
  nonlocal s
  assert s.count(a)==1;s=s.replace(a,b);d.append(dict(before=a,after=b))
 change("need('callbacks={}'in helper,'Caller uses explicit source program without interpreter file fallback')", "need('callbacks={}'in literal and 'program=program,callbacks={}'in literal and 'callbacks={}'in v4,'All actual source paths supply explicit program/callbacks without interpreter file fallback')")
 old=" stem=folder/f'control-{mode}/MFC';context=struct.unpack('<12Q',blob(stem/'cleaned/resource-context.bin'));count=context[11];need(0<count<=16,'Finite actual complete resource serial count')\n resource_dir=stem/'resources';need({p.name for p in resource_dir.iterdir()if p.is_dir()}=={str(n)for n in range(count)},'Exact contiguous actual resource directories')"
 new=""" stem=folder/f'control-{mode}/MFC';terminal=struct.unpack('<13I',blob(folder/f'control-{mode}/terminal-facts.bin'));need(terminal[:7]==(1,mode,0,1,1,13,13)and terminal[7]in(0,1),'Actual precise phase13/current component extent')
 resource_dir=stem/'resources'
 if terminal[7]:
  context=struct.unpack('<12Q',blob(stem/'cleaned/resource-context.bin'));count=context[11];need(0<count<=16,'Finite actual complete owned resource serial count')
  need({p.name for p in resource_dir.iterdir()if p.is_dir()}=={str(n)for n in range(count)},'Exact contiguous actual owned resource directories')
 else:
  count=0;need(not resource_dir.exists(),'Exact constructor refusal has no native owned resource event domain')"""
 change(old,new)
 # This derivative resides under tools, retaining the exact correct ROOT path.
 inverse=s
 for h in reversed(d):assert inverse.count(h['after'])==1;inverse=inverse.replace(h['after'],h['before'])
 assert inverse==parent.read_text();ast.parse(s);p=parent.with_name('root_admission_builder_v2.py');assert not p.exists();p.write_text(s)
 (out/'exact-deltas.json').write_text(json.dumps(d,indent=2)+'\n')
 e=R/'reports/m4-138-preresource-controls/execution-O0-mode7-r1/report.json';eh=sha(e)
 (out/'ROOT-recipe.txt').write_text(f'ROOT ONLY after independently inspecting complete builder2. Author did not execute admission/helper/checker.\nC:/Python314/python.exe {p} {e} {eh} root-strict-admission-O0-mode7-r1\nThen inspect report before invoking preparation-r4/verify_case_v4.py with this admission SHA.\nConstructor refusals with no Component own an empty native resource domain; others must close every actual observed native service module before imports.\n')
 files={str(q):sha(q)for q in(parent,p,Path(__file__),out/'exact-deltas.json',out/'ROOT-recipe.txt',R/'reports/m4-138-preresource-strict-review/admission-builder-preparation-r1/report.json',e)}
 (out/'report.json').write_text(json.dumps(dict(passed=True,scope='Unexecuted fail-closed current one-case ROOT ordinary admission builder; exact2code-only readiness corrections',whole_parent_inverse=True,exact_hunks=2,AST_only_checked=True,builder_executed=False,checker_executed=False,worker_executed=False,helpers_imported=False,root_admission_created=False,initializer_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(sha256=sha(out/'report.json'),builder_sha256=sha(p))))
if __name__=='__main__':main()
