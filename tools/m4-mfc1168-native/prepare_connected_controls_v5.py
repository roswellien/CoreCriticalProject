"""Additive unchanged controls with durable first-failure facts."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
p = Path(__file__).parent
adapter = p / 'prepare_connected_controls_v4.py'
source = adapter.read_text()
tail = "exec(compile(text,str(parent),'exec'),globals())"
assert source.endswith(tail + '\n')
scope = {'__file__': str(adapter), '__name__': 'prepare_adapter_only'}
exec(compile(source[:-len(tail + '\n')], str(adapter), 'exec'), scope)
text, parent = scope['text'], scope['parent']
assert text.count("R/'tools/m4-mfc1168-native/connected_controls_v3.inc'") == 1
text = text.replace("R/'tools/m4-mfc1168-native/connected_controls_v3.inc'", "R/'tools/m4-mfc1168-native/connected_controls_v4.inc'")
text = text.replace("pin(sys.executable)", "pin(R/'tools/m4-mfc1168-native/derive_connected_controls_v4.py');pin(R/'tools/m4-mfc1168-native/prepare_connected_controls_v5.py');pin(sys.executable)")
exec(compile(text, str(parent), 'exec'), globals())
