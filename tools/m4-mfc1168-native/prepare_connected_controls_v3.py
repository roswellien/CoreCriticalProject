from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'prepare_connected_controls_v2.py';text=parent.read_text()
needle="exec(compile(text,str(parent),'exec'),globals())"
edit="text=text.replace(\"R/'tools/m4-mfc1168-native/connected_controls.inc'\",\"R/'tools/m4-mfc1168-native/connected_controls_v2.inc'\");text=text.replace(\"pin(sys.executable)\",\"pin(R/'tools/m4-mfc1168-native/derive_connected_controls_v2.py');pin(R/'tools/m4-mfc1168-native/prepare_connected_controls_v3.py');pin(sys.executable)\");"
assert text.count(needle)==1;text=text.replace(needle,edit+needle)
exec(compile(text,str(parent),'exec'),globals())
