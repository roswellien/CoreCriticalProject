"""Correct current FPS bootstrap namespace from physical component4, preserving v1."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-preresource-strict-review/preparation-r2';assert not out.exists();out.mkdir()
 parent=R/'tools/m4-138-preresource-strict-review/ordinary_case.py';s=parent.read_text();deltas=[]
 def change(a,b):
  nonlocal s
  assert s.count(a)==1;s=s.replace(a,b);deltas.append(dict(before=a,after=b))
 change("counts['whole_widget_retry_fields']=retry_scope(a,stem+'Widget/pre-resource-retry-before/',stem+'Widget/pre-resource-retry-after/',('State.bin','CPU.bin','FX.bin','status.bin','accesses.bin','APIs.bin','fonts.bin','TIB.bin','stack.bin'))", "counts['whole_widget_public_retry_fields']=retry_scope(a,stem+'Widget/pre-resource-retry-before/',stem+'Widget/pre-resource-retry-after/',('State.bin','CPU.bin','FX.bin','TIB.bin','stack.bin'))\n counts['whole_widget_private_retry_fields']=retry_scope(a,stem+'Widget/bootstrap/pre-resource-retry-before/',stem+'Widget/bootstrap/pre-resource-retry-after/',('State.bin','CPU.bin','FX.bin','status.bin','accesses.bin','APIs.bin','fonts.bin','formats.bin','format-dispatches.bin'))")
 change("'virtuals.bin','arrays.bin','imports.bin')", "'virtuals.bin','arrays.bin','imports.bin','formats.bin','format-dispatches.bin')")
 change("stem+'Widget/pre-resource-retry-before/'+k", "stem+'Widget/bootstrap/pre-resource-retry-before/'+k")
 change("stem+'Widget/cleaned/status.bin'", "stem+'Widget/bootstrap/cleaned/status.bin'")
 change("stem+'Widget/cleaned/fonts.bin'", "stem+'Widget/bootstrap/cleaned/fonts.bin'")
 inverse=s
 for d in reversed(deltas):assert inverse.count(d['after'])==1;inverse=inverse.replace(d['after'],d['before'])
 assert inverse==parent.read_text();ast.parse(s);helper=out/'ordinary_case_v2.py';helper.write_text(s)
 old=R/'reports/m4-138-preresource-strict-review/preparation-r1/verify_case_v1.py';t=old.read_text();a="ROOT/'tools/m4-138-preresource-strict-review/ordinary_case.py'";b="ROOT/'reports/m4-138-preresource-strict-review/preparation-r2/ordinary_case_v2.py'";assert t.count(a)==1;t=t.replace(a,b);assert t.replace(b,a)==old.read_text();ast.parse(t);checker=out/'verify_case_v2.py';checker.write_text(t)
 physical=R/'reports/m4-fps-native/connected-component-preparation-r4/component.cpp';body=physical.read_text();assert 'root?"root-"+std::to_string(root->root)+"/":"bootstrap/"'in body
 (out/'exact-deltas.json').write_text(json.dumps(deltas,indent=2)+'\n')
 files={str(p):sha(p)for p in(parent,old,helper,checker,physical,Path(__file__),out/'exact-deltas.json')}
 (out/'report.json').write_text(json.dumps(dict(passed=True,scope='Current physically compiled FPS bootstrap private vs whole-runtime public namespace binding; exact5 helper changes plus1 checker helper-path substitution',whole_helper_inverse=True,whole_checker_inverse=True,semantic_rules_unchanged=True,runtime_checker_executed=False,worker_executed=False,accepted_function_credit=0,initializer_credit=0,files=files),indent=2)+'\n');print(sha(out/'report.json'))
if __name__=='__main__':main()
