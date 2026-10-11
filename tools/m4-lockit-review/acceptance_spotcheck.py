"""Bounded post-acceptance count/source review; no closure or archive rehash."""
from pathlib import Path
import hashlib,json,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def need(value,message):
    if not value:raise ValueError(message)
def main(name):
    out=ROOT/'reports/m4-lockit-review'/name;need(not out.exists(),'Fresh bounded acceptance spot-check');out.mkdir(parents=True)
    inputs={};passed=False;counts={}
    def read(relative):
        path=Path(relative);path=path if path.is_absolute()else ROOT/path
        raw=path.read_bytes();need(len(raw)<=32*1024*1024,'Bounded metadata only');inputs[str(path.resolve())]=hashlib.sha256(raw).hexdigest();return json.loads(raw)
    try:
        acceptance=read('reports/m4-joint-startup124-root/acceptance-r1/report.json')
        acceptance_path=str((ROOT/'reports/m4-joint-startup124-root/acceptance-r1/report.json').resolve())
        need(inputs[acceptance_path]=='6bd35e55bca15e1a0537044bf59a1c3ced5e9ef8b30a8a169b71c78824811462'and acceptance['passed'],'Exact sealed current acceptance')
        need((acceptance['connected_roots'],acceptance['new_roots'],acceptance['total_inventory_roots'],acceptance['remaining_inventory_roots'])==(124,4,144,20),'Exact initializer inventory scope')
        need(not acceptance['inventory_is_project_completion_percentage']and not acceptance['whole_M4_complete']and not acceptance['native_game_launch_complete'],'Inventory percentage distinct from whole M4/game launch completion')
        need(len(acceptance['gates'])==39 and sum(len(g['equal'])for g in acceptance['gates'].values())==acceptance['explicit_measured_predicates']==324,'Exact actual gate/predicate extents')
        need(acceptance['physical_closure']['passed']and acceptance['physical_closure']['unique_physical_dependencies']==11809 and
             not acceptance['physical_closure']['metadata_only_cache_used'],'Original acceptance reports actual11809 physical closure; this review does not repeat it')
        need(all(value is False for value in acceptance['bounded_scope'].values()),'Every declared excluded path remains outside acceptance')
        documents={}
        def field(value,path):
            for part in path.split('.'):
                value=value[int(part)]if isinstance(value,list)else value[part]
            return value
        for label,gate in acceptance['gates'].items():
            value=read(gate['path']);path=str((ROOT/gate['path']).resolve())
            need(inputs[path]==gate['sha256']and value['passed'],'Exact sealed bounded gate '+label)
            for key,expected in gate['equal'].items():need(field(value,key)==expected,'Measured acceptance predicate '+label+'.'+key)
            documents[label]=value
        prep=read('reports/m4-joint-startup124/preparation-r5/report.json');order=prep['selected_order']
        inventory=read('reports/m4-service-initializers/static-r1/root-classification.json')['roots']
        frontier=read('reports/m4-joint-startup124-root/next-frontier-r1/report.json');remaining=read('reports/m4-joint-startup124-root/next-frontier-r1/remaining-roots.json')
        selected={(r['slot'],r['entry'])for r in order};full={(r['slot'],r['entry'])for r in inventory};left={(r['slot'],r['entry'])for r in remaining}
        need(len(selected)==124 and len(full)==144 and len(left)==20 and selected.isdisjoint(left)and selected|left==full,'Exact144 original table inventory partitioned into124 accepted and20 remaining')
        need(frontier['passed']and frontier['counts']['remaining_roots']==20 and frontier['counts']['unique_physical_instruction_rows']==4336 and frontier['counts']['unique_physical_instruction_bytes']==13068 and not frontier['native_executed']and not frontier['original_executed']and frontier['initializer_credit']==0,'Remaining frontier is static recovery only')
        source=documents['source'];phases=read(Path(ROOT/acceptance['gates']['source']['path']).parent/'phases.json')
        cases={(level,sequence)for level in('O0','O2')for sequence in range(6)}
        for case in cases:
            rows=[r for r in phases if(r['level'],r['sequence'])==case]
            need(len(rows)==124 and [r['entry']for r in rows]==[r['entry']for r in order]and [r['phase']for r in rows]==list(range(124))and rows[-1]['registry_calls']==96,'Actual persistent source phase order and callback count')
        provider=documents['provider'];p=provider['provider_counts'];extent=acceptance['extent']
        need(extent['ordered_callbacks_per_sequence']==p['selected_registration_closures']//12==96 and extent['observed_source_pages']==43 and source['counts']['whole_page_BEFORE']==source['counts']['whole_page_AFTER']==124*12*43,'Callbacks/pages independently derived from actual source/provider proof counts')
        need(extent['MFC_allocations_per_sequence']==p['actual_MFC_allocations']//12==58 and extent['string_allocations_per_sequence']==p['actual_duplicate_allocations']//12==19 and
             extent['live_ordinary_owners_per_sequence']==58+19+1==p['actual_source_frees']//12==78 and extent['live_critical_sections_per_sequence']==p['actual_CS_deletes']//12==5,'58MFC+19strings+1registry owners and five explicit locks; free/delete counts consistent')
        link=documents['link'];need(extent['linked_literal_COFFs_per_level']==link['literal_COFF_links']//2==363 and extent['compiled_objects_per_level']==link['compiled_objects']//2==27 and
             extent['capture_objects_per_level']==2 and extent['actual_linked_inputs_per_level']==link['actual_linked_inputs']//2==363+27+2==392,'392 actual linked inputs include363 literal27 compiled2 capture objects')
        need(documents['resource']['guest_CS_bytes']==24 and documents['resource']['native_resource_bytes']==40 and not documents['resource']['seeded_state2']and
             not source['native_CS40_opaque_copy']and source['guest_CS24_semantic_output']and not source['native_DllMain_credit'],'Authentic loaded state2/semantic24/native40 association remains bounded')
        need(not documents['paired']['Lockit_original_postRET_observed']and not documents['paired']['original_provider_scratch_stack_crossbranch_equal']and
             documents['paired']['native_full_stack_source_proven']and not documents['paired']['whole_game_liveness_proven'],'Paired original pre-epilogue/typed API and strict native stack scope remain explicit')
        counts=dict(gates=39,predicates=324,accepted_inventory_roots=124,remaining_inventory_roots=20,total_inventory_roots=144,
                    source_sequences=12,source_phases=1488,callbacks_per_sequence=96,MFC_owners_per_sequence=58,ordinary_owners_per_sequence=78,
                    whole_source_pages=43,actual_linked_inputs_per_level=392)
        passed=True
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        report=dict(passed=passed,scope='Post-acceptance independent bounded gate/predicate/count-source/inventory spot-check; no dependency closure or capture rehash',
                    native_capture_archive_opened=False,original_capture_archive_opened=False,physical_dependency_closure_rehashed=False,
                    whole_M4_complete=False,native_game_launch_complete=False,initializer_credit_added=0,counts=counts,bounded_metadata_inputs=inputs)
        path=out/'report.json';raw=(json.dumps(report,indent=2)+'\n').encode();path.write_bytes(raw);print(json.dumps(dict(passed=passed,report_sha256=hashlib.sha256(raw).hexdigest(),counts=counts)))
if __name__=='__main__':main(sys.argv[1])
