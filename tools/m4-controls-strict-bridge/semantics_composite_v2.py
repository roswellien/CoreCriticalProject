"""Exact retained accepted131 semantic predicates plus finite138 delta."""
def semantic_checks(rows,gates):
    parent=rows['parent']
    typed_equal(gates['parent']['sha256'],PARENT_SHA,'accepted131 identity')
    for field,expected in dict(connected_roots=131,remaining_inventory_roots=13,whole_M4_complete=False,native_game_launch_complete=False).items():typed_equal(parent[field],expected,'parent '+field)
    preparation=rows['native_preparation'];original=rows['original_preparation']
    prior=read(ROOT/'reports/m4-joint-startup131/preparation-r1/report.json','2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25')
    order=preparation['selected_order']
    need(len(order)==138 and len({row['entry']for row in order})==138,'All138 distinct current selected roots')
    need(order[13]==dict(entry=0x5ae3e4,slot=0x5e0040),'Actual new MFC physical slot13')
    widgets={0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0}
    need([row for row in order if row['entry']not in widgets]==prior['selected_order'],'All131 parent roots and relative order retained')
    for phase,entry,slot in ((15,0x40e250,0x5e0048),(16,0x40ef50,0x5e004c),(17,0x40f000,0x5e0050),(47,0x479590,0x5e00cc),(134,0x5a3c30,0x5e0234),(135,0x5a3ff0,0x5e0238),(136,0x5a66f0,0x5e023c)):
        need(order[phase]==dict(entry=entry,slot=slot),'Exact additive widget physical slot')
    need(original['selected_order']==order,'Same actual original/native current schedule')
    typed_equal(preparation['current_registration_callbacks'],108,'Current callback inventory')
    need(prior['current_registration_callbacks']==101,'Entire accepted parent callback inventory')
    for leaf in ('registration_contract.hpp',):
        current=Path(gates['native_preparation']['path']).parent/leaf
        previous=ROOT/'reports/m4-joint-startup131/preparation-r1'/leaf
        old_text=previous.read_text();new_text=(ROOT/current).read_text()
        old_array=re.search(r'registration_roots *[{]([^}]+)[}]',old_text).group(1)
        new_array=re.search(r'registration_roots *[{]([^}]+)[}]',new_text).group(1)
        old_values=re.findall(r'0x[0-9a-fA-F]+',old_array);new_values=re.findall(r'0x[0-9a-fA-F]+',new_array)
        need(len(old_values)==101 and len(new_values)==108 and new_values[:101]==old_values and [int(x,16)for x in new_values[101:]]==[0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0],'Entire parent callbacks retained with exact seven additions')
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
    for field,expected in dict(phases=828,MFC_original_phases=6,MFC_full_normal_boundaries=42,MFC_full_named_API_pairs=24,MFC_true_root_TIB8192_endpoints=12,MFC_whole_borrowed_backing_endpoints=60,MFC_codepage_CS24_endpoints=12).items():typed_equal(rows['original_validation']['counts'][field],expected,'genuine original extent '+field)
    source=rows['source_provider'];lineage=source['executed_lineage']
    for field,expected in dict(conditional_PCs=2,source_consumers_per_sequence=171,capture_reader_opened=False,worker_executed=False,initializer_credit=0).items():typed_equal(rows['source_legacy_flags'][field],expected,'Finite legacy flag source proof '+field)
    typed_equal(lineage['execution_sha256'],gates['native_execution']['sha256'],'source exact current native execution')
    typed_equal(lineage['build_sha256'],gates['native_build']['sha256'],'source exact current native build')
    typed_equal(lineage['joint_preparation_sha256'],gates['native_preparation']['sha256'],'source exact current preparation')
    for field in('reader_closed','source_and_provider_combined','complete_selected_source','complete_provider_lifecycle','worker_post_HeapDestroy_identity_observed'):typed_equal(source[field],True,'complete current source/provider '+field)
    for field in('per_phase_BEFORE_machine_seed','candidate_AFTER_machine_seed','canonical_reader_changed','duplicate_selected_source_reader','native_CS40_opaque_copy','native_DllMain_credit'):typed_equal(source[field],False,'bounded current source/provider '+field)
    expected=dict(persistent138_sequences=12,persistent_phases=1656,whole_page_BEFORE=114264,whole_page_AFTER=114264,MFC_literal_phases=12,MFC_source_instructions=1704,MFC_source_operands=1356,MFC_typed_API_CPU_frame_relations=48,MFC_whole_region_BEFORE=144,MFC_whole_region_AFTER=144,MFC_whole_State_CPU_FX=12,MFC_owned_resource_lifecycles=12,MFC_actual_API_identity_CS40_sides=312,MFC_whole_actual_caller_FX512_ENV28=12)
    for field,count in expected.items():typed_equal(source['counts'][field],count,'complete new/current source extent '+field)
    cases=source['provider_sequences'];need(len(cases)==12 and {(row['level'],row['sequence'])for row in cases}=={(level,seq)for level in('O0','O2')for seq in range(6)},'All12 inherited provider chains actually rerun')
    total=sum(row['compared_checkpoints']for row in cases);need(total>0,'Measured current provider checkpoints')
    for field in('whole_State_checkpoints','whole_CPU_checkpoints','whole_FX_checkpoints'):typed_equal(source['provider_counts'][field],total,'complete provider '+field)
    for case in cases:
        capacity=case['first_replay_msize_capacity']
        need(case['all_resources_released']and case['actual_post_HeapDestroy_identity'],'Actual whole same-owner native lifecycle complete')
        need(case['selected_used_bytes']==432 and capacity>=432 and capacity%4==0 and case['predicted_growth_replays']==case['actual_growth_replays']==(capacity-432)//4+1,'Source-predicted actual registry capacity/growth')
    paired=rows['paired'];need(paired['reader_closed']and paired['paired_initialization_data_contract'],'Fresh complete current source-backed pair')
    for field in('blanket_page_mask','original_and_native_bytes_modified','whole_game_liveness_proven','loaded_input_native_DllMain_credit'):typed_equal(paired[field],False,'explicit paired bound '+field)
    for label,target in(('source_provider_review','source_provider'),('source_new_mfc_review','source_provider'),('source_closure','source_provider'),('original_old_source_review','original_old_source'),('paired_review','paired'),('controls_review','controls')):
        need(has(rows[label],ROOT/gates[target]['path'],gates[target]['sha256']),'Independent exact physical evidence edge '+label+' -> '+target)
    typed_equal(rows['controls_execution']['build_sha256'],gates['controls_build']['sha256'],'Actual connected control build')
    if rows['controls_preparation'].get('scope_identity')=='current138_controls_preparation_composite_v1':
        underlying=rows['controls_preparation']['underlying_current8_preparation']
        typed_equal(underlying['sha256'],'f413ea66cb259ecebf8bf76024113a0410fe5883304fa10af9a442b291c1b07e','Exact immutable current8 source preparation')
        need(has(rows['controls_preparation'],ROOT/underlying['path'],underlying['sha256']),'Scoped physical current8 preparation edge')
        typed_equal(rows['controls_build']['preparation_sha256'],underlying['sha256'],'Actual current8 build consumes immutable preparation')
        legacy=rows['controls_preparation']['underlying_legacy12_preparation']
        typed_equal(legacy['sha256'],'8a322602c066931f5dd3ced2b9319f6907b0b01413828e2d72dd482c5ce09b2c','Exact separate actual legacy12 prefix preparation')
        need(has(rows['controls_preparation'],ROOT/legacy['path'],legacy['sha256']),'Scoped physical legacy12 preparation edge')
        GRAPH.current8_legacy12_preparation(rows,gates,ROOT=ROOT,read=read,has=has,typed_equal=typed_equal,need=need)
    else:
        typed_equal(rows['controls_build']['preparation_sha256'],gates['controls_preparation']['sha256'],'Current connected control preparation')
    typed_equal(rows['controls_prelaunch']['build_sha256'],gates['controls_build']['sha256'],'Whole connected control link admission')
    # All accepted parent dependencies stay in the final union. Current gates
    # must add their complete archive parts, not merely transport receipts.
    for path,identity in parent['files'].items():need(PINS.get(normalized(str(Path(path).resolve())))==identity,'Entire accepted131 proof retained')

