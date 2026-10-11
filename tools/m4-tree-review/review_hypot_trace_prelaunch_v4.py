"""Admit only real uninitialized COFF BSS without treating it as file bytes."""
from pathlib import Path
import hashlib
import sys

sys.dont_write_bytecode = True
PREVIOUS = Path(__file__).with_name('review_hypot_trace_prelaunch_v3.py')
source = PREVIOUS.read_text(encoding='utf-8')
anchor = "exec(compile(source, str(BASE), 'exec'), {'__file__': str(Path(__file__).resolve()), '__name__': '__main__'})"
assert source.count(anchor) == 1
source = source.replace(anchor, '''old = "        need(raw + size <= len(data) and reloc + number * 10 <= len(data), 'Whole COFF section and relocations')"
new = "        need((raw+size<=len(data) or (raw==0 and flags&0x80 and not flags&0x20000000)) and reloc+number*10<=len(data), 'Whole initialized COFF file bytes, or declared nonexecutable uninitialized BSS, plus relocations')"
assert source.count(old)==1
source=source.replace(old,new)
old = "sections[i + 1] = dict(bytes=data[raw:raw + size], flags=flags, relocations=rows)"
new = "sections[i + 1] = dict(bytes=data[raw:raw+size] if raw else b'', logical_size=size, uninitialized=bool(flags&0x80), flags=flags, relocations=rows)"
assert source.count(old)==1
source=source.replace(old,new)
''' + anchor)
exec(compile(source, str(PREVIOUS), 'exec'), {'__file__': str(Path(__file__).resolve()), '__name__': '__main__'})
