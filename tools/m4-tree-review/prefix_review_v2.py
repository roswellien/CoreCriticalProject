"""Bindings contain physical PC/kind/raw; use the literal fs_hook_PC symbol."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
p = Path(__file__).resolve().parent/'prefix_review.py'
s = p.read_text(encoding='utf-8')
old = "name_ = h['declared_observer']; name_ = name_ if name_.startswith('_') else '_'+name_"
new = "name_ = h.get('declared_observer', 'fs_hook_'+format(h['PC'],'x')); name_ = name_ if name_.startswith('_') else '_'+name_"
assert s.count(old)==1
s = s.replace(old,new)
# Retain both authored checker bytes and the additive correction in the receipt.
s = s.replace("pin(__file__); passed=True", "pin(__file__); pin(p); passed=True")
exec(compile(s,str(p),'exec'),globals())
