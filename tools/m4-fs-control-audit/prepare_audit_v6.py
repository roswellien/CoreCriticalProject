"""Use the physically authenticated MOV ECX [EAX+4] for the second-link prefix."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-fs-control-audit/audit_v5.py';s=p.read_text();assert s.count("expected_state,2296,q[16]")==1
s=s.replace('expected_state,2296,q[16]','expected_state,2248,q[16]').replace('Literal MOV EDI then next refused store','Literal MOV ECX [EAX+4] then next refused store')
t=p.with_name('audit_v6.py');assert not t.exists();t.write_text(s)
