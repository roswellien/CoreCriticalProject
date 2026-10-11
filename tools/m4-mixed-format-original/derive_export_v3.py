from pathlib import Path
p=Path(__file__).resolve().parent;s=(p/'export_native_v2.py').read_text()
a="need(len(accesses)==11,'Ten literal owner writes and one reached owner read')";b="need(len(accesses)==10 and all(r['write']for r in accesses),'Ten exact literal MFC owner writes; no reached dynamic MFC owner read')"
assert a in s;s=s.replace(a,b).replace('owned_access_rows=11','owned_access_rows=10')
(p/'export_native_v3.py').write_text(s)
