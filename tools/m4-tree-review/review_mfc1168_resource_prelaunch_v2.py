"""Count all three observation restores plus the explicit caller ENV restore."""
from pathlib import Path
import hashlib
BASE=Path(__file__).with_name('review_mfc1168_resource_prelaunch.py')
SHA='ec43465a7913e4729d39fe7acb0ad6ef7a4c1ed5180a5151b26269b962d7331b'
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==SHA
text=BASE.read_text()
before="asm.count('fnstenv')==asm.count('fldenv')==3"
assert text.count(before)==1
text=text.replace(before,"asm.count('fnstenv')==3 and asm.count('fldenv')==4")
before='    pin(__file__);pin(sys.executable);out.mkdir()'
assert text.count(before)==1
text=text.replace(before,'    pin(BASE,SHA);pin(__file__);pin(sys.executable);out.mkdir()')
exec(compile(text,str(BASE),'exec'),globals())
