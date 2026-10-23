"""Immutable run_v2 derivative: ordinary inventory budget only; no worker here."""
from pathlib import Path
import hashlib
p=Path(__file__).with_name('run_v2.py')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='5f007131081e93c70eec05657c93849c21ba05a9db2617dbbcfe6c7baa626063'
s=p.read_text()
base=p.with_name('run_v1.py')
assert hashlib.sha256(base.read_bytes()).hexdigest()=='3c2768c447e9804a8a8ee800e03171ff4ca030a4cbc9000822ef6824b7641d35'
needle="exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())"
assert s.count(needle)==1
replacement="""a='assert len(leaves)<=4096 and sum(p.stat().st_size for p in leaves)<=128*1024*1024'
b='assert len(leaves)<=100000 and sum(p.stat().st_size for p in leaves)<=512*1024*1024'
assert s.count(a)==1
s=s.replace(a,b)
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())"""
s=s.replace(needle,replacement)
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
