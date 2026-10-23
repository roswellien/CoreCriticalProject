from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-141-consumer-review/root_run_source_v1.py';s=p.read_text()
for old,new in [('root-source-execution-r1','root-source-execution-r2'),('root-source-admission-r1','root-source-admission-r2'),('5ecdc7341f7fc2db2d55477f7426f02e84ddad51e00bd0f9819c3108b4c0a6c1','946362c6794c7dfb9b0ef8dc7c139686af01cf07e1bb435568f8d088fd80a9bf'),('preparation-r4','preparation-r5'),('combined-source-provider-r1','combined-source-provider-r2')]:
 assert old in s;s=s.replace(old,new)
q=p.with_name('root_run_source_v2.py');assert not q.exists();q.write_text(s)
