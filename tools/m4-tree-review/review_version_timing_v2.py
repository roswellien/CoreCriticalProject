"""Bind the exact inserted finite CALL switch at its actual header location."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_version_timing.py');t=p.read_text()
start=t.index("  oldh=pin(old/'literals.hpp')");end=t.index("  s=importlib.util.spec_from_file_location",start)
t=t[:start]+'''  oldh=pin(old/'literals.hpp').read_text();newh=pin(new/'literals.hpp').read_text()
  extra='inline bool call_pre_store(unsigned pc){switch(pc){\\n'+''.join('case %d:return true;\\n'%x['pc']for x in timing)+'default:return false;}}\\n'
  anchor='inline const Instruction*instruction(unsigned pc)'
  assert oldh.count(anchor)==1 and newh==oldh.replace(anchor,extra+anchor)
'''+t[end:]
t=t.replace('  pin(__file__);pin(sys.executable);passed=True',"  pin(R/'tools/m4-tree-review/review_version_timing.py');pin(__file__);pin(sys.executable);passed=True")
exec(compile(t,str(Path(__file__)),'exec'),globals())
