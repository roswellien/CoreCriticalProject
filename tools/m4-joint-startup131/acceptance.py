"""Grant one inventory root only after the complete current131 evidence closes.

The accepted130 receipt retains its finite proofs. Every new current sequence,
source/provider comparison, pairing policy and connected fault control must
agree with the physically reviewed workers. The final union is freshly hashed.
"""
from pathlib import Path
import hashlib, json, sys, time, traceback

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import normalized, digest, unique_object, verify_manifest

PARENT_SHA='12215395619ea72ee1a587763112bc3a2ed9aad15c9c99a5697f69c9658429aa'
REQUIRED={
    'parent','native_preparation','native_build','native_prelaunch','native_execution',
    'original_preparation','original_build','original_prelaunch','original_execution',
    'original_validation','original_source','original_source_review',
    'original_old_source','original_old_source_review',
    'source_preparation','source_preflight','source_legacy_flags','source_provider','source_provider_review','source_new_mfc_review','source_closure',
    'pair_preparation','pair_policy_review','loaded_input_relation','paired','paired_review',
    'controls_preparation','controls_build','controls_prelaunch','controls_execution',
    'controls','controls_review','controls_equivalence',
}
PINS={}

def need(value,label):
    if not value:raise ValueError(label)

def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def register(path,identity):
    key=normalized(str(Path(path).resolve()));identity=digest(identity)
    need(key not in PINS or PINS[key]==identity,'Conflict-free physical dependency '+key)
    PINS[key]=identity

def read(path,identity=None):
    path=Path(path).resolve();actual=sha(path)
    need(identity is None or identity==actual,'Exact current receipt '+str(path));register(path,actual)
    return json.loads(path.read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)

def absorb(report):
    for field in('files','physical_inputs','physical_dependencies','generated_sources','sources','tools','artifacts','retained_capture_inputs'):
        for path,identity in report.get(field,{}).items():register(path,identity)

def value_at(report,field):
    for key in field.split('.'):report=report[int(key)]if isinstance(report,list)else report[key]
    return report

def typed_equal(actual,expected,label):need(type(actual)is type(expected)and actual==expected,'Exact typed '+label)

def has(report,path,identity):
    target=normalized(str(Path(path).resolve()))
    return any(normalized(str(Path(p).resolve()))==target and h==identity
        for field in('files','physical_inputs','physical_dependencies','generated_sources','sources','tools','artifacts')
        for p,h in report.get(field,{}).items())

def semantic_checks(rows,gates):
    parent=rows['parent']
    typed_equal(gates['parent']['sha256'],PARENT_SHA,'accepted130 identity')
    for field,expected in dict(connected_roots=130,remaining_inventory_roots=14,whole_M4_complete=False,native_game_launch_complete=False).items():typed_equal(parent[field],expected,'parent '+field)
    preparation=rows['native_preparation'];original=rows['original_preparation']
    prior=read(preparation['parent_joint130_preparation'],'060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c')
    order=preparation['selected_order']
    need(len(order)==131 and len({row['entry']for row in order})==131,'All131 distinct current selected roots')
    need(order[13]==dict(entry=0x5ae3e4,slot=0x5e0040),'Actual new MFC physical slot13')
    need([row for row in order if row['entry']!=0x5ae3e4]==prior['selected_order'],'All130 parent roots and relative order retained')
    need(original['selected_order']==order,'Same actual original/native current schedule')
    typed_equal(preparation['current_registration_callbacks'],101,'Current callback inventory')
    need(len(prior['registration_roots'])==101,'Entire parent callback inventory')
    for leaf in ('registration_contract.hpp',):
        current=Path(gates['native_preparation']['path']).parent/leaf
        previous=Path(preparation['parent_joint130_preparation']).parent/leaf
        need(sha(ROOT/current)==sha(previous),'Whole parent registration callbacks retained')
        register(ROOT/current,sha(ROOT/current));register(previous,sha(previous))
    for label in('native_build','native_execution'):
        typed_equal(rows[label]['build_sha256']if label=='native_execution'else rows[label]['preparation_sha256'],gates['native_build'if label=='native_execution'else'native_preparation']['sha256'],label+' physical lineage')
    typed_equal(rows['native_prelaunch']['build_sha256'],gates['native_build']['sha256'],'native whole-link admission')
    typed_equal(rows['native_execution']['admission_review_sha256'],gates['native_prelaunch']['sha256'],'actual native prelaunch execution')
    typed_equal(rows['native_execution']['all_bounded_readers_closed'],True,'native strict readers closed')
    typed_equal(rows['native_execution']['all_workers_terminal'],True,'native workers terminal')
    need([row['level']for row in rows['native_execution']['levels']]==['O0','O2'],'Both actual compiler levels')
    for label in('original_execution','original_validation'):
        typed_equal(rows[label]['build_sha256'],gates['original_build']['sha256'],'actual original '+label)
    typed_equal(rows['original_build']['preparation_sha256'],gates['original_preparation']['sha256'],'original preparation lineage')
    typed_equal(rows['original_source']['original_validation_sha256'],gates['original_validation']['sha256'],'fresh six-domain source input')
    typed_equal(rows['original_source_review']['current_source_sha256'],gates['original_source']['sha256'],'independent new original source audit')
    for field,expected in dict(phases=786,MFC_original_phases=6,MFC_full_normal_boundaries=42,MFC_full_named_API_pairs=24,MFC_true_root_TIB8192_endpoints=12,MFC_whole_borrowed_backing_endpoints=60,MFC_codepage_CS24_endpoints=12).items():typed_equal(rows['original_validation']['counts'][field],expected,'genuine original extent '+field)
    source=rows['source_provider'];lineage=source['executed_lineage']
    for field,expected in dict(conditional_PCs=2,source_consumers_per_sequence=171,capture_reader_opened=False,worker_executed=False,initializer_credit=0).items():typed_equal(rows['source_legacy_flags'][field],expected,'Finite legacy flag source proof '+field)
    typed_equal(lineage['execution_sha256'],gates['native_execution']['sha256'],'source exact current native execution')
    typed_equal(lineage['build_sha256'],gates['native_build']['sha256'],'source exact current native build')
    typed_equal(lineage['joint_preparation_sha256'],gates['native_preparation']['sha256'],'source exact current preparation')
    for field in('reader_closed','source_and_provider_combined','complete_selected_source','complete_provider_lifecycle','worker_post_HeapDestroy_identity_observed'):typed_equal(source[field],True,'complete current source/provider '+field)
    for field in('per_phase_BEFORE_machine_seed','candidate_AFTER_machine_seed','canonical_reader_changed','duplicate_selected_source_reader','native_CS40_opaque_copy','native_DllMain_credit'):typed_equal(source[field],False,'bounded current source/provider '+field)
    expected=dict(persistent131_sequences=12,persistent_phases=1572,whole_page_BEFORE=72312,whole_page_AFTER=72312,MFC_literal_phases=12,MFC_source_instructions=1704,MFC_source_operands=1356,MFC_typed_API_CPU_frame_relations=48,MFC_whole_region_BEFORE=144,MFC_whole_region_AFTER=144,MFC_whole_State_CPU_FX=12,MFC_owned_resource_lifecycles=12,MFC_actual_API_identity_CS40_sides=312,MFC_whole_actual_caller_FX512_ENV28=12)
    for field,count in expected.items():typed_equal(source['counts'][field],count,'complete new/current source extent '+field)
    cases=source['provider_sequences'];need(len(cases)==12 and {(row['level'],row['sequence'])for row in cases}=={(level,seq)for level in('O0','O2')for seq in range(6)},'All12 inherited provider chains actually rerun')
    total=sum(row['compared_checkpoints']for row in cases);need(total>0,'Measured current provider checkpoints')
    for field in('whole_State_checkpoints','whole_CPU_checkpoints','whole_FX_checkpoints'):typed_equal(source['provider_counts'][field],total,'complete provider '+field)
    for case in cases:
        capacity=case['first_replay_msize_capacity']
        need(case['all_resources_released']and case['actual_post_HeapDestroy_identity'],'Actual whole same-owner native lifecycle complete')
        need(case['selected_used_bytes']==404 and capacity>=404 and capacity%4==0 and case['predicted_growth_replays']==case['actual_growth_replays']==(capacity-404)//4+1,'Source-predicted actual registry capacity/growth')
    paired=rows['paired'];need(paired['reader_closed']and paired['paired_initialization_data_contract'],'Fresh complete current source-backed pair')
    for field in('blanket_page_mask','original_and_native_bytes_modified','whole_game_liveness_proven','loaded_input_native_DllMain_credit'):typed_equal(paired[field],False,'explicit paired bound '+field)
    for label,target in(('source_provider_review','source_provider'),('source_new_mfc_review','source_provider'),('source_closure','source_provider'),('original_old_source_review','original_old_source'),('paired_review','paired'),('controls_review','controls')):
        need(has(rows[label],ROOT/gates[target]['path'],gates[target]['sha256']),'Independent exact physical evidence edge '+label+' -> '+target)
    typed_equal(rows['controls_execution']['build_sha256'],gates['controls_build']['sha256'],'Actual connected control build')
    typed_equal(rows['controls_build']['preparation_sha256'],gates['controls_preparation']['sha256'],'Current connected control preparation')
    typed_equal(rows['controls_prelaunch']['build_sha256'],gates['controls_build']['sha256'],'Whole connected control link admission')
    # All accepted parent dependencies stay in the final union. Current gates
    # must add their complete archive parts, not merely transport receipts.
    for path,identity in parent['files'].items():need(PINS.get(normalized(str(Path(path).resolve())))==identity,'Entire accepted130 proof retained')

def main(configuration,name,review_path,review_sha):
    started=time.perf_counter();out=ROOT/'reports/m4-joint-startup131-root'/name
    need(not out.exists(),'Fresh complete acceptance');out.mkdir(parents=True)
    passed=False;config={};closure={};predicates=0
    try:
        config=read(configuration);register(__file__,sha(__file__))
        need(set(config['gates'])==REQUIRED,'All mandatory current131 evidence gates')
        for field in('configuration_source','review_specification'):
            register(config[field],config[field+'_sha256'])
        review=read(review_path,review_sha);absorb(review)
        need(review['passed']and review['gates_reviewed']==len(REQUIRED)and has(review,configuration,sha(configuration))and has(review,__file__,sha(__file__)),'Independent sealed exact current acceptance configuration')
        rows={}
        for label,gate in config['gates'].items():
            need(set(gate)=={'path','sha256','equal'}and len(gate['equal'])>=2,'Exact measured gate schema '+label)
            path=ROOT/gate['path'];report=read(path,gate['sha256'])
            typed_equal(report['passed'],True,'passed current gate '+label);absorb(report)
            sibling=path.parent/'pins.json'
            if sibling.exists():absorb(read(sibling))
            for field,expected in gate['equal'].items():typed_equal(value_at(report,field),expected,label+':'+field);predicates+=1
            rows[label]=report
        semantic_checks(rows,config['gates'])
        closure=verify_manifest(PINS)
        need(closure['passed']and closure['metadata_only_cache_used']is False,'Fresh complete historical/current physical union rehash')
        passed=True
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        result=dict(passed=passed,scope='Connected selected131 startup inventory with current original/native/source/provider/pair and connected MFC refusals',connected_roots=131 if passed else 130,new_roots=1 if passed else 0,total_inventory_roots=144,remaining_inventory_roots=13 if passed else 14,initializer_inventory_fraction=(131 if passed else 130)/144,inventory_is_project_completion_percentage=False,gates=config.get('gates',{}),explicit_measured_predicates=predicates,physical_closure=closure,elapsed_seconds=time.perf_counter()-started,whole_M4_complete=False,native_game_launch_complete=False,native_menu=False,native_Training=False,files=PINS)
        path=out/'report.json';path.write_text(json.dumps(result,indent=2)+'\n');register(path,sha(path))
        (out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n')
        print(json.dumps(dict(passed=passed,sha256=sha(path),connected_roots=result['connected_roots'],physical_inputs=len(PINS))),flush=True)

if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),sys.argv[4])
