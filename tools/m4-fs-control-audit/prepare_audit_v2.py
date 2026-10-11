"""Additive correction of Windows Ninja path spelling only."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-fs-control-audit/audit.py';s=p.read_text()
a="link=next(x for x in ninja.splitlines()if x.startswith('build mw34_joint_startup109.exe:'))"
b=a+".replace(chr(92),'/')";assert s.count(a)==1;s=s.replace(a,b)
a="str((tree/'CMakeFiles/mw34_joint_startup109.dir/fixture.cpp.obj').as_posix()).replace(':','$:')in link"
assert s.count(a)==1;s=s.replace(a,"'CMakeFiles/mw34_joint_startup109.dir/fixture.cpp.obj'in link")
t=p.with_name('audit_v2.py');assert not t.exists();t.write_text(s)
