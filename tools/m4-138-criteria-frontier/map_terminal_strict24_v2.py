"""Exact pretty-JSON trailing indent correction; metadata scope unchanged."""
from pathlib import Path
import hashlib,json
p=Path(__file__).with_name('map_terminal_strict24_v1.py');s=p.read_text()
changes=[('import collections,hashlib,json,sys','import collections,hashlib,json,re,sys'),("with p.open('rb')as f:f.seek(-8,2);tail=f.read()","with p.open('rb')as f:f.seek(-64,2);tail=f.read()"),("  assert tail.rstrip().endswith(b'}\\n}')or tail.rstrip().endswith(b'}\\r\\n}'),'Known complete top-level terminal files map'","  assert re.search(rb'\\r?\\n  }\\r?\\n}\\r?\\n?$',tail),'Known complete top-level terminal files map'")]
for a,b in changes:assert s.count(a)==1;s=s.replace(a,b)
ns={'__file__':str(Path(__file__).resolve()),'__name__':'metadata_only'};exec(compile(s,str(p),'exec'),ns);ns['main']('strict24-named-facet-mapping-r2')
