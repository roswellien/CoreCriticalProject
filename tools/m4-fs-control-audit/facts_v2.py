"""Read actual isolated FS control causes, without acceptance or mutations."""
import hashlib,importlib.util,json,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main(outname):
 out=R/'reports/m4-fs-control-audit'/outname;assert not out.exists();out.mkdir();pins={};facts=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);pins[str(p)]=v;return p
 spec=importlib.util.spec_from_file_location('fs_audit_direct',pin(R/'tools/m4-crt-allocation-root/run_v2.py'));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 e=json.loads(pin(R/'reports/m4-fs-controls/execution-r2/report.json','ba68d95c8f8ed3027c5e6ce623123aed55b76d67b0dcf47fa9a97fae7c503503').read_bytes())
 for row in e['levels']:
  a=mod.DirectSet(pin(row['capture'],row['capture_sha256']),pin)
  try:
   assert a.words('header.bin',6)==(1,24,48,9968,6,10)
   for case in range(24):
    b=a.data(f'case-{case}/first.bin');tags=struct.unpack_from('<32Q',b);prefix=f'case-{case}/first-live/';trigger=f'case-{case}/first-trigger/'
    fault=a.words(prefix+'locale-fault.bin',4);reason=a.data(prefix+'locale-fault-reason.bin').decode()if fault[0]else ''
    frames=list(struct.iter_unpack('<32Q',a.data(prefix+'fs-frame-witnesses.bin')))
    accesses=list(struct.iter_unpack('<IIQII',a.data(prefix+'locale-source-accesses.bin')))
    mfc=list(struct.iter_unpack('<32Q',a.data(prefix+'mfc-allocation-witnesses.bin')))
    trig={n:list(struct.unpack('<'+('I'if n in ('TIB','record')else'Q')*(len(a.data(trigger+n+'.bin'))//(4 if n in ('TIB','record')else 8)),a.data(trigger+n+'.bin')))for n in ('frame','chain','owner','mfc','TIB','record')}
    f=dict(level=row['level'],case=case,tags=tags,fault=fault,reason=reason,frames=frames,mfc=mfc,trig=trig,last_source=accesses[-12:]);facts.append(f)
    print(json.dumps(dict(level=row['level'],case=case,tags=tags[:17],fault=fault,reason=reason,last_source=accesses[-2:],frame=trig['frame'][:23],owner=trig['owner'])),flush=True)
  finally:a.close()
 pin(__file__);(out/'facts.json').write_text(json.dumps(dict(scope='Actual immutable raw cause observations; no acceptance',cases=facts,files=pins),indent=2)+'\n');print(json.dumps(dict(facts_sha256=sha(out/'facts.json'))))
if __name__=='__main__':main(*sys.argv[1:])
