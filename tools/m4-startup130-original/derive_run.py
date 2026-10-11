from pathlib import Path
p=Path(__file__).resolve().parent;root=p.parents[1]
s=(root/'tools/m4-tree-original/run125.py').read_text()
for a,b in [('original125','original130'),('reports/m4-tree-original','reports/m4-startup130-original')]:
 assert a in s;s=s.replace(a,b)
(p/'run.py').write_text(s)
