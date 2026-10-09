"""Authenticate a failed finite test capture without granting execution credit."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(capture,name):
 out=ROOT/'reports/m4-fs-review'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;pins[str(p)]=v;return p
 tool=pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py');sp=importlib.util.spec_from_file_location('FS_failure_reader',tool);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
 r=m.DirectSet(Path(capture).resolve(),pin)
 try:
  reason=r.data('sequence-0/selected/locale-fault-reason.bin').decode()
  frame_bytes=r.data('sequence-0/selected/fs-frame-witnesses.bin');assert len(frame_bytes)%256==0
  frames=[struct.unpack_from('<32Q',frame_bytes,i)for i in range(0,len(frame_bytes),256)]
  events=r.data('sequence-0/selected/fs-chain-events.bin');assert len(events)%128==0
  value=dict(passed=True,scope='Authenticated finite failure diagnosis only; candidate failed and initializer credit remains zero',candidate_passed=False,reason=reason,frame_count=len(frames),events=len(events)//128,frame_progress=[dict(entry=hex(x[3]),install_committed=x[15],restored=x[19],returned=x[21],predecessor=hex(x[8]),record_address=hex(x[9]))for x in frames],native_executed=True,initializer_credit=False)
 finally:r.close()
 pin(__file__);value['files']=pins;(out/'report.json').write_text(json.dumps(value,indent=2)+'\n');print(json.dumps({k:value[k]for k in('candidate_passed','reason','frame_count','events','frame_progress')}))
if __name__=='__main__':main(*sys.argv[1:])
