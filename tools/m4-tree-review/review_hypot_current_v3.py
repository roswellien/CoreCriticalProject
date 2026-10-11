"""Fresh exact gap-list review; preserve earlier review and wrapper failures."""
from pathlib import Path
BASE=Path(__file__).with_name('review_hypot_current.py')
text=BASE.read_text()
old="need(descriptors['descriptor_gaps']==0,'Complete zero-gap descriptor inventory')"
new="need(descriptors['descriptor_gaps']==[],'Complete zero-gap descriptor inventory')"
assert text.count(old)==1
text=text.replace(old,new)
old='\n  pin(__file__);pin(sys.executable)\n'
assert text.count(old)==1
text=text.replace(old,'\n  pin(BASE);pin(__file__);pin(sys.executable)\n')
exec(compile(text,str(BASE),'exec'),globals())
