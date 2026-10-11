from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'prepare_connected_component.py';text=parent.read_text()
anchor="copy(R/'tools/m4-mfc1168-native'/name,out/name)"
assert text.count(anchor)==1
text=text.replace(anchor,"copy(R/'tools/m4-mfc1168-native'/('connected_component_v2.cpp'if name=='connected_component.cpp'else name),out/name)")
text=text.replace("pin(sys.executable)","pin(parent);pin(R/'tools/m4-mfc1168-native/derive_connected_component_v2.py');pin(sys.executable)")
exec(compile(text,str(parent),'exec'),globals())
