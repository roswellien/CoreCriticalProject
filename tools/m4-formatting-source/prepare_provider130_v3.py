"""Preserve two failed preparers; split compound statements before phase export."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('prepare_provider130_v2.py');s=p.read_text();a="exec(compile(s,str(p),'exec'),globals())";assert s.count(a)==1
b="""s=s.replace('       obs=F.S.CURRENT;', '       obs=F.S.CURRENT;')
s=s.replace('if entry in F.FORMAT_ROOTS:\\n', '\\n      if entry in F.FORMAT_ROOTS:\\n')
exec(compile(s,str(p),'exec'),globals())"""
s=s.replace(a,b)
exec(compile(s,str(p),'exec'),globals())
