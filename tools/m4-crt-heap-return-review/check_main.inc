def main(native_path, output):
    path = Path(native_path).absolute()
    out = Path(output).absolute()
    base = ROOT / 'reports/m4-crt-heap-return-review'
    need(out.parent == base and out.name.startswith('check-') and not out.exists(), 'Fresh independent hardware/inventory report')
    out.mkdir()
    native = read(path)
    need(native['passed'] is True and native['native_scenarios'] == 244, 'Successful independent actual native corpus')
    files = dict(native['files'])
    def pin(p, expected=None):
        p = Path(p).absolute()
        actual = sha_file(p)
        need(expected is None or actual == expected, 'Current hardware/inventory physical association')
        key = normalized(str(p))
        need(key not in files or files[key] == actual, 'Conflict-free current observer association')
        files[key] = actual
    for p in (path,Path(__file__),Path(__file__).parent/'bundle_union.py',frozen_path,Path(sys.executable)):
        pin(p)
    pin(native['packaging_path'],native['packaging_sha256'])
    packaging=read(native['packaging_path'])
    need(packaging['passed'] is True and packaging['native_rerun'] is False and packaging['transport_limits_changed'] is False and packaging['byte_identical_private_copies'] is True and packaging['copy_verified'] is True and native['native_rerun'] is False and native['adopts_actual_native_execution'] is True,'Explicit same-stage bounded packaging adoption')
    pin(packaging['partition_tool_path'],packaging['partition_tool_sha256'])
    pin(packaging['packager_tool_path'],packaging['packager_tool_sha256'])
    validator, association = T.load_validator()
    actual, counts, inventory_tests, before, after = 0, {}, [], None, None
    actual_heaps=actual_queries=actual_output_commits=actual_selector_returns=actual_initializer_returns=actual_mode_stores=actual_initializer_reads=0
    for level in ('O0','O2'):
        info = native['levels'][level]
        verify_stage(info['native_stage'], info['native_stage_sha256'])
        original_stage=read(Path(info['native_stage'])/'stage.json')
        need(original_stage['passed'] is True and original_stage['argv']==info['argv'] and original_stage['argv'][-1]==info['source_tree'] and packaging['levels'][level]['native_stage_sha256']==info['native_stage_sha256'] and packaging['levels'][level]['inventory_sha256']==info['inventory_sha256'] and packaging['levels'][level]['bundles']==info['bundles'],'Original native stage and packaging level association')
        for key in ('source_controls','source_complete'):
            pin(info[key],info[key+'_sha256'])
            need(original_stage['artifact_sha256'][info[key]]==info[key+'_sha256'],'Original closed native output digest')
        verify_stage(info['partition_stage'],info['partition_stage_sha256'])
        pin(info['partition_map'],info['partition_map_sha256'])
        mapping=read(info['partition_map'])
        need(mapping['passed'] is True and mapping['source_files_modified'] is False and mapping['transport_limit_unchanged']==200000 and mapping['original_relative_paths_preserved'] is True,'Source-preserving partitioning with unchanged transport limits')
        for part in info['bundles']:
            verify_stage(part['pack_stage'],part['pack_stage_sha256'])
            pin(part['inventory_path'],part['inventory_sha256'])
        pin(info['inventory_path'], info['inventory_sha256'])
        published_records = read(info['inventory_path'])['files']
        need(published_records==mapping['files'] and info['logical_files']==mapping['logical_files'],'Whole original native inventory equals partition map')
        for mapped,part in zip(mapping['parts'],info['bundles']):
            need(mapped['part']==part['part'] and mapped['pack_source']==part['pack_source'] and mapped['logical_files']==part['logical_files'] and mapped['files']==read(part['inventory_path'])['files'],'Exact original-to-part association')
        need(all(set(row) == {'bytes','sha256'} and type(row['bytes']) is int and row['bytes'] >= 0 for row in published_records.values()), 'Exact published logical inventory schema')
        records = {name:{'size_bytes':row['bytes'],'sha256':row['sha256']} for name,row in published_records.items()}
        with BundleUnion(info,published_records) as bundle:
            result, count, heaps, queries, output_commits, selector_returns, initializer_returns, mode_stores, initializer_reads = semantic_inventory(bundle, records)
            need(count == info['logical_files'] and result == info['result'], 'Exact native-to-archive receipt association')
            reader = T.LogicalReader(records, bundle=bundle)
            for number in range(1,123):
                for actor in ('writer','entry'):
                    validator(reader.path(f'case-{number}/{actor}-host-before.bin'), reader.path(f'case-{number}/{actor}-host-after.bin'), number)
                    actual += 1
            for diagnostic in (1,2):
                validator(reader.path(f"direct-query-failure-{diagnostic}/query-host-before.bin"),reader.path(f"direct-query-failure-{diagnostic}/query-host-after.bin"),122+diagnostic)
                actual+=1
            actual_heaps+=heaps;actual_queries+=queries;actual_output_commits+=output_commits;actual_selector_returns+=selector_returns;actual_initializer_returns+=initializer_returns;actual_mode_stores+=mode_stores;actual_initializer_reads+=initializer_reads
            counts[level] = count
            if level == 'O0':
                before = bundle.read_bytes('case-1/entry-host-before.bin')
                after = bundle.read_bytes('case-1/entry-host-after.bin')
                class Overlay:
                    def __init__(self,changes=None,names=None):self.changes=changes or {};self.inventory=names
                    def read_bytes(self,name):return self.changes[name] if name in self.changes else bundle.read_bytes(name)
                    def names(self):return self.inventory if self.inventory is not None else bundle.names()
                def rejection(label, overlay):
                    denied, reason = False, ''
                    try:semantic_inventory(overlay, records)
                    except (ValueError,KeyError) as error:denied, reason = True, str(error)
                    need(denied, 'Independent inventory corruption refuses')
                    inventory_tests.append(dict(label=label,denied=True,reason=reason))
                rejection('missing_COMPLETE',Overlay({'COMPLETE':b'PARTIAL!'}))
                rejection('missing_case_record',Overlay(names=tuple(n for n in bundle.names() if n!='case-1/heap-events.bin')))
                rejection('extra_case_record',Overlay(names=tuple(sorted(bundle.names()+('case-123/heap-status.bin',)))))
                rejection('missing_required_HeapCreate_phase',Overlay(names=tuple(n for n in bundle.names() if n!='case-1/heap-create-api-before/state.bin')))
                rejection('invented_HeapCreate_phase_on_early_fault',Overlay(names=tuple(sorted(bundle.names()+('case-19/heap-create-api-before/state.bin',)))))
                rejection('wrong_independent_request',Overlay({'case-1/mainargs-mode.bin':(121).to_bytes(4,'little')}))
                for label, offset in (('active_boundary_depth',36),('active_heap_after_cleanup',52)):
                    status=bytearray(bundle.read_bytes('case-1/heap-status.bin'));status[offset:offset+4]=(1).to_bytes(4,'little')
                    rejection(label,Overlay({'case-1/heap-status.bin':bytes(status)}))
                for filename,offset,label in (('independent-ownership.bin',24,'actual_create_count'),('independent-ownership.bin',40,'actual_release_success_count'),('independent-ownership.bin',56,'live_handle_after_cleanup'),('heap-registry.bin',32,'full_native_HANDLE_association'),('heap-registry.bin',56,'registry_live_after_cleanup'),('heap-registry.bin',80,'actual_destroy_result'),('heap-witness.bin',48,'actual_full_HANDLE_witness'),('heap-witness.bin',56,'guest_token_witness'),('heap-witness.bin',64,'actual_incoming_error_read'),('heap-witness.bin',80,'actual_restored_error_read'),('heap-api-accesses.bin',4,'real_source_return_frame'),('heap-create-api-before.bin',0,'named_creator_API_identity'),('heap-destroy-api-after.bin',0,'named_release_API_identity')):
                    data=bytearray(bundle.read_bytes('case-1/'+filename));data[offset]^=1
                    rejection(label,Overlay({'case-1/'+filename:bytes(data)}))
                for filename,offset,label in (('lower-input-status.bin',0,'declared_initial_pattern'),('declared-lower-input.bin',0x624,'declared_initial_tail_word'),('heap-accesses.bin',13*20+8,'first_probe_read_value'),('heap-accesses.bin',23*20+8,'query_return_store_value'),('heap-undefined-sites.bin',12,'qualified_final_TEST_AF'),('heap-status.bin',128,'probe_reached'),('heap-status.bin',132,'genuine_probe_returned'),('heap-status.bin',136,'query_frontier_reached'),('heap-status.bin',140,'genuine_probe_frame'),('independent-after/page-536870912.bin',0x10,'complete_lower_page_untouched_byte'),('independent-after/page-536870912.bin',0x618,'literal_query_return_word')):
                    data=bytearray(bundle.read_bytes('case-1/'+filename));data[offset]^=1
                    rejection(label,Overlay({'case-1/'+filename:bytes(data)}))
                for filename,offset,label in (('query-witness.bin',24,'private_actual_BOOL'),('query-witness.bin',88,'actual_output_commit_count'),('query-witness.bin',144,'actual_native_major'),('query-status.bin',28,'query_returned_flag'),('query-status.bin',32,'genuine_selector_RET_flag'),('query-output-accesses.bin',8,'native_output_commit_value'),('query-output.bin',4,'full_native_major_bytes'),('query-input.bin',0,'original_source_query_size'),('query-api-before.bin',0,'actual_named_query_API'),('heap-api-accesses.bin',24,'second_genuine_API_return_frame'),('heap-undefined-sites.bin',16,'qualified_query_TEST_AF'),('heap-accesses.bin',30*20+8,'genuine_selector_RET_word')):
                    data=bytearray(bundle.read_bytes('case-1/'+filename));data[offset]^=1
                    rejection(label,Overlay({'case-1/'+filename:bytes(data)}))
                for filename,offset,label in (('status.bin',16,'actual_host_only_failed_BOOL'),('status.bin',12,'nonzero_host_only_incoming_error'),('scratch-before.bin',0,'host_only_invalid_size'),('api-after.bin',0,'actual_host_only_API_identity')):
                    data=bytearray(bundle.read_bytes('direct-query-failure-1/'+filename));data[offset]^=1
                    rejection(label,Overlay({'direct-query-failure-1/'+filename:bytes(data)}))
                for filename,offset,label in (('heap-return-progress.bin',12,'private_genuine_mode_store'),('heap-return-progress.bin',20,'genuine_RET_before_read'),('heap-return-progress.bin',24,'genuine_initializer_RET'),('heap-return-progress.bin',28,'live_token_after_actual_cleanup'),('heap-return-public.bin',12,'public_source_mode_value'),('heap-return-public.bin',20,'public_initializer_return'),('heap-accesses.bin',31*20+8,'literal_mode_store_value'),('heap-accesses.bin',34*20+8,'genuine_initializer_RETURN_WORD'),('heap-events.bin',11*16+12,'mode_store_event'),('independent-after/page-2013483008.bin',4,'complete_genuine_mode_global_page'),('independent-after/page-536875008.bin',0x858,'original_fragment_return_word'),('heap-create-before/heap-provider.bin',0x49,'immutable_existing_success_source')):
                    data=bytearray(bundle.read_bytes('case-1/'+filename));data[offset]^=1
                    rejection(label,Overlay({'case-1/'+filename:bytes(data)}))
                for field,value in (('actual_GetVersionExA_executed',False),('synthetic_API_results',True),('passed',1),('scenarios',65),('original_executed',True),('ordinary_game_launched',True),('whole_M4_complete',True),('malformed_token_denials',17)):
                    changed=dict(result);changed[field]=value;rejection('result_'+field,Overlay({'controls.json':json.dumps(changed).encode()}))
    preservation=list(range(5))+list(range(24,28))+[32+16*i+k for i in range(8) for k in range(10)]+[160+16*i+k for i in range(6,16) for k in range(16)]+list(range(512,540))
    fixtures=list(range(5))+list(range(24,28))+[32+16*i+k for i in range(8) for k in range(10)]+[160+16*i+k for i in range(6,16) for k in range(16)]+[512,513,516,517,520,521]+list(range(524,538))
    tests=[]
    for direction,offsets in (('after',preservation),('coherent_wrong_before_fixture',fixtures)):
        for offset in offsets:
            b=bytearray(before);a=bytearray(after);a[offset]^=1
            if direction!='after':b[offset]^=1
            pb,pa=T.overlay_paths(b,a);denied=False
            try:validator(pb,pa,1)
            except ValueError:denied=True
            need(denied,'Unchanged meaningful hardware semantic corruption refuses')
            tests.append(dict(direction=direction,offset=offset,denied=True))
    for extent in (543,545):
        pb,pa=T.overlay_paths(before[:extent] if extent<544 else before+b'\0',after);denied=False
        try:validator(pb,pa,1)
        except ValueError:denied=True
        need(denied,'Wrong hardware extent rejected');tests.append(dict(direction='wrong_extent',bytes=extent,denied=True))
    need(actual==492 and len(tests)==548 and len(inventory_tests)==68,'Complete actual hardware/control/inventory corpus')
    for source, digest in T.SOURCES.items():
        pin(source,digest)
    closure = verify_manifest(files)
    report={'passed':True,'native_path':str(path),'native_sha256':sha_file(path),'native_scenarios':244,'native_checks':native['native_checks'],
            'actual_hardware_pairs':492,'hardware_semantic_denials':548,'inventory_request_denials':68,'actual_HeapCreate_calls':actual_heaps,'actual_successful_HeapDestroy_calls':actual_heaps,'actual_integrated_GetVersionExA_calls':actual_queries,'counterfactual_direct_host_failure_queries':4,'actual_output_DWORD_commits':actual_output_commits,'actual_selector_RETs':actual_selector_returns,'actual_initializer_RETs':actual_initializer_returns,'actual_source_mode_stores':actual_mode_stores,'actual_initializer_RETURN_WORD_reads':actual_initializer_reads,'logical_files':counts,
            'validator':association,'tests':tests,'inventory_tests':inventory_tests,'physical_closure':closure,'files':files,
            'full_causal_source_model_oracle':False,'native_executed':False,'original_executed':False,'HeapCreate_executed':False,'validates_actual_heap_ownership':True,'declared_initial_lower_stack_patterns':6,'GetVersionExA_executed':False,'validates_actual_query_native_witness':True,'synthetic_API_results':False,'alternate_query_branch_live_coverage':False,'selector_result_produced_by_genuine_source':True,'guest_heap_mode_global_published':True,'heap_initializer_completed_for_measured_mode1':True,'fragment_caller_TEST_executed':False,'probe_return_proved':True,'original_stack_guard_growth_proved':False,'heap_initialized':False,'table_initialization_proved':False,'whole_M4_complete':False}
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    publish_bytes(out/'pins.json',(json.dumps({'files':files},indent=2)+'\n').encode())
    print(json.dumps({'passed':True,'report_sha256':sha_file(out/'report.json'),'pins_sha256':sha_file(out/'pins.json'),'hardware_pairs':492,'checks':native['native_checks']}))


if __name__=='__main__':
    main(*sys.argv[1:])
