"""Independent bounded physical native API/provider125 proof review."""
import collections
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/m4-lockit-review'))
from provider_exports import Exports, exported, identity
sys.path.insert(0, str(Path(__file__).parent))
import review_connected125_v2 as C


def main(provider_path, name):
    provider_path = Path(provider_path).resolve()
    out = ROOT / 'reports/m4-tree-review' / name
    C.need(not out.exists(), 'Fresh bounded provider125 review')
    out.mkdir(parents=True)
    counts = collections.Counter()
    passed = False
    error = None
    try:
        C.pin(__file__)
        C.pin(ROOT / 'tools/m4-tree-review/review_connected125_v2.py')
        C.pin(ROOT / 'tools/m4-lockit-review/provider_exports.py',
              'de71cd3549d50f0543ba0f7165b13b1a06594bc7e868a6fe44c65e6899562ecf')
        report = C.read(provider_path)
        C.lineage(report)
        C.need(report['complete_provider_lifecycle'] and report['worker_post_HeapDestroy_identity_observed'],
               'Complete actual current provider cleanup and post-destroy identity observed')
        source = C.read(ROOT / 'reports/m4-tree-source/connected-native125-source-r2/report.json',
                        '02fbae62687ca09d73c8c05ae86981c02570208b2a3ae92faea8b81ac9509f76')
        C.read(ROOT / 'reports/m4-tree-review/connected125-source-r2/report.json',
               'c1f95535dc29dfe5b2a8bf6429c5d2070c9c20cc2261829b7cf27af7a6cf049d')
        for key in ('persistent_phases', 'whole_page_BEFORE', 'whole_page_AFTER',
                    'literal_registration_roots', 'literal_Lockit_CALL_RET_pairs',
                    'actual_native_CS40_source_API_relations', 'native_FS_source_accesses',
                    'actual_native12B_source_relations', 'whole_owned_access_relations',
                    'whole_publication_relations', 'whole_native_scratch_contexts',
                    'whole_native_tree_owner_backings'):
            C.need(report['counts'][key] == source['counts'][key], 'Provider repeats complete actual source extent ' + key)
        required = ['tools/m4-tree-source/compare_provider125_v4.py', 'tools/m4-tree-source/final_observer125_v2.py',
                    'tools/m4-tree-source/responses125.py', 'tools/m4-tree-source/game_model_v4.py',
                    'tools/m4-tree-source/native_tree_relations_v4.py', 'tools/m4-tree-source/continuity125.py',
                    'tools/m4-lockit-source/string_observer124.py', 'tools/m4-lockit-source/capture.py',
                    'tools/m4-lockit-source/bridge_v2.py', 'tools/m4-lockit-source/identity_records.py',
                    'tools/m4-vtable-review/exact_equal.py', 'tools/m4-vtable-review/event_model.py',
                    'tools/m4-vtable-review/vtable_model.py', 'tools/m4-onexit-review/provider_responses_v2.py',
                    'tools/m4-onexit-review/provider_responses.py', 'tools/m4-onexit-review/provider_bridge.py']
        for relative in required:
            path = (ROOT / relative).resolve()
            C.need(str(path) in report['files'], 'Exact executed provider trust boundary is pinned')
            C.pin(path, report['files'][str(path)])
            counts['reviewed_provider_boundary_tools'] += 1
        observer = (ROOT / 'tools/m4-tree-source/final_observer125_v2.py').read_text()
        C.need("r['words'][18]==proof['generation']" in observer and
               "r['words'][16]==data['value']" in observer and
               "w[4]==proof['allocation_CALL_pc']" in observer,
               'Source publication resolves actual current generation rather than first repeated CALL owner')
        prep = C.read(ROOT / 'reports/m4-tree-native/preparation-r5/report.json',
                      C.EXPECTED['reports/m4-tree-native/preparation-r5/report.json'])
        loaded = C.pin(prep['loaded_input_page'], prep['loaded_input_page_sha256']).read_bytes()
        iat = C.pin(prep['loaded_IAT_page'], prep['loaded_IAT_page_sha256']).read_bytes()
        C.need(len(loaded) == len(iat) == 4096 and struct.unpack_from('<I', loaded, 0x658)[0] == 2,
               'Whole authentic original loaded state2 and resolved IAT inputs')
        baseline = loaded[0x640:0x658]
        C.need(struct.unpack('<6I', baseline)[1:5] == (0xffffffff, 0, 0, 0),
               'Original opaque CS24 starts initialized and unheld')
        pe_path = C.pin(ROOT / 'tools/analysis/pe.py',
                        'bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
        spec = importlib.util.spec_from_file_location('bounded125_physical_provider', pe_path)
        PE = importlib.util.module_from_spec(spec); spec.loader.exec_module(PE)
        physical = PE.PEImage(C.pin(ROOT / 'local/mw3-staged/Shared_DLLs/MSVCP50.DLL',
                                 '91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
        contracts = {}
        for site, slot, name in ((0x7810a30b, 0x78146198, 'EnterCriticalSection'),
                                 (0x7810a35e, 0x78146184, 'LeaveCriticalSection')):
            offset = physical.rva_range(site - physical.image_base, 6)[0]
            C.need(physical.read(offset, 6) == b'\xff\x15' + struct.pack('<I', slot),
                   'Exact physical indirect source stdcall')
            contracts[site] = slot, struct.unpack_from('<I', iat, slot - 0x78146000)[0], name
            counts['physical_source_API_CALLs'] += 1
        records = C.output(report, provider_path.parent, 'API-identity-proofs.json')
        proofs = {}
        cache = {}
        for digest, proof in records['proofs'].items():
            C.need(hashlib.sha256(json.dumps(proof, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == digest,
                   'Exact deduplicated whole identity proof')
            a, b = bytes.fromhex(proof['identity_before_hex']), bytes.fromhex(proof['identity_after_hex'])
            C.need(len(a) == len(b) == 88 and a == b, 'Complete unchanged actual11Q native identity')
            ident = identity(struct.unpack('<11Q', a), proof['owner_path'], proof['owner_sha256'], C.pin)
            if 'export_before_hex' in proof:
                a, b = bytes.fromhex(proof['export_before_hex']), bytes.fromhex(proof['export_after_hex'])
                C.need(a == b, 'Full4624B named/owner export witness unchanged')
                exported(a, ident, proof['name'], C.pin, cache)
            else:
                key = ident[2], ident[3]
                if key not in cache:
                    cache[key] = Exports(ident[2], ident[3], C.pin)
                rva, forwarded = cache[key].named(proof['name'])
                C.need(not forwarded and ident[1] + rva == ident[0], 'Physical direct lifecycle owner export')
            proofs[digest] = proof
            counts['independent_physical_named_owner_proofs'] += 1
        cases = {(level, seq) for level in ('O0', 'O2') for seq in range(6)}
        observed = {}
        services = collections.Counter()
        for row in records['observations']:
            case = row['level'], row['sequence']
            C.need(case in cases and row['proof_sha256'] in proofs, 'Exact current actual case and immutable proof')
            proof = proofs[row['proof_sha256']]
            C.need(row['requested'] == proof['name'], 'Actual named API joins physical identity')
            if row['API_index'] is None:
                C.need(row['service'] in ('create', 'query', 'destroy') and row['requested'] ==
                       {'create': 'HeapCreate', 'query': 'GetVersionExA', 'destroy': 'HeapDestroy'}[row['service']],
                       'Exact real lifecycle identity service')
                services[case + (row['service'],)] += 1
                counts['actual_lifecycle_identity_pairs'] += 1
            else:
                key = case + (row['API_index'],)
                C.need(key not in observed and len(row['witness_words']) == 32 and
                       row['witness_words'][:2] == [1, row['API_index']] and
                       row['witness_words'][14:16] == [1, 1] and 'export_before_hex' in proof,
                       'Unique complete successful actual32Q typed API witness')
                observed[key] = row
                counts['actual_typed_identity_pairs'] += 1
        C.need(all(services[case + (service,)] == 1 for case in cases for service in ('create', 'query', 'destroy')),
               'All36 bootstrap/query/postdestroy actual identity pairs')
        expected_counts = {'complete125_provider_sequences': 12, 'selected_registration_closures': 1164,
                           'real_producer_allocations': 12, 'actual_MFC_allocations': 780,
                           'actual_duplicate_allocations': 228, 'actual_source_frees': 1020,
                           'actual_MFC_source_frees': 780, 'actual_CS_deletes': 60, 'actual_heap_destroys': 12,
                           'exact_tree_primary_publications': 84}
        for key, value in expected_counts.items():
            C.need(report['provider_counts'][key] == value, 'Measured full current lifecycle ' + key)
        seen = set()
        for row in report['provider_sequences']:
            case = row['level'], row['sequence']
            C.need(case in cases and case not in seen and row['actual_MFC_allocations'] == 65 and
                   row['selected_used_bytes'] == 388 and row['actual_growth_replays'] == row['predicted_growth_replays'] > 0 and
                   row['all_resources_released'] and row['actual_post_HeapDestroy_identity'],
                   'Whole actual65 MFC/97 callback/measuredMSIZE/growth/frees/sameheap lifecycle')
            C.need(sorted(key[2] for key in observed if key[:2] == case) == list(range(row['cleaned_API_count'])),
                   'Physical identities cover every actual typed API index through cleanup')
            seen.add(case)
        C.need(seen == cases, 'All twelve actual complete lifecycles')
        lockit = C.output(report, provider_path.parent, 'Lockit-source-derivations.json')
        C.need(len(lockit) == 12, 'Every current provider source case')
        for case_row in lockit:
            case = case_row['level'], case_row['sequence']
            C.need(case in cases and len(case_row['imports']) == 8 and
                   len(case_row['state_reads']) == len(case_row['API_relations']) == 34,
                   'Inherited8 source imports and full34 state reads/API effects')
            for relation in case_row['API_relations']:
                site = relation['source_PC']; slot, raw, name = contracts[site]
                w = relation['actual_API_words']; depth = relation['depth']
                row = observed[case + (relation['API_index'],)]
                C.need(row['requested'] == name and row['witness_words'] == w and
                       w[:8] == [1, relation['API_index'], site, slot, raw, relation['frame'], relation['return_pc'], 1],
                       'Actual whole32Q source CALL/frame joins unchanged physical named API proof')
                C.need(w[9] == w[11] and w[8] == w[12] == 0 and w[16] == relation['native_owner'] and
                       w[17] == 40 and w[18] == depth and depth in (0, 1, 2),
                       'Whole actual VOID/LastError/native40/serial recursion contract')
                wanted = bytearray(baseline)
                struct.pack_into('<III', wanted, 4, relation['LockCount'], depth, relation['OwningThread'])
                C.need(bytes(wanted).hex() == relation['derived_CS24_hex'] and
                       relation['LockCount'] == (0xffffffff if not depth else 0xfffffffe),
                       'Whole guest24 derives from authentic opaque identity and typed serial fields')
                image = bytes.fromhex(relation['actual_native_CS40_hex'])
                C.need(len(image) == 40 and struct.unpack_from('<II', image, 8) == (relation['LockCount'], depth) and
                       struct.unpack_from('<Q', image, 16)[0] == relation['OwningThread'],
                       'Actual native40 Windows fields agree with separately derived guest24')
                counts['physical_actual_Lockit_API_relations'] += 1
        C.need(counts['physical_actual_Lockit_API_relations'] == 408, 'Every old/new actual source API relation physically joined')
        passed = True
    except Exception as failure:
        error = repr(failure)
    finally:
        result = dict(passed=passed, scope='Independent bounded whole physical identity/provider125 source/lifecycle review; producing reader owns actual capture observations',
                      provider_report=str(provider_path), provider_sha256=C.PINS.get(str(provider_path)),
                      counts=dict(counts), captures_opened=0, initializer_credit=False,
                      native_DllMain_credit=False, original_volatile_API_equality_claimed=False,
                      original_provider_stack_equality_claimed=False, whole_M4_complete=False, error=error, files=C.PINS)
        (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(dict(passed=passed, report_sha256=hashlib.sha256((out / 'report.json').read_bytes()).hexdigest(), counts=dict(counts), error=error)))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
