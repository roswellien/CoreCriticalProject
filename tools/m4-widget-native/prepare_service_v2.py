"""Use exact frozen callback identities instead of preparatory handwritten IDs."""
from pathlib import Path
import hashlib,json
p=Path(__file__).resolve().parent;R=p.parents[1];base=p/'prepare_service.py';s=base.read_text()
raw=(p/'borrowed_onexit.inc').read_text();c=json.loads((R/'reports/m4-widget-native/preparation-r2/contracts.json').read_text());import re
for row in c['roots']:
 root=row['root'];callback=row['registration']['callback'];pattern=r'(case 0x%x:callback=)0x[0-9a-f]+'%root;raw,count=re.subn(pattern,lambda m:m[1]+'0x%x'%callback,raw);assert count==1
current=p/'borrowed_onexit_v2.inc';assert not current.exists()or current.read_text()==raw;current.write_text(raw)
s=s.replace("R/'tools/m4-widget-native/borrowed_onexit.inc'","R/'tools/m4-widget-native/borrowed_onexit_v2.inc'")
s=s.replace("for p in [Path(__file__).resolve(),add,contracts", "for p in [base,Path(__file__).resolve(),R/'tools/m4-widget-native/borrowed_onexit.inc',add,contracts")
exec(compile(s,str(base),'exec'),globals())
