"""Check the getter's physical MOV/RET bytes emitted with MASM db directives."""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
parent2=R/'tools/m4-tree-review/review_constructor37_prelaunch_v2.py'
assert hashlib.sha256(parent2.read_bytes()).hexdigest()=='54ac29d688aadb80d4e0b82f22313197f16f3d11a2572a1c8babc508754180c4'
wrapper=parent2.read_text()
old="exec(compile(text,str(parent),'exec'),globals())"
new="""old_getter = "assert 'mov eax,DWORD PTR [ecx+4]'in asm and 'ret'in asm"
new_getter = "assert physical(game,0x40a850,4)==bytes.fromhex('8b4104c3') and ' db 08bh,041h,004h' in asm and ' db 0c3h' in asm"
assert text.count(old_getter)==1; text=text.replace(old_getter,new_getter)
text=text.replace('pin(parent);', 'pin(parent2);pin(parent);')
exec(compile(text,str(parent),'exec'),globals())"""
assert wrapper.count(old)==1;wrapper=wrapper.replace(old,new)
exec(compile(wrapper,str(parent2),'exec'),globals())
