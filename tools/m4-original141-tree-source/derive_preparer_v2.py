from pathlib import Path
p=Path(__file__).with_name('prepare_v1.py')
s=p.read_text(encoding='utf-8').replace('preparation-r1','preparation-r2').replace('tree_source_v1.py','tree_source_v2.py')
s='\n'.join(line for line in s.split('\n')if not line.startswith(' edit("current-original138", "current-original141")'))
q=p.with_name('prepare_v2.py');assert not q.exists();q.write_text(s,encoding='utf-8')
