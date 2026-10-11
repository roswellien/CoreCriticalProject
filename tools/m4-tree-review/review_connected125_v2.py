"""Independent light review of the final persistent125 source proof.

Only sealed bounded JSON, source tools and physical provider inputs are read.
The producing source observer owns actual archive execution/equality evidence.
"""
import collections
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
PINS = {}
EXPECTED = {
    'reports/m4-tree-native/preparation-r5/report.json': '9b6c7ab64a42dd67d26e73a7b4357063729085a808173b2818e704430386fef2',
    'reports/m4-joint-startup125/preparation-r4/report.json': '243b6f4c86dc2b966789e23faed4a10fe2efa62ba51f43e854fa843acde392e7',
    'reports/m4-joint-startup125/build-r1/build.json': 'cdb5b9ca08e4e66dae276fa783bc59b5944e8435113fe9bb65a73cc53f218165',
    'reports/m4-joint-startup125-root/execution-r1/report.json': 'e384b6271c43f2e2e8d5a88f1a09e0940c85f111f2455744ad45de30ba73d8a8',
}


def need(value, message):
    if not value:
        raise ValueError(message)


def pin(path, digest=None):
    path = Path(path).resolve()
    need(path.suffix not in ('.mwb', '.zip'), 'No archive/capture reader in independent light review')
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    need(digest is None or actual == digest, 'Exact current light input ' + str(path))
    need(str(path) not in PINS or PINS[str(path)] == actual, 'Immutable bounded review input')
    PINS[str(path)] = actual
    return path


def read(path, digest=None):
    path = pin(path, digest)
    need(path.stat().st_size <= 64 * 1024 * 1024, 'Bounded emitted proof')
    return json.loads(path.read_bytes())


def lineage(report):
    labels = {'execution': 'reports/m4-joint-startup125-root/execution-r1/report.json',
              'build': 'reports/m4-joint-startup125/build-r1/build.json',
              'joint_preparation': 'reports/m4-joint-startup125/preparation-r4/report.json',
              'native_preparation': 'reports/m4-tree-native/preparation-r5/report.json'}
    need(report['passed'], 'Current source proof passed')
    for key, relative in labels.items():
        target = (ROOT / relative).resolve()
        need(Path(report['executed_lineage'][key]).resolve() == target, 'Exact fresh lineage ' + key)
        need(report['files'][str(target)] == EXPECTED[relative], 'Source proof binds current physical lineage')
        read(target, EXPECTED[relative])
    need(not report['per_phase_BEFORE_machine_seed'] and not report['candidate_AFTER_machine_seed'] and
         not report['paired_original_game_equivalence'] and not report['initializer_credit'] and
         not report['whole_M4_complete'] and report['loaded_state2_source_input'] and
         not report['native_CS40_opaque_copy'] and report['guest_CS24_semantic_output'] and
         not report['native_DllMain_credit'], 'Exact finite source/provider scope')


def output(report, folder, name):
    path = (folder / name).resolve()
    return read(path, report['files'][str(path)])


def main(source_path, name):
    source_path = Path(source_path).resolve()
    out = ROOT / 'reports/m4-tree-review' / name
    need(not out.exists(), 'Fresh source review revision')
    out.mkdir(parents=True)
    counts = collections.Counter()
    passed = False
    error = None
    try:
        pin(__file__)
        report = read(source_path)
        lineage(report)
        needed = ['tools/m4-tree-source/compare_connected125_v3.py', 'tools/m4-tree-source/game_model_v4.py',
                  'tools/m4-tree-source/game_model_v3.py', 'tools/m4-tree-source/game_model.py',
                  'tools/m4-tree-source/responses125.py', 'tools/m4-tree-source/native_tree_relations_v4.py',
                  'tools/m4-tree-source/continuity125.py', 'tools/m4-lockit-source/bridge_v2.py',
                  'tools/m4-lockit-source/identity_records.py', 'tools/m4-lockit-source/game_model.py',
                  'tools/m4-lockit-source/capture.py',
                  'tools/m4-onexit-review/provider_bridge.py', 'tools/m4-onexit-review/provider_capture.py',
                  'tools/m4-onexit-review/provider_responses_v2.py', 'tools/m4-onexit-review/provider_responses.py']
        for relative in needed:
            path = (ROOT / relative).resolve()
            need(str(path) in report['files'], 'Every executed current trust-boundary model is pinned')
            pin(path, report['files'][str(path)])
            counts['reviewed_source_boundary_tools'] += 1
        source_text = (ROOT / needed[0]).read_text()
        need("len(machine.lockit_state_reads)==34" in source_text and
             "len(machine.lockit_import_proofs)==8" in source_text and
             "b[76:116]" in source_text and "b[116:628]" in source_text and
             "machine.tree_result()" in source_text and "T.verify(a,stem,result" in source_text,
             'Explicit34 source API calls retain inherited8 imports and exact immutable CPU/FX slices')
        for key, expected in {'persistent_phases': 1500, 'whole_page_BEFORE': 64500,
                              'whole_page_AFTER': 64500, 'literal_registration_roots': 1164,
                              'persistent125_sequences': 12, 'actual_native_CS_resource_associations': 12,
                              'literal_Lockit_CALL_RET_pairs': 408,
                              'actual_native_CS40_source_API_relations': 408,
                              'native_FS_source_accesses': 936,
                              'actual_native12B_source_relations': 624,
                              'whole_native_tree_owner_backings': 84}.items():
            need(report['counts'][key] == expected, 'Exact measured current source extent ' + key)
        cases = {(level, sequence) for level in ('O0', 'O2') for sequence in range(6)}
        phases = output(report, source_path.parent, 'phases.json')
        need(len(phases) == 1500 and {(r['level'], r['sequence'], r['phase']) for r in phases} ==
             {(level, sequence, phase) for level, sequence in cases for phase in range(125)},
             'Every actual current phase once')
        tree = output(report, source_path.parent, 'Tree-source-derivations.json')
        need(len(tree) == 12 and {(r['level'], r['sequence']) for r in tree} == cases,
             'Every actual full125 source tree once')
        contracts = read(ROOT / 'reports/m4-tree-source/dynamic-contracts-r1/normal-contracts.json',
                         'fbdd6e79dc26328ae2bd6a2e02d264971eaa190251d589f085904ffd9486829c')
        helpers = ROOT / 'tools/m4-tree-review/pair_source_review_v2.py'
        spec = importlib.util.spec_from_file_location('independent125_types', pin(helpers))
        types = importlib.util.module_from_spec(spec); spec.loader.exec_module(types)
        helper = ROOT / 'tools/m4-tree-paired/tree_relations_v2.py'
        spec = importlib.util.spec_from_file_location('independent125_local_provenance', pin(helper))
        local = importlib.util.module_from_spec(spec); spec.loader.exec_module(local)
        for row in tree:
            source = row['source']; owners = source['owners']
            need(not source['candidate_AFTER_seed'] and len(owners) == 7, 'Own branch literal seven-role tree')
            need(len(source['owned_accesses']) == 172 and len(source['publications']) == 7 and
                 len(source['FS_frames']) == 7 and len(source['Lockit_calls']) == 26,
                 'Current repeated source access/publication/FS/Lockit extent')
            for access, contract in zip(source['owned_accesses'], contracts['owned_causal_order']):
                need((access['pc'], access['owner_index'], access['offset'], access['bytes'], bool(access['write'])) ==
                     (contract['pc'], contract['owner_role_index'], contract['offset'], contract['bytes'], contract['write']),
                     'Every current tree operand retains exact original source role/PC/width/causal occurrence')
                types.own_value(access, owners, contract['value_owner_role_index'])
                counts['reviewed_current_typed_owned_operands'] += 1
            saved = [r for r in source['static_field_writes'] if (r['pc'], r['address'], r['width']) in local.LOCAL_BYTES]
            need(len(saved) == 2, 'Exactly two current literal saved local stores')
            for write in saved:
                local.local_provenance(source, write)
                counts['reviewed_current_saved_local_read_store_joins'] += 1
            for owner in owners:
                need(len(bytes.fromhex(owner['initial_hex'])) == len(bytes.fromhex(owner['source_final_hex'])) == 32,
                     'Whole own backing extent with authentic acquired tail')
                counts['reviewed_current_whole_capacity_exports'] += 1
            # Whole dynamic joins are measured by the actual producing observer,
            # with full16Q records and complete API checkpoints kept separate.
            for key, expected in {'whole_owned_access_relations': 172, 'whole_publication_relations': 7,
                                  'actual_generation_occurrence_joins': 7, 'whole12B_FS_relations': 14,
                                  'whole_native_scratch_contexts': 26}.items():
                need(row['counts'][key] == expected, 'Whole actual current tree relation ' + key)
        lockit = output(report, source_path.parent, 'Lockit-source-derivations.json')
        need(len(lockit) == 12 and {(r['level'], r['sequence']) for r in lockit} == cases,
             'All actual source provider cases')
        for row in lockit:
            need(len(row['imports']) == 8 and len(row['state_reads']) == len(row['API_relations']) == 34,
                 'Old imports and every newly reused literal provider state read/API remain distinct')
            need(all(r[1:] == [0x78145658, 2] for r in row['state_reads']), 'Only genuine loaded state2 FastPath admitted')
            counts['reviewed_current_source_state_reads'] += 34
        passed = True
    except Exception as failure:
        error = repr(failure)
    finally:
        result = dict(passed=passed, scope='Independent bounded current125 source/typed tree observer review; producing gate owns full capture consumption',
                      counts=dict(counts), source_report=str(source_path), source_sha256=PINS.get(str(source_path)),
                      exact_loaded_fastpath_only=True, native_whole_stack_source_comparison=True,
                      captures_opened=0, independent_capture_reexecution=False, initializer_credit=False,
                      whole_M4_complete=False, error=error, files=PINS)
        (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(dict(passed=passed, report_sha256=hashlib.sha256((out / 'report.json').read_bytes()).hexdigest(), counts=dict(counts), error=error)))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
