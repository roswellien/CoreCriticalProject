"""Current changed connected28 direct execution; no game launch."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-joint-startup28-root'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from stages import run_stage,verify_stage
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(buildpath,digest,name,controls=False):
 out=BASE/name;assert not out.exists();out.mkdir(parents=True);pins={};rows=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);pins[str(p)]=v;return p
 try:
  b=json.loads(pin(buildpath,digest).read_bytes());assert b['passed']
  for p,h in json.loads(pin(Path(buildpath).parent/'pins.json').read_bytes())['files'].items():pin(p,h)
  game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a');pin(__file__)
  dsfile=pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('strict_current28',dsfile);ds=importlib.util.module_from_spec(spec);spec.loader.exec_module(ds)
  for level in('O0','O2'):
   worker=pin(b['workers'][level]['path'],b['workers'][level]['sha256']);capture=out/level;stage=out/(level+'-stage')
   st=run_stage(list(map(str,(worker,game,provider,capture))),stage,timeout_seconds=120,required_outputs=[capture/'transport.json'],inputs=list(pins));pin(stage/'stage.json');verify_stage(stage,sha(stage/'stage.json'));assert st['passed'],st['status']
   records=ds.DirectSet(capture/'transport.json',pin)
   try:
    if controls:
     version,cases,attempts,stride,pages,native=records.words('header.bin',6);assert (version,cases,attempts,pages,native)==(1,14,28,17,159716)
     for k in range(14):
      a=records.data(f'case-{k}/first.bin');r=records.data(f'case-{k}/retry.bin');assert len(a)==len(r)==stride
      at=struct.unpack_from('<24I',a);rt=struct.unpack_from('<24I',r);assert at[:3]==(k,0,int(k==0))and rt[:3]==(k,1,0);assert at[3]==(28 if k==0 else 15 if k==12 else 14);assert at[23]==at[3]and rt[3]==rt[23]==at[3];assert at[8]==rt[8]and at[7]==rt[7];assert at[14]==int(k==0 or 9<=k<=12);assert at[15]==int(k in(0,12));assert at[22]==rt[22]==0x4d573328
     count=records.words('counts.bin',3);assert count[1:]==(14,28)and count[0]>100;assert records.data('COMPLETE.txt')==b'Independent connected28 controls passed\n'
    else:
     assert records.words('native-header.bin',6)==(1,6,28,168,17,159716)
     assert records.words('sequences-header.bin',4)==(1,6,147400,17)
     for seq in range(6):
      tags=struct.unpack_from('<12I',records.data(f'sequence-{seq}/summary.bin'));assert tags[0]==seq and tags[4:]==(1,28,0,0,0,0,0,0)
      identity=records.data(f'sequence-{seq}/spi-identity.bin');assert len(identity)==4640;sc=struct.unpack_from('<8Q',identity);assert sc[0]==1 and sc[2]==sc[3]==sc[5]and sc[1]and sc[4]and sc[2]>0xffffffff
      assert identity[64:96].rstrip(b'\0')==b'SystemParametersInfoA'
      for off,h in((544,identity[416:480]),(2592,identity[480:544])):
       path=identity[off:off+2048].decode('utf-16-le').split('\0')[0];pin(path,h.decode())
      witness=records.words(f'sequence-{seq}/spi-witness.bin',16,'Q');assert witness[0]==1 and witness[1]==sc[2]and witness[2]>0xffffffff and witness[3:7]==(48,0,0x608fa0,0)and witness[11:]==(0x200017e0,0x482ce3,16,1,1)
      assert records.words(f'sequence-{seq}/spi-fault.bin',6)==(0,0,0,0,1,1)
      for phase in range(28):assert len(records.data(f'sequence-{seq}/phase-{phase}.bin'))==159716
     assert records.data('COMPLETE.txt')==b'Six persistent28-root sequences complete; fullM4 incomplete\n'
    rows.append(dict(level=level,stage=str(stage/'stage.json'),stage_sha256=sha(stage/'stage.json'),capture=str(capture/'transport.json'),logical_files=len(records.entries),elapsed_seconds=st['elapsed_seconds']))
   finally:records.close()
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Independent compiled fault/outside-return controls'if controls else'Actual native connected28 changed corpus direct execution',build_path=str(buildpath),build_sha256=digest,levels=rows,files=pins,native_executed=True,initializer_credit=False,whole_M4_complete=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3],'--controls'in sys.argv[4:])
