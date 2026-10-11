from pathlib import Path
p=Path(__file__).resolve().parent;root=p.parents[1]
s=(root/'tools/m4-tree-original/build125.ps1').read_text()
for a,b in [('reports/m4-tree-original','reports/m4-startup130-original'),('phases=750;roots=125;pages=43','phases=780;roots=130;pages=43;external_pages=3;combined_pages=46')]:
 assert a in s;s=s.replace(a,b)
(p/'build.ps1').write_text(s)
