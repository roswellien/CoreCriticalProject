"""Retain the failed r1 review; enforce the actual empty gap-list schema."""
from pathlib import Path
BASE=Path(__file__).with_name('review_hypot_current.py')
text=BASE.read_text()
old="need(descriptors['descriptor_gaps']==0,'Complete zero-gap descriptor inventory')"
new="need(descriptors['descriptor_gaps']==[],'Complete zero-gap descriptor inventory')"
assert text.count(old)==1
text=text.replace(old,new)
old='  pin(__file__);pin(sys.executable)'
assert text.count(old)==1
text=text.replace(old,'  pin(BASE);pin(__file__);pin(sys.executable)')
exec(compile(text,str(BASE),'exec'),globals())
