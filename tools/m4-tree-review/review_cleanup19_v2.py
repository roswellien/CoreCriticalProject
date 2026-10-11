"""Exact CRLF-preserving native19 transition; retained first diagnostic was LF-only."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_cleanup19.py');s=p.read_text()
a="   assert s.count(before)==1 and s.replace(before,after).encode()==y"
b="   before=before.replace('\\n','\\r\\n');after=after.replace('\\n','\\r\\n');assert s.count(before)==1 and s.replace(before,after).encode()==y"
assert s.count(a)==1;s=s.replace(a,b).replace(' pin(__file__)',' pin(__file__);pin(p)')
exec(compile(s,str(p),'exec'),globals())
