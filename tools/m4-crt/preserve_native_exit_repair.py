"""Physical preservation of r8 and independent causal findings before repair."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'reports/m4-runtime/pre-native-exit-repair'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(ok,why):
 if not ok:raise ValueError(why)
need(not OUT.exists(),'Fresh native-exit repair preservation')
oldcopies={}
for rel in ('reports/m4-runtime/pre-service-continuation-extension/manifest.json','reports/m4-runtime/pre-public-bytes-repair/manifest.json'):
 j=json.loads((ROOT/rel).read_text())
 for c in j['literal_source_copies']:oldcopies[(c['original_path'],c['sha256'])]=c['preserved_path']
buildpath=ROOT/'reports/m4-runtime/context-r8/build.json';need(sha(buildpath)=='660b00619b6761412729a817fb352c414af82a4df890fe68fb0eee7adb405d54','Exact r8 build')
build=json.loads(buildpath.read_text(encoding='utf-8-sig'));need(build['passed'],'r8 authored pass')
peerpath=ROOT/'reports/m4-runtime/independent-service-r7/report.json';need(sha(peerpath)=='ab2f493b1c550a00200ee81e7247b304e7249567f0001b37341dda3a412cd6c7','Exact independent findings')
sources=dict(build['source_files'])
for directory in ('tools/m4-crt','tests/m4-crt'):
 for p in (ROOT/directory).rglob('*'):
  if p.is_file() and p.suffix in ('.py','.cpp','.hpp','.ps1','.asm','.txt') and '__pycache__' not in str(p):sources[str(p)]=sha(p)
sources[str(ROOT/'docs/m4-crt-contract.md')]=sha(ROOT/'docs/m4-crt-contract.md')
OUT.mkdir(parents=True);copies=[]
for original,h in sources.items():
 p=Path(original);q=OUT/'sources'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes());need(sha(q)==h,'Exact current source copy')
 copies.append({'original_path':original,'preserved_path':str(q),'sha256':h});oldcopies[(original,h)]=str(q)
files={};replacements=[]
def add(original,h):
 physical=oldcopies.get((original,h),original);need(sha(physical)==h,'Physical immutable file '+physical)
 if physical!=original:replacements.append({'original_path':original,'preserved_path':physical,'sha256':h})
 need(physical not in files or files[physical]==h,'Conflicting immutable identities');files[physical]=h
for group in ('source_files','tool_files','artifacts'):
 for p,h in build[group].items():add(p,h)
for rel in ('reports/m4-runtime/independent-service-r7/pins.json','reports/m4-runtime/durable-r4-chain-r1/pins.json','reports/m4-crt/provider-recovery-r1/pins.json'):
 p=ROOT/rel;j=json.loads(p.read_text())
 for original,identity in j['files'].items():add(original,identity['sha256'] if isinstance(identity,dict) else identity)
 add(str(p),sha(p))
for p in (buildpath,peerpath,ROOT/'reports/m4-runtime/pre-public-bytes-repair/manifest.json',Path(__file__).resolve()):add(str(p),sha(p))
for p in (ROOT/'reports/m4-runtime/independent-service-r7').rglob('*'):
 if p.is_file():add(str(p),sha(p))
manifest={'passed':True,'scope':'Preserve authored r8 pass and independently measured r7 failures before generic exit/provider-binding repair; no service/game equivalence',
 'literal_source_copies':copies,'physical_unchanged_files':files,'explicit_historical_source_replacements':replacements,
 'independent_findings':{'path':str(peerpath),'sha256':sha(peerpath),'status':'failed, three findings retained'},
 'previous_build':{'path':str(buildpath),'sha256':sha(buildpath)},'whole_M4_complete':False}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');files[str(OUT/'manifest.json')]=sha(OUT/'manifest.json')
(OUT/'pins.json').write_text(json.dumps({'files':files,'source_replacements':replacements},indent=2)+'\n')
print(json.dumps({'source_copies':len(copies),'physical_bindings':len(files),'manifest_sha256':sha(OUT/'manifest.json'),'pins_sha256':sha(OUT/'pins.json')}))
