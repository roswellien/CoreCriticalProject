"""Preserve the failed source-file guard and bind corrected exact metadata."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
prior=R/'tools/m4-widget-native/prepare_fixture_v13.py';s=prior.read_text()
a="R/'tools/m4-widget-native/derive_fixture_v9.py',R/'tools/m4-widget-native/fixture_v4.cpp'"
b="R/'tools/m4-widget-native/derive_fixture_v9.py',R/'tools/m4-widget-native/derive_fixture_v10.py',R/'tools/m4-widget-native/prepare_fixture_v13.py',R/'tools/m4-widget-native/fixture_v4.cpp'"
assert s.count(a)==1
exec(compile(s.replace(a,b),str(prior),'exec'),globals())
