"""Show exact generated link names; no mutations."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[2]
b=json.loads((R/'reports/m4-fs-controls/build-r5/build.json').read_bytes())
t=Path(b['workers']['O0']['path']).parent
l=next(x for x in (t/'build.ninja').read_text().splitlines()if x.startswith('build mw34_joint_startup109.exe:'))
print(l[:1800])
print([p for p in b['workers']['O0']['objects']if p.endswith('.obj')and Path(p).as_posix().replace(':','$:')not in l][:8])
