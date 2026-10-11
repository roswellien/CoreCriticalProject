"""Independent bounded exact-delta and ninth auxiliary-byte source review."""
from pathlib import Path
from collections import Counter
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def need(value,message):
    if not value:raise ValueError(message)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main(name):
    out=ROOT/'reports/m4-lockit-review'/name;need(not out.exists(),'Fresh exact paired preparation review');out.mkdir(parents=True)
    pins={};counts=Counter();passed=False;rows=[]
    def pin(path,digest=None):
        path=Path(path).resolve();actual=sha(path);need(digest is None or actual==digest,'Exact bounded preparation input '+str(path));need(str(path)not in pins or pins[str(path)]==actual,'Frozen bounded input');pins[str(path)]=actual;return path
    def read(path,digest=None):
        path=pin(path,digest);need(path.stat().st_size<=16*1024*1024,'Bounded preparation JSON');return json.loads(path.read_bytes())
    try:
        pin(__file__)
        prep=read(ROOT/'reports/m4-lockit-paired-provider/paired-preparation-r3/report.json','d7ad4c38d24209898dc693a3949aac11058d6428f05793082e738329871de78b')
        need(prep['passed']and not prep['native_reader_opened']and not prep['initializer_credit'],'Preparation only')
        for path,digest in prep['files'].items():pin(path,digest)
        old=(ROOT/'tools/m4-lockit-paired-provider/paired_v2.py').read_text(encoding='utf-8');new=(ROOT/'tools/m4-lockit-paired-provider/paired_v3.py').read_text(encoding='utf-8')
        start=new.index("  # The wrapper's auxiliary byte store");end=new.index('  lockit_roots=',start);auxiliary=new[start:end]
        need("lockit_fields.append(dict(root=0x500660,pc=0x50068b,address=0x60bf90,write=True,bytes=1,source_value=None))"in auxiliary and
             "auxiliary['bytes_hex']=='881590bf6000'"in auxiliary and "authored_branch_identities==native_branch_identities"in auxiliary,
             'Only exact physical auxiliary field added, all nine native source field identities required')
        stripped=new[:start]+new[end:]
        start=stripped.index('  # Keep the41 ordinary-page counter');end=stripped.index('  pin(__file__);passed=True',start)
        oldstart=old.index("  need(counts['paired_phases']==1488 and counts['paired124_sequences']==12",old.index('  ori.close()'));oldend=old.index('  pin(__file__);passed=True',oldstart)
        counters=stripped[start:end]
        need("counts['whole42_nonstack_page_endpoint_relations']=counts['whole_nonstack_page_relations']+counts['separate_whole_loader_page_input_relations']"in counters and
             "counts['whole_nonstack_page_relations']==122016"in counters and "counts['separate_whole_loader_page_input_relations']==2976"in counters and
             "counts['whole42_nonstack_page_endpoint_relations']==124992"in counters,'Exact ordinary/whole-loader scopes are distinct')
        normalized=stripped[:start]+old[oldstart:oldend]+stripped[end:]
        need(normalized==old,'Exactly two additive source inventory/counter changes; no other byte/numeric/ownership comparison changed')
        counts['reviewed_exact_additive_change_groups']=2
        pe_path=pin(ROOT/'tools/analysis/pe.py','bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638')
        spec=importlib.util.spec_from_file_location('bounded_auxiliary_PE',pe_path);PE=importlib.util.module_from_spec(spec);spec.loader.exec_module(PE)
        image=PE.PEImage(pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
        def physical(pc,n):return image.read(image.rva_range(pc-image.image_base,n)[0],n)
        need(physical(0x500670,1)==b'\x51'and physical(0x500685,12)==bytes.fromhex('8a54240333c0881590bf6000'),'Literal PUSH ECX; MOV DL,[ESP+3]; XOR EAX,EAX; MOV [60BF90],DL')
        original=read(ROOT/'reports/m4-lockit-paired-provider/original-r2/report.json','48f184d6edbaae5e1ec9d384f743089210e65dea9655822a4f517b41fa3b757b')
        path=(ROOT/'reports/m4-lockit-paired-provider/original-r2/original-source-access-ledgers.json').resolve();ledgers=read(path,original['files'][str(path)])
        selected=[row for row in ledgers if row['root']==0x500660];need(len(selected)==6 and {row['sequence']for row in selected}==set(range(6)),'All six genuine original root ledgers')
        for ledger in selected:
            accesses=ledger['rows'];writes=[(i,row)for i,row in enumerate(accesses)if row[0]==0x50068b and row[1]==0x60bf90 and row[3:]==[1,1]];need(len(writes)==1,'Unique original literal auxiliary write');wi,write=writes[0]
            reads=[(i,row)for i,row in enumerate(accesses[:wi])if row[0]==0x500685 and row[3:]==[1,0]];need(len(reads)==1,'Unique prior original literal auxiliary read');ri,operand=reads[0]
            stores=[row for row in accesses[:ri]if row[4]and row[1]<=operand[1]<row[1]+row[3]];need(stores,'Original input byte has dominating source stack store');store=stores[-1];offset=operand[1]-store[1]
            need(store[0]==0x500670 and store[3:]==[4,1]and offset==3 and ((store[2]>>24)&255)==operand[2]==write[2],'Original auxiliary derives exact high byte of genuine source PUSH ECX')
            rows.append(dict(sequence=ledger['sequence'],dominating_store=store,source_read=operand,source_write=write));counts['independent_original_auxiliary_byteflows']+=1
        source=read(ROOT/'reports/m4-lockit-source/connected-native-source-r3/report.json','5aea52d95b8a84ab0c8ae273604af7121ae3f2b88763610fd5d18a51fc99533f')
        path=(ROOT/'reports/m4-lockit-source/connected-native-source-r3/Lockit-header-derivations.json').resolve();fields=read(path,source['files'][str(path)])
        actual=[row for row in fields if row['root']==0x500660 and row['field']==0x60bf90];need(len(actual)==12,'All twelve current native auxiliary derivations')
        for row in actual:
            p=row['provenance'];need(row['write_pc']==0x50068b and row['read_pc']==0x500685 and p['kind']=='dominating_source_store'and
                 p['pc']==0x500670 and p['width']==4 and p['extracted_byte_offset']==3 and row['read_address']==p['address']+3 and
                 p['value']==row['source_root_BEFORE_cpu'][1]and row['value']==(p['value']>>24)&255,'Native auxiliary retains exact independent source PUSH/read/store provenance')
            counts['independent_native_auxiliary_byteflows']+=1
        need(actual==prep['native_source_auxiliary_rows']and [row['source_write']for row in rows]==prep['genuine_original_auxiliary_source_writes'],'Preparation emitted branch facts exactly match separately sealed genuine source proofs')
        need(1488*2*41==122016 and 1488*2==2976 and 1488*2*42==124992,'Complete endpoint counter arithmetic and distinct loader coverage')
        counts['ordinary_whole_page_endpoints']=122016;counts['separate_whole_loader_page_endpoints']=2976;counts['combined42_nonstack_page_endpoints']=124992
        passed=True
    except Exception:
        (out/'failure.txt').write_text(traceback.format_exc(),encoding='utf-8');raise
    finally:
        path=out/'auxiliary-provenances.json';path.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8');pin(path)
        report=dict(passed=passed,scope='Independent physical/source ninth auxiliary byte and exact additive paired v3 change review; preserves ordinary41 and separately related full loader page coverage',native_capture_archive_opened=False,original_capture_archive_opened=False,actual_final_paired_capture_credit=False,initializer_credit=False,counts=dict(counts),files=pins)
        path=out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(dict(passed=passed,report_sha256=sha(path),counts=dict(counts))))
if __name__=='__main__':main(sys.argv[1])
