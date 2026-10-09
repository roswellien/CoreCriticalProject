"""Additive literal source/version and immutable artifact preservation."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=Path(sys.argv[1]).resolve()
assert out.parent==ROOT/'reports/m4-fp-numeric-max-integration' and not out.exists()
out.mkdir()
copies=[];bindings={}
for p in sorted((ROOT/'tools/m4-fp-numeric-max-integration').glob('*')):
 if p.is_file():
  q=out/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
  copies.append({'original_path':str(p),'preserved_path':str(q),'sha256':sha(q)});bindings[str(q)]=sha(q)
for name in sys.argv[2:]:
 base=(ROOT/'reports/m4-fp-numeric-max-integration'/name).resolve();assert base.is_relative_to(ROOT/'reports/m4-fp-numeric-max-integration')
 for p in sorted(base.rglob('*')):
  if p.is_file():bindings[str(p)]=sha(p)
 p=base/'build.json'
 if p.exists():
  b=json.loads(p.read_text(encoding='utf-8-sig'))
  for path,h in b['artifacts'].items():assert sha(path)==h;bindings[path]=h
bindings[str(Path(__file__))]=sha(__file__)
report={'passed':True,'scope':'Prior literal sources and immutable attempts preserved before NEW source mutation','source_copies':copies,'existing_immutable_bindings':bindings,'original_executed':False}
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'manifest':str(out/'manifest.json'),'sha256':sha(out/'manifest.json'),'bindings':len(bindings)}))
