"""Use the exact original CRT domain spelling, preserving all earlier attempts."""
from pathlib import Path
BASE=Path(__file__).with_name('review_hypot_current.py')
text=BASE.read_text()
changes=[
 ("need(descriptors['descriptor_gaps']==0,'Complete zero-gap descriptor inventory')","need(descriptors['descriptor_gaps']==[],'Complete zero-gap descriptor inventory')"),
 ("'crt':blob(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL')","'CRT':blob(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL')"),
 ('\n  pin(__file__);pin(sys.executable)\n','\n  pin(BASE);pin(__file__);pin(sys.executable)\n'),
]
for old,new in changes:
 assert text.count(old)==1
 text=text.replace(old,new)
exec(compile(text,str(BASE),'exec'),globals())
