"""Exact no-escape source overlay materialization fix; prior artifacts retained."""
from pathlib import Path
p=Path(__file__).with_name('evaluate_literal_sorter_v6.py');s=p.read_text();a="overlay=(T/'evaluate_literal_sorter_v4.py').read_text();before=\"derived.write_text(body+'\\\\n')\";assert overlay.count(before)==1;overlay=overlay.replace(before,\"derived.write_text(body+chr(10))\")"
b="import re\noverlay=(T/'evaluate_literal_sorter_v4.py').read_text();overlay,n=re.subn(r\"derived[.]write_text[(]body[+]'[^']+'[)]\",'derived.write_text(body+chr(10))',overlay);assert n==1"
assert s.count(a)==1;s=s.replace(a,b);exec(compile(s,str(p),'exec'))
