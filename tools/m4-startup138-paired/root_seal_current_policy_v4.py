"""Retain ROOT current policy review, rebind solely original-report rename."""
from pathlib import Path
import hashlib
p=Path(__file__).with_name('root_seal_current_policy_v3.py')
with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
assert h=='804becc86bbeaad3c991dbdeb166e07f4c4bbf60ee2598fc4f1a910ef2529e97'
s=p.read_text()
changes=[('root-policy-admission-r2','root-policy-admission-r3'),('comparer-preparation-r6','comparer-preparation-r7'),('e44982fcb1cdc7938c89ea0c65ce3aff66b9ceeb13d01931c0f87b8db638ecc6','a005a4989556903f6f7e04308dca12f9a96fe3d8b4ed0e6c50c7a94c4fe76f6c'),('preflight_comparer_v7.py','preflight_comparer_v8.py'),('root-definition-preflight-r2','root-definition-preflight-r3'),('all48_hunks_exactly_invert','all49_hunks_exactly_invert')]
for a,b in changes:
 assert a in s;s=s.replace(a,b)
inverse=s
for a,b in reversed(changes):inverse=inverse.replace(b,a)
assert inverse==p.read_text()
s=s.replace('pin(__file__);pin(sys.executable);out.mkdir()',"pin(__file__);pin(Path(__file__).with_name('root_seal_current_policy_v3.py'),'804becc86bbeaad3c991dbdeb166e07f4c4bbf60ee2598fc4f1a910ef2529e97');pin(sys.executable);out.mkdir()")
exec(compile(s,str(p),'exec'))
