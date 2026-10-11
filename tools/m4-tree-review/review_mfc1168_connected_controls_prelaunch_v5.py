"""Run the exact diagnostic delta check after loading the candidate control file."""
from pathlib import Path
previous=Path(__file__).with_name('review_mfc1168_connected_controls_prelaunch_v4.py')
program=previous.read_text()
lines=program.splitlines(True)
matches=[i for i,line in enumerate(lines) if line.startswith('injection += ') and 'checks = ' in line]
assert len(matches)==1
target="  assert controls==pin(R/'tools/m4-mfc1168-native/connected_controls_v4.inc').read_text()"
lines[matches[0]]="injection += \"source=source.replace(\" + repr("+repr(target)+") + \",\" + repr("+repr(target)+"+diagnostic_checks) + \")\\n\"\n"
program=''.join(lines)
program=program.replace("connected_controls_prelaunch_v4.py');\",","connected_controls_prelaunch_v4.py');pin(R/'tools/m4-tree-review/review_mfc1168_connected_controls_prelaunch_v5.py');\",")
exec(compile(program,str(previous),'exec'),globals())
