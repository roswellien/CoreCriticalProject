"""Independent bounded four-root source/private relation, with explicit historical export correction."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_formatting_native.py');s=p.read_text()
for a,b in [('native-source-r9','native-family-source-r3'),('0f2e817ff2bf938e32be26d7018d3921be5142461bf54ddfe70e0a676daa2306','52d776251f86a787db71d4b15a91f174737099986585c8dfe7a0d5c9c452e521'),('native-witnesses-r4','native-family-witnesses-r2'),('284091a7d9efd64e695d399e89de94496a8c8c9181e4f0a3ecf589ef3d864510','ac778e7886943f67cf5bc5a5e0f7e1f04f00ce71dde5d1bf398309f7c270bcd5'),('preparation-r15','preparation-r18'),('bbe18a53a6c8c400f3274e470a28ded84d7c7c45c4fc860cf5e598ed4d5730aa','68498a9eaaf924205e11bbf30fbaa355380afc528b892c6739f9a1d199731d06'),('fixture-execution-r4','family-fixture-execution-r1'),('55ecbdc1a115f73ab046ea92f6e33f5af0020d92a530dbe2a3e145af7d37bba0','5ecd8260c6625a589c8e1c517b41c1c7f8deddfbbeb1b61825f6e337c1767297'),('[0x4df610,0x4e0710,0x4e0810]','[0x4df610,0x4e0710,0x4e0810,0x4e1ca0]'),('native15/build7','native18/familybuild2'),('len(rows)==len(proofs)==6','len(rows)==len(proofs)==8'),('(8,10,12)[phase]','(8,10,12,11)[phase]'),('native15 formatter3','native18 formatter4')]:
 assert a in s,a;s=s.replace(a,b)
a="proofs=C.read(area/'native-family-witnesses-r2/witness-source-relations.json',witness['files'][str((area/'native-family-witnesses-r2/witness-source-relations.json').resolve())]);"
b="""export=C.read(area/'native-family-witness-export-r1/report.json','39178a042636c988b74801deeb78ca01de5be23e649732fc1e4e1826909529e5');C.need(export['passed']and export['rows']==8 and len(export['corrections'])==2 and not export['capture_reader_opened']and export['source_receipt_sha256']==C.PINS[str((area/'native-family-source-r3/report.json').resolve())]and export['witness_receipt_sha256']==C.PINS[str((area/'native-family-witnesses-r2/report.json').resolve())],'Explicit export-only formatter-owner shadow correction binds immutable actual proof');proofs=C.read(area/'native-family-witness-export-r1/witness-source-relations.json',export['files'][str((area/'native-family-witness-export-r1/witness-source-relations.json').resolve())]);
        family=C.read(Path(native['native_include'])/'family-contracts.json',native['mixed_contracts_sha256']);normal['cases'].append(dict(root_contract=dict(owned_pointer_field=0x60b66c),owned_accesses=family['additional_format_owned_order']));"""
assert s.count(a)==1;s=s.replace(a,b)
a="        operations=C.pin(Path(native['native_include'])/'formatting_operations.inc').read_text();"
b="""        # Independent typed roles and complete genuine capacities for the additional MFC domain.
        for r in rows:
            if r['root']!=0x4e1ca0:continue
            owners=r['mixed_owners'];contracts=family['mixed_interface'];C.need(len(owners)==3 and len({o['generation']for o in owners})==3,'Three distinct actual allocation occurrences');ops=[]
            for o,c in zip(owners,contracts['MFC_allocation_contracts']):
                C.need(o['owner_role']==c['owner_index']and o['allocation_CALL_pc']==c['allocation_CALL_pc']and o['requested']==c['requested']and o['extent']==c['measured_capacity']and o['native']and o['live'],'Exact actual MFC source site/role/current generation/capacity')
                initial=bytes.fromhex(o['initial']);full=bytearray(initial);C.need(len(initial)==o['extent'],'Full current genuine allocation initial capacity')
                for row in o['source_owned_accesses']:
                    pc,address,value,width,writing=row;C.need(writing==1 and width==4 and o['guest']<=address and address+width<=o['guest']+o['requested'],'Literal wholeDWORD store stays within source requested role');full[address-o['guest']:address-o['guest']+width]=value.to_bytes(width,'little');ops.append((pc,o['owner_role'],address-o['guest'],width,writing,value))
                C.need(full.hex()==o['source_final_hex']and full[o['requested']:]==initial[o['requested']:],'Entire original acquisition-derived MFC backing and untouched capacity tail');counts['whole_mixed_capacity_byteflows']+=1
            ordered=sorted(ops,key=lambda row:next(i for i,a in enumerate(r['source_accesses'])if a[0]==row[0]and a[1]==owners[row[1]]['guest']+row[2]))
            for actual,c in zip(ordered,contracts['owned_access_contracts']):
                pc,role,offset,width,writing,value=actual;relation=c['source_value_relation'];want=relation['literal']if'literal'in relation else owners[relation['owner_index']]['guest']+relation['offset']
                C.need((pc,role,offset,width,writing,value)==(c['source_pc'],c['owner_index'],c['owned_offset'],c['width'],int(c['write']),want),'Exact causal source PC/role/direction/width and literal or typed owner value');counts['independent_mixed_source_store_joins']+=1
            C.need(len(ordered)==len(contracts['owned_access_contracts'])==10,'No extra mixed owner access admitted')
            for c in contracts['publication_contracts']:
                owner=owners[c['owner_index']];matched=[a for a in r['source_accesses']if a[0]==c['publication_pc']and a[1]==c['publication_address']];C.need(matched==[[c['publication_pc'],c['publication_address'],owner['guest'],4,1]],'Exact source current occurrence primary publication');counts['independent_mixed_source_publications']+=1
            for i,c in enumerate(r['Lockit_API_relations']):
                g=bytes.fromhex(c['derived_CS24_hex']);n=bytes.fromhex(c['actual_native_CS40_hex']);words=c['actual_API_words'];C.need(len(g)==24 and len(n)==40 and len(words)==32 and c['depth']==(1,0)[i]and words[2]==(0x7810a30b,0x7810a35e)[i]and words[16]==c['native_owner']and words[18]==c['depth'],'Actual provider API identity/owner/depth and bounded typed CS input');gw=struct.unpack('<6I',g);nw=struct.unpack('<QiiQQQ',n);C.need(gw[1]==nw[1]&0xffffffff and gw[2]==nw[2]and gw[3]==nw[3]&0xffffffff and gw[5]==nw[5]&0xffffffff,'Guest typed24/native opaque40 semantic lock fields');counts['independent_mixed_API_CS_relations']+=1
        operations=C.pin(Path(native['native_include'])/'formatting_operations.inc').read_text();"""
assert s.count(a)==1;s=s.replace(a,b)
a="{'strict_native_phases':6,'whole_BEFORE_pages':420,'whole_AFTER_pages':420,'whole_source_access_records':7966,'whole_native_owner_backings':6,'literal_cdecl_CALL_RET':18,'literal_table_dispatches':24,'complete_actual_lifecycles':2,'whole_provider_checkpoints':148,'whole_heap_prefix_checkpoints':42,'literal_producer_source_frees':2,'actual_native_CS_deletes':10,'actual_native_formatter_cleanup_frees':6}"
b="{'strict_native_phases':8,'whole_BEFORE_pages':560,'whole_AFTER_pages':560,'whole_source_access_records':13954,'whole_native_owner_backings':8,'whole_mixed_native_owner_backings':6,'literal_cdecl_CALL_RET':24,'literal_table_dispatches':32,'complete_actual_lifecycles':2,'whole_provider_checkpoints':250,'whole_heap_prefix_checkpoints':42,'literal_mixed_MFC_source_frees':6,'literal_producer_source_frees':2,'actual_native_CS_deletes':10,'actual_native_formatter_cleanup_frees':8}"
assert s.count(a)==1;s=s.replace(a,b)
a="{'literal_private_cdecl_rows':18,'literal_private_owned_operands':66,'literal_private_publications':6,'literal_private_table_dispatches':24,'actual_cleaned_allocation_lifetimes':8,'actual_cleaned_native_CS_lifetimes':10,'outside_return_whole_State_source_proofs_consumed':2}"
b="{'literal_private_cdecl_rows':24,'literal_private_owned_operands':90,'literal_private_publications':8,'literal_private_table_dispatches':32,'literal_private_mixed_owner_rows':20,'actual_cleaned_allocation_lifetimes':16,'actual_cleaned_native_CS_lifetimes':10,'outside_return_whole_State_source_proofs_consumed':2}"
assert s.count(a)==1;s=s.replace(a,b)
s=s.replace('C.pin(__file__);C.pin(C.__file__)','C.pin(__file__);C.pin(R/\'tools/m4-tree-review/review_formatting_native.py\');C.pin(C.__file__)')
s=s.replace('generic_formatter_closed=False,','generic_formatter_closed=False,mixed_private_publication_rows_independently_compared=False,mixed_private_FS_records_independently_compared=False,fault_cleanup_proof_claim=False,')
exec(compile(s,str(p),'exec'),globals())
