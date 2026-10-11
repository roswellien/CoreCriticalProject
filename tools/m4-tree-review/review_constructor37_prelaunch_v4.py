"""Retain the actual thirteen-root prerequisite collection boundary.

The two constructors have separate complete BEFORE/AFTER owner collections;
the unchanged prerequisite collection applies only to the original13 roots.
"""
from pathlib import Path
import hashlib,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
parent=R/'tools/m4-tree-review/review_constructor37_prelaunch.py'
assert hashlib.sha256(parent.read_bytes()).hexdigest()=='b41fb7810010189edba1ebf22f121e5c6d5db18a5adbf556840dad50b63ee67f'
text=parent.read_text()
changes={
 'permission in(1,2)':'permission in(0,1,2)',
 'address not in oldpack and permission==2':'address not in oldpack and permission in(0,2)',
 "assert 'mov eax,DWORD PTR [ecx+4]'in asm and 'ret'in asm":"assert physical(game,0x40a850,4)==bytes.fromhex('8b4104c3') and ' db 08bh,041h,004h' in asm and ' db 0c3h' in asm",
 "assert 'if(phase<15)constructor_collect' in main_cpp":"assert 'if(phase<13)constructor_collect' in main_cpp",
 "pin(R/'tools/m4-constructor-original/run.py');pin(__file__);":"pin(parent);pin(R/'tools/m4-constructor-original/run.py');pin(__file__);",
}
for before,after in changes.items():
 assert text.count(before)==1; text=text.replace(before,after)
exec(compile(text,str(parent),'exec'),globals())
