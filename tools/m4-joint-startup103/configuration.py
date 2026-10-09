"""Freeze exact measured gate hashes for the additive103 acceptance."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(final_controls):
 controls=json.loads(Path(final_controls).read_bytes());gates={}
 def add(label,path,equal=None,digest=None):
  p=(ROOT/path).resolve();r=json.loads(p.read_bytes());assert r['passed'];h=sha(p);assert digest is None or digest==h
  for field,value in(equal or{}).items():
   actual=r
   for key in field.split('.'):actual=actual[key]
   assert actual==value,(label,field,actual,value)
  gates[label]=dict(path=p.relative_to(ROOT).as_posix(),sha256=h,equal=equal or{})
 add('parent','reports/m4-joint-startup71-root/acceptance-r1/report.json',{'connected_roots':71},'64c010e01930d4f84d7df9cb8cd932669ce25b6f3f1dc21989f197282025fdfc')
 add('preflight','reports/m4-joint-startup103-root/preflight-r1/report.json',{'passed':True},'c70acd86bd7be0536895512617605dad5c65a8a5d2f2a684d247138f30c8326c')
 add('original','reports/m4-mfc-source/original-run-r3/report.json',{'phases':618,'record_bytes':291456,'per_phase_reseed':False},'a50819520282272712899cb64faedd8d568c08a22d6d25e65fbc18358571faa0')
 add('original_constructors','reports/m4-mfc-source/original-game-source-r1/report.json',{'counts.constructor_prefixes':450,'counts.actual_MFC_source_owned_byteflows':210,'counts.whole_nonstack_page_checks':15300,'AFTER_machine_seed':False,'actual_MFC_malloc_calls':210},'0759e9c4f7423a8695bc4feb993998734c3c4e2dcea16d079f2e6a84feb6a958')
 add('native','reports/m4-joint-startup103-root/execution-r1/report.json',{'native_executed':True,'whole_M4_complete':False},'0bcd1aa560347cb57bac4346e12ad47e67964beb3ded9ff13eb478a7bd8f9a53')
 add('source','reports/m4-mfc-source/connected-native-source-r1/report.json',{'counts.persistent_phases':1236,'counts.persistent103_sequences':12,'counts.whole_page_BEFORE':43260,'counts.whole_page_AFTER':43260,'per_phase_BEFORE_machine_seed':False,'candidate_AFTER_machine_seed':False},'7f8af81d8f7bfdde801f44fb17387abbbe66fecaf18452e60972f349b7c77473')
 add('paired','reports/m4-mfc-source/paired-initialization-policy-r2/report.json',{'counts.paired_phases':1236,'counts.whole_nonstack_page_relations':84048,'counts.source_MFC_owner_relations':420,'counts.source_MFC_one_past_end_relations':48,'counts.new_header_branch_derivations':864,'MFC_import_relation_slots':511,'blanket_page_mask':False,'original_and_native_bytes_modified':False},'3e6c9d9b887bb7864f42ea1468b6f7eda181494fcd44d8a4b0464e2418ad1207')
 add('paired_scope','reports/m4-mfc-source/paired-scope-r1/report.json',{'metadata_correction_only':True,'comparisons_rerun':False,'comparison_algorithm_changed':False,'callback_execution_claimed':False,'whole_game_header_liveness_proven':False,'SPI_metadata_AFTER_phases':[51,52,53,54,55,56,57],'SPI_metadata_BEFORE_phases':[52,53,54,55,56,57,58]},'054727e9b47e64ffc7878036ccde0859b15cc861333a6886cccf9006f7ef3723')
 add('paired_review','reports/m4-joint-startup103-root/paired-review-r1/report.json',{'counts.retained_own_branch_saved_byte_proofs':864,'counts.raw_FX_pairs_with_only_capability_differences':2472,'counts.raw_whole_page_difference_scopes':84048,'blanket_page_mask':False},'c6f5d83eacee89add5cd64cb6de141479f93d0955aeb1c1e9a1e146b9f5eaec3')
 add('fields','reports/m4-mfc-source/field-contracts-r1/report.json',{'primary_allocation_fields':35,'one_past_end_fields':4,'header_count':36,'AFTER_machine_seed':False},'63cd8d2665580dc397745d0f34769dac321089fa2ec422eeea7681b08e3a1a55')
 add('provider','reports/m4-mfc-review/provider-source-r1/report.json',{'provider_counts.complete103_provider_sequences':12,'provider_counts.whole_State_checkpoints':17652,'provider_counts.whole_CPU_checkpoints':17652,'provider_counts.whole_FX_checkpoints':17652,'provider_counts.whole_checkpoint_pages':1274988,'provider_counts.actual_MFC_allocations':420,'provider_counts.actual_source_frees':624,'provider_counts.successful_actual_growth':144,'provider_counts.actual_post_HeapDestroy_identity_proofs':12,'worker_post_HeapDestroy_identity_observed':True},'a66c45c77fd8ee58859bc1104a16b9c6ad20efe92f913a55971e05f72fa51b46')
 add('provider_seal','reports/m4-mfc-review/provider-seal-r1/report.json',{'persistent_game_phases':1236,'full_source_state_checkpoints':17652,'API_response_injection':False,'handler_TLS_or_actual_allocation_null_paths_admitted':False,'callback_execution':False},'d3f0f269bbce2a5eff848c4df3c2cbbcb5b7685ee2dfabb8edb5e0a930aa0bbd')
 for label in('controls','control_snapshot','control_audit','control_dependency'):
  item=controls[label];assert item['equal'];add(label,item['path'],item['equal'],item['sha256'])
 add('control_execution','reports/m4-mfc-review/controls-execution-r2/report.json',{'native_executed':True,'source_bodies_modified':False,'API_response_injection':False},'61602e0a989e262300dadf1e102fbc44ce21166719cb3e769e8e6bddd3fea009')
 add('control_link','reports/m4-joint-startup103-root/control-link-r3/report.json',{'declared_source_inputs':592,'actual_literal_COFF_links':590,'retained_unlinked_archives':2,'compiled_fixture_registry_checks':6,'metadata_correction_only':True,'workers_rebuilt':False},'11df2f0f9e49dda3e7e410fc251e6f41987a60213441a34fcc15ffcb0fbfe5e3')
 add('control_plan','reports/m4-mfc-review/control-plan-r2/report.json',{'planned_distinct_cases':21,'planned_actual_attempts':84,'native_executed':False},'d8fa671bd63e205da9f4ba8b45a0aa85b585b5efe6b666db0f82794898946025')
 add('continuity','reports/m4-joint-startup103-root/integration-audit-r1/report.json',{'counts.complete_State_and_projection_checks':2472,'counts.registry_carries':1224,'counts.selected_host_returns':12,'counts.growth_cleanup_host_returns':12},'4950803abceb1891e988a5e1e465c059994851133b3fd8d45cf81c72d01e56a5')
 add('interface','reports/m4-mfc-review/interface-r1/report.json',{'new_original_instructions':23,'new_literal_bytes':53,'family_roots':32,'null_allocator_failure_path_admitted':False,'handler_TLS_path_admitted':False},'f9ac44cdc91b751974f965830bd9bda0412801339e1392bf95834ec4bc36161d')
 add('game_static','reports/m4-mfc-review/game-static-r1/report.json',{'physical_literal_rows':547,'new_game_bodies':65,'per_root_static_allocation_sites':35,'native_executed':False},'248996818bda699505f754ad26f389ff1dfd2269b19cd5ba66303ae40d035e73')
 add('provider_symbols','reports/m4-mfc-native/symbol-attribution-r1/report.json',{'body_count':2,'physical_COFF_count':4,'sealed_original_lifts_modified':False},'9c0533366c101555011a098eaf4846d2ca3443bf9f9ba76912a12fb17c4d46c0')
 add('game_symbols','reports/m4-mfc-source/symbol-attribution-r2/report.json',{'body_count':65,'physical_COFF_count':130},'1a6cdb1e870c2f173a43730c0ca98acf8fe0635bbbc2e5b72baf1c9e6a111cb8')
 add('game_callbacks','reports/m4-mfc-source/game-callbacks-r1/report.json',{'bodies':65,'unique_sites':3},'22ab5428e1340697d884db0711aafb51a6f736af9032e8b6a5fe2bf68d2fa94a')
 add('calibration','reports/m4-mfc-review/prefix-calibration-r1/report.json',{'computed_allocator_prefixes':32,'computed_free_prefixes':16,'complete_source_callframe_checks':48,'actual_API_executed':False,'AFTER_machine_seed':False},'38cd8bdd2dde0fb3df8c23ccbd38d1f40b77d6e533d2b269bcd01fc383a40aa9')
 add('source_recovery','reports/m4-mfc-source/recovery-r4/report.json',digest='b50217399d254eddc620ab39bf8d934fd2cc30233e575356a9d8c40761c33e0f')
 add('allocation_geometry','reports/m4-mfc-source/allocation-contracts-r4/report.json',digest='30ef9954b16ba185294871d5cb419df502b656aab7f12fc521a4e3b09fe156f2')
 add('loader','reports/m4-mfc-source/loader-identity-r1/report.json',{'original_loader_executed':True,'MFC_DllMain_initialization_executed':True,'allocator_source_called':False},'7925f659144954487b1b13d781d4aee48aa0b8d20887ce9ee8aa40ce7a12b09b')
 add('ghidra','reports/m4-mfc-ghidra/export-r1/report.json',digest='df20391c774cfcb55b9c2b49255a80374796c23fdf491270bcfb7655fd46e4a3')
 add('provider_lifts','reports/m4-mfc-native/lifts-r1/report.json',digest='3c49ba0a564416ec1c3eb1b3c656f82381947cfd47cabc8a076209246eecf73d')
 add('game_lifts','reports/m4-mfc-source/lifts-r1/report.json',digest='2b1c617c612cc35ccbf76ed644d023752f3ba946d124bfe62a43f6a643c55f9f')
 add('native_preparation','reports/m4-mfc-native/preparation-r1/report.json',digest='3a2a6a2b43c4cc38c305e8f6965e4a56254f9677415c67cbb40091919072817e')
 add('build','reports/m4-joint-startup103/build-r1/build.json',digest='75e233397c59e42ac11f86eef7195181c17d9c02aae4f5cf16fd4566585e4531')
 result=dict(gates=gates,extent=dict(selected_roots=103,new_roots=32,original_sequences=6,original_phases=618,native_sequences=12,native_phases=1236,MFC_allocations_per_sequence=35,string_allocations_per_sequence=16,live_ordinary_owners_per_sequence=52,ordered_callbacks_per_sequence=75,observed_source_pages=35,declared_source_inputs_per_level=296,linked_literal_COFFs_per_level=295,retained_unlinked_archives_per_level=1),bounded_scope=dict(new_FSQRT='Inherited accepted zero-vector constructor only',callback_execution=False,full_CRT_attach=False,full_native_MFC_attach=False,native_menu=False,native_Training=False,whole_game_alias_liveness=False,whole_original_provider_stack_equality=False,per_phase_machine_reseed=False,candidate_AFTER_machine_seed=False,host_libc_string_replacement=False,malloc_NULL_or_handler_TLS_execution=False,source_owned_header_and_pointer_relations=True),configuration_source=str(Path(__file__).resolve()),configuration_source_sha256=sha(__file__),control_specification=str(Path(final_controls).resolve()),control_specification_sha256=sha(final_controls))
 out=ROOT/'reports/m4-joint-startup103-root/configuration-r1.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(configuration=str(out),sha256=sha(out),gates=len(gates))))
if __name__=='__main__':main(sys.argv[1])
