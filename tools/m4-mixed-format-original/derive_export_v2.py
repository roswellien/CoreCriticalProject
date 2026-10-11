from pathlib import Path
p=Path(__file__).resolve().parent;s=(p/'export_native.py').read_text()
a='0x5bb530:0x78002fe5';b='0x5bb530:0x78002fe5,0x5bb52c:0x78004a36'
assert a in s;s=s.replace(a,b)
(p/'export_native_v2.py').write_text(s)
