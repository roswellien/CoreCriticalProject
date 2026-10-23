"""Exact current producer trailing scope fields retained after files map."""
from pathlib import Path
p=Path(__file__).with_name('map_terminal_strict24_v1.py');s=p.read_text()
a="  metadata=json.loads(head[:head.index(marker)]+b'  \"files\":{}}')\n  # Authenticate whole receipt bytes, parse only bounded leading fields.\n  with p.open('rb')as f:f.seek(-8,2);tail=f.read()\n  assert tail.rstrip().endswith(b'}\\n}')or tail.rstrip().endswith(b'}\\r\\n}'),'Known complete top-level terminal files map'\n  return metadata"
b="""  # Exact verifier-v5 appends real closure/observation flags after files.
  # Retain those actual fields; never invent them from prefix or passed.
  with p.open('rb')as f:f.seek(-4096,2);tail=f.read()
  ends=list(re.finditer(rb'\\r?\\n  }(?=,\\r?\\n  "all_bounded_readers_closed":)',tail));assert len(ends)==1,'Exact known producer files/scope boundary'
  suffix=tail[ends[0].end():];assert len(suffix)<2048
  metadata=json.loads(head[:head.index(marker)]+b'  "files":{}'+suffix)
  return metadata"""
assert s.count(a)==1;s=s.replace(a,b);assert s.count('import collections,hashlib,json,sys')==1;s=s.replace('import collections,hashlib,json,sys','import collections,hashlib,json,re,sys')
ns={'__file__':str(Path(__file__).resolve()),'__name__':'metadata_only'};exec(compile(s,str(p),'exec'),ns);ns['main']('strict24-named-facet-mapping-r3')
