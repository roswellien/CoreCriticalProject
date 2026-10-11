"""Bind current outcome/domain reviews to the same finite Component source."""
from pathlib import Path
h=Path(__file__).resolve().parent;p=h/'prepare.py';s=p.read_text()
for a,b in [("for row in bodies['reused']:","for row in bodies['reusable']:"),("return address==0x5bcc80||address==0x5cab78||address==0x5ca6f0;","return address==0x5bcc80;"),("game.data[game.rva_to_offset(address-game.image_base):game.rva_to_offset(address-game.image_base)+n]","game.data[game.rva_range(address-game.image_base,n)[0]:game.rva_range(address-game.image_base,n)[0]+n]"),("for p in(__file__,R/'tools/m4-constructor-native/build.py'","for p in(__file__,R/'tools/m4-constructor-native/prepare.py',R/'tools/m4-constructor-native/prepare_v2.py',R/'tools/m4-constructor-native/prepare_v3.py',R/'tools/m4-constructor-native/build.py'")]:
 if s.count(a)!=1:raise ValueError('Exact inherited Component preparer hunk')
 s=s.replace(a,b,1)
a=" service=pin(service,service_sha);sv=json.loads(service.read_bytes());"
b=" outcomes=read(R/'reports/m4-tree-review/constructor37-outcomes-r1/report.json','bb570f3a1210990840eb50f8cd5ea2cfbf3f027c14b9ee9d6837a5d9b88604f5');domains=read(R/'reports/m4-constructor-native/source-domains-r1/report.json','370901f6c5379614c0325477e5be272d66768f5393e6c9c861bc3c88d2c99216');need(outcomes['passed']and domains['passed'],'Independent current original outcome/domain gates')\n"+a
if s.count(a)!=1:raise ValueError('One exact current domain-review binding')
s=s.replace(a,b,1).replace('flag_consumer_audit_pending=True,','flag_consumer_audit_pending=True,source_store_operand_value_guard_pending=True,',1)
exec(compile(s,str(p),'exec'),globals())
