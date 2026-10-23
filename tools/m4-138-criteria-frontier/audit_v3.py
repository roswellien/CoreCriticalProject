"""Exact wrapper local-variable pin correction; proof predicates unchanged."""
from pathlib import Path
import hashlib
p=Path(__file__).with_name('audit_v2.py')
s=p.read_text()
a="pin(p,'bc2151ce1aafca7077ce58a0326d3300309738e7e81d3c98d182510430232c8f');pin(__file__);pin(sys.executable)"
b="pin(Path(__file__).with_name('audit_v1.py'),'bc2151ce1aafca7077ce58a0326d3300309738e7e81d3c98d182510430232c8f');pin(Path(__file__).with_name('audit_v2.py'));pin(__file__);pin(sys.executable)"
assert s.count(a)==1
s=s.replace(a,b)
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
