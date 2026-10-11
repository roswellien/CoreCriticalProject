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
    out=ROOT/'reports/m4-lockit-review'/name;need(not out.exists(),'Fresh bounded paired review');out.mkdir(parents=True)
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
        actual=read(ROOT/'reports/m4-joint-startup124-root/execution-r2/report.json','e0ca3ce031afbcde80ff84c0968d30850972625d2f6d8e2a8c8934386a2e7732')
        need(actual['passed']and actual['build_sha256']=='05a198d319f2e3ee2259b998a8989db23df0b20afd40416fb185e7a0b1d17c30', 'Exact current nativeprep5/build4 run')
        prep=read(ROOT/'reports/m4-lockit-native/preparation-r5/report.json','965ea738333677c308749108b7f0b211772e89d4dd5e2ed14ea561cb63d0bdc1')
        original=read(ROOT/'reports/m4-lockit-paired-provider/original-r2/report.json','48f184d6edbaae5e1ec9d384f743089210e65dea9655822a4f517b41fa3b757b')
        observer=read(ROOT/'reports/m4-lockit-review/full-original-r1/report.json','570bc3dc54aadcb7b67abccb06182c7177eeb7d059bb31ea5caf40f57625659f')
        need(original['passed']and observer['passed']and report['Lockit_independent_original_compiled_observer_gate_sha256']==sha(ROOT/'reports/m4-lockit-review/full-original-r1/report.json'),
             'Actual complete compiled/linked observers and original source owner proof bound')
        for path in (ROOT/'tools/m4-lockit-paired-provider/paired_v2.py',ROOT/'tools/m4-lockit-paired-provider/original_v2.py'):
            files=report['files'] if path.name=='paired_v2.py' else original['files'];pin(path,files[str(path.resolve())])
        paired_code=(ROOT/'tools/m4-lockit-paired-provider/paired_v2.py').read_text(encoding='utf-8')
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
        patch_path=(ROOT/'reports/m4-lockit-paired-provider/original-r2/provider-observer-spans.json').resolve()
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
        expected_pages={0x7810a000:(sha_bytes(oldrx),sha_bytes(rx),sorted(declared_rx)),
                        0x78145000:(sha_bytes(rw),sha_bytes(rw),[]),
                        0x78146000:(sha_bytes(oldiat),sha_bytes(iat),sorted(declared_iat))}
        pages=output('Lockit-provider-page-relations.json');need(len(pages)==8928,'All three entire provider pages across1488before/afterphases')
        seen=set()
        for row in pages:
            key=(row['level'],row['sequence'],row['phase'],row['side'],row['page']);need(key not in seen,'Each complete paired provider endpoint once');seen.add(key)
            expected=expected_pages[row['page']]
            need((row['original_sha256'],row['native_sha256'],row['exact_declared_difference_offsets'])==expected,
                 'Every complete paired provider page equals independently reconstructed physical/authentic input and exact original observers')
            counts['independently_reconstructed_whole_provider_pages']+=1
        need(seen=={(level,seq,phase,side,page)for level,seq in cases for phase in range(124)for side in('before','after')for page in expected_pages},
             'Complete provider endpoint grid with no omissions')
        expected_counts={'paired_phases':1488,'paired124_sequences':12,'Lockit_paired_complete12B_normal_FS_relations':96,
            'Lockit_paired_bounded_API_semantic_relations':96,'Lockit_actual_owner_publication_activations':96,
            'Lockit_branch_field_source_derivations':216,'Lockit_whole_native_owned_carries':288}
        for key,value in expected_counts.items():need(report['counts'][key]==value,'All sealed paired reader observations '+key)
        counts['complete_paired_sequences']=12;counts['complete_paired_phases']=1488
        passed=True
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        receipt=dict(passed=passed,scope='Independent bounded paired observer/API return scope, raw12B FS records, complete32B/4096B owner byteflow, exact reconstructed whole provider pages and final sealed paired receipt',
            native_capture_archive_opened=False,original_capture_archive_opened=False,original_postRET_observed=False,
            original_API_volatile_CPU_equivalence_claimed=False,original_scratch_stack_crossbranch_equality_claimed=False,
            whole_machine_observations_attributed_to_paired_reader=True,initializer_credit=False,counts=dict(counts),files=pins)
        path=out/'report.json';path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(dict(passed=passed,report_sha256=sha(path),counts=dict(counts))))


def sha_bytes(raw):return hashlib.sha256(raw).hexdigest()


if __name__=='__main__':main(Path(sys.argv[1]).resolve(),Path(sys.argv[2]).resolve(),sys.argv[3])
