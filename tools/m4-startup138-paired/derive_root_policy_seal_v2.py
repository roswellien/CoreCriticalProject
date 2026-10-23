"""Freeze exact root seal corrections for current comparer6; do not invoke it."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 parent=Path(__file__).with_name('root_seal_current_policy.py');text=parent.read_text();new=text
 changes=[
 ('root-policy-admission-r1','root-policy-admission-r2'),
 ('complete_selected138_original_provider_caller_closure_reviewed','complete_selected138_original_provider_input_footprint_reviewed'),
 ('comparer-preparation-r5','comparer-preparation-r6'),
 ('53529d80eec7a4055aa2a21222a60a1cea6ebfc31008fb81ed46271453888685','e44982fcb1cdc7938c89ea0c65ce3aff66b9ceeb13d01931c0f87b8db638ecc6'),
 ('preflight_comparer_v6.py','preflight_comparer_v7.py'),
 ('root-definition-preflight-r1','root-definition-preflight-r2'),
 ('all46_hunks_exactly_invert','all48_hunks_exactly_invert'),
 ('crt_page_policy_v4.py','crt_page_policy_v5.py'),
 ("cells,d['typed_CRT_loader_cells'])","cells,d['typed_CRT_loader_cells'],d['typed_CRT_lock13_objects'])"),
 ("assert not set(range(0x8c,0x90))&set(d['unused_input_offsets'])","assert not (set(range(0x8c,0x90))|set(range(0x130,0x148)))&set(d['unused_input_offsets'])"),
 ]
 for old,replacement in changes:
  assert old in new;new=new.replace(old,replacement)
 for old,replacement in reversed(changes):
  assert replacement in new
  # Two paths occur repeatedly; whole replacement must invert exactly.
  new=new.replace(replacement,old)
 assert new==text
 new=text
 for old,replacement in changes:new=new.replace(old,replacement)
 q=parent.with_name('root_seal_current_policy_v2.py');assert not q.exists();q.write_text(new)
 out=R/'reports/m4-startup138-paired/root-seal-derivative-r2';assert not out.exists();out.mkdir()
 files={str(p.resolve()):sha(p) for p in(parent,q,Path(__file__))}
 receipt=dict(passed=True,scope='Exact root-review tool derivative only, uninvoked',exact_inverse=True,changes=changes,initializer_credit=0,files=files)
 p=out/'report.json';p.write_text(json.dumps(receipt,indent=2)+'\n');print(sha(p))
if __name__=='__main__':main()
