"""Independent source formula crosscheck using declared hypothetical inputs only."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode=True
import interpreter as I
ROOT=I.ROOT
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import normalized,verify_manifest
from paths import publish_bytes
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main():
 out=ROOT/'reports/m4-crt-locale-batch-model-review/affine-check-r1';I.need(not out.exists(),'Fresh independent source-only crosscheck')
 files={}
 def add(p,h=None):
  p=Path(p).absolute();v=hashlib.sha256(p.read_bytes()).hexdigest();I.need(h is None or v==h,'Frozen independent crosscheck source');files[normalized(str(p))]=v;return p
 A=load('locale_check_affine',add(ROOT/'tools/m4-crt-allocation-recovery/model.py','6e0e37da74f17b511713b8b699a6809b703a19ad98d0b1eb3bedf67c95b36b61'))
 P=load('locale_check_PE',add(ROOT/'tools/m4-crt/recover_provider.py'));provider=add(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
 pe=P.PE(provider,'2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
 program,callbacks=I.source_program()
 for p in (Path(__file__),Path(I.__file__),ROOT/'reports/m4-crt-locale-batch-recovery/interface-r1/instruction-contracts.json',ROOT/'reports/m4-crt-locale-batch-recovery/callbacks-union-r1/callbacks.json'):add(p)
 rows=[];checks=0
 for size in (0,1,24,31,32,4096):
  state=bytearray(3504);fx=bytes((i*31+size)&255 for i in range(512));cpu=bytes((i*17+size)&255 for i in range(40))
  for name,off in I.REG.items():struct.pack_into('<I',state,off,{'esp':0x20001858,'ebp':0x200018b0}.get(name,0x1000+off))
  struct.pack_into('<I',state,I.BASE['fs'],0x7ffde000);struct.pack_into('<I',state,2472,0x780012b3)
  state[I.FLAGS['CF']]=1;state[I.FLAGS['OF']]=1
  memory={p:bytearray(pe.read(p-pe.base,4096)) for p in (0x7802e000,0x78035000,0x78037000)}
  memory.update({0x20000000:bytearray(4096),0x20001000:bytearray((i*11+size)&255 for i in range(4096)),0x7ffde000:bytearray(struct.pack('<I',0x12345678))})
  struct.pack_into('<II',memory[0x78035000],0,0x48450001,1);struct.pack_into('<I',memory[0x78037000],0x150,0)
  struct.pack_into('<II',memory[0x20001000],0x858,0xffffffe0,size)
  original=A.malloc_mode1(bytes(state),fx,cpu,memory,size,0x31000000)
  m=I.Machine(state,fx,cpu,memory,program,callbacks)
  def api(x,target):
   I.need(target==0x345c6 and x.reg('esp')==0x20001808,'Authentic source HeapAlloc frontier')
   I.need(tuple(x.read(x.reg('esp')+4+4*n,domain='api',pc=0x7800137f) for n in range(3))==(0x48450001,0,(max(size,1)+15)&~15),'Independent hypothetical typed HeapAlloc request')
   x.API_reads.clear();x.api_return(0x7800137f,3,0x31000000)
  m.run(lambda x:x.cursor==0xffffffe0,api)
  for key,a,b in [('State',bytes(m.state),original['state']),('FX',m.fx,original['fx']),('CPU',m.cpu,original['cpu']),('source accesses',m.accesses,original['accesses']),('PCs',m.PCs,original['PCs']),('API return',m.API_reads,original['API_return_reads']),('memory',m.memory,original['memory'])]:
   checks+=1
   if a!=b:
    extra=str(next((i for i,(u,v) in enumerate(zip(a,b)) if u!=v),None)) if isinstance(a,(bytes,list)) else ''
    raise ValueError('Independent exact malloc source formula '+key+' size='+str(size)+' firstdifference='+extra)
  rows.append(dict(size=size,source_PCs=len(m.PCs),source_accesses=len(m.accesses),source_CALLs=len(m.calls),source_RETs=len(m.returns),API_return_reads=len(m.API_reads),hypothetical_response_only=True))
 out.mkdir(parents=True)
 r=dict(schema='mw34-m4-locale-batch-independent-source-crosscheck-v1',passed=True,formula_checks=checks,malloc_declared_controls=rows,native_executed=False,API_executed=False,AFTER_machine_seed=False,files=files,physical_closure=verify_manifest(files))
 p=out/'report.json';publish_bytes(p,(json.dumps(r,sort_keys=True,indent=2)+'\n').encode());add(p)
 q=out/'pins.json';publish_bytes(q,(json.dumps(dict(schema='mw34-locale-batch-model-crosscheck-pins-v1',files=files),sort_keys=True,indent=2)+'\n').encode())
 print(json.dumps(dict(passed=True,report_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),checks=checks)))
if __name__=='__main__':main()
