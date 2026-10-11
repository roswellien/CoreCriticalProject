"""Read-only complete120 provider observer, growth and finite dispatch proof review."""
from pathlib import Path
import ast,difflib,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];H=Path(__file__).parent;sys.path.insert(0,str(R/'tools/m4-pipeline'))
from manifests import verify_manifest
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(proof_path,proof_sha,name):
 out=R/'reports/m4-vtable-review'/name;need(not out.exists(),'Fresh provider review');out.mkdir();pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical provider input');pins[str(p)]=v;return p
 proof=json.loads(pin(proof_path,proof_sha).read_bytes());need(proof['passed'],'All actual persistent120 provider sequences completed')
 prep=json.loads(pin(R/'reports/m4-vtable-review/provider-preparation-r4/report.json','07534d6992b2deb95ca4f481867423bf1495a91efe49e779f4f582e40e24f484').read_bytes());need(prep['passed']and prep['syntax_checked'],'Frozen additive syntax-checked observer')
 for mapping in('files','generated'):
  for p,h in prep[mapping].items():pin(p,h)
 old=pin(H/'final_observer120.py').read_text();new=pin(H/'final_observer120_v2.py').read_text();need(new==old.replace('old_ownerand','old_owner and'),'Unused draft repair changes only missing token whitespace')
 intermediate=pin(H/'observe120_v2.py').read_text();need(intermediate==pin(H/'observe120.py').read_text().replace('final_observer120','final_observer120_v2').replace('finally:a.close()','finally:a.close();del a'),'Outer only changes reviewed observer binding and safe post-close reader release')
 release='   finally:\n    a.close()\n    a.entries.clear()\n    for closed_bundle in a.bundles:closed_bundle._entries.clear()\n    a.bundles.clear()\n    del a'
 outer=pin(H/'observe120_v3.py').read_text();need(outer==intermediate.replace('   finally:a.close();del a',release),'Final derivative releases only the closed dictionary inventory after complete per-level source and checkpoint validation')
 for s in(new,outer):ast.parse(s)
 finish=new[new.index(' def finish('):new.index('\ndef configure(')];need("initial_used=vector['next']-vector['begin']"in finish and "capacity_steps=(vector['capacity']-initial_used)//4+1 if vector['capacity'] else None"in finish,'Initial growth geometry derives from exact persistent source alias/cache')
 need("queries=[f for f in responses.facts[first_API:responses.index]if f['name']=='HeapSize']"in finish and "if first_query_capacity is None and queries"in finish and "(f['words'][16],f['words'][22])==old_owner and f['words'][17]==first_query_capacity"in finish,'First genuinely reached ordinary/realloc-side msize facts bind same old full native owner/source alias/capacity')
 need("derived=(first_query_capacity-initial_used)//4+1"in finish and 'n==observed_replays==capacity_steps'in finish and "m.invoke_external(0x410210,0xffffffa0,responses)"in finish and "registry-replay-{92+n}-before"in finish and "registry-replay-{92+n}-after"in finish,'Every additional registration source step and complete before/after checkpoint is retained until literal next growth')
 need(outer.count('machine,responses=B.bootstrap(')==1 and not proof['per_phase_BEFORE_machine_seed']and not proof['candidate_AFTER_machine_seed'],'One true bootstrap BEFORE input and persistent carry only')
 need(pin(H/'exact_equal.py').read_bytes().replace(b'\r\n',b'\n')==pin(R/'tools/m4-container-review/exact_equal.py','7d7c7fddfe2c051a02bddf7230e2fc5a73f4e0a972aa227c8310de1d7f3c6b97').read_bytes(),'Only CRLF serialization differs; every equality source byte is retained')
 eq=load('unchanged_complete_equality120',pin(H/'exact_equal.py','cc048da31a6624cef4292c20d801b3ec39450208f6ba3df67fb222f3c63a4925')).selfcheck();need(eq==dict(equal_cases=4,difference_refusals=6),'Complete length and byte equality unchanged')
 PE=load('literal_growth_physical_PE',pin(R/'tools/analysis/pe.py'));crt=PE.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes());rows=json.loads(pin(R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json').read_bytes());ins={q['pc']:q for q in rows['instructions']}
 pcs=(0x78004a3c,0x78004a42,0x78004a47,0x78004a4e,0x78004a54,0x78004a56,0x78004a58,0x78004a5b,0x78004a5d,0x7801e27b,0x7801e27c,0x7801e281,0x7801e284,0x7801e285,0x7801e28b,0x7801e290,0x7801e293,0x7801e295,0x7801e29e,0x7801e2a4,0x7801e2aa,0x7801e2af,0x7801e2b2,0x7801e2b5,0x7801e2bb)
 for pc in pcs:
  q=ins[pc];need(crt.read(crt.rva_range(pc-crt.image_base,q['width'])[0],q['width'])==bytes.fromhex(q['bytes_hex']),'Every exact literal growth/size return instruction')
 need(ins[0x78004a42]['operands']==ins[0x7801e27c]['operands']=='0x7800151d'and ins[0x78004a5d]['operands']=='0x7801e27b'and ins[0x7801e28b]['operands']=='0x780019f1','Ordinary and realloc-side genuine msize calls physically distinct')
 c=proof['provider_counts'];seq=proof['provider_sequences'];need(len(seq)==12 and {(q['level'],q['sequence'])for q in seq}=={(l,s)for l in('O0','O2')for s in range(6)},'All actual independent sequences')
 need(c['complete120_provider_sequences']==12 and c['selected_registration_closures']==1104 and c['actual_source_frees']==840 and c['actual_MFC_allocations']==600 and c['actual_duplicate_allocations']==228 and c['actual_heap_destroys']==c['actual_post_HeapDestroy_identity_proofs']==12,'Exact full source allocation/registration/release extent')
 need(c['whole_State_checkpoints']==c['whole_CPU_checkpoints']==c['whole_FX_checkpoints']and c['whole_State_checkpoints']>21996 and c['whole_checkpoint_pages']>1857552,'Every new complete source checkpoint and page retained')
 need(all(q['selected_used_bytes']==368 and q['selected_cached_capacity']in(0,q['first_replay_msize_capacity'])and q['first_replay_msize_capacity']>=368 and q['first_replay_msize_capacity']%4==0 and q['predicted_growth_replays']==q['actual_growth_replays']==(q['first_replay_msize_capacity']-368)//4+1 and q['first_replay_msize_queries']in(1,2)and q['all_resources_released']and q['actual_post_HeapDestroy_identity']for q in seq),'Every sequence independent size/alias geometry predicts actual next growth and same-owner cleanup')
 need(c['independent_vtable_calls']==216 and c['complete_vtable_dump_sets']==36 and c['actual_normal_null_frees']==60 and c['actual_borrowed_constructors']==36,'All six literal indirect calls at selected/grown/cleaned stages plus inherited units retained')
 events=pin(H/'vtable_model.py').read_text();need("self.o.check(m,f'vtable-call-{w[1]}-entered')"in events and "self.o.check(m,f'vtable-call-{w[1]}-returned')"in events and 'publication_index=found[0]'in events and 'self.vptr[5]if virtual else 0'in events,'Six before-derived actual CALL/RET checkpoints and fixed-vs-virtual source publication distinction')
 need("not any(r[0]in range(0x59ff88,0x59ffa1)for r in m.accesses)"in events,'Nonzero copy branch absent complete selected source accesses')
 pin(__file__);report=dict(passed=True,provider=str(proof_path),provider_sha256=proof_sha,complete_provider_sequences=12,whole_machine_checkpoints=c['whole_State_checkpoints'],whole_checkpoint_pages=c['whole_checkpoint_pages'],actual_first_replay_msize_queries=c['actual_first_replay_msize_queries'],actual_growth_replays=c['genuine_growth_replays'],first_replay_geometry=seq,literal_growth_instructions_reviewed=len(pcs),complete_equality_cases=eq,equality_physical_change_only_CRLF=True,whole_indirect_stage_relations=216,per_phase_BEFORE_machine_seed=False,candidate_AFTER_machine_seed=False,API_response_injection=False,initializer_credit=False,files=pins,physical_closure=verify_manifest(pins),scope='Independent complete120 provider lifecycle/checkpoint proof review from one true bootstrap BEFORE, literal source instructions and bounded actual API observations. Whole frames and owned bytes are retained; old finite10 numerical oracle scope unchanged. No nonzero helper pointee, handler/unwind or entire original provider volatile/stack equivalence claim.')
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
