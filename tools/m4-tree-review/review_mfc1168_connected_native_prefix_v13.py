"""Retain every compiled cold missing edge as well as the six O2 reached edges."""
from pathlib import Path
BASE13=Path(__file__).with_name('review_mfc1168_connected_native_prefix_v12.py')
program=BASE13.read_text();anchor='program=BASE12.read_text();'
assert program.count(anchor)==1
program=program.replace(anchor,"program=BASE12.read_text().replace('len(source_targets)==6','len(source_targets)>=6').replace(\"counts['actual_missing_thunk_source_CALL_targets']+=6\",\"counts['actual_missing_thunk_source_CALL_targets']+=len(source_targets)\");")
exec(compile(program,str(BASE13),'exec'),globals())
