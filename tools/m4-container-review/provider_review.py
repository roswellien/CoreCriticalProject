"""Authenticate persistent116 observer derivation and literal growth query scope."""
from pathlib import Path
import difflib,hashlib,importlib.util,json,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/m4-pipeline'))
from manifests import verify_manifest
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def main(name):
 out=R/'reports/m4-container-review'/name;need(not out.exists(),'Fresh provider review');out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Exact physical input '+str(p));pins[str(p)]=v;return p
 proof=json.loads(pin(R/'reports/m4-container-review/provider-source-r2/report.json','2d1d2b2b4270821a1ea345c0dcc50b7c1d129ee9d812b3e6a5f29ced4b58628c').read_bytes());need(proof['passed'],'Completed all actual provider sequences')
 prep=json.loads(pin(R/'reports/m4-container-review/preparation-r2/report.json','ea24d10040359ac4d1efb65208c87feab57863ed128c3973da646e22e3f7440a').read_bytes());need(prep['passed'],'Frozen additive derivation')
 for p,h in prep['files'].items():pin(p,h)
 outer=pin(Path(__file__).with_name('observe116_v2.py')).read_text();new=pin(Path(__file__).with_name('final_observer116_v2.py')).read_text();old=pin(Path(__file__).with_name('final_observer116.py')).read_text();original_outer=pin(Path(__file__).with_name('observe116.py')).read_text()
 need(outer==original_outer.replace('final_observer116 as V','final_observer116_v2 as V').replace("with_name('final_observer116.py')","with_name('final_observer116_v2.py')"),'Outer source carry changed only reviewed module binding and physical pin')
 old_finish=old[old.index(' def finish('):old.index('\ndef configure(')];new_finish=new[new.index(' def finish('):new.index('\ndef configure(')]
 need(old[:old.index(' def finish(')]==new[:new.index(' def finish(')]and old[old.index('\ndef configure('):]==new[new.index('\ndef configure('):],'All source checkpoints, provider model, ownership and event hooks unchanged')
 firstline="queries=[f for f in responses.facts[first_API:responses.index]if f['name']=='HeapSize']"
 need(firstline in new_finish and "f['words'][16]==vector['native']and f['words'][22]==vector['begin']and f['words'][17]==first_query_capacity"in new_finish,'Both actual typed query facts bind one old source alias/full native owner/capacity')
 need("len(queries)==1 or len(responses.growth)==initial_growths+1"in new_finish and "capacity_steps=(first_query_capacity-initial_used)//4+1"in new_finish and "n==observed_replays==capacity_steps"in new_finish,'Additional query requires genuine literal growth; replay prediction derives from measured capacity and source DWORD append')
 need('m.invoke_external(0x410210,0xffffffa0,responses)'in new_finish and "self.check(m,f'registry-replay-{88+n}-before')"in new_finish and "self.check(m,f'registry-replay-{88+n}-after')"in new_finish,'Every additional source replay retains complete before/after checkpoint proof')
 need("not vector['capacity']or vector['capacity']==first_query_capacity"in new_finish,'Cached capacity is corroboration only, never an AFTER substitute')
 need(outer.count('machine,responses=B.bootstrap(')==1 and not proof['per_phase_BEFORE_machine_seed']and not proof['candidate_AFTER_machine_seed'],'One true bootstrap BEFORE with persistent source carry')
 need("before['memory'][page]=physical"in outer and "Declared native complete raw physical MFC data BEFORE input"in outer,'Named whole raw MFC data input admitted explicitly')
 exact=load('full_equality116',pin(Path(__file__).with_name('exact_equal.py'),'7d7c7fddfe2c051a02bddf7230e2fc5a73f4e0a972aa227c8310de1d7f3c6b97'));eq=exact.selfcheck();need(eq==dict(equal_cases=4,difference_refusals=6),'Complete length and byte equality unchanged')
 pe=load('independent_growth_PE',pin(R/'tools/analysis/pe.py'));crt=pe.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes());interface=json.loads(pin(R/'reports/m4-onexit-review/interface-r1/instruction-contracts.json').read_bytes());ins={q['pc']:q for q in interface['instructions']}
 reviewed=(0x78004a3c,0x78004a42,0x78004a47,0x78004a4e,0x78004a54,0x78004a56,0x78004a58,0x78004a5b,0x78004a5d,0x7801e27b,0x7801e27c,0x7801e281,0x7801e284,0x7801e285,0x7801e28b,0x7801e290,0x7801e293,0x7801e295,0x7801e29e,0x7801e2a4,0x7801e2aa,0x7801e2af,0x7801e2b2,0x7801e2b5,0x7801e2bb)
 for pc in reviewed:
  q=ins[pc];need(crt.read(crt.rva_range(pc-crt.image_base,q['width'])[0],q['width'])==bytes.fromhex(q['bytes_hex']),'Exact original growth/query literal instruction '+hex(pc))
 need(ins[0x78004a42]['operands']==ins[0x7801e27c]['operands']=='0x7800151d'and ins[0x78004a5d]['operands']=='0x7801e27b'and ins[0x7801e28b]['operands']=='0x780019f1','One onexit msize and second pre-realloc msize are separate genuine original source calls')
 seq=proof['provider_sequences'];c=proof['provider_counts'];need(len(seq)==12 and {(x['level'],x['sequence'])for x in seq}=={(l,s)for l in('O0','O2')for s in range(6)},'Every actual O0/O2 persistent source sequence')
 need(all(x['selected_used_bytes']==x['selected_cached_capacity']==x['first_replay_msize_capacity']==352 and x['first_replay_msize_queries']==2 and x['predicted_growth_replays']==x['actual_growth_replays']==1 and x['all_resources_released']and x['actual_post_HeapDestroy_identity']for x in seq),'All actual first replay facts predict one genuine additional growth and complete cleanup')
 need(c['complete116_provider_sequences']==12 and c['actual_first_replay_msize_queries']==24 and c['whole_State_checkpoints']==c['whole_CPU_checkpoints']==c['whole_FX_checkpoints']==21996 and c['whole_checkpoint_pages']==1857552,'Exact completed machine/page/query evidence')
 need(c['actual_normal_null_frees']==60 and c['actual_borrowed_constructors']==36 and c['source_unchanged_acquired_vector_extents']==60 and c['container_vector_stores']==612,'All new source units and complete unchanged acquired vector backing')
 delta=out/'query-derivation.diff';delta.write_text(''.join(difflib.unified_diff(old_finish.splitlines(True),new_finish.splitlines(True))));pin(delta);pin(__file__);pin(R/'tools/m4-pipeline/manifests.py');physical=verify_manifest(pins);need(physical['passed'],'Static physical closure')
 report=dict(passed=True,scope='Read-only authentication of exact source/observer derivation and completed persistent116 proof. Genuine first source onexit msize and growth-side msize query the same actual old owner; no expected values from candidate AFTER. Finite old10 numerical oracle scope remains unchanged.',complete_provider_sequences=12,whole_machine_checkpoints=21996,whole_checkpoint_pages=1857552,actual_first_replay_msize_queries=24,literal_growth_instructions_reviewed=len(reviewed),predicted_additional_growth_replays=12,source_unchanged_vector_backings=60,complete_equality_cases=eq,provider_model_changed=False,API_response_injection=False,per_phase_BEFORE_machine_seed=False,candidate_AFTER_machine_seed=False,whole_original_provider_stack_equality_claimed=False,handler_TLS_paths_admitted=False,initializer_credit=0,native_executed_by_reviewer=False,files=pins,physical_closure=physical)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(*sys.argv[1:])
