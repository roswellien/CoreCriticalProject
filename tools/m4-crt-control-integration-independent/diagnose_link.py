"""Preserve the exact linked-vs-standalone reviewer failure before repair."""
from pathlib import Path
import hashlib, importlib.util, json, difflib, re, sys
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parents[2]
out=root/'reports/m4-crt-control-integration/independent-static-diagnostic-r1'
assert not out.exists()
out.mkdir()
(out/'diagnostic-source.py').write_bytes(Path(__file__).read_bytes())
p=root/'tools/m4-crt-control-independent/review.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='49eea1a0c6615d685acad629c4ef10bab32c6f14aa960a0c1e1d01c6750f6e61'
s=importlib.util.spec_from_file_location('frozen_root_review',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
paths=[root/'reports/m4-crt-control-integration/research-r1/game-host.ll',root/'reports/m4-crt-control-integration/research-r1/host.ll',root/'tools/m4-crt-control-integration-independent/static_review.py',root/'reports/m4-crt-control-integration/independent-static-review-r1/review-source.py',root/'reports/m4-crt-control-integration/independent-static-review-r1/failure.txt',p]
a,b=[q.read_text() for q in paths[:2]];ab,bb=m.strip_body(a),m.strip_body(b)
diffs={}
for name in ('sub_5ac5a0','sub_5ac5d6'):
    x,y=m.canonical(ab[name]),m.canonical(bb[name])
    diffs[name]='\n'.join(difflib.unified_diff(x.splitlines(),y.splitlines(),fromfile='standalone',tofile='linked',lineterm=''))+'\n'
    (out/(name+'.diff')).write_text(diffs[name])
    print(name,diffs[name])
types=lambda t:dict(re.findall(r'^(%[\w.]+) = type (.+)$',t,re.M))
report={'source_bindings':{str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in paths},'types_equal':types(a)==types(b),'standalone_definitions':list(ab),'linked_definitions':list(bb),'exact_differences':diffs,'production_finding':False,'diagnosis':'Initial strict comparison rejects LLVM linker alias spelling; proof must be checked before acceptance.'}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
