"""ROOT policy review rebind for the independently proved terminal writer."""
from pathlib import Path
import hashlib
p=Path(__file__).with_name('root_seal_current_policy_v3.py')
with p.open('rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()=='d484982603ab920ab2d6824bda43b400182dd29a5c7a0185830bad69e97db43f'
s=p.read_text()
changes=[('root-policy-admission-r2','root-policy-admission-r5'),('comparer-preparation-r6','comparer-preparation-r8'),('e44982fcb1cdc7938c89ea0c65ce3aff66b9ceeb13d01931c0f87b8db638ecc6','cc301fb0aec83f46d12f37c700b88765b944a6407cc174701f620e885b9f4949'),('preflight_comparer_v7.py','preflight_comparer_v9.py'),('root-definition-preflight-r2','root-definition-preflight-r5'),('all48_hunks_exactly_invert','all50_hunks_exactly_invert')]
for a,b in changes:assert a in s;s=s.replace(a,b)
inverse=s
for a,b in reversed(changes):inverse=inverse.replace(b,a)
assert inverse==p.read_text()
anchor=" assert caller['complete_selected138_original_provider_input_footprint_reviewed'] is True"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n terminal=read(R/'reports/m4-startup138-paired/widget-terminal-writer-root-review-r2/report.json','0fadb2a271833f91851ca28b6b430748db99ad0d113b7c878c63fe800d7812cb');assert terminal['independent_review']and terminal['terminal_fields']==804 and terminal['source_zero_terminal_fields']==624 and terminal['source_font_terminal_fields']==180")
s=s.replace('pin(__file__);pin(sys.executable);out.mkdir()',"pin(__file__);pin(Path(__file__).with_name('root_seal_current_policy_v3.py'),'d484982603ab920ab2d6824bda43b400182dd29a5c7a0185830bad69e97db43f');pin(sys.executable);out.mkdir()")
exec(compile(s,str(p),'exec'))
