from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'prepare.py').read_text();assert "reports/m4-cosine-original/preparation-r2"in s
(p/'prepare_v2.py').write_text(s.replace('reports/m4-cosine-original/preparation-r2','reports/m4-cosine-original/prep-r2'))
