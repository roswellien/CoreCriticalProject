"""Archive-free review of preserved constructor refusal and existing repair."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-138-constructor-readiness'/name
 assert not out.exists(),'Fresh review receipt'
 pins={}
 def pin(relative):
  p=(R/relative).resolve();assert p.suffix not in('.mwb','.zip');pins[str(p)]=sha(p);return p
 def read(relative):return json.loads(pin(relative).read_bytes())
 base='reports/m4-constructor-native/'
 stage=read(base+'fixture-execution-r1/O0-stage/stage.json')
 stderr=pin(base+'fixture-execution-r1/O0-stage/stderr.bin').read_text()
 assert not stage['passed']and stage['exit_code']==1
 assert 'abi_violation site=0x004103f0 target=0x004103f0' in stderr
 diagnosis=read('reports/m4-tree-review/constructor-native37-failure-r1/report.json')
 assert diagnosis['passed']and diagnosis['reader_closed']and diagnosis['initializer_credit']==0
 assert pins[str((R/'reports/m4-tree-review/constructor-native37-failure-r1/report.json').resolve())]=='ac147e114599064caa909c6949d381cfd3bd122dbf9823143a957604407e4555'
 for fn in('locale-fault-reason.bin','locale-fault.bin','registry-exception-message.bin','registry-exception-witness.bin'):
  p=pin('reports/m4-tree-review/constructor-native37-failure-r1/sequence-0/selected/'+fn)
  assert pins[str(p)]==diagnosis['files'][str(p)]
 old=pin(base+'service-preparation-r4/fs_operations.inc').read_text()
 abort=pin(base+'service-preparation-r4/locale_batch_binding.inc').read_text()
 runtime=pin('tools/m4-runtime/runtime.cpp').read_text()
 assert 'install->pc<0x78000000' in old and '0x7800ef03' in old
 assert 'throw mg::BridgeAbort{}' in abort
 assert 'catch (...)' in runtime and 'Admitted native callback raised an unsupported host exception' in runtime
 repaired=read(base+'service-preparation-r5/report.json')
 assert repaired['passed']and not repaired['native_executed']and repaired['initializer_credit']==0
 assert sorted(repaired['changed_files'])==['fs_operations.inc','locale_batch.hpp','session_impl.inc']
 for fn in repaired['changed_files']:
  p=pin(base+'service-preparation-r5/'+fn);assert pins[str(p)]==repaired['files'][str(p)]
 contract=read(base+'service-preparation-r5/constructor-FS-contracts.json')
 assert len(contract['frames'])==5 and contract['observed_failure_head']==0x2000177c
 admitted=read(base+'admitted-controller-r1/report.json')
 build=read(base+'fixture-build-r8/build.json')
 prep=read(base+'fixture-preparation-r4/report.json')
 preflight=read('reports/m4-tree-review/constructor-native37-prelaunch-r4/report.json')
 for d in(admitted,build,prep,preflight):assert d['passed']
 assert admitted['build_sha256']==pins[str((R/(base+'fixture-build-r8/build.json')).resolve())]
 assert admitted['preparation_sha256']==pins[str((R/(base+'fixture-preparation-r4/report.json')).resolve())]
 controller=Path(admitted['controller_path']);assert controller==R/'tools/m4-constructor-native/run_fixture_v2.py'
 pin(controller.relative_to(R));assert pins[str(controller)]==admitted['controller_sha256']
 for relative in (base+'fixture-preparation-r3/report.json',base+'fixture-build-r7/build.json',
                  base+'fixture-preparation-r3/fixture.cpp',base+'preparation-r7/component.cpp',
                  'tools/m4-constructor-native/prepare_service_v6.py'):
  pin(relative)
 pins[str(Path(__file__).resolve())]=sha(Path(__file__).resolve())
 report=dict(passed=True,scope='Archive-free failed-stage diagnostic and bounded existing repair lineage review only',
  initializer_credit=0,native_execution_performed=False,canonical_capture_reader_opened=False,
  entire_dependency_union_verified=False,repair_execution_proven=False,
  wrapper_reason=stderr.strip(),source_reason='Only an accepted original CRT normal frame may nest the owned guest FS chain',
  failure_cause='Inherited service fs_guard rejected a literal constructor-owned outer FS predecessor at 0x2000177c: its old admission permits CRT install PCs >=0x78000000 and handler 0x7800ef03 only',
  wrapper_explanation='Binding::deny records the source reason then throws mg::BridgeAbort, a non-std exception; Runtime catch-all translates it to the unsupported host exception ABI refusal',
  smallest_repair='Already implemented in service-preparation-r5: retain the CRT branch, additionally authenticate exactly five literal constructor FS install/handler forms against the committed FS source store and full12-byte private stack mirror; balance active constructor scope and sentinel endpoints',
  reuse_paths=dict(controller=admitted['controller_path'],build=base+'fixture-build-r8/build.json',
   preparation=base+'fixture-preparation-r4/report.json',service=base+'service-preparation-r5/report.json',
   preflight='reports/m4-tree-review/constructor-native37-prelaunch-r4/report.json'),
  remaining='Root scheduling admission for bounded O0/O2 r8 writer retry, then strict whole-source/provider/state/resource comparison, independent review and full carried integration before accepted credit',
  files=pins)
 out.mkdir(parents=True);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
