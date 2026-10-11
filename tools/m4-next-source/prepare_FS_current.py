"""Resolve current independent observer and full native producer receipts."""
from pathlib import Path
T=Path(__file__).resolve().parent
for name in('validate_FS_observations','compare_FS_policy','compare_paired_policy'):
 source=T/(name+('_v3.py'if name!='compare_paired_policy'else '_v4.py'))
 target=T/(name+('_v4.py'if name!='compare_paired_policy'else '_v5.py'))
 assert not target.exists();s=source.read_text()
 s=s.replace('reports/m4-vtable-original/observer-compiled-r1/report.json','reports/m4-vtable-review/observer-compiled-r1/report.json')
 s=s.replace('reports/m4-joint-startup120-root/execution-r1/report.json','reports/m4-joint-startup120-root/execution-r3/report.json')
 compile(s,str(target),'exec');target.write_text(s)
