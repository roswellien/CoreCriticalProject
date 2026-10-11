"""Additive native19 derivative of frozen control preparation3."""
from pathlib import Path
import json,hashlib,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
p=Path(__file__).with_name('prepare_mixed_controls_v3.py');s=p.read_text()
before=" native=read(p['native_preparation'],p['native_preparation_sha256']);assert native['passed']"
after=""" parent_native=read(p['native_preparation'],p['native_preparation_sha256']);assert parent_native['passed']
 review=read(R/'reports/m4-tree-review/cleanup19-r2/report.json','ba43095f791a7e16d2e747e2c1f3d414e15d29744588b91509fb1ee7122b4afb');assert review['passed'] and review['native19_sha256']=='1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3'
 target_native=R/'reports/m4-formatting-native/preparation-r19/report.json';native=read(target_native,review['native19_sha256']);assert native['passed']
 old_include=p['native_include'];old_library=p['native_library'];p['native_include']=native['native_include'];p['native_library']=native['native_library'];p['native_preparation']=str(target_native.resolve());p['native_preparation_sha256']=review['native19_sha256']"""
assert s.count(before)==1;s=s.replace(before,after)
before="cm=(parent/'CMakeLists.txt').read_text().replace"
after="cm=(parent/'CMakeLists.txt').read_text().replace(old_include.replace('\\\\','/'),p['native_include'].replace('\\\\','/')).replace(old_library.replace('\\\\','/'),p['native_library'].replace('\\\\','/')).replace"
assert s.count(before)==1;s=s.replace(before,after)
s=s.replace('pin(__file__);files=',"pin(__file__);pin(R/'tools/m4-tree-review/prepare_mixed_controls_v3.py');files=")
exec(compile(s,str(p),'exec'),globals())
