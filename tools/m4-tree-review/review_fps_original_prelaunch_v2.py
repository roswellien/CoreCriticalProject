"""Use the physical PE export name array and complete literal virtual target."""
from pathlib import Path
BASE=Path(__file__).with_name('review_fps_original_prelaunch.py')
program=BASE.read_text()
changes=[("physical(game,0x409b30,1)==b'\\xc3'","physical(game,0x409b30,10)==bytes.fromhex('c7817404000001000000')and physical(game,0x409b3a,5)==bytes.fromhex('e9c1631900')"),("r.get('name')=='vsprintf'","'vsprintf'in r['names']"),("pin(R/'tools/m4-fps-original/prepare.py');pin(__file__)","pin(BASE);pin(R/'tools/m4-fps-original/prepare.py');pin(__file__)")]
for a,b in changes:assert program.count(a)==1,a;program=program.replace(a,b)
exec(compile(program,str(BASE),'exec'),globals())
