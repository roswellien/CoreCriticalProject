"""Use explicit guest-mutating API tokens rather than the Win32 MBI State field."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_joint138_gdi_source.py');t=p.read_text()
assert t.count("('State','Runtime','memory().write'")==1
t=t.replace("('State','Runtime','memory().write'","('std::construct_at','remill_state','memory().write'")
t=t.replace('  pin(__file__);pin(sys.executable)',"  pin(R/'tools/m4-tree-review/review_joint138_gdi_source.py');pin(__file__);pin(sys.executable)")
exec(compile(t,str(Path(__file__)),'exec'),globals())
