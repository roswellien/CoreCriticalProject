"""Bounded independent physical-provider and typed Lockit proof review.

Consumes only sealed JSON proofs and physical PE/input pages. It does not open
the native/original archives. Whole persistent source-machine and owner checks
remain attributed to the separately reviewed source observer's actual reader.
"""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import traceback
sys.dont_write_bytecode = True
from provider_exports import Exports, exported, identity, need
ROOT = Path(__file__).resolve().parents[2]

EXPECTED = {
    'reports/m4-lockit-native/preparation-r5/report.json':
        '965ea738333677c308749108b7f0b211772e89d4dd5e2ed14ea561cb63d0bdc1',
    'reports/m4-joint-startup124/preparation-r5/report.json':
        '7a2e383ab47bdb668e56181cdc3eec1c75ebf03437e5f9b9ac675861370a85c7',
    'reports/m4-joint-startup124/build-r4/build.json':
        '05a198d319f2e3ee2259b998a8989db23df0b20afd40416fb185e7a0b1d17c30',
    'reports/m4-joint-startup124-root/execution-r2/report.json':
        'e0ca3ce031afbcde80ff84c0968d30850972625d2f6d8e2a8c8934386a2e7732',
    'reports/m4-lockit-original/original-validation-r2/report.json':
        '4a6f998156b13fc24ed6e6cb285ae482ff562c8d267d1a171c35b0bf7a36c6c3',
    'reports/m4-lockit-review/native-integration-r5/report.json':
        'b05f1e1f5c820d6d209ef1eb1176b29c098860eb06acef9d03de26a1d1f71c37',
    'reports/m4-lockit-review/controls-validation-r4/report.json':
        '1f37a6d0d2fd9fd9dfd812920c710c4717edf6e6cfb4e2f559b4d59fdf6ca129',
}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main(source_report, name):
    out = ROOT / 'reports/m4-lockit-review' / name
    need(not out.exists(), 'Fresh bounded provider review revision')
    out.mkdir(parents=True)
    pins = {}; counts = Counter(); passed = False; physical_rows = []; api_rows = []
    def pin(path, digest=None):
        path = Path(path).resolve(); actual = sha(path)
        need(digest is None or actual == digest, 'Exact bounded physical input ' + str(path))
        need(str(path) not in pins or pins[str(path)] == actual, 'Immutable bounded review input')
        pins[str(path)] = actual
        return path
    def read(path, digest=None):
        path = pin(path, digest)
        need(path.stat().st_size <= 32 * 1024 * 1024, 'Bounded JSON review input')
        return json.loads(path.read_bytes())
    try:
        pin(__file__); pin(Path(__file__).with_name('provider_exports.py'))
        current = {relative: read(ROOT / relative, digest) for relative, digest in EXPECTED.items()}
        need(all(value['passed'] for value in current.values()), 'All exact current prerequisite gates')
        source_report = Path(source_report).resolve(); report = read(source_report)
        need(report['passed'] and report['complete_provider_lifecycle'] and
             report['worker_post_HeapDestroy_identity_observed'], 'Actual current provider proof passed')
        lineage = report['executed_lineage']
        paths = {'execution': 'reports/m4-joint-startup124-root/execution-r2/report.json',
                 'build': 'reports/m4-joint-startup124/build-r4/build.json',
                 'joint_preparation': 'reports/m4-joint-startup124/preparation-r5/report.json',
                 'native_preparation': 'reports/m4-lockit-native/preparation-r5/report.json'}
        for key, relative in paths.items():
            need(Path(lineage[key]).resolve() == (ROOT / relative).resolve(),
                 'Fresh provider proof exact current ' + key)
            need(report['files'][str((ROOT / relative).resolve())] == EXPECTED[relative],
                 'Provider file map binds exact current ' + key)
            if key != 'execution':
                need(lineage[key + '_sha256'] == EXPECTED[relative], 'Explicit current lineage digest')
        need(not report['per_phase_BEFORE_machine_seed'] and not report['candidate_AFTER_machine_seed']
             and not report['paired_original_game_equivalence'] and not report['initializer_credit']
             and not report['whole_M4_complete'] and report['loaded_state2_source_input']
             and not report['native_CS40_opaque_copy'] and report['guest_CS24_semantic_output']
             and not report['native_DllMain_credit'], 'Precisely bounded persistent model and provider scope')
        observer_sources = [
            'tools/m4-lockit-source/compare_provider124_v5.py',
            'tools/m4-lockit-source/final_observer124_v2.py',
            'tools/m4-lockit-source/string_observer124.py',
            'tools/m4-lockit-source/responses.py', 'tools/m4-lockit-source/responses_v2.py',
            'tools/m4-lockit-source/identity_records.py', 'tools/m4-lockit-source/capture.py',
            'tools/m4-lockit-source/game_model.py', 'tools/m4-lockit-source/continuity.py',
            'tools/m4-lockit-source/header_derivations.py',
            'tools/m4-vtable-review/exact_equal.py', 'tools/m4-vtable-review/event_model.py',
            'tools/m4-vtable-review/vtable_model.py',
            'tools/m4-onexit-review/provider_bridge.py', 'tools/m4-onexit-review/provider_capture.py',
            'tools/m4-onexit-review/provider_responses_v2.py',
            'tools/m4-onexit-review/provider_responses.py',
        ]
        for relative in observer_sources:
            path = (ROOT / relative).resolve()
            need(str(path) in report['files'], 'Every executed trust-boundary observer source pinned')
            pin(path, report['files'][str(path)]); counts['bound_observer_sources'] += 1
        prep = current['reports/m4-lockit-native/preparation-r5/report.json']
        loaded = pin(prep['loaded_input_page'], prep['loaded_input_page_sha256']).read_bytes()
        iat = pin(prep['loaded_IAT_page'], prep['loaded_IAT_page_sha256']).read_bytes()
        need(len(loaded) == len(iat) == 4096 and struct.unpack_from('<I', loaded, 0x658)[0] == 2,
             'Whole genuine final original loaded provider input pages')
        authentic = loaded[0x640:0x658]
        need(struct.unpack('<6I', authentic)[1:5] == (0xffffffff, 0, 0, 0),
             'Authentic original unheld serial CS24 baseline')
        # The prior input preparation3 and final5 have identical full loaded pages;
        # no executable or owner fix substituted raw BSS for actual loader input.
        prior = read(ROOT / 'reports/m4-lockit-native/preparation-r3/report.json')
        need(prior['loaded_input_page_sha256'] == prep['loaded_input_page_sha256'] and
             prior['loaded_IAT_page_sha256'] == prep['loaded_IAT_page_sha256'],
             'Inherited provider model input preparation equals complete current5 input')
        need(prep['loaded_original_bootstrap_sha256'] ==
             EXPECTED['reports/m4-lockit-original/original-validation-r2/report.json'],
             'Authentic input comes from final observed original DLL load')
        counts['authentic_whole_input_pages'] = 2
        pcfile = pin(ROOT / 'tools/analysis/pe.py',
                     'bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
        spec = importlib.util.spec_from_file_location('independent_provider_PE32', pcfile)
        PE = importlib.util.module_from_spec(spec); spec.loader.exec_module(PE)
        image = PE.PEImage(pin(ROOT / 'local/mw3-staged/Shared_DLLs/MSVCP50.DLL',
            '91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
        contracts = {}
        for site, slot, name in ((0x7810a30b, 0x78146198, 'EnterCriticalSection'),
                                 (0x7810a35e, 0x78146184, 'LeaveCriticalSection')):
            offset = image.rva_range(site - image.image_base, 6)[0]
            need(image.read(offset, 6) == b'\xff\x15' + struct.pack('<I', slot),
                 'Exact physical source indirect stdcall API instruction')
            contracts[site] = slot, struct.unpack_from('<I', iat, slot - 0x78146000)[0], name
            counts['physical_API_CALL_contracts'] += 1
        def bounded_output(filename):
            path = (source_report.parent / filename).resolve()
            return read(path, report['files'][str(path)])
        records = bounded_output('API-identity-proofs.json')
        need(Path(report['API_identity_proofs']).resolve() ==
             (source_report.parent / 'API-identity-proofs.json').resolve(), 'Direct bounded identity proof link')
        cache = {}; proofs = {}
        for digest, proof in records['proofs'].items():
            canonical = json.dumps(proof, sort_keys=True, separators=(',', ':')).encode()
            need(hashlib.sha256(canonical).hexdigest() == digest, 'Exact emitted immutable deduplicated proof identity')
            raw0, raw1 = bytes.fromhex(proof['identity_before_hex']), bytes.fromhex(proof['identity_after_hex'])
            need(len(raw0) == len(raw1) == 88 and raw0 == raw1, 'Whole actual 11Q identity unchanged')
            ident = identity(struct.unpack('<11Q', raw0), proof['owner_path'], proof['owner_sha256'], pin)
            if 'export_before_hex' in proof:
                export0, export1 = bytes.fromhex(proof['export_before_hex']), bytes.fromhex(proof['export_after_hex'])
                need(export0 == export1, 'Whole actual before/after named/owner export proof unchanged')
                row = exported(export0, ident, proof['name'], pin, cache)
            else:
                key = (ident[2], ident[3])
                if key not in cache: cache[key] = Exports(ident[2], ident[3], pin)
                rva, forward = cache[key].named(proof['name'])
                need(not forward and ident[1] + rva == ident[0],
                     'Actual same lifecycle named export resolves direct physical owner')
                row = dict(requested=proof['name'], target=ident[0], owning_module=ident[2],
                           owning_sha256=ident[3], owning_RVA=rva, lifecycle=True)
            proofs[digest] = proof, ident; physical_rows.append(dict(proof_sha256=digest, **row))
        observed = {}; cases = {(level, seq) for level in ('O0', 'O2') for seq in range(6)}
        services = Counter()
        for row in records['observations']:
            case = row['level'], row['sequence']; need(case in cases, 'Exact actual12case identity association')
            proof, ident = proofs[row['proof_sha256']]
            need(row['requested'] == proof['name'], 'Actual API name joins immutable physical identity')
            if row['API_index'] is None:
                need(row['service'] in ('create', 'query', 'destroy') and
                     row['requested'] == {'create':'HeapCreate', 'query':'GetVersionExA', 'destroy':'HeapDestroy'}[row['service']],
                     'Exact measured bootstrap/query/cleanup identity service')
                services[case + (row['service'],)] += 1; counts['actual_lifecycle_identity_pairs'] += 1
            else:
                key = case + (row['API_index'],)
                need(key not in observed and len(row['witness_words']) == 32 and
                     row['witness_words'][:2] == [1, row['API_index']] and
                     row['witness_words'][14:16] == [1,1] and
                     'export_before_hex' in proof, 'One actual complete successfully observed typed API identity')
                observed[key] = row; counts['actual_typed_identity_pairs'] += 1
        need(all(services[case + (service,)] == 1 for case in cases for service in ('create', 'query', 'destroy')),
             'All36 lifecycle before/after physical owner identities including post-HeapDestroy')
        pc = report['provider_counts']; final_cases = {}
        expected_counts = {'complete124_provider_sequences':12, 'selected_registration_closures':1152,
            'real_producer_allocations':12, 'actual_MFC_allocations':696, 'actual_duplicate_allocations':228,
            'actual_source_frees':936, 'actual_MFC_source_frees':696, 'actual_CS_deletes':60,
            'actual_heap_destroys':12}
        for key, expected in expected_counts.items():
            need(pc[key] == expected, 'Exact complete observed lifecycle count ' + key)
        for row in report['provider_sequences']:
            case = row['level'], row['sequence']; need(case in cases and case not in final_cases,
                'Every actual provider lifecycle exactly once')
            need(row['actual_MFC_allocations'] == 58 and row['selected_used_bytes'] == 384 and
                 row['predicted_growth_replays'] == row['actual_growth_replays'] > 0 and
                 row['all_resources_released'] and row['actual_post_HeapDestroy_identity'],
                 'All actual owners, measured next growth and complete same-heap cleanup')
            indices = sorted(key[2] for key in observed if key[:2] == case)
            need(indices == list(range(row['cleaned_API_count'])), 'Identity proofs cover every actual typed API index')
            final_cases[case] = row
        need(set(final_cases) == cases, 'All12 actual persistent provider cases sealed')
        counts['complete_observed_provider_lifecycles'] = 12
        lockit = bounded_output('Lockit-source-derivations.json')
        need(len(lockit) == 12, 'All12 independently derived Lockit source cases')
        shape = read(ROOT / 'reports/m4-lockit-review/native-integration-r5/resource-domain.json')
        wanted_imports = {}
        for root, ctor, dtor, cbias, dbias in shape['roots']:
            wanted_imports[ctor] = (0x5bb4f8, 0x1df582, 0x7810a290, cbias - 4)
            wanted_imports[dtor] = (0x5bb4f4, 0x1df568, 0x7810a350, dbias - 4)
        for case_record in lockit:
            case = case_record['level'], case_record['sequence']; need(case in cases, 'Current Lockit mathematical case')
            imports = case_record['imports']; relations = case_record['API_relations']
            need(len(imports) == len(relations) == len(case_record['state_reads']) == 8,
                 'All eight actual source imports/state reads/API effects')
            need({row['PC'] for row in imports} == set(wanted_imports), 'Exact four root ctor/dtor callsites')
            generation = None; native_owner = None; actual_thread = None
            for index, (imp, rel, sr) in enumerate(zip(imports, relations, case_record['state_reads'])):
                slot, raw, entry, scratch = wanted_imports[imp['PC']]
                need((imp['slot'], imp['raw'], imp['target'], imp['scratch_offset'],
                      imp['call_target_frame_offset']) == (slot, raw, entry, scratch, scratch + 4),
                     'Independent reviewed literal source import/scratch contract')
                need(imp['ECX'] == imp['before_CALL_ESP'] + scratch and sr == [entry, 0x78145658, 2],
                     'Literal caller ECX and genuine carried provider state2')
                site = 0x7810a30b if entry == 0x7810a290 else 0x7810a35e
                depth = 1 if entry == 0x7810a290 else 0
                frame = imp['before_CALL_ESP'] - 4 - (16 if depth else 8)
                cell, actual_raw, requested = contracts[site]
                words = rel['actual_API_words']; actual = observed[case + (rel['API_index'],)]
                need(words == actual['witness_words'] and actual['requested'] == requested and
                     words[:8] == [1, rel['API_index'], site, cell, actual_raw, frame, site + 6, 1],
                     'Exact actual named API/source CALL return/argument frame relation')
                need(words[8] == words[12] == 0 and words[9] == words[11] and
                     words[13] == 24 and words[14:16] == [1,1] and words[17] == 40 and
                     words[18] == depth and words[19] == 0 and words[20] == 0x78145640 and
                     words[29:32] == [1,1,0], 'Explicit VOID and guest24/native40 typed API domain')
                need((rel['source_PC'], rel['frame'], rel['return_pc'], rel['guest_CS'], rel['depth']) ==
                     (site, frame, site + 6, 0x78145640, depth), 'Exact independently reviewed actual API relation metadata')
                image40 = bytes.fromhex(rel['actual_native_CS40_hex']); semantic24 = bytes.fromhex(rel['derived_CS24_hex'])
                need(len(image40) == 40 and len(semantic24) == 24, 'Whole actual native40 and explicit semantic24 extents')
                lockcount, recursion, ownerthread = struct.unpack_from('<iIQ', image40, 8)
                expected_lock = 0xfffffffe if depth else 0xffffffff
                need(lockcount & 0xffffffff == expected_lock and recursion == depth and
                     (ownerthread > 0 if depth else ownerthread == 0), 'Real serial Windows lock field effects')
                if depth:
                    if actual_thread is None: actual_thread = ownerthread
                    need(ownerthread == actual_thread <= 0xffffffff, 'Same actual current thread for every source pair')
                expected24 = bytearray(authentic)
                struct.pack_into('<3I', expected24, 4, expected_lock, depth, actual_thread if depth else 0)
                need(semantic24 == expected24 and rel['LockCount'] == expected_lock and
                     rel['OwningThread'] == (actual_thread if depth else 0),
                     'All24 semantic output bytes from independently authentic identity and measured effect')
                if generation is None: generation, native_owner = rel['generation'], rel['native_owner']
                need(generation == rel['generation'] > 0 and native_owner == rel['native_owner'] == words[16],
                     'Distinct live provider native owner/generation persists across all source calls')
                api_rows.append(dict(level=case[0], sequence=case[1], import_PC=imp['PC'],
                    source_API_PC=site, frame=frame, depth=depth, actual_thread=ownerthread,
                    API_index=rel['API_index'], physical_proof_sha256=actual['proof_sha256']))
                counts['independent_full24_semantic_relations'] += 1
                counts['actual_native40_field_relations'] += 1
        need(counts['independent_full24_semantic_relations'] == 96, 'All96 actual Lockit semantic relations checked')
        need(report['counts']['persistent_phases'] == 1488 and
             report['counts']['whole_page_BEFORE'] == report['counts']['whole_page_AFTER'] == 63984,
             'Fresh source reader independently compared all persistent phases/entire43pages')
        counts['unique_physical_identity_proofs'] = len(proofs)
        counts['physical_native_module_images'] = len(cache)
        passed = True
    except Exception:
        (out / 'failure.txt').write_text(traceback.format_exc(), encoding='utf-8')
        raise
    finally:
        for filename, value in [('physical-export-relations.json', physical_rows), ('Lockit-semantic-relations.json', api_rows)]:
            path = out / filename; path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8'); pin(path)
        receipt = dict(passed=passed, scope='Independent bounded physical named/owning export resolution, current source-observer trust-boundary review, all96 guest24/native40 Lockit API relations and exact current provider lifecycle receipt',
            native_capture_archive_opened=False, original_capture_archive_opened=False,
            whole_machine_observations_attributed_to_source_reader=True,
            native_DllMain_credit=False, opaque_native40_to_guest24_copy=False,
            original_volatile_API_EAX_equivalence_claimed=False,
            original_API_instruction_body_equivalence_claimed=False,
            initializer_credit=False, counts=dict(counts), files=pins)
        path = out / 'report.json'; path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(dict(passed=passed, report_sha256=sha(path), counts=dict(counts))))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(), sys.argv[2])
