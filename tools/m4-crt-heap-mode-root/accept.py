"""Admit the genuine selector/probe path to its unresolved version-query CALL."""
import json
from pathlib import Path
import sys
import time
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
BASE=ROOT/'reports/m4-crt-heap-mode-root'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from capture_bundle import CaptureBundle,sha_file
from manifests import normalized,unique_object,verify_manifest
from paths import publish_bytes,workspace_path
from stages import verify_stage

NAMES={'recovery','source_contract','preparation','build','author_execution','root_model',
       'source_audit','draft_model_audit','model_audit','compiled_build','compiled_native',
       'hardware_review','independent_seal'}
CATEGORIES=('files','sources','source_files','tools','tool_files','libraries','entry_objects',
    'matherr_objects','control_objects','initterm_objects','mainargs_objects','normal_argv_objects',
    'producer_objects','parser_objects','locale_objects','heap_objects','heap_mode_objects',
    'compiler_read_headers','artifacts','input_files')


def need(value,why):
    if not value: raise ValueError(why)


def read(path):
    return json.loads(Path(path).read_bytes(),object_pairs_hook=unique_object)


def main(config_path,config_sha,directory):
    started=time.perf_counter_ns();out=workspace_path(directory,reports=True)
    need(out.parent==BASE and not out.exists(),'Fresh acceptance output')
    files={}
    def add(path,digest=None):
        path=Path(path).absolute();key=normalized(str(path));value=sha_file(path) if digest is None else digest
        need(key not in files or files[key]==value,'Consistent current dependency '+str(path))
        files[key]=value;return path
    config=read(add(config_path,config_sha))
    need(sha_file(config_path)==config_sha,'External admission config digest')
    need(set(config)=={'receipts','pins','history','documents','observer_stage'},'Exact config schema')
    need(set(config['receipts'])==NAMES,'All independent current proof domains')
    values={}
    for name,item in config['receipts'].items():
        need(set(item)=={'path','sha256'},'Exact receipt identity')
        path=add(item['path'],item['sha256']);need(sha_file(path)==item['sha256'],'Fixed receipt '+name)
        value=read(path);need(value['passed'] is True,'Successful receipt '+name);values[name]=value
        for field in ('whole_M4_complete','original_executed','ordinary_game_launched',
                      'GetVersionExA_executed','heap_mode_selected','mode_selected',
                      'heap_initialized','initializer_RET_executed','source_initializer_RET_executed'):
            if field in value: need(value[field] is False,'Bounded scope '+name+'/'+field)
        for category in CATEGORIES:
            for p,h in value.get(category,{}).items(): add(p,h)
    for item in config['pins']:
        path=add(item['path'],item['sha256']);need(sha_file(path)==item['sha256'],'Fixed pin map')
        for p,h in read(path)['files'].items(): add(p,h)
    # Historical receipt identities are retained without reopening their old closures.
    for item in config['history']+config['documents']:
        path=add(item['path'],item['sha256']);need(sha_file(path)==item['sha256'],'Fixed history/document')
    def equals(name,wanted):
        for key,value in wanted.items(): need(values[name].get(key)==value,name+'/'+key)
    def digest(name): return config['receipts'][name]['sha256']
    need(values['build']['preparation_sha256']==values['source_audit']['preparation_sha256']==digest('preparation'),
         'Compiled and independently audited exact preparation')
    need(values['author_execution']['build_sha256']==values['source_audit']['build_sha256']==digest('build'),
         'Executed and independently audited exact production build')
    counts=values['recovery']['counts']
    for k,v in dict(total_source_instructions=39,total_source_accesses=24,source_CALLs=5,
        actual_probe_RET=1,selector_RET=0,new_guarded_compiled_source_bytes=86,
        total_heap_executed_source_bytes=132,separate_carried_HeapCreate_API_return_reads=1).items():
        need(counts[k]==v,'Original recovered counts/'+k)
    query=values['recovery']['unresolved_query_contract']
    need(query['source_CALL']==0x78003a2b and query['source_IAT']==0x7802e0a0 and
         query['raw_target']==0x34600 and query['source_size_DWORD']==148 and
         query['API_executed'] is False and query['API_returned'] is False and
         query['API_output_produced'] is False and query['whole_structure_initialized'] is False,
         'Exact unresolved original query frontier')
    equals('source_contract',dict(combined_source_PCs=39,combined_source_accesses=24,
        combined_actual_source_CALLs=5,genuine_probe_RET_count=1,new_compiled_source_bytes=86,
        new_executed_source_bytes=84,combined_executed_source_bytes=132,combined_source_identity_bytes=2026,
        separate_HeapCreate_API_return_reads=1,GetVersionExA_executed=False,query_outcome_invented=False,
        source_mode_selector_RET_executed=False,mode_selected=False,heap_initialized=False,native_executed=False))
    maps=values['source_contract']['mapping_contract']
    need(maps['total_mappings']==20 and maps['prior_mappings']==18 and
         maps['original_policy_and_TIB_metadata_preserved'] is True and
         maps['original_guard_growth_equivalence'] is False and maps['lower_stack_original_capture_equivalence'] is False,
         'Declared research lower page and preserved original stack metadata')
    equals('preparation',dict(source_identity_bytes=2026,reused_compiled_source_bytes=84,new_compiled_source_bytes=86,
        new_guest_objects=4,reused_guest_objects=26,success_executed_source_bytes=132,source_accesses=24,source_PCs=39,
        separate_API_return_reads=1,borrowed_pages=20,prior_pages_preserved=18,Policy_and_TIB_unchanged=True,
        State_bytes=3504,FX_bytes=512,State_reseed_after_writer=False,Runtime_CPU_preserved=True,
        Runtime_call_record_added=False,scheduler_store_count=0,scheduler_State_projection='EIP only',
        OS_query_called=False,heap_mode_selected=False,initializer_RET_executed=False,native_component_executed=False))
    equals('source_audit',dict(reused_guest_objects=26,new_guest_objects=4,unchanged_FDIV_libraries=2,
        new_compiled_guarded_bytes=86,executed_success_bytes=132,source_PCs=39,source_accesses=24,
        separate_API_return_reads=1,borrowed_pages=20,prior_pages_preserved=18,GetVersionExA_executed=False,
        original_stack_guard_growth_proved=False,original_lower_stack_bytes_equivalent=False,native_executed=False))
    equals('author_execution',dict(positive_sequences=48,causal_sequences=24,native_stages_completed=2,
        native_executed_by_author=True,actual_HeapCreate_calls=72,actual_owned_results=72,
        actual_successful_HeapDestroy_calls=72,injected_zero_result_sequences=0,
        injected_pre_OS_cleanup_skip_sequences=0,source_PCs=39,source_accesses=24,genuine_probe_RET_executed=True,
        first_OS_query_executed=False,declared_ordinary_lower_stack_input_zero=True,borrowed_pages=20,
        API_guest_model_universal_original_equivalence_claimed=False,heap_mode_selected=False,initializer_RET_executed=False))
    equals('root_model',dict(original_BEFORE_ordinary_sequences=48,checks=155741,
        selected_semantic_byte_corruption_denials=2352,root_full_causal_model_sequences=0,
        whole_State_bytes=3504,whole_FX_bytes=512,whole_Runtime_CPU_bytes=40,whole_pages=20,
        source_identity_bytes=2026,new_compiled_source_bytes=86,reused_heap_source_bytes=84,executed_source_bytes=132,
        source_PCs=39,source_accesses=24,actual_source_CALLs=5,genuine_stack_probe_RET=1,distinct_API_return_reads=1,
        host_guest_stack_stores=0,generic_Runtime_CPU_preserved=True,source_RET_executed=True,
        heap_initializer_RET=False,GetVersionExA_executed=False,heap_mode_selected=False,
        main_initializer_count=27,independently_executed_by_root=False,execution_sha256=digest('author_execution'),
        author_expected_model_imported=False,AFTER_machine_state_used_as_seed=False,
        lower_stack_original_observed=False,original_guard_stack_growth_proved=False,TIB_and_Policy_changed=False))
    equals('draft_model_audit',dict(ordinary_rows=48,model_comparisons=4044,current_native_proof_bound=False,
        source_report_sha256=digest('recovery'),AFTER_machine_state_used_as_seed=False,author_expected_model_imported=False))
    equals('model_audit',dict(ordinary_rows=48,model_comparisons=11052,current_native_proof_bound=True,
        current_native_compared=True,current_ordinary_native_rows_compared=48,current_native_checkpoints_per_row=34,
        current_phase_machine_and_W_R_metadata_pairs_compared=1632,exact_unused_older_later_native_records_compared=1248,
        distinct_typed_heap_create_ctor_and_heap_mode_resource_owners=48,inactive_heap_create_ctor_registry_has_no_resource=True,
        actual_named_host_HeapCreate_results_witnessed=48,actual_owned_host_HeapDestroy_successes_witnessed=48,
        source_report_sha256=digest('recovery'),actual_source_PCs=39,actual_source_accesses=24,actual_source_CALLs=5,
        genuine_source_probe_RET=1,separate_API_return_reads=1,captured_mappings=20,
        AFTER_machine_state_used_as_seed=False,author_expected_model_imported=False,
        lower_stack_bytes_original_observed=False,original_stack_guard_growth_proved=False,
        TIB_and_Policy_stack_limit_changed=False,query_API_output_produced=False,GetVersionExA_executed=False,
        selector_RET_executed=False,source_initializer_RET_executed=False))
    proof=values['model_audit']['final_root_proof'];stage=config['observer_stage']
    need(proof['execution_sha256']==digest('author_execution') and proof['observer_sha256']==digest('root_model')
         and proof['stage_sha256']==stage['sha256'],'Final independent audit binds actual root proof')
    need(verify_stage(stage['path'],stage['sha256'])['recorded_stage_passed'],'Stable successful observer stage')
    command=read(Path(stage['path'])/'stage.json')
    need({normalized(p):h for p,h in command['artifact_sha256'].items()}[normalized(config['receipts']['root_model']['path'])]
         ==digest('root_model'),'Observer output association')
    for p in Path(stage['path']).iterdir():
        if p.is_file(): add(p)
    native=values['compiled_native'];hardware=values['hardware_review'];seal=values['independent_seal']
    equals('compiled_native',dict(native_scenarios=132,native_checks=6770,malformed_token_denials=38,
        original_executed=False,ordinary_game_launched=False,full_causal_source_model_oracle=False,whole_M4_complete=False))
    need(native['compiled_sha256']==digest('compiled_build'),'Actual independent corpus binds fixture build')
    need(hardware['native_sha256']==digest('compiled_native'),'Independent hardware review binds actual corpus')
    need(hardware['actual_hardware_pairs']==264 and hardware['native_scenarios']==132 and
         hardware['native_checks']==6770 and hardware['hardware_semantic_denials']==548 and
         hardware['inventory_request_denials']==39 and hardware['actual_HeapCreate_calls']==84 and
         hardware['actual_successful_HeapDestroy_calls']==84 and
         hardware['declared_initial_lower_stack_patterns']==6 and hardware['probe_return_proved'] is True,
         'Exact independently reviewed132-row hardware and heap lifecycle corpus')
    fixture=values['compiled_build']
    need(fixture['compiled_only'] is True and
         {normalized(p):h for p,h in fixture['sources'].items()}[normalized(config['receipts']['build']['path'])]==digest('build'),
         'Independent fixture compile binds production build')
    # Final independent aggregate identities and counts are validated below.
    validate_independent_seal(seal,values,config)
    archives=[];verified_stages=[]
    for kind,levels in (('author',values['author_execution']['levels']),('independent',native['levels'])):
        need(set(levels)=={'O0','O2'},'Exact optimization levels '+kind)
        for level,info in levels.items():
            for key in ('native_stage','pack_stage'):
                s=Path(info[key]);receipt=add(s/'stage.json');h=sha_file(receipt)
                checked=verify_stage(s,h);need(checked['recorded_stage_passed'],'Successful actual native/archive stage')
                if kind=='independent': need(h==info[key+'_sha256'],'Externally bound independent stage')
                command=read(receipt)
                if key=='native_stage':
                    need([normalized(p) for p in command['argv']]==[normalized(p) for p in info['argv']],
                         'Exact native worker request')
                    need(normalized(command['argv'][0])==normalized(info['worker']),'Actual isolated worker')
                for name in ('stdout.bin','stderr.bin'): add(s/name)
                verified_stages.append(dict(kind=kind,level=level,role=key,verification=checked))
            h=info['bundle_sha256']
            with CaptureBundle(add(info['bundle'],h),h) as reader:
                need(reader.read_bytes('COMPLETE')==b'COMPLETE','Closed strict capture')
                need(len(reader.names())==info['logical_files'],'Exact externally bound capture inventory')
                if kind=='author':
                    need(info['logical_files']==61659,'Exact author archive size')
                    for i in range(36):
                        result=json.loads(reader.read_bytes(f'row-{i}/result.json'),object_pairs_hook=unique_object)
                        need(result['passed'] and result['scenario']==i and result['control']==(0 if i<24 else i+109),
                             'Complete author row request')
                else:
                    need(info['logical_files']==84732,'Exact independent archive size')
                    result=json.loads(reader.read_bytes('controls.json'),object_pairs_hook=unique_object)
                    need(result==info['result'] and result['passed'] and result['scenarios']==66
                         and result['checks']==3385 and result['malformed_token_denials']==19,
                         'Complete closed independent request corpus')
            archives.append(dict(kind=kind,level=level,path=info['bundle'],sha256=h,logical_files=info['logical_files']))
    need(not any('/actual-o' in p.replace('\\','/') and '/case-' in p.replace('\\','/') for p in files),
         'Current independent evidence is strict archives, without flat capture expansion')
    for p in (Path(__file__),Path(__file__).with_name('create_config.py'),Path(__file__).with_name('final_check.py'),Path(sys.executable)):
        add(p)
    closure=verify_manifest(files);out.mkdir()
    publish_bytes(out/'pins.json',(json.dumps(dict(files=files),indent=2)+'\n').encode())
    report=dict(passed=True,scope='Genuine x64 selector prologue and relocated probe RET to unresolved original GetVersionExA CALL',
        receipts=config['receipts'],history=config['history'],documents=config['documents'],files=files,
        physical_closure=closure,pins_sha256=sha_file(out/'pins.json'),archives=archives,verified_stages=verified_stages,
        historical_receipts_expanded=False,independent_root_native_execution_count=0,
        author_normal_sequences=48,author_fault_sequences=24,root_original_BEFORE_sequences=48,
        root_model_checks=155741,root_model_corruption_denials=2352,root_full_causal_model_sequences=0,
        independent_compiled_scenarios=132,independent_compiled_checks=6770,actual_hardware_pairs=264,
        hardware_semantic_denials=hardware['hardware_semantic_denials'],inventory_request_denials=hardware['inventory_request_denials'],
        author_actual_HeapCreate_calls=72,author_actual_successful_HeapDestroy_calls=72,
        independent_actual_HeapCreate_calls=hardware['actual_HeapCreate_calls'],
        independent_actual_successful_HeapDestroy_calls=hardware['actual_successful_HeapDestroy_calls'],
        new_guest_objects=4,unchanged_guest_objects=26,new_guest_compiled_bytes=86,reused_compiled_source_bytes=84,
        executed_source_bytes=132,total_source_identity_bytes=2026,whole_State_bytes=3504,whole_FX_bytes=512,
        whole_Runtime_CPU_bytes=40,full_pages=20,prior_pages_preserved=18,checkpoints_per_ordinary_row=34,
        source_PCs=39,source_accesses=24,actual_source_CALLs=5,genuine_probe_RET=1,distinct_API_return_reads=1,
        host_guest_execution_stores=0,State_projection='EIP only',generic_Runtime_CPU_preserved=True,
        terminal_EIP=0x34600,terminal_ESP=0x20000618,query_source_CALL=0x78003a2b,query_import=0x7802e0a0,
        query_struct_pointer=0x200017b8,only_query_size_DWORD_initialized=True,
        lower_stack_initial_input_declared=True,lower_stack_original_observed=False,original_guard_stack_growth_proved=False,
        TIB_and_Policy_changed=False,undefined_AF_universal_original_equivalence=False,
        source_AF_representatives={str(pc):0 for pc in (0x780039bf,0x780039d6,0x780058db,0x780058c5)},
        GetVersionExA_executed=False,heap_mode_selected=False,selector_RET=False,heap_initializer_RET=False,
        heap_initialized=False,locale_initialized=False,argument_initialization_complete=False,
        selected_initializer_roots=27,selected_initializer_inventory=144,full_CRT_complete=False,
        original_attach_proved=False,ordinary_game_launched=False,original_executed=False,whole_M4_complete=False,
        seconds=(time.perf_counter_ns()-started)/1e9)
    publish_bytes(out/'report.json',(json.dumps(report,indent=2)+'\n').encode())
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','receipts','history','documents','archives','verified_stages')}))


def validate_independent_seal(seal,values,config):
    for key,wanted in dict(native_scenarios=132,native_assertions=6770,actual_hardware_pairs=264,
        malformed_token_denials=38,new_guest_objects=4,reused_guest_objects=26,
        declared_initial_lower_stack_patterns=6,author_controls_per_optimization=12,
        independent_controls_per_optimization=48,new_nonzero_caller_error_fixture=False,
        full_causal_source_model_oracle=False,original_executed=False,ordinary_game_launched=False,
        whole_M4_complete=False).items():
        need(seal.get(key)==wanted,'Independent final aggregate/'+key)
    for role,name in (('source','source_contract'),('audit','source_audit'),('native','compiled_native'),('hardware','hardware_review')):
        item=seal['evidence'][role];bound=config['receipts'][name]
        need(item['sha256']==bound['sha256'] and normalized(item['path'])==normalized(bound['path']),
             'Independent final aggregate exact evidence '+role)
    for key in ('actual_HeapCreate_calls','actual_successful_HeapDestroy_calls','hardware_semantic_denials','inventory_request_denials'):
        need(seal[key]==values['hardware_review'][key],'Independent exact reviewed count '+key)
    need(seal['actual_HeapCreate_calls']==seal['actual_successful_HeapDestroy_calls']>0,
         'Every actual independent created heap released successfully')


if __name__=='__main__': main(*sys.argv[1:])
