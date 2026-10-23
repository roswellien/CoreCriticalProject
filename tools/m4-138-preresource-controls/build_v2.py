"""Include current whole-link prelaunch object pins, not only build outputs."""
from pathlib import Path
import hashlib
p=Path(__file__).with_name('build_v1.py');s=p.read_text()
a="build=json.loads(pin(pr['parent_build'],pr['parent_build_sha256']).read_bytes());assert build['passed']"
b=a+"\n  review=json.loads(pin(R/'reports/m4-tree-review/joint138-prelaunch-r10/report.json','cede59b7c9b77ab98b78da72374938775b3c78ec3e9a737f618bd688873e3325').read_bytes());assert review['passed'] and review['build_sha256']==pr['parent_build_sha256']\n  def admitted_hash(p):\n   h=review['files'].get(str(p),build['files'].get(str(p)));assert h is not None,('No current physical input pin',p);return h"
assert s.count(a)==1;s=s.replace(a,b)
assert s.count("build['files'][str(p)]")==2;s=s.replace("build['files'][str(p)]","admitted_hash(p)")
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
