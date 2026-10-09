"""Additive completed native-capture publication; no native execution."""
import json, pathlib, sys, time
sys.dont_write_bytecode=True
from transport import ROOT, T, need, read_json, CaptureBundle, pack_capture, sha_file, publish_bytes, semantic_inventory, PINS, verify_manifest
BASE=ROOT/'reports/m4-crt-parser-prefix'

def main(directory):
 out=pathlib.Path(directory).absolute()
 need(out.parent==BASE and out.name.startswith('independent-compiled-'),'Immediate new fixture output')
 raw=out/'flat-build.json';build=read_json(raw)
 need(build['passed'],'Successful completed O0/O2 worker required')
 archives={};commands=[]
 for level in ('O0','O2'):
  tree=out/level/'actual';need((tree/'COMPLETE').read_bytes()==b'COMPLETE','Closed native writer before pack')
  target=out/level/'actual.capture';started=time.perf_counter_ns();receipt=pack_capture(tree,target)
  receipt_path=out/level/'pack-receipt.json';publish_bytes(receipt_path,(json.dumps(receipt,indent=2)+'\n').encode())
  with CaptureBundle(target,receipt['sha256']) as reader:
   records={}
   for name in reader.names():
    data=reader.read_bytes(name);import hashlib
    records[name]={'size_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
   result,count=semantic_inventory(reader,records)
  inventory=out/level/'logical-inventory.json';publish_bytes(inventory,(json.dumps({'files':records},indent=2)+'\n').encode())
  archives[level]=dict(path=str(target),sha256=receipt['sha256'],inventory_path=str(inventory),inventory_sha256=sha_file(inventory),logical_files=count,flat_source_directory=str(tree),flat_files_preserved=True,COMPLETE_verified=True,pack_seconds=(time.perf_counter_ns()-started)/1e9)
  for p in (target,inventory,receipt_path):build['artifacts'][str(p)]=sha_file(p)
 sources={}
 for p,digest in build['sources'].items():T.add(sources,p,digest)
 for relative,digest in PINS.items():T.add(sources,ROOT/relative,digest)
 for p in (pathlib.Path(__file__).absolute(),ROOT/'tools/m4-crt-parser-prefix-review/transport.py',raw):T.add(sources,p,sha_file(p))
 build['sources']=sources
 build['capture_archives']=archives;build['capture_dependency_scope']='Strict complete archive logical entries; flat source trees preserved and superseded as capture dependencies'
 physical={}
 for category in ('sources','tools','libraries','entry_objects','matherr_objects','control_objects','initterm_objects','mainargs_objects','normal_argv_objects','producer_objects','parser_objects','compiler_read_headers','artifacts'):
  for p,digest in build[category].items():T.add(physical,p,digest)
 build['publication_physical_closure']=verify_manifest(physical)
 publish_bytes(out/'build.json',(json.dumps(build,indent=2)+'\n').encode())
 print(json.dumps(dict(passed=True,archives={k:v['logical_files'] for k,v in archives.items()})))

if __name__=='__main__':
 need(len(sys.argv)==2,'seal_captures.py completed fresh fixture directory');main(sys.argv[1])
