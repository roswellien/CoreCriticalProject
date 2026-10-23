"""UNEXECUTED bounded reuse join. No raw/SQLite/DLL/source evaluator rerun.

ROOT independently reviews the checker4 source policy first. Existing exact
executed semantic, independent witness, owner and actual linked proofs remain
separate from future terminal raw integrity and durable-inventory expansion.
"""
from pathlib import Path
import collections,hashlib,json,re,sys
R=Path(__file__).resolve().parents[2]
EXECUTION='43d8a2a8e56e6d6a0286236685b16fc6e36b806ebcc8fc6199d49c95e69e0863'
SEMANTICS='88e0a18bc8b32fb70c3fd460c828c44127613662fd4467cf3385ae78b56861cb'
PREPARATION='f413ea66cb259ecebf8bf76024113a0410fe5883304fa10af9a442b291c1b07e'
BUILD='e064098f58982c7c6115e43f0ebf14a39eb1ae68f4162225c48c10c70b2f1bf6'
SOURCES={
 'causes':('reports/m4-joint-startup138/context-controls-verification-r1/actual-Context-causes.json','05aa8414254e6605d57f8c8cdd23dbead21980415fd5db2e7a3799172759082b'),
 'witnesses':('reports/m4-138-controls-review/raw-witnesses-r1/report.json','e6d81728fe07075576e1b3d9cbde174f1829bcf008de0989d51573d3f1b074c0'),
 'GDI_owners':('reports/m4-138-controls-review/gdi-owners-r1/report.json','31f295d7128be8c0cef31bd8c9358f74055b8d3d736476881a858fde51f58c15'),
 'equivalence':('reports/m4-138-controls-review/equivalence-r1/report.json','e46f3f2a8ad63ac3ed6f229cfbcbaecc2238a42758d0195b0684a97a53c4f0cf'),
 'actual_link_join':('reports/m4-138-controls-review/current-link-join-r1/report.json','a1f3aa8e0203af187b2d8cdbcc315792c0eb330c40c9ec67ebf2f1ade0d4e87f')}
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(admission,admission_sha,name):
 ap=Path(admission).resolve();need(sha(ap)==admission_sha,'Independent ROOT bounded-role admission');A=json.loads(ap.read_bytes());need(A['passed']is True and A['current16_source_policy_admitted']is True,'Actual scoped source-policy independent review, not author self-admission');files={}
 def read(p,h):
  p=Path(p).resolve();need(str(p)in A['files']and A['files'][str(p)]==h and p.stat().st_size<32*1024*1024 and p.suffix.lower()not in('.mwb','.mwi','.mwc','.zip'),'Only admitted bounded metadata, never giant/raw/DB/canonical inputs');need(sha(p)==h,'Whole exact existing metadata input');files[str(p)]=h;return json.loads(p.read_bytes())
 need(A['files'][str(Path(__file__).resolve())]==sha(__file__),'Exact current role adapter reviewed');files[str(Path(__file__).resolve())]=sha(__file__)
 # This is only a bounded projection of exact already executed checker4.
 # ROOT authenticates it against full88e0 receipt through completed raw proof;
 # this adapter never reads its huge map or predicts new source outcomes.
 H=A['executed_checker4_semantic_header'];need(A['executed_checker4_semantic_sha256']==SEMANTICS and H['passed']is True and H['execution_sha256']==EXECUTION and H['preparation_sha256']==PREPARATION,'Exact executed current16 source semantics, not unexecuted checker5')
 limits=('partial_fault_register_prediction','hidden_Runtime_frames_or_permissions_bytes_observed','whole_prior131_semantic_source_equivalence_claimed','source_callbacks_executed','source_bootstrap_or_teardown_modeled');need(all(H[k]is False for k in limits),'All genuine bounded scope exclusions retained')
 fp=A['current16_fullraw_report'];fh=A['current16_fullraw_sha256'];F=read(fp,fh);need(F['passed']is True and F['controls_verification_sha256']==SEMANTICS and F['all_bounded_readers_closed']is True and F['raw_export_readers_closed']is True and F['raw_exports_all_logical_entries']is True and F['proof_inventory']['sqlite_closed_before_hash']is True,'Future actual terminal required; no partial/running proof');need(F['counts']['whole_export_targets_authenticated']==10691866 and F['counts']['whole_exported_retry_files_equal']==3547696,'Separate measured raw/private retry domain')
 D={key:read(R/path,h)for key,(path,h)in SOURCES.items()};expected={(level,mode)for level in('O0','O2')for mode in range(1,9)}
 def keyed(rows):
  result={(r['level'],r['mode']):r for r in rows};need(len(result)==len(rows)==16 and set(result)==expected,'Exact all16 distinct actual modes, no success-only subset');return result
 C=keyed(D['causes']);W=keyed(D['witnesses']['cases']);G=keyed(D['GDI_owners']['cases']);keyed(F['cases']);need(all(D[k]['passed']is True for k in('witnesses','GDI_owners','equivalence','actual_link_join')),'Existing actual independent witnesses/owners/AST/link evidence')
 sums=collections.Counter()
 for key,case in C.items():
  witness=W[key];owner=G[key];proof=case['actual_GDI_identity'];need(proof==owner['proof'],'Entire source/manual physical owner proof independently agrees, not matching counts only');need(proof['passed']is True and proof['actual_source_calls']==149 and proof['actual_manual_calls']==15 and proof['whole_identity_sides']==328 and proof['whole_named_entry64_sides']==328,'All actual149source+15manual calls/both identity entry sides')
  calls=proof['calls'];need(len(calls)==164 and[c['serial']for c in calls]==list(range(164)),'Whole exact chronological source/manual call extent');need(all(c['call_words'][3]==int(i>=149)for i,c in enumerate(calls)),'Source calls remain distinct from manual native cleanup')
  need(proof['source_output_equivalence_claimed']is False and proof['font_lifetime_closure_claimed']is False and proof['origin_forwarder_chain_verified']is False,'Owner helper scope does not imply source/lifetime/forwarder semantics')
  words=case['actual_fault_context_words'];need(len(words)==13 and words[:5]==[1,1,1,135,0]and words[7]==135 and words[12]==1,'Actual same carried current Context failed/poisoned after135');need(case['actual_cause_words'][:4]==[1,key[1],135,0x5a3ff0],'Exact current authored fault identity');need(witness['source_rows']==len(case['actual_suffix_operands'])and witness['resource_rows']==15 and witness['full_current_Context_direct_retry']is True,'Independent causal operand/manual owned lifetime witnesses')
  sums.update(dict(cases=1,source_operand_rows=len(case['actual_suffix_operands']),source_GDI_calls=proof['actual_source_calls'],manual_owned_cleanup_calls=proof['actual_manual_calls'],whole_identity_sides=proof['whole_identity_sides'],whole_entry64_sides=proof['whole_named_entry64_sides']))
 need(sums['source_operand_rows']==D['witnesses']['counts']['exact_causal_source_operand_rows']==H['counts']['exact_causal_source_operand_prefix_rows']==966,'Actual source-derived finite operand prefix total');need(sums['source_GDI_calls']==H['counts']['actual_named_GDI_source_calls']==2384 and sums['manual_owned_cleanup_calls']==D['witnesses']['counts']['actual_owned_DeleteObject_rows']==H['counts']['actual_owned_font_cleanup_calls']==240 and sums['whole_identity_sides']==H['counts']['whole_GDI_identity_sides']==5248,'Reproduce scoped actualsource/manual/owner counters')
 E=D['equivalence'];L=D['actual_link_join'];need(E['checker4_sha256']=='5a6b673cad65db1b0c64329c57f5525df0634d70f39165712707dee8151b006e'and E['historical_completed_report_binds_checker4']is True and E['checker5_execution_claimed']is False,'Actual executed checker identity separate from unchanged unexecuted performance derivative');need(L['controls_execution_sha256']==EXECUTION and L['controls_prelaunch_sha256']=='55990e0cff619c9ee69f2e5e81e27d9e6e92bd4da8d0b5557e4eb28879a10b3a'and L['current_native3_admitted_full_link_join']is True and L['whole_Context_inverse_restores_positive']is True,'Actual current linked positive/control source identity, not historical820-only claim')
 need(A['manual_cleanup_finite_policy_reviewed']is True and A['final_named_owner_entry64_scope_reviewed']is True,'ROOT explicitly reviews finite owned native cleanup and final-owner scope; no source callback/whole wrapper claim')
 files[str(ap)]=admission_sha;need(re.fullmatch('[A-Za-z0-9_-]{1,90}',name),'Simple namespace');out=R/'reports/m4-controls-terminal-composite'/name;need(not out.exists(),'Fresh outputs');out.mkdir()
 semantic=dict(passed=True,current16_fullraw_sha256=fh,execution_sha256=EXECUTION,preparation_sha256=PREPARATION,build_sha256=BUILD,executed_semantic_sha256=SEMANTICS,all16_distinct_modes_reviewed=True,finite_GDI_owner_manual_cleanup_lifetime_predicates_reviewed=True,finite_controls_predicate_scope='Own-input fault mutations, exact reached operand location/width/direction and read payloads, observed committed witness-write byteflow, denied mode5/7 writes uncommitted, observed private retry, final named owner entry64 and fifteen owned generations manually cleaned by native DeleteObject. Committed write values are not all independently instruction evaluated; full prior131/135positiveprefix and source callback cleanup remain separate',committed_source_write_values_independently_instruction_evaluated=False,committed_write_values_from_actual_source_witness=True,whole_fault_memory_fully_source_predicted=False,source_callbacks_executed=False,source_bootstrap_or_teardown_modeled=False,partial_fault_register_prediction=False,whole_hidden_Runtime_frames_or_permissions_claim=False,forwarder_origin_or_transitive_wrapper_body_claim=False,whole_current138_positive_semantic_equivalence_claim=False,counts=dict(sums),proof_inventory_expansion_still_required=True,raw_integrity_is_semantic_equivalence=False,files=files)
 scope=dict(passed=True,execution_sha256=EXECUTION,preparation_sha256=PREPARATION,build_sha256=BUILD,executed_semantic_sha256=SEMANTICS,ROOT_source_policy_admission_sha256=admission_sha,observation_limits=dict(old_registry_private_vectors_retry_claim=False,full_memory_permission_snapshot_claim=False,whole_hidden_Runtime_frames_or_permissions_claim=False),source_callbacks_executed=False,manual_native_owned_cleanup_only=True,final_named_owner_entry64_only=True,committed_source_write_values_independently_instruction_evaluated=False,committed_write_values_from_actual_source_witness=True,whole_fault_memory_fully_source_predicted=False,files=files)
 for leaf,value in(('current16-semantic-review.json',semantic),('current8-scope-review.json',scope)):(out/leaf).write_text(json.dumps(value,indent=2)+'\n')
if __name__=='__main__':main(*sys.argv[1:])
