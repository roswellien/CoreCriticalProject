"""Materialize inherited nested source-only wrappers before exact overlays."""
from pathlib import Path
p=Path(__file__).with_name('evaluate_literal_sorter_v4.py');s=p.read_text()
before="assert s.count(a)==1;s=s.replace(a,b);exec(compile(s,str(p),'exec'))"
after="""ns={'__file__':str(p)}
exec(compile(s.rsplit(a,1)[0],str(p),'exec'),ns)
stage=ns['s'];exec(compile(stage.rsplit(a,1)[0],str(p),'exec'),ns)
ns['s']=ns['s'];ns['p']=p
exec(compile(b,str(p),'exec'),ns)"""
assert s.count(before)==1;s=s.replace(before,after);exec(compile(s,str(p),'exec'))
