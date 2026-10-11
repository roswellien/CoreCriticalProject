"""Current observed constructor service domains; no payload/archive/native seeds."""
from pathlib import Path
from collections import Counter
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
NEW=(0x4103f0,0x410440,0x459b40)
PHASES={0x4103f0:13,0x410440:14,0x459b40:36}
OBJECTS={0x4103f0:0x604008,0x410440:0x603fb8,0x459b40:0x605ae0}
CASES=((0,0x7f,0),(0,0x37f,7),(0,0xf7f,0),(1,0x47f,7),(1,0xa7f,0),(1,0xe7f,7))
FRAME=0x20001800

def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def need(value,message):
    if not value:raise ValueError(message)
def words(raw,offset=0,count=1):return struct.unpack_from('<'+str(count)+'I',raw,offset)

def main(name):
    out=ROOT/'reports/m4-constructor-native'/name
    need(not out.exists(),'Fresh additive observed source domains')
    out.mkdir(parents=True);files={};counts=Counter();passed=False
    def pin(path,digest=None):
        path=Path(path).resolve()
        need(path.suffix.lower()!='.mwb'and path.name not in('transport.json','payload.bin','index.json'),'No archive, transport, index or raw payload read')
        actual=sha(path);need(digest is None or actual==digest,'Exact current observation/source input '+str(path))
        need(str(path)not in files or files[str(path)]==actual,'Stable successful physical input');files[str(path)]=actual;return path
    def read(path,digest=None):return json.loads(pin(path,digest).read_bytes())
    def write(filename,data):
        path=out/filename;path.write_text(json.dumps(data,indent=2)+'\n');pin(path);return str(path.resolve())
    try:
        validation_path=ROOT/'reports/m4-constructor-original/chronological-validation-r3/report.json'
        validation=read(validation_path,'00f22911cff2ebde706df7eac235d1621127cb6bd670fd9d680c8478f19b0b95')
        need(validation['passed']and validation['reader_closed']and validation['counts']['whole_phase_records']==222,'Current complete closed six-domain original observations')
        base=validation_path.parent
        def observation(name):
            path=base/name;return read(path,validation['files'][str(path.resolve())])
        phases=observation('constructor-observations.json')
        normal=observation('constructor-normal-boundaries.json')
        allocations=observation('actual-initial-allocation-inputs.json')
        graphs=observation('actual-list-graphs.json')
        cleanup=observation('actual-new-owner-cleanup.json')
        nulls=observation('actual-new-NULL-free-boundaries.json')
        source_path=ROOT/'reports/m4-constructor-source/preparation-r1/report.json'
        source=read(source_path,'0d5adb32fbd8b8d3d8d3da308cd48a7050071f2f2c61795840d63955385c26cf')
        need(source['passed'],'Exact literal constructor preparation')
        source_contracts_path=source_path.parent/'contracts.json'
        source_contracts=read(source_contracts_path,source['files'][str(source_contracts_path.resolve())])
        instruction_path=source_path.parent/'source-instructions.json'
        instructions=read(instruction_path,source['files'][str(instruction_path.resolve())]);by_pc={r['pc']:r for r in instructions}
        prep=Path(validation['preparation_path'])
        original_prep=read(prep/'report.json',validation['preparation_sha256'])
        original_contracts_path=prep/'contracts.json'
        original_contracts=read(original_contracts_path,original_prep['files'][str(original_contracts_path.resolve())])
        order_path=prep/'selected-order.json';order=read(order_path,original_prep['files'][str(order_path.resolve())])
        chain_path=ROOT/'reports/m4-constructor-original/entry-chain-r1/report.json'
        chain=read(chain_path,original_contracts['source_MFC_entry_chain_sha256'])
        rounding_path=ROOT/'reports/m4-constructor-original/request-rounding-r1/report.json'
        rounding=read(rounding_path,'c1817707871eda399c126602e2bc6240081f076d914776cb091ff3babc375ee7')
        need(chain['passed']and rounding['passed']and rounding['admitted_heap_mode']==1,'Finite actual owning export/frame and mode1 request contracts')
        pe_path=pin(ROOT/'tools/analysis/pe.py',source['files'][str((ROOT/'tools/analysis/pe.py').resolve())])
        spec=importlib.util.spec_from_file_location('constructor_domain_PE',pe_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        image_path=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
        image=module.PEImage(image_path.read_bytes())
        for row in instructions:
            offset,_=image.rva_range(row['pc']-image.image_base,row['size'])
            need(image.data[offset:offset+row['size']]==bytes.fromhex(row['bytes']),'Exact physical literal instruction '+hex(row['pc']))
        counts['physical_unique_source_rows']=len(by_pc)
        for report in(chain,rounding):
            for path,digest in report['files'].items():
                if Path(path).suffix.lower()in('.dll','.stdout','.py'):pin(path,digest)
        # Physical MFC/CRT service names and rounding bytes are source proof,
        # while actual targets/frames and request pairs below remain observations.
        static_alloc=[row for row in instructions if row['mnemonic']=='call'and row['operands'].startswith('0x5abd26 ')]
        static_free=[row for row in instructions if row['mnemonic']=='call'and row['operands'].startswith('0x5abd1a ')]
        observed_alloc_PCs={row['CPU'][9]-5 for row in normal if 1<=row['metadata'][3]<=8}
        observed_free_PCs={row['source_CALL_PC']for row in nulls}
        need(len(static_alloc)==8 and len(static_free)==6,'Exact finite static allocator/free site inventory')
        indexed_normal={(r['sequence'],r['phase'],r['index']):(i,r)for i,r in enumerate(normal)}
        indexed_initial={(r['sequence'],r['metadata'][1]):(i,r)for i,r in enumerate(allocations)}
        indexed_graph={r['stem']:(i,r)for i,r in enumerate(graphs)}
        indexed_cleanup={(r['sequence'],r['metadata'][1]):(i,r)for i,r in enumerate(cleanup)}
        before_inputs=[];domain_rows=[]
        def ref(filename,index):return dict(path=str((base/filename).resolve()),JSON_pointer='/'+str(index),sha256=validation['files'][str((base/filename).resolve())])
        def graph_checked(stem,owner_map):
            index,g=indexed_graph[stem];nodes=g['nodes'];meta=g['metadata']
            need(bool(nodes)==bool(meta[2]),'Actual bounded header and node inventory')
            for i,node in enumerate(nodes):
                m=node['metadata'];raw=bytes.fromhex(node['whole_backing_hex']);owner=owner_map[m[4]]
                need(len(raw)==m[3]==owner['metadata'][8]and m[2]==owner['metadata'][7]and m[5:7]==owner['metadata'][2:4]and raw==bytes.fromhex(owner['whole_backing_hex'])and list(words(raw,0,3))==m[7:10],'Whole BEFORE node matches own live allocator occurrence bytes and role')
                need(m[7]==nodes[(i+1)%len(nodes)]['metadata'][2]and m[8]==nodes[(i-1)%len(nodes)]['metadata'][2],'Complete balanced cyclic forward/backward BEFORE links')
            if nodes:need(nodes[0]['metadata'][2]==meta[2],'Actual graph begins at whole observed header')
            counts['whole_BEFORE_graphs']+=1;counts['whole_BEFORE_node_backings']+=len(nodes)
            return index,g
        for phase_index,phase_row in enumerate(phases):
            sequence,phase,root=phase_row['sequence'],phase_row['phase'],phase_row['root']
            need(root in NEW and phase==PHASES[root]and order[phase]['entry']==root,'Actual later selected chronology association')
            stem=f'phase/{sequence}/{phase}'
            owners_index,owners=indexed_graph[stem+'/BEFORE-owners'];owner_map={v['metadata'][1]:v for v in owners['whole_live_owners']}
            need(len(owner_map)==len(owners['whole_live_owners']),'Complete unique current BEFORE owner occurrence inventory')
            for owner in owner_map.values():
                m=owner['metadata'];raw=bytes.fromhex(owner['whole_backing_hex'])
                need(m[9]==1 and len(raw)==m[8]and(m[2]==0xffffffff or m[2]<phase),'Actual whole live owner predates this constructor; no source AFTER input')
                counts['whole_BEFORE_owner_backings']+=1;counts['whole_BEFORE_owner_bytes']+=len(raw)
            shared_index,shared=graph_checked(stem+'/BEFORE-constructor',owner_map)
            member_index,member=graph_checked(stem+'/BEFORE-member',owner_map)
            before_inputs.append(dict(sequence=sequence,phase=phase,root=root,observed_only=True,native_seed=False,source_AFTER_seed=False,whole_shared_graph=shared,whole_member_graph=member,whole_live_owners=owners['whole_live_owners'],input_paths=dict(shared=ref('actual-list-graphs.json',shared_index),member=ref('actual-list-graphs.json',member_index),owners=ref('actual-list-graphs.json',owners_index)),source_frame=FRAME))
            actual_normal=[(i,r)for i,r in enumerate(normal)if(r['sequence'],r['phase'])==(sequence,phase)]
            pairs=[];getter_pairs=[]
            for normal_index,row in actual_normal:
                kind=row['metadata'][3]
                if 1<=kind<=8:
                    entry_index,entry=indexed_normal[(sequence,phase,row['paired_entry_index'])]
                    call=row['CPU'][9]-5;source_row=by_pc[call]
                    need(source_row in static_alloc and entry['metadata'][3]==0 and entry['CPU'][9]==chain['MFC_exports']['823']['target']and words(bytes.fromhex(entry['frame64_hex']))[0]==call+5,'Actual true named MFC823 entry and physical source CALL return')
                    request=words(bytes.fromhex(entry['frame64_hex']),4)[0];rounded=((request if request else 1)+15)&0xfffffff0
                    occurrence=row['matched_allocation_occurrence'];initial_index,initial=indexed_initial[(sequence,occurrence[1])];api=initial['API26']
                    need(initial['metadata']==occurrence and occurrence[2]==phase and occurrence[6]==row['source_derived_HeapAlloc_requested']==rounded and request==row['source_MFC_requested']and occurrence[7]==row['CPU'][0]and len(bytes.fromhex(initial['whole_initial_hex']))==occurrence[8]==occurrence[11]and api[4]-chain['MFC823_entry_to_HeapAlloc_before_delta']==entry['CPU'][4],'Source request, literal CRT rounding, genuine frame and full measured HeapAlloc initial capacity join')
                    need(row['CPU'][4]==entry['CPU'][4]+4 and all(row['CPU'][j]==entry['CPU'][j]for j in(3,5,6,7)),'Observed balanced cdecl caller frame and nonvolatile registers')
                    if call==0x58af12:
                        role=dict(kind='shared-list-node',source_object=OBJECTS[root],payload_offset=8,source_publication_stores=[0x58af22,0x58af2c,0x58af2f,0x58af38,0x4d5110])
                        after_graph=indexed_graph[stem+'/AFTER-constructor'][1]
                    elif call==0x58af6a:
                        role=dict(kind='four-byte vector backing',source_object=OBJECTS[root],publication_field_offset=12,source_publication_store=0x58afbe,publication_proof_scope='Literal same-instance source store; this small-export inventory does not independently re-read the full phase AFTER object page')
                        after_graph=None
                        need(entry['CPU'][6]==row['CPU'][6]==OBJECTS[root],'Actual allocator caller retains source receiver')
                    elif call==0x58f2a2:
                        role=dict(kind='member-list-header',source_object=0x605ae0,publication_cell=0x605ae4,source_publication_store=0x459bb0)
                        after_graph=indexed_graph[stem+'/AFTER-member'][1]
                    elif call==0x45b80e:
                        role=dict(kind='member-list-node',source_object=0x605ae0,payload_source_object=0x605b9c,payload_offset=8)
                        after_graph=indexed_graph[stem+'/AFTER-member'][1]
                    else:raise ValueError('Unexpected actually reached allocation CALL')
                    if after_graph is not None:
                        matches=[v for v in after_graph['nodes']if v['metadata'][4]==occurrence[1]]
                        need(len(matches)==1 and matches[0]['metadata'][2:4]==[occurrence[7],occurrence[8]],'Actual returned owner joins published complete source list role')
                        role['published_role_observed']=True
                        if call==0x58af12:need(matches[0]['metadata'][9]==OBJECTS[root],'Actual shared-node source object payload')
                        elif call==0x58f2a2:need(after_graph['metadata'][2]==occurrence[7],'Actual member header cell joins returned header occurrence')
                        else:need(matches[0]['metadata'][9]==0x605b9c,'Actual member-node source object payload')
                    cleanup_index,clean=indexed_cleanup[(sequence,occurrence[1])]
                    need(clean['metadata']==occurrence and clean['returned']and len(bytes.fromhex(clean['whole_before_hex']))==occurrence[8],'Actual whole matching research cleanup occurrence and return')
                    pairs.append(dict(source_CALL_PC=call,source_return_PC=call+5,actual_MFC_entry=entry['CPU'][9],entry_ESP=entry['CPU'][4],entry_frame_minus_root=entry['CPU'][4]-FRAME,return_ESP=row['CPU'][4],source_requested=request,literal_CRT_API_requested=rounded,actual_HeapAlloc_capacity=occurrence[8],source_receiver=row['CPU'][6],observed_occurrence=occurrence,owner_role=role,full_initial_input_observation=ref('actual-initial-allocation-inputs.json',initial_index),entry_observation=ref('constructor-normal-boundaries.json',entry_index),return_observation=ref('constructor-normal-boundaries.json',normal_index),cleanup_observation=ref('actual-new-owner-cleanup.json',cleanup_index),native_return_seed=False,own_native_allocator_required=True))
                    counts['actual_allocation_pairs']+=1
                elif kind==11:
                    entry_index,entry=indexed_normal[(sequence,phase,row['paired_entry_index'])];g=entry['CPU'];permissions=entry['observed_backing_permissions'];node=entry['source_published_owner_node']
                    need(g[1]==permissions[2]==node['metadata'][9]and permissions[4]==g[2]and permissions[6]==permissions[4]+0x18 and permissions[7]==0x40a850 and permissions[9]==2 and node['metadata'][4]in owner_map and node==next(n for n in shared['nodes']if n['metadata'][4]==node['metadata'][4]),'Actual BEFORE published whole owner supplies receiver and owning readonly vptr slot')
                    slot_offset,_=image.rva_range(permissions[6]-image.image_base,4)
                    need(words(image.data,slot_offset)[0]==0x40a850 and g[9]==0x40a850 and row['CPU'][9]==0x40a853 and row['CPU'][4]==g[4]and words(bytes.fromhex(entry['frame64_hex']))[0]==0x58b186,'Physical readonly getter dispatch and actual retained preRET frame')
                    need(row['FX512_hex']==entry['FX512_hex']and row['ENV28_hex']==entry['ENV28_hex']and row['frame64_hex']==entry['frame64_hex']and all(row['CPU'][j]==g[j]for j in range(10)if j not in(0,9)),'Observed full integer-only getter frame, FP/control and preserved registers')
                    getter_pairs.append(dict(source_CALL_PC=0x58b183,source_return_PC=0x58b186,entry_PC=0x40a850,preRET_PC=0x40a853,receiver=g[1],vptr=g[2],slot=permissions[6],physical_target=0x40a850,source_frame=g[4],frame_minus_root=g[4]-FRAME,source_candidate_identifier=g[7],receiver_field_offset=4,entry_observation=ref('constructor-normal-boundaries.json',entry_index),preRET_observation=ref('constructor-normal-boundaries.json',normal_index),whole_receiver_page_sha256=entry['whole_receiver_page_sha256'],whole_readonly_vptr_page_sha256=entry['whole_vptr_page_sha256'],published_owner_occurrence=node['metadata'][4],source_return_value_seed=False,postRET_observed=False,own_native_receiver_field_read_required=True))
                    counts['actual_getter_entry_preRET_pairs']+=1
            phase_nulls=[(i,r)for i,r in enumerate(nulls)if(r['sequence'],r['phase'])==(sequence,phase)]
            null_pairs=[]
            for null_index,row in phase_nulls:
                if row['metadata'][3]!=1:continue
                before_index,before=phase_nulls[row['index']-1]
                need(before['metadata'][3]==0 and row['source_CALL_PC']==before['source_CALL_PC']==0x58af9a and row['source_return_PC']==before['source_return_PC']==0x58af9f and row['frame16_hex']==before['frame16_hex']and words(bytes.fromhex(row['frame16_hex']),0,4)==(0x5f40178c,0,0x58af9f,0)and row['CPU'][4]==before['CPU'][4]and row['metadata'][6:]==before['metadata'][6:],'Exact actual balanced NULL-free call frame, source return, head and API-count conservation')
                null_pairs.append(dict(source_CALL_PC=0x58af9a,source_return_PC=0x58af9f,actual_CRT_entry=before['CPU'][9],actual_CRT_preRET_PC=row['CPU'][9],actual_MFC825_entry=chain['MFC_exports']['825']['target'],source_frame=before['CPU'][4],frame_minus_root=before['CPU'][4]-FRAME,argument=0,entry_observation=ref('actual-new-NULL-free-boundaries.json',before_index),preRET_observation=ref('actual-new-NULL-free-boundaries.json',null_index),postRET_observed=False,native_NULL_free_effect_must_be_literal=True))
                counts['actual_NULL_free_pairs']+=1
            need(len(pairs)==phase_row['observed_allocation_pairs']and len(getter_pairs)==phase_row['observed_getter_pairs'],'Observed per-phase service counts retained, never predicted inputs')
            domain_rows.append(dict(sequence=sequence,repeat=CASES[sequence][0],CW=CASES[sequence][1],TOP=CASES[sequence][2],phase=phase,root=root,slot=order[phase]['slot'],source_object=OBJECTS[root],allocation_pairs=pairs,NULL_free_pairs=null_pairs,getter_pairs=getter_pairs,BEFORE=dict(shared_header=shared['metadata'][2],shared_counter=shared['metadata'][4],shared_node_count=len(shared['nodes']),member_header=member['metadata'][2],member_counter=member['metadata'][4],member_node_count=len(member['nodes']),whole_live_owner_count=len(owner_map),full_observation_file=str((out/'BEFORE-input-observations.json').resolve()),JSON_pointer='/'+str(len(before_inputs)-1)),actual_observations_only=True))
        need(len(domain_rows)==18 and counts['actual_allocation_pairs']==36 and counts['actual_NULL_free_pairs']==12 and counts['actual_getter_entry_preRET_pairs']==12,'All current six-domain observed normal constructor services')
        before_path=write('BEFORE-input-observations.json',before_inputs)
        roots=[]
        for root in NEW:
            current=[r for r in domain_rows if r['root']==root]
            need(len(current)==6,'Six genuinely observed domains per root')
            signatures=[dict(allocations=[(v['source_CALL_PC'],v['source_requested'],v['literal_CRT_API_requested'],v['actual_HeapAlloc_capacity'],v['owner_role']['kind'])for v in r['allocation_pairs']],NULL_free_sites=[v['source_CALL_PC']for v in r['NULL_free_pairs']],getter_sites=[(v['receiver'],v['vptr'],v['slot'],v['source_frame'])for v in r['getter_pairs']],BEFORE_shape={k:v for k,v in r['BEFORE'].items()if k not in('shared_header','full_observation_file','JSON_pointer')})for r in current]
            need(all(s==signatures[0]for s in signatures),'Same actual source service shape across six CW/TOP domains; opaque owner addresses/bytes remain separate')
            source_root=next(v for v in source_contracts['roots']if v['entry']==root)
            roots.append(dict(root=root,slot=source_root['slot'],phase=PHASES[root],source_object=OBJECTS[root],six_domain_observed_service_shape=signatures[0],callback=source_root['callback'],registration_CALL_PC=source_root['registration_CALL_pc'],registration_service=0x5ac140,registration_evidence_scope='Physical literal root plus actual complete callback-vector validation; provider CPU is a separate source model',callback_shutdown_executed=False,full_selected_chronology_before=order[:PHASES[root]],domains=current))
        static_sites=dict(allocator_sites=[dict(**r,observed_in_current_six_domains=r['pc']in observed_alloc_PCs)for r in static_alloc],free_sites=[dict(**r,observed_NULL_pair_in_current_six_domains=r['pc']in observed_free_PCs,other_normal_inputs_unobserved=True)for r in static_free],unobserved_allocator_PCs=sorted({r['pc']for r in static_alloc}-observed_alloc_PCs),unobserved_free_PCs=sorted({r['pc']for r in static_free}-observed_free_PCs),uncompiled_recursive_frontier=0x56fea0,recursive_frontier_excluded_by_this_small_export_inventory=False,required_later_source_read=dict(root=0x459b40,phase=36,flag=0x72c2c4,scope='Whole current source BEFORE page/source branch proof required; this small-export inventory does not read the raw phase page'))
        contracts=dict(schema='mw34.current_constructor_observed_source_domains.v1',scope='Observed original finite source domains to inform native contracts; every native input/owner/pointer/field/result must arise from its own carried source chronology and literal service adapter',roots=roots,static_sites=static_sites,source_service_chain=chain['MFC_exports'],CRT_named_services=chain['CRT_named_exports'],request_rounding=dict(admitted_heap_mode=1,source_request_max=rounding['source_request_max'],zero_normalization=rounding['zero_normalization'],addend=15,mask=0xfffffff0,formula=rounding['formula'],literal_source_required=True),whole_BEFORE_observations=dict(path=before_path,sha256=sha(before_path),observed_only=True,native_seed=False,source_AFTER_seed=False),third_root_chronology=dict(root=0x459b40,phase=36,slot=0x5e00a0,prior_selected_roots=36,prior_current131_roots=34,first_two_new_roots=2,unexecuted_widget_slots=[0x5e0048,0x5e004c,0x5e0050],full144_chronology_claim=False),research_cleanup=dict(actual_new_owner_returns=36,actual_capacity_metadata_and_full_before_backings='Original small JSON observation only',callback_shutdown_executed=False,scope='Source cleanup validation is distinct from registered shutdown behavior'),source_AFTER_seed=False,original_return_value_seed=False,native_execution_performed=False,initializer_credit=0)
        contracts_path=write('source-contracts.json',contracts)
        pin(__file__)
        for path,digest in list(files.items()):pin(path,digest)
        passed=True
    except BaseException:
        (out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        report=dict(passed=passed,scope='Archive-free current constructor normal-path service inventory and complete BEFORE observations from exact closed strict original validation. Physical source, actual request/rounded-capacity ownership, NULL-free/getter and balanced BEFORE domains remain distinct from native execution/proof.',validation_sha256='00f22911cff2ebde706df7eac235d1621127cb6bd670fd9d680c8478f19b0b95',source_preparation_sha256='0d5adb32fbd8b8d3d8d3da308cd48a7050071f2f2c61795840d63955385c26cf',request_rounding_sha256='c1817707871eda399c126602e2bc6240081f076d914776cb091ff3babc375ee7',counts=dict(counts),source_contracts_path=contracts_path if 'contracts_path'in locals()else None,source_contracts_sha256=sha(contracts_path)if'contracts_path'in locals()else None,BEFORE_input_observations_path=before_path if'before_path'in locals()else None,capture_reader_opened=False,payload_reader_opened=False,index_reader_opened=False,worker_executed=False,native_seed=False,source_AFTER_seed=False,initializer_credit=0,files=files)
        path=out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(path),counts=dict(counts))))

if __name__=='__main__':main(sys.argv[1])
