"""Freeze the successful complete120 persistent provider proof and source closure."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];H=Path(__file__).parent;sys.path.insert(0,str(R/'tools/m4-pipeline'))
from manifests import normalized,digest,verify_manifest

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def main(proof_path,proof_sha,review_path,review_sha,name):
 out=R/'reports/m4-vtable-review'/name;need(not out.exists(),'Fresh provider physical seal');out.mkdir(parents=True);pins={};dependencies={};values={}
 def add(p,h):
  p=normalized(str(Path(p).resolve()));h=digest(h);need(p not in pins or pins[p]==h,'Conflict in immutable physical closure '+p);pins[p]=h
 receipts={str(Path(proof_path).resolve()):proof_sha,str(Path(review_path).resolve()):review_sha,
  str(R/'reports/m4-vtable-review/provider-preparation-r4/report.json'):'07534d6992b2deb95ca4f481867423bf1495a91efe49e779f4f582e40e24f484',
  str(R/'reports/m4-next-review/review-r1/report.json'):'e06af6b9b8a321a8a9a6ed0653d820ad42b39914d5702d408b20f3a30cec3aed',
  str(R/'reports/m4-vtable-review/observer-static-r2/report.json'):'b7151a732bed9021d7cd80c80bdf371ac1e2866a965a52f1a49856c7b7d70aeb',
  str(R/'reports/m4-vtable-review/observer-compiled-r1/report.json'):'187a196dd06207c071148521f7cef27e151200653f1eedbd0b67f084b323589a',
  str(R/'reports/m4-vtable-review/malloc-EDX-review-r1/report.json'):'4c4fc08cc8434b79a74cc70cd7ccae4efaf206e64b68e71f72a8e576fd0b0ace',
  str(R/'reports/m4-next-source/original-game-source-r1/report.json'):'d463ca7beddb8b7ccce6c51749d9146cf70e9c7de47cc42cba9584a9430a2f04',
  str(R/'reports/m4-vtable-original/preparation-r3/report.json'):'a2e7635100478713acbc5efbc7557ba20ac8d060c461241b2ef1785b291105b5',
  str(R/'reports/m4-vtable-original/build-r2/build.json'):'ea4fb73e11dfa0d5c4b6f4145eb57df5148e5b096bb44e3fdd6c8d9d99e6dc5a',
  str(R/'reports/m4-vtable-original/validation-r1/report.json'):'2a072a38b8f0ff98377709a10da203b017bea92615baa9b153f548027565c251',
  str(R/'reports/m4-vtable-native/preparation-r4/report.json'):'b52c62a1ec6e1306a9629f53fbe80621be96404907d322efbbeef136ec10ee93',
  str(R/'reports/m4-joint-startup120/build-r3/build.json'):'da860ebe873730cc5218ce80b4b2f232d7ab8da143e28b4d4146777980a8cc4b',
  str(R/'reports/m4-joint-startup120-root/execution-r3/report.json'):'8224e3f12206e9c7bafd5fc0db43e4dead45f53b748953979cadcca1c43e249b'}
 for p,h in receipts.items():
  path=Path(p);need(sha(path)==h,'Exact completed receipt '+p);r=json.loads(path.read_bytes());need(r['passed'],'Passed completed gate '+p);add(path,h);dependencies[str(path)]=h;values[str(path)]=r
  for k in ('files','physical_inputs','generated'):
   for file,hash_ in r.get(k,{}).items():add(file,hash_)
  manifest=path.parent/'pins.json'
  if manifest.exists():
   add(manifest,sha(manifest))
   for file,hash_ in json.loads(manifest.read_bytes())['files'].items():add(file,hash_)
 source=values[str(Path(proof_path).resolve())];c=source['provider_counts'];review=values[str(Path(review_path).resolve())]
 need(c['complete120_provider_sequences']==12 and c['selected_registration_closures']==1104 and c['actual_source_frees']==840 and c['actual_heap_destroys']==c['actual_post_HeapDestroy_identity_proofs']==12,'Complete actual initializer/provider/resource extent')
 need(c['whole_State_checkpoints']==c['whole_CPU_checkpoints']==c['whole_FX_checkpoints']==review['whole_machine_checkpoints']and c['whole_checkpoint_pages']==review['whole_checkpoint_pages'],'Every source checkpoint retains whole machine/pages')
 need(not source['candidate_AFTER_machine_seed']and not source['per_phase_BEFORE_machine_seed'],'One true bootstrap BEFORE plus persistent carry')
 paths=[H/n for n in ('observe120_v3.py','final_observer120_v2.py','vtable_model.py','string_observer116.py','event_model.py','exact_equal.py','provider_review_v2.py','derive_review_v2.py','derive_provider.py','derive_provider_v2.py','derive_provider_v3.py')]+[R/'tools'/d/n for d,n in (('m4-next-source','game_model.py'),('m4-onexit-review','provider_bridge.py'),('m4-onexit-review','provider_capture.py'),('m4-onexit-review','provider_responses.py'),('m4-onexit-review','provider_responses_v2.py'),('m4-onexit-review','provider_model.py'),('m4-mfc-review','provider_model.py'),('m4-strings-review','final_observer_v2.py'))]
 copies=[]
 for path in paths:
  h=sha(path);add(path,h);copy=out/'sources'/path.parent.name/path.name;copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(path.read_bytes());add(copy,h);copies.append(dict(source=str(path),copy=str(copy),sha256=h))
 add(__file__,sha(__file__));add(R/'tools/m4-pipeline/manifests.py',sha(R/'tools/m4-pipeline/manifests.py'));physical=verify_manifest(pins);need(physical['passed'],'One complete conflict-normalized physical dependency rehash')
 report=dict(passed=True,scope='Frozen complete120 provider proof from one true bootstrap BEFORE, literal source operand contracts and authentic finite native API leaf observations. Exact six rooted static indirect CALL/RET frames, whole private owner bytes, normal frame chains, subsequent growth and source cleanup are retained. Positive/empty/normal NULL domains only; nonzero helper copy, exception/unwind/handler/TLS and entire original provider volatile-stack equivalence remain outside scope.',persistent_game_phases=1440,complete_provider_sequences=12,full_source_state_checkpoints=c['whole_State_checkpoints'],whole_checkpoint_pages=c['whole_checkpoint_pages'],counts=c,copied_sources=copies,dependencies=dependencies,source_seed='One true bootstrap BEFORE, no per-phase or candidate AFTER input',growth_prediction=source['provider_sequences'],API_response_injection=False,callback_execution=False,handler_TLS_or_actual_allocation_null_paths_admitted=False,nonzero_vtable_helper_pointee_admitted=False,whole_original_provider_stack_equality_claimed=False,initializer_credit=False,whole_M4_complete=False,physical_closure=physical,files=pins)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');add(out/'report.json',sha(out/'report.json'));(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),physical_inputs=len(pins),copied_sources=len(copies))))
if __name__=='__main__':main(*sys.argv[1:])
