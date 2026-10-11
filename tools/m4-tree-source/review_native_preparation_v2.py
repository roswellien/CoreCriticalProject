"""Independently join frozen native normal-tree guards to literal source contracts."""
from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parents[2]
EXPECTED='9b6c7ab64a42dd67d26e73a7b4357063729085a808173b2818e704430386fef2'
def main(name):
    out=ROOT/'reports/m4-tree-source'/name;assert not out.exists();out.mkdir(parents=True);pins={}
    def pin(path,expected=None):
        path=Path(path).resolve();digest=hashlib.sha256(path.read_bytes()).hexdigest();assert expected is None or digest==expected,(path,digest);pins[str(path)]=digest;return path
    p=ROOT/'reports/m4-tree-native/preparation-r5'
    native=json.loads(pin(p/'report.json',EXPECTED).read_bytes());assert native['passed'] and not native['source_or_native_executed']
    source=json.loads(pin(ROOT/'reports/m4-tree-source/dynamic-contracts-r1/report.json','9a44bbb1c6be884f166837457e7db2619a1045efb2fb27ac398665e578df49d3').read_bytes());assert source['passed']
    d=json.loads(pin(source['contracts'],source['contracts_sha256']).read_bytes())
    paths={f:pin(p/f,native['files'][str((p/f).resolve())]) for f in ('tree_contract.inc','tree_operations.inc','fs_operations.inc','lockit_operations.inc','session_impl.inc','locale_batch_operations.inc','locale_batch_binding.inc')}
    t={f:path.read_text() for f,path in paths.items()};contract=t['tree_contract.inc'];operations=t['tree_operations.inc']
    def array(symbol):
        body=re.search(r'\b'+re.escape(symbol)+r'\[\]\{(.*?)\};',contract,re.S).group(1)
        result=[]
        for row in re.findall(r'\{([^{}]+)\}',body):
            result.append([0xffffffff if v.strip()=='UINT32_MAX' else v.strip()=='true' if v.strip() in ('true','false') else int(v.strip(),0) for v in row.split(',')])
        return result
    expected_accesses=[[r['pc'],r['owner_role_index'],r['offset'],r['bytes'],0xffffffff if r['value_owner_role_index'] is None else r['value_owner_role_index'],r['write']] for r in d['owned_causal_order']]
    assert array('tree_access_order')==expected_accesses
    expected_pubs=[[r[k] if r[k] is not None else 0xffffffff for k in ('pc','owner_role_index','parent_owner_role_index','parent_offset','static_publication')]for r in d['publications']]
    assert array('tree_publication_order')==expected_pubs
    for symbol,expected in [('tree_owner_sites',[r['CALL_pc'] for r in d['owners']]),('tree_lockit_order',[r['CALL_pc'] for r in d['Lockit_call_order']])]:
        actual=[int(v,0) for v in re.search(r'\b'+symbol+r'\[\]\{([^}]+)\}',contract).group(1).split(',')];assert actual==expected
    normal={r['CALL_pc']:(r['target'],r['target_entry_ESP_bias'],r['source_LEA_pc'])for r in d['Lockit_call_order']}
    scratch=array('tree_scratches');assert sum(row[4]for row in scratch)==len(normal)==8
    for site,target,offset,lea,admitted in scratch:
        if admitted:assert (target,offset,lea)==normal[site]
        else:assert site not in normal
    checks={
      'actual_generation_role_and_exact_allocation_site':'mfc_for_generation(a->generation)'in operations and 'r.words[4]!=tree_owner_sites[role]'in operations,
      'positive_requested24_capacity_bounds':'a->requested!=24'in operations and 'std::uint64_t(address)+bytes>std::uint64_t(a->guest)+a->requested'in operations,
      'foreign_expired_required_owner_denied':'if(!a||a->kind!=4){if(required)deny('in operations,
      'exact172_causal_access_order':'expected.pc!=ins->pc||expected.role!=role||expected.offset!=offset||expected.width!=bytes||expected.writing!=writing'in operations and '++tree_owner_cursor_'in operations,
      'exact39_live_pointer_role_joins':'value_owner->guest!=value||value_owner->kind!=4||tree_role(value_owner->generation)!=expected.value_role'in operations,
      'exact7_current_child_parent_publications':'expected.role!=tree_role(a->generation)'in operations and 'expected.parent!=tree_role(parent->generation)||expected.offset!=offset'in operations and 'r->words[23]'in operations and '++tree_publication_cursor_'in operations,
      'exact26_normal_Lockit_call_order':'tree_lockit_order[tree_lockit_contexts_.size()]!=site'in operations,
      'register_definition_current_FS_invocation':'imported->at(6)<=fs_begin->at(13)'in operations,
      'register_actual_raw_read_join':'read.value!=definition->raw'in operations,
      'direct_actual_raw_read_join':'r.value!=definition->raw'in operations,
      'shared_exact_committed_left_write_suffix':'a.pc!=0x4badc7||b.pc!=0x4badc9'in operations and 'a.address!=state.gpr.rax.dword||a.value!=state.gpr.rdi.dword'in operations and 'b.address!=state.gpr.rdi.dword+4||b.value!=state.gpr.rax.dword'in operations,
      'same_scratch_caller_frame_FS_invocation_LIFO':'held[4]!=caller.frame'in operations and 'held[5]!=invocation'in operations and 'site==0x4badd0?0x4bad8fU'in operations,
      'distinct_source_header1_map5':'load<unsigned>({0x60b318})!=1'in operations and 'load<unsigned>({0x60b304})!=5'in operations,
      'root_exhausts_order_owner_scratch_FS':'tree_owner_cursor_!=std::size(tree_access_order)'in operations and 'tree_publication_cursor_!=7'in operations and 'tree_lockit_contexts_.size()!=26'in operations and 'owners!=7'in operations and '!tree_lockit_held_.empty()||!fs_active_.empty()'in operations,
      'owner_before_and_after_hooks_scoped_to_tree':'if(registry_root_==tree_root){tree_owner_before(address,value,bytes,writing);return;}'in t['fs_operations.inc'] and 'if(registry_root_==tree_root){tree_owner_after(address,value,bytes,writing);return;}'in t['fs_operations.inc'],
      'root_entry_and_return_hooks':'binding->tree_enter();binding->guard()'in t['session_impl.inc'] and 'tree_returned(f.entry)'in t['locale_batch_operations.inc'],
      'observer_preserves_private_role_cursors':'tree_owner_cursor!=tree_owner_cursor_||tree_publication_cursor!=tree_publication_cursor_'in t['locale_batch_binding.inc'],
    }
    assert all(checks.values()),[k for k,v in checks.items()if not v]
    assert d['final_header_counter']==1 and d['final_map_count']==5
    pin(__file__)
    report=dict(passed=True,scope='Read-only exact source-contract review of frozen native preparation-r5; guard syntax and finite generated arrays, no native execution credit',reviewed_native_preparation_sha256=EXPECTED,checks=checks,counts=dict(owned_causal_accesses=len(expected_accesses),distinct_role_tuples=len(d['owned_access_tuples']),live_pointer_role_joins=sum(r[4]!=0xffffffff for r in expected_accesses),primary_publications=len(expected_pubs),Lockit_call_occurrences=len(d['Lockit_call_order']),normal_Lockit_sites=len(normal)),native_execution_credit=False,initializer_credit=False,files=pins)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,report_sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest(),counts=report['counts'])))
if __name__=='__main__':main(sys.argv[1])
