"""Fresh native19/preparation2/build2 bounded integration review."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_joint130_prelaunch_v2.py');s=p.read_text()
for a,b in [("pd=area/'preparation-r1';bd=area/'build-r1'","pd=area/'preparation-r2';bd=area/'build-r2'"),('21acafa2fc5632035531efa72be355a324a37d34f3728a9d6fe2630be978c73f','060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c'),('4ccb1347bd85872f06ff6a57d1bd539effcd6d24de1c302b7cb2e4758b3ea976','1a51ee4bbba62c9505eb1ffae7dee2538cc68297708119a1fa3485769a1cde53'),('native18','native19')]:
 assert a in s,a;s=s.replace(a,b)
s=s.replace('  C.pin(__file__);','  C.pin(__file__);C.pin(p);')
anchor="  C.need(all(x['passed']for x in(p,b,prior,accepted,native,cos))"
assert s.count(anchor)==1
s=s.replace(anchor,"  cleanup=C.read(R/'reports/m4-tree-review/cleanup19-r2/report.json','ba43095f791a7e16d2e747e2c1f3d414e15d29744588b91509fb1ee7122b4afb');C.need(cleanup['passed']and cleanup['native19_sha256']==p['native_preparation_sha256'],'Current cleanup transition bound before executable integration')\n"+anchor)
exec(compile(s,str(p),'exec'),globals())
