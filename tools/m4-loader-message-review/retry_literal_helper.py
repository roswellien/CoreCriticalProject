"""Exactly one ROOT-admitted recursive helper lift and O0/O2 object compile.

Inherited entry objects are physically pinned/reused. No target/generated
object/DLL or native worker is executed. Original failed outputs are retained.
"""
from pathlib import Path
p=Path(__file__).with_name('lift_literal_sorter.py');s=p.read_text();changes=[]
def change(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b);changes.append(dict(before=a,after=b))
change('literal-sorter-lifts-r1','literal-sorter-helper-lifts-r2')
change("lifter=pin(R/'local/tools/remill-x87-control-repair/remill-lift-control-21.exe')", """review_path=pin(R/'reports/m4-loader-message-review/recursive-lifter-root-review-r1/report.json','71433b68717c3e44b8378dc9290c3c5b433b09d0b49dd3cf28edb152aa492393');review=json.loads(review_path.read_bytes());need(review['passed']is True and review['helper_retry_admitted']is True and review['helper_PC']==0x10001740 and review['maximum_retry_seconds']==120,'Exactly one bounded ROOT-admitted helper retry')
  for path,h in review['files'].items():pin(path,h)
  lifter=pin(review['tool_path'],review['tool_sha256'])""")
change("for entry,limit in((0x10001000,0x10001650),(0x10001740,0x10001a60)):", """prior_path=pin(R/'reports/m4-loader-message-review/literal-sorter-lifts-r1/report.json','f2ee85012b773a68a87690bf52b654e9e86cfaddf97563c7e70a281370681e83');prior=json.loads(prior_path.read_bytes());need(prior['passed']is False and set(prior['bodies'])=={'f_10001000'},'Preserved failed helper attempt and real compiled entry only')
  for path,h in prior['files'].items():pin(path,h)
  entry_body=prior['bodies']['f_10001000'];need(entry_body['entry']==0x10001000 and set(entry_body['objects'])=={'O0','O2'}and all(0x10001000<=pc<0x10001650 for pc in entry_body['physical_PCs']),'Exact inherited entry compilation and physical scope');results['f_10001000']=entry_body;covered.update(entry_body['physical_PCs'])
  for entry,limit in((0x10001740,0x10001a60),):""")
change("pin(p)\n  q=out/'report.json'", "pin(p)\n  delta=out/'controller-source-delta.json';delta.write_text(json.dumps(changes,indent=2)+'\\n');pin(delta);pin(R/'tools/m4-loader-message-review/lift_literal_sorter.py')\n  q=out/'report.json'")
change("source_machine_evaluated=False,native_executed=False", "ROOT_helper_retry_review_sha256='71433b68717c3e44b8378dc9290c3c5b433b09d0b49dd3cf28edb152aa492393',helper_lift_retry_invocations=1,maximum_lift_seconds=120,inherited_entry_recompiled=False,source_machine_evaluated=False,native_executed=False")
original=p.read_text();inverse=s
for row in reversed(changes):
 assert inverse.count(row['after'])==1;inverse=inverse.replace(row['after'],row['before'])
assert inverse==original
exec(compile(s,str(p),'exec'))
