"""Prepare only; no live batch report/payload/ordinary union enumeration."""
from pathlib import Path
import ast,hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-138-preresource-strict-review/aggregate-admission-preparation-r1';assert not out.exists();out.mkdir()
 tool=R/'tools/m4-138-preresource-strict-review/root_aggregate_admission_v1.py';ast.parse(tool.read_text());aggregate=R/'tools/m4-138-preresource-strict-review/aggregate_v1.py';ast.parse(aggregate.read_text());assert sha(aggregate)=='e864cb2228d33944cf3dc55beb84d6c83da55fb9bcda1d687516d0ad662562cb'
 recipe=f'''ROOT only after independently inspecting admission tool and terminal24strict batch.
Do not invoke while batch incomplete. Author did not read live batch, launch workers/checkers/readers, or enumerate raw output inventories.
C:/Python314/python.exe {tool} <terminal-passed-serial-batch2-report> <exact-batchSHA> <fresh-root-aggregate-admission-name> <fresh-aggregate-name>
Tool requires actual24 typed distinct strict receipts, exact current raw manifest+each raw/source/admission filemap, exactly46 successful ordinary child commands, current checker5/code pins, all actual denial/retry/frame64/caller fields, and false hidden Runtime/private/permission claims.
Whole union uses a disk SQLite index and streamed standard files map: one case JSON/physical file at a time. This tool is intended to run after batch is sealed; no active output writer is consumed.
Then ROOT inspect terminal admission report + whole-ordinary-union.json and exact24 aggregate-manifest.json before running emitted aggregate_v1.py command. Whole union receipt supplements every actual raw/admission/source leaf rather than only report metadata.
No accepted-function/initializer credit, authoritative allowances, configuration or acceptance invocation. The existing aggregate remains immutable and unexecuted by this tool.
'''
 (out/'ROOT-recipe.txt').write_text(recipe)
 files={str(p):sha(p)for p in(tool,aggregate,Path(__file__).resolve(),out/'ROOT-recipe.txt',R/'reports/m4-138-preresource-strict-review/serial-batch-preparation-r2/report.json',R/'reports/m4-138-preresource-strict-review/preparation-r5/report.json',R/'reports/m4-138-preresource-strict-review/admission-builder-preparation-r4/report.json')}
 result=dict(passed=True,scope='Unexecuted ROOT aggregate admission tooling; future terminal24 evidence required. No live batch or full inventory consumed',AST_only_checked=True,current_case_count_not_inferred=True,required_actual_typed_case_count=24,required_precise_denials=24,required_unchanged_poisoned_retries=24,required_real_entryframe64_checks=24,required_fullcaller_FX512_ENV28_checks=48,required_named_source_TLS_API_CPU_frame_joins=4,dependency_union_backend='bounded disk SQLite plus streamed whole ordinary files-map JSON',live_batch_report_opened=False,raw_inventory_enumerated=False,admission_tool_executed=False,aggregate_executed=False,checker_executed=False,worker_executed=False,capture_reader_opened=False,hidden_Runtime_map_equality_claim=False,hidden_private_equality_claim=False,permission_map_equality_claim=False,accepted_function_credit=0,initializer_credit=0,files=files)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(report_sha256=sha(out/'report.json'),tool_sha256=sha(tool))))
if __name__=='__main__':main()
