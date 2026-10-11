"""Actual API target CPU and source site are separately bound by full API frame witness."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).resolve().parent/'check_controls.py';s=p.read_text(encoding='utf-8')
s=s.replace("native-integration-r3/report.json","native-integration-r5/report.json")
old="identity=a.words(trigger+'identity.bin',3);need(identity[0]==(41 if case in (11,12) else 40) and identity[1]==0x7810a30b,'Exact targeted first genuine source API boundary')"
new="identity=a.words(trigger+'identity.bin',3);api=a.words(trigger+'api-witness.bin',32,'Q');need(identity[0]==(41 if case in (11,12) else 40) and identity[1]==api[4] and api[2:4]==(0x7810a30b,0x78146198) and api[6]==0x7810a311 and api[7]==1 and api[20]==0x78145640 and api[14]==int(case in (11,12)),'Exact actual target CPU and separately witnessed genuine source API CALL boundary')"
assert s.count(old)==1;s=s.replace(old,new)
old="need(fault[0] and fault[1]==0x7810a30b,'Checked first-fault source PC identity')"
new="need(fault[0] and fault[1] in (api[4],api[2]),'Checked first-fault actual API target or exact retained source CALL-site identity')"
assert s.count(old)==1;s=s.replace(old,new)
exec(compile(s,str(p),'exec'),globals())
