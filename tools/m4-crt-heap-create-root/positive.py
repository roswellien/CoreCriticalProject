"""Compare ordinary full-machine rows to BEFORE and typed actual API witness."""
import json
import struct
from consumer import F, M, OLD
from before import stage
from prefix import predict, FRAGMENT, SOURCE_CALL, SOURCE_RETURN, ENTRY, API_CALL, API_SLOT, API_RETURN, RAW_API, MODE_CALL, MODE_ENTRY, MODE_RETURN
from ownership import witness, phase_ownership, TOKEN

REASON='Required genuine CRT heap mode selector remains unresolved'


def positive(row,entry,phases,program,index,level):
    result=json.loads((row/'result.json').read_bytes())
    F.require(result['passed'] and result['scenario']==index and result['control']==0,'Exact ordinary native request')
    F.require(result['writer_complete'] and result['entry_executed'] and result['poisoned_retry'] and
        not result['State_reseed_after_writer'] and not result['full_CRT'] and not result['whole_M4_complete'],
        'Bounded carried startup execution and poisoned retry')
    F.require(result['source_events']==len(entry.events) and result['writer_events']==97 and result['data_routes']==1,
        'Complete prior source and writer execution ledgers')
    job=F.words((row/'heap-create-job.bin').read_bytes(),32)
    F.require(job[:22]==(0,0x20001858,0x20001860,10,1,6,2,10,0,MODE_CALL,MODE_ENTRY,
        1,0,1,1,1,1,1,1,1,0,1) and job[22]==job[23] and
        job[24:]==(FRAGMENT,ENTRY,SOURCE_CALL,SOURCE_RETURN,MODE_ENTRY,MODE_CALL,18,84),
        'Exact completed source/API/cleanup job and terminal fault')
    actual=witness(row,job)
    heap=predict(entry,program,actual['token'])
    phases.update(heap['phases'])
    final=stage(heap['state'],heap['fx'],heap['cpu'],heap['memory'])
    phases['entry-after-fault']=final
    phases['retry-after']=dict(final)
    tags={name.split('/')[1] for name in row.inventory if name.startswith(row.name+'/') and name.count('/')==1}
    F.require(tags==set(phases) and len(phases)==31,'Exact independently derived complete checkpoint inventory')
    for tag,files in phases.items():
        files.update(phase_ownership(tag,actual))
        F.full_stage(row,tag,files,index==0 and tag.startswith('heap-create-'))
    evidence=OLD.evidence(entry)
    evidence['mainargs-job.bin']=struct.pack('<20I',M.SLOT,M.RAW,*([0]*13),1,0,0,MODE_CALL,MODE_ENTRY)
    evidence['mainargs-events.bin']=bytes(256)
    evidence['mainargs-accesses.bin']=bytes(1280)
    for name,value in evidence.items():
        captured=(row/name).read_bytes()
        F.require((json.loads(captured) if name.endswith('.json') else captured)==value,'Exact carried prior evidence '+name)
    F.require((result['fault_reason'],result['fault_site'],result['fault_target'])==(0,MODE_CALL,MODE_ENTRY),
        'Typed unresolved translation at genuine mode-selector CALL')
    for name in ('mainargs-reason.txt','heap-create-reason.txt'):
        F.require((row/name).read_text().strip()==REASON,'First bounded source diagnostic '+name)
    for name,reason in (('initterm',entry.init_reason),('control',entry.control_reason),('matherr','')):
        F.require((row/(name+'-reason.txt')).read_text().strip()==reason,'Unchanged prior reason '+name)
    for actor in ('writer','entry'):
        M.D.host((row/(actor+'-host-before.bin')).read_bytes(),(row/(actor+'-host-after.bin')).read_bytes())
    entry_job=(row/'entry-job.bin').read_bytes()
    F.require(len(entry_job)==40 and entry_job[32:]==bytes(8) and struct.unpack_from('<3I',entry_job,20)==(0,MODE_CALL,MODE_ENTRY),
        'Real entry fault boundary without compiled fixture callback')
    accesses=b''.join(struct.pack('<5I',*values) for values in heap['accesses'])
    F.require((row/'heap-create-accesses.bin').read_bytes()==accesses+bytes(640-len(accesses)),
        'Complete independent ten-access original-source ledger')
    returned=struct.pack('<5I',*heap['API_return_access'])
    F.require((row/'heap-create-api-accesses.bin').read_bytes()==returned+bytes(160-len(returned)),
        'Distinct checked finite-API-return read ledger')
    events=[(1,FRAGMENT,0x20001860,0),(2,SOURCE_CALL,ENTRY,SOURCE_RETURN),
        (3,API_CALL,API_SLOT,RAW_API),(4,API_CALL,0x20001848,API_RETURN),
        (5,0x780039d8,0x78035000,TOKEN),(6,MODE_CALL,MODE_ENTRY,MODE_RETURN)]
    event_bytes=b''.join(struct.pack('<4I',*values) for values in events)
    F.require((row/'heap-create-events.bin').read_bytes()==event_bytes+bytes(128-len(event_bytes)),
        'Host projection, source CALLs, distinct API return and source publication events')
    F.require(F.words((row/'heap-create-scheduler.bin').read_bytes(),8)==heap['scheduler'],
        'Only carried State EIP scheduled; no host guest-memory store')
    F.require(F.words((row/'heap-create-undefined.bin').read_bytes(),8)==(ENTRY,API_RETURN,0,0,0,0,0,0),
        'Two exact source-site generated AF representatives')
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
    }
    for name,value in unused.items():
        F.require((row/name).read_bytes()==value,'Constructed but unused earlier service '+name)
    for name in ('filename','commandline','parser','locale','heap'):
        F.require((row/(name+'-reason.txt')).read_text().strip()=='','Unused service has no fabricated fault '+name)
    root_files=set(evidence)|set(unused)|{'input.bin','writer-record.bin','writer-host-before.bin','writer-host-after.bin',
        'entry-host-before.bin','entry-host-after.bin','entry-job.bin','result.json','matherr-reason.txt','control-reason.txt',
        'initterm-reason.txt','mainargs-reason.txt','filename-reason.txt','commandline-reason.txt','parser-reason.txt',
        'locale-reason.txt','heap-reason.txt','heap-create-reason.txt','heap-create-job.bin','heap-create-events.bin',
        'heap-create-accesses.bin','heap-create-api-accesses.bin','heap-create-scheduler.bin','heap-create-undefined.bin',
        'heap-create-witness.bin','heap-create-registry.bin','heap-create-api-before.bin','heap-create-api-after.bin',
        'heap-destroy-api-before.bin','heap-destroy-api-after.bin'}
    F.require(row.inventory[row.name]==root_files,'Exact complete ordinary root evidence inventory')
    F.require(struct.unpack_from('<I',heap['memory'][0x78035000],4)[0]==0,
        'Mode remains source-file identity zero, no source mode publication')
    return dict(index=index,level=level,source_PCs=13,source_accesses=10,actual_source_CALLs=3,
        distinct_API_return_reads=1,host_guest_memory_stores=0,checkpoints=31,
        whole_State=3504,whole_FX=512,whole_Runtime_CPU=40,whole_pages=18,
        full_host_handle=actual['full_host_handle'],guest_token=TOKEN,actual_HeapCreate=True,
        actual_owned_HeapDestroy=True,owned_host_handle_closed=True,
        guest_handle_source_published=True,heap_mode_selected=False,heap_initialized=False,
        original_x86_API_implementation_equivalence=False,root_full_causal_model=False)
