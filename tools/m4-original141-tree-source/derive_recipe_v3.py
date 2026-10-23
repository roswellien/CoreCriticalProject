from pathlib import Path
import hashlib
R=Path(__file__).resolve().parents[2]
p=R/'tools/m4-original141-tree-source/prepare_admission_recipe_v2.py';s=p.read_text(encoding='utf-8').replace('admission-recipe-r2','admission-recipe-r3').replace('run_ordinary_v2.py','run_ordinary_v4.py')
anchor="controls,control_gate=report(R/'reports/m4-original141-tree-source/ordinary-boundary-controls-r1/report.json','ba5f7efdf71cba46f591fe56db0f8154074db7bfb5d1edb25679658ddf69dfdc')"
assert s.count(anchor)==1
new=anchor
for directory,digest in [('authorized-io-preparation-r1','ffa8509d6688e48c544fd5ce399a5d0870a64007520af3c03e38834d134d94f6'),('authorized-io-preparation-r2','156de21c1b39e95941f70bdd94f7716a06a8ddffe3fdfd14521cc23b610965c9'),('import-inventory-r2','e999db06968951368c1202fd67842e57f32ebfd8ad514a2ea8f4cdb38818f1c2'),('authorized-io-controls-r1',None)]:
 if digest is None:digest=hashlib.sha256((R/'reports/m4-original141-tree-source'/directory/'report.json').read_bytes()).hexdigest()
 new+="\n report(R/'reports/m4-original141-tree-source/"+directory+"/report.json',"+repr(digest)+")"
s=s.replace(anchor,new);q=p.with_name('prepare_admission_recipe_v3.py');assert not q.exists();q.write_text(s,encoding='utf-8')
