"""Literal new container/string rows and narrow owning import projections."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('accepted109_full_game_model',ROOT/'tools/m4-fs-source/game_model.py');G=importlib.util.module_from_spec(sp);sp.loader.exec_module(G)
I=G.I;SF=G.SF;begin_root=G.begin_root;complete_root=G.complete_root
def frozen(p,h):
 p=ROOT/p;I.need(hashlib.sha256(p.read_bytes()).hexdigest()==h,'Exact new container source input');return json.loads(p.read_bytes())
def source_program():
 program,callbacks=G.source_program()
 data=frozen('reports/m4-container-source/recovery-r3/instruction-contracts.json','3aeed69c05122c689a2f0951c2d49052db307beba917f5bcf756969aa7bbb09d')
 # Contract hash is checked below through its independently frozen report.
 for r in data['instructions']:
  p=r['pc'];I.need(p not in program or program[p]==r,'Identical old/new game instruction');program[p]=r
 data=frozen('reports/m4-container-source/game-callbacks-r1/callbacks.json','cdfab5c67196ff18158368766a515e1e1bd44adebecde02d8ecc4b1eb0a9bbc4')
 for p,v in data['State_offsets_by_original_PC'].items():
  p=int(p);v=tuple(v);I.need(p not in callbacks or callbacks[p]==v,'Identical old/new source callback');callbacks[p]=v
 for r in json.loads((ROOT/'reports/m4-container-source/provider-lifts-r1/instruction-contracts.json').read_bytes())['instructions']:
  p=r['pc'];I.need(p not in program,'Disjoint literal540 provider');program[p]=r
 # This normal research/game prefix executes the exact already-lifted null
 # branch. Full production provider model includes the complete free body.
 parserpath=ROOT/'tools/m4-crt-locale-batch-recovery/recover_v2.py';s=importlib.util.spec_from_file_location('container_null_operand_parser',parserpath);P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
 for r in json.loads((ROOT/'reports/m4-fs-next-plan/plan-r3/physical-CRTfreeNULL-rows.json').read_bytes()):
  row=P.instruction_contract(dict(pc=r['pc'],width=r['size'],bytes_hex=r['bytes'],mnemonic=r['mnemonic'],operands=r['operands'].split(' <')[0]));p=row['pc'];I.need(p not in program or program[p]==row,'Identical literal free null source');program[p]=row
 return program,callbacks
class Machine(G.Machine):
 def read(self,address,size=4,domain='source',pc=None):
  original_pc=self.word(2472)if pc is None else pc;value=super().read(address,size,domain,pc)
  if domain=='source'and size==4:
   pair={(0x5abdb0,0x5bb454):(0x8000021c,0x5f4020b4),(0x5abd1a,0x5bb4c8):(0x80000339,0x5f401782)}.get((original_pc,address))
   if pair:
    raw,target=pair;I.need(value==raw,'Exact raw-first new game ordinal import');self.import_projections.append((7,original_pc,address,value,target,0,0,0));return target
  return value
