"""Source-only current141 paired frontier; no model/import/reader execution."""
from pathlib import Path
import ast, hashlib, json

R = Path(__file__).resolve().parents[2]

def main():
    out = R / 'reports/m4-startup141-paired/current-frontier-r2'
    assert not out.exists()
    names = [
        'reports/m4-startup138-paired/comparer-preparation-r15/paired138.py',
        'reports/m4-startup138-paired/configuration-r8/configuration.json',
        'tools/m4-startup141-paired/current_identity_v1.py',
        'tools/m4-startup141-paired/constructor_relations141_v1.py',
        'tools/m4-startup141-paired/constructor_structural54_pair_v1.py',
        'tools/m4-141-consumer-review/prepare_paired141_readiness_v1.py',
        'tools/m4-startup141-paired/prepare_current_plan_v1.py',
    ]
    files = {}
    for name in names:
        p = R / name
        assert p.stat().st_size < 1024 * 1024
        raw = p.read_bytes()
        files[str(p)] = hashlib.sha256(raw).hexdigest()
        if p.suffix == '.py':
            ast.parse(raw.decode('utf-8-sig'))
    parent = R / names[0]
    assert files[str(parent)] == '7d3aa767576a4b27ed86cb3b4932cb7663f26a9313e3539611cbfe94654f956d'
    text = parent.read_text()
    assert "if page==0x20001000:continue" in text
    assert "if page==0x5f4cc000:" in text
    assert "whole_nonstack_page_relations']==221904" in text
    assert "separate_whole_loader_page_input_relations']==3312" in text
    assert "whole45_nonstack_page_endpoint_relations']==225216" in text
    phases = 2 * 6 * 141
    coverage = dict(paired_sequences=12, paired_phases=phases,
                    source_pages_per_side=69, source_page_endpoints=phases*2*69,
                    inherited_stack_pages_outside_crossbranch_page_loop=phases*2,
                    separate_whole_loader_page_input_relations=phases*2,
                    ordinary_whole_nonstack_page_relations=phases*2*67,
                    total_nonstack_page_endpoint_relations=phases*2*68,
                    separate_global5F2000_page_endpoints=phases*2,
                    current_original_phases=6*141,
                    current_original_global5F2000_endpoints=6*141*2)
    assert coverage['ordinary_whole_nonstack_page_relations']==226728
    assert coverage['total_nonstack_page_endpoint_relations']==230112
    # These identities were supplied by ROOT or existing source declarations;
    # this source-only preparation does not rehash or reopen their inventories.
    identities = dict(
        original_strict3='e981f00f520ce83019bdb7c77fef740871de14f24c2e9aee0052293fcec1a58c',
        original18='8f910be42c5be26bf6e41260361b61b3ec258aefedf2cbdaabe35e3992498899',
        native141_carried6='8684b0a3219a72a3a0712dd99170e0c584ee0c5cd438effcd9632a83bc3d72b3',
        native141_execution2='536eeb8c62c9de8276e46d727907faea417b91a22c2cbae2b3cdbca80da7c2b6',
        native36_source8='20c0105497eeab094c67e37cdd7f5db7ea94095e4ca0386a1f702a313ede8f96',
        structural54_pair2='221f7645e5a418af17d9c92754850a5e2775ab63445a1911ae120c6f4f7158ce')
    blockers = [
        dict(domain='native_input_carry_FS', next='Finish independent previous-checkpoint region/initial-FS head provenance policy for actual native36 input; retain source-readiness ownership.', closed=False),
        dict(domain='current_original_family_view', next='Typed child view of actual original7 constructor18/format24/old4-24/MFC6/widget42/tree6 artifacts to inherited53 consumer roles; no old138 artifact substitution or synthesized source rows.', closed=False),
        dict(domain='loaded_input_CRT', next='Fresh actual current141 bootstrap/144-cell named import and full CRT input footprint policy, including every constructor source/API buffer and current module ownership; preserve whole-page unused-input and source-access proofs.', closed=False),
        dict(domain='allphase_global5F2000', next='Typed source-owned owner publication and untouched/carry relation at all3384 original/native BEFORE/AFTER endpoints; structural54 currently compares constructor-only source-computed global output, not every carried phase.', closed=False),
        dict(domain='owner_registry_cleanup', next='Exact111 callback vector, real growth births/full capacities,74 MFC owner chronology, manual cleanup and source callback scope; retain separate original/native own-tail conservation for all intervening families.', closed=False),
        dict(domain='FS_domains', next='Preserve normal28/56 domain and separately constructor7 frames/14 raw12 records/21 events; no fabricated global35/70 merger.', closed=False),
        dict(domain='rebased_observer_source_stack', next='Use actual current28000000 worker and11 PUSHFD source-defined/undefined flags, ordered shadow writes and live read/API buffer transparency. Rebind full observer/module spans, not ancestor18000000 hashes.', closed=False),
        dict(domain='allphase_CPU_FX_ENV', next='Keep inherited GPR/flags/FX/ENV policy with source/table-derived SPI seam. Independently derive any current widget original API metadata clear vs native relation; original own predicted ENV clear is not paired equality or a new byte mask.', closed=False),
        dict(domain='preserved53_and_config', next='Exact finite inverses for main and phase-sensitive helpers, current execution.runs schema, current original strict export only, full admitted physical closure and fail-closed indirect imports before ordinary readers.', closed=False),
        dict(domain='actual_pair_and_acceptance', next='One ROOT-admitted ordinary paired1692 consumer and complete independent paired review; then strict acceptance retaining accepted138 parent gates plus genuine three-root criteria. Passing source/structural helpers cannot add credit.', closed=False),
    ]
    out.mkdir(parents=True)
    for leaf, obj in [('coverage-domains.json',coverage),('remaining-gates.json',blockers),('declared-current-identities.json',identities)]:
        p=out/leaf;p.write_text(json.dumps(obj,indent=2)+'\n');files[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    files[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result = dict(prepared_only=True, source_only=True,
        inherited53_parent_preserved=True, current_full141_comparer_exists=False,
        identities_declared_not_remeasured=True, full141_pair_gate_closed=False,
        narrow_path_hash_only_main_adaptation_sufficient=False,
        current_original7_and_native6_passes_are_not_pair_acceptance=True,
        structural54_complete_constructor_acceptance_claim=False,
        source_models_executed=False, production_imports_executed=False,
        ordinary_export_reader_opened=False, canonical_reader_opened=False,
        worker_launched=False, accepted_function_credit=0,
        next_least_cost_step='Independent current native36 input carry/FS review, then immutable original7 child-view and current CRT/widget ENV policy preparation; these permit a whole53-preserving full comparer derivative without relaxing scope.', files=files)
    q=out/'preparation-only.json';q.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(path=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest())))

if __name__=='__main__':
    main()
