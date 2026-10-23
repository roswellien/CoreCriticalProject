"""ROOT current comparer and exact tree chronology policy binding."""
from pathlib import Path
p=Path(__file__).with_name('root_seal_current_policy_v7.py');s=p.read_text()
changes=[('root-policy-admission-r5','root-policy-admission-r6'),('comparer-preparation-r8','comparer-preparation-r11'),('cc301fb0aec83f46d12f37c700b88765b944a6407cc174701f620e885b9f4949','69888fc3aecb975215744406b7147da737f1593a6be19678dba606257351f6eb'),('preflight_comparer_v9.py','preflight_comparer_v11.py'),('root-definition-preflight-r5','root-definition-preflight-r6'),('all50_hunks_exactly_invert','all51_hunks_exactly_invert')]
for a,b in changes:assert s.count(a)==1;s=s.replace(a,b)
a="terminal=read(R/'reports/m4-startup138-paired/widget-terminal-writer-root-review-r2/report.json'"
b="tree=read(R/'reports/m4-startup138-paired/tree-phase-root-review-r1/report.json','51e4aef13a576afdf694f37d19657059fb6ea14b29363580418ba5981a6ebddb');assert tree['independent_review']and tree['tree_phase']==83;terminal=read(R/'reports/m4-startup138-paired/widget-terminal-writer-root-review-r2/report.json'"
assert s.count(a)==1;s=s.replace(a,b)
a="pin(__file__);pin(Path(__file__).with_name('root_seal_current_policy_v3.py')"
b="pin(__file__);pin(Path(__file__).with_name('root_seal_current_policy_v7.py'));pin(Path(__file__).with_name('root_seal_current_policy_v3.py')"
assert s.count(a)==1;s=s.replace(a,b)
exec(compile(s,str(p),'exec'))
