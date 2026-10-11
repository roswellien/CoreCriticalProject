"""Retain all generator versions in the exact two-emitter physical review."""
from pathlib import Path
previous=Path(__file__).with_name('review_mfc1168_connected_controls_prelaunch_v6.py')
program=previous.read_text()
program=program.replace("anchor=\"pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v5.py');\"", "anchor=\"pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v4.py');\"")
program=program.replace("anchor+\"pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v6.py');\"", "anchor+\"pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v5.py');pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v6.py');pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v7.py');\"")
exec(compile(program,str(previous),'exec'),globals())
