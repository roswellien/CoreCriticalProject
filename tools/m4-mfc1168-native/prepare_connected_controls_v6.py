"""Additive exact IAT control mutation fix; no component behavior changes."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;adapter=p/'prepare_connected_controls_v5.py';source=adapter.read_text();tail="exec(compile(text, str(parent), 'exec'), globals())";assert source.endswith(tail+'\n')
scope={'__file__':str(adapter),'__name__':'prepare_adapter_only'};exec(compile(source[:-len(tail+'\n')],str(adapter),'exec'),scope);text=scope['text'];parent=scope['parent']
assert text.count("R/'tools/m4-mfc1168-native/connected_controls_v4.inc'")==1
text=text.replace("R/'tools/m4-mfc1168-native/connected_controls_v4.inc'","R/'tools/m4-mfc1168-native/connected_controls_v5.inc'")
text=text.replace('pin(sys.executable)',"pin(R/'tools/m4-mfc1168-native/derive_connected_controls_v5.py');pin(R/'tools/m4-mfc1168-native/prepare_connected_controls_v6.py');pin(sys.executable)")
exec(compile(text,str(parent),'exec'),globals())
