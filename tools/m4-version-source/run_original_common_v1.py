"""One independently admitted original8 matched caller broker invocation; metadata reader only."""
from pathlib import Path
import hashlib,json,re,sys,traceback
R=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True;sys.path.insert(0,str(R/'tools/m4-pipeline'))
from stages import run_stage,verify_stage
PREP_SHA='fafc198f6a20184cf3cc3bec67710e8f22eb7408789568eacefb73c90163d48f'
BUILD_SHA='14e3040ee8aa42f014a07d042bf3bab06d3565006b9ce5a2dfb39cf952893b52'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(review,review_sha,name):
 out=R/'reports/m4-version-source'/name;need(not out.exists(),'Fresh independently admitted original version output');pins={};passed=False;launched=terminal=0;run={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'Original controller never opens archive payloads');v=sha(p);need(h is None or v==h,'Exact original controller frozen physical input '+str(p));pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 try:
  prep_path=R/'reports/m4-version-source/original-preparation-r8/report.json';build_path=R/'reports/m4-version-source/original-build-r8/build.json';prep=read(prep_path,PREP_SHA);build=read(build_path,BUILD_SHA);admission=read(review,review_sha)
  need(prep['passed']and build['passed']and build['preparation_sha256']==PREP_SHA,'Exact frozen original8 matched caller compile-only candidate');need(admission['passed']and admission['preparation_sha256']==PREP_SHA and admission['build_sha256']==BUILD_SHA and admission['worker_sha256']==build['worker_sha256'],'Actual independent original8 matched caller whole-link/preparation/worker review')
  need(admission['common_caller_recipe_sha256']=='ca7f036b3693ef71bbbe5ce7a0af4ae3cb98755550d1bd1dcd8da955ab311281'and prep['common_caller_recipe_sha256']=='ca7f036b3693ef71bbbe5ce7a0af4ae3cb98755550d1bd1dcd8da955ab311281','Actual independent common caller recipe admission');
  for d in(prep,build):
   for p,h in d['files'].items():pin(p,h)
  worker=pin(build['worker'],build['worker_sha256']);pack=pin(prep_path.parent/'pages.bin',prep['pack_sha256']);game=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');provider=pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a');pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');pin(R/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8');pin(__file__);pin(sys.executable);pin(R/'tools/m4-pipeline/stages.py')
  need(Path(prep['required_process_cwd'])==(R/'MW3').resolve()and Path(prep['explicit_writer_reports_root'])==(R/'reports').resolve(),'Exact physical relative filename cwd and explicitly compiled project reports root')
  out.mkdir(parents=True);capture=out/'original';stage=out/'original-stage';argv=[str(worker),str(pack),str(game),str(provider),str(capture)];launched=1;st=run_stage(argv,stage,timeout_seconds=200,required_outputs=[capture/'transport.json'],cwd=R/'MW3',inputs=list(pins));terminal=1;pin(stage/'stage.json');verify_stage(stage,sha(stage/'stage.json'));run=dict(argv=argv,cwd=str(R/'MW3'),stage=str(stage/'stage.json'),stage_sha256=sha(stage/'stage.json'),passed=st['passed'],elapsed_seconds=st['elapsed_seconds']);need(st['passed'],'The single actual original brokered invocation must terminate successfully')
  stdout=pin(stage/'stdout.bin').read_bytes();stderr=pin(stage/'stderr.bin').read_bytes();children=re.findall(rb'Original direct broker child finished: pid=(\d+) exit=(\d+)',stderr);need(len(children)==1 and int(children[0][0])>0 and int(children[0][1])==0,'One actual pre-reserved original child completed with exit0')
  transport=read(capture/'transport.json');need(transport['passed']and transport['transport_only']and transport['format']=='mw34.capture.direct.v1'and transport['parts'],'Actual completed transport metadata only');parts=transport['parts'];need(len(parts)<=8 and sum(p['logical_files']for p in parts)==transport['logical_files']and sum(p['payload_bytes']for p in parts)==transport['payload_bytes'],'Whole transport metadata totals')
  declared={'transport.json'};rows=[]
  for part in parts:
   name=part['bundle'];need(Path(name).name==name and name.endswith('.mwb')and name not in declared,'Finite unique metadata-declared original bundle');declared.add(name);p=capture/name;need(p.is_file()and p.stat().st_size==part['bundle_bytes'],'Actual metadata-declared bundle filesystem extent without opening payload');rows.append(dict(path=str(p),bytes=p.stat().st_size,writer_reported_sha256=part['sha256'],opened_by_controller=False))
  need({p.name for p in capture.iterdir()}==declared,'Only declared completed original transport files');run.update(capture=str(capture),transport_sha256=sha(capture/'transport.json'),logical_files=transport['logical_files'],payload_bytes=transport['payload_bytes'],parts=rows,actual_child_pid=int(children[0][0]),stdout_sha256=sha(stage/'stdout.bin'),stderr_sha256=sha(stage/'stderr.bin'))
  for p,h in pins.items():need(sha(p)==h,'Frozen original inputs and metadata conserved after completion')
  passed=True
 except BaseException:
  if out.exists():(out/'failure.txt').write_text(traceback.format_exc())
  raise
 finally:
  if out.exists():
   d=dict(passed=passed,scope='One independently admitted original8 matched caller broker/child execution with actual worker guards; controller reads transport metadata only, no archive payload validation or equivalence credit',preparation_sha256=PREP_SHA,build_sha256=BUILD_SHA,admission_review=str(review),admission_review_sha256=review_sha,run=run,original_worker_invocations=launched,role="single_original8_common_transport",common_caller_recipe_sha256="ca7f036b3693ef71bbbe5ce7a0af4ae3cb98755550d1bd1dcd8da955ab311281",all_workers_terminal=launched==terminal,archive_payload_reader_opened=False,source_original_equivalence=False,initializer_credit=0,files=pins);p=out/'report.json';p.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(p),sha256=sha(p))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
