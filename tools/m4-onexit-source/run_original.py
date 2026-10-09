"""Execute frozen actual original54 into direct strict canonical archives."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2];BASE=ROOT/'reports/m4-onexit-source'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from stages import run_stage,verify_stage
CASES=((0,0x7f,0),(0,0x37f,7),(0,0xf7f,0),(1,0x47f,7),(1,0xa7f,0),(1,0xe7f,7))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(buildpath,digest,name):
 out=BASE/name;assert not out.exists();out.mkdir(parents=True);files={};passed=False
 def pin(p,h=None):
  p=Path(p).absolute();v=sha(p);assert h is None or h==v,(p,h,v);files[str(p)]=v;return p
 try:
  b=json.loads(pin(buildpath,digest).read_text(encoding='utf-8-sig'));assert b['passed']
  for p,h in json.loads(pin(Path(buildpath).parent/'pins.json').read_text(encoding='utf-8-sig'))['files'].items():pin(p,h)
  worker=pin(b['worker'],b['worker_sha256']);pack=pin(b['pack']);game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a');pin(__file__);pin(sys.executable);pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
  capture=out/'original';stage=out/'run';st=run_stage(list(map(str,(worker,pack,game,provider,capture))),stage,timeout_seconds=190,required_outputs=[capture/'transport.json'],inputs=list(files));verify_stage(stage,sha(pin(stage/'stage.json')));assert st['passed'],'Actual original54stage failed'
  p=pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('onexit_original_direct',p);ds=importlib.util.module_from_spec(spec);spec.loader.exec_module(ds);records=ds.DirectSet(capture/'transport.json',pin)
  try:
   assert records.data('COMPLETE.txt')==b'complete';head=records.data('header.bin');assert head[:8]==b'MW4J54O1'and struct.unpack_from('<6I',head,8)==(1,6,54,324,28,234112)
   prep=json.loads(pin(Path(b['preparation'])/'report.json',b['preparation_sha256']).read_bytes());order=prep['order'];roots=json.loads(pin(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json').read_bytes());callbacks=[r['registration']['callback']for r in roots]
   for seq,(repeat,cw,top)in enumerate(CASES):
    seen=[]
    for phase,row in enumerate(order):
     data=records.data(f'phase/{seq}/{phase}.bin');assert len(data)==234112;assert struct.unpack_from('<9I',data)==(seq,repeat,phase,row['slot'],row['entry'],cw,top,0,1);assert struct.unpack_from('<I',data,92)[0]==0x20001804 and struct.unpack_from('<I',data,112)[0]==0x410a80
     begin,nxt,capacity,mode=struct.unpack_from('<4I',data,233584);assert begin and begin<=nxt and(nxt-begin)%4==0 and 104<=capacity<=512;assert mode==1,'Actual source-established mode1 provider domain'
     found=next((r for r in roots if r['entry']==row['entry']),None)
     if found:seen.append(found['registration']['callback'])
     assert nxt-begin==len(seen)*4;assert struct.unpack_from('<'+str(len(seen))+'I',data,233600)==tuple(seen)
    assert records.data(f'cleanup/{seq}/registry.bin')==struct.pack('<26I',*callbacks)
   passed=True
  finally:records.close()
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual original54 x86 persistent28observedpages, original sentinel/producer and real32MSVCRTregistration; no nativeattach/exitcallbacks',original_executed=True,native_executed=False,phases=324 if passed else 0,build_path=str(buildpath),build_sha256=digest,original_capture=str(out/'original/transport.json'),record_bytes=234112,per_phase_reseed=False,files=files);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).absolute(),sys.argv[2],sys.argv[3])
