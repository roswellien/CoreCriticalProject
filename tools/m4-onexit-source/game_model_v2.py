"""Additive literal FNSTSW cache materialization and lower-tail callback attribution.

The frozen architectural game model remains intact. These additions expose
exact Remill State representation effects required by whole3504 comparison;
no numerical result or candidate AFTER byte enters the model.
"""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('frozen_onexit_game_architecture',ROOT/'tools/m4-onexit-source/game_model.py');G=importlib.util.module_from_spec(spec);spec.loader.exec_module(G)
I=G.I;SF=G.SF;u16=G.u16;put16=G.put16;begin_root=G.begin_root;complete_root=G.complete_root
def source_program():
 rows,callbacks=G.source_program();path=ROOT/'reports/m4-onexit-source/tail-receipt-r1/callbacks.json'
 I.need(hashlib.sha256(path.read_bytes()).hexdigest()=='9317687a6f188709479dc00a7a9406ed38463ac3d3f2bc7125b3456ca429cbd0','Exact new lower-tail callback original attribution')
 extra={int(k):tuple(v)for k,v in json.loads(path.read_bytes())['State_offsets_by_original_PC'].items()}
 for pc,offsets in extra.items():I.need(pc in rows and (pc not in callbacks or callbacks[pc]==offsets),'Identical exact original tail callback');callbacks[pc]=offsets
 return rows,callbacks
class Machine(G.Machine):
 def step(self):
  pc=self.cursor;row=self.program.get(pc);super().step()
  if row['mnemonic']=='fnstsw':
   # Original Remill FNSTSW computes the shadow status and stores that value
   # into both State.fxsave.swd and its actual AX destination. The source
   # architectural SW/result was already computed by the frozen parent.
   put16(self.state,2770,self.fp_status())
