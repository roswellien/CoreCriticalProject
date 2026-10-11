"""Bind the two actual O0/O2 anonymous TLS emitter identities, with full storage proof."""
from pathlib import Path
import runpy

previous=Path(__file__).with_name('review_mfc1168_connected_controls_prelaunch_v5.py')
scope=runpy.run_path(str(previous),run_name='generate_review_only')
text=scope['text']
globals().update({key:scope[key]for key in ('BASE','V2','V3','V4')})
name='?emitter@?A0x832FC712@m4_mfc1168_connected@mw34@@3UEmitter@?A0x832FC712@12@A'
anchor='TLS_names={'
assert text.count(anchor)==1
text=text.replace(anchor,anchor+repr(name)+',')
anchor="pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v5.py');"
assert text.count(anchor)==1
text=text.replace(anchor,anchor+"pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v6.py');")
exec(compile(text,str(__file__),'exec'),globals())
