"""Review actual SSA final-store block, retaining failed constant-label assumption."""
from pathlib import Path
BASE=Path(__file__).with_name('review_hypot_current.py')
text=BASE.read_text()
changes=[
 ("need(descriptors['descriptor_gaps']==0,'Complete zero-gap descriptor inventory')","need(descriptors['descriptor_gaps']==[],'Complete zero-gap descriptor inventory')"),
 ("'crt':blob(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL')","'CRT':blob(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL')"),
 (";last=ir.index('i32 4937989')",";last=ir.index('\\n2611:')"),
 ('\n  pin(__file__);pin(sys.executable)\n','\n  pin(BASE);pin(__file__);pin(sys.executable)\n'),
]
for old,new in changes:
 assert text.count(old)==1
 text=text.replace(old,new)
exec(compile(text,str(BASE),'exec'),globals())
