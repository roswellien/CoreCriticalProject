"""Exact v2 checker with immutable preparation3 owning-symbol proof."""
from pathlib import Path
import hashlib
p=Path(__file__).with_name('check_schema138_v2.py')
assert hashlib.sha256(p.read_bytes()).hexdigest()=='6a25b1108de0cbf5bfab9eef54a2266af782877b94a26a70d52e84b65e2ff1f2'
t=p.read_text()
needle="exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())"
assert t.count(needle)==1
t=t.replace(needle,"s=s.replace(\"pin(__file__);pin(sys.executable)\",\"pin(Path(__file__).with_name('check_schema138_v2.py'),'6a25b1108de0cbf5bfab9eef54a2266af782877b94a26a70d52e84b65e2ff1f2');pin(__file__);pin(sys.executable)\")\n"+needle)
exec(compile(t,str(Path(__file__).resolve()),'exec'),globals())
