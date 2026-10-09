"""Additive original game and MFC source model. No native AFTER inputs."""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('accepted71_full_game_model',ROOT/'tools/m4-strings-source/game_model.py');G=importlib.util.module_from_spec(sp);sp.loader.exec_module(G)
I=G.I;SF=G.SF;begin_root=G.begin_root;complete_root=G.complete_root
def frozen(path,h):
 p=ROOT/path;I.need(hashlib.sha256(p.read_bytes()).hexdigest()==h,'Exact new original MFC source interface');return json.loads(p.read_bytes())
def source_program():
 program,callbacks=G.source_program()
 data=json.loads((ROOT/'reports/m4-mfc-source/recovery-r4/instruction-contracts.json').read_bytes())
 for r in data['instructions']:
  pc=r['pc'];I.need(pc not in program or program[pc]==r,'Identical reused original game instruction');program[pc]=r
 data=frozen('reports/m4-mfc-source/game-callbacks-r1/callbacks.json','b4e0130a8243db989bf5669f8df725beaecff2be00c58983a37de08bf7c3c2f7')
 for pc,offsets in data['State_offsets_by_original_PC'].items():
  pc=int(pc);offsets=tuple(offsets);I.need(pc not in callbacks or callbacks[pc]==offsets,'Exact source callback identity');callbacks[pc]=offsets
 data=frozen('reports/m4-mfc-review/interface-r1/instruction-contracts.json','94fddd9fc34c0d1dff5100ae8a9f5c66b39e66854a1e5a2d07ac81966656dfeb')
 for r in data['instructions']:
  pc=r['pc'];I.need(pc not in program,'Disjoint MFC original source PCs');program[pc]=r
 for pc,offsets in data['callbacks_by_original_PC'].items():
  pc=int(pc);offsets=tuple(offsets);I.need(pc not in callbacks or callbacks[pc]==offsets,'Exact provider callback identity');callbacks[pc]=offsets
 return program,callbacks
class Machine(G.Machine):
 def read(self,address,size=4,domain='source',pc=None):
  original_pc=self.word(2472)if pc is None else pc
  value=super().read(address,size,domain,pc)
  if domain=='source'and size==4:
   pair={(0x5f401ea1,0x5f49814c):(0x78001498,0x780012b3),(0x5f401786,0x5f498148):(0x7800138a,0x78001390)}.get((original_pc,address))
   if address==0x5bb4bc:
    I.need(original_pc==0x5abd26,'Exact game MFC owning import source PC');pair=(0x80000337,0x5f401ea0)
   if pair:
    raw,target=pair;I.need(value==raw,'Exact raw-first MFC import relocation');self.import_projections.append((6,original_pc,address,value,target,0,0,0));return target
  return value
