"""The emitter's exact initialized pointer begins at its declared section offset8."""
from pathlib import Path
BASE15=Path(__file__).with_name('review_mfc1168_connected_native_prefix_v14.py')
program=BASE15.read_text();anchor='program=BASE14.read_text()'
assert program.count(anchor)==1
replacement=anchor
for before,after in[("sym['value']==0 and len(storage)in(8,24)","sym['value']in(0,8) and len(storage)in(8,24)"),('storage[:8]',"storage[sym['value']:sym['value']+8]")]:
 replacement+='.replace('+repr(before)+','+repr(after)+')'
program=program.replace(anchor,replacement)
exec(compile(program,str(BASE15),'exec'),globals())
