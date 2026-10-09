"""Seal a read-only review of the final root verifier and its bounded claims."""
import ast,json,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import normalized,unique_object,verify_manifest
from paths import publish_bytes
WATCHED=('tools/m4-crt-heap-return-root/accept.py','tools/m4-crt-heap-return-root/create_config.py',
 'tools/m4-crt-heap-return-root/final_check.py','docs/m4-progress-heap-return.md',
 'docs/m4-crt-heap-return-review.md','tools/m4-crt-heap-return-root/README.md',
 'tools/m4-crt-heap-return/README.md','tools/m4-crt-heap-return-review/README.md',
 'tools/m4-crt-heap-return-recovery/README.md','tools/m4-crt-heap-return-root-audit/README.md',
 'tools/m4-crt-heap-return-root-audit/README-final.md')
AUTHOR_SHA='c80e2a7b3317673dcfe660c2c8ef6a54b6080e83f61418423379c2fec3d401a0'
ORIGINAL_SHA='7e1c25565468f3d286e8262076825e616bd24c10b9ce1665fa06237a1be8d52b'
CORRECTION_SHA='9f74b0ff818a83d37ef60888289efd98c3d0bab0024798ce87448ad6e758a35a'
FINAL_VERIFIERS=(
 '048d4b11df63ae24026835fcc92bf7d7d8df7a604730a0c8d2f6454ec9354c75',
 '0821bc592e1c06930dcd5677d2a4e12a93410a628f7c6707b3e475de20936589',
 'be8b726f21659c689e80efa003de31b8a474cafc7245b20bd213e50e0a38f215')
def read(p):return json.loads(Path(p).read_bytes(),object_pairs_hook=unique_object)
def main():
 started=time.perf_counter_ns();out=ROOT/'reports/m4-crt-heap-return-acceptance-review/review-r1'
 assert not out.exists()
 paths=[ROOT/p for p in WATCHED]
 for p,h in zip(paths[:3],FINAL_VERIFIERS):
  assert sha_file(p)==h
  ast.parse(p.read_text(),filename=str(p))
 author=ROOT/'reports/m4-crt-heap-return/execution-r2/report.json'
 original=ROOT/'reports/m4-crt-heap-return/execution-r1/report.json'
 correction=ROOT/'reports/m4-crt-heap-return/counts-correction-r1/report.json'
 assert sha_file(author)==AUTHOR_SHA and sha_file(original)==ORIGINAL_SHA and sha_file(correction)==CORRECTION_SHA
 a,b,c=read(author),read(original),read(correction)
 assert a['passed'] and a['levels']==b['levels'] and a['native_stages_completed']==b['native_stages_completed']==2
 assert a['corrected_from_execution_sha256']==ORIGINAL_SHA and a['rollup_correction_sha256']==CORRECTION_SHA
 assert a['actual_source_mode_publication_sequences']==c['actual_source_mode_publication_sequences']==68
 assert b['actual_source_mode_publication_sequences']==c['original_public_flag_count']==70
 assert c['intentional_public_flag_forgery_sequences']==2 and c['controls']==[158]
 assert a['genuine_initializer_RET_sequences']==c['genuine_initializer_RET_sequences']==52
 assert a['native_rerun'] is False and a['new_native_execution_credit'] is False
 text=paths[0].read_text()
 for word in ('corrected_from_execution_sha256','rollup_correction_sha256','native_rerun','new_native_execution_credit',
              'initializer','source_identity','artifact_sha256','worker_sha','fixture_objects','COMPLETE',
              "claim['files']==actual_part",'byte_identical_copies_only','partition_tool_sha256',
              'Exact whole-case partition assignment and separate diagnostics'):
  assert word in text,word
 files={normalized(str(p)):sha_file(p)for p in [*paths,author,original,correction,Path(__file__).resolve(),Path(sys.executable)]}
 closure=verify_manifest(files)
 report=dict(passed=True,scope='Independent read-only final root verifier/provenance/documentation review; no root acceptance or native execution performed by this reviewer',
  source_only_review=True,native_executed=False,no_native_executed=True,original_or_game_executed=False,whole_M4_complete=False,
  reviewed_files=list(WATCHED),files=files,physical_closure=closure,
  findings=[dict(issue='Corrected author rollup provenance required explicit validation beyond transitive file closure',
   disposition='Resolved in final root acceptance verifier before configuration freeze'),
   dict(issue='Actual per-part archive inventories and case sets required association with partition claims in addition to the whole disjoint union',
   disposition='Resolved in final root acceptance verifier before configuration freeze')],
  remaining_concrete_blockers=0,
  author_execution_sha256=AUTHOR_SHA,uncorrected_rollup_history_sha256=ORIGINAL_SHA,correction_receipt_sha256=CORRECTION_SHA,
  source_identity_bytes=2086,reused_guest_COFFs=38,unchanged_FDIV_libraries=2,source_PCs=59,source_accesses=35,
  source_CALLs=5,genuine_source_RETs=3,executed_source_bytes=192,full_pages=21,ordinary_checkpoints=44,
  same_immutable_archives_workers_stages_confirmed=True,correction_native_rerun=False,
  initializer_mode1_return_credit_bounded=True,fragment_caller_continued=False,full_CRT_or_allocator_credit=False,
  universal_original_API_or_AF_equivalence_credit=False,in_game_native_launch_credit=False,
  reviewer_native_execution_count=0,full_causal_model_execution_credit=False,seconds=(time.perf_counter_ns()-started)/1e9)
 out.mkdir(parents=True)
 publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
 files[str(out/'report.json')]=sha_file(out/'report.json')
 publish_bytes(out/'pins.json',(json.dumps(dict(files=files),indent=2)+'\n').encode())
 print(json.dumps(dict(passed=True,report_sha256=sha_file(out/'report.json'),pins_sha256=sha_file(out/'pins.json'))))
if __name__=='__main__':main()
