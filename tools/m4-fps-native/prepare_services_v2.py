"""Complete current7 copied metadata; preserve preparer1 and its receipt."""
from pathlib import Path
R=Path(__file__).resolve().parents[2];generator=R/'tools/m4-fps-native/prepare_services.py';s=generator.read_text()
a=" q=out/'report.json';q.write_text"
b=""" result.update(parent_preparation=str(report),parent_preparation_sha256=sha(report),source_relations=relations,copied_files=len(relations),unchanged_files=sum(row['byte_identical']for row in relations),roots=old['roots']+[0x40f000],source_callbacks=dict(old['source_callbacks'],**{str(0x40f000):0x40f030}))
 pins[str(R/'tools/m4-fps-native/prepare_services.py')]=sha(R/'tools/m4-fps-native/prepare_services.py')
 q=out/'report.json';q.write_text"""
assert s.count(a)==1
exec(compile(s.replace(a,b),str(generator),'exec'),globals())
