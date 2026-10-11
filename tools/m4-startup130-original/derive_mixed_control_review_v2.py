"""Pin the bounded exported causes independently; producer has no output pin."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2]
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
old=R/'tools/m4-startup130-original/review_mixed_controls.py';new=old.with_name('review_mixed_controls_v2.py');assert not new.exists();s=old.read_text();a="causes=read(cp,v['files'][str(cp.resolve())])";b="causes=read(cp);need(\"(out/'actual-causes.json').write_text(json.dumps(causes\"in textbase,'Executed producer writes its actual validated causal row list; bounded output independently pinned by this gate')";assert s.count(a)==1;s=s.replace(a,b);assert s.count('mixed-controls-review-r1')==1;s=s.replace('mixed-controls-review-r1','mixed-controls-review-r2');a='pin(__file__);passed=True';b="pin(__file__);pin(R/'tools/m4-startup130-original/review_mixed_controls.py');pin(R/'tools/m4-startup130-original/derive_mixed_control_review_v2.py');passed=True";assert s.count(a)==1;s=s.replace(a,b);new.write_text(s)
print(sha(new))
