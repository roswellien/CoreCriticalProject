"""Preserve first component; refreeze its exact bodies against service4."""
from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parent;R=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=P/'prepare_component_v1.py';s=p.read_text();old_sha=sha(p)
changes=[('service-preparation-r3','service-preparation-r4'),('e2b5f0b0cd96dfc1a395c9f0d4e41da4783540d174df857d1cd284d4b9f74318','f35a730b53c0299e42d0955a89d29ce2e3289569f5a47fbad538344f55a0dbc5'),('service-build-r3','service-build-r4'),('c8e0c511a8fbf83e99151266fb9ca49b1c096acbd2b239dac9734a706127cb63','9c9426e2e70b24c6b71ae102581c625a155ccc61acecc0c914dcc065904ea133')]
for a,b in changes:assert a in s;s=s.replace(a,b)
a='  pin(__file__)';assert s.count(a)==1;s=s.replace(a,a+";pin(R/'tools/m4-version-source/prepare_component_v1.py','%s');pin(R/'tools/m4-version-source/derive_component_v2.py')"%old_sha)
q=P/'prepare_component_v2.py';assert not q.exists();q.write_text(s);print(json.dumps(dict(path=str(q),sha256=sha(q),native_executed=False)))
