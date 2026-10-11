"""Separate the integer credit count from boolean execution-scope fields."""
from pathlib import Path
import hashlib
import sys

sys.dont_write_bytecode = True
BASE = Path(__file__).with_name('review_hypot_trace_prelaunch.py')
assert hashlib.sha256(BASE.read_bytes()).hexdigest() == '7a6409b32f1dfa6be52bc83144ec15e4e17016aaf392ecff4276b055a098b086'
source = BASE.read_text(encoding='utf-8')
old = "'archive_reader_opened','original_executed','initializer_credit','normal_return_replay_used'"
assert source.count(old) == 1
source = source.replace(old, "'archive_reader_opened','original_executed','normal_return_replay_used'")
anchor = "    need([prep[k] for k in ('trace_event_bytes'"
assert source.count(anchor) == 1
source = source.replace(anchor, "    need(type(prep['initializer_credit']) is int and prep['initializer_credit']==0, 'Exactly zero initializer credit')\n" + anchor)
exec(compile(source, str(BASE), 'exec'), {'__file__': str(Path(__file__).resolve()), '__name__': '__main__'})
