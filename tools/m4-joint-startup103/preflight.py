"""Seal prerequisite evidence without claiming execution or added root coverage."""
from pathlib import Path
import hashlib,json,sys,time
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=ROOT/'reports/m4-joint-startup103-root'/name;out.mkdir(parents=True,exist_ok=False);files={};rows={};started=time.perf_counter()
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 gates={
 'accepted71':('reports/m4-joint-startup71-root/acceptance-r1/report.json','64c010e01930d4f84d7df9cb8cd932669ce25b6f3f1dc21989f197282025fdfc'),
 'loader':('reports/m4-mfc-source/loader-identity-r1/report.json','7925f659144954487b1b13d781d4aee48aa0b8d20887ce9ee8aa40ce7a12b09b'),
 'ghidra':('reports/m4-mfc-ghidra/export-r1/report.json','df20391c774cfcb55b9c2b49255a80374796c23fdf491270bcfb7655fd46e4a3'),
 'interface':('reports/m4-mfc-review/interface-r1/report.json','f9ac44cdc91b751974f965830bd9bda0412801339e1392bf95834ec4bc36161d'),
 'provider_lifts':('reports/m4-mfc-native/lifts-r1/report.json',None),
 'provider_symbols':('reports/m4-mfc-native/symbol-attribution-r1/report.json',None),
 'sharing_evaluation':('reports/m4-capture-sharing-evaluation/evaluation-r1/report.json','d3af20faf8aed27cd7f350f305d1e00ce0b4d87879ea4d2a42e44c71c9636f48')}
 for label,(path,h)in gates.items():
  p=pin(ROOT/path,h);r=json.loads(p.read_bytes());assert r['passed'];rows[label]=dict(path=str(p),sha256=sha(p))
  for physical,digest in r.get('files',{}).items():pin(physical,digest)
  if(p.parent/'pins.json').exists():
   for physical,digest in json.loads(pin(p.parent/'pins.json').read_bytes())['files'].items():pin(physical,digest)
 loader=json.loads((ROOT/gates['loader'][0]).read_bytes());assert loader['original_loader_executed']and not loader['allocator_source_called']and not loader['raw_bound_targets_executed']
 assert [(x['name'],x['MFC_IAT_slot'],x['actual_loader_target'])for x in loader['bindings']]==[('malloc',0x5f49814c,0x780012b3),('free',0x5f498148,0x78001390)]
 symbols=json.loads((ROOT/gates['provider_symbols'][0]).read_bytes());assert symbols['body_count']==2 and symbols['physical_COFF_count']==4
 pin(__file__);report=dict(passed=True,scope='MFC allocation family prerequisite identity/static compilation/evaluation only; no constructor capture or current103 acceptance',gates=rows,accepted_roots=71,prospective_roots=103,new_roots_admitted=0,MFC_allocator_executed=False,whole_M4_complete=False,elapsed_seconds=time.perf_counter()-started,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report=str(out/'report.json'),sha256=sha(out/'report.json'),physical_inputs=len(files))),flush=True)
if __name__=='__main__':main(sys.argv[1])
