"""Extract only four failure witnesses from the terminal failed141 capture."""
from pathlib import Path
import hashlib,json,struct,sys
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 out=R/'reports/m4-startup141-root/failure-diagnostic-r1';assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v;pins[str(p)]=v;return p
 ep=pin(R/'reports/m4-startup141-root/execution-r1/report.json','4c46600d5f5f9bd2e95721493e268cb28c2228d289720ffb77789c99f8a494c3');e=json.loads(ep.read_bytes());assert not e['passed']and e['all_workers_terminal']and e['actual_workers_launched']==1
 p=pin(e['runs']['O0']['capture']);t=json.loads(p.read_bytes());assert t['passed']and t['format']=='mw34.capture.direct.v1'and t['transport_only']and not t['native_executed']
 desired={f'sequence-0/selected/{v}'for v in('locale-fault-reason.bin','locale-fault.bin','registry-exception-message.bin','registry-exception-witness.bin')};found={};names=set();total=0
 for part in t['parts']:
  bundle=pin(p.parent/part['bundle'],part['sha256'])
  with bundle.open('rb')as f:
   magic,length,digest=struct.unpack('<8sQ32s',f.read(48));assert magic==b'MW34CAP1'and length==part['index_bytes']and digest.hex()==part['index_sha256'];raw=f.read(length);assert hashlib.sha256(raw).digest()==digest;index=json.loads(raw);assert len(index['files'])==part['logical_files']and index['total_bytes']==part['payload_bytes']and bundle.stat().st_size==part['bundle_bytes'];end=0
   for row in index['files']:
    assert row['offset']==end and row['path'].casefold()not in names;names.add(row['path'].casefold());end+=row['size']
    if row['path']in desired:
     f.seek(48+length+row['offset']);b=f.read(row['size']);assert hashlib.sha256(b).hexdigest()==row['sha256'];q=out/Path(row['path']).name;q.write_bytes(b);pin(q);found[row['path']]=dict(path=str(q),bytes=len(b),sha256=sha(q),hex=b.hex())
   assert end==part['payload_bytes'];total+=len(index['files'])
 assert total==t['logical_files']and set(found)==desired
 for q,h in pins.items():assert sha(q)==h
 pin(__file__);pin(sys.executable);q=out/'report.json';q.write_text(json.dumps(dict(passed=True,scope='Four diagnostic records only from whole-hash-authenticated terminal failed capture; no complete logical validation or acceptance',records=found,all_readers_closed=True,initializer_credit=0,files=pins),indent=2)+'\n');print(sha(q));print(json.dumps(found))
if __name__=='__main__':main()
