"""Pin checker path explicitly; preparation p is local to the checker main."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
v2 = Path(__file__).resolve().parent/'prefix_review_v2.py'
s = v2.read_text(encoding='utf-8')
old = '"pin(__file__); pin(p); passed=True"'
new = '"pin(__file__); pin(R/\'tools/m4-tree-review/prefix_review.py\'); pin(R/\'tools/m4-tree-review/prefix_review_v2.py\'); passed=True"'
assert s.count(old) == 1
exec(compile(s.replace(old,new),str(v2),'exec'),globals())
