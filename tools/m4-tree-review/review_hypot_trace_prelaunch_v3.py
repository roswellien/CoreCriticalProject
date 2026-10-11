"""Same physical preflight, bound to the worker with three overlaps removed."""
from pathlib import Path
import hashlib
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).with_name('review_hypot_trace_prelaunch.py')
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == '7a6409b32f1dfa6be52bc83144ec15e4e17016aaf392ecff4276b055a098b086'
PREVIOUS = Path(__file__).with_name('review_hypot_trace_prelaunch_v2.py')
assert hashlib.sha256(PREVIOUS.read_bytes()).hexdigest() == '7a698fa31f3d13e9b4855af9d0e3579f774b3b3c40a47642ea913b7c12dbc985'
source = BASE.read_text(encoding='utf-8')
replacements = [
    ("'archive_reader_opened','original_executed','initializer_credit','normal_return_replay_used'",
     "'archive_reader_opened','original_executed','normal_return_replay_used'"),
    ("    need([prep[k] for k in ('trace_event_bytes'",
     "    need(type(prep['initializer_credit']) is int and prep['initializer_credit']==0, 'Exactly zero initializer credit')\n    need([prep[k] for k in ('trace_event_bytes'"),
    ("PREP = R / 'reports/m4-hypot-original/trace-preparation-r5'", "PREP = R / 'reports/m4-hypot-original/trace-preparation-r6'"),
    ("BUILD = R / 'reports/m4-hypot-original/trace-build-r4'", "BUILD = R / 'reports/m4-hypot-original/trace-build-r5'"),
    ('0431e475a5e7f11be98fafe2adcff2503f4f5882592f760ccee632d651b1ced8',
     '4328b1b5a0672c829cc6e5a4e8a2f6ccc2dae9ced3924085ea9598307e9ad56f'),
    ('42aa622268789d4694423e47c632b4531b625dd1b915550f83dc10d593c6f53a',
     '9789874d306e45f6ed25799da3cf4eba93d3bf5ea05e778c3d3a68d32d9ca6b0'),
    ("    readlog=pin(BUILD/'build-x86/mw34_joint_startup124_original.dir/Release/mw34_joi.8D15F356.tlog/CL.read.1.tlog').read_text(encoding='utf-16')",
     "    readlogs=list((BUILD/'build-x86/mw34_joint_startup124_original.dir/Release').glob('*.tlog/CL.read.1.tlog'))\n    need(len(readlogs)==1,'Exactly one actual current compiler read log')\n    readlog=pin(readlogs[0]).read_text(encoding='utf-16')")
]
for old, new in replacements:
    assert source.count(old) == 1, old
    source = source.replace(old, new)
exec(compile(source, str(BASE), 'exec'), {'__file__': str(Path(__file__).resolve()), '__name__': '__main__'})
