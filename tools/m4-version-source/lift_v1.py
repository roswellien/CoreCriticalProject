"""Eight finite version bodies with the unchanged reviewed Remill host lowerer."""
from pathlib import Path
import hashlib,sys
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-remaining-service-source/lift.py'
assert hashlib.sha256(p.read_bytes()).hexdigest()=='998290ca327e5dce18a22da3d45a723f2f0f55f35f4cce137820ffa3aeea6b44'
s=p.read_text()
changes={"REC=ROOT/'reports/m4-remaining-service-source/preparation-r1'":"REC=ROOT/'reports/m4-version-source/preparation-r2'","REC_SHA='2cf6b50240076b4fd2ecced04ce1389b3b94c8b03ea331799c48ec90b4b34933'":"REC_SHA='137c214307a28b0e120b600ee53f14fcfacac0a72a7ef64b437178f3b3b17c75'","out=ROOT/'reports/m4-remaining-service-source'/name":"out=ROOT/'reports/m4-version-source'/name",'root_count=5':'root_count=1',"pin(ROOT/'tools/m4-widget-source/lift.py');":"pin(ROOT/'tools/m4-remaining-service-source/lift.py','998290ca327e5dce18a22da3d45a723f2f0f55f35f4cce137820ffa3aeea6b44');pin(ROOT/'tools/m4-widget-source/lift.py');"}
for a,b in changes.items():assert s.count(a)==1,a;s=s.replace(a,b)
exec(compile(s,str(p),'exec'),globals())
