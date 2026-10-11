"""Retain each inherited source adapter's exact optimization-level headers."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-widget-native/build_fixture_v4.py';s=p.read_text()
old="for inc in includes:flags+=['-I',inc]"
new="for inc in [Path(d['parent_include'])/level,Path(d['native_include'])/level,*includes]:flags+=['-I',inc]"
assert s.count(old)==1;s=s.replace(old,new).replace("R/'tools/m4-widget-native/build_fixture_v4.ps1'", "R/'tools/m4-widget-native/build_fixture_v5.ps1'")
p=R/'tools/m4-widget-native/build_fixture_v5.py';assert not p.exists();p.write_text(s)
p=R/'tools/m4-widget-native/build_fixture_v4.ps1';s=p.read_text().replace("'build_fixture_v4.py'","'build_fixture_v5.py'")
p=R/'tools/m4-widget-native/build_fixture_v5.ps1';assert not p.exists();p.write_text(s)
p=R/'tools/m4-widget-native/prepare_fixture_v5.py';s=p.read_text().replace("'tools/m4-widget-native/derive_fixture_v5.py'", "'tools/m4-widget-native/derive_fixture_v5.py','tools/m4-widget-native/build_fixture_v5.py','tools/m4-widget-native/build_fixture_v5.ps1','tools/m4-widget-native/derive_fixture_v6.py'")
p=R/'tools/m4-widget-native/prepare_fixture_v6.py';assert not p.exists();p.write_text(s)
