"""Read-only frozen original BEFORE/source chain and declared raw-page admission."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode=True
import interpreter_v2 as I
ROOT=I.ROOT
PINS={'consumer.py':'2d6f357baabea5e2fa750fb7d111bb81ab313e4fe39d05c8c613f23aef2606e8',
 'before.py':'819ec625f266e99c1ce6c7bd2209e030a00a29dd283b060c3c61b5d8aea97ea6',
 'prefix.py':'9f1eafac2333c97cc5192b0681e57d3968269617a13a1b25c7e649eb5dee716e'}
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Before:
 def __init__(self,out,add):
  core=ROOT/'tools/m4-crt-heap-return-root'
  for name,h in PINS.items():add(core/name,h)
  previous={name:sys.modules.get(name) for name in ('consumer','before')}
  self.consumer=load('locale_batch_fixed_before_consumer',core/'consumer.py');sys.modules['consumer']=self.consumer
  try:
   self.before=load('locale_batch_fixed_before',core/'before.py');sys.modules['before']=self.before
   self.prefix=load('locale_batch_fixed_prefix',core/'prefix.py')
  finally:
   for name,value in previous.items():
    if value is None:sys.modules.pop(name,None)
    else:sys.modules[name]=value
  F,M,OLD=self.consumer.F,self.consumer.M,self.consumer.OLD
  self.material=M.source_material(out);self.heap_program,self.heap_pages,self.heap_commands=self.prefix.source_material(out)
  self.material[7].update(self.heap_pages)
  self.wp,self.pp,self.gp=M.R.source_material()
  original=add(ROOT/'reports/m4-crt-fdiv-reference/run-normal-r1/original.bin','cbcb423813a712851f63a4921b72544499e74488d24184a4f084a74ae14009b2')
  self.payloads=[M.R.project(value) for value in M.R.originals(original.read_bytes())[:6]]
  self.PE=load('locale_batch_before_PE',add(ROOT/'tools/m4-crt/recover_provider.py'))
  self.provider_path=add(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
  self.pe=self.PE.PE(self.provider_path,'2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
 def row(self,row,index,level,response,declared_pages):
  program,providers,maths,ctrl,init,mainargs,argv,pages,commands=self.material
  entry,earlier=self.before.expected(row,self.payloads[index],self.wp,self.pp,self.gp,program,providers,maths,ctrl,init,mainargs,argv,pages,level)
  I.need(entry.init_complete and not entry.init_failed and not entry.args_failed and not entry.args_used and not entry.args_accesses,'Healthy original BEFORE-derived authentic mainargs seam')
  # Finite original source-page admission after the final FDIV route. Earlier
  # source checkpoints retain the sparse authenticated pack byte for byte.
  earlier['locale-original-pages-before']=self.before.stage(entry.state,entry.fx,entry.runtime_cpu,entry.mem)
  for page in (0x78004000,0x7802f000):
   entry.mem[page]=bytearray(self.pe.read(page-self.pe.base,4096))
  earlier['locale-original-pages-after']=self.before.stage(entry.state,entry.fx,entry.runtime_cpu,entry.mem)
  initial=self.prefix.predict(entry,self.heap_program,0x48450001,response)
  I.need(initial['initializer_RET'] and initial['heap_mode_value']==1,'Source-derived actual qualifying initializer RET')
  extras={}
  for page in declared_pages:
   if page in initial['memory']:continue
   I.need(0x78000000<=page<0x78042000 and page%4096==0,'Declared raw original provider research page')
   extras[page]=bytearray(self.pe.read(page-self.pe.base,4096))
  def admit(memory):
   result=copy.deepcopy(memory)
   for page,raw in extras.items():
    value=bytearray(raw)
    # Older original BEFORE models have small owned aliases for CRT globals;
    # source-computed bytes, rather than a captured whole AFTER page, extend them.
    for address,b in result.items():
     if isinstance(address,int) and page<=address and address+len(b)<=page+4096:value[address-page:address-page+len(b)]=b
    result[page]=value
   return result
  initial['memory']=admit(initial['memory'])
  fs=struct.unpack_from('<I',initial['state'],I.BASE['fs'])[0]
  initial['memory'][fs+4]=bytearray(struct.pack('<2I',0x20002000,0x20001000))
  initial['memory'][fs+0x18]=bytearray(struct.pack('<I',fs))
  for stage in list(initial['phases'].values())+list(earlier.values()):
   # Frozen source checkpoints store pages as named capture fields, not memories.
   for page,raw in extras.items():
    value=bytearray(raw)
    globals_key='crt-globals.bin'
    if globals_key in stage and page==0x78038000:value[0xee8:0xef4]=stage[globals_key]
    stage['page-'+str(page)+'.bin']=bytes(value)
  return initial,earlier,{p:bytes(initial['memory'][p]) for p in extras}
