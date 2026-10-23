"""Exact synthetic object facade for preflight v3, no filesystem object opening."""
from pathlib import Path
import hashlib
p=Path(__file__).with_name('preflight_schema_v3.py');s=p.read_text()
assert s.count("pin=lambda p:p,bf=Path('.')")==1
s=s.replace("pin=lambda p:p,bf=Path('.')","pin=lambda p:type('SyntheticObject',(),{'read_bytes':lambda self:bytes()})(),bf=Path('.')")
exec(compile(s,str(Path(__file__).resolve()),'exec'),globals())
