from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'prepare_v2.py').read_text()
for a,b in [('reports/m4-cosine-original/prep-r2','reports/m4-cosine-original/prefix-preparation-r2'),('reports/m4-cosine-original/validation-r2','reports/m4-cosine-original/prefix-validation-r2')]:
 assert a in s;s=s.replace(a,b)
(p/'prepare_v3.py').write_text(s)
