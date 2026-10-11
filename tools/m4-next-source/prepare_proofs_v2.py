"""Preserve initial syntax-only readers; fix bounded label substitution.

The initial unexecuted template changed the terminal decimal digits of the
new original memory offset while replacing a milestone label. This derivative
keeps all numeric ABI offsets intact and emits fresh versioned reader files.
"""
from pathlib import Path
T=Path(__file__).resolve().parent
source=T/'prepare_proofs.py'
target=T/'prepare_proofs_corrected.py'
assert not target.exists()
s=source.read_text()
s=s.replace("p=T/name;assert not p.exists();compile(s,str(p),'exec');p.write_text(s)","p=T/(Path(name).stem+'_v2.py');assert not p.exists();compile(s,str(p),'exec');p.write_text(s)")
s=s.replace("return s.replace('116','120').replace", "return re.sub(r'(?<![0-9a-f])116(?![0-9a-f])','120',s).replace")
s=s.replace('proof-preparation-r1','proof-preparation-r2')
target.write_text(s)
