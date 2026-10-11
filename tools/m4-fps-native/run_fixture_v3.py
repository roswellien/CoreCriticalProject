"""Run only the exact independently admitted seven-root widget/FPS fixture, never game UI."""
from pathlib import Path
import hashlib,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/m4-pipeline'))
from stages import run_stage,verify_stage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(review,review_sha,name):
 out=R/'reports/m4-fps-native'/name;need(not out.exists(),'Fresh admitted widget execution');out.mkdir();pins={};runs={};passed=False;launched=0
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive/capture reader');v=sha(p);need(h is None or h==v,'Exact input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Unchanged pinned input');pins[str(p)]=v;return p
 def words(p,n):return struct.unpack('<'+'I'*n,pin(p).read_bytes())
 try:
  bh='636115c9d926249b88de76bb1a12020a2f566c09220beb20838e510d7d28763a';ph='bf63967a42e1f35c869ea5e1e0473122d9913f1d03bd68d104c1a63e2aaa04f0';b=json.loads(pin(R/'reports/m4-fps-native/fixture-build-r2/build.json',bh).read_bytes());p=json.loads(pin(R/'reports/m4-fps-native/fixture-preparation-r2/report.json',ph).read_bytes());admission=json.loads(pin(review,review_sha).read_bytes());need(admission['passed']and admission['build_sha256']==bh and admission['preparation_sha256']==ph,'Independent prelaunch binds exact current linked build and recipe');need(b['passed']and p['passed']and b['preparation_sha256']==ph,'Exact linked preparation')
  for q,h in b['files'].items():pin(q,h)
  for q,h in p['files'].items():pin(q,h)
  inputs=[pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'),pin(R/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8'),pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a')];pin(__file__);pin(sys.executable)
  for level in('O0','O2'):
   worker=pin(b['workers'][level]['path'],b['workers'][level]['sha256']);capture=out/level;stage=out/(level+'-stage');args=[str(worker),*[str(q)for q in inputs],str(capture),review_sha];launched+=1;st=run_stage(args,stage,timeout_seconds=180,required_outputs=[capture/'cleanup/status.bin'],inputs=list(pins));pin(stage/'stage.json');verify_stage(stage,sha(stage/'stage.json'));runs[level]=dict(worker=str(worker),arguments=args,stage=str(stage/'stage.json'),stage_sha256=sha(stage/'stage.json'),capture=str(capture),elapsed_seconds=st['elapsed_seconds'],passed=st['passed']);print(json.dumps(dict(level=level,worker_passed=st['passed'])),flush=True);need(st['passed'],'Actual '+level+' widget worker terminal success')
   need(words(capture/'cleanup/status.bin',8)==(1,1,7,58,0,0,0,0),'Seven measured registered root routes complete')
   for phase,root in enumerate(p['source_roots']):
    stem=capture/f'phase-{phase}'/f'root-{root}'/'after';status=struct.unpack('<12Q',pin(stem/'status.bin').read_bytes());need(status[1]==phase+1 and status[2]==root and status[4:7]==(0,0,0),'Exact measured current root/selected count/live context');need(len(pin(stem/'State.bin').read_bytes())==3504 and len(pin(stem/'CPU.bin').read_bytes())==40 and len(pin(stem/'FX.bin').read_bytes())==512,'Whole actual component machine endpoints')
   final=capture/'phase-6'/f"root-{p['source_roots'][-1]}"/'after';need((final/'accesses.bin').stat().st_size==25003*24,'Complete causal operand extent');need((final/'APIs.bin').stat().st_size==149*1488,'Complete actual API records');need((final/'virtuals.bin').stat().st_size==511*32 and(final/'FS-events.bin').stat().st_size==588*32 and(final/'arrays.bin').stat().st_size==75*32,'Exact dynamic virtual/FS/array closure');need(len(list((capture/'cleanup'/'manual-font-cleanup').glob('*-row.bin')))==15,'Actual15 owned font cleanup returns')
   need((final/'formats.bin').stat().st_size==2528,'One whole actual literal vsprintf entry/return record');need((final/'format-dispatches.bin').stat().st_size==3*32,'Three actual literal readonly character dispatches')
   page_contract=json.loads(pin(R/'reports/m4-fps-native/fixture-preparation-r2/provider-page-contracts.json').read_bytes())
   for page in page_contract['pages']:
    address=page['address'];stem=capture/'provider-mapping'/('page-'+str(address));row=words(Path(str(stem)+'-row.bin'),6);need(row[:4]==(1,address,page['file_offset'],page['permissions'])and row[4:6]in((0,1),(1,0)),'Exact current physical mapping disposition')
    physical=pin(Path(str(stem)+'-physical.bin'),page['sha256']).read_bytes();after=pin(Path(str(stem)+'-after.bin')).read_bytes();need(len(physical)==len(after)==4096,'Complete mapped/provider admission payloads')
    if row[4]:need(after==physical,'Absent page receives whole own physical payload')
    else:need(pin(Path(str(stem)+'-before.bin')).read_bytes()==after,'Every prior provider payload preserved exactly')
    for phase in range(7):
     for side in('before','after'):need(len(pin(capture/f'phase-{phase}'/side/f'provider-source-page-{address}.bin').read_bytes())==4096,'Whole current provider phase endpoint')
   # Ordinary file witnesses only. No canonical payload/index reader is opened.
   manifest={str(q.relative_to(capture)).replace('\\','/'):dict(bytes=q.stat().st_size,sha256=sha(q))for q in capture.rglob('*')if q.is_file()};f=out/(level+'-output-manifest.json');f.write_text(json.dumps(manifest,indent=2)+'\n');pin(f);runs[level]['output_manifest']=str(f);runs[level]['output_manifest_sha256']=sha(f);runs[level]['observed_files']=len(manifest)
  for q,h in list(pins.items()):need(sha(q)==h,'All current inputs/observations unchanged after workers')
  passed=True
 except BaseException:
  passed=False
  (out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Seven registered widget/FPS Runtime roots through literal vsprintf and current accepted source registry service with actual native GDI; measured worker structure only, no source/native equivalence or connected138 acceptance',build_sha256='636115c9d926249b88de76bb1a12020a2f566c09220beb20838e510d7d28763a',preparation_sha256='bf63967a42e1f35c869ea5e1e0473122d9913f1d03bd68d104c1a63e2aaa04f0',admission_review=str(review),admission_review_sha256=review_sha,runs=runs,actual_workers_launched=launched,all_workers_terminal=True,archive_reader_opened=False,initializer_credit=0,files=pins);f=out/'report.json';f.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(f),sha256=sha(f))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
