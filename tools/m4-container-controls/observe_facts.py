"""Bounded authenticated observations; no acceptance or whole-payload validation claim."""
from pathlib import Path
import hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(execution,name):
 out=ROOT/'reports/m4-container-controls'/name;assert not out.exists();out.mkdir();facts=[];pins={str(Path(__file__).resolve()):sha(__file__)}
 e=json.loads(Path(execution).read_bytes());pins[str(Path(execution).resolve())]=sha(execution)
 for level in e['levels']:
  path=Path(level['capture']);assert sha(path)==level['capture_sha256'];pins[str(path)]=level['capture_sha256'];v=json.loads(path.read_bytes());entries={};streams=[]
  try:
   for part in v['parts']:
    p=path.parent/part['bundle'];assert sha(p)==part['sha256'];pins[str(p)]=part['sha256'];f=p.open('rb');streams.append(f);magic,n,digest=struct.unpack('<8sQ32s',f.read(48));raw=f.read(n);assert magic==b'MW34CAP1'and hashlib.sha256(raw).digest()==digest
    for x in json.loads(raw)['files']:entries[x['path']]=(f,48+n+x['offset'],x['size'],x['sha256'])
   def data(key):
    f,off,n,h=entries[key];f.seek(off);b=f.read(n);assert len(b)==n and hashlib.sha256(b).hexdigest()==h;return b
   def words(key,fmt):return struct.unpack(fmt,data(key))
   for c in range(34):
    live=f'case-{c}/first-live/';p=f'case-{c}/first-trigger/';fault=words(live+'locale-fault.bin','<4I');reason=data(live+'locale-fault-reason.bin').decode()if fault[0]else''
    row=dict(level=level['level'],case=c,fault=fault,reason=reason,tags=struct.unpack_from('<32Q',data(f'case-{c}/first.bin')),trigger=words(p+'identity.bin','<3I'),null=words(p+'nullfree.bin','<32Q'),borrowed=words(p+'borrowed.bin','<32Q'),vector=words(p+'vector.bin','<16Q'),mfc=words(p+'mfc.bin','<32Q'),string=words(p+'string.bin','<32Q'))
    facts.append(row);print(json.dumps({k:row[k]for k in('level','case','fault','reason','trigger')}),flush=True)
  finally:
   for f in streams:f.close()
 report=dict(scope='Bounded actual immutable record observations; no acceptance. Whole partSHA and each selected recordSHA checked; not independent complete logical-payload validation.',cases=facts,files=pins);(out/'facts.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(facts_sha256=sha(out/'facts.json'))))
if __name__=='__main__':main(*sys.argv[1:])
