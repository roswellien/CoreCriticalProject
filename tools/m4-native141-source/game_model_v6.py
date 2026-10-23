"""Own literal malloc request joins; v5 instruction/FS/CPU semantics unchanged."""
from pathlib import Path
import importlib.util,sys
sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('constructor_v5_request_parent',Path(__file__).with_name('game_model_v5.py'));P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
I=P.I;G=P.G;ROOTS=P.ROOTS;BITS=P.BITS;Machine=P.Machine;from_original_before=P.from_original_before;source_program=P.source_program
class ActualAPIs(P.ActualAPIs):
 def __call__(self,m,target):
  I.need(self.index<len(self.facts),'Finite exact current API occurrence');f=self.facts[self.index]
  for owner in f.get('initial_allocations',[]):
   frames=[v for v in m.call_stack if v[0]==0x780012b3];I.need(len(frames)==1,'Exactly one genuine literal malloc invocation owns HeapAlloc birth');request=int.from_bytes(m.bytes(frames[0][1]+4,4),'little');I.need(0<request<=0xffffffe0 and f['argc']==3 and f['args'][2]==((request+15)&~15),'Literal current malloc request and actual source rounded API request')
   if 'actual_API_requested'in owner:I.need(owner['actual_API_requested']==f['args'][2],'Original measured API allocation request is rounded source request')
   else:I.need(owner['requested']==request,'Native measured owner request equals genuine literal malloc caller request')
   owner['source_requested']=request;owner['actual_API_requested']=f['args'][2];owner['requested']=request
  return super().__call__(m,target)
