"""Add literal game/string rows to the frozen independent source machine."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('accepted54_game_model',ROOT/'tools/m4-onexit-source/game_model_v2.py');G=importlib.util.module_from_spec(sp);sp.loader.exec_module(G)
I=G.I;SF=G.SF;begin_root=G.begin_root;complete_root=G.complete_root
def frozen(path,digest):
 p=ROOT/path;I.need(hashlib.sha256(p.read_bytes()).hexdigest()==digest,'Exact literal source contract '+path);return json.loads(p.read_bytes())
def source_program():
 rows,callbacks=G.source_program();extra=frozen('reports/m4-strings-source/recovery-r7/instruction-contracts.json','e1a4a4e2a6f1d55b5a1a94b10254202e88304e67dfbedd77326e72f0986e97a9')
 for row in extra['instructions']:
  pc=row['pc'];I.need(pc not in rows or rows[pc]==row,'Identical overlapping literal game instruction');rows[pc]=row
 cb=frozen('reports/m4-strings-source/game-callbacks-r1/callbacks.json','b881e7ed9d73bcae8bdaebf83b88046ebdc4a8221ed63c95490d32da3380b4ad')
 for pc,offsets in cb['State_offsets_by_original_PC'].items():
  pc=int(pc);offsets=tuple(offsets);I.need(pc not in callbacks or callbacks[pc]==offsets,'Identical game callback order');callbacks[pc]=offsets
 sp=importlib.util.spec_from_file_location('new_literal_string_provider',ROOT/'tools/m4-strings-review/provider_model.py');S=importlib.util.module_from_spec(sp);sp.loader.exec_module(S)
 p=ROOT/'reports/m4-strings-review/interface-r2/instruction-contracts.json';more,cb=S.source_program(p)
 for pc,row in more.items():I.need(pc not in rows or rows[pc]==row,'Identical provider instruction');rows[pc]=row
 for pc,offsets in cb.items():I.need(pc not in callbacks or callbacks[pc]==offsets,'Identical provider callbacks');callbacks[pc]=offsets
 return rows,callbacks
class Machine(G.Machine):
 def read(self,address,size=4,domain='source',pc=None):
  value=super().read(address,size,domain,pc)
  if domain=='source'and size==4 and address==0x5bb670:
   I.need(value==0x1df886,'Exact raw owning game _strdup IAT');self.import_projections.append((5,self.word(2472),address,value,0x78010a6d,0,0,0));return 0x78010a6d
  return value
