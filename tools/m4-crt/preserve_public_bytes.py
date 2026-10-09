"""Freeze r7/native CRT preflight before asset-free public-test repair."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/m4-runtime/pre-public-bytes-repair'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(ok,why):
 if not ok:raise ValueError(why)
need(not OUT.exists(),'Fresh public-byte preservation')
sources={};files={};builds=[]
for relative,expected in [('reports/m4-runtime/context-r7/build.json','02671aaae2e96ac9d1c507e3939c4a3047d67228b65efecae722f405e229a257'),('reports/m4-crt/native-preflight-r1/build.json',None)]:
 p=ROOT/relative;need(expected is None or sha(p)==expected,'Exact earlier r7 build');j=json.loads(p.read_text(encoding='utf-8-sig'));need(j['passed'],'Passed baseline')
 sources.update(j['source_files'])
 for key in ('source_files','tool_files','artifacts'):files.update(j[key])
 files[str(p)]=sha(p);builds.append({'path':str(p),'sha256':sha(p)})
for relative in ('reports/m4-runtime/durable-r4-chain-r1/pins.json','reports/m4-crt/provider-recovery-r1/pins.json'):
 p=ROOT/relative;j=json.loads(p.read_text());files.update(j['files']);files[str(p)]=sha(p)
for relative in ('reports/m4-runtime/context-r5','reports/m4-runtime/context-r6'):
 for p in (ROOT/relative).rglob('*'):
  if p.is_file():files[str(p)]=sha(p)
for p,h in files.items():need(sha(p)==h,'Exact current immutable identity '+p)
OUT.mkdir(parents=True);copies=[]
for original,h in sources.items():
 p=Path(original);q=OUT/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());need(sha(q)==h,'Exact literal source copy');copies.append({'original_path':original,'preserved_path':str(q),'sha256':h})
files[str(Path(__file__).resolve())]=sha(__file__)
manifest={'passed':True,'reason':'Preserve all earlier r7/native CRT sources and artifacts before removing vendor bytes from public test/recovery source',
 'previous_builds':builds,'literal_source_copies':copies,'unchanged_existing_files':files,
 'scope':'r7 continuation/CRT authored preflight only, no original service equivalence; old ABI remains historical',
 'historical_source_path_policy':'Future durable maps explicitly replace any changed historical live source path with its exact preserved literal source. Old flat maps remain retained documents.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'sources':len(copies),'unchanged_files':len(files),'manifest_sha256':sha(OUT/'manifest.json')}))
