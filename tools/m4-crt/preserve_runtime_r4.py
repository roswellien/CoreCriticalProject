"""Preserve literal r4 and its restricted review before a new additive API."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/m4-runtime/pre-service-continuation-extension'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(ok,why):
 if not ok:raise ValueError(why)
need(not OUT.exists(),'Fresh preservation directory required')
buildpath=ROOT/'reports/m4-runtime/context-r4/build.json'
reviewpath=ROOT/'reports/m4-runtime/independent-root-r4/review.json'
mapath=ROOT/'reports/m4-runtime/independent-root-r4/pins.json'
need(digest(buildpath)=='1c37ebebcf8e347b438b9af9170d6db487dfc613dc65cf2ff3db19e5703e7815','Exact r4 build')
build=json.loads(buildpath.read_text());review=json.loads(reviewpath.read_text());oldpins=json.loads(mapath.read_text())
need(build['passed'] and review['passed'],'Earlier passed baseline')
bindings={}
for group in ('source_files','tool_files','artifacts'):bindings.update(build[group])
bindings.update(oldpins['files'])
for p in (buildpath,reviewpath,mapath,Path(__file__)):bindings[str(p.resolve())]=digest(p)
for p,h in bindings.items():need(digest(p)==h,'Immutable current identity '+p)
OUT.mkdir(parents=True)
copies=[]
for p,h in build['source_files'].items():
 source=Path(p);dest=OUT/'sources'/source.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes())
 need(digest(dest)==h,'Literal source identity');copies.append({'original_path':p,'preserved_path':str(dest),'sha256':h})
manifest={'passed':True,'reason':'Preserve r4 and restricted independent review before measured service-continuation API extension',
 'previous_build_sha256':digest(buildpath),'previous_review_sha256':digest(reviewpath),'previous_pins_sha256':digest(mapath),
 'literal_source_copies':copies,'unchanged_existing_files':bindings,
 'historical_mutable_source_paths':'After extension, resolve older live source bindings through these exact literal copies; do not naively demand former bytes at updated live paths.',
 'previous_runtime_scope':'No original game/CRT/menu; raw memory swallowed fault and legacy FX/ENV limits preserved.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'preserved_sources':len(copies),'unchanged_files':len(bindings),'manifest_sha256':digest(OUT/'manifest.json')}))
