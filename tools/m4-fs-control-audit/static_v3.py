"""Read-only final source admission and caller-wrapper scope review."""
from pathlib import Path
import difflib,hashlib,json,sys
R=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True;sys.path.insert(0,str(R/'tools/m4-pipeline'))
from manifests import verify_manifest
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=R/'reports/m4-fs-control-audit'/name;need(not out.exists(),'Fresh static receipt');out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Frozen source '+str(p));pins[str(p)]=v;return p
 baseline=json.loads(pin(R/'reports/m4-fs-control-audit/static-r2/report.json','a596cea39863c4454fd35135a5b4c978c32d63af4839e08c56fb5e87a36af127').read_bytes());need(baseline['passed'],'Exact earlier admitted source anchor')
 native=json.loads(pin(R/'reports/m4-fs-native/preparation-r3/report.json').read_bytes());need(native['passed'],'Final frozen derivative')
 old=pin(R/'reports/m4-fs-native/preparation-r2/fs_operations.inc').read_text();new=pin(R/'reports/m4-fs-native/preparation-r3/fs_operations.inc').read_text()
 expected=old.replace(' stable_hook(point);\n if(records!=',' const auto native_input=fs_native_input_;const auto admitted=fs_admitted_;\n stable_hook(point);\n if(records!=').replace('||raw_records!=fs_record_bytes_)','||raw_records!=fs_record_bytes_||native_input!=fs_native_input_||admitted!=fs_admitted_)')
 need(new==expected,'Final FS source derivative adds only two private immutability snapshots and equality guards')
 for name in('fs_records_','fs_active_','fs_events_','fs_probe_','fs_owner_accesses_','fs_owner_probe_','fs_publications_','fs_graphs_','fs_record_bytes_','fs_native_input_','fs_admitted_'):need(name in new[new.index('void Binding::fs_hook('):new.index('void Binding::fs_event(')],'All newly owned observer state is guarded '+name)
 need(pin(R/'reports/m4-fs-native/preparation-r2/locale_batch_operations.inc').read_bytes()==pin(R/'reports/m4-fs-native/preparation-r3/locale_batch_operations.inc').read_bytes(),'Actual write/expected/source-ledger/posthook anchor unchanged after reviewed fix')
 fixture=pin(R/'reports/m4-fs-controls/build-r5/fixture.cpp').read_text();w=fixture[fixture.index('[[clang::noinline]] unsigned invoke('):fixture.index('void dump(Context&')]
 need(w.index('ErrorBoundary errors')<w.index('NumericHostBoundary boundary')<w.index('try{')<w.index('catch(...)')<w.index('return t.okay'),'Explicit caller boundaries enclose invocation and authored catch')
 need('Naked throwing Session replay' in fixture,'Excluded naked API exception-metadata behavior documented')
 ops=pin(R/'reports/m4-fs-native/preparation-r3/session_impl.inc').read_text();body=ops[ops.index(' void replay('):ops.index(' void probe_string(')]
 need(body.index('check();')<body.index('InvocationHostBoundary host'),'Early unwrapped refusal remains outside callee hardware guarantee; fixture wrapper owns whole attempt')
 hook=pin(R/'reports/m4-fs-controls/build-r5/hooks.hpp').read_text();need('words[word]^=1' in hook and '"fs-owned-access-probe.bin"'in hook and '"fs-owned-accesses.bin"'in hook and '"fs-native-input.bin"'in hook,'Controls deliberately exercise three actual private const-view backing mutations')
 pin(__file__);dest=out/'guard.diff';dest.write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='prep2',tofile='prep3')));pin(dest)
 report=dict(passed=True,scope='Final source-only review; checked postcommit anchors unchanged, every new private FS witness/provenance field snapshotted around hooks80..87. Explicit caller numerical/error wrapper includes source calls and C++ catch. No naked throwing Session API caller ENV promise, handler/TLS path admission, or execution/initializer credit.',native_executed=False,initializer_credit=0,guarded_private_fields=11,caller_boundary_includes_catch=True,naked_throw_metadata_preservation_claimed=False,files=pins,current_physical_closure=verify_manifest(pins))
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(*sys.argv[1:])
