"""Independent bounded paired proof/observer-scope and byte-relation review.

Whole capture comparison remains the paired reader's observation. Small raw
CS/API/FS/owner proofs and reconstructed complete provider pages are checked
again here without opening a native/original capture reader.
"""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import traceback
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[2]


def need(value,message):
    if not value: raise ValueError(message)


def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def main(paired_report,source_report,name):
    out=ROOT/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh bounded paired review');out.mkdir(parents=True)
    pins={};counts=Counter();passed=False;relations=[];preflight_path=ROOT/'reports/m4-tree-review/paired131-preparation-review-r2/report.json'
    def pin(path,digest=None):
        path=Path(path).resolve();actual=sha(path);need(digest is None or actual==digest,'Exact bounded paired input '+str(path))
        need(str(path)not in pins or pins[str(path)]==actual,'Immutable bounded paired input');pins[str(path)]=actual;return path
    def read(path,digest=None):
        path=pin(path,digest);need(path.stat().st_size<=64*1024*1024,'Bounded paired JSON proof');return json.loads(path.read_bytes())
    try:
        pin(__file__);pin(ROOT/'tools/m4-tree-review/review_paired125_v2.py');pin(ROOT/'tools/m4-tree-review/prepare_paired130_review.py');pin(ROOT/'tools/m4-tree-review/review_paired130.py');paired_report=Path(paired_report).resolve();source_report=Path(source_report).resolve()
        report=read(paired_report);source=read(source_report);configuration=read(report['configuration_path'],report['configuration_sha256'])
        need(report['passed']and report['paired_initialization_data_contract']and source['passed']and
             report['native_source_report_sha256']==sha(source_report),'Fresh actual paired and strict source proofs join')
        actual=read(ROOT/'reports/m4-joint-startup131-root/execution-r1/report.json','e250499a23537e21a206989f1dc9f1db2e40faae57840daa3b7cd4bb8d3a7a57')
        need(actual['passed']and actual['build_sha256']=='6381e7288fcea6ece0c2b8b4420d6daf4e5aaa616484b40498589b4f869fcca5', 'Exact current nativeprep5/build4 run')
        prep=read(ROOT/'reports/m4-formatting-native/preparation-r19/report.json','1f704ba8254433b9ae7387a53322c33b4db536b99eb79363ff71e54169cb65f3')
        original=read(configuration['original_old4_source']['path'],configuration['original_old4_source']['sha256'])
        observer=read(ROOT/'reports/m4-tree-review/original131-prelaunch-r4/report.json','e5a09a7c7771c0c7f99cc907000ca999903e21b87d1342160684f237452608ed')
        need(original['passed']and observer['passed']and report['Lockit_independent_original_compiled_observer_gate_sha256']==sha(ROOT/'reports/m4-tree-review/original131-prelaunch-r4/report.json'),
             'Actual complete compiled/linked observers and original source owner proof bound')
        path=ROOT/'tools/m4-startup131-paired/paired_v2.py';pin(path,report['files'][str(path.resolve())])
        paired_code=path.read_text(encoding='utf-8')
        need("need(all(x['offset']in declared for x in differences)"in paired_code and
             'No undeclared paired byte difference'in paired_code and "if page==0x20001000:continue"in paired_code,
             'All unequal nonstack bytes explicitly accounted; scratch stack attributed to strict independent source proof')
        need(not report['Lockit_original_postRET_observed']and not report['Lockit_opaque_loaded_bytes_masked']and
             not report['original_and_native_bytes_modified']and not report['blanket_page_mask']and
             not report['original_provider_scratch_stack_crossbranch_equal']and report['native_full_stack_source_proven']and
             not report['whole_game_liveness_proven']and report['initializers_added_by_this_report']==0 and
             not report['whole_M4_complete'],'Precisely bounded paired data/API/representation contract')
        need('7810A311 before MOV EAX,EDI'in report['Lockit_original_ctor_APIreturn_scope']and
             '7810A364 literal preRET'in report['Lockit_original_dtor_APIreturn_scope'],
             'Actual original API returned snapshots precede source epilogue/RET')
        need(report['original_record_bytes']==356992 and report['native_record_bytes']==159716 and
             report['Lockit_private_requested_sizes']==[24,24,24,24,20,20,24,24]and
             report['Lockit_whole_private_initial_backings']==32 and report['Lockit_native_whole_mapped_backings']==4096,
             'Immutable phase ABI and exact requested20/24/fullactual32/mapped4096 extents')
        def output(name):
            path=(paired_report.parent/name).resolve();return read(path,report['files'][str(path)])
        owners=output('Lockit-private-owners.json');need(len(owners)==96,'All eight new actual owners in12cases')
        expected_requests={0x411010:24,0x4dc140:24,0x500660:20,0x5968f0:24};cases={(level,seq)for level in('O0','O2')for seq in range(6)}
        for case in cases:
            selected=[row for row in owners if(row['level'],row['sequence'])==case]
            need(len(selected)==8 and Counter(row['root']for row in selected)==Counter({root:2 for root in expected_requests}),
                 'Every genuine four-root pair has exactly eight positive private owners')
            for row in selected:
                meta=row['original_meta'];record=row['native_record'];request=expected_requests[row['root']]
                need(row['requested_size']==meta[4]==record[7]==request and meta[8]==record[19]==32 and
                     record[16]and record[17]and record[18]and record[21]==record[23]==1,
                     'Exact original/native positive request/private backing/publication identity')
                old_initial=bytes.fromhex(row['original_initial_hex']);new_initial=bytes.fromhex(row['native_initial_hex'])
                old_expected=bytes.fromhex(row['original_expected_hex']);need(len(old_initial)==len(new_initial)==len(old_expected)==32,
                     'Every actual acquired branch backing retained complete')
                old=bytearray(old_initial);new=bytearray(4096);new[:32]=new_initial;writes=row['source_writes']
                need(len(writes)==4,'Four independently source-corroborated DWORD stores per header/sentinel')
                for write in writes:
                    need(write['write']and write['bytes']==4 and 0<=write['owner_offset']<=request-4,
                         'All source writes lie within genuine requested20/24extent')
                    value=write['source_value'];targets=[target for target in selected if target['original_meta'][7]==value]
                    need(len(targets)<=1,'Unique live original typed pointer association')
                    translated=targets[0]['native_record'][16]if targets else value;offset=write['owner_offset']
                    old[offset:offset+4]=struct.pack('<I',value);new[offset:offset+4]=struct.pack('<I',translated)
                    counts['reconstructed_typed_owner_DWORD_stores']+=1
                need(old==old_expected and hashlib.sha256(new).hexdigest()==row['native_expected_sha256'],
                     'All original32/native4096 byteflow reconstructed from branch initial bytes and literal source stores')
                need(old[request:]==old_initial[request:]and new[request:32]==new_initial[request:],
                     'Requested-size padding tails preserve their own actual initial bytes')
                counts['independent_private_owner_byteflows']+=1
        APIs=output('Lockit-paired-API-observations.json');need(len(APIs)==96,'All96 bounded original/native API pairs')
        actual_sources=read(source_report.parent/'Lockit-source-derivations.json',source['files'][str((source_report.parent/'Lockit-source-derivations.json').resolve())])
        for row in APIs:
            relation=row['native_source_relation'];index=0 if row['kind']==1 else 1
            need(row['kind']in(1,4)and not row['original_postRET_observed']and not row['native_postRET_API_observed'],
                 'Actual APIentry/APIreturned observations with explicit preRET scope')
            before=row['actual_original_APIentry_CPU'];after=row['actual_original_sourceAPIreturn_CPU']
            need(len(before)==len(after)==10 and before[4]==relation['frame']and after[4]==before[4]+8 and
                 after[9]==relation['return_pc']==(0x7810a311 if index==0 else 0x7810a364),
                 'Genuine original stdcall ESP/PC frame relation with actual returned boundary')
            case=(row['level'],row['sequence']);entry_relation=next(r for r in actual_sources if(r['level'],r['sequence'])==case)
            need(relation in entry_relation['API_relations'],'Paired API relation joins independently persistent current source proof')
            old0=bytes.fromhex(row['actual_original_CS24_before_hex']);old1=bytes.fromhex(row['actual_original_CS24_returned_hex']);new1=bytes.fromhex(relation['derived_CS24_hex'])
            need(len(old0)==len(old1)==len(new1)==24,'Whole actual originalCS24 and typed native semanticCS24')
            original_thread=struct.unpack_from('<I',old1 if index==0 else old0,12)[0]
            native_thread=relation['OwningThread']if index==0 else 0
            need(original_thread>0 and (native_thread>0 if index==0 else native_thread==0),
                 'Own actual current-thread relation retains raw per-process identities')
            expected_before=0 if index==0 else original_thread;expected_after=original_thread if index==0 else 0
            need(struct.unpack_from('<I',old0,12)[0]==expected_before and struct.unpack_from('<I',old1,12)[0]==expected_after,
                 'Actual original own-thread Enter/Leave resource effects')
            need(old1[:12]==new1[:12]and old1[16:]==new1[16:],
                 'Every actual original/native opaque and numerical CS24 output byte agrees except authenticated own-thread DWORD')
            counts['independent_paired_API_frame_CS24_relations']+=1
        FS=output('Lockit-paired-normal-FS.json');need(len(FS)==96,'All96 complete new normal FS install/restore records')
        contracts=read(ROOT/'reports/m4-lockit-source/recovery-r1/FS-frame-contracts.json')
        byroot={row['root']:row for row in contracts}
        for row in FS:
            old=bytes.fromhex(row['original_record_hex']);new=bytes.fromhex(row['native_record_hex']);need(len(old)==len(new)==12,
                 'Both branches retain complete12B actual source record')
            need(old[4:]==new[4:]and struct.unpack_from('<I',old)[0]==row['original_saved_predecessor']and
                 struct.unpack_from('<I',new)[0]==row['native_saved_predecessor'],'Whole physical source record joins own saved predecessor and exact source handler/scope')
            contract=byroot[row['root']];need(row['PC']==contract['install'if row['kind']==1 else'restore']and
                 struct.unpack_from('<I',old,4)[0]==contract['handler'],'Exact original source FS instruction/handler')
            counts['independent_complete12B_FS_relations']+=1
        # Reconstruct all three entire provider pages, including exactly the
        # real original observer substitutions; compare every emitted endpoint.
        parser=pin(ROOT/'tools/analysis/pe.py','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
        spec=importlib.util.spec_from_file_location('paired_bounded_PE32',parser);PE=importlib.util.module_from_spec(spec);spec.loader.exec_module(PE)
        image=PE.PEImage(pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
        rx=image.read(image.rva_range(0x7810a000-image.image_base,4096)[0],4096);oldrx=bytearray(rx)
        patch_path=(Path(configuration['original_old4_source']['path']).parent/'provider-observer-spans.json').resolve()
        patches=read(patch_path,original['files'][str(patch_path)]);need(len(patches)==4,'Exactly four actual linked original provider observer spans')
        declared_rx=[]
        for patch in patches:
            offset=patch['PC']&4095;width=patch['width'];old=bytes.fromhex(patch['original_hex']);literal=bytes.fromhex(patch['source_hex'])
            need(rx[offset:offset+width]==literal and len(old)==width and old[0]==0xe9 and
                 (patch['PC']+5+struct.unpack_from('<i',old,1)[0])&0xffffffff==patch['compiled_target'],
                 'Exact full physical original observer CALL target/padding vs native raw source instruction span')
            oldrx[offset:offset+width]=old;declared_rx+=list(range(offset,offset+width))
        rw=pin(prep['loaded_input_page'],prep['loaded_input_page_sha256']).read_bytes()
        iat=pin(prep['loaded_IAT_page'],prep['loaded_IAT_page_sha256']).read_bytes();oldiat=bytearray(iat);declared_iat=[]
        for cell,target in report['Lockit_exact_original_API_observer_targets'].items():
            cell=int(cell);need(cell in(0x78146198,0x78146184),'Only exact original Enter/Leave observer import cells')
            offset=cell&4095;struct.pack_into('<I',oldiat,offset,target);declared_iat+=list(range(offset,offset+4))
        input_gate_path=Path(configuration['loaded_inputs']['path']).resolve()
        input_gate=read(input_gate_path,configuration['loaded_inputs']['sha256'])
        need(input_gate['passed'] and report['loaded_input_relation_report_sha256']==sha(input_gate_path),
             'Actual paired consumer binds reviewed finite page input/access policy')
        original_rw=pin(input_gate['whole_original_input_page'],input_gate['whole_original_input_page_sha256']).read_bytes()
        domain_path=input_gate_path.parent/'input-domain.json';domain=read(domain_path,input_gate['files'][str(domain_path.resolve())])
        declared_rw=[r['offset'] for r in domain['differences']]
        need(len(declared_rw)==71 and len({offset&~3 for offset in declared_rw})==25,
             'Entire exact fresh differing input-byte domain')
        need(domain['differences']==[dict(offset=i,original=a,native=b) for i,(a,b) in enumerate(zip(original_rw,rw)) if a!=b],
             'Full independently reconstructed own-page difference list')
        need("equal(actual,loaded_cp_native_RW" in paired_code and "equal(differences,loaded_input_differences" in paired_code,
             'Actual comparer checks each complete own bootstrap page and whole fixed delta; no wildcard')
        expected_pages={0x7810a000:(sha_bytes(oldrx),sha_bytes(rx),sorted(declared_rx)),
                        0x78145000:(sha_bytes(original_rw),sha_bytes(rw),declared_rw),
                        0x78146000:(sha_bytes(oldiat),sha_bytes(iat),sorted(declared_iat))}
        pages=output('Lockit-provider-page-relations.json');need(len(pages)==9432,'All three entire provider pages across1500before/afterphases')
        seen=set()
        for row in pages:
            key=(row['level'],row['sequence'],row['phase'],row['side'],row['page']);need(key not in seen,'Each complete paired provider endpoint once');seen.add(key)
            expected=expected_pages[row['page']]
            need((row['original_sha256'],row['native_sha256'],row['exact_declared_difference_offsets'])==expected,
                 'Every complete paired provider page equals independently reconstructed physical/authentic input and exact original observers')
            counts['independently_reconstructed_whole_provider_pages']+=1
        need(seen=={(level,seq,phase,side,page)for level,seq in cases for phase in range(131)for side in('before','after')for page in expected_pages},
             'Complete provider endpoint grid with no omissions')
        expected_counts={'paired_phases':1572,'paired131_sequences':12,'Lockit_paired_complete12B_normal_FS_relations':96,
            'Lockit_paired_bounded_API_semantic_relations':96,'Lockit_actual_owner_publication_activations':96,
            'Lockit_branch_field_source_derivations':216,'Lockit_whole_native_owned_carries':288}
        for key,value in expected_counts.items():need(report['counts'][key]==value,'All sealed paired reader observations '+key)
        for key,value in {'whole_nonstack_page_relations':138336,'separate_whole_loader_page_input_relations':3144,
                          'whole45_nonstack_page_endpoint_relations':141480,'whole_exact_loaded_input_endpoint_relations':3144}.items():
            need(report['counts'][key]==value,'Exact current whole endpoint scope '+key);counts[key]=value
        # The v3 guard correction is authenticated against physical PE bytes.
        game=PE.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
        guards={0x4b7f70:'e80b000000',0x4b7f75:'e916000000',0x4b7f90:'68a07f4b00'}
        for pc,raw in guards.items():
            data=bytes.fromhex(raw);need(game.read(game.rva_range(pc-game.image_base,len(data))[0],len(data))==data,
                                        'Actual root CALL, tail JMP and callback PUSH physical source')
            counts['physical_tree_registration_guard_rows']+=1
        sys.path.insert(0,str(ROOT/'tools/m4-tree-review'))
        import pair_tree_seams as S
        import review_pair_helper_v2 as H
        for module in (S,H):pin(module.__file__)
        helper_path=ROOT/'tools/m4-startup131-paired/tree_relations.py';pin(helper_path,report['files'][str(helper_path.resolve())])
        spec=importlib.util.spec_from_file_location('bounded125_typed_pair',helper_path)
        T=importlib.util.module_from_spec(spec);spec.loader.exec_module(T)
        contract=read(ROOT/'reports/m4-tree-source/dynamic-contracts-r1/normal-contracts.json',
                      'fbdd6e79dc26328ae2bd6a2e02d264971eaa190251d589f085904ffd9486829c')
        read(ROOT/'reports/m4-tree-review/pair-helper-r2/report.json','50005b020c8bbb409de494ed582e2a97fcb4f1ffb3d16aedb92fcd9f764315f9')
        original_tree_gate=read(configuration['original_combined_source']['path'],configuration['original_combined_source']['sha256'])
        original_tree_path=Path(configuration['original_combined_source']['path']).parent/'original-Tree-source-derivations.json'
        original_tree_rows=read(original_tree_path,original_tree_gate['files'][str(original_tree_path.resolve())])
        tree_original={r['sequence']:r['source']for r in original_tree_rows}
        need(len(tree_original)==6 and all(r['phase']==79 for r in original_tree_rows),'Exact six current original tree occurrences')
        native_path=source_report.parent/'Tree-source-derivations.json'
        natives=read(native_path,source['files'][str(native_path.resolve())])
        actual_tree_pairs=output('Tree-paired-source-relations.json')
        need(len(natives)==len(actual_tree_pairs)==12,'Every current true native/source/paired tree case')
        preparation=read(ROOT/'reports/m4-joint-startup131/preparation-r1/report.json',
                         '2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25')
        order=preparation['selected_order'];treephase=next(i for i,r in enumerate(order)if r['entry']==0x4b7f70)
        prior_calls=2*sum(r['entry'] in expected_requests for r in order[:treephase])
        need(treephase==79 and prior_calls==2,'Literal table locates tree26 effects after first old4 pair')
        totals=Counter()
        for case in natives:
            original_case=tree_original[case['sequence']];native_case=case['source']
            # Synthesized mapping adapter tests only bounded literal derivations.
            # Actual native pages/generations are authenticated by source and paired readers.
            fields,derived=T.compare(original_case,native_case,H.DerivedMappingAdapter(native_case),'',contract)
            actual_case=next(r for r in actual_tree_pairs if (r['level'],r['sequence'])==(case['level'],case['sequence']))
            need(actual_case['counts']==derived and actual_case['static_fields']=={str(a):list(v) for a,v in fields.items()},
                 'Independent bounded own-capacity/typed access/static derivation equals exact actual paired export')
            totals.update(derived)
            raw=case['API_relations'];need(len(raw)==36,'Every current complete provider26+old8 call order')
            relations.append(dict(level=case['level'],sequence=case['sequence'],
                                  tree_API_scratch_FS=S.compare(original_case,native_case,raw[prior_calls:prior_calls+26],counts)))
            counts['tree_saved_local_byte_pairs']+=derived['tree_saved_local_byte_relations']
            counts['tree_saved_local_read_to_store_joins']+=derived['tree_literal_saved_local_read_to_store_joins']
        for key,value in totals.items():
            need(report['counts'][key]==value,'All actual tree paired counters join independently derived bounded source '+key)
        counts['tree_owned_operand_pairs']=totals['tree_paired_owned_accesses']
        counts['tree_whole_capacity_pairs']=totals['tree_whole_branch_owner_backing_pairs']
        need(counts['tree_owned_operand_pairs']==2064 and counts['tree_whole_capacity_pairs']==84 and
             counts['tree_scratch_role_pairs']==312 and counts['tree_typed_API_semantic_pairs']==312 and
             counts['tree_complete12B_FS_pairs']==168 and counts['tree_saved_local_byte_pairs']==24 and
             counts['tree_saved_local_read_to_store_joins']==48,'Complete finite new tree source/API/FS/backing extent')
        preflight_path=ROOT/'reports/m4-tree-review/paired131-preparation-review-r2/report.json'
        preflight=read(preflight_path,'3c863aed6f6bed096b6ec9f7fa705f09f6fb7ce63b0f3b8de4fe48377c740f54')
        need(preflight['passed']and preflight['paired_executed']is False,'Exact separate unexecuted helper preflight')
        configuration=read(report['configuration_path'],report['configuration_sha256'])
        for row in configuration.values():
            if isinstance(row,dict)and 'path'in row:
                gate=read(row['path'],row['sha256']);need(gate['passed'],'All current paired frozen prerequisite gates')
        # Replay the exact formatter/mixed helper over sealed source exports.
        # This synthesized mapping supplies only literal results for bounded
        # derivation review; actual backing equality remains source/paired-reader evidence.
        fmt_path=ROOT/'tools/m4-startup131-paired/format_relations.py';pin(fmt_path,report['files'][str(fmt_path.resolve())])
        spec=importlib.util.spec_from_file_location('bounded130_format_helper',fmt_path)
        FMT=importlib.util.module_from_spec(spec);spec.loader.exec_module(FMT)
        ofpath=original_tree_path.parent/'original-Formatting-source-derivations.json'
        originals=read(ofpath,original_tree_gate['files'][str(ofpath.resolve())])
        nfpath=source_report.parent/'Formatting-source-derivations.json'
        natives_fmt=read(nfpath,source['files'][str(nfpath.resolve())])
        pairs=output('Formatting-paired-source-relations.json')
        need(len(originals)==24 and len(natives_fmt)==len(pairs)==48,'All four actual roots in each current O0/O2 case')
        class DerivedFormatMapping:
            def __init__(self,row):
                self.rows={o['generation']:o for o in [row['owner']]+row['mixed_owners']}
            def data(self,key):
                import re
                match=re.search(r'locale-allocation-(\d+)-(initial|expected|owned-page)\.bin$',key)
                need(match is not None,'Bounded derived mapping admits only exact owner backing names')
                o=self.rows[int(match[1])]
                return bytes.fromhex(o['initial'])if match[2]=='initial'else bytes.fromhex(o['source_final_hex'])+bytes(4096-o['extent'])
        original_prep=read(ROOT/'reports/m4-startup131-original/preparation-r4/report.json','1ee9bd012dcb8e5d4023de10ab6c6046d29d561098cf7c95fffc89ce96ddaceb')
        whole_pages=set(original_prep['observed_pages']+original_prep['extra_whole_source_pages']);need(len(whole_pages)==46,'Exact whole current130 source page inventory')
        format_totals=Counter()
        for row in natives_fmt:
            old=next(o for o in originals if(o['sequence'],o['root'])==(row['sequence'],row['root']))
            actual_pair=next(p for p in pairs if(p['level'],p['sequence'],p['root'])==(row['level'],row['sequence'],row['root']))
            fields,derived,pair=FMT.compare(old,row,DerivedFormatMapping(row),f"sequence-{row['sequence']}/selected/",whole_pages,None)
            need(pair==actual_pair,'Independent bounded formatter/mixed own-capacity/cdecl/FS/API/static derivation equals exact actual paired export')
            format_totals.update(derived)
        expected_format=dict(paired_new_format_owners=48,paired_new_format_cdecl_lifetimes=144,paired_new_format_cdecl_boundary_relations=288,paired_new_format_publications=48,paired_new_mixed_MFC_owners=36,paired_new_mixed_source_owned_writes=120,paired_new_mixed_publications=36,paired_new_mixed_bounded_API_relations=24,paired_new_mixed_FS_install_restore12B_relations=48,paired_new_mixed_saved_byte_source_derivations=96)
        for key,value in format_totals.items():need(report['counts'][key]==value,'All current paired formatter/mixed counts independently rederived '+key)
        for key,value in expected_format.items():need(format_totals[key]==value,'Complete finite formatter/mixed coverage '+key)
        counts.update(format_totals)
        mfc=output('MFC-paired-source-relations.json')
        need(len(mfc)==12 and {(row['level'],row['sequence'])for row in mfc}==cases,'Every current MFC branch pair retained')
        for row in mfc:
            need(row['root']==0x5ae3e4 and row['phase']==13 and len(row['operand_relations'])==113 and len(row['borrowed_roles'])==5 and len(row['normal_boundaries'])==7 and len(row['API_lifetimes'])==4 and len(row['native_whole_regions'])==12 and len(row['whole_module_input_relations'])==2,'All finite MFC full relation outputs')
            need(not row['original_postRET_observed']and not row['candidate_AFTER_machine_seed']and not row['original_API_held_CS24_observed'],'Exact MFC capture/source scope')
        for key,value in dict(paired_MFC_source_PC_occurrences=1704,paired_MFC_ordered_operand_relations=1356,paired_MFC_normal_boundary_relations=84,paired_MFC_named_API_lifetimes=48,paired_MFC_whole_borrowed_role_byteflows=60,paired_MFC_whole_borrowed_endpoint_pairs=120,paired_MFC_source_FS_install_restore_relations=24,paired_MFC_whole_region_endpoint_relations=288,paired_MFC_whole_module_input_relations=24).items():
            need(report['counts'][key]==value,'Every actual new MFC paired relation '+key);counts[key]=value
        for path,digest in preflight['files'].items():pin(path,digest)
        import review_mfc_pair131 as MP
        pin(MP.__file__);counts.update(MP.compare(paired_report,report,source_report,source,pin))
        counts['paired_comparer_exact_preflight_bound']=1
        counts['paired_configuration_prerequisites']=sum(isinstance(v,dict)and'path'in v for v in configuration.values())
        artifact=out/'tree-seam-observations.json';artifact.write_text(json.dumps(relations,indent=2)+'\n');pin(artifact)
        counts['complete_paired_sequences']=12;counts['complete_paired_phases']=1572
        passed=True
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        receipt=dict(passed=passed,scope='Independent bounded paired observer/API return scope, raw12B FS records, complete32B/4096B owner byteflow, exact reconstructed whole provider pages and final sealed paired receipt',
            paired_report_sha256=sha(paired_report),native_source_sha256=sha(source_report),paired_preflight_sha256=sha(preflight_path),native_capture_archive_opened=False,original_capture_archive_opened=False,original_postRET_observed=False, bounded_mapping_adapter_is_capture=False,
            original_API_volatile_CPU_equivalence_claimed=False,original_scratch_stack_crossbranch_equality_claimed=False,
            whole_machine_observations_attributed_to_paired_reader=True,initializer_credit=False,counts=dict(counts),files=pins)
        path=out/'report.json';path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(passed=passed,report_sha256=sha(path),counts=dict(counts))))


def sha_bytes(raw):return hashlib.sha256(raw).hexdigest()


if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve(),sys.argv[3])
