"""Read-only inspection of direct control diagnostics; no execution or model seeds."""
from pathlib import Path
import hashlib,importlib.util,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
def pin(p,h=None):
 p=Path(p)
 with p.open('rb')as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
 if h is not None and actual!=h:raise ValueError('Changed physical input')
 return p
spec=importlib.util.spec_from_file_location('control_diagnostic_direct',ROOT/'tools/m4-crt-allocation-root/run_v2.py');D=importlib.util.module_from_spec(spec);spec.loader.exec_module(D)
a=D.DirectSet(ROOT/sys.argv[1],pin)
try:
 for n in range(14):
  p=f'case-{n}/first-live/';raw=a.data(f'case-{n}/first.bin');tags=struct.unpack_from('<32Q',raw);fault=a.words(p+'locale-fault.bin',4);provider=a.words(p+'registry-summary.bin',32,'Q')
  msg=a.data(p+'registry-exception-message.bin').decode();sr=list(struct.iter_unpack('<32Q',a.data(p+'strings-witnesses.bin')));alloc=list(struct.iter_unpack('<16Q',a.data(p+'locale-allocations.bin')))
  ledger=list(struct.iter_unpack('<IIQII',a.data(p+'locale-source-accesses.bin')))
  print(n,'prefix',tags[4],'Contextfault',[hex(v)for v in tags[15:20]],'locale',[hex(v)for v in fault],'Registry',[hex(v)for v in provider[15:19]],'message',msg)
  print('string',[[hex(q[i])for i in(5,6,8,9,10,13,14,16,17,20,21,22,26,27)]for q in sr[:1]],'alloc',len(alloc),'copy',a.words(f'case-{n}/first-trigger-copy.bin',5,'Q'))
  print('source-tail',[(hex(pc),hex(addr),hex(v),size,write)for pc,addr,v,size,write in ledger[-5:]])
finally:a.close()
