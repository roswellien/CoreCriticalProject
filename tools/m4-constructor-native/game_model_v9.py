"""Exact v8 observer transparency also at typed API frame/input seams."""
from pathlib import Path
import importlib.util,sys
sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('constructor_v8_api_shadow_parent',Path(__file__).with_name('game_model_v8.py'));P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
I=P.I;G=P.G;ROOTS=P.ROOTS;BITS=P.BITS;from_original_before=P.from_original_before;source_program=P.source_program
class Machine(P.Machine):
 def observer_live_bytes(self,address,size):
  if self.observer_shadow is not None:
   start=max(address,0x20001000);end=min(address+size,0x20002000)
   if start<end:
    I.need(self.bytes(start,end-start)==self.observer_shadow[start-0x20001000:end-0x20001000],'Exact observer stack transparency for every typed provider frame/input byte');self.observer_read_checks+=1
class ActualAPIs(P.ActualAPIs):
 def __call__(self,m,target):
  I.need(self.index<len(self.facts),'Finite exact current API occurrence');fact=self.facts[self.index];m.observer_live_bytes(m.reg('esp'),4+4*fact['argc'])
  for b in fact.get('input_buffers',[]):m.observer_live_bytes(b['address'],b['bytes'])
  for owner in fact.get('initial_allocations',[]):
   frames=[v for v in m.call_stack if v[0]==0x780012b3];I.need(len(frames)==1,'Exactly one genuine malloc frame for live provider request');m.observer_live_bytes(frames[0][1]+4,4)
  return super().__call__(m,target)
