"""Bounded read-only policy disposition; never execute a gate or inventory."""
from pathlib import Path
import hashlib, json

R = Path(__file__).resolve().parents[2]
OUT = R / 'reports/m4-controls-terminal-composite/field-disposition-r1'

def digest(p):
    assert p.stat().st_size < 2 * 1024 * 1024, 'Small source/metadata only'
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not OUT.exists(), 'Fresh preparation only'
    paths = [
        'reports/m4-138-criteria-frontier/terminal45-typed-recipe-r1/pending45-terminal-field-mapping.json',
        'reports/m4-joint-startup131-root/configuration-r1/configuration.json',
        'tools/m4-controls-terminal-composite/finalize45_v3.py',
        'tools/m4-controls-terminal-composite/build_v7.py',
        'tools/m4-mfc1168-native/verify_connected_controls.py',
        'tools/m4-mfc1168-native/verify_connected_controls_v5.py',
        'tools/m4-tree-review/review_mfc131_controls.py',
        'reports/m4-138-preresource-strict-review/preparation-r5/verify_case_v5.py',
        'reports/m4-controls-terminal-composite/root-current16-finite-review-r1/current16-semantic-review.json',
        'reports/m4-controls-terminal-composite/root-current16-finite-review-r1/current8-scope-review.json',
    ]
    files = {str(R / p): digest(R / p) for p in paths}
    files[str(Path(__file__).resolve())] = digest(Path(__file__).resolve())
    mapping = json.loads((R / paths[0]).read_bytes())
    baseline = json.loads((R / paths[1]).read_bytes())
    gates = baseline['gates']
    assert len(mapping) == 45
    known = {
        'actual_precise_denials': 24, 'whole_retry_vectors': 386172,
        'whole_caller_FX512_ENV28': 48, 'whole_borrowed_capacity_prefixes': 60,
        'whole_borrowed_guestCS24_prefixes': 12, 'actual_API_identity_CS40_sides': 208,
        'actual_owned_lifecycles': 12, 'actual_unchanged_poisoned_retries': 24,
        'pre_resource_refusals': 12, 'recorded_rejected_source_write_payloads': 2,
        'source_TLS_refusal_frame64': 2,
    }
    physical = {
        'whole_intended_protected_IAT_mutation_repairs': 2,
        'whole_diagnostic_only_delta': 1, 'whole_authored_public_faults': 12,
        'whole_true_source_entry_observer': 1, 'actual_compiler_TLS_cells': 56,
        'whole_linked_control_functions': 7,
        'entry_observer_inlined_in_whole_MFC_entry': 1,
    }
    rows = []
    for index, m in enumerate(mapping, 1):
        gate, field = m['gate'], m['baseline_field']
        equal = gates[gate]['equal']
        assert field in equal and type(equal[field]).__name__ == m['baseline_type']
        assert equal[field] == m['baseline_expected']
        leaf = field.split('.')[-1]
        support, value, need, exclusion = '', None, '', ''
        if gate == 'controls_preparation':
            support = 'Same legacy12 source contract plus separate current8 source contract and observation limits'
            value = 12 if leaf == 'control_cases' else False
            need = 'Actual composite preparation with exact f413/e064 current8 and 8a322/9a656 legacy12 edges; independently reviewed preparation source schema'
            exclusion = '12 is legacy fault modes, not current8 modes or 40 executed cases. False private/permission claims cannot be flipped.'
        elif gate == 'controls_prelaunch':
            support = 'Actual ROOT complete7 physical receipt 4a88d2c69f550221f553267af1a2eb5a569ccb8c1c9d7cf1ed4be859c8616212'
            value = physical[leaf]
            need = 'Whole composite source/build/prelaunch joins to this same legacy12 receipt, actual compiler/TLS ownership and whole linked functions'
            exclusion = 'No borrowed current8 replacement. TLS56 is initialized legacy compiler cells, not TLS API calls, CS size, or owner1 cell. Seven are whole function bodies, not 15 CALL joins.'
        elif field.startswith('counts.') and leaf in known:
            support = 'Actual legacy24 aggregate d3f4c2352cbf957088d885f2a8f5d21268cf86efc002556994b6a71c4d42e8c9'
            if leaf in ('whole_borrowed_guestCS24_prefixes', 'source_TLS_refusal_frame64'):
                support = 'Actual same-legacy24 named supplement 88bb674315463694c75fcd21c62a0f3bf5151a2ba5a55149994e1489074f5265'
            value = known[leaf]
            need = 'Reproduce exact per-case source/semantic counters and same case inventories in actual composite; fresh independent scoped whole-byte review'
            exclusion = 'Legacy24 finite predicates only; current16 supplemental observations and manual font cleanup do not establish these legacy source-derived capacity/TLS frame counts.'
            if leaf == 'whole_caller_FX512_ENV28':
                exclusion += ' Entire 512B FX/28B ENV denial/retry hardware equality; not all hidden caller/private frames.'
            if leaf == 'whole_borrowed_guestCS24_prefixes':
                exclusion += ' Whole original guest CS24, distinct from native CS40.'
            if leaf == 'source_TLS_refusal_frame64':
                exclusion += ' Two named legacy zero-index source-derived TLS call frames, not every API/bootstrap frame.'
        elif leaf == 'whole_export_targets_authenticated':
            support = 'Future distinct scoped raw union: all actual legacy24 payloads plus actual current16 10691866 raw entries'
            need = 'Actual SQLite raw scoped/case count, exact terminal case inventory, complete physical byte/size hashes and independent composite expansion'
            exclusion = 'Unknown until actual composite. Not dependency rows, retry count, or current16 count alone; no guessed addition.'
        elif leaf == 'execution_sha256':
            support = 'Actual current8 execution 43d8a2a8e56e6d6a0286236685b16fc6e36b806ebcc8fc6199d49c95e69e0863 with separate legacy24 execution lineage'
            value = '43d8a2a8e56e6d6a0286236685b16fc6e36b806ebcc8fc6199d49c95e69e0863'
            need = 'Exact actual composer schema and source graph proving all old24 worker/build/preparation executions separately'
            exclusion = 'This field identifies current8 production; it does not relabel legacy12/24 execution or old semantic producer 88e0.'
        elif leaf == 'controls_verification_sha256':
            support = 'Future independent controls_review exact edge to NEW actual composite controls'
            need = 'Fresh independent actual review; controls_verification_sha256 and controls_sha256 both equal new controls SHA; expanded scoped union and all 45 individual reviews'
            exclusion = 'Cannot reuse old 88e0, current16 raw2a008, or author composite assertion as independent review.'
        elif leaf in ('whole_old_registry_private_retry_claim', 'whole_permissions_retry_claim'):
            support = 'Actual old24 finite scopes and current16 ROOT scope9c79f74002c7b8630e699b4687fc987e7edfcd12d31f3ec53f9be5deae9fa6e3'
            value = False
            need = 'Actual composite preserves False; independent scoped physical review'
            exclusion = 'Captured observed private retry equality never implies all hidden private objects or complete memory permission state.'
        else:
            support = 'Closed actual component receipts; future whole composite producer and independent scoped expansion'
            value = m['baseline_expected']
            need = 'Actual same-input composite terminal, closed SQLite/readers and exact raw inventories; independent controls review for review-gate fields'
            exclusion = 'passed and closed are scoped predicates, not source bootstrap/teardown, full write prediction, native game execution, or function credit.'
        rows.append(dict(index=index, gate=gate, field=field,
                         baseline_type=m['baseline_type'], baseline_expected=m['baseline_expected'],
                         existing_support=support, supported_value_before_composer=value,
                         required_actual_next_evidence=need, scope_exclusion=exclusion,
                         disposition='support_identified_actual_composite_and_independent_review_pending',
                         allowance=False, accepted_function_credit=0))
    assert len(rows) == 45 and len({(r['gate'],r['field']) for r in rows}) == 45
    OUT.mkdir(parents=True)
    (OUT / 'per-field-disposition.json').write_text(json.dumps(rows, indent=2)+'\n')
    result = dict(prepared=True, scope='Read-only 45-field acceptance-scope diagnosis',
                  fields=45, accepted131_baseline_values_and_types_checked=True,
                  current16_full_committed_write_prediction_required_by_any_of_45=False,
                  current16_source_bootstrap_or_callback_cleanup_required_by_any_of_45=False,
                  these_exclusions_can_replace_legacy24_source_predicates=False,
                  all45_closed=False, composite_executed=False, checker_executed=False,
                  allowance_created=False, accepted_function_credit=0,
                  finalizer_limit='finalize45_v3 authenticates typed ROOT assertions; physical_domain/reason text is not executable source/semantic proof. Actual independent scoped expansion and strict graph still required.',
                  additional_review_requirement='The independent review must expose both controls_sha256 and controls_verification_sha256 equal the actual NEW controls SHA; finalizer checks the first, retained strict semantic edge checks the second.',
                  next_step='ROOT review completed manifest/build7 and actual scoped source roles; one admitted composite build with whole final byte union, followed by independent scoped expansion/45-field review. Do not run finalizer/config/checker or mint allowance before those terminal receipts.',
                  files=files)
    files[str(OUT / 'per-field-disposition.json')] = digest(OUT / 'per-field-disposition.json')
    (OUT / 'preparation-only.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(preparation=str(OUT / 'preparation-only.json'),sha256=digest(OUT / 'preparation-only.json'))))

if __name__ == '__main__':
    main()
