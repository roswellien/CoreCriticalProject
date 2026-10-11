"""Independent bounded review of the exact selected125 acceptance configuration.

Every gate receipt and typed predicate is checked. Declared payload identities
are conflict-normalized but not read; the final acceptance must physically hash
the entire union, including every retained historical capture archive.
"""
import ast
import collections
import hashlib
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import review_connected125_v2 as C

LABELS = set('parent game_recovery game_lifts game_callbacks game_static game_trace owner_source original_preparation original_build original_run original_validation original_review original_source tree_original_source native_preparation preparation build abi link resource build_review iteration lineage native source source_review source_closure provider provider_review paired paired_review pair_source pair_policy fixture_build fixture_execution fixture_source controls_build controls_execution controls controls_review controls_equivalence loaded_input_relation'.split())
BOUNDED = set('callback_execution full_CRT_attach full_native_MFC_attach native_MSVCP_DllMain MSVCP_lazy_or_Sleep_path native_menu native_Training whole_game_alias_liveness handler_execution exception_dispatch allocation_NULL_paths whole_original_provider_stack_equality whole_original_Windows_TIB_page_claimed general_virtual_dispatch nonzero_59FF80_pointee_path naked_throwing_Session_plus_caller_catch_ENV_metadata_guaranteed'.split())
EXTENT = dict(selected_roots=125, new_roots=1, original_sequences=6, original_phases=750,
              native_sequences=12, native_phases=1500, ordered_callbacks_per_sequence=97,
              observed_source_pages=43, MFC_allocations_per_sequence=65,
              string_allocations_per_sequence=19, live_ordinary_owners_per_sequence=85,
              live_critical_sections_per_sequence=5, new_requested24_allocations_per_sequence=7,
              new_actual_capacity32_allocations_per_sequence=7, tree_owned_accesses_per_sequence=172,
              tree_primary_publications_per_sequence=7, tree_Lockit_pairs_per_sequence=26,
              normal_game_FS_records_per_sequence=26, linked_literal_COFFs_per_level=371,
              compiled_objects_per_level=27, capture_objects_per_level=2, actual_linked_inputs_per_level=400)
FIELDS = ('files', 'physical_inputs', 'physical_dependencies', 'generated_sources', 'sources', 'tools', 'artifacts')


def normalized(path):
    return str(Path(path).resolve()).replace('\\', '/').casefold()


def value(row, name):
    for part in name.split('.'):
        row = row[int(part)] if isinstance(row, list) else row[part]
    return row


def has(report, path, identity):
    return any(normalized(p) == normalized(path) and digest == identity
               for field in FIELDS for p, digest in report.get(field, {}).items())


def main(configuration, name):
    path = Path(configuration).resolve()
    out = ROOT / 'reports/m4-tree-review' / name
    C.need(not out.exists(), 'Fresh independent configuration review')
    out.mkdir(parents=True)
    counts = collections.Counter()
    passed = False
    error = None
    union = {}
    gates = {}
    try:
        C.pin(__file__)
        C.pin(C.__file__)
        config = C.read(path, '5de1b79bc32d4d9aaf060ac80838cb734c6de7f4c71bafcd3f2a1baf391e90d2')
        accept_path = ROOT / 'tools/m4-joint-startup125/accept_v2.py'
        accept = C.pin(accept_path, 'f0994ae67ce3d07d110551196938fdcf278e7297b732f5aa0ef30a9927e74f37').read_text()
        previous_accept = C.pin(ROOT / 'tools/m4-joint-startup125/accept.py',
                                '74e8002d2a081790b997cd6389ecd78b0cd7b1f1d1288f08a3a4db2c64319d19').read_text()
        old_block = "        need(rows['original_source']['source_contract_sha256'] == old_interface['contracts_sha256'] and has(rows['original_source'], old_interface['contracts'], old_interface['contracts_sha256']), 'Fresh actual source uses exact unchanged native old-owner interface')\n"
        new_block = """        bridge_item = rows['parent']['gates']['owner_original']
        old_bridge = read(ROOT / bridge_item['path'], bridge_item['sha256']); absorb(old_bridge)
        original_contract_path = ROOT / 'reports/m4-lockit-source/owned-contracts-r1/report.json'
        original_contract_sha = rows['original_source']['source_contract_sha256']
        need(old_bridge['passed'] and old_bridge['original_source_contract_sha256'] == original_contract_sha and old_bridge['source_contract_sha256'] == old_interface['contracts_sha256'], 'Accepted physical original-to-native owner interface bridge')
        need(has(rows['original_source'], original_contract_path, original_contract_sha) and has(old_interface, original_contract_path, original_contract_sha) and has(old_bridge, old_interface['contracts'], old_interface['contracts_sha256']), 'Fresh actual source and unchanged native interface share exact bridged physical original contract')
        need(rows['original_source']['source_owned_contracts'] == old_bridge['source_owned_contracts'] == old_interface['owned_accesses'] == 32 and rows['original_source']['source_publication_contracts'] == old_bridge['source_publication_contracts'] == old_interface['publications'] == 8, 'Complete fresh original owner/publication corroborations to accepted interface')
"""
        C.need(previous_accept.count(old_block) == 1 and accept == previous_accept.replace(old_block, new_block),
               'Only additive accept_v2 change is the explicit accepted original-to-native metadata bridge')
        counts['exact_acceptor_bridge_delta'] = 1
        specification_path = ROOT / 'tools/m4-joint-startup125/specification.py'
        specification = C.pin(specification_path).read_text()
        C.pin(config['configuration_source'], config['configuration_source_sha256'])
        reviewed_spec = C.read(config['review_specification'], config['review_specification_sha256'])
        C.need(len(LABELS) == 42 and set(config['gates']) == set(reviewed_spec) == LABELS,
               'Exact independent complete42-gate selected125 inventory')
        C.need(config['gates'] == reviewed_spec and config['extent'] == EXTENT,
               'Final configuration freezes complete reviewed predicate specification and exact measured extent')
        C.need(set(config['bounded_scope']) == BOUNDED and all(v is False for v in config['bounded_scope'].values()),
               'All native game/attach/exception/volatile scope exclusions retained explicitly')
        tree = ast.parse(accept)
        declared = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                        and any(isinstance(target, ast.Name) and target.id == 'REQUIRED' for target in node.targets))
        C.need(declared == LABELS and "closure = verify_manifest(PINS)" in accept and
               "closure['metadata_only_cache_used'] is False" in accept and
               "need(len(reuse) == 166" in accept and
               'inventory_is_project_completion_percentage=False' in accept and
               'whole_M4_complete=False' in accept and 'native_game_launch_complete=False' in accept,
               'Reviewed actual acceptor requires full166 historical payload union rehash and preserves project scope')
        C.need("rows = ROWS |" in specification and "type(actual) is type(expected)" in specification,
               'Known41 plus exact final paired-review supplement without predicate type coercion')
        for label, item in config['gates'].items():
            C.need(set(item) == {'path', 'sha256', 'equal'} and len(item['equal']) >= 2,
                   'Each exact gate has substantial typed measured predicates')
            target = (ROOT / item['path']).resolve()
            C.need(target.is_relative_to(ROOT) and target.suffix == '.json', 'Each actual gate receipt is a named workspace JSON')
            report = C.read(target, item['sha256'])
            C.need(report['passed'] is True, 'Only genuinely passed current gate ' + label)
            for field, expected in item['equal'].items():
                actual = value(report, field)
                C.need(type(actual) is type(expected) and actual == expected, 'Every independent exact predicate ' + label + ':' + field)
                counts['typed_measured_predicates_reviewed'] += 1
            gates[label] = report
            for field in FIELDS:
                for dependency, identity in report.get(field, {}).items():
                    key = normalized(dependency)
                    C.need(isinstance(identity, str) and len(identity) == 64 and int(identity, 16) >= 0,
                           'Every retained declared dependency has an exact SHA256')
                    C.need(key not in union or union[key] == identity, 'No conflicting physical union identity')
                    union[key] = identity
            counts['passed_gate_receipts_reviewed'] += 1

        edges = [('paired', 'loaded_input_relation'), ('source_review', 'source'), ('source_closure', 'source'),
                 ('source_closure', 'provider'), ('provider_review', 'provider'), ('paired_review', 'paired'),
                 ('controls_review', 'controls'), ('controls', 'controls_execution'),
                 ('controls_equivalence', 'controls_build'), ('controls_equivalence', 'controls'),
                 ('controls_equivalence', 'build'), ('original_source', 'original_validation'),
                 ('original_review', 'original_validation'), ('build_review', 'abi'), ('build_review', 'link'),
                 ('build_review', 'resource'), ('build_review', 'fixture_source')]
        edges += [(label, 'build') for label in ('abi', 'link', 'resource')]
        edges += [('lineage', label) for label in ('native_preparation', 'preparation', 'build')]
        edges += [(label, 'native') for label in ('source', 'provider', 'paired')]
        for label, target in edges:
            item = config['gates'][target]
            C.need(has(gates[label], ROOT / item['path'], item['sha256']), 'Every actual current evidence edge ' + label + '->' + target)
            counts['exact_physical_evidence_edges'] += 1
        C.need(gates['parent']['connected_roots'] == 124 and gates['parent']['remaining_inventory_roots'] == 20 and
               gates['parent']['whole_M4_complete'] is False, 'Accepted124 inheritance is an initializer inventory count')
        for parent, child, field in [('native', 'build', 'build_sha256'), ('build', 'preparation', 'preparation_sha256'),
                                     ('preparation', 'native_preparation', 'native_preparation_sha256'),
                                     ('preparation', 'parent', 'parent_acceptance_sha256'),
                                     ('original_build', 'original_preparation', 'preparation_sha256'),
                                     ('original_run', 'original_build', 'build_sha256'),
                                     ('original_validation', 'original_build', 'build_sha256'),
                                     ('fixture_execution', 'fixture_build', 'build_sha256'),
                                     ('controls_execution', 'controls_build', 'build_sha256')]:
            C.need(gates[parent][field] == config['gates'][child]['sha256'], 'Every true execution/preparation parent edge')
            counts['actual_execution_lineage_edges'] += 1
        for relative, identity in C.EXPECTED.items():
            C.need(config['gates'][{'reports/m4-tree-native/preparation-r5/report.json':'native_preparation',
                                   'reports/m4-joint-startup125/preparation-r4/report.json':'preparation',
                                   'reports/m4-joint-startup125/build-r1/build.json':'build',
                                   'reports/m4-joint-startup125-root/execution-r1/report.json':'native'}[relative]]['sha256'] == identity,
                   'Exact physically reviewed current library and fresh actual full125 execution')
        C.need([row['level'] for row in gates['native']['levels']] == ['O0', 'O2'], 'Both genuine final native levels')
        for row in gates['controls_equivalence']['levels']:
            C.need(row['only_permitted_difference'] == [4, 8] and row['all_non_timestamp_bytes_equal'] is True and
                   row['code_data_relocation_symbol_bytes_equal'] is True and
                   all(4 <= offset < 8 for offset in row['actual_differing_offsets']) and
                   row['linked_literal_inputs'] == 371 and row['actual_compiler_dependencies'] == 481,
                   'Controls apply to final exact compiled library with only COFF timestamp bytes exempt')
        for label in ('preparation', 'build', 'native'):
            C.need(gates[label]['full_dependency_acceptance_rehash_required'] is True, 'Final full-rehash obligation retained')
            retained = gates[label]['inherited_capture_payload_hashes_reused']
            C.need(len(retained) == 166 and all(union.get(normalized(p)) == h for p, h in retained.items()),
                   'All166 historical capture identities retained in declared final union')
            counts['retained_historical_payload_identity_joins'] += len(retained)
        C.need(len(gates['preparation']['selected_order']) == 125 and len(gates['preparation']['registration_roots']) == 97 and
               gates['native_preparation']['new_roots'] == [0x4b7f70], 'Exact shortest next counted one-root closure')
        native = gates['native_preparation']
        C.need(native['live_owner_bound'] == 85 and native['exact_owned_causal_accesses'] == 172 and
               native['exact_primary_publications'] == 7 and native['normal_branch_only'] is True and
               native['native_DllMain_executed'] is False, 'Actual source-defined finite tree owner/path bounds')
        bridge_item = gates['parent']['gates']['owner_original']
        C.need(bridge_item['path'] == 'reports/m4-lockit-build-review/original-interface-r1/report.json' and
               bridge_item['sha256'] == '1de5a8634b09699e428805d558356c4d87456d8d26f291ddfd56924b7a7593a0',
               'Exact genuine accepted124 owner-original bridge receipt')
        bridge = C.read(ROOT / bridge_item['path'], bridge_item['sha256'])
        interface = C.read(native['owner_contract_report'], native['owner_contract_report_sha256'])
        source_path = ROOT / 'reports/m4-lockit-source/owned-contracts-r1/report.json'
        source_sha = gates['original_source']['source_contract_sha256']
        source = C.read(source_path, source_sha)
        contracts = C.read(interface['contracts'], interface['contracts_sha256'])
        C.need(source_sha == '8ca045fb36a503276b05223b4c9401792077e256dbf3c37691ecb9adb4e3a51a' and
               interface['contracts_sha256'] == '51e8f4ff329fda7f35b041f017d1445384ecda08906004b9366359a4bfb6af3f' and
               source_sha != interface['contracts_sha256'], 'Original source report and native serialization are distinct exact artifacts')
        C.need(bridge['passed'] is True and interface['passed'] is True and source['passed'] is True and
               bridge['original_source_contract_sha256'] == source_sha and
               bridge['source_contract_sha256'] == interface['contracts_sha256'] and
               bridge['source_interface_sha256'] == native['owner_contract_report_sha256'],
               'Accepted metadata bridge names both actual artifact identities and their interface')
        for report, target, identity in [(gates['original_source'], source_path, source_sha),
                                         (interface, source_path, source_sha),
                                         (bridge, interface['contracts'], interface['contracts_sha256'])]:
            C.need(has(report, target, identity), 'Physically authenticated original/native bridge edge')
            counts['original_native_contract_bridge_edges'] += 1
        C.need(gates['original_source']['source_owned_contracts'] == bridge['source_owned_contracts'] ==
               source['owned_accesses'] == interface['owned_accesses'] == 32 and
               gates['original_source']['source_publication_contracts'] == bridge['source_publication_contracts'] ==
               source['publications'] == interface['publications'] == 8, 'Entire source/serialization bridge extent remains32 accesses/eight publications')
        own_fields = ('root', 'pc', 'write', 'bytes', 'owner_root', 'owner_CALL_pc', 'owner_offset')
        pub_fields = ('root', 'CALL_pc', 'requested_size', 'object', 'publication', 'publication_PC', 'owner_root', 'owner_CALL_pc', 'owner_offset')
        def pinned_rows(report, relative):
            target = ROOT / relative
            identities = [identity for name, identity in report['files'].items() if normalized(name) == normalized(target)]
            C.need(len(identities) == 1, 'Exact physically bounded bridge source input')
            return C.read(target, identities[0])
        source_owned = pinned_rows(source, 'reports/m4-lockit-source/owned-contracts-r1/shared-owner-accesses.json')
        source_pub = pinned_rows(source, 'reports/m4-lockit-source/owned-contracts-r1/allocation-inputs.json')
        fields = lambda rows, order: [[int(row[key]) for key in order] for row in rows]
        C.need(set(contracts) == {'fs_owned_accesses', 'fs_inputs'} and
               fields(source_owned, own_fields) == contracts['fs_owned_accesses'] and len(source_owned) == 32 and
               fields(source_pub, pub_fields) == contracts['fs_inputs'] and len(source_pub) == 8,
               'Independent complete ordered serialization from original affine rows to native arrays')
        current_owned = pinned_rows(gates['original_source'], 'reports/m4-tree-original/old-Lockit-source-r3/original-source-owned-contract-corroborations.json')
        current_pub = pinned_rows(gates['original_source'], 'reports/m4-tree-original/old-Lockit-source-r3/original-source-publication-contract-corroborations.json')
        C.need(len(current_owned) == 192 and len(current_pub) == 48, 'All six fresh original125 branch corroboration inventories')
        for sequence in range(6):
            owned = [row for row in current_owned if row['sequence'] == sequence]
            pub = [row for row in current_pub if row['sequence'] == sequence]
            C.need(fields(owned, own_fields) == contracts['fs_owned_accesses'] and
                   fields(pub, pub_fields) == contracts['fs_inputs'] and
                   all(row['source_address'] == row['owner_pointer'] + row['owner_offset'] for row in owned),
                   'Every fresh original125 dynamic source observation retains exact native serialization')
            counts['fresh_original_bridge_access_corroborations'] += len(owned)
            counts['fresh_original_bridge_publication_corroborations'] += len(pub)
        for label in ('source', 'provider'):
            C.need(gates[label]['per_phase_BEFORE_machine_seed'] is False and gates[label]['candidate_AFTER_machine_seed'] is False,
                   'One bootstrap with persistent literal state, no per-phase or AFTER seed')
        paired = gates['paired']
        for field in ('blanket_page_mask', 'original_and_native_bytes_modified', 'whole_game_liveness_proven',
                      'Lockit_original_postRET_observed', 'Lockit_opaque_loaded_bytes_masked',
                      'loaded_input_opaque_pointer_targets_proven', 'loaded_input_native_DllMain_credit'):
            C.need(paired[field] is False, 'Finite actual paired scope preserves exclusion ' + field)
        C.need(paired['original_record_bytes'] == 356992 and paired['native_record_bytes'] == 159716 and
               paired['loaded_input_relation_report_sha256'] == config['gates']['loaded_input_relation']['sha256'],
               'Unchanged original/native ABI and exact independently reviewed opaque-input relation')
        review = gates['paired_review']['counts']
        for field, expected in dict(complete_paired_sequences=12, complete_paired_phases=1500,
                                    tree_owned_operand_pairs=2064, tree_whole_capacity_pairs=84,
                                    tree_scratch_role_pairs=312, tree_complete12B_FS_pairs=168,
                                    tree_saved_local_byte_pairs=24).items():
            C.need(review[field] == expected, 'Concrete independent paired tree seam extent')
        counts['declared_conflict_free_union_identities'] = len(union)
        passed = True
    except BaseException as exc:
        error = repr(exc)
        raise
    finally:
        artifact = out / 'reviewed-predicates-and-union.json'
        artifact.write_text(json.dumps(dict(gates=locals().get('config', {}).get('gates', {}),
                                           declared_dependency_identities=union), indent=2) + '\n')
        C.pin(artifact)
        report = dict(passed=passed, error=error, gates_reviewed=counts['passed_gate_receipts_reviewed'],
                      scope='Independent exact42-gate configuration/predicate/lineage/library/scope review; complete declared identity union retained; actual all-payload rehash remains mandatory final acceptance',
                      counts=dict(counts), initializer_credit=False, whole_M4_complete=False,
                      capture_archives_opened=0, payload_hashes_physically_reverified=False,
                      final_full_union_rehash_required=True, files=C.PINS)
        target = out / 'report.json'
        target.write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(dict(passed=passed, sha256=hashlib.sha256(target.read_bytes()).hexdigest(), gates_reviewed=report['gates_reviewed'], counts=dict(counts))))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
