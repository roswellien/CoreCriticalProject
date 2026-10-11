"""Replace the complete diagnostic assertion line, including its diff message."""
from pathlib import Path
previous=Path(__file__).with_name('review_mfc1168_connected_controls_prelaunch_v8.py')
program=previous.read_text()
program=program.replace("anchor='  assert controls==previous_controls.replace(old_line,replacement)'", "anchor=next(line for line in text.splitlines()if line.startswith('  assert controls==previous_controls.replace(old_line,replacement)'))")
program=program.replace("anchor+\"pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v8.py');\"", "anchor+\"pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v8.py');pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v9.py');\"")
exec(compile(program,str(previous),'exec'),globals())
