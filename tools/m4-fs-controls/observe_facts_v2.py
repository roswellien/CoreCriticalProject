"""Read actual control causes without asserting acceptance."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(execution,name):
 out=ROOT/'reports/m4-fs-controls'/name;assert not out.exists();out.mkdir();pins={};facts=[]
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);pins[str(p)]=v;return p
 pin(__file__);path=pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('fs_control_archive',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 e=json.loads(pin(execution).read_bytes())
 for row in e['levels']:
  a=mod.DirectSet(pin(row['capture'],row['capture_sha256']),pin)
  try:
   header=a.words('header.bin',6)
   for case in range(header[1]):
    key=f'case-{case}/first.bin'
    if key not in a.entries:continue
    b=a.data(key);tags=struct.unpack_from('<32Q',b);before=b[8880:9424];after=b[9424:9968]
    differences=[(i,before[i],after[i])for i in range(544)if before[i]!=after[i]]
    prefix=f'case-{case}/first-live/'
    fault=a.words(prefix+'locale-fault.bin',4);reason=a.data(prefix+'locale-fault-reason.bin').decode()if fault[0]else ''
    frames=list(struct.iter_unpack('<32Q',a.data(prefix+'fs-frame-witnesses.bin')))
    accesses=list(struct.iter_unpack('<IIQII',a.data(prefix+'locale-source-accesses.bin')))
    facts.append(dict(level=row['level'],case=case,tags=tags,fault=fault,reason=reason,frames=frames,hardware_differences=differences,last_source=accesses[-8:]))
    print(json.dumps(dict(level=row['level'],case=case,tags=tags[:17],fault=fault,reason=reason,last_source=accesses[-2:])),flush=True)
  finally:a.close()
 (out/'facts.json').write_text(json.dumps(dict(scope='Actual immutable causal observations only; no acceptance',cases=facts,files=pins),indent=2)+'\n')
 print(json.dumps(dict(facts_sha256=sha(out/'facts.json'))))
if __name__=='__main__':main(*sys.argv[1:])
