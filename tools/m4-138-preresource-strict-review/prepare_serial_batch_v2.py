"""Immutable dependency-only current builder4/checker5 serial-controller binding."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-preresource-strict-review/serial-batch-preparation-r2';assert not out.exists();out.mkdir()
 parent=R/'tools/m4-138-preresource-strict-review/serial_batch_v1.py';s=parent.read_text();d=[]
 def change(a,b,n=1):
  nonlocal s
  assert s.count(a)==n;s=s.replace(a,b);d.append(dict(before=a,after=b,count=n))
 builder=R/'tools/m4-138-preresource-strict-review/root_admission_builder_v4.py';bp=R/'reports/m4-138-preresource-strict-review/admission-builder-preparation-r4/report.json';checker=R/'reports/m4-138-preresource-strict-review/preparation-r5/verify_case_v5.py'
 change('e981fb6f993bd87a4b349a0c06cc1c18bb30a80befe95fcdee36b10f43f1ca16',sha(builder))
 change('3d3d14f27b5634666b3edacfbf99f95a2e9e970ea66750face2be4ab4b1a86f2',sha(bp))
 change('serial-batch-preparation-r1','serial-batch-preparation-r2')
 change('root_admission_builder_v3.py','root_admission_builder_v4.py')
 change('root-admission-builder-preparation-r3/report.json','admission-builder-preparation-r4/report.json')
 change('preparation-r4/verify_case_v4.py','preparation-r5/verify_case_v5.py')
 inverse=s
 for h in reversed(d):assert inverse.count(h['after'])==h['count'];inverse=inverse.replace(h['after'],h['before'])
 assert inverse==parent.read_text();ast.parse(s);q=parent.with_name('serial_batch_v2.py');assert not q.exists();q.write_text(s)
 old=R/'reports/m4-138-preresource-strict-review/serial-batch-preparation-r1';manifest=(old/'raw-case-manifest.json').read_bytes();assert hashlib.sha256(manifest).hexdigest()=='4236a3d22a13529d94106f909833c62229b70f30395622eb58549c54bce38e18';(out/'raw-case-manifest.json').write_bytes(manifest)
 (out/'exact-deltas.json').write_text(json.dumps(d,indent=2)+'\n')
 required=json.loads((old/'ROOT-admission-required-fields.json').read_bytes());required['preparation_sha256']='Exact current serial-batch-preparation-r2/report.json hash';required['checker5_exact_admission_pin_exception_review_required']=True;required['builder4_whole_closure_and_checker5_inverse_review_required']=True;required['mode7_full_strict_success_pending']=True
 (out/'ROOT-admission-required-fields.json').write_text(json.dumps(required,indent=2)+'\n')
 (out/'ROOT-recipe.txt').write_text(f'ROOT inspect/admit builder4/checker5/controller2 first. No author launches.\nDo not proceed until a fresh full strict O0mode7 passed receipt is physically independently verified; old failed9c1400 and schema-only receipts cannot substitute.\nC:/Python314/python.exe {q} <ROOT-controller-admission-report> <admissionSHA> <fresh-batch-name> <fresh-passed-mode7-strict-report> <mode7-strictSHA>\nScope/admission fields defined in ROOT-admission-required-fields.json. Full raw manifest is byte-identical to preparation1,23remaining cases each receive one fresh builder4 admission plus one strict checker5, serial fail-stop. Acceptance/aggregation remain separate.\n')
 files={str(p):sha(p)for p in(parent,q,builder,bp,checker,Path(__file__),old/'report.json',out/'raw-case-manifest.json',out/'exact-deltas.json',out/'ROOT-admission-required-fields.json',out/'ROOT-recipe.txt',R/'reports/m4-138-preresource-strict-review/preparation-r5/report.json',R/'reports/m4-138-preresource-strict-review/preparation-r2/ordinary_case_v2.py')}
 (out/'report.json').write_text(json.dumps(dict(passed=True,scope='Unexecuted exact6 dependency substitutions only; ROOT approval and fresh full strict mode7 success required before remaining23 serial checks',whole_parent_inverse=True,exact_hunks=6,strict_checker_sha256=sha(checker),production_sha256='59fbbf6c9da98b54b2bf84fe7ee7582557b789ab73260255822ca93206b9c69f',raw_manifest_whole_unchanged=True,actual_raw_cases=24,remaining_case_count=23,prior_mode7_full_strict_success_pending=True,controller_executed=False,builder_executed=False,checker_executed=False,native_worker_executed=False,capture_reader_opened=False,configuration_created=False,accepted_function_credit=0,initializer_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(report_sha256=sha(out/'report.json'),controller_sha256=sha(q))))
if __name__=='__main__':main()
