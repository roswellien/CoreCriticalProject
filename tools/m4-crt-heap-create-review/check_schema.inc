def need(value,why):
    if not value:raise ValueError(why)
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)
REQUESTS=[0]*6+list(range(121,133))+list(range(1,49))
PAGES=(0x78004000,0x78011000,0x7802c000,0x7802e000,0x7802f000,0x78030000,0x78037000,0x20001000,0x5bb000,0x736000,0x9a1000,0x7800b000,0x78039000,0x7803b000,0x5e0000,0x78001000,0x78003000,0x78035000)
PHASE_FILES=set('commandline-source.bin control-cold.bin control-hot.bin control-thunk.bin control-wrapper.bin crt-globals.bin entry-source.bin fx.bin initterm-provider.bin initterm-thunk.bin mainargs-builder.bin mainargs-provider.bin matherr-source.bin parser-source.bin runtime-cpu.bin state-cpu.bin state.bin tib-0.bin tib-24.bin tib-4.bin locale-stub.bin locale-setmbcp.bin locale-lock.bin heap-fragment.bin heap-provider.bin heap-create-witness.bin heap-create-registry.bin'.split())|{f'page-{p}.bin' for p in PAGES}
CASE_FILES=set('actual-filename-witness.bin calls.json carry-accesses.bin carry-actual-bytes.bin carry-consumer-accesses.bin carry-events.bin carry-status.bin entry-host-after.bin entry-host-before.bin filename-status.bin filename-witness.bin job-fault.bin mainargs-accesses.bin mainargs-events.bin mainargs-mode.bin mainargs-reason.txt mainargs-status.bin writer-host-after.bin writer-host-before.bin parser-accesses.bin parser-events.bin parser-undefined-sites.bin parser-status.bin heap-accesses.bin heap-events.bin heap-undefined-sites.bin heap-scheduler.bin heap-status.bin heap-api-accesses.bin heap-witness.bin heap-registry.bin heap-create-api-before.bin heap-create-api-after.bin heap-destroy-api-before.bin heap-destroy-api-after.bin independent-ownership.bin'.split())
BASE_PHASES=set('entry-projected matherr-before matherr-projected matherr-after control-before control-projected control-after control-provider-before control-provider-projected control-provider-after initterm-thunk-before initterm-thunk-projected initterm-thunk-after initterm-before initterm-projected initterm-after mainargs-before independent-after heap-create-before heap-create-projected heap-create-after'.split())
PROVIDER={0,*range(121,133),*range(3,11),24,34,35,*range(36,44),45,46,47}
API=PROVIDER-{34,35}
RETURN_BEFORE={0,121,*range(125,133),*range(6,11),39,42,43,45,46,47}
RETURNED=RETURN_BEFORE-{125,6,43}
PUBLISHED={0,121,127,*range(129,133),*range(8,11),39,42,45,46,47}
MODE={0,*range(130,133),*range(8,11),39,42,45}
ACTUAL={0,*range(122,133),*range(4,11),*range(36,44),45,46,47}
REGISTERED=ACTUAL-{122,123,4,36}
API_READ=RETURN_BEFORE-{43}
COUNTS={m:0 for m in REQUESTS}
COUNTS.update({0:10,2:1,17:1,33:2,34:7,35:8})
COUNTS.update({m:8 for m in {3,4,5,6,7,24,36,37,38,40,41,43,122,123,124,125,126,128}})
COUNTS.update({m:9 for m in {46,121,127,129}})
COUNTS.update({m:10 for m in {8,9,10,39,42,45,47,130,131,132}})

def api_identity(data,changed=False):
    need(len(data)==2184,'Exact packed actual API identity extent')
    q=struct.unpack('<7Q4I',data[:72]);address,named,owner,owner_named,base,size,allocation,state,kind,protect,allocation_protect=q
    if not any(data):return None
    need(address==(named^int(changed)) and named==owner_named and owner==allocation and base<=named<base+size and state==0x1000 and kind==0x1000000 and not(protect&0x101) and protect&0xf0,'Actual named executable committed image API identity')
    digest=data[72:136].decode('ascii');need(len(digest)==64 and all(c in '0123456789abcdef' for c in digest),'Actual physical module hash syntax')
    path=data[136:].decode('utf-16-le').split('\0',1)[0];need(Path(path).is_absolute() and sha_file(path)==digest,'Actual API loaded owner module physical hash')
    return (named,owner,path,digest)

def semantic_inventory(reader,records):
    need(reader.read_bytes('COMPLETE')==b'COMPLETE','Closed independent native completion marker')
    result=json.loads(reader.read_bytes('controls.json'),object_pairs_hook=unique_object)
    need(type(result['passed']) is bool and result['passed'] and type(result['scenarios']) is int and result['scenarios']==66 and result['original_executed'] is False and result['ordinary_game_launched'] is False and result['whole_M4_complete'] is False,'Exact independent fixture domain')
    need(type(result['checks']) is int and result['checks']>0 and type(result['malformed_token_denials']) is int and result['malformed_token_denials']==18,'Actual assertion and token denial domain')
    expected={'COMPLETE','controls.json'};created=destroyed=0
    for number,mode in enumerate(REQUESTS,1):
        case=f'case-{number}';need(struct.unpack('<I',reader.read_bytes(case+'/mainargs-mode.bin'))[0]==mode,'Fixed independent case order')
        s=struct.unpack('<32I',reader.read_bytes(case+'/heap-status.bin'))
        ev=6 if mode in MODE or mode==121 else 4 if mode in RETURNED else 3 if mode in API else 2 if mode in PROVIDER or mode==18 else 1
        undef=2 if mode in PUBLISHED or mode==128 else 1 if mode in PROVIDER or mode==19 else 0
        need(s[:10]==(mode,mode if mode>=121 else int(mode==13),0x20001858+int(mode==11),0x20001860+int(mode==12),COUNTS[mode],int(mode in API_READ),ev,undef,10,0),'Independent specified source/API progress and closed depth')
        need(s[12:23]==(1,0,1,int(mode in API),int(mode in ACTUAL),int(mode in REGISTERED),int(mode in RETURNED),int(mode in PUBLISHED),int(mode in MODE),int(mode==121),1),'Independent typed result and owned lifecycle')
        need(s[23]==s[24]==0,'Actual checkpoint-observed saved/restored caller LastError; explicit nonzero seam tested separately')
        need(s[25:]==(0x7800183c,0x780039bf,0x7800183e,0x78001843,0x780039d0,0x7802e0a8,0x780039d6),'Exact original source/API constants')
        sites=struct.unpack('<8I',reader.read_bytes(case+'/heap-undefined-sites.bin'))
        expected_sites=(0x780039bf,0x780039d6)+(0,)*6 if undef==2 else (0x780039bf,)+(0,)*7 if mode in PROVIDER else (0,)*8
        need(sites==expected_sites,'Exact narrowly scoped source-artifact AF ledger')
        scheduler=struct.unpack('<8I',reader.read_bytes(case+'/heap-scheduler.bin'));need(scheduler[0]==1 and scheduler[2:6]==(0x20001860,0x7800183c,0x20001860,0) and scheduler[6:]==(0x5bb514,0x20001860),'StatePC-only bootstrap has no guest store or CPU projection')
        own=struct.unpack('<8Q',reader.read_bytes(case+'/independent-ownership.bin'));called=int(mode in ACTUAL)
        need(own[1:]==(called,called,called,called,called,int(mode!=131),0) and bool(own[0])==bool(called),'Independent actual live/released heap membership, matching release and duplicate no-op checks')
        r=struct.unpack('<18Q',reader.read_bytes(case+'/heap-registry.bin'))
        need(r[:3]==(1,r[1],1) and r[1] and r[3:11]==(0x48450001 if mode in REGISTERED else 0,own[0],called,int(mode in REGISTERED),0,called,called,called),'Private full-HANDLE registry agrees with independent actual ownership counters')
        need(r[12]==called+int(mode==132) and r[13]==int(mode==132) and r[14]==int(mode==123) and r[15]==1 and r[16]==own[0] and r[17]==int(mode==40),'Exact rollback/cleanup skip/success input/lookup refusal')
        w=struct.unpack('<16Q',reader.read_bytes(case+'/heap-witness.bin'))
        if mode in ACTUAL or mode==121:
            need(w[:6]==(1,int(mode==121),called,0,4096,0) and w[6]==(own[0]^(0x100000000 if mode==36 else 0)) and w[7]==((0x48450001^int(mode==124)) if mode in REGISTERED else 0),'Typed actual API argument/full-HANDLE/token witness with declared fixture mutation')
            need(w[8]==w[10]==s[23] and w[11]==(own[0] if mode in REGISTERED else 0) and w[12:]==(0x20001848,0x780039d6,0x20001858,0x780039d6),'Actual API error reads and source stdcall return frame witness')
        else:need(not any(w),'No invented API witness before actual admission')
        identities={name:api_identity(reader.read_bytes(case+'/'+name+'.bin'),(mode==38 and name=='heap-create-api-after') or (mode==39 and name=='heap-destroy-api-before')) for name in ('heap-create-api-before','heap-create-api-after','heap-destroy-api-before','heap-destroy-api-after')}
        measured=bool(called or mode==121)
        need(bool(identities['heap-create-api-before'])==measured and bool(identities['heap-create-api-after'])==measured and bool(identities['heap-destroy-api-before'])==measured and bool(identities['heap-destroy-api-after'])==bool(called),'Actual API identities exist only for measured creation/release phases')
        need(identities['heap-create-api-before']==identities['heap-create-api-after'],'Matching actual create API owner identity after normalization of explicit metadata fixture')
        if called:need(identities['heap-destroy-api-before']==identities['heap-destroy-api-after'],'Matching actual release API owner identity after explicit metadata fixture normalization')
        phases=set(BASE_PHASES)
        for mode_set,name in ((PROVIDER,'heap-create-provider-before'),(API,'heap-create-api-before'),(RETURN_BEFORE,'heap-create-api-return-before'),(RETURNED,'heap-create-api-returned'),(PUBLISHED,'heap-create-published'),(MODE,'heap-create-mode-before'),({121},'heap-create-zero-before')):
            if mode in mode_set:phases.add(name)
        expected|={case+'/'+name for name in CASE_FILES}
        for phase in phases:expected|={case+'/'+phase+'/'+name for name in PHASE_FILES}
        created+=called;destroyed+=own[5]
    need(reader.names()==tuple(sorted(expected)),'Exact whole native case/phase/logical-file inventory')
    need(created==destroyed==35,'Exact actual native heap create and successful release count per optimization')
    T.validate_inventory(reader,records)
    return result,len(expected)
