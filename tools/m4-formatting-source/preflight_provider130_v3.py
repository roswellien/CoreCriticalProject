"""Preflight the added bounded source-provider export; never read captures."""
from pathlib import Path
p=Path(__file__).with_name('preflight_provider130_v2.py');s=p.read_text()
a="exec(compile(s,str(p),'exec'),globals())";assert s.count(a)==1
s=s.replace(a,"a='compare_provider130_v4.py';assert s.count(a)==1;s=s.replace(a,'compare_provider130_v5.py')\nexec(compile(s,str(p),'exec'),globals())")
exec(compile(s,str(p),'exec'),globals())
