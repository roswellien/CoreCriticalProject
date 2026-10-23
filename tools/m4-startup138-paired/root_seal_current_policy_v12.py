"""ROOT direct immutable rebind of previously reviewed finite policy seal."""
from pathlib import Path
import hashlib,sys
prepared_sha=sys.argv.pop(1)
assert len(prepared_sha)==64
p=Path(__file__).with_name('root_seal_current_policy_v3.py')
with p.open('rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()=='d484982603ab920ab2d6824bda43b400182dd29a5c7a0185830bad69e97db43f'
s=p.read_text()
changes=[('root-policy-admission-r2','root-policy-admission-r8'),('comparer-preparation-r6','comparer-preparation-r15'),('e44982fcb1cdc7938c89ea0c65ce3aff66b9ceeb13d01931c0f87b8db638ecc6',prepared_sha),('preflight_comparer_v7.py','preflight_comparer_v15.py'),('root-definition-preflight-r2','root-definition-preflight-r8'),('all48_hunks_exactly_invert','all53_hunks_exactly_invert')]
for a,b in changes:assert a in s;s=s.replace(a,b)
anchor=" assert caller['complete_selected138_original_provider_input_footprint_reviewed'] is True"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n terminal=read(R/'reports/m4-startup138-paired/widget-terminal-writer-root-review-r2/report.json','0fadb2a271833f91851ca28b6b430748db99ad0d113b7c878c63fe800d7812cb');assert terminal['independent_review']and terminal['terminal_fields']==804\n tree=read(R/'reports/m4-startup138-paired/tree-phase-root-review-r1/report.json','51e4aef13a576afdf694f37d19657059fb6ea14b29363580418ba5981a6ebddb');assert tree['independent_review']and tree['tree_phase']==83\n formatter=read(R/'reports/m4-startup138-paired/format-module-root-review-r3/report.json','97fceac99e6d05cd2263fefa482d5205a93b711f2471352903dbcf611ec933f7');assert formatter['independent_review']and formatter['separate_CRT_publications']==72 and formatter['refused_adverses']==504")
a='pin(__file__);pin(sys.executable);out.mkdir()'
b="pin(__file__);pin(Path(__file__).with_name('root_seal_current_policy_v3.py'),'d484982603ab920ab2d6824bda43b400182dd29a5c7a0185830bad69e97db43f');pin(sys.executable);out.mkdir()"
assert s.count(a)==1;s=s.replace(a,b)
exec(compile(s,str(p),'exec'))
