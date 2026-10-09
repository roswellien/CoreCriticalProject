"""Whole ordinary native comparison to BEFORE, source and declared stack input."""
import json
import struct
from consumer import F,M,OLD
from before import stage,STACK_PAGE,PROBE_PAGE
from prefix import predict,FRAGMENT,SOURCE_CALL,SOURCE_RETURN,ENTRY,API_CALL,API_SLOT,API_RETURN,RAW_API,MODE_CALL,MODE_ENTRY,MODE_RETURN,PROBE,PROBE_CALL,PROBE_RETURN,PROBE_RET,QUERY_CALL,QUERY_SLOT,QUERY_RETURN,RAW_QUERY
from ownership import witness,phase_ownership,TOKEN

REASON = 'Required genuine CRT GetVersionExA remains unresolved'


def positive(row,entry,phases,program,index,level):
    result = json.loads((row/'result.json').read_bytes())
    F.require(result['passed'] and result['scenario']==index and result['control']==0,'Exact ordinary native request')
    F.require(result['writer_complete'] and result['entry_executed'] and result['poisoned_retry']
        and not result['State_reseed_after_writer'] and not result['full_CRT'] and not result['whole_M4_complete'],
        'Bounded carried startup and poisoned retry')
    F.require(result['source_events']==len(entry.events) and result['writer_events']==97 and result['data_routes']==1,
              'Unchanged complete earlier source/writer ledgers')
    F.require((row/'heap-mode-lower-input.bin').read_bytes()==bytes(4096),
              'Explicit ordinary zero-owned lower-stack input; no original-capture claim')
    job = F.words((row/'heap-mode-job.bin').read_bytes(),44)
    F.require(job[:22]==(0,0x20001858,0x20001860,24,1,9,4,10,0,QUERY_CALL,QUERY_SLOT,
        1,0,1,1,1,1,1,1,1,0,1) and job[22]==job[23]
        and job[24:]==(FRAGMENT,ENTRY,SOURCE_CALL,SOURCE_RETURN,MODE_ENTRY,MODE_CALL,20,84,
            0x2000184c,PROBE,PROBE_CALL,PROBE_RETURN,QUERY_CALL,QUERY_SLOT,RAW_QUERY,QUERY_RETURN,1,1,86,2026),
        'Exact completed selector/probe/query source progress and closed owned heap')
    actual = witness(row,job)
    heap = predict(entry,program,actual['token'])
    phases.update(heap['phases'])
    final = stage(heap['state'],heap['fx'],heap['cpu'],heap['memory'])
    phases['entry-after-fault'],phases['retry-after'] = final,dict(final)
    tags = {name.split('/')[1] for name in row.inventory if name.startswith(row.name+'/') and name.count('/')==1}
    F.require(tags==set(phases) and len(phases)==34,'Exact complete independent 34-checkpoint inventory')
    for tag,files in phases.items():
        files.update(phase_ownership(tag,actual))
        F.full_stage(row,tag,files,index==0 and tag.startswith(('heap-create-','heap-mode-')))
    evidence = OLD.evidence(entry)
    evidence['mainargs-job.bin'] = struct.pack('<20I',M.SLOT,M.RAW,*([0]*13),1,0,0,QUERY_CALL,QUERY_SLOT)
    evidence['mainargs-events.bin'],evidence['mainargs-accesses.bin'] = bytes(256),bytes(1280)
    for name,value in evidence.items():
        captured = (row/name).read_bytes()
        F.require((json.loads(captured) if name.endswith('.json') else captured)==value,'Exact carried prior evidence '+name)
    F.require((result['fault_reason'],result['fault_site'],result['fault_target'])==(1,QUERY_CALL,QUERY_SLOT),
              'Typed unresolved import at genuine version-query source CALL')
    for name in ('mainargs-reason.txt','heap-mode-reason.txt'):
        F.require((row/name).read_text().strip()==REASON,'First truthful bounded diagnostic '+name)
    for name,reason in (('initterm',entry.init_reason),('control',entry.control_reason),('matherr','')):
        F.require((row/(name+'-reason.txt')).read_text().strip()==reason,'Unchanged earlier reason '+name)
    for actor in ('writer','entry'):
        M.D.host((row/(actor+'-host-before.bin')).read_bytes(),(row/(actor+'-host-after.bin')).read_bytes())
    entry_job = (row/'entry-job.bin').read_bytes()
    F.require(len(entry_job)==40 and entry_job[32:]==bytes(8)
              and struct.unpack_from('<3I',entry_job,20)==(1,QUERY_CALL,QUERY_SLOT),
              'Real entry import fault without fixture callback')
    accesses = b''.join(struct.pack('<5I',*values) for values in heap['accesses'])
    F.require((row/'heap-mode-accesses.bin').read_bytes()==accesses+bytes(1280-len(accesses)),
              'Complete independent 24-access original-source ledger')
    returned = struct.pack('<5I',*heap['API_return_access'])
    F.require((row/'heap-mode-api-accesses.bin').read_bytes()==returned+bytes(160-len(returned)),
              'One distinct finite HeapCreate API-return read')
    events = [(1,FRAGMENT,0x20001860,0),(2,SOURCE_CALL,ENTRY,SOURCE_RETURN),
        (3,API_CALL,API_SLOT,RAW_API),(4,API_CALL,0x20001848,API_RETURN),
        (5,0x780039d8,0x78035000,TOKEN),(6,MODE_CALL,MODE_ENTRY,MODE_RETURN),
        (7,PROBE_CALL,PROBE,PROBE_RETURN),(8,PROBE_RET,PROBE_RETURN,0x20000620),
        (9,QUERY_CALL,QUERY_SLOT,RAW_QUERY)]
    event_bytes = b''.join(struct.pack('<4I',*values) for values in events)
    F.require((row/'heap-mode-events.bin').read_bytes()==event_bytes+bytes(256-len(event_bytes)),
              'Authentic five CALLs, API-return seam, publication and relocated probe RET')
    F.require(F.words((row/'heap-mode-scheduler.bin').read_bytes(),8)==heap['scheduler'],
              'Only EIP scheduled, no execution-time host guest-memory store')
    F.require(F.words((row/'heap-mode-undefined.bin').read_bytes(),8)==
        (ENTRY,API_RETURN,0x780058db,0x780058c5,0,0,0,0),'Four exact-site generated AF representatives')
    unused = {
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
        'heap-create-accesses.bin':bytes(640),'heap-create-api-accesses.bin':bytes(160),
        'heap-create-events.bin':bytes(128),'heap-create-undefined.bin':bytes(32),
        'heap-create-scheduler.bin':bytes(32),'heap-create-witness.bin':bytes(128),
    }
    for name,value in unused.items():
        F.require((row/name).read_bytes()==value,'Constructed but unused earlier/later service '+name)
    old_registry64 = struct.unpack('<18Q',(row/'heap-create-registry.bin').read_bytes())
    F.require(old_registry64[:1]==(1,) and old_registry64[1]!=0 and old_registry64[1]!=actual['registry_owner']
              and old_registry64[2:]==(1,*([0]*15)),
              'Unused distinct constructor-only heap-create host association, no acquired resource')
    for name in ('filename','commandline','parser','locale','heap','heap-create'):
        F.require((row/(name+'-reason.txt')).read_text().strip()=='','Unused service has no fabricated fault '+name)
    root_files = set(evidence)|set(unused)|{'heap-create-registry.bin','input.bin','writer-record.bin',
        'writer-host-before.bin','writer-host-after.bin','entry-host-before.bin','entry-host-after.bin',
        'entry-job.bin','result.json','matherr-reason.txt','control-reason.txt','initterm-reason.txt',
        'mainargs-reason.txt','filename-reason.txt','commandline-reason.txt','parser-reason.txt',
        'locale-reason.txt','heap-reason.txt','heap-create-reason.txt','heap-mode-reason.txt',
        'heap-mode-job.bin','heap-mode-events.bin','heap-mode-accesses.bin','heap-mode-api-accesses.bin',
        'heap-mode-scheduler.bin','heap-mode-undefined.bin','heap-mode-witness.bin','heap-mode-registry.bin',
        'heap-mode-lower-input.bin','heap-mode-create-api-before.bin','heap-mode-create-api-after.bin',
        'heap-mode-destroy-api-before.bin','heap-mode-destroy-api-after.bin'}
    F.require(row.inventory[row.name]==root_files,'Exact complete ordinary root evidence inventory')
    F.require(struct.unpack_from('<I',heap['memory'][0x78035000],4)[0]==0,
              'Heap mode global unproduced at first version-query CALL')
    return dict(index=index,level=level,source_PCs=39,source_accesses=24,actual_source_CALLs=5,
        distinct_API_return_reads=1,genuine_probe_RET=1,host_guest_memory_stores=0,checkpoints=34,
        whole_State=3504,whole_FX=512,whole_Runtime_CPU=40,whole_pages=20,
        full_host_handle=actual['full_host_handle'],guest_token=TOKEN,actual_HeapCreate=True,
        actual_owned_HeapDestroy=True,owned_host_handle_closed=True,GetVersionExA_executed=False,
        original_lower_stack_captured=False,original_guard_stack_growth=False,
        heap_mode_selected=False,heap_initialized=False,heap_initializer_RET=False,root_full_causal_model=False)
