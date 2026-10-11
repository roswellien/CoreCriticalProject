"""Authorized one-reader, bounded retained phase47 registry diagnostic."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-joint-startup138'/name;assert not out.exists();out.mkdir();pins={};opened=False;closed=True;rows=[];ds=None;passed=False
 def pin(p,h=None):p=Path(p).resolve();v=sha(p);assert h is None or h==v;assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 try:
  e=pin(R/'reports/m4-joint-startup138-root/execution-r1/report.json','87c9af9e76003962dbf8ada12a5c56e32376a824aee6294abd85f7998f6b85ce');assert json.loads(e.read_bytes())['passed']is False;script=pin(R/'tools/m4-crt-allocation-root/run_v2.py');spec=importlib.util.spec_from_file_location('registry138_failed_DS',script);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);ds=m.DirectSet(R/'reports/m4-joint-startup138-root/execution-r1/O0/transport.json',pin);opened=True;closed=False;names=sorted(ds.entries);(out/'logical-inventory.json').write_text(json.dumps(names,indent=2)+'\n');selected=[n for n in names if n.startswith('sequence-0/selected/')];(out/'selected-inventory.json').write_text(json.dumps(selected,indent=2)+'\n')
  keep={'FAILURE.txt','CLEANUP-FAILURE.txt','sequence-0/summary.bin'}
  for n in names:
   if n in keep or n.startswith('sequence-0/phase-47-before-') or n.startswith('sequence-0/Widget/root-4691344/') or n.startswith('sequence-0/selected/')and(any(v in n for v in('registry-summary','registry-growth','source-accesses','native-api-witness','allocation-','registry-research-projections','locale-registry'))):
    b=ds.data(n)
    # Keep bounded scalar/input/owner ledgers; whole Game images are irrelevant
    # to the exact producer owner obligation and are not duplicated here.
    if len(b)<=2*1024*1024:
     p=out/'retained'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);rows.append(dict(logical=n,size=len(b),sha256=hashlib.sha256(b).hexdigest(),path=str(p.resolve())))
  if 'sequence-0/selected/registry-summary.bin'in names:
   w=ds.words('sequence-0/selected/registry-summary.bin',32,'Q');print(json.dumps(dict(registry_summary=w)),flush=True)
  print(json.dumps(dict(selected_logical_files=len(selected),retained=len(rows),selected_names=[n for n in selected if any(k in n for k in('allocation','registry-summary','growth'))][:100])),flush=True)
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if ds is not None:ds.close();del ds;closed=True
  for p in out.rglob('*'):
   if p.is_file():pin(p)
  pin(__file__);pin(sys.executable);report=dict(passed=passed,scope='Retained failure diagnostic only; one strictly authenticated current failed O0 reader, bounded selected owner/source/frame records exported unchanged',execution_sha256='87c9af9e76003962dbf8ada12a5c56e32376a824aee6294abd85f7998f6b85ce',reader_opened=opened,all_readers_closed=closed,retained=rows,initializer_credit=0,files=pins);p=out/'report.json';p.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,reader_closed=closed,path=str(p),sha256=sha(p))))
if __name__=='__main__':main(sys.argv[1])
