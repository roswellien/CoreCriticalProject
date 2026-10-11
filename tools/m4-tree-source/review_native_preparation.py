"""Read-only source review of the unexecuted native tree preparatory guards."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
def main(name):
    out=ROOT/'reports/m4-tree-source'/name;assert not out.exists();out.mkdir(parents=True);pins={}
    def pin(path,expected=None):
        path=Path(path).resolve();digest=hashlib.sha256(path.read_bytes()).hexdigest();assert expected is None or digest==expected;pins[str(path)]=digest;return path
    preparation=ROOT/'reports/m4-tree-native/preparation-r2'
    receipt=pin(preparation/'report.json','0276177655c14876a73c519f7c2f0935898a49c2a13e34236d82ab188ee289c8')
    native=json.loads(receipt.read_bytes());assert native['passed']
    operations=pin(preparation/'tree_operations.inc');text=operations.read_text()
    source=pin(ROOT/'reports/m4-tree-source/dynamic-contracts-r1/report.json','9a44bbb1c6be884f166837457e7db2619a1045efb2fb27ac398665e578df49d3');source_receipt=json.loads(source.read_bytes())
    dynamic=json.loads(pin(source_receipt['contracts'],source_receipt['contracts_sha256']).read_bytes())
    checks={
        'actual_generation_owner_resolution':'mfc_for_generation(a->generation)'in text,
        'requested_bounds_before_access':'std::uint64_t(address)+bytes>std::uint64_t(a->guest)+a->requested'in text,
        'register_definition_current_FS_invocation':'imported->at(6)<=fs_begin->at(13)'in text,
        'register_actual_raw_read_join':'read.value!=definition->raw'in text,
        'direct_actual_raw_read_join':'r.value!=definition->raw'in text,
        'shared_exact_left_write_suffix':'a.pc!=0x4badc7||b.pc!=0x4badc9'in text,
        'shared_actual_register_address_value_join':'b.address!=state.gpr.rdi.dword+4||b.value!=state.gpr.rax.dword'in text,
        'same_scratch_caller_frame_FS_invocation_LIFO':'held[4]!=caller.frame'in text and'held[5]!=invocation'in text,
        'shared_matching_constructor4BAD8F':'site==0x4badd0?0x4bad8fU'in text,
        'positive_owner_primary_publication_count':'r.words[23]!=1'in text,
    }
    assert all(checks.values())
    findings=[dict(priority='blocking_before_positive_execution',line=next(i for i,line in enumerate(text.splitlines(),1)if'0x60b318})!=5'in line),
                   statement='Native root RET compares shared-header counter60B318 with5. Literal source counter is1; element count5 is60B304. Require both independently.',
                   source_predicates=dict(header_counter=dynamic['final_header_counter'],map_count=dynamic['final_map_count'])),
              dict(priority='tighten_before_guard_acceptance',statement='Owner guard admits any decoded tree PC and any DWORD offset0..20 for any tree MFC role. Replace this preparatory union with the135 sealed PC/direction/width/site-invocation/offset tuples and actual live generation. It currently returns early for non-kind4 allocations; a source operation requiring a tree owner must reject a foreign allocation kind instead.',
                   contract=str(Path(source_receipt['contracts']).resolve())),
              dict(priority='tighten_before_guard_acceptance',statement='Node publication validates root/site/live parent and offset0/8, but does not yet bind exact current node-site ordinal and source-derived parent role. Use the7 sealed publication rows and observed owner identity; retain one primary publication per current generation.'),
              dict(priority='proof_scope',statement='Original prefix allows only independently proved unused uninitialized external-stack observations. A native source comparison still requires full source-derived stack/State/CPU/FX; this original policy must not become a native wildcard.')]
    pin(__file__)
    report=dict(passed=False,review_completed=True,scope='Independent read-only preparation-r2 source-contract review; no native execution performed',
                existing_provenance_checks=checks,findings=findings,source_dynamic_contract_sha256=source_receipt['contracts_sha256'],
                reviewed_native_preparation_sha256=pins[str(receipt)],native_execution_credit=False,files=pins)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(review_completed=True,passed=False,report_sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest())))
if __name__=='__main__':main(sys.argv[1])
