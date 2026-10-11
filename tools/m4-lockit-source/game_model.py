"""Persistent original-only four-Lockit source extension after accepted120.

Game/provider rows are literal. Provider state2 must come from the genuine DLL
loader input page; this model cannot seed it, initialize a CS, or invent API
results. A caller supplies finite actual typed Windows API witnesses through
the inherited source interpreter seam. Cold and contended provider PCs remain
outside the admitted program.
"""
from pathlib import Path
import hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('accepted120_Lockit_game',ROOT/'tools/m4-next-source/game_model.py');G=importlib.util.module_from_spec(s);s.loader.exec_module(G)
I=G.I;SF=G.SF;begin_root=G.begin_root;complete_root=G.complete_root
def frozen(path,expected):
 raw=(ROOT/path).read_bytes();I.need(hashlib.sha256(raw).hexdigest()==expected,'Exact additive Lockit source contract');return json.loads(raw)
def source_program():
 program,callbacks=G.source_program()
 game=frozen('reports/m4-lockit-source/recovery-r1/instruction-contracts.json','c102e277742f2cd6e2a352f9e40f44f7d7d2ea1107d8bde242d103b586e75f25')
 provider=frozen('reports/m4-lockit-source/provider-interface-r1/instruction-contracts.json','97419d4f2ba54e078dc1bb32f8f368ac8b5c757f40dbd9ac780d32c2faf453fd')
 for row in game['instructions']+provider['instructions']:
  pc=row['pc'];I.need(pc not in program or program[pc]==row,'Identical retained/additive original instruction');program[pc]=row
 new=frozen('reports/m4-lockit-source/game-callbacks-r1/callbacks.json','bf22c3a6a9167c408c7f23ae09d6987a1c1448474411f131a0590ead30040147')
 for pc,offsets in new['State_offsets_by_original_PC'].items():
  pc=int(pc);offsets=tuple(offsets);I.need(pc not in callbacks or callbacks[pc]==offsets,'Exact additive LLVM undefined callback order');callbacks[pc]=offsets
 # The full compiled constructor interval retains two cold undefined sites.
 # Both are outside the initialized-path program and receive no source credit.
 return program,callbacks

GAME_IMPORTS={
 (0x4125d4,0x5bb4f8):(0x1df582,0x7810a290,0x20),
 (0x412648,0x5bb4f4):(0x1df568,0x7810a350,0x20),
 (0x4dc193,0x5bb4f8):(0x1df582,0x7810a290,0x10),
 (0x4dc207,0x5bb4f4):(0x1df568,0x7810a350,0x10),
 (0x500d04,0x5bb4f8):(0x1df582,0x7810a290,0x20),
 (0x500d78,0x5bb4f4):(0x1df568,0x7810a350,0x20),
 (0x596b33,0x5bb4f8):(0x1df582,0x7810a290,0x10),
 (0x596ba7,0x5bb4f4):(0x1df568,0x7810a350,0x10),
}
FAST_PCS={0x7810a290,0x7810a295,0x7810a296,0x7810a297,0x7810a29a,0x7810a29c,0x7810a306,0x7810a30b,0x7810a311,0x7810a313,0x7810a314,0x7810a315,0x7810a350,0x7810a357,0x7810a359,0x7810a35e,0x7810a364}
class Machine(G.Machine):
 def __init__(self,*a,**k):
  super().__init__(*a,**k);self.lockit_import_proofs=[];self.lockit_state_reads=[]
 def read(self,address,size=4,domain='source',pc=None):
  original_pc=self.word(2472)if pc is None else pc;value=super().read(address,size,domain,pc)
  if domain=='source'and size==4:
   named=GAME_IMPORTS.get((original_pc,address))
   if named is not None:
    raw,target,offset=named;I.need(value==raw,'Read-time exact owning game MSVCP import')
    I.need(self.reg('ecx')==(self.reg('esp')+offset)&0xffffffff,'Exact original LEA-established scratch ECX before source CALL')
    self.lockit_import_proofs.append(dict(PC=original_pc,slot=address,raw=value,target=target,ECX=self.reg('ecx'),before_CALL_ESP=self.reg('esp'),scratch_offset=offset,call_target_frame_offset=offset+4))
    self.import_projections.append((8,original_pc,address,value,target,0,0,0));return target
   if address==0x78145658 and original_pc in(0x7810a290,0x7810a350):
    I.need(value==2,'Authentic admitted original postDllMain state2; no initialized-state seed')
    self.lockit_state_reads.append((original_pc,address,value))
  return value
 def step(self):
  pc=self.cursor
  if 0x7810a290<=pc<=0x7810a364:I.need(pc in FAST_PCS,'Coldstate0/contendedstate1 provider instructions are outside initialized source domain')
  return super().step()
