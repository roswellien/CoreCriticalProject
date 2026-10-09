"""Accept the bounded actual source initializer return from independent proofs."""
import hashlib
import json
from pathlib import Path
import sys
import time
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
BASE=ROOT/'reports/m4-crt-heap-return-root'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle,sha_file
from manifests import normalized,unique_object,verify_manifest
from paths import publish_bytes,workspace_path
from stages import verify_stage
NAMES={'recovery','source_contract','preparation','build','author_execution','root_model',
       'source_audit','draft_model_audit','model_audit','compiled_build','compiled_native','hardware_review','independent_seal'}
CATEGORIES=('files','sources','source_files','tools','tool_files','libraries','entry_objects','matherr_objects',
    'control_objects','initterm_objects','mainargs_objects','normal_argv_objects','producer_objects','parser_objects',
    'locale_objects','heap_objects','heap_mode_objects','heap_version_objects','compiler_read_headers','artifacts','input_files')
def need(value,why):
    if not value:raise ValueError(why)
def read(path):return json.loads(Path(path).read_bytes(),object_pairs_hook=unique_object)
def main(config_path,config_sha,directory):
    started=time.perf_counter_ns();out=workspace_path(directory,reports=True)
    need(out.parent==BASE and not out.exists(),'Fresh acceptance output')
    files={}
    def add(path,digest=None):
        path=Path(path).absolute();key=normalized(str(path));value=sha_file(path) if digest is None else digest
        need(key not in files or files[key]==value,'Consistent dependency '+str(path))
        files[key]=value;return path
    config=read(add(config_path,config_sha));need(sha_file(config_path)==config_sha,'External config digest')
    need(set(config)=={'receipts','pins','history','documents','observer_stage'},'Exact config schema')
    need(set(config['receipts'])==NAMES,'Complete independent proof domains')
    values={}
    for name,item in config['receipts'].items():
        need(set(item)=={'path','sha256'},'Exact receipt identity')
        path=add(item['path'],item['sha256']);need(sha_file(path)==item['sha256'],'Fixed receipt '+name)
        value=read(path);need(value['passed'] is True,'Successful receipt '+name);values[name]=value
        for field in ('whole_M4_complete','original_executed','ordinary_game_launched','game_launched',
            'heap_initialized','full_heap_allocator_initialized','full_heap_initialization_complete',
            'environment_API_called','environment_API_executed','original_attach_proved',
            'fragment_caller_continued','fragment_caller_executed','post_initializer_fragment_caller_executed',
            'full_CRT_complete','table_initialization_proved'):
            if field in value:need(value[field] is False,'Bounded scope '+name+'/'+field)
        for category in CATEGORIES:
            for p,h in value.get(category,{}).items():add(p,h)
    for item in config['pins']:
        path=add(item['path'],item['sha256']);need(sha_file(path)==item['sha256'],'Fixed pin map')
        for p,h in read(path)['files'].items():add(p,h)
    for item in config['history']+config['documents']:
        path=add(item['path'],item['sha256']);need(sha_file(path)==item['sha256'],'Fixed history/document')
    review_path=ROOT/'reports/m4-crt-heap-return-acceptance-review/review-r1/report.json'
    need(any(normalized(item['path'])==normalized(str(review_path)) for item in config['history']),
         'Current acceptance-script review identity')
    script_review=read(review_path)
    need(script_review['passed'] is True and script_review['source_only_review'] is True and
        script_review['native_executed'] is False,'Independent source-only acceptance-script review')
    reviewed={normalized(p):h for p,h in script_review['files'].items()}
    for name in ('accept.py','create_config.py','final_check.py'):
        path=Path(__file__).with_name(name)
        need(reviewed.get(normalized(str(path)))==sha_file(path),'Review binds final root script '+name)
    for item in config['documents']:
        need(reviewed.get(normalized(item['path']))==item['sha256'],'Review binds final document '+item['path'])
    def equals(name,wanted):
        for key,value in wanted.items():need(values[name].get(key)==value,name+'/'+key)
    def digest(name):return config['receipts'][name]['sha256']
    counts=values['recovery']['counts']
    for key,value in dict(qualifying_total_source_PCs=59,qualifying_total_source_accesses=35,
        qualifying_source_CALLs=5,qualifying_source_RETs=3,added_source_PCs=8,added_source_accesses=4,
        added_executed_source_bytes=23,qualifying_executed_source_bytes=192,local_total_guarded_identity_bytes=230,
        total_source_identity_bytes=2086,new_guarded_source_bytes=0,new_guest_objects=0,preserved_guest_objects=38,
        prior_mappings=21,total_mappings=21,separate_API_return_reads=2,separate_API_output_DWORD_stores=37).items():
        need(counts[key]==value,'Recovered count/'+key)
    ret=values['recovery']['qualifying_return_contract']
    need(ret['EIP']==0x78001843 and ret['ESP']==0x2000185c and ret['EAX']==1 and
        ret['source_RET_PC']==0x78003a0b and ret['source_RET_read_address']==0x20001858 and
        ret['heap_mode_global_value_after']==1 and ret['genuine_mode_publication_by_source_MOV'] and
        ret['cdecl_argument_still_present'] and not ret['cdecl_argument_cleanup_executed'] and
        not ret['fragment_caller_TEST1843_executed'],'Authentic source mode store and bounded initializer return')
    chronology=values['recovery']['chronology']
    need(chronology['private_HANDLE_live_at_source_initializer_RET'] and
        chronology['accepted_previous_after_registry_already_closed'] and
        values['recovery']['source_authority']['existing_O0_O2_objects_unchanged'],
        'Live fresh actual call chronology, no resume of revoked older AFTER')
    equals('source_contract',dict(new_guarded_source_bytes=0,newly_admitted_existing_source_bytes=23,
        combined_source_identity_bytes=2086,mode1_combined_source_PCs=59,mode1_combined_source_accesses=35,
        mode1_combined_executed_source_bytes=192,mode1_original_source_CALLs=5,mode1_original_source_RETs=3,
        separate_API_return_reads=2,borrowed_pages=21,new_compiled_objects_expected=0,reused_guest_objects_expected=38,
        native_executed=False,initializer_source_return_proved=False))
    equals('preparation',dict(source_identity_bytes=2086,reused_compiled_source_bytes=230,new_compiled_source_bytes=0,
        new_guest_objects=0,reused_guest_objects=38,reused_FDIV_libraries=2,qualifying_executed_source_bytes=192,
        source_accesses=35,source_PCs=59,source_CALLs=5,source_RETs=3,separate_API_return_reads=2,
        declared_API_output_DWORD_stores=37,borrowed_pages=21,prior_pages_preserved=21,new_pages=0,
        State_bytes=3504,FX_bytes=512,CPU_bytes=40,State_reseed_after_writer=False,Runtime_CPU_preserved=True,
        Runtime_call_record_added=False,scheduler_store_count=0,native_component_executed=False))
    need(values['build']['preparation_sha256']==values['source_audit']['preparation_sha256']==digest('preparation'),
         'Exact compiled and independently audited preparation')
    need(values['author_execution']['build_sha256']==values['source_audit']['build_sha256']==digest('build'),
         'Actual execution and source audit bind exact build')
    need(normalized(values['build']['preparation_path'])==normalized(config['receipts']['preparation']['path']),
         'Corrected preparation path, despite identical scalar summaries')
    add(values['build']['source_scope_note'],values['build']['source_scope_note_sha256'])
    equals('source_audit',dict(reused_guest_objects=38,new_guest_objects=0,unchanged_FDIV_libraries=2,
        new_guarded_source_bytes=0,newly_admitted_existing_source_bytes=23,source_identity_bytes=2086,
        mode1_executed_source_bytes=192,mode1_source_PCs=59,mode1_source_accesses=35,
        separate_API_return_reads=2,mode1_original_source_CALLs=5,mode1_original_source_RETs=3,borrowed_pages=21,
        native_executed=False))
    equals('author_execution',dict(positive_sequences=48,causal_sequences=24,native_stages_completed=2,
        native_executed_by_author=True,actual_HeapCreate_calls=72,actual_owned_results=72,
        actual_successful_HeapDestroy_calls=72,injected_zero_result_sequences=0,
        injected_pre_OS_cleanup_skip_sequences=0,actual_GetVersionExA_calls=72,actual_API_output_DWORD_commits=2664,
        qualifying_selector_RET_sequences=72,alternate_environment_frontier_sequences=0,
        actual_source_mode_publication_sequences=68,genuine_initializer_RET_sequences=52,
        ordinary_source_PCs_if_qualifying=59,ordinary_source_accesses_if_qualifying=35,source_RET_count_if_qualifying=3,
        heap_mode_global_published=True,initializer_RET_executed=True,fragment_caller_continued=False,
        new_guest_objects=0,reused_guest_objects=38,native_rerun=False,new_native_execution_credit=False,
        corrected_from_execution_sha256='7e1c25565468f3d286e8262076825e616bd24c10b9ce1665fa06237a1be8d52b',
        rollup_correction_sha256='9f74b0ff818a83d37ef60888289efd98c3d0bab0024798ce87448ad6e758a35a'))
    equals('root_model',dict(original_BEFORE_ordinary_sequences=48,root_full_causal_model_sequences=0,
        checks=304892,selected_semantic_byte_corruption_denials=5192,
        whole_State_bytes=3504,whole_FX_bytes=512,whole_Runtime_CPU_bytes=40,whole_pages=21,
        checkpoints_per_qualifying_row=44,source_identity_bytes=2086,new_compiled_source_bytes=0,
        qualifying_executed_source_bytes=192,qualifying_source_PCs=59,qualifying_source_accesses=35,
        qualifying_source_CALLs=5,qualifying_genuine_source_RETs=3,separate_API_return_reads=2,
        ordinary_selector_RET_sequences=48,ordinary_initializer_RET_sequences=48,ordinary_environment_frontier_sequences=0,
        execution_sha256=digest('author_execution'),heap_mode_global_published=True,heap_initializer_RET=True,
        author_expected_model_imported=False,AFTER_machine_state_used_as_seed=False,independently_executed_by_root=False,
        synthetic_API_response_used=False,host_source_execution_stores=0,main_initializer_count=27))
    need(values['root_model']['checks']>0 and values['root_model']['selected_semantic_byte_corruption_denials']>0,
         'Actual complete observer checks and corruption refusals')
    executed=values['author_execution']
    old_path=add(executed['corrected_from_execution_path'],executed['corrected_from_execution_sha256'])
    need(sha_file(old_path)==executed['corrected_from_execution_sha256'],'Exact original rollup identity')
    old_execution=read(old_path)
    need(old_execution['levels']==executed['levels'] and old_execution['build_sha256']==executed['build_sha256'] and
        old_execution['actual_source_mode_publication_sequences']==70,'Corrected counts reuse identical actual execution')
    correction_path=add(executed['rollup_correction_path'],executed['rollup_correction_sha256'])
    need(sha_file(correction_path)==executed['rollup_correction_sha256'],'Exact source-ledger correction identity')
    correction=read(correction_path)
    for key,wanted in dict(passed=True,original_public_flag_count=70,actual_source_mode_publication_sequences=68,
        genuine_initializer_RET_sequences=52,intentional_public_flag_forgery_sequences=2,controls=[158],
        native_rerun=False,source_or_worker_changed=False,
        corrected_from_execution_sha256=executed['corrected_from_execution_sha256']).items():
        need(correction[key]==wanted,'Explicit source-ledger correction/'+key)
    need(normalized(correction['corrected_from_execution_path'])==normalized(str(old_path)) and
        normalized(correction['tool_path'])==normalized(executed['rollup_correction_tool_path']) and
        correction['tool_sha256']==executed['rollup_correction_tool_sha256'],'Exact correction provenance')
    add(correction['tool_path'],correction['tool_sha256'])
    for level,info in executed['levels'].items():
        recorded=correction['archives'][level]
        need(normalized(recorded['path'])==normalized(info['bundle']) and recorded['sha256']==info['bundle_sha256'] and
            recorded['logical_files']==info['logical_files'],'Source-ledger correction binds unchanged '+level+' archive')
    equals('draft_model_audit',dict(ordinary_rows=48,model_comparisons=7824,current_native_proof_bound=False,
        qualifying_source_PCs=59,qualifying_source_accesses=35,qualifying_source_CALLs=5,
        genuine_source_initializer_RET=1,source_report_sha256=digest('recovery'),AFTER_machine_state_used_as_seed=False))
    audit=values['model_audit'];proof=audit['final_root_proof'];stage=config['observer_stage']
    equals('model_audit',dict(source_report_sha256=digest('recovery'),qualifying_source_PCs=59,
        model_comparisons=16944,
        qualifying_source_accesses=35,qualifying_source_CALLs=5,genuine_source_probe_RET=1,
        genuine_source_selector_RET=1,genuine_source_initializer_RET=1,separate_API_return_reads=2,
        whole_State_bytes=3504,whole_FX_bytes=512,whole_Runtime_CPU_bytes=40,captured_mappings=21,
        AFTER_machine_state_used_as_seed=False,author_expected_model_imported=False,
        post_initializer_fragment_caller_executed=False,lower_stack_bytes_original_observed=False,
        original_stack_guard_growth_proved=False,TIB_and_Policy_stack_limit_changed=False,
        current_phase_machine_W_R_Q_input_output_transport_sets_compared=2112,
        current_phase_return_progress8DWORD_sets_compared=2112,exact_unused_older_later_native_records_compared=2208,
        distinct_typed_ctor_private_owner_checks=144,complete_return_progress8DWORD_checked_in_every_phase=True,
        unused_heap_create_heap_mode_heap_version_ctor_registries_have_no_resource=True,
        actual_ordinary_initializer_RET_sequences=48,actual_ordinary_source_mode_publications=48,
        private_HANDLE_live_at_initializer_RET_checked=True,current_fault_reason=0))
    need(proof['execution_sha256']==digest('author_execution') and proof['observer_sha256']==digest('root_model') and
        proof['stage_sha256']==stage['sha256'],'Independent final audit binds actual root observer')
    need(audit['current_native_proof_bound'] and audit['current_native_compared'] and audit['ordinary_rows']==48 and
        audit['current_ordinary_native_rows_compared']==48 and audit['current_native_checkpoints_per_row']==44 and
        audit['current_fault_site']==0x78003a0b and audit['current_fault_target']==0x78001843,
        'Whole current native capture independently audited')
    need(verify_stage(stage['path'],stage['sha256'])['recorded_stage_passed'],'Stable successful root observer')
    command=read(Path(stage['path'])/'stage.json')
    need({normalized(p):h for p,h in command['artifact_sha256'].items()}.get(
        normalized(config['receipts']['root_model']['path']))==digest('root_model'),'Observer output association')
    for p in Path(stage['path']).iterdir():
        if p.is_file():add(p)
    native,hardware,seal,fixture=(values[k] for k in ('compiled_native','hardware_review','independent_seal','compiled_build'))
    equals('compiled_native',dict(native_scenarios=244,malformed_token_denials=44,counterfactual_direct_host_failure_queries=4,
        native_checks=15042,
        adopts_actual_native_execution=True,validates_actual_native_GetVersionExA=True,native_rerun=False,
        synthetic_API_results=False,declared_lower_stack_inputs=6,full_causal_source_model_oracle=False))
    need(native['compiled_sha256']==digest('compiled_build') and hardware['native_sha256']==digest('compiled_native'),
         'Independent fixture, actual corpus and hardware review association')
    equals('hardware_review',dict(actual_hardware_pairs=492,native_scenarios=244,hardware_semantic_denials=548,
        inventory_request_denials=68,actual_HeapCreate_calls=196,actual_successful_HeapDestroy_calls=196,
        actual_integrated_GetVersionExA_calls=132,actual_output_DWORD_commits=4078,actual_selector_RETs=90,
        actual_initializer_RETs=24,actual_source_mode_stores=66,actual_initializer_RETURN_WORD_reads=28,
        counterfactual_direct_host_failure_queries=4,
        synthetic_API_results=False,alternate_query_branch_live_coverage=False))
    need(hardware['native_checks']==native['native_checks']>0,'Actual independently reviewed assertion count')
    for role,name in (('source','source_contract'),('audit','source_audit'),('compiled','compiled_build'),
                      ('native','compiled_native'),('hardware','hardware_review')):
        item=seal['evidence'][role];bound=config['receipts'][name]
        need(item['sha256']==bound['sha256'] and normalized(item['path'])==normalized(bound['path']),
             'Independent aggregate binds exact '+role)
    for key in ('native_scenarios','actual_hardware_pairs','actual_HeapCreate_calls','actual_successful_HeapDestroy_calls',
        'actual_integrated_GetVersionExA_calls','actual_output_DWORD_commits','actual_selector_RETs','actual_initializer_RETs',
        'actual_source_mode_stores','actual_initializer_RETURN_WORD_reads','hardware_semantic_denials','inventory_request_denials'):
        need(seal[key]==hardware[key],'Independent aggregate exact '+key)
    need(seal['native_assertions']==native['native_checks'] and seal['malformed_token_denials']==44,
         'Final independent aggregate counters')
    need(fixture['compiled_only'] and {normalized(p):h for p,h in fixture['sources'].items()}[
        normalized(config['receipts']['build']['path'])]==digest('build'),'Fixture binds exact corrected production build')
    fixture_objects={}
    for category in CATEGORIES:
        if category.endswith('_objects'):
            for p,h in fixture.get(category,{}).items():
                key=normalized(p);need(key not in fixture_objects or fixture_objects[key]==h,'Consistent fixture object')
                fixture_objects[key]=h
    production={normalized(p):h for p,h in values['build']['entry_objects'].items()}
    need(len(production)==38 and fixture_objects==production,'All38 exact immutable COFF paths and hashes')
    need(len(fixture['libraries'])==len(values['build']['libraries'])==2 and
        {normalized(p):h for p,h in fixture['libraries'].items()}==
        {normalized(p):h for p,h in values['build']['libraries'].items()},'Both unchanged FDIV libraries')
    archives=[];verified_stages=[]
    packaging_path=add(native['packaging_path'],native['packaging_sha256'])
    need(sha_file(packaging_path)==native['packaging_sha256'],'Exact unchanged-tree partition publication')
    packaging=read(packaging_path)
    need(packaging['passed'] is True and packaging['native_rerun'] is False and
        packaging['transport_limits_changed'] is False and packaging['byte_identical_private_copies'] is True and
        packaging['copy_verified'] is True,'Bounded partitions retain original transport checks')
    partition_tool=add(packaging['partition_tool_path'],packaging['partition_tool_sha256'])
    need(sha_file(partition_tool)==packaging['partition_tool_sha256'] and
        packaging['partition_tool_sha256']=='30feabf8bc66b531e34721d0cc5914b13886b42409c5019e7ae7e380d53b1d81' and
        partition_tool==ROOT/'tools/m4-crt-heap-return-review/partition_copy.py',
        'Exact reviewed source-preserving copy tool')
    for kind,levels in (('author',values['author_execution']['levels']),('independent',native['levels'])):
        need(set(levels)=={'O0','O2'},'Exact optimization levels '+kind)
        for level,info in levels.items():
            expected_worker=(values['build']['workers'][level] if kind=='author' else
                str(Path(config['receipts']['compiled_build']['path']).parent/level/'controls.exe'))
            need(normalized(info['worker'])==normalized(expected_worker),'Exact compiled worker')
            owner=values['build'] if kind=='author' else fixture
            worker_sha={normalized(p):h for p,h in owner['artifacts'].items()}[normalized(info['worker'])]
            need(sha_file(info['worker'])==worker_sha,'Worker equals build artifact')
            s=Path(info['native_stage']);receipt=add(s/'stage.json');h=sha_file(receipt);checked=verify_stage(s,h)
            need(checked['recorded_stage_passed'],'Successful original actual native stage')
            if kind=='independent':need(h==info['native_stage_sha256'],'Fixed independent native stage')
            command=read(receipt);native_outputs={normalized(p):h for p,h in command['artifact_sha256'].items()}
            need([normalized(p) for p in command['argv']]==[normalized(p) for p in info['argv']],
                 'Exact native request paths')
            need(normalized(command['argv'][0])==normalized(info['worker']) and
                {normalized(p):h for p,h in command['input_sha256'].items()}.get(
                    normalized(info['worker']))==worker_sha,'Actual isolated compiled worker hash')
            need(native_outputs.get(normalized(str(Path(info['argv'][-1])/'COMPLETE')))==
                hashlib.sha256(b'COMPLETE').hexdigest(),'Native closed output association')
            for name in ('stdout.bin','stderr.bin'):add(s/name)
            verified_stages.append(dict(kind=kind,level=level,role='native_stage',verification=checked))
            parts=[dict(info,pack_source=info['argv'][-1])] if kind=='author' else info['bundles']
            need(len(parts)==(1 if kind=='author' else 2),'Exact bounded archive partitions')
            if kind=='independent':
                need([part['part'] for part in parts]==[1,2] and
                    [part['logical_files'] for part in parts]==[105543,125646] and info['logical_files']==231189,
                    'Exact ordered partition IDs and measured closed inventories')
            whole={};seen=set();controls=None;complete=None;part_maps=[]
            for part in parts:
                s=Path(part['pack_stage']);receipt=add(s/'stage.json');h=sha_file(receipt);checked=verify_stage(s,h)
                need(checked['recorded_stage_passed'],'Successful strict bounded archive stage')
                if kind=='independent':need(h==part['pack_stage_sha256'],'Fixed independent pack stage')
                command=read(receipt);outputs={normalized(p):h for p,h in command['artifact_sha256'].items()}
                if kind=='independent':
                    need({normalized(p):v for p,v in command['input_sha256'].items()}.get(
                        normalized(info['partition_map']))==info['partition_map_sha256'],
                        'Each strict pack stage binds the unchanged-source partition map')
                need(outputs.get(normalized(part['bundle']))==part['bundle_sha256'],'Exact pack output archive')
                wanted=[str(Path(sys.executable)),str(ROOT/'tools/m4-pipeline/capture_bundle.py'),
                        'pack',part['pack_source'],part['bundle']]
                need(len(command['argv'])==5 and command['argv'][2]=='pack' and
                    [normalized(command['argv'][i]) for i in (0,1,3,4)]==
                    [normalized(wanted[i]) for i in (0,1,3,4)],'Exact strict pack request, source and output')
                for name in ('stdout.bin','stderr.bin'):add(s/name)
                verified_stages.append(dict(kind=kind,level=level,role='pack_stage',verification=checked))
                h=part['bundle_sha256']
                part_actual={}
                with CaptureBundle(add(part['bundle'],h),h) as reader:
                    need(len(reader.names())==part['logical_files'],'Externally bound bounded archive inventory')
                    for name in reader.names():
                        need(name.casefold() not in seen,'No duplicated logical path across strict partitions')
                        seen.add(name.casefold());raw=reader.read_bytes(name)
                        whole[name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
                        part_actual[name]=whole[name]
                        if name=='COMPLETE':complete=raw
                        if name=='controls.json':controls=raw
                    if kind=='author':
                        need(info['logical_files']==96068,'Exact observed author archive size')
                        need({n.split('/')[0] for n in reader.names()}=={'COMPLETE','units'}|{f'row-{i}' for i in range(36)},
                             'Complete author top-level inventory')
                        for i in range(36):
                            result=json.loads(reader.read_bytes(f'row-{i}/result.json'),object_pairs_hook=unique_object)
                            need(result['passed'] is True and result['scenario']==i and result['control']==(0 if i<24 else i+133),
                                 'Complete author ordinary/fault requests')
                part_maps.append(part_actual)
                archives.append(dict(kind=kind,level=level,path=part['bundle'],sha256=h,logical_files=part['logical_files']))
            need(complete==b'COMPLETE' and len(whole)==info['logical_files'],'Exact disjoint complete archive union')
            if kind=='independent':
                inventory=add(info['inventory_path'],info['inventory_sha256'])
                need(sha_file(inventory)==info['inventory_sha256'] and read(inventory)['files']==whole,
                     'Exact complete original relative-path/hash inventory across partitions')
                level_package=packaging['levels'][level]
                need(normalized(level_package['source_tree'])==normalized(info['argv'][-1]) and
                    level_package['native_stage_sha256']==info['native_stage_sha256'] and
                    level_package['inventory_sha256']==info['inventory_sha256'] and
                    level_package['bundles']==parts,'Partition proof binds original closed native tree and exact archives')
                partition_map=add(info['partition_map'],info['partition_map_sha256'])
                need(sha_file(partition_map)==info['partition_map_sha256'],'Exact hardlink partition source map')
                need(not partition_map.is_relative_to(Path(info['argv'][-1])),
                    'Partition manifest is outside the original native source tree')
                mapping=read(partition_map)
                need(mapping['passed'] is True and mapping['source_files_modified'] is False and
                    mapping['hardlinks_only'] is False and mapping['byte_identical_copies_only'] is True and
                    mapping['original_relative_paths_preserved'] is True and
                    mapping['native_executed'] is False and mapping['transport_limit_unchanged']==200000 and
                    normalized(mapping['source'])==normalized(info['argv'][-1]) and mapping['files']==whole,
                    'Original completed source tree and preserved disjoint relative-path/hash union')
                need([claim['part'] for claim in mapping['parts']]==[1,2],'Two exact ordered strict map parts')
                for claim,part,actual_part in zip(mapping['parts'],parts,part_maps):
                    part_inventory=add(part['inventory_path'],part['inventory_sha256'])
                    need(sha_file(part_inventory)==part['inventory_sha256'] and claim['part']==part['part'] and
                        normalized(claim['pack_source'])==normalized(part['pack_source']) and
                        claim['logical_files']==part['logical_files'] and
                        read(part_inventory)['files']==claim['files']==actual_part,
                        'Each bounded archive belongs to its exact original source-map partition')
                    expected_tops={f'case-{i}' for i in range(1,62)} if part['part']==1 else {
                        f'case-{i}' for i in range(62,123)}
                    if part['part']==1:expected_tops|={'COMPLETE','controls.json','direct-query-failure-1','direct-query-failure-2'}
                    need({name.split('/')[0] for name in actual_part}==expected_tops,
                        'Exact whole-case partition assignment and separate diagnostics')
                partition_stage=Path(info['partition_stage']);h=info['partition_stage_sha256']
                need(verify_stage(partition_stage,h)['recorded_stage_passed'],'Successful unchanged-source partition stage')
                command=read(add(partition_stage/'stage.json',h))
                need({normalized(p):v for p,v in command['input_sha256'].items()}.get(
                    normalized(str(partition_tool)))==packaging['partition_tool_sha256'],
                    'Actual partition stage input binds the exact reviewed copy tool')
                wanted=[str(Path(sys.executable)),str(partition_tool),
                    info['argv'][-1],str(Path(parts[0]['pack_source']).parent),str(partition_map)]
                need([normalized(p) for p in command['argv']]==[normalized(p) for p in wanted] and
                    {normalized(p):v for p,v in command['artifact_sha256'].items()}.get(
                        normalized(str(partition_map)))==info['partition_map_sha256'],
                    'Exact source-tree partition request and closed map output')
                for name in ('stdout.bin','stderr.bin'):add(partition_stage/name)
                need(native_outputs.get(normalized(str(Path(info['argv'][-1])/'controls.json')))==
                    hashlib.sha256(controls).hexdigest(),'Exact native result/archive union association')
                result=json.loads(controls,object_pairs_hook=unique_object)
                need(result==info['result'] and result['passed'] is True and result['scenarios']==122 and
                    result['malformed_token_denials']==22 and result['direct_host_failure_queries']==2 and
                    result['synthetic_API_results'] is False,'Complete independent actual requests')
    need(native['native_checks']==sum(v['result']['checks'] for v in native['levels'].values()),'Actual assertion aggregate')
    # Current native corpora remain archived. Exactly two older uncredited samples may survive their failure receipt.
    historical_samples={
        normalized(str(ROOT/'reports/m4-crt-heap-version-review/native-r1/actual-O0/case-47/writer-host-before.bin')):
            '2249e4ddeee6333aac29b3a60af606241067de4286f21cd873510032d0ce767d',
        normalized(str(ROOT/'reports/m4-crt-heap-version-review/native-r1/actual-O0/case-47/writer-host-after.bin')):
            'c272aeb3a1ea03cb19c14a26d690318410c7e68998426c258f6015185c5c92a4'}
    flat={p:h for p,h in files.items() if '/actual-o' in p.replace('\\','/') and '/case-' in p.replace('\\','/')}
    need(not flat or flat==historical_samples,'No expansion of current flat captures')
    failure_path=ROOT/'reports/m4-crt-heap-version-review/failed-native-r1/report.json'
    need(any(normalized(x['path'])==normalized(str(failure_path)) and x['sha256']==
        '33b04d1f74afbbccb3cec2b33fb2f85119e7f1e29ba5837f9a3cef912a701811' for x in config['history']),
        'Prior hardware refusal kept without success credit')
    failure=read(failure_path);need(failure['passed'] is False and failure['current_proof_credit'] is False and
        failure['validator_weakened'] is False and failure['current_candidate_entered_at_failure'] is False and
        all(failure['files'][p]==h for p,h in historical_samples.items()),
        'Strict historic hardware checks and exact refused samples retained')
    for p in (Path(__file__),Path(__file__).with_name('create_config.py'),Path(__file__).with_name('final_check.py'),
              Path(sys.executable)):add(p)
    closure=verify_manifest(files);out.mkdir()
    publish_bytes(out/'pins.json',(json.dumps(dict(files=files),indent=2)+'\n').encode())
    report=dict(passed=True,scope='Actual source mode1 heap publication and genuine initializer RET; STOP before fragment caller',
        receipts=config['receipts'],history=config['history'],documents=config['documents'],files=files,
        physical_closure=closure,pins_sha256=sha_file(out/'pins.json'),archives=archives,verified_stages=verified_stages,
        historical_receipts_expanded=False,independent_root_native_execution_count=0,
        author_normal_sequences=48,author_fault_sequences=24,root_original_BEFORE_sequences=48,
        root_model_checks=values['root_model']['checks'],root_model_corruption_denials=values['root_model']['selected_semantic_byte_corruption_denials'],
        root_full_causal_model_sequences=0,independent_compiled_scenarios=244,independent_compiled_checks=native['native_checks'],
        total_integrated_native_scenarios=316,actual_hardware_pairs=492,
        author_actual_HeapCreate_calls=72,author_actual_successful_HeapDestroy_calls=72,
        independent_actual_HeapCreate_calls=196,independent_actual_successful_HeapDestroy_calls=196,
        author_actual_GetVersionExA_calls=72,author_actual_API_output_DWORD_commits=2664,
        independent_actual_GetVersionExA_calls=132,independent_actual_API_output_DWORD_commits=4078,
        author_selector_RET_sequences=72,author_mode_store_sequences=68,author_initializer_RET_sequences=52,
        independent_selector_RET_sequences=90,independent_mode_store_sequences=66,independent_initializer_RET_sequences=24,
        ordinary_initializer_RET_sequences=48,counterfactual_direct_host_failure_queries=4,
        hardware_semantic_denials=hardware['hardware_semantic_denials'],inventory_request_denials=hardware['inventory_request_denials'],
        new_guest_objects=0,unchanged_guest_objects=38,new_guest_compiled_bytes=0,reused_compiled_bytes=230,
        executed_source_bytes=192,total_source_identity_bytes=2086,whole_State_bytes=3504,whole_FX_bytes=512,
        whole_Runtime_CPU_bytes=40,full_pages=21,prior_pages_preserved=21,checkpoints_per_ordinary_row=44,
        source_PCs=59,source_accesses=35,actual_source_CALLs=5,genuine_probe_RET=1,genuine_selector_RET=1,genuine_initializer_RET=1,
        distinct_API_return_reads=2,separate_API_output_DWORDs=37,complete_API_input_and_output_bytes=148,
        terminal_EIP=0x78001843,terminal_ESP=0x2000185c,terminal_EAX=1,heap_mode_global_value=1,
        heap_mode_global_published=True,heap_initializer_RET=True,qualifying_source_initializer_completed=True,
        full_heap_allocator_initialized=False,heap_initialized=False,fragment_caller_executed=False,
        original_attach_proved=False,full_CRT_complete=False,whole_M4_complete=False,
        ordinary_game_launched=False,original_executed=False,environment_API_executed=False,
        selected_initializer_roots=27,selected_initializer_inventory=144,
        scheduler_State_projection='EIP only',host_guest_source_execution_stores=0,generic_Runtime_CPU_preserved=True,
        lower_stack_original_observed=False,original_guard_stack_growth_proved=False,TIB_and_Policy_changed=False,
        undefined_AF_universal_original_equivalence=False,original_API_internals_or_manifest_response_universal_equivalence=False,
        initial_metadata_loss_cause_proved=False,historical_hardware_sample_success_credit=False,
        seconds=(time.perf_counter_ns()-started)/1e9)
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','receipts','history','documents','archives','verified_stages')}))
if __name__=='__main__':main(*sys.argv[1:])
