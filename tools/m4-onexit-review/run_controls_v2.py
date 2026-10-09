"""Execute fresh compiled controls and validate their direct canonical records."""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-onexit-review'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
sys.path.insert(0,str(ROOT/'tools/m4-crt-locale-batch-review'))
from stages import run_stage,verify_stage
from manifests import verify_manifest

def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(ok,why):
    if not ok:raise ValueError(why)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v

def main(buildpath,digest,name):
    out=BASE/name;need(not out.exists(),'Fresh independent actual execution');out.mkdir(parents=True)
    pins={};rows=[];passed=False;metrics=dict(actual_attempts=0,ordinary_sequences=0,causal_faults=0,retry_refusals=0,
                                           rich_hardware_pairs=0,physical_API_proofs=0,actual_native_moves=0,partial_transfer_faults=0)
    def pin(p,h=None):
        p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Current exact physical dependency '+str(p));pins[str(p)]=v;return p
    try:
        b=json.loads(pin(buildpath,digest).read_bytes());need(b['passed'],'Frozen successful control compilation')
        for p,h in json.loads(pin(Path(buildpath).parent/'pins.json').read_bytes())['files'].items():pin(p,h)
        game=pin(ROOT/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf')
        numeric=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a')
        crt=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
        pin(__file__)
        d=module('strict_onexit_control',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'))
        e=module('physical_onexit_exports',pin(ROOT/'tools/m4-crt-locale-batch-review/check_v2.py'))
        e.FORWARDS.update(HeapSize='RtlSizeHeap',HeapReAlloc='RtlReAllocateHeap')
        for level in ('O0','O2'):
            worker=pin(b['workers'][level]['path'],b['workers'][level]['sha256']);capture=out/level;stage=out/(level+'-stage')
            st=run_stage(list(map(str,(worker,game,numeric,crt,capture))),stage,timeout_seconds=180,
                         required_outputs=[capture/'transport.json'],inputs=list(pins))
            pin(stage/'stage.json');verify_stage(stage,sha(stage/'stage.json'));need(st['passed'],'Actual current independent worker completion')
            archive=d.DirectSet(capture/'transport.json',pin)
            try:
                header=archive.words('header.bin',6);need(header[:3]==(1,14,28) and header[3]==9968 and header[5]==32,
                                                      'Exact current independent record schema')
                for selected in range(14):
                    record=[]
                    for attempt in ('first','retry'):
                        raw=archive.data(f'case-{selected}/{attempt}.bin');need(len(raw)==header[3],'Complete direct control record')
                        tags=struct.unpack_from('<32Q',raw);before=struct.unpack_from('<32Q',raw,256);after=struct.unpack_from('<32Q',raw,512)
                        need(tags[:3]==(1,selected,int(attempt=='retry')) and tags[13]==0x4D573354 and tags[14]==1,
                             'Actual identified attempt, preserved LastError and successful cleanup')
                        need(not any(after[n] for n in (10,11,15)) and after[4]==1,
                             'No live private allocation/CS/heap after actual cleanup; tag14 independently checks actual live heap handle')
                        a,z=raw[8880:9424],raw[9424:9968]
                        need(a[512:540]==z[512:540] and a[:5]==z[:5] and a[24:28]==z[24:28],
                             'Full legacy ENV28 and strict loaded CW/SW/FTW/MXCSR preservation')
                        need(struct.unpack_from('<H',a)[0]==0xA7F and struct.unpack_from('<I',a,24)[0]==0x5FA5
                             and a[4] and any(a[524:540]),'Actually loaded nontrivial independent hardware domain')
                        for index in range(8):need(a[32+16*index:42+16*index]==z[32+16*index:42+16*index],'Each strict physical raw80 x87 register')
                        need(a[256:416]==z[256:416] and not((tags[20]^tags[21])&0x400),'Nonvolatile native XMM6..15 and DF preservation')
                        if attempt=='retry':
                            need(not tags[3] and tags[5] and tags[19] and tags[9]==tags[10] and tags[11]==tags[4],
                                 'Retry refused without more selected root routes')
                            need(before==after and raw[768:4272]==raw[4272:7776] and raw[7776:8288]==raw[8288:8800]
                                 and raw[8800:8840]==raw[8840:8880],'Retry preserves complete machine and owner counters')
                            metrics['retry_refusals']+=1
                        elif not selected:
                            need(tags[3]==1 and tags[4]==tags[12]==54 and tags[7]==0 and tags[8]==1 and after[14]>=1,
                                 'Connected54 ordinary sequence plus actual growth and one foreign-thread refusal')
                            metrics['ordinary_sequences']+=1
                        else:
                            need(not tags[3] and tags[5] and tags[19] and tags[7]==1 and tags[12]==tags[4],
                                 'One actual causal refusal retains completed source prefix')
                            metrics['causal_faults']+=1
                        metrics['actual_attempts']+=1;metrics['rich_hardware_pairs']+=1;record.append(tags)
                    need(record[0][10]==record[1][10] and record[0][4]==record[1][4], 'Retry root count and routes retain the exact prior prefix')
                    prefix=f'case-{selected}/first-cleaned/'
                    summary=archive.words(prefix+'locale-summary.bin',32)
                    need(summary[23]==1 and summary[14]==summary[15]==summary[30]==0,
                         'Independent dumped finished owner has no live allocation, CS or native heap')
                    allocation_raw=archive.data(prefix+'locale-allocations.bin')
                    section_raw=archive.data(prefix+'locale-critical-sections.bin')
                    need(len(allocation_raw)%128==0 and len(section_raw)%128==0,
                         'Complete dumped actual allocation and critical-section rows')
                    allocations=list(struct.iter_unpack('<16Q',allocation_raw))
                    sections=list(struct.iter_unpack('<16Q',section_raw))
                    need(all(a[8]==0 and a[9]==0 and (a[10] or a[11]) for a in allocations),
                         'Every actually acquired allocation is released and its guest mapping removed')
                    need(all(s[5]==0 and s[8] and s[9] and s[7]==1 for s in sections),
                         'Every actually initialized private critical section is unlocked and deleted once')
                    heap=archive.words(prefix+'heap-create-witness.bin',16,'Q')
                    lifecycle=archive.words(prefix+'heap-create-registry.bin',18,'Q')
                    need(heap[:6]==(1,0,1,0,4096,0) and heap[6] and heap[6]!=0x48450001
                         and heap[7]==0x48450001 and heap[11]==heap[6],
                         'Actual uninjected HeapCreate request and distinct full-width private handle')
                    need(lifecycle[0]==1 and lifecycle[1] and lifecycle[2:11]==(1,0x48450001,heap[6],1,1,0,1,1,1)
                         and lifecycle[12:]==(1,0,0,1,heap[6],0),
                         'Exactly one matching successful HeapDestroy, no duplicate/skip/rollback/foreign lookup')
                    for service,requested in (('create','HeapCreate'),('query','GetVersionExA'),('destroy','HeapDestroy')):
                        stem=prefix+'heap-'+service+'-api-'
                        actual_before=e.identity(archive,stem+'before',pin)
                        actual_after=e.identity(archive,stem+'after',pin)
                        need(actual_before==actual_after,'Immutable actual bootstrap/lifecycle API identity')
                        rva,forward=e.export(Path(actual_before[2]),requested)
                        need(not forward and actual_before[1]+rva==actual_before[0],
                             'Physical direct owning export matches the actual full-width API target')
                        metrics['physical_API_proofs']+=1
                    if selected==9:
                        pressure=archive.data('case-9/first-pressure.bin');need(len(pressure)==256*96,'Exactly256 genuine bounded research pressure blocks')
                        pressure_rows=list(struct.iter_unpack('<12Q',pressure));native_owned={a[7] for a in allocations}
                        need(len({q[4] for q in pressure_rows})==256,'Every actual research pressure block is distinct')
                        for n,q in enumerate(pressure_rows):
                            need(q[:4]==(1,n,heap[6],128) and q[4] and q[4]%16==0 and q[4] not in native_owned
                                 and 128<=q[5]<=4096 and q[7]==1 and q[8]!=0 and not any(q[10:]),
                                 'Actual research pressure private heap/pointer/extent and one successful independent release')
                        for n,(requested,alias) in enumerate((('HeapAlloc','RtlAllocateHeap'),('HeapSize','RtlSizeHeap'),('HeapFree','HeapFree'))):
                            actual_before=e.identity(archive,f'case-9/first-pressure-{n}-before',pin)
                            actual_after=e.identity(archive,f'case-9/first-pressure-{n}-after',pin)
                            need(actual_before==actual_after,'Actual research pressure API identity stable')
                            rva,forward=e.export(Path(actual_before[2]),alias)
                            need(not forward and actual_before[1]+rva==actual_before[0],'Exact physical direct owning research API alias export')
                            named=pin(Path('C:/Windows/System32/kernel32.dll'));named_rva,named_forward=e.export(named,requested)
                            if requested!='HeapFree':need(named_forward=='NTDLL.'+alias,'Exact physical research allocator forwarder')
                            else:need(not named_forward,'Exact physical research free direct named export')
                            metrics['physical_API_proofs']+=1
                    changed_API_records=[]
                    for index in range(summary[18]):
                        stem=prefix+f'locale-api-{index}';words=archive.words(stem+'-witness.bin',32,'Q')
                        if not words[31] and words[2] in (0x780015B5,0x78011C27):changed_API_records.append(words)
                        if not words[14]:continue
                        proof=archive.data(stem+'-export-before.bin');requested=proof[48:80].split(b'\0',1)[0].decode('ascii')
                        api_identity_before=e.identity(archive,stem+'-identity-before',pin)
                        api_identity_after=e.identity(archive,stem+'-identity-after',pin)
                        need(api_identity_before==api_identity_after and archive.data(stem+'-export-after.bin')==proof,'Actual typed API identity/forwarder stable')
                        e.export_proof(proof,api_identity_before,requested,pin);metrics['physical_API_proofs']+=1
                    need(changed_API_records,'Actual changed provider API records exist in every scenario')
                    if selected==9:need(any(archive.words(prefix+f'registry-growth-{n}-witness.bin',32,'Q')[18] for n in range(after[14])),'Stale alias control occurs only after genuine physical HeapReAlloc movement')
                    last_changed=changed_API_records[-1]
                    if selected in (1,2,3,4,9,10,12,13):
                        need(last_changed[14]==last_changed[15]==0,
                             'Causal bad input/identity/permission ownership case refuses before the actual targeted API')
                    elif selected==5:
                        need(last_changed[2]==0x780015B5 and last_changed[14]==last_changed[15]==1,
                             'Append permission fault follows a genuinely completed HeapSize stdcall')
                    elif selected in (6,7):
                        need(last_changed[2]==0x78011C27 and last_changed[14]==1 and last_changed[15]==0,
                             'Actual realloc completed before causal alias/transfer refusal; source stdcall remains uncommitted')
                    elif selected==8:
                        need(last_changed[2]==0x78011C27 and last_changed[14]==last_changed[15]==1,
                             'Observer fault follows the genuine realloc stdcall completion')
                    for index in range(after[14]):
                        growth=archive.words(prefix+f'registry-growth-{index}-witness.bin',32,'Q')
                        if growth[18]:metrics['actual_native_moves']+=1
                        if selected==7:
                            need(growth[11] and 0<growth[20]<growth[16] and growth[21], 'Real successful realloc followed by partial committed guest transfer refusal')
                            metrics['partial_transfer_faults']+=1
                need(archive.data('COMPLETE.txt')==b'Independent connected54 onexit controls passed\n','Direct worker semantic completion')
                rows.append(dict(level=level,stage=str(stage/'stage.json'),stage_sha256=sha(stage/'stage.json'),
                                 capture=str(capture/'transport.json'),capture_sha256=sha(capture/'transport.json'),
                                 logical_records=len(archive.entries),elapsed_seconds=st['elapsed_seconds']))
            finally:archive.close()
        passed=True
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        report=dict(passed=passed,schema='mw34-onexit-independent-compiled-controls-v2',build=str(buildpath),build_sha256=digest,
                    levels=rows,metrics=metrics,files=pins,native_executed=True,source_bodies_modified=False,
                    API_response_injection=False,actual_API_null_failure_claimed=False,callback_execution=False,
                    research_pressure_scope='Scenario9 only:256 genuine128-byte allocations on exact live private heap, no guest alias/source API changes; each independently released and physical API identity authenticated',
                    initializer_credit=False,whole_M4_complete=False,physical_closure=verify_manifest(pins))
        (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pins[str(out/'report.json')]=sha(out/'report.json')
        (out/'pins.json').write_text(json.dumps(dict(files=pins),indent=2)+'\n')
        print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'))))

if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
