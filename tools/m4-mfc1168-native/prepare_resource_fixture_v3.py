from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'prepare_resource_fixture_v2.py';text=parent.read_text()
text=text.replace('fixture_resource_v2.cpp','fixture_resource_v3.cpp')
text=text.replace("R/'tools/m4-mfc1168-native/derive_resource_fixture_v2.py',", "R/'tools/m4-mfc1168-native/derive_resource_fixture_v2.py',R/'tools/m4-mfc1168-native/derive_resource_fixture_v3.py',R/'tools/m4-mfc1168-native/prepare_resource_fixture_v2.py',")
exec(compile(text,str(parent),'exec'),globals())
