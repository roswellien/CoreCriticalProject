"""Freeze actual production rows and unexecuted strict serial controller."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-preresource-strict-review/serial-batch-preparation-r1';assert not out.exists();out.mkdir()
 p=R/'reports/m4-138-preresource-root-review/root-case-production-r1/report.json';ph='59fbbf6c9da98b54b2bf84fe7ee7582557b789ab73260255822ca93206b9c69f';assert sha(p)==ph
 v=json.loads(p.read_bytes());assert v['passed']and v['raw_cases']==24 and v['all_workers_terminal']and not v['strict_outcomes_verified']
 rows=v['runs'];assert len(rows)==24 and [(r['level'],r['mode'])for r in rows]==[(l,m)for l in('O0','O2')for m in range(1,13)]
 assert len({r['report']for r in rows})==24
 manifest=dict(production=str(p),production_sha256=ph,runs=rows,scope='Exact sealed actual raw case path/digest rows; no strict outcomes inferred')
 (out/'raw-case-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 controller=R/'tools/m4-138-preresource-strict-review/serial_batch_v1.py';ast.parse(controller.read_text())
 builder=R/'tools/m4-138-preresource-strict-review/root_admission_builder_v3.py';assert sha(builder)=='e981fb6f993bd87a4b349a0c06cc1c18bb30a80befe95fcdee36b10f43f1ca16'
 bp=R/'reports/m4-138-preresource-strict-review/root-admission-builder-preparation-r3/report.json';assert sha(bp)=='3d3d14f27b5634666b3edacfbf99f95a2e9e970ea66750face2be4ab4b1a86f2'
 checker=R/'reports/m4-138-preresource-strict-review/preparation-r4/verify_case_v4.py'
 roots=[controller,builder,bp,checker,Path(__file__).resolve(),p,out/'raw-case-manifest.json',R/'reports/m4-138-preresource-strict-review/preparation-r4/report.json',R/'reports/m4-138-preresource-strict-review/preparation-r2/ordinary_case_v2.py',R/'reports/m4-138-preresource-strict-review/schema-preflight-r2/report.json']
 needs=dict(scope_identity='current138_preresource_serial_strict_remaining23',passed='ROOT must independently inspect code and mint this Boolean only if admitted',no_native_workers=True,no_archive_readers=True,preparation_sha256='Exact current serial-batch-preparation-r1/report.json hash',mode7_strict_report='Exact independently passed current O0mode7 full strict receipt path',mode7_strict_sha256='Exact full strict receipt hash; never old failed or schema-only receipt',files='All preparation.files, all24 exact raw receipt paths/digests below, actual Python interpreter and passed mode7 full strict receipt. No speculative whole raw success collapse.',raw_receipts=[dict(path=r['report'],sha256=r['sha256'])for r in rows],python=str(Path(sys.executable).resolve()))
 (out/'ROOT-admission-required-fields.json').write_text(json.dumps(needs,indent=2)+'\n')
 (out/'ROOT-recipe.txt').write_text(f'ROOT inspect/admit serial_batch_v1.py first. Author has not executed controller, builder, checker or native worker.\nWait for complete strict O0mode7 success, then independently seal scope current138_preresource_serial_strict_remaining23 per ROOT-admission-required-fields.json.\nC:/Python314/python.exe {controller} <ROOT-controller-admission-report> <admissionSHA> <fresh-batch-name> <passed-mode7-strict-report> <mode7-strictSHA>\nEach of23remaining cases uses exact sealed raw report/hash; independent builder3 then strict checker4 serially. All future namespaces checked fresh before first child. First failed child stops entire controller and preserves logs; no automatic retries/no failed-receipt reuse.\nController report records24passedcase receipt identities. ROOT must still independently admit actual all24 aggregation manifest before aggregate_v1.py, and acceptance remains separate.\n')
 roots.extend([out/'ROOT-admission-required-fields.json',out/'ROOT-recipe.txt'])
 result=dict(passed=True,scope='Unexecuted ROOT-admission-required exact23 serial ordinary admission/strict checker controller with one prior complete strict mode7',production_sha256=ph,actual_raw_cases=24,remaining_case_count=23,strict_checker_sha256=sha(checker),fresh_admissions_required=23,fresh_strict_checks_required=23,prior_mode7_full_strict_receipt_required=True,case_row_identities_from_sealed_production=True,raw_receipt_bodies_opened=False,AST_only_checked=True,controller_executed=False,builder_executed=False,checker_executed=False,native_worker_executed=False,capture_reader_opened=False,root_controller_admission_created=False,configuration_created=False,accepted_function_credit=0,initializer_credit=0,files={str(q):sha(q)for q in roots})
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),controller_sha256=sha(controller),manifest_sha256=sha(out/'raw-case-manifest.json'))))
if __name__=='__main__':main()
