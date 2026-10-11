"""Independent causal fixture/composed-validator/sealed receipt review, no archive."""
from pathlib import Path
import hashlib,json,runpy,struct,subprocess,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in PINS or PINS[str(p)]==v;PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def main(name):
 out=ROOT/'reports/m4-lockit-build-review'/name;assert not out.exists();out.mkdir(parents=True)
 review=ROOT/'reports/m4-lockit-review';build=read(review/'controls-build-r5/build.json','a78ad98f6d724c7b020a807b09eb60e3f94a685a02ec896a5635622b68b2ab7f');execution=read(review/'controls-execution-r4/report.json','a877a33d14107c854256b7964de180015033c140c178f8832d9ee28d7eef18a2');validation=read(review/'controls-validation-r4/report.json','1f37a6d0d2fd9fd9dfd812920c710c4717edf6e6cfb4e2f559b4d59fdf6ca129')
 assert build['passed']and execution['passed']and validation['passed']and execution['build_sha256']=='a78ad98f6d724c7b020a807b09eb60e3f94a685a02ec896a5635622b68b2ab7f'
 assert build['parent_build_sha256']=='05a198d319f2e3ee2259b998a8989db23df0b20afd40416fb185e7a0b1d17c30'
 parent=read(build['parent_build'],build['parent_build_sha256']);assert parent['passed']and parent['preparation_sha256']=='7a2e383ab47bdb668e56181cdc3eec1c75ebf03437e5f9b9ac675861370a85c7'
 native=read(ROOT/'reports/m4-lockit-native/preparation-r5/report.json','965ea738333677c308749108b7f0b211772e89d4dd5e2ed14ea561cb63d0bdc1');assert native['passed']
 def source(p):return pin(p,build['sources'][str(Path(p).resolve())]).read_text()
 fixture=source(review/'controls-source-r2/fixture.inc');hooks=source(review/'controls-source-r2/hooks.hpp');compiled=source(review/'controls-build-r5/fixture.cpp')
 assert source(review/'controls-build-r5/hooks.hpp')==hooks
 assert compiled.endswith(fixture)and compiled.startswith('#define main frozen_connected124_worker_main\n#include "D:/Projects/MW34Recomp/reports/m4-joint-startup124/preparation-r5/native_main.cpp"\n#undef main\n')
 for snippet in ('point!=(after?41U:40U)','actual.api[2]!=0x7810a30b','trigger_PC=pc','trigger.calls.size()==1&&trigger.calls[0][2]==0x411010','selected==11||selected==12','row[11]==40&&row[5]==1','restore_resource->RecursionCount^=1','std::memcpy(restore_resource,resource_before.data(),40)','const auto address=state->gpr.rsp.dword+4'):
  assert snippet in hooks,snippet
 assert fixture.index('(void)invoke(t);mw34_lockit_controls::restore_actual();')<fixture.index('c.registry().finish();')
 for snippet in ('ni::NumericHostBoundary boundary(0x37f)','sample.owner_before==sample.owner_after','sample.state_before==sample.state_after&&sample.fx_before==sample.fx_after&&sample.cpu_before==sample.cpu_after','first-cleaned','c.registry().test_hook=nullptr;attempt(c,w,1,0)'):
  if snippet!='first-cleaned':assert snippet in fixture,snippet
 validator=ROOT/'tools/m4-lockit-review/check_controls_v6.py'
 for p in validator.parent.glob('check_controls*.py'):pin(p,validation['files'][str(p.resolve())])
 # The composed module only defines main because __name__ is not __main__.
 # It does not open a capture or execute the checker.
 composed=runpy.run_path(str(validator),run_name='independent_static_validator_review')['source'];assert isinstance(composed,str)
 (out/'composed-validator.py.txt').write_text(composed);pin(out/'composed-validator.py.txt')
 for snippet in ("api[2:4]==(0x7810a30b,0x78146198)","api[5]+4","fault[1] in ((0x4dc193,) if case==5 else (api[4],api[2]))","source[-1]==(0x4dc193,0x5bb4f8,effect[3],4,0)","tags[4]==int(case==5)","sample[768:4272]==sample[4272:7776]","first[4272:7776]==sample[768:4272]","H.copied_suffixes(a,base+'first-cleaned/',base+target)","struct.unpack_from('<I',old,12)[0]==1","struct.unpack_from('<I',new,12)[0]==0","new[1:]==old[1:]"):
  assert snippet in composed,snippet
 causes=read(review/'controls-validation-r4/causes.json','63715a165583ea209d5775629c3e1e84b7efa83e2b40ecb647a224768afa9eea');assert len(causes)==30
 assert {(r['level'],r['case'])for r in causes}=={(level,case)for level in('O0','O2')for case in range(1,16)}
 for row in causes:
  assert row['source_PC']==0x771143e0 and row['point']==(41 if row['case']in(11,12)else 40)and row['source_prefix_rows']>=1 and row['reason']
  if row['case']==5:assert row['source_prefix_rows']==376 and row['actual_intervention'][1]==0x5bb4f8 and 'named Lockit import' in row['reason']
  if row['case']==12:assert row['actual_intervention'][0]==6 and row['actual_intervention'][2:5]==[1,0,40]and 'actual native resource bytes' in row['reason']
 counts=validation['counts'];assert counts['actual_attempts']==64 and counts['same_session_refusals']==32 and counts['causal_targeted_refusals']==30 and counts['positive_four_root_runs']==2 and counts['positive_actual_Lockit_CALL_RET']==16 and counts['positive_actual_new_owners']==16 and counts['real_resources_deleted']==160
 # Authenticate which actual controls compilation consumed the frozen fixture,
 # hooks, and native5 source. Existing Ninja dependency receipts are read only.
 ninja=pin('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe');levels=[]
 for level in('O0','O2'):
  worker=build['workers'][level];exe=pin(worker['path'],worker['sha256']);folder=exe.parent;graph=pin(folder/'build.ninja').read_text();declared=read(review/'controls-build-r5/pins.json')['files']
  assert str(review/'controls-build-r5/fixture.cpp').replace(':','$:')in graph and '/machine:x64'in graph
  dep=subprocess.run([str(ninja),'-t','deps'],cwd=folder,capture_output=True,timeout=15);assert dep.returncode==0
  (out/(level+'-compiler-dependencies.txt')).write_bytes(dep.stdout);pin(out/(level+'-compiler-dependencies.txt'));deps=dep.stdout.decode(errors='replace').replace('\\','/').casefold()
  for p in(review/'controls-build-r5/fixture.cpp',review/'controls-build-r5/hooks.hpp',ROOT/'reports/m4-lockit-native/preparation-r5/registry_library.cpp',ROOT/'reports/m4-lockit-native/preparation-r5/lockit_operations.inc'):assert str(p).replace('\\','/').casefold()in deps
  with exe.open('rb')as f:f.seek(60);offset=struct.unpack('<I',f.read(4))[0];f.seek(offset);assert f.read(6)==b'PE\0\0\x64\x86'
  levels.append(dict(level=level,actual_AMD64_worker_sha256=worker['sha256'],actual_compiler_fixture_hooks_native5_consumed=True))
 pin(__file__);report=dict(passed=True,scope='Independent composed causal source/actual compilation/sealed receipt review; no second capture reader, no new execution or initializer credit',controls_validation_sha256='1f37a6d0d2fd9fd9dfd812920c710c4717edf6e6cfb4e2f559b4d59fdf6ca129',controls_build_sha256='a78ad98f6d724c7b020a807b09eb60e3f94a685a02ec896a5635622b68b2ab7f',controls_execution_sha256='a877a33d14107c854256b7964de180015033c140c178f8832d9ee28d7eef18a2',parent_native_build_sha256=build['parent_build_sha256'],independent_capture_reader_opened=False,causal_cases_per_level=15,causal_targeted_refusals=30,complete_attempts=64,whole_same_session_retries=32,delayed_import_refusal_source_PC=0x4dc193,API_PC_scope='Actual imported API target PC771143E0 separate from source CALLPC7810A30B in the full API witness; frame uses source witness ESP, not carried RuntimeCPU',native_CS40_restored_before_cleanup=True,levels=levels,initializer_credit=False,files=PINS)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
