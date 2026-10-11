"""Measured exact124 acceptance predicates; unresolved gates cannot be frozen."""
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
ROWS={
 'parent':('m4-joint-startup120-root/acceptance-r1/report.json',dict(connected_roots=120,remaining_inventory_roots=24,whole_M4_complete=False)),
 'game_recovery':('m4-lockit-source/recovery-r1/report.json',dict(root_count=4,game_bodies=10,unique_instructions=303,unique_bytes=1048,registration_callbacks=4)),
 'game_lifts':('m4-lockit-source/lifts-r1/report.json',dict(root_count=4,new_guest_objects=20,State_bytes=3504,FX_bytes=512,CPU_bytes=40)),
 'game_symbols':('m4-lockit-source/symbol-attribution-r1/report.json',dict(body_count=10,physical_COFF_count=20,corrected_manifest_entries=10,source_COFF_recompiled=False,sealed_sources_modified=False)),
 'game_callbacks':('m4-lockit-source/game-callbacks-r1/report.json',dict(bodies=10,unique_sites=5)),
 'game_static':('m4-lockit-review/static-r1/report.json',{'counts.four_roots':4,'counts.game_entries':14,'counts.game_rows':303,'counts.game_bytes':1048,'counts.syntactic_MFC24_sites':6,'counts.syntactic_MFC20_sites':2,'counts.game_FS_sites':12,'counts.registration_callbacks':4}),
 'game_interface':('m4-lockit-review/source-interface-r2/report.json',{'counts.literal_scratch_CALL_frame_relations':8,'counts.complete_FS_frame_contracts':4}),
 'provider_recovery':('m4-lockit-source/provider-recovery-r1/report.json',dict(body_count=2,unique_instructions=17,unique_bytes=51,actual_postDllMain_state=2,state_seeded=False,cold_state0_admitted=False,contended_state1_admitted=False)),
 'provider_lifts':('m4-lockit-source/provider-lifts-r2/report.json',dict(new_guest_objects=4,State_bytes=3504,FX_bytes=512,CPU_bytes=40)),
 'provider_interface':('m4-lockit-source/provider-interface-r1/report.json',dict(body_count=2,physical_COFF_count=4,admitted_rows=17,admitted_bytes=51,physical_full_source_intervals_retained=True,cold_state0_admitted=False,contended_state1_admitted=False,actual_loaded_state=2)),
 'ghidra':('m4-lockit-source/ghidra-r1/report.json',{'runs.0.functions':10,'runs.0.decompiled':10,'runs.0.body_bytes_verified':525,'cold_imports':0,'provider_export':False,'static_only':True}),
 'original_preparation':('m4-lockit-original/original-preparation-r4/report.json',dict(record_bytes=356992,FS_hooks=45,Lockit_hooks=4,Lockit_snapshot_bytes=12988,Lockit_snapshots_per_reached_root=6,callbacks=96,per_phase_reseed=False,AFTER_machine_seed=False)),
 'original_build':('m4-lockit-original/original-build-r3/build.json',dict(record_bytes=356992,sequences=6,phases=744,pages=43,direct_primary=True)),
 'original_run':('m4-lockit-original/original-execution-r2/report.json',dict(original_executed=True,native_executed=False,per_phase_reseed=False)),
 'original_validation':('m4-lockit-original/original-validation-r2/report.json',{'record_bytes':356992,'observed_pages':43,'callbacks':96,'initialized_state':2,'state_seeded':False,'counts.phases':744,'counts.Lockit_snapshots':144,'counts.owners':48,'counts.owner_phase_relations':1860,'counts.actual_initial_allocations':48,'counts.new_FS_records':72,'counts.actual_API_frames':48,'counts.whole_provider_page_relations':2232}),
 'original_review':('m4-lockit-review/full-original-r1/report.json',{'counts.compiled_FS_functions':45,'counts.compiled_FS_bytes':16500,'counts.compiled_FS_relocations':2520,'counts.compiled_linked_Lockit_functions':6,'counts.compiled_linked_Lockit_bytes':1134,'counts.compiled_linked_Lockit_relocations':172,'counts.original_phases':744,'counts.actual_Lockit_CPU_FX_ENV_boundaries':144,'counts.actual_API_frame_relations':48,'counts.actual_new_owners':48,'counts.whole_owner_phase_carries':1860,'counts.actual_new_owner_cleanups':48,'original_postRET_CPU_captured':False}),
 'original_source':('m4-lockit-paired-provider/original-r2/report.json',{'counts.normal_original_FS_joins':72,'counts.actual_original_source_boundary_joins':144,'counts.bounded_original_API_volatile_boundaries':48,'counts.actual_original_initial_owner_inputs':48,'counts.whole_original_prefix_page_relations':1008,'counts.literal_original_new_root_prefixes':24,'counts.whole_original_owner_phase_carries':1860,'counts.whole_original_owner_cleanup_joins':48,'AFTER_machine_seed':False,'observed_original_postRET':False,'whole_original_provider_stack_equivalence':False}),
 'owner_source':('m4-lockit-source/owned-interface-r1/report.json',dict(owned_accesses=32,publications=8)),
 'owner_original':('m4-lockit-paired-provider/original-r2/report.json',{'source_owned_contracts':32,'source_publication_contracts':8,'counts.source_owned_contract_corroborations':192,'counts.source_publication_contract_corroborations':48}),
 'native_preparation':('m4-lockit-native/preparation-r5/report.json',dict(new_game_bodies=10,new_provider_bodies=2,observed_loaded_state=2,normal_new_allocations=8,normal_new_FS_records=4,new_FS_owned_accesses=32,new_FS_owned_publications=8,generic_MFC_publication_count_for_new_sites=0,guest_CS_semantic_outputs=24,guest_CS_native_opaque_copy=False,native_DllMain_executed=False,complete_FS_installation_guard_unchanged=True)),
 'preparation':('m4-joint-startup124/preparation-r5/report.json',dict(linked_literal_COFFs_per_level=363,added_literal_COFFs_per_level=12,canonical_capture_transport=True)),
 'build':('m4-joint-startup124/build-r4/build.json',dict(passed=True,guest_executed=False,full_dependency_acceptance_rehash_required=True,whole_M4_complete=False)),
 'abi':('m4-lockit-build-review/abi-r2/report.json',dict(packed_schema_identical_to_accepted120=True,unique_whole_pages=43,selected_roots=124,registrations=96)),
 'link':('m4-lockit-build-review/link-r2/report.json',dict(literal_COFF_links=726,compiled_objects=54,actual_linked_inputs=784)),
 'resource':('m4-lockit-build-review/resource-r2/report.json',dict(guest_CS_bytes=24,native_resource_bytes=40,guest_semantic_DWORD_offsets=[4,8,12],opaque_loaded_DWORD_offsets=[0,16,20],seeded_state2=False)),
 'native_integration':('m4-lockit-review/native-integration-r5/report.json',{'counts.whole_loaded_input_pages':2,'counts.actual_named_API_contracts':2,'counts.literal_CALL_scratch_contracts':8,'counts.exact_allocation_size_contracts':8,'counts.whole_literal_RX_spans':22,'counts.reviewed_resource_admission_invariants':6,'counts.physical_early_FS_variant_contracts':2,'counts.exact_physical_new_owner_stores':32,'counts.exact_physical_new_owner_publications':8}),
 'iteration':('m4-lockit-build-review/iteration-r1/report.json',dict(historical_archive_identities=165,historical_archive_bytes=116855698353,historical_payloads_opened=False,changed_code_and_PE_inputs_physically_hashed=True,current_worker_outputs_fully_validated_by_DirectSet=True,historical_identities_retained_in_dependency_union=True,full_final_dependency_rehash_required=True)),
 'lineage':('m4-joint-startup124-root/lineage-r2/report.json',dict(authenticated_preparation_edges=4,authenticated_native_generations=3,stale_metadata_path_discrepancies=1,authoritative_files_map_consistent=True,generated_native_sources_checked=63,executed_receipts_modified=False,generated_code_modified=False,native_worker_modified=False)),
 'native':('m4-joint-startup124-root/execution-r2/report.json',{'native_executed':True,'full_dependency_acceptance_rehash_required':True,'levels.0.level':'O0','levels.1.level':'O2','levels.0.logical_files':3399774,'levels.1.logical_files':3399774,'levels.0.payload_bytes':13209324735,'levels.1.payload_bytes':13209324735}),
 'controls_build':('m4-lockit-review/controls-build-r5/build.json',dict(source_bodies_modified=False,API_response_injection=False)),
 'controls_execution':('m4-lockit-review/controls-execution-r4/report.json',{'native_executed':True,'source_bodies_modified':False,'API_response_injection':False,'levels.0.level':'O0','levels.1.level':'O2','levels.0.passed':True,'levels.1.passed':True}),
 'controls':('m4-lockit-review/controls-validation-r4/report.json',{'counts.rich_caller_hardware_pairs':64,'counts.real_cleanup_hardware_pairs':64,'counts.actual_attempts':64,'counts.whole_retry_records':241328,'counts.same_session_refusals':32,'counts.causal_targeted_refusals':30,'counts.positive_four_root_runs':2,'counts.positive_actual_Lockit_CALL_RET':16,'counts.positive_actual_new_owners':16,'counts.real_resources_deleted':160,'counts.whole_current_pages':2080}),
 'controls_review':('m4-lockit-review/controls-review-r2/report.json',{'counts.bound_causal_tool_sources':12,'counts.reviewed_actual_refusal_causes':30,'counts.actual_completed_control_workers':2,'native_capture_archive_opened':False}),
}

def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main(supplement,name):
 import importlib.util
 spec=importlib.util.spec_from_file_location('a',Path(__file__).with_name('accept.py'));a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
 more=json.loads(Path(supplement).read_bytes());assert not set(ROWS)&set(more)
 rows=ROWS|{label:(item['path'],item['equal']) for label,item in more.items()};assert set(rows)==a.REQUIRED
 gates={}
 for label,(relative,equal) in rows.items():
  path=ROOT/'reports'/relative;report=json.loads(path.read_bytes());assert report['passed'] is True,label
  for field,expected in equal.items():assert a.extent_value(report,field)==expected,(label,field,expected)
  gates[label]=dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),equal=equal)
 out=ROOT/'reports/m4-joint-startup124-root'/name;assert not out.exists()
 out.write_text(json.dumps(gates,indent=2)+'\n');print(json.dumps(dict(path=str(out),sha256=sha(out),gates=len(gates),predicates=sum(len(i['equal']) for i in gates.values()))))

if __name__=='__main__':main(*sys.argv[1:])
