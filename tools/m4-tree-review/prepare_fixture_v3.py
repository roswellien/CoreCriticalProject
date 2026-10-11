"""Use additive fixture whose after_phase observes already incremented phase1."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
v2=Path(__file__).resolve().parent/'prepare_fixture_v2.py'
s=v2.read_text(encoding='utf-8')
anchor="s=p.read_text(encoding='utf-8')"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\ns=s.replace(\"fixture=pin(R/'tools/m4-tree-review/fixture.inc')\",\"fixture=pin(R/'tools/m4-tree-review/fixture_v2.inc');pin(R/'tools/m4-tree-review/fixture.inc');pin(R/'tools/m4-tree-review/prepare_fixture_v2.py')\")")
exec(compile(s,str(v2),'exec'),globals())
