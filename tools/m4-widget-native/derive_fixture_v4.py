"""Clang response files use GNU-style escaping; normalize path separators."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-widget-native/build_fixture_v2.py';s=p.read_text()
old="subprocess.list2cmdline([str(a)])for a in link_args"
new="'\"'+str(a).replace('\\\\','/').replace('\"','\\\\\"')+'\"'for a in link_args"
assert s.count(old)==1;s=s.replace(old,new).replace("R/'tools/m4-widget-native/build_fixture_v2.ps1'", "R/'tools/m4-widget-native/build_fixture_v3.ps1'")
p=R/'tools/m4-widget-native/build_fixture_v3.py';assert not p.exists();p.write_text(s)
p=R/'tools/m4-widget-native/build_fixture_v2.ps1';s=p.read_text().replace("'build_fixture_v2.py'","'build_fixture_v3.py'")
p=R/'tools/m4-widget-native/build_fixture_v3.ps1';assert not p.exists();p.write_text(s)
p=R/'tools/m4-widget-native/prepare_fixture_v3.py';s=p.read_text().replace("'tools/m4-widget-native/derive_fixture_v3.py'", "'tools/m4-widget-native/derive_fixture_v3.py','tools/m4-widget-native/build_fixture_v3.py','tools/m4-widget-native/build_fixture_v3.ps1','tools/m4-widget-native/derive_fixture_v4.py'")
p=R/'tools/m4-widget-native/prepare_fixture_v4.py';assert not p.exists();p.write_text(s)
