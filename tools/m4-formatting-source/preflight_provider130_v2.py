"""Keep the failed preparatory order-schema check; admit exact entry/slot rows."""
from pathlib import Path
p=Path(__file__).with_name('preflight_provider130.py');s=p.read_text()
a="set(j['selected_order'])";assert s.count(a)==1;s=s.replace(a,"{r['entry'] for r in j['selected_order']}")
a='paths=set(READS)|';assert s.count(a)==1;s=s.replace(a,"paths=set(READS)|{str(ROOT/'tools/m4-formatting-source/preflight_provider130.py')}|")
exec(compile(s,str(p),'exec'),globals())
