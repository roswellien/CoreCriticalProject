"""Correct local parser API names in the retained root admission recipe."""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_joint138_prelaunch.py')
source=p.read_text()
for a,b in [("game.read_va(x['slot'],4)","game.read(game.rva_range(x['slot']-game.image_base,4)[0],4)"),('review_linked_mfc1168.py','review_mfc1168_native_prelaunch_v4.py')]:
 assert source.count(a)==1;source=source.replace(a,b)
source=source.replace('  pin(__file__);pin(sys.executable)','  pin(p);pin(__file__);pin(sys.executable)')
exec(compile(source,str(Path(__file__)),'exec'),globals())
