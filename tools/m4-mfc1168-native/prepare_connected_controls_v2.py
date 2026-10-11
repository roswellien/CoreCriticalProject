"""Seal generated files only after all authored transformations complete."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).parent;parent=p/'prepare_connected_controls.py';text=parent.read_text()
text=text.replace("generated[str(p.resolve())]=sha(p);pin(p)","generated[str(p.resolve())]=sha(p)")
text=text.replace("pin(__file__);pin(sys.executable)","[pin(q,h)for q,h in generated.items()];pin(__file__);pin(R/'tools/m4-mfc1168-native/prepare_connected_controls.py');pin(R/'tools/m4-mfc1168-native/prepare_connected_controls_v2.py');pin(sys.executable)")
exec(compile(text,str(parent),'exec'),globals())
