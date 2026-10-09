"""Authenticate failed first install and the narrow additive store-order repair."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=ROOT/'reports/m4-fs-native/store-order-diagnosis-r1';assert not out.exists();out.mkdir()
 pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,h,v);pins[str(p)]=v;return p
 path=pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('fs_store_order_archive',path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 a=mod.DirectSet(ROOT/'reports/m4-joint-startup109-root/execution-r1/O0/transport.json',pin)
 try:
  name=next(n for n in a.entries if n.endswith('/fs-frame-witnesses.bin') and a.data(n))
  prefix=name[:-len('fs-frame-witnesses.bin')]
  frames=list(struct.iter_unpack('<32Q',a.data(name)));events=list(struct.iter_unpack('<16Q',a.data(prefix+'fs-chain-events.bin')))
  tib=a.words(prefix+'fs-current-tib.bin',5);active=a.words(prefix+'fs-active-records.bin',1)
  assert len(frames)==1 and frames[0][15]==1 and frames[0][19]==frames[0][21]==0 and len(events)==2
  assert [r[4]for r in events]==[80,81] and tib[1]==0xffffffff and active==(0,)
  old=pin(ROOT/'reports/m4-fs-native/preparation-r1/locale_batch_operations.inc');new=pin(ROOT/'reports/m4-fs-native/preparation-r2/locale_batch_operations.inc')
  before=old.read_text();after=new.read_text()
  wrong='check_source_access(a,v,n,true);fs_write_after(a,v,n);fs_owner_after(a,v,n,true);'
  right='expected_store(a,&v,n);source_access(a,v,n,true);fs_write_after(a,v,n);fs_owner_after(a,v,n,true);'
  assert wrong in before and wrong not in after and right in after
  fixed=before.replace(wrong,'check_source_access(a,v,n,true);',1).replace('expected_store(a,&v,n);source_access(a,v,n,true);',right,1)
  assert fixed==after,'Narrow hook-order change only'
  pin(ROOT/'reports/m4-fs-native/preparation-r1/report.json');pin(ROOT/'reports/m4-fs-native/preparation-r2/report.json');pin(__file__)
  report=dict(passed=True,scope='Authenticated failure cause and exact additive producer fix only; corrected native execution pending',failed_candidate_passed=False,
   cause='Substring transform matched source_access inside check_source_access, marking FS installed while actual TIB retained sentinel',actual_tib=tib,actual_active=active,actual_frame=frames[0],actual_event_points=[r[4]for r in events],only_production_semantic_change='Moved FS/owner after hooks after actual write, expected/fullnative mirror and genuine source ledger',files=pins)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
 finally:a.close()
if __name__=='__main__':main()
