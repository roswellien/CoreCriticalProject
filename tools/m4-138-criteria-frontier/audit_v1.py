"""Bounded ordinary criterion recommendations; never an acceptance configuration."""
from pathlib import Path
import collections, hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[2]
PINS = {}
def pin(p, expected=None):
    p = Path(p).resolve()
    assert p.is_relative_to(R) or p == Path(sys.executable).resolve()
    assert p.suffix.lower() not in ('.mwb', '.mwi', '.zip') and p.name != 'transport.json'
    assert p.stat().st_size < 32*1024*1024, 'Only bounded ordinary input'
    with p.open('rb') as f: h = hashlib.file_digest(f, 'sha256').hexdigest()
    assert expected is None or h == expected, str(p)
    assert str(p) not in PINS or PINS[str(p)] == h
    PINS[str(p)] = h
    return p
def read(p, expected=None): return json.loads(pin(R/p, expected).read_bytes())
def at(v, field):
    for part in field.split('.'): v = v[int(part)] if isinstance(v,list) else v[part]
    return v
def main(name):
    out = R/'reports/m4-138-criteria-frontier'/name
    assert not out.exists()
    baseline = read('reports/m4-joint-startup131-root/configuration-r1/configuration.json','ba2fbf12ddedbac6c57ffb1ef6f14ade3712319a368671585daddd5f011c5ef7')
    proposal = read('reports/m4-138-controls-review/criterion-delta-proposal-r2/criterion-841-proposal.json','b921d266c3427130c431319329d0971246e0767a7a1efbfb7ae0c689852f3a94')
    bindings = read('reports/m4-138-controls-review/criterion-delta-proposal-r2/candidate-33-gate-bindings.json','ce66ab5fbf6da13e48ef839647add2f410e46ba63d374152753fd6574fa7605f')
    rows = [dict(x) for x in proposal if x['status']=='unresolved' and x['gate']!='paired_review']
    assert len(rows)==133 and sum(x['status']=='unresolved' for x in proposal)==196
    closure = read('reports/m4-tree-review/source138-closure-r1/report.json','fc2453e5a9ff713d122f73e3a165edbdcc43da1b31c18f8bae787e6d6b43b38b')
    closure_code = pin(R/'tools/m4-138-controls-review/seal_source6_closure.py').read_text()
    assert closure['passed'] and closure['source_provider_sha256']=='40822c09a868ff39de882a4d70dbe7aa5b0949f8e2c4cf4bf8253d3bf4f92052'
    assert "current_preflight=read(R/'reports/m4-tree-review/joint131-source-preflight-r4/report.json'" in closure_code
    assert "for record in(current_preparation,current_preflight):" in closure_code
    historical = {}
    for label in ('source_preflight','source_legacy_flags'):
        g = baseline['gates'][label]; b = read(g['path'],g['sha256']); historical[label]=b
        for p,h in b['files'].items():
            assert closure['files'].get(p)==h, 'Current closure retains complete historical proof input'
            pin(p,h)
        for f,v in g['equal'].items(): assert type(at(b,f)) is type(v) and at(b,f)==v
    source_entry = pin(R/'reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py',closure['files'][str((R/'reports/m4-joint-startup138-source/preparation-r11/compare_provider138.py').resolve())]).read_text()
    assert "J=load('persistent54_accepted27',ROOT/'tools/m4-joint-startup27-review/observe.py')" in source_entry
    assert 'm,c,inst,schedule=J.models()' in source_entry
    # Pure source-operand review of the current six original MFC derivations.
    # No machine, API, archive, or capture reader is constructed.
    pp = read(bindings['pair_preparation']['path'], bindings['pair_preparation']['sha256'])
    hp = pin(R/'tools/m4-startup131-paired/mfc_relations_v2.py','4ab2c11a89b47d8f380d348dab8a548d3a71c529ecafc25282d362064c0dc67b')
    assert pp['files'][str(hp)]==PINS[str(hp)]
    pin(pp['comparer'],pp['comparer_sha256'])
    spec=importlib.util.spec_from_file_location('frontier_finite_mfc_relations',hp)
    M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
    current_original=read('reports/m4-startup138-original/mfc-source-r2/report.json','6a4e28040c31aebbc108904cb6a574d964aa28f045ff446f1362deaedd260801')
    dp=R/'reports/m4-startup138-original/mfc-source-r2/source-derivations.json'
    derived=json.loads(pin(dp,current_original['files'][str(dp)]).read_bytes())
    assert len(derived)==6
    counts=collections.Counter(); witnesses=[]
    for row in derived:
        assert (row['root'],row['phase'])==(M.ROOT,13) and not row['source_AFTER_seed'] and row['actual_prefix_carried_BEFORE']
        a=row['source_accesses']; owners=row['source_borrowed_backings']; by={x['role']:x for x in owners}
        assert len(row['source_PCs'])==142 and len(a)==113 and tuple(by)==M.ROLES
        assert tuple(x['PC'] for x in row['source_normal_boundary_relations'])==M.PCS and len(row['source_API_relations'])==4
        for i,role in M.ROLE_VALUES.items(): assert a[i][2]==by[role]['address'];counts['original_role_value_corroborations']+=1
        for i in M.FS_VALUES: assert a[i][2]==row['source_FS_BEFORE'] and a[i][3]==4;counts['original_FS_value_corroborations']+=1
        for i in M.IMPORT_ACCESSES: assert a[i][3:]==[4,0];counts['original_import_operand_corroborations']+=1
        assert a[45][0]==0x5f4010c3 and a[45][2]==by['global-object']['address']
        for owner in owners: M.own_byteflow(owner,a);counts['original_whole_role_byteflows_reviewed']+=1
        assert row['source_FS_BEFORE']==row['source_FS_AFTER'] and len(row['source_FS_writes'])==2
        for api in row['source_API_relations']: assert api['no_postRET_memory_seed'] and not api['intermediate_source_FS_observation']
        counts['genuine_source_cases_reviewed']+=1;counts['genuine_source_PC_occurrences_reviewed']+=len(row['source_PCs']);counts['genuine_source_operands_reviewed']+=len(a)
        witnesses.append(dict(sequence=row['sequence'],root=row['root'],phase=row['phase'],source_PCs=row['source_PCs'],imports={str(i):a[i] for i in M.IMPORT_ACCESSES},role_values={str(i):a[i] for i in M.ROLE_VALUES},FS_values={str(i):a[i] for i in M.FS_VALUES}))
    metadata=read('reports/m4-138-controls-review/readiness-r1/report.json')['receipt_metadata']
    assert metadata['passed'] and metadata['execution_sha256']==bindings['controls_execution']['sha256']
    assert metadata['whole_prior131_semantic_source_equivalence_claimed'] is False
    pin(R/'tools/m4-joint-startup138/check_context_controls_v4.py')
    pin(R/'tools/m4-joint-startup138/check_context_controls_v3.py')
    pin(R/'tools/m4-joint-startup138/controls_main.cpp')
    link=read('reports/m4-138-controls-review/current-link-join-r1/report.json')
    assert link['passed'] and link['positive_execution_sha256']==bindings['native_execution']['sha256'] and link['controls_execution_sha256']==bindings['controls_execution']['sha256']
    current={label:read(g['path'],g['sha256']) for label,g in bindings.items() if any(x['gate']==label for x in rows) and label not in ('controls','controls_review') and g['path']}
    rename={('native_execution','current131_acceptance'):'current138_acceptance',('native_prelaunch','counts.all_physical_initializer_table_pairs'):'counts.physical_sorted_initializer_slots',('original_prelaunch','counts.physical_selected_pairs'):'counts.physical_selected_initializer_cells',('source_provider','counts.persistent131_sequences'):'counts.persistent138_sequences'}
    for x in rows:
        label,f,old=x['gate'],x['baseline_field'],x['baseline_expected']
        x.update(audit_status='missing_same_domain_measurement',recommendation='Retain obligation; derive exact named physical subdomain from current inputs. Broader totals, passed, or a different observation scope cannot replace this predicate.',candidate=None)
        if label in historical:
            x.update(audit_status='exact_historical_scope_reuse_candidate',candidate=dict(path=baseline['gates'][label]['path'],sha256=baseline['gates'][label]['sha256'],field=f,expected=old),recommendation='Retain exact historical gate and typed value in its unchanged scope; source138 closure physically retains every proof input and explicitly admits the TIB preflight; final138 consumer/complete source gate remain separate. ROOT must review gate composition.')
        elif label=='pair_policy_review' and f.startswith('counts.') and f[7:] in counts:
            value=counts[f[7:]];assert type(value) is type(old) and value==old
            x.update(audit_status='current_original_operand_proof_candidate',candidate=dict(proof_file='current-original-MFC-corroborations.json',field=f,expected=value),recommendation='Current original3 six carried source cases independently satisfy the exact historical operand/role/FS/byteflow predicates; use supplemental scoped receipt together with current ROOT policy8, not ROOT policy passed as an alias.')
        elif (label,f) in rename:
            target=rename[label,f];value=at(current[label],target);assert type(value) is type(old)
            x.update(audit_status='explicit_same_domain_rename_candidate',candidate=dict(path=bindings[label]['path'],sha256=bindings[label]['sha256'],field=target,expected=value),recommendation='Explicit separately reviewed typed field relation required; physical selected order extends131 by seven actual slots, or same false no-acceptance invariant / twelve-case source extent. No allowance is created here.')
        elif label in ('controls','controls_review'):
            x.update(audit_status='controls_domain_or_full_inventory_pending',recommendation='Current eight-by-two post-resource Context cases differ from historical twelve pre-resource cases. Require explicit union/domain proof plus terminal fullraw durable inventory; readiness/header counts are not whole raw acceptance.')
            if label=='controls' and f in ('passed','initializer_credit','execution_sha256'):
                value=at(metadata,f);assert type(value) is type(old)
                x.update(audit_status='bounded_current_controls_metadata_candidate',candidate=dict(path='reports/m4-joint-startup138/context-controls-verification-r1/report.json',sha256='88e0a18bc8b32fb70c3fd460c828c44127613662fd4467cf3385ae78b56861cb',field=f,expected=value),recommendation='Historical bounded readiness authenticates producer metadata only. Fullraw physical map/payload/retry proof and fresh whole union remain mandatory; this audit does not open or independently hash the giant report.')
            if f=='counts.pre_resource_refusals': x['recommendation']='Genuine domain gap: current faults follow135 carried roots and15 owned fonts; post-resource refusals cannot establish historical twelve pre-resource refusals. Preserve historical control domain with exact unchanged component/current-link proof or supply scoped new evidence.'
            if f=='counts.source_TLS_refusal_frame64': x['recommendation']='Genuine domain gap: current source TIB permission refusal does not by itself establish historical compiler/source TLS64 refusal frame. Require exact target/frame/prefix witness or reviewed unchanged historical subdomain.'
        elif label=='pair_policy_review' and f in ('helper_sha256','comparer_sha256'):
            value=PINS[str(hp)] if f=='helper_sha256' else pp['comparer_sha256']
            x.update(audit_status='physical_current_policy_identity_candidate',candidate=dict(path=str(hp if f=='helper_sha256' else Path(pp['comparer'])),sha256=value,expected=value),recommendation='Current prep15 physically retains the identical finite MFC helper; comparer identity changes via53 exact inverse hunks. Bind code identities through current independent ROOT policy8 and definition-preflight8; do not equate identities to semantic approval.')
    counts_by_status=dict(collections.Counter(x['audit_status'] for x in rows))
    out.mkdir(parents=True)
    for leaf,data in [('predicate-recommendations.json',rows),('current-original-MFC-corroborations.json',witnesses)]:
        q=out/leaf;q.write_text(json.dumps(data,indent=2)+'\n');pin(q)
    pin(__file__);pin(sys.executable)
    report=dict(passed=True,scope='Bounded ordinary133-predicate frontier audit, excluded paired_review63; recommendations and measured finite original-MFC predicates only, not acceptance or allowances',baseline_gates=33,baseline_predicates=841,unresolved_proposal_predicates=196,excluded_paired_review_predicates=63,examined_predicates=133,counts=counts_by_status,current_original_MFC_counts=dict(counts),historical_legacy_all10_physical_inputs_rehashed=True,historical_preflight_all83_physical_inputs_rehashed=True,current_closure_source6_binding=closure['source_provider_sha256'],controls_metadata_scope='Existing bounded readiness metadata; no giant report/fullraw inventory opened',current_link_counts=link['counts'],fullraw_verifier_known_PID=48436,fullraw_verifier_interrupted=False,archive_reader_opened=False,source_machine_executed=False,worker_launched=False,configuration_created=False,allowance_created=False,acceptance_executed=False,initializer_credit=0,files=PINS)
    q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(report=str(q),sha256=hashlib.sha256(q.read_bytes()).hexdigest(),counts=counts_by_status)))
if __name__=='__main__':main(sys.argv[1])
