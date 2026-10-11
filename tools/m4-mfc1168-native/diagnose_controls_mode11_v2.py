"""Retain the actual opaque frame extent rather than assuming its row width."""
from pathlib import Path
import hashlib
p=Path(__file__).with_name('diagnose_controls_mode11.py')
text=p.read_text()
old="  frames=list(struct.iter_unpack('<8Q',a.data(prefix+'refused/frames.bin')))if prefix+'refused/frames.bin'in a.entries else []"
new="  frames={'hex':a.data(prefix+'refused/frames.bin').hex(),'bytes':len(a.data(prefix+'refused/frames.bin'))}if prefix+'refused/frames.bin'in a.entries else {}"
assert text.count(old)==1
text=text.replace(old,new).replace('connected-controls-mode11-diagnostic-r1','connected-controls-mode11-diagnostic-r2')
exec(compile(text,str(p),'exec'),globals())
