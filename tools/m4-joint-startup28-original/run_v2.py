"""Run actual connected original28 into direct strict archives, never game launch."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-joint-startup28-original'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from stages import run_stage,verify_stage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(buildpath,digest,name,checkpoint=False):
 out=BASE/name;assert not out.exists();out.mkdir(parents=True);pins={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);pins[str(p)]=v;return p
 try:
  b=json.loads(pin(buildpath,digest).read_text(encoding='utf-8-sig'));assert b['passed']
  for p,h in json.loads(pin(Path(buildpath).parent/'pins.json').read_text(encoding='utf-8-sig'))['files'].items():pin(p,h)
  worker=pin(b['worker'],b['worker_sha256']);pack=pin(b['pack']);game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a')
  api=pin(Path('C:/Windows/SysWOW64/user32.dll'));pin(__file__);pin(sys.executable)
  stage=out/'run';capture=out/'original';args=list(map(str,(worker,pack,game,provider,capture)))+(['--checkpoint']if checkpoint else[])
  st=run_stage(args,stage,timeout_seconds=190,required_outputs=[capture/'transport.json'],inputs=list(pins));verify_stage(stage,sha(pin(stage/'stage.json')));assert st['passed'],'Actual original stage failed'
  dsfile=pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('strict_direct_original28',dsfile);ds=importlib.util.module_from_spec(spec);spec.loader.exec_module(ds)
  records=ds.DirectSet(capture/'transport.json',pin)
  try:
   assert records.data('COMPLETE.txt')==b'complete';head=records.data('header.bin');assert head[:8]==(b'MW4J28D1'if checkpoint else b'MW4J28O1')and struct.unpack_from('<6I',head,8)==(1,6,28,168,17,143472)
   prep=json.loads(pin(Path(b['preparation'])/'report.json',b['preparation_sha256']).read_bytes());order=prep['order'];cases=prep['cases']
   for sequence,(repeat,cw,top)in enumerate(cases):
    for phase,row in enumerate(order):
     data=records.data(f'phase/{sequence}/{phase}.bin');assert len(data)==143472;assert struct.unpack_from('<9I',data)==(sequence,repeat,phase,row['slot'],row['entry'],cw,top,0,1);assert struct.unpack_from('<I',data,92)[0]==0x20001804 and struct.unpack_from('<I',data,112)[0]==0x410a80
     service=data[142260:];assert len(service)==1212
     if row['entry']==0x482cf0:
      values=struct.unpack_from('<5I',service,1192);assert values[0]==1 and values[2]==16 and values[3]+20==values[4];assert struct.unpack_from('<I',service,16)[0]==0x200017e0 and struct.unpack_from('<I',service,56)[0]==0x200017f4
     else:assert service==bytes(1212)
   assert sha(api)==pins[str(api)]
  finally:records.close()
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual connected28 x86 sequence on persistent17pages with actual SPI stdcall16 and numeric provider; directarchives from firstcapture; no softwareState observed',build_path=str(buildpath),build_sha256=digest,original_capture=str(out/'original/transport.json'),phases=168 if passed else 0,sequences=6 if passed else 0,original_record_bytes=143472,Common_bytes=141540,original_executed=True,direct_primary=not checkpoint,debugger_secondary=checkpoint,per_phase_reseed=False,native_executed=False,whole_M4_complete=False,files=pins)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3],'--checkpoint'in sys.argv[4:])
