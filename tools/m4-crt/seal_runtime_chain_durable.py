"""Explicit physical durable bindings, retaining historical flat maps intact."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/m4-runtime/durable-r4-chain-r1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(ok,why):
 if not ok:raise ValueError(why)
need(not OUT.exists(),'Fresh durable output')
preservepath=ROOT/'reports/m4-runtime/pre-service-continuation-extension/manifest.json'
need(sha(preservepath)=='86e4b7372d3c1e766f2e17cd84176805b59b87af17b97f6031ddffa7fdb39324','Exact preservation')
preserve=json.loads(preservepath.read_text())
replacements={v['original_path']:v for v in preserve['literal_source_copies']}
files={};replaced=[];maps=[]
for relative in ('reports/m4-runtime/independent-root-r4/pins.json','reports/m4-initializer-chain/author-review-r1/pins.json'):
 p=ROOT/relative;mapping=json.loads(p.read_text());maps.append({'path':str(p),'sha256':sha(p)})
 for original,identity in mapping['files'].items():
  h=identity['sha256'] if isinstance(identity,dict) else identity
  physical=original
  if original in replacements:
   r=replacements[original];need(r['sha256']==h,'Replacement exactly agrees with historical map')
   physical=r['preserved_path'];replaced.append({'historical_map':str(p),'original_path':original,'durable_path':physical,'sha256':h})
  need(sha(physical)==h,'Durable physical file identity '+physical)
  need(physical not in files or files[physical]==h,'Durable binding conflict');files[physical]=h
 files[str(p)]=sha(p)
for path in (preservepath,ROOT/'reports/m4-runtime/context-r4/build.json',ROOT/'reports/m4-runtime/independent-root-r4/review.json',ROOT/'reports/m4-initializer-chain/author-review-r1/report.json',Path(__file__).resolve()):files[str(path)]=sha(path)
for path in (ROOT/'reports/m4-runtime/durable-schema-attempt1').iterdir():files[str(path.resolve())]=sha(path)
OUT.mkdir(parents=True)
report={'passed':True,'scope':'Physical durable aggregate for immutable runtime r4 and chain r1; no new Runtime/CRT/menu acceptance',
 'historical_maps':maps,'source_replacements':replaced,'source_preservation_manifest':str(preservepath),
 'rule':'Each older live source identity is bound to its exact preserved literal file; old maps remain historical documents, not directly rehashable live maps after extension.',
 'old_static_chain_ABI_only':True,'fresh_extended_runtime_chain_compilation_required':True,'whole_M4_complete':False}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');files[str(OUT/'report.json')]=sha(OUT/'report.json')
(OUT/'pins.json').write_text(json.dumps({'files':files,'source_replacements':replaced},indent=2)+'\n')
print(json.dumps({'bindings':len(files),'replacements':len(replaced),'report_sha256':sha(OUT/'report.json'),'pins_sha256':sha(OUT/'pins.json')}))
