"""Correct all three owner-kind predicates, including the active guard."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('prepare_v13.py');s=p.read_text();a="s.count('a->kind!=2')==2";assert s.count(a)==1;s=s.replace(a,"s.count('a->kind!=2')==3");s=s.replace('pins[str(Path(__file__).resolve())]=sha(__file__)','pins[str(Path(__file__).resolve())]=sha(__file__);pins[str(p.resolve())]=sha(p)')
exec(compile(s,str(p),'exec'),globals())
