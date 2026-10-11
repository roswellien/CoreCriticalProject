"""Use architectural CPU from the literal prefix State, matching its source PC."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-formatting-source/compare_native_fixture_v7.py';s=p.read_text();a="equal(phase['cpu'],actual['cpu'],'Whole literal heap-prefix checkpoint CPU '+name)";assert s.count(a)==1;s=s.replace(a,"equal(B.cpu(phase['state']),actual['cpu'],'Whole literal heap-prefix checkpoint CPU '+name)")
target=R/'tools/m4-formatting-source/compare_native_fixture_v8.py';assert not target.exists();target.write_text(s)
