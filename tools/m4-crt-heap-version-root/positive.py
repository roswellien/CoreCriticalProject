"""Complete ordinary source/state comparison driven by the typed API witness."""
import json
import struct
from consumer import F,M,OLD
from before import stage
from prefix import predict,FRAGMENT,SOURCE_CALL,SOURCE_RETURN,ENTRY,API_CALL,API_SLOT,API_RETURN,RAW_API,MODE_CALL,MODE_ENTRY,MODE_RETURN,PROBE_CALL,PROBE_RETURN,PROBE_RET,QUERY_CALL,QUERY_SLOT,QUERY_RETURN,RAW_QUERY,ENV_CALL,ENV_SLOT,ENV_RETURN,SELECTOR_RET
from ownership import witness,phase_ownership,phase_query,TOKEN


def positive(row,entry,phases,program,index,level):
    result=json.loads((row/'result.json').read_bytes())
    F.require(result['passed'] and result['scenario']==index and result['control']==0,'Exact ordinary native request')
    F.require(result['writer_complete'] and result['entry_executed'] and result['poisoned_retry'] and
              not result['State_reseed_after_writer'] and not result['full_CRT'] and not result['whole_M4_complete'],
              'Bounded carried startup with unchanged poisoned retry')
    F.require(result['source_events']==len(entry.events) and result['writer_events']==97 and result['data_routes']==1,
              'All earlier original source/writer routes retained')
    job=F.words((row/'heap-version-job.bin').read_bytes(),64)
    actual=witness(row,job);model=predict(entry,program,TOKEN,actual['response'])
    good=model['selector_returned'];pc=model['fault_PC'];target=model['fault_address']
    F.require(job[:22]==(0,0x20001858,0x20001860,len(model['accesses']),2,11,5,10,0,pc,target,
        1,0,1,1,1,1,1,1,1,0,1) and job[22]==job[23] and
        job[24:]==(FRAGMENT,ENTRY,SOURCE_CALL,SOURCE_RETURN,MODE_ENTRY,MODE_CALL,21,84,
            0x2000184c,0x780058b5,PROBE_CALL,PROBE_RETURN,QUERY_CALL,QUERY_SLOT,RAW_QUERY,QUERY_RETURN,1,1,86,2086,
            0x20000618,0x200017b8,1,actual['query_words'][3],37,1,1,1,int(good),int(not good),26,23,8,3,
            ENV_CALL,ENV_SLOT,0x345e6,0x7800ccc5,148,2086),
        'Exact genuine source progress, query response, transport and privately closed heap')
    F.require((row/'heap-version-lower-input.bin').read_bytes()==bytes(4096),'Declared ordinary lower-page input')
    phases.update(model['phases']);final=stage(model['state'],model['fx'],model['cpu'],model['memory'])
    phases['entry-after-fault'],phases['retry-after']=final,dict(final)
    tags={name.split('/')[1] for name in row.inventory if name.startswith(row.name+'/') and name.count('/')==1}
    F.require(tags==set(phases) and len(phases)==40,'Exact full40-checkpoint ordinary inventory')
    for tag,files in phases.items():
        files.update(phase_ownership(tag,actual));files.update(phase_query(tag,actual,model))
        F.full_stage(row,tag,files,index==0 and tag.startswith(('heap-create-','heap-mode-','heap-version-')))
    evidence=OLD.evidence(entry)
    evidence['mainargs-job.bin']=struct.pack('<20I',M.SLOT,M.RAW,*([0]*13),1,0,0,pc,target)
    evidence['mainargs-events.bin'],evidence['mainargs-accesses.bin']=bytes(256),bytes(1280)
    for name,value in evidence.items():
        captured=(row/name).read_bytes()
        F.require((json.loads(captured) if name.endswith('.json') else captured)==value,'Exact carried evidence '+name)
    reason=('Genuine selector returned; heap mode publication remains unadmitted' if good else
            'Required genuine CRT GetEnvironmentVariableA remains unresolved')
    F.require((result['fault_reason'],result['fault_site'],result['fault_target'])==(0 if good else 1,pc,target),
              'Truthful original selector RET or environment CALL boundary')
    for name in ('mainargs-reason.txt','heap-version-reason.txt'):
        F.require((row/name).read_text().strip()==reason,'Exact first bounded diagnostic')
    for name,value in (('initterm',entry.init_reason),('control',entry.control_reason),('matherr','')):
        F.require((row/(name+'-reason.txt')).read_text().strip()==value,'Unchanged earlier diagnostic')
    for actor in ('writer','entry'):
        M.D.host((row/(actor+'-host-before.bin')).read_bytes(),(row/(actor+'-host-after.bin')).read_bytes())
    entry_job=(row/'entry-job.bin').read_bytes()
    F.require(len(entry_job)==40 and entry_job[32:]==bytes(8) and struct.unpack_from('<3I',entry_job,20)==(0 if good else 1,pc,target),
              'Real bounded entry fault without fixture callback')
    def ledger(name,values,capacity):
        raw=b''.join(struct.pack('<5I',*v) for v in values)
        F.require((row/name).read_bytes()==raw+bytes(capacity-len(raw)),'Complete independent typed ledger '+name)
    ledger('heap-version-accesses.bin',model['accesses'],1280)
    ledger('heap-version-api-accesses.bin',[model['API_return_access'],model['query_return_access']],160)
    ledger('heap-version-output-accesses.bin',model['query_output_accesses'],1280)
    events=[(1,FRAGMENT,0x20001860,0),(2,SOURCE_CALL,ENTRY,SOURCE_RETURN),
        (3,API_CALL,API_SLOT,RAW_API),(4,API_CALL,0x20001848,API_RETURN),(5,0x780039d8,0x78035000,TOKEN),
        (6,MODE_CALL,MODE_ENTRY,MODE_RETURN),(7,PROBE_CALL,0x780058b5,PROBE_RETURN),
        (8,PROBE_RET,PROBE_RETURN,0x20000620),(9,QUERY_CALL,QUERY_SLOT,RAW_QUERY),
        (10,QUERY_CALL,0x20000618,QUERY_RETURN),
        (11,SELECTOR_RET,MODE_RETURN,0x20001854) if good else (11,ENV_CALL,ENV_SLOT,0x345e6)]
    raw=b''.join(struct.pack('<4I',*v) for v in events)
    F.require((row/'heap-version-events.bin').read_bytes()==raw+bytes(256-len(raw)),
              'Original CALL/RET and separate finite API-return event ledger')
    F.require(F.words((row/'heap-version-scheduler.bin').read_bytes(),8)==model['scheduler'],'Only original EIP scheduler seam')
    F.require(F.words((row/'heap-version-undefined.bin').read_bytes(),8)==
        (ENTRY,API_RETURN,0x780058db,0x780058c5,QUERY_RETURN,0,0,0),'Five exact source AF representatives')
    unused={
        'filename-job.bin':struct.pack('<22I',0,0xa11c0000+index,*([0]*18),0x78037174,0x7800bbd6),
        'filename-witness.bin':bytes(536),
        'commandline-job.bin':struct.pack('<28I',*([0]*4),0x3442e,*([0]*20),0x33000000,0x78037174,0x78001897),
        'commandline-accesses.bin':bytes(320),'commandline-consumer-accesses.bin':bytes(320),'commandline-events.bin':bytes(256),
        'parser-job.bin':struct.pack('<20I',*([0]*14),0x7800bc48,0x7800bbf7,0x7800bbfc,0x7800bce6,0x780379e1,436),
        'parser-accesses.bin':bytes(640),'parser-events.bin':bytes(128),'parser-undefined.bin':bytes(32),
        'locale-job.bin':struct.pack('<24I',*([0]*15),0x78003dd2,0x78003ddb,0x78001055,0x7800107b,0x780012b3,0x78001080,0x7803708c,17,269),
        'locale-accesses.bin':bytes(640),'locale-events.bin':bytes(128),'locale-scheduler.bin':bytes(40),
        'heap-job.bin':struct.pack('<26I',*([0]*16),FRAGMENT,ENTRY,SOURCE_CALL,SOURCE_RETURN,API_CALL,API_SLOT,API_RETURN,RAW_API,17,84),
        'heap-accesses.bin':bytes(640),'heap-events.bin':bytes(128),'heap-undefined.bin':bytes(32),'heap-scheduler.bin':bytes(32),
        'heap-create-job.bin':struct.pack('<32I',*([0]*24),FRAGMENT,ENTRY,SOURCE_CALL,SOURCE_RETURN,MODE_ENTRY,MODE_CALL,18,84),
        'heap-create-accesses.bin':bytes(640),'heap-create-api-accesses.bin':bytes(160),'heap-create-events.bin':bytes(128),
        'heap-create-undefined.bin':bytes(32),'heap-create-scheduler.bin':bytes(32),'heap-create-witness.bin':bytes(128),
        'heap-mode-job.bin':struct.pack('<44I',*([0]*24),FRAGMENT,ENTRY,SOURCE_CALL,SOURCE_RETURN,MODE_ENTRY,MODE_CALL,20,84,
            0,0x780058b5,PROBE_CALL,PROBE_RETURN,QUERY_CALL,QUERY_SLOT,RAW_QUERY,QUERY_RETURN,0,0,86,2026),
        'heap-mode-accesses.bin':bytes(1280),'heap-mode-api-accesses.bin':bytes(160),'heap-mode-events.bin':bytes(256),
        'heap-mode-undefined.bin':bytes(32),'heap-mode-scheduler.bin':bytes(32),'heap-mode-witness.bin':bytes(128),
        'heap-mode-lower-input.bin':bytes(4096)}
    for name,value in unused.items(): F.require((row/name).read_bytes()==value,'Exact unused service '+name)
    owners=[actual['registry_owner']]
    for name in ('heap-create-registry.bin','heap-mode-registry.bin'):
        values=struct.unpack('<18Q',(row/name).read_bytes())
        F.require(values[0]==1 and values[1]!=0 and values[1] not in owners and values[2:]==(1,*([0]*15)),
                  'Distinct unused constructor-only owner without resource '+name)
        owners.append(values[1])
    for name in ('filename','commandline','parser','locale','heap','heap-create','heap-mode'):
        F.require((row/(name+'-reason.txt')).read_text().strip()=='','No fabricated unused fault '+name)
    root_files=set(evidence)|set(unused)|{'heap-create-registry.bin','heap-mode-registry.bin','input.bin','writer-record.bin',
        'writer-host-before.bin','writer-host-after.bin','entry-host-before.bin','entry-host-after.bin','entry-job.bin','result.json',
        'matherr-reason.txt','control-reason.txt','initterm-reason.txt','mainargs-reason.txt','filename-reason.txt','commandline-reason.txt',
        'parser-reason.txt','locale-reason.txt','heap-reason.txt','heap-create-reason.txt','heap-mode-reason.txt','heap-version-reason.txt',
        'heap-version-job.bin','heap-version-accesses.bin','heap-version-api-accesses.bin','heap-version-output-accesses.bin',
        'heap-version-events.bin','heap-version-undefined.bin','heap-version-scheduler.bin','heap-version-witness.bin','heap-version-registry.bin',
        'heap-version-lower-input.bin','heap-version-query-witness.bin','query-input.bin','query-output.bin',
        'heap-version-create-api-before.bin','heap-version-create-api-after.bin','heap-version-destroy-api-before.bin',
        'heap-version-destroy-api-after.bin','heap-version-query-api-before.bin','heap-version-query-api-after.bin'}
    F.require(row.inventory[row.name]==root_files,'Complete exact ordinary root evidence inventory')
    F.require(struct.unpack_from('<I',model['memory'][0x78035000],4)[0]==0,'Heap-mode global not published by unexecuted caller')
    return dict(index=index,level=level,source_PCs=len(model['PCs']),source_accesses=len(model['accesses']),
        actual_source_CALLs=len(model['routes']),genuine_source_RETs=2 if good else 1,API_return_reads=2,
        API_transport_DWORDs=37,checkpoints=40,whole_State=3504,whole_FX=512,whole_Runtime_CPU=40,whole_pages=21,
        actual_HeapCreate=True,actual_HeapDestroy=True,actual_GetVersionExA=True,native_BOOL=actual['query_words'][3],
        measured_major=actual['query_words'][18],measured_platform=actual['query_words'][19],selector_returned=good,
        selector_value=1 if good else None,environment_reached=not good,heap_mode_published=False,
        heap_initializer_RET=False,root_full_causal_model=False,original_API_internals_equivalence=False)
