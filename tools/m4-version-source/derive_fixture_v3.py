"""Preserve failed candidate; bind only exact pre-store timing component3."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=P/'prepare_fixture_v2.py';s=p.read_text()
for a,b in [('component-preparation-r2','component-preparation-r3'),('1143e3cef914a5582e93231a810dfd32cc0eabd94534ccaa7025045b0964ed4d','e47cc5974bc3da9ea51ce56e90090568f0451d9fad065a9fef22428e6a926217'),('component-build-r2','component-build-r3'),('3bca59f305044aa480117626ecd3718acb64694b5578ec88a87671a794284b52','d68e132e29dfaf40fd230dc23ec347960a14a84427eb568831b7c1b354a5f640')]:
 assert a in s;s=s.replace(a,b)
a='  pin(__file__)';assert s.count(a)==1;s=s.replace(a,a+";pin(R/'tools/m4-version-source/prepare_fixture_v2.py','"+sha(p)+"');pin(R/'tools/m4-version-source/derive_fixture_v3.py')")
q=P/'prepare_fixture_v3.py';assert not q.exists();q.write_text(s)
print(json.dumps(dict(path=str(q),sha256=sha(q),native_executed=False)))
