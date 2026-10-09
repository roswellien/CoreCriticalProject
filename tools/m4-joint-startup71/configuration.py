"""Freeze the measured family gates after the final independent audits pass."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(controls,snapshot,audit,causality,name):
 gates={}
 def add(label,path,equal=None,expected=None):
  p=ROOT/path;r=json.loads(p.read_bytes());assert r['passed'];h=sha(p);assert expected is None or h==expected
  for field,value in (equal or{}).items():
   actual=r
   for k in field.split('.'):actual=actual[k]
   assert actual==value,(label,field,actual,value)
  gates[label]=dict(path=str(p.relative_to(ROOT)).replace('\\','/'),sha256=h,equal=equal or{})
 add('parent','reports/m4-joint-startup54-root/acceptance-r1/report.json',{'connected_roots':54},'5a7feb121fd1a8fc95d4e31da18af67099e91012b3f70e36e17575973b4cd89c')
 add('original','reports/m4-strings-source/original-run-r3/report.json',{'phases':426,'record_bytes':266880,'per_phase_reseed':False},'aa9cbb6c64151d4b81e7b7b8acabd321638bc171d5650b46e8c99d112f6b33d5')
 add('original_constructors','reports/m4-strings-source/original-game-source-r2/report.json',{'counts.constructor_prefixes':258,'counts.original_string_byteflows':96,'counts.whole_nonstack_page_checks':7998,'AFTER_machine_seed':False},'e53b80c8b2e58404c9605e20cb8a6b63b85178a6beb35c4e308c97490ba455d0')
 add('native','reports/m4-joint-startup71-root/execution-r1/report.json',{'native_executed':True,'whole_M4_complete':False},'5750a8dad9611381ba540cbad8c7534472e8c16d32c4f425d3fd6814c48844fa')
 add('source','reports/m4-strings-source/connected-native-source-r1/report.json',{'counts.persistent_phases':852,'counts.persistent71_sequences':12,'counts.whole_page_BEFORE':27264,'counts.whole_page_AFTER':27264,'candidate_AFTER_machine_seed':False},'55bebe771e5da315a4556b55ba0845260d388a3438dc9d83f53a21fc19df1496')
 add('paired','reports/m4-strings-source/paired-initialization-scope-r2/report.json',{'counts.paired_phases':852,'counts.source_string_owner_relations':192,'counts.null_descriptor_relations':12,'counts.whole_nonstack_page_relations':52824,'blanket_page_mask':False,'comparison_algorithm_changed':False},'71de3aa5ee90dcbf93737e9463443e604a5a10c0af1a4be834c5eeae562f3bfc')
 add('paired_review','reports/m4-joint-startup71-root/paired-review-r1/report.json',{'counts.raw_FX_pairs_with_only_capability_differences':1704,'counts.raw_whole_page_difference_scopes':52824},'2abf256c75c6af64111c716bb9d7dbc916d902a20c24da7ebbbbcfef832df9d7')
 add('source_fields','reports/m4-strings-source/paired-field-identity-r1/report.json',expected='95d8fd296ca323c7fb16d89a4d257efbd3bced836ee6ba44d712808d15c85b01')
 add('provider','reports/m4-strings-review/provider-acceptance-r2/report.json',{'counts.complete71_provider_sequences':12,'counts.whole_State_checkpoints':8688,'counts.whole_CPU_checkpoints':8688,'counts.whole_FX_checkpoints':8688,'counts.whole_checkpoint_pages':442008,'counts.actual_duplicate_allocations':192,'counts.actual_source_frees':204,'counts.successful_actual_growth':48,'counts.actual_heap_destroys':12,'worker_post_HeapDestroy_identity_observed':True,'whole_pages_masked':False},'b2573dc26574b7efd0c56d3f071cdf84269d01dfe795e8f97d915efa30f68c1c')
 add('controls',controls,{'metrics.actual_attempts':56,'metrics.ordinary_sequences':2,'metrics.causal_faults':26,'metrics.retry_refusals':28,'metrics.rich_hardware_pairs':56,'metrics.partial_transfer_faults':2,'metrics.normal_duplicate_source_frees':32,'API_response_injection':False},'80031604b0af92783eb12cce2e401d2188fe08b660c5e142303f1bb4380c3a92')
 add('control_snapshot',snapshot,expected='d895dcf4509b6f3fe5f0dadd5028a5d7ef0a03a53a4937309962a09c51932f15')
 add('control_audit',audit,{'counts.actual_control_cases':28,'counts.corrected_exact_IAT_guard_refusals':2,'counts.strict_outside_hardware_pairs':56,'counts.physical_HeapDestroy_identity_triplets':28},'65a2b1a0d46503259bd93f1662a0a13f0c8f32de5f39f572527068d62fa640bc')
 add('control_causality',causality,{'all_intended_controls_reached':True,'full_state_seeded_from_AFTER':False,'source_copy_prefix_derived_from_BEFORE':True},'097aa5f5525b1c4150f721ebcfbe097a872f2faf811aa51d428a07a7adb60574')
 add('continuity','reports/m4-joint-startup71-root/integration-audit-r1/report.json',{'counts.complete_State_and_projection_checks':1704,'counts.registry_carries':840,'counts.selected_host_returns':12,'counts.growth_cleanup_host_returns':12},'e6b03ddacfccf90efafe6e6755d9bb797c7bcb79c9b9d24f42ed29adf3964994')
 add('interface','reports/m4-strings-review/interface-r2/report.json',{'new_original_instructions':117,'new_literal_bytes':312,'family_roots':17,'actual_nonnull_string_inputs':16,'null_constructor_paths':1},'f5497ee4fb82d55e9d8ec903eecfe536e257ebcc7029dc27b33058be5700df74')
 add('provider_symbols','reports/m4-strings-native/symbol-attribution-r1/report.json',{'body_count':3,'physical_COFF_count':6})
 add('game_symbols','reports/m4-strings-source/symbol-attribution-r1/report.json',{'body_count':39,'physical_COFF_count':78,'sealed_sources_modified':False},'af1ce72980f8a7d77d1445b9b0d0b41601afe84f80125104a7eb0bfa29c11b1d')
 add('game_callbacks','reports/m4-strings-source/game-callbacks-r1/report.json',{'bodies':39,'unique_sites':16},'ed9975573be6803854775877eb94679d78651822e96e7aa42e982552b82e96db')
 add('calibration','reports/m4-strings-review/model-calibration-r1/report.json',{'computed_strlen_runs':264,'computed_strcpy_runs':264,'AFTER_machine_seed':False,'host_strlen_strcpy_used':False},'845b9d01b81c26b04731dc3cf7f10bd3ad31739485ec7eab072eb42eedcd4385')
 add('source_correction','reports/m4-strings-source/recovery-r7/report.json',expected='972ec961d7617d2e7b789d23ab1ce82da0c33424b37c12e2dc94c23d1e154341')
 add('ghidra','reports/m4-strings-ghidra/export-r1/report.json',{'static_only':True,'native_executed':False,'initializer_credit':False},'7ae5e4341ded0c520aa9ae95bb2b67c895995a1aad7113ae69495d5a2220f399')
 value=dict(gates=gates,extent=dict(selected_roots=71,new_roots=17,original_sequences=6,original_phases=426,native_sequences=12,native_phases=852,string_calls_per_sequence=16,ordered_callbacks_per_sequence=43,observed_source_pages=32),bounded_scope=dict(new_FSQRT='Inherited accepted zero-vector constructor only',callback_execution=False,full_CRT_attach=False,native_menu=False,native_Training=False,whole_game_alias_liveness=False,whole_original_provider_stack_equality=False,per_phase_machine_reseed=False,candidate_AFTER_machine_seed=False,host_libc_string_replacement=False),configuration_source=str(Path(__file__).resolve()),configuration_source_sha256=sha(__file__))
 out=ROOT/'reports/m4-joint-startup71-root'/name;assert not out.exists();out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(dict(configuration=str(out),sha256=sha(out),gates=len(gates))))
if __name__=='__main__':main(*sys.argv[1:])
