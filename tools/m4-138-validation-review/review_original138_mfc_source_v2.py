"""Independent six-domain causal byteflow, defined flags and true-TIB source audit.

The inputs are sealed small exports from the current original worker. Archive
readers remain closed. Source-derived intermediate control is distinguished
from the observed normal boundaries and actual Win32 replies.
"""
from pathlib import Path
from collections import Counter
import hashlib, json, struct, sys, traceback

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'reports/m4-startup138-original/mfc-source-r2/report.json'
SOURCE_SHA='6a4e28040c31aebbc108904cb6a574d964aa28f045ff446f1362deaedd260801'
VALIDATION_SHA='02ea1ce07ac3e5aa5dff6e20813b956117383784ae4f5e1ffd6aa1822f603f5f'
ADMISSION_SHA='eeab0505853554e353c389a6cae857f6b2c5696c0c2044e406880234b9f37e0c'
PINS={}

def need(value,label):
    if not value:raise ValueError(label)

def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def pin(path,identity=None):
    path=Path(path).resolve();need(path.suffix.lower()not in('.mwb','.zip','.mwi')and path.name not in('index.json','payload.bin','transport.json','manifest.json','bundle.json')and path.stat().st_size<=32*1024*1024,'Only bounded ordinary sealed inputs; archive readers remain closed')
    actual=sha(path);need(identity is None or identity==actual,'Exact current input '+str(path))
    need(str(path)not in PINS or PINS[str(path)]==actual,'Immutable audit input')
    PINS[str(path)]=actual;return path

def read(path,identity=None):return json.loads(pin(path,identity).read_bytes())
def equal(actual,expected,label):need(actual==expected,label)
def words(data,offset=0,count=1):return struct.unpack_from('<'+'I'*count,data,offset)

def main(name):
    out=ROOT/'reports/m4-138-validation-review'/name;need(not out.exists(),'Fresh current review');out.mkdir()
    passed=False;counts=Counter();relations=[]
    try:
        source=read(SOURCE,SOURCE_SHA)
        need(source['passed']and not source['source_AFTER_seed']and not source['capture_archive_reader_opened'],'Current literal source, no AFTER seed')
        validation=read(source['original_validation_path'],VALIDATION_SHA)
        need(validation['passed']and validation['reader_closed'],'Current original reader closed')
        execution=read(Path(validation['execution_path'])/'report.json',validation['execution_sha256'])
        build=read(execution['build_path'],execution['build_sha256'])
        preparation=read(Path(build['preparation'])/'report.json',build['preparation_sha256'])
        admission=read(ROOT/'reports/m4-138-validation-review/original138-observer-prelaunch-r1/report.json',ADMISSION_SHA)
        adapter=read(ROOT/'reports/m4-startup138-original/mfc-source-preparation-r2/report.json','71d8e8e5b0656a80266228f5130de545b8d12eb6ca86fe59152d67496413dcb0');need(adapter['passed']and adapter['exact_inverse_restores_parent']and adapter['files'][str((ROOT/'reports/m4-startup138-original/original-validation-r3/report.json').resolve())]==VALIDATION_SHA,'Current additive MFC source adapter lineage')
        for path,identity in adapter['files'].items():pin(path,identity)
        need(validation['counts']['phases']==828 and validation['combined_pages']==69 and validation['callbacks']==108 and validation['initializer_credit']==0 and not validation['native_executed'],'Current138 observation domain without credit')
        need(len(preparation['observed_pages'])==43 and len(preparation['extra_whole_source_pages'])==26,'Complete global69 preparation geometry')
        mfc_extras=(0x5cd000,0x5e3000,0x5e9000);need(set(mfc_extras)<=set(preparation['extra_whole_source_pages']),'All inherited MFC46 own-domain extras retained')
        equal(admission['build_sha256'],execution['build_sha256'],'Actual current whole linked observer admission')
        for path,identity in source['files'].items():pin(path,identity)
        rows=read(SOURCE.parent/'source-derivations.json')
        current=read(Path(source['original_validation_path']).parent/'fresh-MFC-observations.json')
        equal([row['sequence']for row in rows],list(range(6)),'All six source domains')
        equal([row['sequence']for row in current],list(range(6)),'All six actual domains')
        contract=read(ROOT/'reports/m4-mfc1168-probe/validation-r6/reached-instruction-contracts.json')
        program={row['pc']:row for row in contract['instructions']}
        equal(len(program),142,'Complete literal physical source union')
        consume={'je':('ZF',),'jne':('ZF',),'jge':('SF','OF')}
        allowed={'mov','push','pop','call','ret','je','cmp','jmp','test','jne','leave','lea','jge','sub','xor','and'}
        equal({row['mnemonic']for row in program.values()},allowed,'Exact finite mnemonic/control consumer inventory')
        for sequence,(derived,observed)in enumerate(zip(rows,current)):
            def raw(key):
                path=Path(source['original_validation_path']).parent/'actual-MFC-inputs'/key
                identity=validation['files'][str(path.resolve())]
                return pin(path,identity).read_bytes()
            stem=f'phase/{sequence}/13/'
            memory={};targets={};record=raw(f'phase/{sequence}/13.bin')
            equal(len(record),356992,'Entire genuine original phase')
            for i,address in enumerate(preparation['observed_pages']):
                memory[address]=bytearray(record[2276+i*4096:2276+(i+1)*4096])
                targets[address]=record[178404+i*4096:178404+(i+1)*4096]
            for address in mfc_extras:
                memory[address]=bytearray(raw(stem+f'extra-before/{address}.bin'))
                targets[address]=raw(stem+f'extra-after/{address}.bin')
            for owner in('MFC','CRT'):
                for address,*_ in struct.iter_unpack('<4I',raw(stem+'MFC1168/BEFORE/'+owner+'/metadata.bin')):
                    payload=raw(stem+f'MFC1168/BEFORE/{owner}/{address}.bin')
                    need(address not in memory or memory[address]==payload,'Genuine whole input aliases agree')
                    memory[address]=bytearray(payload);targets[address]=raw(stem+f'MFC1168/AFTER/{owner}/{address}.bin')
            teb=words(raw(stem+'TEB-before-base.bin'))[0];before_teb=raw(stem+'TEB-before.bin')
            equal(len(before_teb),8192,'Actual root-entry TIB extent')
            equal(words(before_teb,24)[0],teb,'Actual coherent TIB identity')
            memory[teb]=bytearray(before_teb[:4096]);memory[teb+4096]=bytearray(before_teb[4096:])
            for owner in derived['source_borrowed_backings']:
                payload=raw(stem+'MFC1168/BEFORE/domain/'+owner['role']+'/bytes.bin')
                equal(payload.hex(),owner['initial_hex'],'Whole borrowed capacity source preimage')
                equal(len(payload),owner['extent'],'Exact complete borrowed extent')
                memory[owner['address']]=bytearray(payload)
            def get(address,size):
                result=bytearray();cursor=address
                while cursor<address+size:
                    owners=[(base,data)for base,data in memory.items()if base<=cursor<base+len(data)]
                    need(owners,'Causal operand has genuine BEFORE owner '+hex(cursor))
                    base,data=max(owners,key=lambda row:row[0]+len(row[1]));end=min(address+size,base+len(data));chunk=bytes(data[cursor-base:end-base])
                    for other,other_data in memory.items():
                        lo,hi=max(cursor,other),min(end,other+len(other_data))
                        if lo<hi:equal(other_data[lo-other:hi-other],chunk[lo-cursor:hi-cursor],'Exact live overlap alias')
                    result.extend(chunk);cursor=end
                return bytes(result)
            equal(len(derived['source_accesses']),113,'All causal operand events')
            for pc,address,value,width,writing in derived['source_accesses']:
                need(pc in program and width in(1,2,4,8),'Exact physical source operand PC/width')
                payload=value.to_bytes(width,'little');old=get(address,width)
                if writing:
                    for base,data in memory.items():
                        lo,hi=max(base,address),min(base+len(data),address+width)
                        if lo<hi:data[lo-base:hi-base]=payload[lo-address:hi-address]
                    counts['independent_causal_source_writes']+=1
                else:equal(old,payload,'Complete independent source read');counts['independent_causal_source_reads']+=1
            for address,expected in targets.items():
                if address==0x20001000:continue
                equal(get(address,4096),expected,'Whole source-derived nonstack endpoint')
                counts['independent_whole_nonstack_page_byteflows']+=1
            for owner in derived['source_borrowed_backings']:
                actual=get(owner['address'],owner['extent'])
                equal(actual.hex(),owner['source_final_hex'],'Independent entire borrowed byteflow')
                equal(actual,raw(stem+'MFC1168/AFTER/domain/'+owner['role']+'/bytes.bin'),'Current measured whole borrowed endpoint')
                counts['independent_whole_borrowed_backings']+=1
            equal(words(before_teb)[0],derived['source_FS_BEFORE'],'Genuine source-entry FS head')
            equal(get(teb,4),raw(stem+'TEB-after.bin')[:4],'Actual root-return TIB head')
            equal(derived['source_FS_BEFORE'],derived['source_FS_AFTER'],'Literal imported EH frame balanced')
            equal(derived['source_CPU_AFTER'],observed['CPU_after'],'Entire actual root-return CPU')
            equal(derived['source_FX_hex'],observed['FX_after_hex'],'Whole actual guest FX')
            equal(derived['source_ENV_hex'],observed['ENV_after_hex'],'Whole actual guest ENV')
            equal(len(derived['source_normal_boundary_relations']),7,'All measured normal boundaries')
            equal(len(derived['source_API_relations']),4,'All measured typed API pairs')
            equal([row['PC']for row in derived['flag_lifetimes']],derived['source_PCs'],'Complete chronological flag-domain inventory')
            before={};api_sites={row['source_PC']for row in derived['source_API_relations']}
            for row in derived['flag_lifetimes']:
                pc=row['PC'];used=consume.get(program[pc]['mnemonic'],())
                need(not set(used)&set(before),'Every consumed source flag is defined before control reads it')
                counts['independent_defined_source_flag_consumers']+=bool(used)
                before={}if pc in api_sites else row['undefined_flags']
            for field in('actual_per_instruction_chronological_trace','intermediate_source_FS_observation','whole_stack_endpoint_claim','whole_TEB_endpoint_claim','opaque_OS_CS_internal_writes_claim','source_AFTER_seed'):equal(derived[field],False,'Exact bounded original source claim '+field)
            counts['whole_actual_root_CPU_FX_ENV_joins']+=1
            counts['actual_TIB_head_source_joins']+=2
            relations.append(dict(sequence=sequence,source_PCs=derived['source_PCs'],actual_root_CPU=observed['CPU_after'],source_derived_intermediate_control=True,actual_instruction_trace=False))
        equal(counts['independent_defined_source_flag_consumers'],66,'All eleven current condition consumers per domain')
        equal(counts['independent_whole_borrowed_backings'],30,'All six-domain borrowed capacities')
        equal(counts['independent_whole_nonstack_page_byteflows'],2064,'Exact retained MFC46 plus full actual module endpoint byteflows')
        equal(counts['whole_actual_root_CPU_FX_ENV_joins'],6,'All actual normal root endpoints')
        equal(counts['actual_TIB_head_source_joins'],12,'All source-entry and source-return FS head joins')
        pin(ROOT/'tools/m4-tree-review/review_original131_mfc_source.py');pin(ROOT/'tools/m4-138-validation-review/derive_mfc_source_review.py');pin(ROOT/'reports/m4-138-validation-review/mfc-source-review-preparation-r1/report.json');pin(__file__);pin(sys.executable)
        for path,identity in PINS.items():equal(sha(path),identity,'Successful physical review inputs stable')
        passed=True
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        path=out/'report.json'
        path.write_text(json.dumps(dict(passed=passed,current_source_sha256=SOURCE_SHA,original_validation_sha256=VALIDATION_SHA,admission_sha256=ADMISSION_SHA,counts=dict(counts),source_AFTER_seed=False,capture_archive_reader_opened=False,all_bounded_readers_closed=True,initializer_credit=0,native_credit=0,semantic_page_domain=46,global_original138_page_domain=69,widget_global69_semantics_reviewed=False,source_derived_intermediate_control=True,actual_instruction_trace=False,files=PINS),indent=2)+'\n')
        print(json.dumps(dict(passed=passed,sha256=sha(path),counts=dict(counts))))

if __name__=='__main__':main(sys.argv[1])
