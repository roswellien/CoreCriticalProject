"""Reattribute exact CALL timing fix and unchanged real VERSION service4."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];p=R/'tools/m4-tree-review/review_version_prelaunch_v3.py';scope={'__file__':str(p),'__name__':'materialize_only'}
exec(compile(p.read_text(),str(p),'exec'),scope);t=scope['s']
for a,b in [
 ('dfca62ad2dbae9045fc034a5fa3770606451b524fcfe31ce46f73792dcb5f62c','ba1a85aea023afd7ef61608aa84656c10f431b44e0b097bf5e09778278aa18ee'),
 ('55a9c4b17f1413263607bf55fd30d722a63b6dcd4b56ce4caf3ccdb8472a0b45','d4959b4e37c2a8f38919545bcb3689d568f111bfe0495d639f5b029f3b20ee42'),
 ('component-preparation-r2','component-preparation-r3'),('component-build-r2','component-build-r3'),('fixture-preparation-r2','fixture-preparation-r3'),('fixture-build-r1','fixture-build-r2'),
 ('1143e3cef914a5582e93231a810dfd32cc0eabd94534ccaa7025045b0964ed4d','e47cc5974bc3da9ea51ce56e90090568f0451d9fad065a9fef22428e6a926217'),
 ('3bca59f305044aa480117626ecd3718acb64694b5578ec88a87671a794284b52','d68e132e29dfaf40fd230dc23ec347960a14a84427eb568831b7c1b354a5f640'),
 ('run_fixture_v1.py','run_fixture_v2.py')]:assert a in t,a;t=t.replace(a,b)
anchor="  S=load(R/'tools/analysis/pe.py'"
at=t.index(anchor)
t=t[:at]+"  read(R/'reports/m4-tree-review/version-call-timing-r2/report.json','489c3d0b219a99f5a81b15cd01d62ae91435ac0393eafb51b0346ec9391742a1')\n  read(R/'reports/m4-version-source/controller-preparation-r2/report.json','f69c927773a3fa63d97e76ab131ef90f163c1122dd86fdae5c1c0ff5fd369ece')\n"+t[at:]
t=t.replace("  pin(R/'tools/m4-tree-review/review_version_prelaunch.py');", "  pin(R/'tools/m4-tree-review/review_version_prelaunch_v3.py');pin(R/'tools/m4-tree-review/review_version_prelaunch.py');")
exec(compile(t,str(Path(__file__)),'exec'),globals())
