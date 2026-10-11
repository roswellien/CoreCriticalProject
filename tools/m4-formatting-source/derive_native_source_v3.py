"""Join native resource kind to the actual metadata, not the API model dictionary."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-formatting-source/compare_native_fixture_v2.py';s=p.read_text()
a="and owner['kind']==1,'Actual generic source malloc requested/capacity/kind')";assert s.count(a)==1
s=s.replace(a,"and generation>0,'Actual source malloc requested/capacity/generation');actual_owners=list(struct.iter_unpack('<16Q',reader.data(f'actual-after-root-{phase}/locale-allocations.bin')));matching=[r for r in actual_owners if r[1]==owner['guest']and r[5]==generation];need(len(matching)==1 and matching[0][2:4]==(owner['requested'],owner['extent'])and matching[0][6]==1 and matching[0][8]==owner['native'],'Genuine actual generic native owner kind and physical backing identity')")
target=R/'tools/m4-formatting-source/compare_native_fixture_v3.py';assert not target.exists();target.write_text(s)
