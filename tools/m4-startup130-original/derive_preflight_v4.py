from pathlib import Path
p=Path(__file__).resolve().parent;s=(p/'preflight_v3.py').read_text();assert 'original125-preparation-r2'in s
(p/'preflight_v4.py').write_text(s.replace('original125-preparation-r2','original125-preparation-r1'))
