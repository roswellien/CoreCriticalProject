"""Only independently admitted exact version workers; root owns the writer slot."""
from pathlib import Path
import hashlib,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/m4-pipeline'))
from stages import run_stage,verify_stage
BUILD_SHA='55a9c4b17f1413263607bf55fd30d722a63b6dcd4b56ce4caf3ccdb8472a0b45'
PREP_SHA='dfca62ad2dbae9045fc034a5fa3770606451b524fcfe31ce46f73792dcb5f62c'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(review,review_sha,name):
 out=R/'reports/m4-version-source'/name;need(not out.exists(),'Fresh independently admitted version execution');pins={};runs={};passed=False;launched=0;terminal=0
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive/canonical payload reader');v=sha(p);need(h is None or v==h,'Exact current admitted physical input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Unchanged current pinned input');pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 try:
  build=read(R/'reports/m4-version-source/fixture-build-r1/build.json',BUILD_SHA);prep=read(R/'reports/m4-version-source/fixture-preparation-r2/report.json',PREP_SHA);admission=read(review,review_sha)
  need(admission['passed']and admission['build_sha256']==BUILD_SHA and admission['preparation_sha256']==PREP_SHA,'Actual independent review of these linked workers and frozen caller recipe');need(build['passed']and prep['passed']and build['preparation_sha256']==PREP_SHA,'Exact admitted compile-only candidates')
  for d in(build,prep):
   for p,h in d['files'].items():pin(p,h)
  inputs=[pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'),pin(R/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8'),pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a')]
  pin(__file__);pin(sys.executable);pin(R/'tools/m4-pipeline/stages.py');out.mkdir(parents=True)
  for level in('O0','O2'):
   worker=pin(build['workers'][level]['path'],build['workers'][level]['sha256']);capture=out/level;stage=out/(level+'-stage');args=[str(worker),*[str(p)for p in inputs],str(capture),review_sha];launched+=1;st=run_stage(args,stage,timeout_seconds=180,required_outputs=[capture/'cleanup/status.bin'],cwd=Path(prep['worker_cwd']),inputs=list(pins));terminal+=1;pin(stage/'stage.json');verify_stage(stage,sha(stage/'stage.json'));runs[level]=dict(worker=str(worker),arguments=args,cwd=prep['worker_cwd'],capture=str(capture),stage=str(stage/'stage.json'),stage_sha256=sha(stage/'stage.json'),elapsed_seconds=st['elapsed_seconds'],passed=st['passed']);print(json.dumps(dict(level=level,worker_passed=st['passed'])),flush=True);need(st['passed'],'Actual '+level+' version worker terminal success')
   status=struct.unpack('<8I',pin(capture/'cleanup/status.bin').read_bytes());need(status==(1,1,1,10,0,0,0,0),'Actual sole registered literal root and all ten compiled bodies without poison')
   for side in('before','after'):
    p=capture/'phase-0'/side;need(len(pin(p/'State.bin').read_bytes())==3504 and len(pin(p/'CPU.bin').read_bytes())==40 and len(pin(p/'FX.bin').read_bytes())==512,'Whole actual own current caller endpoints');need(len(pin(p/'stack.bin').read_bytes())==4096,'Whole actual stack endpoint')
   API_files=sorted((capture/'phase-0').glob('version-api-*-words.bin'));need(len(API_files)<=3,'Only measured actual VERSION source calls; no required success or resource-size constant')
   for n,p in enumerate(API_files):
    stem=p.name.removesuffix('-words.bin');w=struct.unpack('<16Q',pin(p).read_bytes());need(w[0]==1 and w[2]==n and w[1]in(0x4af10e,0x4af12c,0x4af167),'Measured literal native API chronology');err=struct.unpack('<3Q',pin(p.parent/(stem+'-last-error.bin')).read_bytes());need(err[0]==err[1]and(err[1],err[2])==w[8:10],'Actual source-boundary incoming error restored before provider');alias=struct.unpack('<8Q',pin(p.parent/(stem+'-owner-alias.bin')).read_bytes());need(alias[2]<=alias[3]and alias[1]==w[14]and alias[3]==w[15],'Actual requested extent and source-rounded MFC owner are distinct witnesses')
    if n==2 and alias[5]:need(alias[5]>=alias[4]and alias[6]==alias[5]-alias[4]and alias[6]<alias[2]and alias[7]<=alias[2]-alias[6],'Whole actual returned resource alias inside requested current owner')
    for suffix,size in(('-frame.bin',64),('-CPU-before.bin',40),('-CPU-after.bin',40),('-hardware.bin',1152)):need(len(pin(p.parent/(stem+suffix)).read_bytes())==size,'Whole typed actual native API record')
   manifest={str(p.relative_to(capture)).replace('\\','/'):dict(bytes=p.stat().st_size,sha256=sha(p))for p in capture.rglob('*')if p.is_file()};q=out/(level+'-output-manifest.json');q.write_text(json.dumps(manifest,indent=2)+'\n');pin(q);runs[level].update(output_manifest=str(q),output_manifest_sha256=sha(q),observed_files=len(manifest),measured_native_API_calls=len(API_files))
  for p,h in pins.items():need(sha(p)==h,'Entire exact input/ordinary witness closure remains unchanged')
  passed=True
 except BaseException:
  if out.exists():(out/'failure.txt').write_text(traceback.format_exc())
  raise
 finally:
  if out.exists():
   report=dict(passed=passed,scope='Actual sole version initializer route through genuine MFC ownership and actual VERSION.dll APIs; measured worker structure only, source/original equivalence and carried prefix remain separate',build_sha256=BUILD_SHA,preparation_sha256=PREP_SHA,admission_review=str(review),admission_review_sha256=review_sha,runs=runs,actual_workers_launched=launched,all_workers_terminal=launched==terminal,archive_reader_opened=False,source_original_equivalence=False,carried_accepted_prefix=False,initializer_credit=0,files=pins);q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
