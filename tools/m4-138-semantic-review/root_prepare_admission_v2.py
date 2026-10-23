from pathlib import Path
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-138-semantic-review/root_admit_semantics_v1.py';s=p.read_text()
s=s.replace("out=R/'reports/m4-138-semantic-review/root-admission-r1'","out=R/'reports/m4-138-semantic-review/root-admission-r2'")
s=s.replace("prep=R/'reports/m4-138-semantic-review/preparation-r3/report.json'","prep=R/'reports/m4-138-semantic-review/preparation-r4/report.json'")
s=s.replace("d=read(prep,'d167fe5da91a37ab141b0b9b1816901c4f279c817260b06684ffdeb32f25e792')","d=read(prep,'d72457a55321e74eac1c80f7ebf33119519968729a45d46ddf6f07e565895c09')")
s=s.replace("closing=read(prep.parent/'closure-delta-hunks.json')","closing=read(R/'reports/m4-138-semantic-review/preparation-r3/closure-delta-hunks.json')")
old="  first=inverse(pin(child).read_text(),closing[label]);assert first==pin(R/middle).read_text()"
new="""  body=pin(child).read_text()
  if label=='semantic':
   body=inverse(body,read(prep.parent/'exact-two-delta-hunks.json'))
   assert body==pin(R/'tools/m4-138-semantic-review/review_paired138_v3.py').read_text()
  first=inverse(body,closing[label]);assert first==pin(R/middle).read_text()"""
assert s.count(old)==1;s=s.replace(old,new)
anchor=" for p,h in tuple(pins.items()):assert sha(p)==h"
added=""" manifest=read(R/'reports/m4-138-semantic-review/complete-admission-manifest-r1/report.json','d491d7e750eff1d8b457d8b99529435d572ca7cd03ffc51ae0893e2ae23466ba');assert manifest['passed'];collect(manifest)
 whole=read(R/'reports/m4-138-semantic-review/complete-admission-manifest-r1/required-files.json');assert len(whole)==8901
 for path,digest in whole.items():pin(path,digest)
 checks.append('Complete8901 ordinary current external dependencies including retained helper and nested import closure')
"""
assert s.count(anchor)==1;s=s.replace(anchor,added+anchor)
s=s.replace("semantic_preparation_sha256=sha(R/'reports/m4-138-semantic-review/preparation-r3/report.json')","semantic_preparation_sha256=sha(R/'reports/m4-138-semantic-review/preparation-r4/report.json')")
q=p.with_name('root_admit_semantics_v2.py');assert not q.exists();q.write_text(s)
