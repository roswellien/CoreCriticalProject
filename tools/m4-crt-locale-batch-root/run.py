"""Actual native whole-batch execution into checked strict direct archives."""
import json,sys,time,traceback,struct
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-crt-locale-batch-root'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import sha_file
from manifests import verify_manifest,normalized,unique_object
from paths import publish_bytes,workspace_path
from stages import run_stage,verify_stage
sys.path.insert(0,str(ROOT/'tools/m4-crt-allocation-root'))
from run_v2 import DirectSet
def need(c,s):
 if not c:raise RuntimeError(s)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)
def main(bp,bh,directory):
 t=time.perf_counter();out=workspace_path(directory,reports=True);need(out.parent==BASE and not out.exists(),'Fresh owned execution report');out.mkdir(parents=True);files={};levels={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();actual=sha_file(p);need(h is None or actual==h,'Pinned physical dependency '+str(p));key=normalized(str(p));need(key not in files or files[key]==actual,'Consistent physical dependency');files[key]=actual;return p
 try:
  b=read(pin(bp,bh));need(b['passed'],'Successful native candidate build')
  for category in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
   for p,h in b.get(category,{}).items():pin(p,h)
  pin(b['preparation_path'],b['preparation_sha256']);pin(__file__);pin(sys.executable);pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py')
  for name in ('capture_bundle.py','paths.py','stages.py','manifests.py'):pin(ROOT/'tools/m4-pipeline'/name)
  game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');pack=pin(ROOT/'reports/m4-crt-fdiv/native-derived-r1/pack.bin','fd9a41958ac2edf5e1c3f118ec24a59e2df295d94ac1d1b1346deb3cbc46aa80');before=pin(ROOT/'reports/m4-crt-fdiv-replay/preparation-r1/before-inputs.bin','4294b8d926966c04d305b6e22a9166f08a328f4cc1c62984b72677fe83dd638a')
  for level in ('O0','O2'):
   worker=pin(b['workers'][level]);obj=pin(ROOT/f'reports/m4-crt-fdiv-entry-prefix/preparation-r2/candidate-{level}.obj');capture=out/('native-'+level);stage=out/('run-'+level)
   result=run_stage(list(map(str,(worker,game,obj,provider,pack,before,capture))),stage,timeout_seconds=180,required_outputs=[capture/'transport.json'],inputs=list(files));sh=sha_file(pin(stage/'stage.json'));verify_stage(stage,sh);need(result['passed'],'Actual whole-unit native worker '+level)
   observations=DirectSet(capture/'transport.json',pin);rows=[]
   try:
    need(observations.data('COMPLETE')==b'COMPLETE','Semantic completion published')
    for n in range(18):
     p=f'row-{n}/';v=json.loads(observations.data(p+'result.json'),object_pairs_hook=unique_object);control=0 if n<6 else 201+n-6;need(v['passed'] and v['scenario']==n and v['control']==control,'Actual row identity')
     final=observations.words(p+'final/locale-summary.bin',32);heap=observations.words(p+'final/heap-create-registry.bin',18,'Q');live=observations.words(p+'entry-after-stop/locale-summary.bin',32)
     need(final[14]==final[15]==final[30]==0 and final[23]==1,'No live allocation/critical section/heap after cleanup');need(heap[8]==heap[9]==heap[10]==1 and heap[7]==0 and heap[15]==1,'Real same heap created and destroyed')
     need(v['builder_returned']==(control==0) and (not control or final[31]),'Ordinary genuine builder RET or causal refusal')
     if not control:
      need(live[3:7]==(1,1,2,1) and live[7]>0 and live[8]>=0x31000000 and live[14]>=2 and live[15]>=5,'Whole static/defaultlocale/two-parser passes completed with simultaneous ownership')
      need(observations.words(p+'locale-builder-returned/state-cpu.bin',10)[9]==0x7800ba9e,'Actual original builder return target')
     for boundary in ('writer','entry','cleanup'):
      a=observations.data(p+boundary+'-host-before.bin');z=observations.data(p+boundary+'-host-after.bin');need(len(a)==len(z)==544,'Rich hardware boundary record');need(a[512:540]==z[512:540] and a[:5]==z[:5] and a[24:28]==z[24:28],'Complete ENV/CW/SW/FTW/MXCSR preserved')
      for i in range(8):need(a[32+16*i:42+16*i]==z[32+16*i:42+16*i],'Physical raw80 preserved')
      for i in range(6,16):need(a[160+16*i:176+16*i]==z[160+16*i:176+16*i],'Native nonvolatile XMM preserved')
     phases=sorted({name.split('/')[1] for name in observations.entries if name.startswith(p) and name.endswith('/state.bin')})
     for phase in phases:
      need(len(observations.data(p+phase+'/state.bin'))==3504 and len(observations.data(p+phase+'/fx.bin'))==512,'Whole machine observation extent')
     rows.append(dict(scenario=n,control=control,summary=final,live_summary=live,full_machine_checkpoints=len(phases),result=v))
    levels[level]=dict(passed=True,stage_path=str(stage/'stage.json'),stage_sha256=sh,transport_path=str(capture/'transport.json'),transport_sha256=sha_file(capture/'transport.json'),logical_files=len(observations.entries),rows=rows)
   finally:observations.close()
  closure=verify_manifest(files);passed=True
 except Exception:
  publish_bytes(out/'failure.txt',traceback.format_exc().encode());raise
 finally:
  r=dict(schema='mw34-m4-locale-batch-native-execution-v1',passed=passed,native_component_executed=bool(levels),build_path=str(Path(bp).resolve()),build_sha256=bh,levels=levels,files=files,physical_closure=verify_manifest(files),State_reseed_after_writer=False,actual_API_results_injected=False,direct_strict_capture_emission=True,flat_capture_tree=False,full_CRT=False,whole_M4_complete=False,seconds=time.perf_counter()-t)
  publish_bytes(out/'report.json',(json.dumps(r,sort_keys=True,indent=2)+'\n').encode());files[normalized(str(out/'report.json'))]=sha_file(out/'report.json');publish_bytes(out/'pins.json',(json.dumps(dict(schema='mw34-m4-locale-batch-execution-pins-v1',files=files),sort_keys=True,indent=2)+'\n').encode());print(json.dumps(dict(passed=passed,report_sha256=sha_file(out/'report.json'),pins_sha256=sha_file(out/'pins.json'),seconds=r['seconds'])))
if __name__=='__main__':main(*sys.argv[1:])
