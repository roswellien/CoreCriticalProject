"""ROOT direct immutable rebind of previously reviewed finite policy seal."""
from pathlib import Path
import hashlib
p=Path(__file__).with_name('root_seal_current_policy_v3.py')
with p.open('rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()=='d484982603ab920ab2d6824bda43b400182dd29a5c7a0185830bad69e97db43f'
s=p.read_text()
changes=[('root-policy-admission-r2','root-policy-admission-r7'),('comparer-preparation-r6','comparer-preparation-r13'),('e44982fcb1cdc7938c89ea0c65ce3aff66b9ceeb13d01931c0f87b8db638ecc6','84f047b2d83c54ef678e60ba645cd9cf46d3f95737baaa3c70f4d7a7948e3d9c'),('preflight_comparer_v7.py','preflight_comparer_v13.py'),('root-definition-preflight-r2','root-definition-preflight-r7'),('all48_hunks_exactly_invert','all53_hunks_exactly_invert')]
for a,b in changes:assert a in s;s=s.replace(a,b)
anchor=" assert caller['complete_selected138_original_provider_input_footprint_reviewed'] is True"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n terminal=read(R/'reports/m4-startup138-paired/widget-terminal-writer-root-review-r2/report.json','0fadb2a271833f91851ca28b6b430748db99ad0d113b7c878c63fe800d7812cb');assert terminal['independent_review']and terminal['terminal_fields']==804\n tree=read(R/'reports/m4-startup138-paired/tree-phase-root-review-r1/report.json','51e4aef13a576afdf694f37d19657059fb6ea14b29363580418ba5981a6ebddb');assert tree['independent_review']and tree['tree_phase']==83\n formatter=read(R/'reports/m4-startup138-paired/format-module-root-review-r1/report.json','39a98c818eed260d830f1cc646553b66407c9477b0554e5d41d4a2ad959f8f00');assert formatter['independent_review']and formatter['separate_CRT_publications']==72 and formatter['refused_adverses']==504")
a='pin(__file__);pin(sys.executable);out.mkdir()'
b="pin(__file__);pin(Path(__file__).with_name('root_seal_current_policy_v3.py'),'d484982603ab920ab2d6824bda43b400182dd29a5c7a0185830bad69e97db43f');pin(sys.executable);out.mkdir()"
assert s.count(a)==1;s=s.replace(a,b)
exec(compile(s,str(p),'exec'))
