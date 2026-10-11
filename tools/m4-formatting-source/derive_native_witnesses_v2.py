"""Admit actual post-return root clearing and real cleanup pointer retirement."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-formatting-source/compare_native_witnesses.py';s=p.read_text()
a="phase+1,F,guest,generation,len(own),4,1,r['root'])";assert s.count(a)==1;s=s.replace(a,'phase+1,F,guest,generation,len(own),4,1,0)')
a='before[:10]==after[:10]and before[12:]==after[12:]';assert s.count(a)==1;s=s.replace(a,'before[:8]==after[:8]and before[12:]==after[12:]and before[8]and before[9]==1 and after[8:10]==(0,0)')
target=R/'tools/m4-formatting-source/compare_native_witnesses_v2.py';assert not target.exists();target.write_text(s)
