"""Current selected103 execution directly into strict archives; no game launch."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-joint-startup103-root'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from stages import run_stage,verify_stage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(buildpath,digest,name):
 out=BASE/name;assert not out.exists();out.mkdir(parents=True);pins={};rows=[];passed=False;launched=0
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 try:
  b=json.loads(pin(buildpath,digest).read_bytes());assert b['passed'];prep=json.loads(pin(b['preparation'],b['preparation_sha256']).read_bytes());assert prep['passed']and len(prep['selected_order'])==103
  for p,h in json.loads(pin(Path(buildpath).parent/'pins.json').read_bytes())['files'].items():pin(p,h)
  game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a');crt=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7');pin(__file__);pin(sys.executable)
  dsfile=pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('strict_current54',dsfile);ds=importlib.util.module_from_spec(spec);spec.loader.exec_module(ds)
  mfc=pin(ROOT/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8')
  for level in('O0','O2'):
   worker=pin(b['workers'][level]['path'],b['workers'][level]['sha256']);capture=out/level;stage=out/(level+'-stage');launched+=1
   st=run_stage(list(map(str,(worker,game,provider,crt,mfc,capture))),stage,timeout_seconds=360,required_outputs=[capture/'transport.json'],inputs=list(pins));pin(stage/'stage.json');verify_stage(stage,sha(stage/'stage.json'));assert st['passed'],st['status']
   records=ds.DirectSet(capture/'transport.json',pin)
   try:
    assert records.words('native-header.bin',6)==(1,6,103,618,17,159716);assert records.words('sequences-header.bin',4)==(1,6,147400,17)
    entries=records.words('selected-table.bin',103);roots=records.words('registration-roots.bin',75);pages=records.words('extra-pages.bin',len(prep['extra_pages']));assert entries==tuple(x['entry']for x in prep['selected_order'])and roots==tuple(prep['registration_roots'])and pages==tuple(prep['extra_pages'])and len(set(entries))==103 and set(roots)<set(entries)
    for seq in range(6):
     tags=struct.unpack_from('<12I',records.data(f'sequence-{seq}/summary.bin'));assert tags[0]==seq and tags[4:]==(1,103,0,0,0,0,0,0)
     assert records.words(f'sequence-{seq}/spi-fault.bin',6)==(0,0,0,0,1,1)
     for phase,entry in enumerate(entries):
      prefix=f'sequence-{seq}/phase-{phase}';record=records.data(prefix+'.bin');assert len(record)==159716;words=struct.unpack_from('<9I',record);assert words[0]==seq and words[2]==phase and words[4]==entry and words[7]==0
      for point in('before','after'):
       assert len(records.data(prefix+'-'+point+'-registry.bin'))==256
       for page in pages:assert len(records.data(prefix+'-'+point+'-page-'+str(page)+'.bin'))==4096
     assert 1<=records.words(f'sequence-{seq}/growth-replay-count.bin',1)[0]<=512
    assert records.data('COMPLETE.txt')==b'Six persistent103-root sequences and genuine source growth/cleanup complete; fullM4 incomplete\n'
    rows.append(dict(level=level,stage=str(stage/'stage.json'),stage_sha256=sha(stage/'stage.json'),capture=str(capture/'transport.json'),logical_files=len(records.entries),payload_bytes=records.value['payload_bytes'],elapsed_seconds=st['elapsed_seconds']))
   finally:records.close()
   for p,h in pins.items():assert sha(p)==h,('Unchanged input',p)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual native selected103 + directed source growth/cleanup; structural run only, independent semantic comparison still required',build_path=str(buildpath),build_sha256=digest,levels=rows,files=pins,native_executed=bool(launched),initializer_credit=False,whole_M4_complete=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
