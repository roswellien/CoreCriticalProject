"""Use exact successful fixture compiler/link ABI for seven new routes."""
from pathlib import Path
R=Path(__file__).resolve().parents[2];base=R/'tools/m4-widget-native/build_fixture_v5.py';s=base.read_text()
s=s.replace("R/'tools/m4-widget-native/build_fixture_v5.ps1'","R/'tools/m4-widget-native/build_fixture_v5.ps1',base,R/'tools/m4-fps-native/build_fixture.ps1'")
exec(compile(s,str(base),'exec'),globals())
