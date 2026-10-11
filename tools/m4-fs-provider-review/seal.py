"""Freeze the successful109 provider observer and its complete physical inputs."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import normalized,digest,verify_manifest
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(review_path,name):
 out=ROOT/'reports/m4-fs-provider-review'/name;assert not out.exists();out.mkdir(parents=True);pins={};dependencies={}
 def add(p,h):
  k=normalized(str(Path(p).resolve()));h=digest(h);assert k not in pins or pins[k]==h;pins[k]=h
 for path in (ROOT/'reports/m4-fs-provider-review/source-r1/report.json',Path(review_path).resolve(),ROOT/'reports/m4-fs-provider-review/preparation-r2/report.json',ROOT/'reports/m4-fs-provider-review/growth-policy-r1/report.json'):
  r=json.loads(path.read_bytes());assert r['passed'];add(path,sha(path));dependencies[str(path)]=sha(path)
  for p,h in r.get('files',{}).items():add(p,h)
  manifest=path.parent/'pins.json'
  if manifest.exists():
   add(manifest,sha(manifest))
   for p,h in json.loads(manifest.read_bytes())['files'].items():add(p,h)
 source=json.loads((ROOT/'reports/m4-fs-provider-review/source-r1/report.json').read_bytes());c=source['provider_counts'];assert c['complete109_provider_sequences']==12 and c['actual_source_frees']==744 and c['actual_heap_destroys']==c['actual_post_HeapDestroy_identity_proofs']==12 and c['actual_first_replay_msize_capacity_derivations']==12
 copies=[]
 for path in (Path(__file__).with_name('observe109_v3.py'),Path(__file__).with_name('final_observer109_v3.py'),Path(__file__).with_name('exact_equal.py'),ROOT/'tools/m4-fs-source/game_model.py',ROOT/'tools/m4-onexit-review/provider_bridge.py',ROOT/'tools/m4-onexit-review/provider_capture.py',ROOT/'tools/m4-onexit-review/provider_responses.py',ROOT/'tools/m4-onexit-review/provider_responses_v2.py'):
  raw=path.read_bytes();h=sha(path);add(path,h);copy=out/'sources'/path.parent.name/path.name;copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(raw);add(copy,h);copies.append(dict(source=str(path),copy=str(copy),sha256=h))
 add(__file__,sha(__file__));add(ROOT/'tools/m4-pipeline/manifests.py',sha(ROOT/'tools/m4-pipeline/manifests.py'));physical=verify_manifest(pins);assert physical['passed']
 result=dict(passed=True,scope='Frozen independent persistent109 provider source with actual typed API leaves, exact whole checkpoints, growth and cleanup',persistent_game_phases=1308,full_source_state_checkpoints=c['whole_State_checkpoints'],counts=c,copied_sources=copies,dependencies=dependencies,source_seed='One true bootstrap BEFORE; no per-phase or candidate AFTER seed',growth_prediction='First actual source replay HeapSize leaf capacity, exact selected used bytes and literal DWORD append size',API_response_injection=False,callback_execution=False,handler_TLS_or_actual_allocation_null_paths_admitted=False,initializer_credit=False,whole_M4_complete=False,physical_closure=physical,files=pins)
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');add(out/'report.json',sha(out/'report.json'));(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),physical_inputs=len(pins))))
if __name__=='__main__':main(*sys.argv[1:])
