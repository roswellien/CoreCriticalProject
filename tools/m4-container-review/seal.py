"""Freeze the complete successful persistent116 independent provider evidence."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/m4-pipeline'))
from manifests import normalized,digest,verify_manifest
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(name):
 out=R/'reports/m4-container-review'/name;need(not out.exists(),'Fresh provider seal');out.mkdir(parents=True);pins={};dependencies={}
 def add(p,h):
  p=normalized(str(Path(p).resolve()));h=digest(h);need(p not in pins or pins[p]==h,'Conflicting frozen physical input '+p);pins[p]=h
 receipts={
  'reports/m4-container-review/provider-source-r2/report.json':'2d1d2b2b4270821a1ea345c0dcc50b7c1d129ee9d812b3e6a5f29ced4b58628c',
  'reports/m4-container-review/preparation-r2/report.json':'ea24d10040359ac4d1efb65208c87feab57863ed128c3973da646e22e3f7440a',
  'reports/m4-container-review/provider-review-r1/report.json':'802a41ef8865360900a5cf0a87242a3e551614431122a8d603ebe9102cb38b79',
  'reports/m4-container-review/preflight-r1/report.json':'a102855701639f356308f8f7f39338a7dea6975ce1c55c45aff4fc9eddd96aee',
  'reports/m4-container-review/observer-static-r1/report.json':'f6f8b3d9f5d278af06b52bac560daaac76105ba43b0847d6be128813591bbba4',
  'reports/m4-container-review/observer-compiled-r3/report.json':'9cd673ab15e2a6e06baa617a7d84ee341e85fb80d41531e253a7449933642e59',
  'reports/m4-container-review/malloc-edx-review-r1/report.json':'8bc939985ffefea05db6a49bd863864f3e502477d0507004b95ba563bafe5545',
  'reports/m4-container-source/original-game-source-r6/report.json':'6f3f23261d711ce6a8a423b79d82410a2e75ab7e1ffcd6e27def7c27d0a408a5',
  'reports/m4-container-source/original-validation-r1/report.json':'4012b8c62c821131469e012f1e10ba31b621c524c6b0a9b042d5150dd2f3067b',
  'reports/m4-container-native/preparation-r2/report.json':'4d1eb214d383b99a857e927e90768e3de4f87429f1c4def90c49067340e02164',
  'reports/m4-joint-startup116/build-r1/build.json':'40ace32eba53dbf035cf47236f23e4a2e1a7316336c14f7c283ea000e0e0d380',
  'reports/m4-joint-startup116-root/execution-r1/report.json':'0a852e3714e4b3dbc069f5a9b83e0107780c810796090b24537fd335e78c0e5a'}
 values={}
 for p,h in receipts.items():
  path=R/p;need(sha(path)==h,'Exact completed receipt '+p);r=json.loads(path.read_bytes());need(r['passed'],'Passed required receipt '+p);add(path,h);dependencies[str(path)]=h;values[p]=r
  for k,v in r.get('files',{}).items():add(k,v)
  for k,v in r.get('physical_inputs',{}).items():add(k,v)
  manifest=path.parent/'pins.json'
  if manifest.exists():
   add(manifest,sha(manifest))
   for k,v in json.loads(manifest.read_bytes())['files'].items():add(k,v)
 source=values['reports/m4-container-review/provider-source-r2/report.json'];c=source['provider_counts']
 need(c['complete116_provider_sequences']==12 and c['actual_source_frees']==840 and c['actual_heap_destroys']==c['actual_post_HeapDestroy_identity_proofs']==12 and c['actual_first_replay_msize_queries']==24,'Whole persistent source/owner/query/cleanup extent')
 need(c['whole_State_checkpoints']==c['whole_CPU_checkpoints']==c['whole_FX_checkpoints']==21996 and c['whole_checkpoint_pages']==1857552,'Every provider checkpoint carries entire machine/pages')
 paths=[Path(__file__).with_name(n)for n in('observe116_v2.py','final_observer116_v2.py','string_observer116.py','event_model.py','exact_equal.py','provider_review.py','derive.py')]+[R/'tools'/d/n for d,n in(('m4-container-source','game_model.py'),('m4-onexit-review','provider_bridge.py'),('m4-onexit-review','provider_capture.py'),('m4-onexit-review','provider_responses.py'),('m4-onexit-review','provider_responses_v2.py'),('m4-onexit-review','provider_model.py'),('m4-mfc-review','provider_model.py'))]
 copies=[]
 for path in paths:
  h=sha(path);add(path,h);copy=out/'sources'/path.parent.name/path.name;copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(path.read_bytes());add(copy,h);copies.append(dict(source=str(path),copy=str(copy),sha256=h))
 add(__file__,sha(__file__));add(R/'tools/m4-pipeline/manifests.py',sha(R/'tools/m4-pipeline/manifests.py'));physical=verify_manifest(pins);need(physical['passed'],'Full conflict-normalized physical source/capture closure')
 report=dict(passed=True,scope='Frozen independent persistent116 provider source from one true bootstrap BEFORE, literal operand contracts and genuine typed API leaf observations. Every source allocation, whole owner backing, NULL free, borrowed identity, endpoint, subsequent growth and source cleanup retains complete observations.',persistent_game_phases=1392,complete_provider_sequences=12,full_source_state_checkpoints=21996,whole_checkpoint_pages=1857552,counts=c,copied_sources=copies,dependencies=dependencies,source_seed='One true bootstrap BEFORE; no per-phase or candidate AFTER machine seed',growth_prediction='Two actual original msize calls to same old live owner at first genuine replay; measured capacity352 minus exact selectedused352 and literal4B append predicts1 additional growth replay',API_response_injection=False,callback_execution=False,handler_TLS_or_actual_allocation_null_paths_admitted=False,native_borrowed_pointee_mapped=False,whole_original_provider_stack_equality_claimed=False,initializer_credit=False,whole_M4_complete=False,physical_closure=physical,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');add(out/'report.json',sha(out/'report.json'));(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),physical_inputs=len(pins),copied_sources=len(copies))))
if __name__=='__main__':main(*sys.argv[1:])
