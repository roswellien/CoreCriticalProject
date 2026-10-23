"""Bind the terminal ROOT proof into the fresh immutable policy declaration."""
from pathlib import Path
p=Path(__file__).with_name('root_seal_current_policy_v7.py');s=p.read_text()
changes=[('comparer-preparation-r8','comparer-preparation-r9'),('cc301fb0aec83f46d12f37c700b88765b944a6407cc174701f620e885b9f4949','2ef8e701d9f2307991d07fa1024b5a741d083534798a7174b02ad81d96a88b50'),('preflight_comparer_v9.py','preflight_comparer_v10.py')]
for a,b in changes:assert s.count(a)==1;s=s.replace(a,b)
a="pin(__file__);pin(Path(__file__).with_name('root_seal_current_policy_v3.py')"
b="pin(__file__);pin(Path(__file__).with_name('root_seal_current_policy_v7.py'));pin(Path(__file__).with_name('root_seal_current_policy_v3.py')"
assert s.count(a)==1;s=s.replace(a,b)
exec(compile(s,str(p),'exec'))
