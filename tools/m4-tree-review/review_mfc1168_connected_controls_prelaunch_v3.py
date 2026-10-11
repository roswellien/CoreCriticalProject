"""Retain generator paths for the independent physical input closure."""
from pathlib import Path
previous=Path(__file__).with_name('review_mfc1168_connected_controls_prelaunch_v2.py')
program=previous.read_text()
anchor="exec(compile(source,str(parent),'exec'),globals())"
assert program.count(anchor)==1
program=program.replace(anchor, "source=source.replace(\"text = scope['text']\",\"text = scope['text'];globals().update({k:scope[k]for k in('BASE','V2','V3','V4')})\");"+anchor)
program=program.replace("controls_prelaunch.py');pin(BASE)","controls_prelaunch.py');pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v2.py');pin(BASE)")
exec(compile(program,str(previous),'exec'),globals())
