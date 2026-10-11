"""Bind formatter owners to actual generic malloc kind in standalone Session."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('prepare_v9.py');source=p.read_text();anchor="exec(compile(source,str(p),'exec'),globals())";assert source.count(anchor)==1
source=source.replace(anchor,"source=source.replace(\".read_text()[12:-2]\",\".read_text()[12:-2].replace('a->kind!=2','a->kind!=1')\").replace('a->kind!=2','a->kind!=1')\n"+anchor)
exec(compile(source,str(p),'exec'),globals())
