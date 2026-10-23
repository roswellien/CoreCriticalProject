"""Both variant bounds and CRT global addresses derived from physical literals."""
from pathlib import Path
import ast
p=Path(__file__).with_name('inspect_message.py');v2=Path(__file__).with_name('inspect_message_v2.py');tree=ast.parse(v2.read_text());changes=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='changes'for t in n.targets));s=p.read_text()
for a,b in changes:
 b=b.replace('physical-r2','physical-r4').replace('else1540','else 1540');assert s.count(a)==1;s=s.replace(a,b)
before='[base+0x3000,base+0x3004,base+0xe2bc,base+0xe2c0,base+0xe2c4,base+0xe2c8,base+0xe2cc]'
after="[base+0x3000,base+0x3004]+[struct.unpack_from('<I',bytes.fromhex(rows[base+pc]['bytes']),off)[0]for pc,off in [(0x1a69,2),(0x1a85,2),(0x1abf,1),(0x1a9b,1),(0x1b66,2)]]"
assert s.count(before)==1;s=s.replace(before,after)
exec(compile(s,str(p),'exec'))
