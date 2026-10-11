"""Correct one generated-helper pin and bind fresh independent FPS tail proof."""
from pathlib import Path
import ast,hashlib
R=Path(__file__).resolve().parents[2]
parent=R/'tools/m4-fps-native/derive_registry_source.py';target=R/'tools/m4-fps-native/derive_registry_source_current.py';assert not target.exists();t=parent.read_text()
for a,b,n in [
 ("target=R/'tools/m4-fps-native/compare_registry.py'","target=R/'tools/m4-fps-native/compare_registry_v2.py'",1),
 ("R/'reports/m4-fps-native/compare_prefix_v2.py'","R/'tools/m4-fps-native/compare_prefix_v2.py'",1),
]:
 assert t.count(a)==n;(t:=t.replace(a,b))
marker=" marker=\"  contract=read(R/'reports/m4-fps-native/component-preparation-r1/contracts.json');\""
assert t.count(marker)==1
t=t.replace(marker,""" change("need(tail['passed'],'Exact independently reviewed prior six widget tails');need(len(contract['registration_epilogues'])==7,'Exact additive FPS tail contract')", "need(tail['passed'],'Exact independently reviewed prior six widget tails');fps_tail=read(R/'reports/m4-fps-original-review/registration-tail-r1/report.json','5f1c0b74b03f001a7ece24a9b81b1f826ee106a0299f9cd6a91cb51bf88a3807');need(fps_tail['passed']and len(contract['registration_epilogues'])==7,'Exact independently reviewed additive FPS tail contract')")
 marker="  contract=read(R/'reports/m4-fps-native/component-preparation-r1/contracts.json');""" )
ast.parse(t);target.write_text(t);print(target,hashlib.sha256(target.read_bytes()).hexdigest())
