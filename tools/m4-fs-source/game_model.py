"""Additive literal game FS0 source model. No candidate AFTER inputs."""
from pathlib import Path
import hashlib, importlib.util, json, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sp=importlib.util.spec_from_file_location('accepted103_full_game_model',ROOT/'tools/m4-mfc-source/game_model.py')
G=importlib.util.module_from_spec(sp);sp.loader.exec_module(G)
I=G.I;SF=G.SF;begin_root=G.begin_root;complete_root=G.complete_root

def frozen(path,h):
 p=ROOT/path;I.need(hashlib.sha256(p.read_bytes()).hexdigest()==h,'Exact new original FS source interface');return json.loads(p.read_bytes())

def source_program():
 program,callbacks=G.source_program()
 data=json.loads((ROOT/'reports/m4-fs-source/recovery-r3/instruction-contracts.json').read_bytes())
 for r in data['instructions']:
  pc=r['pc'];I.need(pc not in program or program[pc]==r,'Identical reused original game instruction');program[pc]=r
 data=frozen('reports/m4-fs-source/game-callbacks-r1/callbacks.json','978ad7e2a64b8a860ba0af521da6adebaea1197a3059ec84347d03a9fdf33386')
 for pc,offsets in data['State_offsets_by_original_PC'].items():
  pc=int(pc);offsets=tuple(offsets);I.need(pc not in callbacks or callbacks[pc]==offsets,'Exact source callback identity');callbacks[pc]=offsets
 return program,callbacks

class Machine(G.Machine):
 """Original FS segment addressing is inherited unchanged from the interpreter."""
 pass
