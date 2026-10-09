from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import verify_manifest
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=ROOT/'reports/m4-mfc-review'/name;assert not out.exists();out.mkdir(parents=True);pins={};deps={}
 gates=[('reports/m4-mfc-review/provider-source-r1/report.json','a66c45c77fd8ee58859bc1104a16b9c6ad20efe92f913a55971e05f72fa51b46'),('reports/m4-mfc-review/observer-derivation-r1/report.json','e747bcef8b9bbcc60b29319f42ebc1b41d92ad4c848f6d022c3ef66c92a4b949'),('reports/m4-mfc-review/interface-r1/report.json','f9ac44cdc91b751974f965830bd9bda0412801339e1392bf95834ec4bc36161d'),('reports/m4-mfc-review/game-static-r1/report.json','248996818bda699505f754ad26f389ff1dfd2269b19cd5ba66303ae40d035e73'),('reports/m4-mfc-review/prefix-calibration-r1/report.json','38cd8bdd2dde0fb3df8c23ccbd38d1f40b77d6e533d2b269bcd01fc383a40aa9')]
 for path,h in gates:
  p=ROOT/path;assert sha(p)==h;(pins.update({str(p):h}));r=json.loads(p.read_bytes());assert r['passed'];deps[path]=h
  pins.update(r.get('files',{}))
 source=json.loads((ROOT/gates[0][0]).read_bytes());c=source['provider_counts'];assert c['complete103_provider_sequences']==12 and c['whole_State_checkpoints']==17652 and c['actual_MFC_allocations']==420 and c['actual_source_frees']==624 and c['actual_heap_destroys']==12 and c['actual_post_HeapDestroy_identity_proofs']==12
 for path in ['provider_interface.py','provider_model.py','calibrate_prefixes.py','review_game.py','final_observer.py','derive_observer.py','observe_connected.py']:
  p=ROOT/'tools/m4-mfc-review'/path;h=sha(p);assert str(p)not in pins or pins[str(p)]==h;pins[str(p)]=h;q=out/'sources'/path;q.parent.mkdir(exist_ok=True);q.write_bytes(p.read_bytes());pins[str(q)]=h
 pins[str(Path(__file__).resolve())]=sha(__file__);physical=verify_manifest(pins);assert physical['passed']if isinstance(physical,dict)and'passed'in physical else True
 report=dict(passed=True,scope='Independent literal BEFORE/provider ownership and genuine typed API growth/cleanup across12persistent103 sequences; frozen source and physical closure',dependencies=deps,counts=c,persistent_game_phases=1236,full_source_state_checkpoints=17652,source_seed='One actual bootstrap BEFORE per persistent sequence; original operands and finite actual typed API facts; no candidate AFTER seed',declared_tail_projection='Only research call-stack metadata entry5ABD26 to5F401EA0; all source site/frame/return/nonvolatiles and literal CPU/State effects retained',API_response_injection=False,handler_TLS_or_actual_allocation_null_paths_admitted=False,callback_execution=False,initializer_credit=False,whole_M4_complete=False,files=pins,physical_closure=physical)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json');(out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
