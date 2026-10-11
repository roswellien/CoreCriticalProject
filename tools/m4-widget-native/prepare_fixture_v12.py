"""Correct preparer-local name collision; preserve failed preparation-r11."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
base=R/'tools/m4-widget-native/prepare_fixture_v11.py';code=base.read_text()
a="R/'tools/m4-widget-native/prepare_fixture_v9.py',prior"
b="R/'tools/m4-widget-native/prepare_fixture_v9.py',R/'tools/m4-widget-native/prepare_fixture_v10.py',R/'tools/m4-widget-native/prepare_fixture_v11.py'"
assert code.count(a)==1
exec(compile(code.replace(a,b),str(base),'exec'),globals())
