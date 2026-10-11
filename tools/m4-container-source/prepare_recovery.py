"""Create an additive seven-root physical recovery from accepted109."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'tools/m4-fs-source/recover_v3.py';target=ROOT/'tools/m4-container-source/recover.py'
assert not target.exists()
s=source.read_text().replace("BASE=ROOT/'reports/m4-fs-source'","BASE=ROOT/'reports/m4-container-source'")
start=s.index(" plan=json.loads(");end=s.index(" game=Module(",start)
s=s[:start]+''' planbase=ROOT/'reports/m4-fs-next-plan/plan-r3';plan=json.loads(pin(planbase/'plan.json').read_bytes());pin(planbase/'report.json','8a4131187d8357e6d2ec80262fc8bc0c1536d9cd0da7903ca02ab7e1d388239c')
 pin(ROOT/'reports/m4-joint-startup109-root/acceptance-r1/report.json','697765f750209d9bee79541b973494dca89692f4ec630057d282cbbb450266e0')
 remaining=json.loads(pin(ROOT/'reports/m4-joint-startup109-root/next-frontier-r1/remaining-roots.json').read_bytes());roots=[dict(entry=r['entry'],slot=r['slot'])for r in remaining if r['entry']in plan['root_order_by_real_table']];roots.sort(key=lambda r:r['slot']);need(len(roots)==7,'Exact new container/string family7')
 loader=json.loads(pin(BASE/'loader-identity-r2/report.json','f3c5a41e6afcb1c7373a911d5e20434f06c6eafee0cf7755a3fc372e93abd892').read_bytes());need(loader['passed'],'Genuine post-DllMain data and owning ordinal exports')
''' + s[end:]
anchor="new={str(entry):graph for entry,graph in normal.items()if entry not in priorentries}"
assert s.count(anchor)==1
s=s.replace(anchor,"priorentries.update(b['entry']for b in json.loads(pin(ROOT/'reports/m4-fs-source/lifts-r1/report.json','f5af3ee18fd942c5f58226b0ae98fca29d7bdc93877d7cfdd624a43cc0aa1ab8').read_bytes())['source_bodies'].values());"+anchor)
s=s.replace("ROOT/'reports/m4-mfc-source/recovery-r4/instruction-contracts.json','e01223ba12a4e07f50fa00a23c1297f1dcf9920d259c99ef5c4df9073d3d770e'","ROOT/'reports/m4-fs-source/recovery-r3/instruction-contracts.json','527f7b114819fc515081c8bed7cd3b13323b58424205b70107f61f3f24bf8ac7'")
s=s.replace("==109","==116").replace("original109 order","original116 order").replace("root_count=6","root_count=7").replace("original6 new FS","original7 new container/string").replace("FS_frame_contracts=plan['frame_contracts']","FS_frame_contracts=plan['normal_frames']")
s=s.replace("'fs-roots.json':entries","'container-roots.json':entries,'fs-roots.json':entries")
s=s.replace("pages.update(old['source_data_pages']);","pages.update(old['source_data_pages']);pages.add(0x5f4cc000);")
compile(s,str(target),'exec');target.write_text(s)
