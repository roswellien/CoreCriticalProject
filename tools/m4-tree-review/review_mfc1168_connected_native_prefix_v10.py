"""Inspect the exact eight-byte TLS cell inside its whole zero-initialized section."""
from pathlib import Path
BASE10=Path(__file__).with_name('review_mfc1168_connected_native_prefix_v9.py')
program=BASE10.read_text()
old="assert sym['value']==0 and sections[sym['section']]['bytes']==bytes(8)"
new="storage=sections[sym['section']]['bytes'];assert sym['value']==0 and len(storage)in(8,24) and storage==bytes(len(storage)) and storage[sym['value']:sym['value']+8]==bytes(8)"
tuple_text=repr((old,new))+','
anchor='program=BASE9.read_text()'
assert program.count(anchor)==1
program=program.replace(anchor,anchor+'\nprogram=program.replace("edits8=[",'+repr('edits8=['+tuple_text)+')')
exec(compile(program,str(BASE10),'exec'),globals())
