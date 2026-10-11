"""Preserve attempt1; stream and deduplicate physical checks within one preparation."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
s=(HERE/'prepare.py').read_text()
a="def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()"
assert s.count(a)==0 # The inherited preparer already uses streaming SHA.
a="p=Path(p).resolve();v=sha(p);assert h is None or v==h,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return v"
b="p=Path(p).resolve()\n  if str(p)in pins:\n   v=pins[str(p)];assert h is None or v==h,(p,h,v);return v\n  v=sha(p);assert h is None or v==h,(p,h,v);pins[str(p)]=v;return v"
assert s.count(a)==1;s=s.replace(a,b)
p=HERE/'prepare_v2.py';assert not p.exists();compile(s,str(p),'exec');p.write_text(s)
print('Generated additive124preparer with within-operation physical reuse')
