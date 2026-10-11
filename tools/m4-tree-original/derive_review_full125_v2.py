"""Correct inherited hook binding path; preserve failed first review."""
from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[2]
p=Path(__file__).with_name('review_full125.py')
s=p.read_text()
old="hooks=read(prepdir/'lockit-hook-bindings.json')"
new="hooks=read(R/'reports/m4-lockit-original/original-preparation-r4/lockit-hook-bindings.json')"
assert s.count(old)==1
s=s.replace(old,new)
s=s.replace("pin(__file__);passed=True", "pin(__file__);pin(R/'tools/m4-tree-original/review_full125.py');pin(R/'tools/m4-tree-original/derive_review_full125_v2.py');passed=True")
out=p.with_name('review_full125_v2.py')
assert not out.exists()
out.write_text(s)
print(hashlib.sha256(out.read_bytes()).hexdigest())
