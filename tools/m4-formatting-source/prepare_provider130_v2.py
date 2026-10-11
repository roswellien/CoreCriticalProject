"""Preserve failed preparer1, narrowing its ambiguous output-path replacement."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('prepare_provider130.py');s=p.read_text();a='one("ROOT/\'reports/m4-tree-source\'/name","ROOT/\'reports/m4-formatting-source\'/name")';b='one("out=ROOT/\'reports/m4-tree-source\'/name;","out=ROOT/\'reports/m4-formatting-source\'/name;")';assert s.count(a)==1;s=s.replace(a,b)
exec(compile(s,str(p),'exec'),globals())
