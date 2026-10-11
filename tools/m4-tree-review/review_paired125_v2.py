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
    pins={};counts=Counter();passed=False;relations=[]
    def pin(path,digest=None):
        path=Path(path).resolve();actual=sha(path);need(digest is None or actual==digest,'Exact bounded paired input '+str(path))
        need(str(path)not in pins or pins[str(path)]==actual,'Immutable bounded paired input');pins[str(path)]=actual;return path
    def read(path,digest=None):
        path=pin(path,digest);need(path.stat().st_size<=64*1024*1024,'Bounded paired JSON proof');return json.loads(path.read_bytes())
    try:
        pin(__file__);paired_report=Path(paired_report).resolve();source_report=Path(source_report).resolve()
        report=read(paired_report);source=read(source_report)
        need(report['passed']and report['paired_initialization_data_contract']and source['passed']and
             report['native_source_report_sha256']==sha(source_report),'Fresh actual paired and strict source proofs join')
        actual=read(ROOT/'reports/m4-joint-startup125-root/execution-r1/report.json','e384b6271c43f2e2e8d5a88f1a09e0940c85f111f2455744ad45de30ba73d8a8')
        need(actual['passed']and actual['build_sha256']=='cdb5b9ca08e4e66dae276fa783bc59b5944e8435113fe9bb65a73cc53f218165', 'Exact current nativeprep5/build4 run')
        prep=read(ROOT/'reports/m4-tree-native/preparation-r5/report.json','9b6c7ab64a42dd67d26e73a7b4357063729085a808173b2818e704430386fef2')
        original=read(ROOT/'reports/m4-tree-original/old-Lockit-source-r3/report.json','2ebc48e5f6dd213e77b33bea8dda79ef2cd4a46b9e48997f6f346cd4e01d6c2c')
        observer=read(ROOT/'reports/m4-tree-original/full-original-review-r3/report.json','a56d25c7b35ece5315f51f8690c713321495d237522b343430d7acdc40a84260')
        need(original['passed']and observer['passed']and report['Lockit_independent_original_compiled_observer_gate_sha256']==sha(ROOT/'reports/m4-tree-original/full-original-review-r3/report.json'),
             'Actual complete compiled/linked observers and original source owner proof bound')
        path=ROOT/'tools/m4-tree-paired/paired_v4.py';pin(path,report['files'][str(path.resolve())])
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
        patch_path=(ROOT/'reports/m4-tree-original/old-Lockit-source-r3/provider-observer-spans.json').resolve()
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
        input_gate_path=ROOT/'reports/m4-tree-review/loaded-input-page-r2/report.json'
        input_gate=read(input_gate_path,'1da680a0f5d1751af3c35e81d3008abbe769331676800c00176d2f4fe3ace4e5')
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
        pages=output('Lockit-provider-page-relations.json');need(len(pages)==9000,'All three entire provider pages across1500before/afterphases')
        seen=set()
        for row in pages:
            key=(row['level'],row['sequence'],row['phase'],row['side'],row['page']);need(key not in seen,'Each complete paired provider endpoint once');seen.add(key)
            expected=expected_pages[row['page']]
            need((row['original_sha256'],row['native_sha256'],row['exact_declared_difference_offsets'])==expected,
                 'Every complete paired provider page equals independently reconstructed physical/authentic input and exact original observers')
            counts['independently_reconstructed_whole_provider_pages']+=1
        need(seen=={(level,seq,phase,side,page)for level,seq in cases for phase in range(125)for side in('before','after')for page in expected_pages},
             'Complete provider endpoint grid with no omissions')
        expected_counts={'paired_phases':1500,'paired125_sequences':12,'Lockit_paired_complete12B_normal_FS_relations':96,
            'Lockit_paired_bounded_API_semantic_relations':96,'Lockit_actual_owner_publication_activations':96,
            'Lockit_branch_field_source_derivations':216,'Lockit_whole_native_owned_carries':288}
        for key,value in expected_counts.items():need(report['counts'][key]==value,'All sealed paired reader observations '+key)
        for key,value in {'whole_nonstack_page_relations':123000,'separate_whole_loader_page_input_relations':3000,
                          'whole42_nonstack_page_endpoint_relations':126000,'whole_exact_loaded_input_endpoint_relations':3000}.items():
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
        helper_path=ROOT/'tools/m4-tree-paired/tree_relations_v2.py';pin(helper_path,report['files'][str(helper_path.resolve())])
        spec=importlib.util.spec_from_file_location('bounded125_typed_pair',helper_path)
        T=importlib.util.module_from_spec(spec);spec.loader.exec_module(T)
        contract=read(ROOT/'reports/m4-tree-source/dynamic-contracts-r1/normal-contracts.json',
                      'fbdd6e79dc26328ae2bd6a2e02d264971eaa190251d589f085904ffd9486829c')
        read(ROOT/'reports/m4-tree-review/pair-helper-r2/report.json','50005b020c8bbb409de494ed582e2a97fcb4f1ffb3d16aedb92fcd9f764315f9')
        original_tree_gate=read(ROOT/'reports/m4-tree-source/original125-source-r1/report.json',
                               '884abbe43d69570265b2b8539d04455bdb622664d136b0055b8ab073a8735c5f')
        tree_original={}
        for case in original_tree_gate['cases']:
            receipt=Path(case['receipt']);gate=read(receipt,case['sha256'])
            artifact=receipt.parent/'source-derivations.json'
            tree_original[case['sequence']]=read(artifact,gate['files'][str(artifact.resolve())])
        native_path=source_report.parent/'Tree-source-derivations.json'
        natives=read(native_path,source['files'][str(native_path.resolve())])
        actual_tree_pairs=output('Tree-paired-source-relations.json')
        need(len(natives)==len(actual_tree_pairs)==12,'Every current true native/source/paired tree case')
        preparation=read(ROOT/'reports/m4-joint-startup125/preparation-r4/report.json',
                         '243b6f4c86dc2b966789e23faed4a10fe2efa62ba51f43e854fa843acde392e7')
        order=preparation['selected_order'];treephase=next(i for i,r in enumerate(order)if r['entry']==0x4b7f70)
        prior_calls=2*sum(r['entry'] in expected_requests for r in order[:treephase])
        need(treephase==77 and prior_calls==2,'Literal table locates tree26 effects after first old4 pair')
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
            raw=case['API_relations'];need(len(raw)==34,'Every current complete provider26+old8 call order')
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
        artifact=out/'tree-seam-observations.json';artifact.write_text(json.dumps(relations,indent=2)+'\n');pin(artifact)
        counts['complete_paired_sequences']=12;counts['complete_paired_phases']=1500
        passed=True
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        receipt=dict(passed=passed,scope='Independent bounded paired observer/API return scope, raw12B FS records, complete32B/4096B owner byteflow, exact reconstructed whole provider pages and final sealed paired receipt',
            native_capture_archive_opened=False,original_capture_archive_opened=False,original_postRET_observed=False, bounded_mapping_adapter_is_capture=False,
            original_API_volatile_CPU_equivalence_claimed=False,original_scratch_stack_crossbranch_equality_claimed=False,
            whole_machine_observations_attributed_to_paired_reader=True,initializer_credit=False,counts=dict(counts),files=pins)
        path=out/'report.json';path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(passed=passed,report_sha256=sha(path),counts=dict(counts))))


def sha_bytes(raw):return hashlib.sha256(raw).hexdigest()


if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve(),sys.argv[3])
