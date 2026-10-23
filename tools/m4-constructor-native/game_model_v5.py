"""Exact normal CRT malloc/free FS families over inherited literal semantics."""
from pathlib import Path
import importlib.util,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('constructor_v3_frozen',R/'tools/m4-constructor-native/game_model_v3.py');P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
I=P.I;G=P.G;ROOTS=P.ROOTS;BITS=P.BITS;ActualAPIs=P.ActualAPIs;from_original_before=P.from_original_before;source_program=P.source_program
# Family identities are the exact physical instructions, not observer PCs.
FAMILIES={'malloc':(0x780012f2,0x780012f8,0x780012f9,0x78001367,0x7800136a),
          'free':(0x7800139f,0x780013a5,0x780013a6,0x78001416,0x78001419),
          'msize':(0x7800152c,0x78001532,0x78001533,0x78001596,0x78001599)}
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


def source_program(preparation):
 import hashlib,json
 program,callbacks=P.source_program(preparation)
 path=R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json';raw=path.read_bytes();I.need(hashlib.sha256(raw).hexdigest()=='9ab58b814dcc797f54b8929d7e2f8e9f9c022149b0daa40c2fe370884f6ab02d','Whole inherited accepted literal registry provider interface')
 for row in json.loads(raw)['instructions']:
  pc=row['pc'];I.need(pc not in program or (program[pc]['width'],program[pc]['bytes_hex'],program[pc]['decoded_operands'])==(row['width'],row['bytes_hex'],row['decoded_operands']),'Exact shared provider instruction');program[pc]=row
 path=R/'reports/m4-onexit-review/callbacks-r1/callbacks.json';raw=path.read_bytes();I.need(hashlib.sha256(raw).hexdigest()=='3c0a5fab10ec834c8e027ed88a8443b7d63d559c151d40ade6a045a71ce1565d','Inherited literal registry provider callbacks')
 for pc,values in json.loads(raw)['State_offsets_by_original_PC'].items():
  pc=int(pc);values=tuple(values);I.need(pc not in callbacks or callbacks[pc]==values,'Exact shared provider callback');callbacks[pc]=values
 return program,callbacks
