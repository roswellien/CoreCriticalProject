"""Compact positive-whitelist map of immutable completed116 source gates."""
from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];B=R/'reports/m4-container-source'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(paired,owned,name):
 out=B/name
 if out.exists():raise ValueError('Fresh additive source receipt seal')
 roles={'original_prepare':'original-preparation-r2','original_build':'original-build-r2','original_execution':'original-execution-r1','original_validation':'original-validation-r1','original_source':'original-game-source-r6','original_FS':'original-FS-observations-r2','native_source':'connected-native-source-r4','paired_FS':'paired-FS-normal-policy-r1','paired':paired,'paired_owned':owned};result={};pins={}
 for role,folder in roles.items():
  p=B/folder/('build.json'if role=='original_build'else 'report.json');r=json.loads(p.read_bytes())
  if not r['passed']:raise ValueError('Only completed positive gates '+role)
  result[role]=dict(path=p.relative_to(R).as_posix(),sha256=sha(p),counts=r.get('counts',{}));pins[str(p.resolve())]=sha(p)
 expected={'original_source':{'constructor_prefixes':528,'original_string_byteflows':114,'true_API_EDX_scalar_positive_source_carries':414,'NULLfree_source_CPU_FX_ENV_frame_snapshots':60,'new_vector_source_allocations':30,'whole_vector_owner_cleanup_joins':30},'original_FS':{'actual_FS_events':342,'full_CPU_MOV_relations':342,'whole_FX_ENV_relations':342,'actual12B_snapshot_relations':264,'installed_records':114,'restored_records':114},'native_source':{'persistent_phases':1392,'whole_page_BEFORE':51504,'whole_page_AFTER':51504,'native_FS_source_accesses':504,'actual_native12B_source_relations':336,'persistent116_sequences':12},'paired_FS':{'paired_normal_game_frames':168,'whole12B_paired_game_record_relations':336},'paired':{'paired_phases':1392,'whole_nonstack_page_relations':97440,'separate_whole_loader_page_input_relations':2784,'exact_observer_span_relations':8352,'new_vector_typed_field_activations':204,'source_string_owner_relations':228,'paired116_sequences':12},'paired_owned':{'complete_new_paired_owner_relations':96,'whole_new_native_owner_endpoint_relations':288,'exact_vector_endpoint_commits':204,'exact_borrowed_DWORD_CALL_RET_relations':36,'full_true_NULLfree_typed_relations':60,'paired_new_owner_sequences':12}}
 for role,counts in expected.items():
  for key,value in counts.items():
   if result[role]['counts'].get(key)!=value:raise ValueError('Positive whitelist counter '+str((role,key,value,result[role]['counts'].get(key))))
 out.mkdir(parents=True);pins[str(Path(__file__).resolve())]=sha(__file__)
 r=dict(passed=True,scope='Compact map only of completed immutable116 original, native, paired, normal-FS and typed new-owner evidence; final root admission and independent provider/control audits remain separate.',roles=result,positive_counter_whitelist=expected,parent_accepted109_sha256='697765f750209d9bee79541b973494dca89692f4ec630057d282cbbb450266e0',candidate_table_roots=116,original116_sequences=6,native116_sequences=12,original_prefix_complete_BEFORE_per_constructor=True,native_machine_bootstrap_only=True,per_phase_native_machine_reseed=False,AFTER_machine_seed=False,own_process_loaded_page_preserved=True,loader_page_ordinary_mask=False,private_heap_padding_crossbranch_equal=False,real32_API_volatile_crossbranch_equal=False,finite_true_HeapAlloc_EDX_scalar_carry=True,borrowed_pointee_mapped=False,borrowed_pointee_read=False,handler_or_exception_dispatch=False,unwind_or_cold_TLS=False,nonempty_old_vector=False,allocator_null=False,callback_execution=False,whole_M4_complete=False,initializer_credit=0,files=pins);(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),roles=result)))
if __name__=='__main__':main(*sys.argv[1:])
