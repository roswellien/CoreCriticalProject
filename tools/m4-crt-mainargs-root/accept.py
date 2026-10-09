"""Seal the reviewed compiled argument prefix, stopping before filename service execution."""
import hashlib
import json
import ntpath
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(out):
    assert out.parent == ROOT / 'reports/m4-crt-mainargs' and not out.exists()
    out.mkdir()
    pins = {}

    def associate(path, digest):
        assert Path(path).is_absolute(), str(path)
        name = ntpath.normcase(ntpath.normpath(str(path)))
        assert len(digest) == 64 and all(c in '0123456789abcdef' for c in digest), name
        assert name not in pins or pins[name] == digest, name
        pins[name] = digest

    def pin(path, digest=None):
        path = Path(path)
        assert path.is_absolute(), str(path)
        actual = sha(path)
        assert digest is None or actual == digest, str(path)
        associate(path, actual)
        return path

    def receipt(folder, digest, name='report.json', pins_digest=None):
        path = pin(folder / name, digest)
        value = json.loads(path.read_text(encoding='utf-8-sig'))
        assert value['passed'], str(path)
        manifest = folder / 'pins.json'
        if manifest.exists():
            assert pins_digest is not None, str(manifest)
            files = json.loads(pin(manifest, pins_digest).read_text())['files']
        else:
            assert pins_digest is None
            files = value['files']
        assert isinstance(files, dict)
        for path, digest in files.items():
            associate(path, digest)
        return value

    try:
        parent = out.parent
        build = parent / 'build-r2'
        b = json.loads(pin(build / 'build.json',
            '9801c1ca6aa4a4b27f05515072b6ae29831d35d3786d9af92d80478389207cdf').read_text())
        assert b['passed'] and not b['SDK_file_open_attestation']
        for group in ('sources', 'tools', 'libraries', 'entry_objects', 'compiler_read_headers', 'artifacts'):
            for path, digest in b[group].items():
                associate(path, digest)
        preparation = receipt(parent / 'preparation-r2',
            '847529bf56d050054eb3f7be16b5fb44a0341a9338848d45e4c9a78e589b3007',
            pins_digest='73da3f1346fdb40eb85424ed7f27a6708e40dc52480e926797b37f8fbccdaaab')
        recovery = receipt(parent / 'recovery-r3',
            'ea623fb2d4bbad3e7636e8155eaafbc6ce6915e293fdd851e4f9eadbc2e0c038',
            pins_digest='291c84f6c09cf1d599d4f22fe6289029560713f06303266993aec8781853b2e5')
        contract = receipt(parent / 'independent-contract-r1',
            '06b3bc854291aed48ae8d2ba9d05de4ebda1127b2d368bdc93f1c1147199c9ae',
            pins_digest='2c32f01f9a884bb1c6b4f38d7f966bb91c589ea021439933faa6ff0b26e081f5')
        source = receipt(parent / 'independent-contract-r4',
            '5f4546669bbfa55d23f9655ab860baea794ff36ad0029c3e2e86b221252e7c32',
            pins_digest='37711dd24fda0f68b06a4340d4063744cd405980ed3b413c6dbee3aa715dc52f')
        data = receipt(parent / 'independent-data-r2',
            '9fd34b8d7ea26d3e89fff109e3b164b20f6ae279b1e915b83a5405e974102b47')
        execution = receipt(parent / 'root-execution-r1',
            '26be8bd736cb9d53e374982be9f49ce4dec4977104aad272b1aedd2695a4d369', 'execution.json',
            pins_digest='2d151a4b0b83da3a23bf379ee8a911f769884d2b68bb93844ffe91de4d4bc606')
        model = receipt(parent / 'root-model-r2',
            'e9bff42b2f365dba9d5e7be928a1f0139516e3630d2a6af7cdd93027b225dc24',
            pins_digest='aa9993fa46ca359817532afb8bdc995c683606eacd16e61268ee4a90aa96cb99')
        compiled = receipt(parent / 'independent-compiled-review-r1',
            '99a8bc7a06abc5c78fd823d60de9ca052639c86e2c895c7c20edcc0c19396218')
        hardware = receipt(parent / 'independent-compiled-observer-controls-r1',
            '3d28c79f1713e1213b2f15228a41d274eadeed01d9b1ad87fbe300fc0d814f2c')
        audit = receipt(parent / 'independent-root-model-audit-r2',
            'f8b97191a5b368597a08d92d70da11a3aeb04b268038b3edc64201a158de0e1e',
            pins_digest='6a8d4c8c2cd6669175237384e25830123cdbf4305603ce3f0579fd1de5a2dce5')
        author = receipt(parent / 'author-submission-r1',
            '7b949e8f6f0e6ffc9215bfaa9add85318bbaf966b14296addbedefd5781a894e',
            pins_digest='c29af918d383ef2e3f33c2c80eaa8d2d2e6cd07872714d33bc53df26b9c96780')
        previous = receipt(ROOT / 'reports/m4-crt-entry-initterm/root-acceptance-r2',
            '0685db17817db850ae18d146de4c70844c4d94a0a5d41703bff57702b46c46fc',
            pins_digest='144b5e3bbdbf883c6477a8f17e520f21e50fa5a0b469464d26413f3574be84f8')
        assert preparation['borrowed_pages'] == 16 and preparation['new_pages'] == []
        assert preparation['source_identity_bytes'] == 1140
        assert not any(preparation[k] for k in ('State_reseed_after_writer', 'State_reseed_after_control',
            'State_reseed_after_initterm', 'State_reseed_inside_mainargs', 'old_Runtime_modified',
            'Session_derivative_changed', 'argc_argv_environment_outputs_admitted'))
        for name, entry, size, digest in (
            ('mainargs', 0x7800ba5e, 66, '50b6f5f60add9aa9b90997c77efd5fc4ae886ce0443e7dfb803f4b243041073c'),
            ('normal_argv', 0x7800bbbc, 140, '50452775522f91555512d02232fd46c4b4f4363b757763d00c2ba81fd0cc28c4')):
            graph = recovery['graphs'][name]
            assert (graph['entry'], graph['source_bytes'], graph['source_sha256']) == (entry, size, digest)
            assert graph['complete_local_CFG'] and not graph['complete_dependency_closure']
        assert (contract['actual_prefix_instructions'], contract['actual_prefix_memory_accesses'], contract['new_pages']) == (19, 16, 0)
        required = contract['source_contract']['required_stop']
        assert (required['source_site'], required['provider_IAT'], required['raw_target'], required['real_return_PC']) == (
            0x7800bbd0, 0x7802e018, 0x343b0, 0x7800bbd6)
        assert required['args'] == [0, 0x7803b3f0, 260] and required['no_OS_service_success']
        assert source['unchanged_16page_carry'] and source['actual_new_source_bytes'] == 206
        assert all(v['passed'] for v in source['checks'])
        assert source['checks'][-1]['full_source_functions_preserved']
        assert not source['argc_argv_environment_initialized'] and not source['filename_service_success']
        gate = data['selected_safe_executable_gate']
        assert gate['before_commandline_read'] and gate['no_commandline_registry_splice']
        assert not gate['output_DWORDs_written_before_stop'] and gate['no_expected_argc_argv_env_fabrication']
        assert execution['native_executed_by_root'] and (execution['positive_cases'], execution['causal_controls']) == (48, 120)
        assert (model['positive_records'], model['causal_records'], model['whole_State_bytes'], model['whole_FX_bytes'],
            model['whole_pages'], model['source_identity_bytes']) == (48, 120, 3504, 512, 16, 1140)
        assert (model['positive_writer_events'], model['positive_game_events'], model['mainargs_accesses'],
            model['mainargs_route_events'], model['direct_host_boundary_pairs']) == (4656, 2304, 768, 192, 330)
        assert len(model['observer_corruption_denials']) == 88806
        visits = [0x7800ba5e, 0x7800ba5f, 0x7800ba61, 0x7800ba64, 0x7800ba68, 0x7800ba6a,
            0x7800ba6f, 0x7800ba99, 0x7800bbbc, 0x7800bbbd, 0x7800bbbf, 0x7800bbc0,
            0x7800bbc1, 0x7800bbc2, 0x7800bbc3, 0x7800bbc8, 0x7800bbcd, 0x7800bbce, 0x7800bbd0]
        assert len(model['positives']) == 48 and len(model['causals']) == 120
        assert {(v['level'], v['id']) for v in model['positives']} == {(l, i) for l in ('O0', 'O2') for i in range(24)}
        assert all((v['game_events'], v['mainargs_accesses'], v['mainargs_routes'], v['mainargs_source_PCs']) == (
            48, 16, 4, visits) for v in model['positives'])
        assert {(v['level'], v['control']) for v in model['causals']} == {(l, c) for l in ('O0', 'O2') for c in range(1, 61)}
        special = [v for v in model['causals'] if v['control'] == 43]
        assert len(special) == 2
        assert all(v['artifact_specific_injected_operand'] and not v['architectural_source_equivalence_credited']
            and not v['whole_source_prefix_predicted'] for v in special)
        assert all(v['whole_source_prefix_predicted'] for v in model['causals'] if v['control'] != 43)
        assert not any(model[k] for k in ('author_model_imported', 'mode43_generalized_source_equivalence',
            'callbacks_executed', 'argument_initialization_complete', 'provider_API_executed', 'full_CRT'))
        assert (compiled['checks'], compiled['scenarios'], compiled['direct_host_records'],
            compiled['nonzero_complete_legacy_metadata_records'], compiled['malformed_token_denials']) == (2078, 64, 128, 128, 420)
        assert (hardware['actual_hardware_raw80_before_fixtures'], hardware['actual_complete_legacy_tag_before_fixtures'],
            hardware['meaningful_corruption_denials']) == (128, 128, 548)
        assert not hardware['guest_result_inferred_from_AFTER'] and not hardware['volatile_XMM0_5_equality_claimed']
        source_model = pin(ROOT / 'tools/m4-crt-mainargs-root/model.py',
            '2d1abb299279e6788a4d65483ef67b249d26e51465153604f3b34b621d5e4c59')
        observer = pin(ROOT / 'tools/m4-crt-mainargs-root/observe.py',
            'a7e791622a3e21a04970f53695d4403dccbb3856bc72ab8fd75b0b1487f18029')
        assert audit['BEFORE_only'] and not audit['candidate_model_imported'] and not audit['native_AFTER_as_expected_seed']
        assert audit['root_model_sha256'] == sha(source_model) and audit['root_observer_sha256'] == sha(observer)
        assert audit['root_proof_sha256'] == sha(parent / 'root-model-r2/report.json')
        assert audit['root_execution_sha256'] == sha(parent / 'root-execution-r1/execution.json')
        assert (audit['new_prefix_source_PCs'], audit['new_prefix_accesses'], audit['new_prefix_routes'],
            audit['shared_equality_corruption_denials']) == (19, 16, 4, 88806)
        assert not audit['filename_OS_import_success'] and not audit['argument_environment_initialization_complete']
        assert previous['actual_CRT_entry_first_null_initterm_composition_accepted']
        assert (previous['connected_initializer_roots'], previous['total_nonzero_roots'], previous['remaining_nonzero_roots']) == (27, 144, 117)
        assert not any(v['whole_M4_complete'] for v in (b, preparation, recovery, contract, source, data,
            execution, model, compiled, hardware, audit, author, previous))
        # Keep diagnostic revisions without importing their obsolete candidate-source manifests.
        retained = {}
        for folder in ('recovery-r1', 'recovery-r2', 'build-r1', 'independent-contract-r2',
            'independent-contract-r3', 'independent-root-model-audit-r1', 'root-model-r1'):
            paths = [p for p in (parent / folder).iterdir() if p.is_file() and p.name in (
                'failure.txt', 'failure.json', 'report.json', 'build.json', 'failed-source.py', 'auditor-attempt.py')]
            assert paths, folder
            retained[folder] = {str(p): sha(pin(p)) for p in paths}
        pin(__file__)
        pin(sys.executable)
        (out / 'review-source.py').write_bytes(Path(__file__).read_bytes())
        pin(out / 'review-source.py')
        print(json.dumps(dict(stage='physical_dependency_rehash', bindings=len(pins))), flush=True)
        for index, (path, digest) in enumerate(list(pins.items()), 1):
            assert sha(path) == digest, path
            if index % 10000 == 0:
                print(json.dumps(dict(rehashed=index, total=len(pins))), flush=True)
        result = dict(passed=True, date='2026-10-08', actual_CRT_entry_mainargs_to_filename_import_composition_accepted=True,
            build_path=str(build / 'build.json'), root_execution_path=str(parent / 'root-execution-r1/execution.json'),
            root_source_model_path=str(parent / 'root-model-r2/report.json'),
            independent_source_path=str(parent / 'independent-contract-r4/report.json'),
            independent_data_path=str(parent / 'independent-data-r2/report.json'),
            independent_compiled_path=str(parent / 'independent-compiled-review-r1/report.json'),
            independent_hardware_observer_path=str(parent / 'independent-compiled-observer-controls-r1/report.json'),
            independent_root_model_audit_path=str(parent / 'independent-root-model-audit-r2/report.json'),
            author_submission_path=str(parent / 'author-submission-r1/report.json'),
            previous_acceptance_path=str(ROOT / 'reports/m4-crt-entry-initterm/root-acceptance-r2/report.json'),
            actual_route=dict(game_CALL=0x5ac468, game_IAT=0x5bb514, game_raw_IAT=0x1ded02, game_return_PC=0x5ac46e,
                provider=0x7800ba5e, complete_provider_source_bytes=66, internal_CALL=0x7800ba99,
                internal_return_PC=0x7800ba9e, builder=0x7800bbbc, complete_builder_source_bytes=140,
                executed_source_PCs=19, memory_accesses=16, typed_routes=4),
            next_required_import=dict(source_PC=0x7800bbd0, IAT=0x7802e018, raw_target=0x343b0,
                return_PC=0x7800bbd6, name='KERNEL32.dll!GetModuleFileNameA',
                arguments=[0, 0x7803b3f0, 260], frame=0x20001834,
                fault='unresolved_import', real_CALL_effects_preserved=True, service_executed=False),
            positive_compositions=48, causal_cases=120, causal_source_records=118,
            artifact_specific_observer_mutations=2, new_causal_controls=24,
            whole_State_bytes=3504, separate_FX_bytes=512, captured_pages=16, source_identity_bytes=1140,
            writer_positive_events=4656, game_positive_events=2304, mainargs_source_accesses=768,
            mainargs_route_events=192, root_observer_corruption_denials=88806, root_direct_host_pairs=330,
            independent_compiled_assertions=2078, independent_compiled_compositions=64,
            independent_rich_host_pairs=128, independent_token_denials=420, independent_hardware_capture_denials=548,
            source_model_read_only_audit=dict(passed=True, model_sha256=sha(source_model), observer_sha256=sha(observer),
                BEFORE_only_seed=True, new_prefix_checked_PUSH_CALL_store_before_ESP_publication=True,
                new_prefix_read_before_MOV_CMP_result_publication=True,
                early_unconstructed_Context_absence_checked=True, final_proof_sha256=audit['root_proof_sha256']),
            mode43_contract=dict(O0_fault_operand=0x20002008, O2_fault_operand=0x20001874,
                basis='Inherited independently reviewed unchanged COFF/noalias-IR fixtures of an alias-changing observer',
                generalized_guest_source_equivalence=False),
            complete_two_native_bodies_preserved=True, Runtime_provider_translation_registered=False,
            Runtime_provider_import_registered=False, prior_Runtime_and_Session_retained=True,
            pages_borrowed_without_reset=True, State_reseed=False, FX_reseed=False, new_pages=0,
            typed_context_cleanup=True, persistent_State_Runtime_FX=True, generic_Runtime_calls=11,
            generic_Runtime_completed_calls=9, provider_internal_generic_Runtime_frames=0,
            filename_buffer_changed=False, argc_argv_environment_initialized=False,
            argument_function_returned=False, callbacks_executed=False,
            compiler_identity_scope='Recorded compiler commands/read headers and physical source/tool/artifact associations; no process file-open attestation',
            connected_initializer_roots=27, total_nonzero_roots=144, remaining_nonzero_roots=117,
            entry_and_selected_main_table_composed_together=False,
            limits=['Guest corpus: twelve masked CWs, empty TOP0 stack, two repetitions; broader incoming FP domain remains open',
                '128 rich host pairs cover distinct raw80 values and legacy metadata, depth0/1/3/7, TOP3/7 and masked sticky status; broader host domain remains open',
                'Inherited mode43 observer mutations are artifact-specific; undefined AF and volatile XMM0-5 equality are not generalized',
                'No new complete-original-CRT capture; BEFORE-only source model is distinct from prior isolated original/native observations',
                'The NULL-module filename service will observe the native host module; admitted guest executable identity requires an explicit separate contract',
                'Commandline producer is separately reviewed but not integrated here; page overlap, classification/parser, allocator and environment lifetimes remain open',
                'No filename API success, argument outputs/RET, main initializer table, complete CRT/SEH/DLL attach/termination, native menu or gameplay credit'],
            retained_review_revisions=retained, prior_frozen_objects_mutated=False,
            ordinary_game_launched=False, original_executed=False, full_CRT=False,
            M4_status='active', whole_M4_complete=False, physical_dependency_bindings=len(pins))
        (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
        pin(out / 'report.json')
        (out / 'pins.json').write_text(json.dumps(dict(files=dict(sorted(pins.items()))), indent=2) + '\n')
        print(json.dumps(dict(passed=True, bindings=len(pins), report_sha256=sha(out / 'report.json'),
            next_import='GetModuleFileNameA', connected_roots=27)))
    except Exception:
        (out / 'failure.txt').write_text(traceback.format_exc())
        raise


if __name__ == '__main__':
    main(*[Path(p).resolve() for p in sys.argv[1:]])
