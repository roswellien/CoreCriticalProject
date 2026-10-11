"""Project the actual Runtime external CPU overlay at each selected callback."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-formatting-source/compare_native_fixture_v3.py';s=p.read_text()
a='G.begin_root(machine,entry);machine.cpu=B.cpu(machine.state);record=';assert s.count(a)==1
s=s.replace(a,'G.begin_root(machine,entry);n.statecpu(machine.state,machine.projected_cpu());machine.cpu=B.cpu(machine.state);record=')
target=R/'tools/m4-formatting-source/compare_native_fixture_v4.py';assert not target.exists();target.write_text(s)
