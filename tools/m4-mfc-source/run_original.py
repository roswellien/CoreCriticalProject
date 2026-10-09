"""Execute frozen actual original103 into direct strict canonical archives."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2];BASE=ROOT/'reports/m4-mfc-source'
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
  capture=out/'original';stage=out/'run';st=run_stage(list(map(str,(worker,pack,game,provider,capture))),stage,timeout_seconds=190,required_outputs=[capture/'transport.json'],inputs=list(files));verify_stage(stage,sha(pin(stage/'stage.json')));assert st['passed'],'Actual original103stage failed'
  p=pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('onexit_original_direct',p);ds=importlib.util.module_from_spec(spec);spec.loader.exec_module(ds);records=ds.DirectSet(capture/'transport.json',pin)
  try:
   assert records.data('COMPLETE.txt')==b'complete';head=records.data('header.bin');assert head[:8]==b'MW4J103O'and struct.unpack_from('<6I',head,8)==(1,6,103,618,35,291456)
   prep=json.loads(pin(Path(b['preparation'])/'report.json',b['preparation_sha256']).read_bytes());order=prep['order'];roots=json.loads(pin(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json').read_bytes())+json.loads(pin(ROOT/'reports/m4-strings-source/recovery-r7/string-roots.json').read_bytes());roots+=json.loads(pin(BASE/'recovery-r4/mfc-roots.json').read_bytes());roots.sort(key=lambda r:r['slot']);callbacks=[r['registration']['callback']for r in roots]
   for seq,(repeat,cw,top)in enumerate(CASES):
    seen=[]
    for phase,row in enumerate(order):
     data=records.data(f'phase/{seq}/{phase}.bin');assert len(data)==291456;assert struct.unpack_from('<9I',data)==(seq,repeat,phase,row['slot'],row['entry'],cw,top,0,1);assert struct.unpack_from('<I',data,92)[0]==0x20001804 and struct.unpack_from('<I',data,112)[0]==0x410a80
     begin,nxt,capacity,mode=struct.unpack_from('<4I',data,290928);assert begin and begin<=nxt and(nxt-begin)%4==0 and nxt-begin<=capacity<=512;assert mode==1,'Actual source-established mode1 provider domain'
     count=struct.unpack('<I',records.data(f'phase/{seq}/{phase}/api-count.bin'))[0];assert count<=32 and len(records.data(f'phase/{seq}/{phase}/api-ledger.bin'))==count*104;found=next((r for r in roots if r['entry']==row['entry']),None)
     if found:seen.append(found['registration']['callback'])
     assert nxt-begin==len(seen)*4;assert struct.unpack_from('<'+str(len(seen))+'I',data,290944)==tuple(seen)
    assert records.data(f'cleanup/{seq}/registry.bin')==struct.pack('<75I',*callbacks)
   imports=json.loads(pin(Path(b['preparation'])/'mfc-import-bindings.json').read_bytes());ledger=records.data('mfc-import-ledger.bin');assert len(ledger)==511*28;loaded=bytearray(records.data('mfc-loaded-page.bin'));raw=records.data('mfc-raw-page.bin');assert len(loaded)==len(raw)==4096
   for k,expected in enumerate(imports):
    slot,bound,target,declared,owner,named,ordinal=struct.unpack_from('<7I',ledger,k*28);assert(slot,bound,ordinal)==(expected['slot'],expected['raw'],expected['ordinal'])and target==named and declared and owner;assert struct.unpack_from('<I',loaded,slot&4095)[0]==target;struct.pack_into('<I',loaded,slot&4095,bound)
    for base in set((declared,owner)):
     path=records.data(f'mfc-modules/{base}/path.bin').decode('utf-16-le').rstrip('\0');observed=records.data(f'mfc-modules/{base}/image.bin');assert Path(path).read_bytes()==observed;pin(path)
   assert bytes(loaded)==raw,'Every complete nonimport page byte exact after only authenticated511 import projections'
   bindings=prep['mfc_bindings']
   for seq in range(6):
    for mi,item in enumerate(bindings):
     actual=struct.unpack('<8I',records.data(f'phase/{seq}/102/mfc/{mi}/meta.bin'));assert actual[:5]==tuple(item[k]for k in('root','CALL_pc','requested_size','object','publication'))and actual[5]and actual[6]>=item['requested_size']and actual[7]==mi;assert len(records.data(f'phase/{seq}/102/mfc/{mi}/bytes.bin'))==actual[6];assert records.data(f'cleanup/{seq}/mfc-{mi}-before.bin')==struct.pack('<8I',*actual);assert records.data(f'cleanup/{seq}/mfc-{mi}-returned.bin')==struct.pack('<I',1)
   passed=True
  finally:records.close()
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual original103 x86 persistent35observedpages, original sentinel/producer and real32MSVCRTregistration; no nativeattach/exitcallbacks',original_executed=True,native_executed=False,phases=618 if passed else 0,build_path=str(buildpath),build_sha256=digest,original_capture=str(out/'original/transport.json'),record_bytes=291456,per_phase_reseed=False,files=files);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).absolute(),sys.argv[2],sys.argv[3])
