"""Split physical instruction bytes across sparse pages without resizing a page."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[2];T=R/'tools/m4-widget-original';P=R/'reports/m4-widget-original/preparation-r7/report.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=T/'prepare_v6.py';d=json.loads(P.read_text())
if sha(P)!='75c9a2430f4b2f07535c34d3828f2c0315c51e6083f41f58048614cf02a98974'or sha(p)!=d['files'][str(p.resolve())]:raise ValueError('Immutable source')
s=p.read_text()
a="  if page not in records:records[page]=(1,bytearray(b'\\xcc'*4096))\n  records[page][1][pc&4095:(pc&4095)+len(b)]=b"
b="""  consumed=0
  while consumed<len(b):
   address=pc+consumed;page=address&~4095;offset=address&4095;extent=min(len(b)-consumed,4096-offset)
   if page not in records:records[page]=(1,bytearray(b'\\xcc'*4096))
   need(len(records[page][1])==4096,'Exact physical sparse page before write')
   records[page][1][offset:offset+extent]=b[consumed:consumed+extent];consumed+=extent
   need(len(records[page][1])==4096,'Exact physical sparse page after write')"""
if s.count(a)!=1:raise ValueError('Exact sparse write')
s=s.replace(a,b,1)
a=" out.mkdir(parents=True);(out/'pages.bin').write_bytes(b'MW4J124P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',p,perm)+b for p,(perm,b)in records.items()))"
b=""" need(all(len(b)==4096 for _,b in records.values()),'Every sparse page exactly4096B')
 pack=b'MW4J124P'+struct.pack('<I',len(records))+b''.join(struct.pack('<2I',p,perm)+b for p,(perm,b)in records.items())
 need(len(pack)==12+len(records)*4104,'Exact sparse pack physical geometry')
 out.mkdir(parents=True);(out/'pages.bin').write_bytes(pack)"""
if s.count(a)!=1:raise ValueError('Exact pack serialization')
s=s.replace(a,b,1)
a=" pin(__file__);pin(R/'tools/m4-widget-original/derive_prepare_v6.py');"
b=" pin(__file__);pin(R/'tools/m4-widget-original/derive_prepare_v7.py');pin(R/'tools/m4-widget-original/prepare_v6.py');pin(R/'reports/m4-widget-original/preparation-r7/report.json','75c9a2430f4b2f07535c34d3828f2c0315c51e6083f41f58048614cf02a98974');pin(R/'tools/m4-widget-original/derive_prepare_v6.py');"
if s.count(a)!=1:raise ValueError('Exact lineage')
s=s.replace(a,b,1);q=T/'prepare_v7.py'
if q.exists():raise ValueError('Fresh source')
q.write_text(s);print(json.dumps(dict(passed=True,source=str(q),sha256=sha(q))))
