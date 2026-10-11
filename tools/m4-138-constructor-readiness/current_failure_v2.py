"""Strict current failed O0 diagnostic export with finally-closed reader."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-138-constructor-readiness'/name;assert not out.exists();out.mkdir(parents=True)
 pins={};data=None;closed=True;passed=False;views={};e={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h,str(p);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 try:
  ep=pin(R/'reports/m4-constructor-native/fixture-execution-r3/report.json','a886ed1c80e0d9eb0387dde5a8a6660fdc085dc6a3e6953685a714620719985d');e=json.loads(ep.read_bytes())
  assert not e['passed']and e['all_workers_terminal']and e['actual_workers_launched']==1
  assert set(e['runs'])=={'O0'}and not e['runs']['O0']['stage_passed']
  stage=json.loads(pin(e['runs']['O0']['stage'],e['runs']['O0']['stage_sha256']).read_bytes());assert not stage['passed']and stage['exit_code']==1
  module=pin(R/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('current_constructor_failed_direct',module);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
  closed=False;data=m.DirectSet(Path(e['runs']['O0']['capture']),pin)
  selected=[n for n in data.entries if n=='FAILURE.txt'or n.startswith('sequence-0/selected/')and any(x in n for x in('fault','exception','constructor','source-access','source-store','FS','fs-'))]
  assert selected and len(selected)<250
  (out/'selected-diagnostic-inventory.json').write_text(json.dumps(selected,indent=2)+'\n');pin(out/'selected-diagnostic-inventory.json')
  for n in selected:
   b=data.data(n);assert len(b)<32*1024*1024
   p=out/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);pin(p)
   view=dict(bytes=len(b),sha256=sha(p))
   if any(x in n for x in('reason','message','FAILURE.txt')):view['text']=b.decode()
   if n.endswith('locale-fault.bin'):assert len(b)==16;view['words']=list(struct.unpack('<4I',b))
   if n.endswith('registry-exception-witness.bin'):view['words']=list(struct.unpack('<4I',b))
   views[n]=view
  passed=True
 finally:
  if data is not None:data.close();data=None
  closed=True
  pin(__file__);pin(sys.executable)
  for p,h in pins.items():assert sha(p)==h,p
  report=dict(passed=passed,scope='Current failed r9 O0 strict diagnostic export only; no success/equivalence/accepted credit',
   execution_sha256='a886ed1c80e0d9eb0387dde5a8a6660fdc085dc6a3e6953685a714620719985d',reader_closed=closed,
   canonical_reader_opened=True,initializer_credit=0,native_execution_performed=False,views=views,files=pins)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,reader_closed=closed,path=str(q),sha256=sha(q),views=views)))
if __name__=='__main__':main(sys.argv[1])
