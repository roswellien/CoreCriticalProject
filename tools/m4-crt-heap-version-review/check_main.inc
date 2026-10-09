def main(native_path, output):
    path = Path(native_path).absolute()
    out = Path(output).absolute()
    base = ROOT / 'reports/m4-crt-heap-mode-review'
    need(out.parent == base and out.name.startswith('check-') and not out.exists(), 'Fresh independent hardware/inventory report')
    out.mkdir()
    native = read(path)
    need(native['passed'] is True and native['native_scenarios'] == 132, 'Successful independent actual native corpus')
    files = dict(native['files'])
    def pin(p, expected=None):
        p = Path(p).absolute()
        actual = sha_file(p)
        need(expected is None or actual == expected, 'Current hardware/inventory physical association')
        key = normalized(str(p))
        need(key not in files or files[key] == actual, 'Conflict-free current observer association')
        files[key] = actual
    for p in (path,Path(__file__),frozen_path,Path(sys.executable)):
        pin(p)
    validator, association = T.load_validator()
    actual, counts, inventory_tests, before, after = 0, {}, [], None, None
    for level in ('O0','O2'):
        info = native['levels'][level]
        verify_stage(info['native_stage'], info['native_stage_sha256'])
        verify_stage(info['pack_stage'], info['pack_stage_sha256'])
        pin(info['inventory_path'], info['inventory_sha256'])
        published_records = read(info['inventory_path'])['files']
        need(all(set(row) == {'bytes','sha256'} and type(row['bytes']) is int and row['bytes'] >= 0 for row in published_records.values()), 'Exact published logical inventory schema')
        records = {name:{'size_bytes':row['bytes'],'sha256':row['sha256']} for name,row in published_records.items()}
        with CaptureBundle(info['bundle'], info['bundle_sha256']) as bundle:
            result, count = semantic_inventory(bundle, records)
            need(count == info['logical_files'] and result == info['result'], 'Exact native-to-archive receipt association')
            reader = T.LogicalReader(records, bundle=bundle)
            for number in range(1,67):
                for actor in ('writer','entry'):
                    validator(reader.path(f'case-{number}/{actor}-host-before.bin'), reader.path(f'case-{number}/{actor}-host-after.bin'), number)
                    actual += 1
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
                rejection('extra_case_record',Overlay(names=tuple(sorted(bundle.names()+('case-67/heap-status.bin',)))))
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
                for field,value in (('GetVersionExA_executed',True),('passed',1),('scenarios',65),('original_executed',True),('ordinary_game_launched',True),('whole_M4_complete',True),('malformed_token_denials',17)):
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
    need(actual==264 and len(tests)==548 and len(inventory_tests)==39,'Complete actual hardware/control/inventory corpus')
    for source, digest in T.SOURCES.items():
        pin(source,digest)
    closure = verify_manifest(files)
    report={'passed':True,'native_path':str(path),'native_sha256':sha_file(path),'native_scenarios':132,'native_checks':native['native_checks'],
            'actual_hardware_pairs':264,'hardware_semantic_denials':548,'inventory_request_denials':39,'actual_HeapCreate_calls':84,'actual_successful_HeapDestroy_calls':84,'logical_files':counts,
            'validator':association,'tests':tests,'inventory_tests':inventory_tests,'physical_closure':closure,'files':files,
            'full_causal_source_model_oracle':False,'native_executed':False,'original_executed':False,'HeapCreate_executed':False,'validates_actual_heap_ownership':True,'declared_initial_lower_stack_patterns':6,'GetVersionExA_executed':False,'probe_return_proved':True,'original_stack_guard_growth_proved':False,'heap_initialized':False,'table_initialization_proved':False,'whole_M4_complete':False}
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    publish_bytes(out/'pins.json',(json.dumps({'files':files},indent=2)+'\n').encode())
    print(json.dumps({'passed':True,'report_sha256':sha_file(out/'report.json'),'pins_sha256':sha_file(out/'pins.json'),'hardware_pairs':264,'checks':native['native_checks']}))


if __name__=='__main__':
    main(*sys.argv[1:])
