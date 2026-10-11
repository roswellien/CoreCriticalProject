"""Preflight the overlap-complete source-provider inventory; no captures."""
from pathlib import Path
p=Path(__file__).with_name('preflight_provider130.py');s=p.read_text()
for a,b in(("set(j['selected_order'])","{r['entry'] for r in j['selected_order']}"),('compare_provider130_v4.py','compare_provider130_v6.py')):
 assert s.count(a)==1;s=s.replace(a,b)
a='paths=set(READS)|';assert s.count(a)==1;s=s.replace(a,"paths=set(READS)|{str(ROOT/'tools/m4-formatting-source/preflight_provider130.py')}|")
exec(compile(s,str(p),'exec'),globals())
