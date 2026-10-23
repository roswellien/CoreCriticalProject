"""Exact physical five-line registration header geometry for preparation5."""
from pathlib import Path
import hashlib
p=Path(__file__).with_name('prepare_schema_checker_v5.py');s=p.read_text()
for a,b in [("schema-checker-preparation-r5","schema-checker-preparation-r6"),("check_schema138_v4.py","check_schema138_v5.py"),("count(b'\\\\n')==3+1","count(b'\\\\n')==5")]:assert s.count(a)==1;s=s.replace(a,b)
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
