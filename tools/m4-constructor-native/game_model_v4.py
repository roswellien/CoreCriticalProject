"""Exact normal CRT malloc/free FS families over inherited literal semantics."""
from pathlib import Path
import importlib.util,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('constructor_v3_frozen',R/'tools/m4-constructor-native/game_model_v3.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
I=P.I;G=P.G;ROOTS=P.ROOTS;BITS=P.BITS;ActualAPIs=P.ActualAPIs;from_original_before=P.from_original_before;source_program=P.source_program
# Family identities are the exact physical instructions, not observer PCs.
FAMILIES={'malloc':(0x780012f2,0x780012f8,0x780012f9,0x78001367,0x7800136a),
          'free':(0x7800139f,0x780013a5,0x780013a6,0x78001416,0x78001419)}
class Machine(P.Machine):
 def write(self,address,value,size=4,domain='source',pc=None):
  site=self.word(2472)if pc is None else pc
  scoped=self.constructor_active and domain=='source' and address==self.word(I.BASE['fs']) and 0x78000000<=site<0x78040000
  family=None;install=False
  if scoped:
   hit=[(name,form)for name,form in FAMILIES.items()if site in(form[2],form[4])]
   I.need(size==4 and len(hit)==1,'Only exact physical normal CRT family head write')
   family,form=hit[0];install=site==form[2];head=int.from_bytes(self.bytes(address,4),'little')
   if install:
    I.need(value==self.reg('esp')and self.accesses[-2:]==[(form[0],address,head,4,0),(form[1],value,head,4,1)],'Exact same-family CRT FS read then genuine source push then install')
   else:
    I.need(bool(self.constructor_FS),'Normal CRT restoration requires own live scope')
    frame=self.constructor_FS[-1]
    I.need(frame.get('CRT_family')==family and head==frame['frame'] and value==frame['previous'] and self.accesses[-1:]==[(form[3],frame['frame'],value,4,0)],'Exact matching live CRT family and literal saved-head read before restore')
  result=super().write(address,value,size,domain,pc)
  if scoped and install:self.constructor_FS[-1]['CRT_family']=family
  return result
