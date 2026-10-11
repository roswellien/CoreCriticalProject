"""Permit only nine physically named held-register CALLs in literal lifting."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'tools/m4-tree-source/lift.py'
raw=source.read_text()
old="need(not g['unresolved_controls'],'Game source graph closed with literal FS0 only');need(all('fs:[0x0]' in row['operands'] for row in g['FS_sites']),'Only exact normal FS0 instructions')"
new="named={r['pc']:r for r in json.loads((REC/'instruction-contracts.json').read_bytes())['register_import_calls']};need(all(u['reason']=='unresolved indirect control' and u['pc'] in named and u['row']==named[u['pc']]['source_call'] for u in g['unresolved_controls']),'Only exact nine statically named register-held CALLs permitted for literal lifting; dynamic retention proof still pending');need(all('fs:[0x0]' in row['operands'] for row in g['FS_sites']),'Only exact normal FS0 instructions')"
assert raw.count(old)==1
target=ROOT/'tools/m4-tree-source/lift_v2.py';assert not target.exists();target.write_text(raw.replace(old,new))
out=ROOT/'reports/m4-tree-source/register-lift-preparation-r2';assert not out.exists();out.mkdir(parents=True)
files={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest()for p in(source,target,Path(__file__))}
report=dict(passed=True,scope='Source preparation only: nine exact statically named register CALLs; no retention/execution admission',old=old,new=new,files=files)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(passed=True,sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest())))
