"""Disambiguate the inherited numerical Session from the current registry Session."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-widget-native/prepare_fixture_v7.py';s=p.read_text()
old="text=text.replace('#include \"onexit_session.hpp\"'"
new="text=text.replace('#include \"session.hpp\"','#include \"'+(R/'reports/m4-joint-startup130/preparation-r2/session.hpp').as_posix()+'\"');text=text.replace('#include \"onexit_session.hpp\"'"
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("'tools/m4-widget-native/derive_fixture_v7.py'", "'tools/m4-widget-native/derive_fixture_v7.py','tools/m4-widget-native/derive_fixture_v8.py'")
p=R/'tools/m4-widget-native/prepare_fixture_v8.py';assert not p.exists();p.write_text(s)
