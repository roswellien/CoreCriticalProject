"""Use the preserved original worker's exact nullfree/vtable source filenames."""
from pathlib import Path
import ast
BASE=Path(__file__).with_name('review_fps_original_prelaunch.py')
V2=Path(__file__).with_name('review_fps_original_prelaunch_v2.py')
tree=ast.parse(V2.read_text());changes=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='changes')
program=BASE.read_text()
for a,b in changes+[("'null_broker_x86.asm'","'nullfree_observer_x86.asm'"),("'vtable_x86.asm'","'vtable_observer_x86.asm'")]:assert program.count(a)==1,a;program=program.replace(a,b)
program=program.replace('pin(BASE);pin(R/','pin(V2);pin(BASE);pin(R/')
exec(compile(program,str(BASE),'exec'),globals())
