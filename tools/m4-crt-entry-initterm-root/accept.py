"""Seal the bounded actual first-null _initterm composition, without extending M4."""
import hashlib,json,sys,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def main(out):
    assert out.parent==ROOT/'reports/m4-crt-entry-initterm' and not out.exists()
    out.mkdir();pins={}
    def associate(path,digest):
        name=str(Path(path).resolve())
        assert len(digest)==64 and all(c in '0123456789abcdef' for c in digest),name
        assert name not in pins or pins[name]==digest,name
        pins[name]=digest
    def pin(path,digest=None):
        path=Path(path).resolve();actual=sha(path)
        assert digest is None or actual==digest,str(path)
        associate(path,actual);return path
    def receipt(folder,digest,name='report.json',pins_digest=None):
        path=pin(folder/name,digest);value=json.loads(path.read_text(encoding='utf-8-sig'))
        assert value['passed'],str(path)
        manifest=folder/'pins.json'
        files=json.loads(pin(manifest,pins_digest).read_text())['files'] if manifest.exists() else value['files']
        for path,digest in files.items():associate(path,digest)
        return value
    try:
        parent=out.parent;build=parent/'build-r3'
        b=json.loads(pin(build/'build.json','2f746c732287a4bbda845abf9c3c95a2d65e650984b5eda5f0b6616ddaeb19e4').read_text(encoding='utf-8-sig'))
        assert b['passed'] and not b['SDK_file_open_attestation']
        for group in ('sources','tools','libraries','entry_objects','compiler_read_headers','artifacts'):
            for path,digest in b[group].items():associate(path,digest)
        preparation=receipt(parent/'preparation-r3','bc38dc40c895201d961064f89c23e601ce1093ac335fa08d04d61b64c868d5f4',pins_digest='92cade64dd4e58d5636e424126b2d750ca196776078b6889f2b13c9213f85809')
        provider=receipt(parent/'provider-preparation-r3','bf9aa74294caca488d507ff47a475123953b60fc99218837d2903c31eb58ee88',pins_digest='e8cece56d0ea674fff662f0ef5c676b9f30bd5ea59851bee8f6e02d673548b9a')
        execution=receipt(parent/'root-execution-r1','191399ab28c1817477e4d0ab21d1fbc27773119f67d2d5ad10f0fa64f2c0ec64','execution.json')
        model=receipt(parent/'root-model-r2','cea46552bcb0f4bcacc8a438d2ade88f59a9033335b770cceb6073ea9936db68',pins_digest='59b0136c568a60792b203eb1884b5f1b0f0b82c4b9cebbc99d9587fc47218c33')
        source=receipt(parent/'independent-source-r3','915d39918aadc77b1f415993bcb4039ae24d327ae3a0a4c6fb585a46b315d7d4',pins_digest='8c4c6b22e918bf0e25d290006cab8ca85f7ec192b4677304c5ccb0e7fb839eef')
        compiled=receipt(parent/'independent-compiled-review-r1','bd461d197db407edd9c498b2779eff28c94d86145009db2ccc6d8307227a32f4')
        hardware=receipt(parent/'independent-compiled-observer-controls-r1','514bdcadf1bdf1027c916d684fd6d234d8c0dc5049bfc51b68e124b4f35d67e6')
        audit=receipt(parent/'independent-root-model-audit-r1','3138a61452ec26cab1f79852398d06c7cd693d60ffa7283f0ca19b05ce81f2e0',pins_digest='3f3b166761653ba6bf216df582e85f0b4fdd3a7486950edd8e479b93f948a78a')
        previous=receipt(ROOT/'reports/m4-crt-entry-control/root-acceptance-r1','984e18e7165532a0d219082122245d527716042d7dd97ff1fb6f378df134b460')
        assert (provider['entry'],provider['source_bytes'],len(provider['layouts']))==(0x780014f8,28,34)
        assert provider['source_sha256']=='960ed0d00b0200736930590a16fbb3caa9c3bc24af9851a3728258fd9b340678'
        assert provider['first_interval']==[0x5e0248,0x5e024c] and not provider['callback_success_admitted']
        assert preparation['total_pages']==16 and not any(preparation[k] for k in ('State_reseed_after_writer','State_reseed_after_control','State_reseed_after_initterm','old_Session_modified','old_callback_continuation_admitted','callback_success_admitted'))
        assert execution['native_executed_by_root'] and (execution['positive_cases'],execution['causal_controls'])==(48,96)
        assert (model['positive_records'],model['causal_records'],model['whole_State_bytes'],model['whole_FX_bytes'],model['whole_pages'],model['source_identity_bytes'])==(48,96,3504,512,16,934)
        assert (model['positive_writer_events'],model['positive_game_events'],model['initterm_accesses'],model['initterm_route_events'],model['direct_host_boundary_pairs'])==(4656,2304,384,288,282)
        assert len(model['observer_corruption_denials'])==68840
        assert not any(model[k] for k in ('author_model_imported','mode43_generalized_source_equivalence','callbacks_executed','full_CRT','whole_M4_complete'))
        visits=[0x780014f8,0x780014f9,0x780014fd,0x78001502,0x78001506,0x78001508,0x7800150a,0x7800150c,0x780014ff,0x78001502,0x78001506,0x78001512,0x78001513]
        assert all((v['game_events'],v['initterm_accesses'],v['initterm_routes'],v['initterm_source_PCs'])==(48,8,6,visits) for v in model['positives'])
        assert len(model['positives'])==48 and len(model['causals'])==96
        special=[v for v in model['causals'] if v['control']==43]
        assert {v['level']:v['initterm_job'][-1] for v in special}=={'O0':0x20002008,'O2':0x20001874}
        assert all(v['artifact_specific_injected_operand'] and not v['architectural_source_equivalence_credited'] for v in special)
        assert not source['findings'] and source['selected_initializer_count_unchanged']==27
        assert (compiled['checks'],compiled['scenarios'],compiled['direct_host_records'],compiled['nonzero_complete_legacy_metadata_records'],compiled['malformed_token_denials'])==(1540,62,124,124,192)
        assert (hardware['actual_hardware_raw80_before_fixtures'],hardware['actual_complete_legacy_tag_before_fixtures'],hardware['meaningful_corruption_denials'])==(124,124,548)
        assert not hardware['guest_result_inferred_from_AFTER'] and not hardware['volatile_XMM0_5_equality_claimed']
        source_model=pin(ROOT/'tools/m4-crt-entry-initterm-root/model.py','b19863e5ab04f8a348c626601ce3086adfbcd8357b399eefb47c5439565707e1')
        observer=pin(ROOT/'tools/m4-crt-entry-initterm-root/observe.py','453b0032ac308b090d1b77438a10d8fa66ed32d13e979fb991d4536ce44d769f')
        assert audit['BEFORE_only'] and not audit['findings'] and not audit['candidate_model_imported']
        assert audit['model_sha256']==sha(source_model) and audit['observer_sha256']==sha(observer)
        assert audit['root_proof_sha256']==sha(parent/'root-model-r2/report.json')
        assert (audit['causal_source_expectations_excluding_mode43'],audit['causal_mode43_artifact_fixtures'])==(94,2) and not audit['mode43_source_equivalence_credited']
        assert previous['actual_CRT_entry_control_composition_accepted']
        assert (previous['connected_initializer_roots'],previous['total_nonzero_roots'],previous['remaining_nonzero_roots'])==(27,144,117)
        assert not any(v['whole_M4_complete'] for v in (b,preparation,provider,execution,model,source,compiled,hardware,audit,previous))
        # Bind failed receipts without importing obsolete candidate-source manifests.
        for folder in ('root-model-r1','independent-source-r2','independent-compiled-build-r1','execution-r1'):
            candidates=[p for p in (parent/folder).iterdir() if p.is_file() and p.name in ('failure.txt','report.json','build.json')]
            assert candidates,folder
            for path in candidates:pin(path)
        # Queue associations, then read every unique physical dependency once.
        # This is post-build closure; it is not process file-open attestation.
        pin(__file__);pin(sys.executable)
        (out/'review-source.py').write_bytes(Path(__file__).read_bytes());pin(out/'review-source.py')
        for path,digest in list(pins.items()):assert sha(path)==digest,path
        result=dict(passed=True,date='2026-10-08',actual_CRT_entry_first_null_initterm_composition_accepted=True,
            build_path=str(build/'build.json'),root_execution_path=str(parent/'root-execution-r1/execution.json'),root_source_model_path=str(parent/'root-model-r2/report.json'),
            independent_source_path=str(parent/'independent-source-r3/report.json'),independent_compiled_path=str(parent/'independent-compiled-review-r1/report.json'),independent_hardware_observer_path=str(parent/'independent-compiled-observer-controls-r1/report.json'),independent_root_model_audit_path=str(parent/'independent-root-model-audit-r1/report.json'),previous_acceptance_path=str(ROOT/'reports/m4-crt-entry-control/root-acceptance-r1/report.json'),
            actual_route=dict(source_CALL=0x5ac440,thunk=0x5ac598,IAT=0x5bb510,raw_IAT_target=0x1ded12,staged_provider=0x780014f8,provider_source_bytes=28,interval=[0x5e0248,0x5e024c],null_cells_read=1,return_PC=0x5ac445),
            next_required_import=dict(source_PC=0x5ac468,IAT=0x5bb514,raw_target=0x1ded02,return_PC=0x5ac46e,name='MSVCRT.dll!__getmainargs'),
            positive_compositions=48,causal_cases=96,causal_source_records=94,artifact_specific_observer_mutations=2,whole_State_bytes=3504,separate_FX_bytes=512,captured_pages=16,source_identity_bytes=934,
            writer_positive_events=4656,game_positive_events=2304,initterm_source_accesses=384,initterm_route_events=288,root_observer_corruption_denials=68840,root_direct_host_pairs=282,
            independent_compiled_assertions=1540,independent_compiled_compositions=62,independent_rich_host_pairs=124,independent_token_denials=192,independent_hardware_capture_denials=548,
            source_model_read_only_audit=dict(passed=True,model_sha256=sha(source_model),observer_sha256=sha(observer),BEFORE_only_seed=True,PUSH_CALL_store_before_ESP=True,POP_ESP_before_read=True,RET_read_before_PC_ESP=True),
            mode43_contract=dict(O0_fault_operand=0x20002008,O2_fault_operand=0x20001874,basis='Independently decoded unchanged O0/O2 COFFs and preserved noalias provider IR; both current-State guards deny before read/ALU',generalized_guest_source_equivalence=False),
            complete_initterm_provider_translated=True,successful_callback_execution=False,exclusive_end_cell_read_by_positive=False,
            Session_derivative='Exactly three edits: forward declaration, compiled _initterm callback pointer, withholding unused overlapping callback-continuation publication; earlier service bodies retained',
            provider_page_mapped_literal_RX=True,existing_table_page_borrowed_without_reset=True,persistent_State_Runtime_FX=True,typed_context_cleanup=True,
            compiler_identity_scope='Recorded commands, compiler-read headers and physical tool/source/artifact associations; no process file-open attestation',
            connected_initializer_roots=27,total_nonzero_roots=144,remaining_nonzero_roots=117,entry_and_selected_main_table_composed_together=False,
            limits=['Guest corpus is twelve masked CWs, empty TOP0 stack, two repetitions; broader incoming FP domain remains open',
                '124 rich host pairs cover populated legacy metadata, distinct raw80 values, depth0/1/3/7, TOP3/7 and masked sticky status; broader host domain remains open',
                'Mode43 changes a noalias State through the external observer; its cached/reloaded operands are artifact-specific fixtures, not generalized guest instruction behavior',
                'Undefined AF representative is not generalized; volatile XMM0-5 equality is unclaimed',
                'No new complete-original-CRT capture; independent BEFORE-only source modeling is distinct from prior isolated original/native observations',
                'No successful initializer callback, main table, argument initialization, complete SEH/DLL attach/termination, application startup or native menu execution'],
            failed_review_revisions_retained=True,prior_frozen_objects_mutated=False,ordinary_game_launched=False,original_executed=False,M4_status='active',whole_M4_complete=False,physical_dependency_bindings=len(pins))
        (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');pin(out/'report.json')
        (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(pins.items()))),indent=2)+'\n')
        print(json.dumps(dict(passed=True,bindings=len(pins),report_sha256=sha(out/'report.json'),next_import='__getmainargs',connected_roots=27)))
    except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main(*[Path(p).resolve() for p in sys.argv[1:]])
