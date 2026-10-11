"""Freeze normal owner-role tuples and causal seams from executed literal source."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
PINS={}
def pin(path,expected=None):
    path=Path(path).resolve();digest=hashlib.sha256(path.read_bytes()).hexdigest();assert expected is None or digest==expected
    PINS[str(path)]=digest;return path
def main(name):
    out=ROOT/'reports/m4-tree-source'/name;assert not out.exists();out.mkdir(parents=True)
    receipt=pin(ROOT/'reports/m4-tree-source/original-source-r3/report.json','f214d298b40aa4f589d9a99b4083cdf954090486637a577b7db4d9358185a4ff')
    proof=json.loads(receipt.read_bytes());assert proof['passed']and not proof['candidate_AFTER_machine_seed']
    evidence=ROOT/'reports/m4-tree-source/original-source-r3/source-derivations.json'
    data=json.loads(pin(evidence,proof['files'][str(evidence.resolve())]).read_bytes())
    recovery=pin(ROOT/'reports/m4-tree-source/recovery-r1/instruction-contracts.json','a3e74efdaaca40677dbd27c24924c9a20f955fd3d7f67fa75164ee93d3ca34d8')
    physical=json.loads(recovery.read_bytes());rows={r['pc']:r for r in physical['instructions']}
    owners=[{k:r[k]for k in('index','root','CALL_pc','per_site_invocation_ordinal','function_invocation','generation','requested','capacity','role','source_frame')}for r in data['owners']]
    accesses=[];seen=set();causal=[]
    for ordinal,access in enumerate(data['owned_accesses']):
        key=tuple(access[k]for k in('root','pc','write','bytes','owner_CALL_pc','owner_invocation_ordinal','offset'))
        assert access['bytes']==4 and 0<=access['offset']and access['offset']+4<=24
        source=data['source_accesses'][access['source_access_index']]
        assert source==[access['pc'],access['address'],access['value'],access['bytes'],int(access['write'])]
        owner=data['owners'][access['owner_index']]
        assert owner['CALL_pc']==access['owner_CALL_pc']and owner['per_site_invocation_ordinal']==access['owner_invocation_ordinal']and owner['generation']==access['generation']and owner['guest']+access['offset']==access['address']
        if key not in seen:
            seen.add(key);accesses.append(dict(zip(('root','pc','write','bytes','owner_CALL_pc','owner_site_invocation','offset'),key),
                                               owner_role=owner['role'],source_operand_row=rows[access['pc']]))
        causal.append(dict(ordinal=ordinal,owner_role_index=access['owner_index'],source_access_index=access['source_access_index'],
                           pc=access['pc'],write=access['write'],bytes=access['bytes'],offset=access['offset'],
                           value_kind='live_owner_base'if access['write']and access['offset']in(0,4,8)and access['value']else'source_scalar',
                           value_owner_role_index=next((o['index']for o in data['owners']if o['guest']==access['value']),None)))
    pubs=[]
    for publication in data['publications']:
        owner=data['owners'][publication['owner_index']]
        pubs.append(dict(root=publication['root'],pc=publication['pc'],CALL_pc=owner['CALL_pc'],site_invocation=owner['per_site_invocation_ordinal'],
                         requested=24,owner_role_index=owner['index'],parent_owner_role_index=publication['target_owner_index'],
                         parent_offset=publication['target_owner_offset'],static_publication=publication['address']if publication['target_owner_index']is None else 0,
                         source_access_index=publication['source_access_index'],exactly_one_primary_publication=True))
    scratch=[]
    for occurrence,call in enumerate(sorted(data['Lockit_calls'],key=lambda r:r['entered']['source_access_index'])):
        record=dict(occurrence_in_root=occurrence,CALL_pc=call['CALL_pc'],target=call['target'],role=call['role'],
                    source_function_invocation=call['invocation'],source_LEA_pc=call['LEA']['PC'],target_entry_ESP_bias=call['scratch_offset'],
                    preceding_accesses=call['preceding_source_accesses'],source_entered_access_index=call['entered']['source_access_index'],
                    source_returned_access_index=call['returned']['source_access_index'])
        if 'matching_constructor_CALL_pc'in call:record.update(matching_constructor_CALL_pc=call['matching_constructor_CALL_pc'],matching_constructor_invocation=call['matching_constructor_invocation'])
        if call['CALL_pc']==0x4badd0:
            assert call['LEA']['PC']==0x4badcc and call['scratch_offset']==24 and call['matching_constructor_CALL_pc']==0x4bad8f
            record['required_immediate_owned_write_PCs']=[0x4badc7,0x4badc9]
        scratch.append(record)
    frames=[dict(index=r['index'],entry=r['entry'],function_invocation=r['invocation'],handler=r['handler'],depth=r['depth'],
                 restore_scope_value=r['restore_scope_source_store']['value'],scope_store_PC=r['restore_scope_source_store']['pc'],
                 source_read_PC=r['read_PC'],source_install_PC=r['install_PC'],source_restore_PC=r['restore_PC'])for r in data['FS_frames']]
    borrowed=[]
    for storepc,readpc in((0x4b7daf,0x4b7d98),(0x4b7da6,0x4b7da0)):
        writes=[(i,r)for i,r in enumerate(data['source_accesses'])if r[0]==storepc and r[4]];reads=[(i,r)for i,r in enumerate(data['source_accesses'])if r[0]==readpc and not r[4]]
        assert len(writes)==len(reads)==1
        wi,w=writes[0];ri,r=reads[0];assert ri<wi and w[2]==r[2]and w[3]==r[3]==1
        dominating=[(i,s)for i,s in enumerate(data['source_accesses'][:ri])if s[4]and s[1]<=r[1]<s[1]+s[3]]
        borrowed.append(dict(store_PC=storepc,read_PC=readpc,source_read_address=r[1],static_write_address=w[1],value=r[2],
                             read_access_index=ri,write_access_index=wi,dominating_store=dominating[-1]if dominating else None,
                             untouched_true_BEFORE_stack_byte=not dominating,no_observed_AFTER_seed=True))
    negative=[
        dict(id='foreign_owner',predicate='Actual generation resolves source tree root and one exact24B requested owner role'),
        dict(id='oldest_or_newest_node_fallback',predicate='Each source PC/width/offset binds exact allocator site invocation; prior live nodes remain accessible only by their actual generation'),
        dict(id='wrong_role_field',predicate='Owner role/site invocation, source PC, read/write direction, width and requested offset must match a sealed tuple'),
        dict(id='capacity_tail_access',predicate='Actual backing may be32B, but source access at offset24 must reject before operation'),
        dict(id='stale_publication',predicate='Exactly one primary publication for the current unpubished allocator occurrence and its actual parent edge'),
        dict(id='foreign_parent_edge',predicate='Parent role/generation and offset0 or8 match the literal chosen edge'),
        dict(id='wrong_register_definition',predicate='Register-held source target is defined by current insertion invocation read at4BAB1A, after that invocation FS read'),
        dict(id='held_register_corruption',predicate='Actual register value remains the projected owning target after every literal callee'),
        dict(id='alternate_scratch_branch',predicate='Shared4BADD0 is +24 only after exact committed4BADC7/4BADC9 suffix and outstanding same-invocation4BAD8F scope'),
        dict(id='scratch_scope_reuse',predicate='Constructor/destructor use identical scratch, source function frame and FS invocation in LIFO order'),
        dict(id='source_IAT_mutation',predicate='Raw original import cell unchanged before named projection'),
        dict(id='FS_previous_or_scope_mutation',predicate='Whole12B source record: exact parent/handler and scope from dominating literal source store'),
        dict(id='provider_resource_mutation',predicate='Initializedstate2, actual native40 owner/generation/thread and original opaque semantic24 relation remain exact'),
    ]
    value=dict(schema='mw34-tree-normal-dynamic-v1',root=0x4b7f70,normal_original_prefix_only=True,source_receipt_sha256=PINS[str(receipt)],
               owners=owners,owned_access_tuples=accesses,owned_causal_order=causal,publications=pubs,Lockit_call_order=scratch,
               FS_frames=frames,borrowed_static_byte_derivations=borrowed,register_import_derivations=data['register_import_calls'],
               final_header_counter=1,final_map_count=5,normal_predecessor_admitted=False,native_execution_credit=False,
               native_guard_requires_actual_generation=True,native_guard_must_not_assign_tree_effects=True)
    def emit(filename,payload):
        path=out/filename;path.write_text(json.dumps(payload,indent=2)+'\n');pin(path)
    emit('normal-contracts.json',value);emit('causal-negative-predicates.json',negative);pin(__file__)
    report=dict(passed=True,scope='Executed genuine original source-derived normal owner-role/offset and causal import/scratch/FS contracts; no native credit',
                normal_original_source_sha256=PINS[str(receipt)],owners=7,owned_accesses=172,distinct_owned_role_tuples=len(accesses),primary_publications=7,
                Lockit_calls=26,register_CALLs=7,FS_frames=7,FS_accesses=21,borrowed_static_bytes=2,unused_original_frame_bytes_seeded=False,
                contracts=str(out/'normal-contracts.json'),contracts_sha256=PINS[str((out/'normal-contracts.json').resolve())],files=PINS)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest(),distinct_owned_role_tuples=len(accesses))))
if __name__=='__main__':main(sys.argv[1])
