"""Bounded authenticated actual control facts; no acceptance assertions inferred."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(level,name):
 out=R/'reports/m4-vtable-controls'/name;assert not out.exists();out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or v==h;(pins.setdefault(str(p),v)==v)or sys.exit(1);return p
 s=importlib.util.spec_from_file_location('vtable_control_canonical_reader',pin(R/'tools/m4-crt-allocation-root/run_v2.py'));D=importlib.util.module_from_spec(s);s.loader.exec_module(D);a=D.DirectSet(pin(R/'reports/m4-vtable-controls/execution-r1'/level/'transport.json'),pin);facts=[]
 try:
  for c in range(27):
   live=f'case-{c}/first-live/';t=f'case-{c}/first-trigger/';b=a.data(f'case-{c}/first.bin');calls=list(struct.iter_unpack('<32Q',a.data(live+'vtable-call-witnesses.bin')));stores=list(struct.iter_unpack('<16Q',a.data(live+'vtable-source-stores.bin')));fs=list(struct.iter_unpack('<32Q',a.data(live+'fs-frame-witnesses.bin')))
   facts.append(dict(case=c,tags=list(struct.unpack_from('<32Q',b))[:18],fault=a.words(live+'locale-fault.bin',4),reason=a.data(live+'locale-fault-reason.bin').decode()if c else '',trigger=a.words(t+'identity.bin',3),intervention=a.words(t+'actual-intervention.bin',8,'Q'),calls=calls,stores=stores,FS=fs,private_name=a.data(t+'private-name.bin').decode(),current_pages=len(a.words(live+'current-page-addresses.bin',len(a.data(live+'current-page-addresses.bin'))//4))))
 finally:a.close()
 (out/'facts.json').write_text(json.dumps(facts,indent=2)+'\n');pin(__file__);(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(path=str(out/'facts.json'),sha256=sha(out/'facts.json'),cases=[dict(case=q['case'],fault=q['fault'],reason=q['reason'],calls=len(q['calls']),stores=len(q['stores']),trigger=q['trigger'])for q in facts])))
if __name__=='__main__':main(sys.argv[1],sys.argv[2])
