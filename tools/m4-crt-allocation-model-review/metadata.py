"""Independent phase metadata from finite row witnesses and source ledgers."""
import struct
import predict_v3 as P
need=P.need
TERMINAL={'heap-create-after','entry-after-fault','retry-after'}
HEAP_COUNTS={
 'heap-create-before':(0,0),'heap-create-projected':(0,0),'heap-create-provider-before':(2,0),
 'heap-create-api-before':(8,0),'heap-create-api-return-before':(8,0),'heap-create-api-returned':(8,1),
 'heap-create-published':(9,1),'heap-create-mode-before':(10,1),'heap-mode-probe-before':(12,1),
 'heap-mode-probe-after':(19,1),'heap-mode-query-before':(24,1),
 'heap-version-query-native-before':(24,1),'heap-version-query-native-after':(24,1),
 'heap-version-query-output-after':(24,1),'heap-version-query-return-before':(24,1),
 'heap-version-query-returned':(24,2),'heap-version-selector-return-after':(31,2),
 'heap-return-mode-store-before':(31,2),'heap-return-mode-store-after':(32,2),
 'heap-return-initializer-return-before':(34,2),'heap-return-initializer-return-after':(35,2)}


def packed(rows,width,capacity):
    raw=b''.join(struct.pack('<'+str(width)+'I',*row) for row in rows)
    need(len(raw)<=capacity,'Complete bounded independent ledger')
    return raw+bytes(capacity-len(raw))


def phase(tag,expected,initial,chain,actual,old_ownership):
    known=tag in HEAP_COUNTS or tag.startswith('allocation-') or tag in TERMINAL
    counts=chain['counts'].get(tag,HEAP_COUNTS.get(tag,(0,0)))
    source_count,API_count=counts
    oldtag='heap-return-initializer-return-after' if tag.startswith('allocation-') else tag
    oldactual=dict(registry_owner=actual['owner'],full_host_handle=actual['handle'],witness_words=actual['heap_witness'],
        registry_words=actual['heap_registry'],query_words=actual['query'],query_input=actual['query_input'],
        query_output=actual['query_output'],selector_returned=True)
    result=old_ownership.phase_ownership(oldtag,oldactual)
    result.update(old_ownership.phase_query(oldtag,oldactual,initial))
    result.update(old_ownership.phase_progress(oldtag,oldactual))
    API_reads=[initial['API_return_access'],initial['query_return_access'],*chain['API_reads']]
    result['allocation-source-accesses.bin']=packed(chain['accesses'][:source_count],5,2560)
    result['allocation-api-return-accesses.bin']=packed(API_reads[:API_count],5,160)
    phase_number=0;caller=malloc=client=freed=null=batch=0;plan_index=plan_size=start=0
    external_count=projection_count=0;extent=0;mapped=owned=allocated=free_called=free_success=pattern=0;guest=fullptr=0
    w=[0]*16;initial_bytes=pattern_bytes=backing=b''
    if tag.startswith('allocation-') or tag in TERMINAL:
        phase_number=1;caller=int(tag!='allocation-caller-before')
        if tag not in ('allocation-caller-before','allocation-caller-after'):
            extent=chain['extent'];phase_number=2;start=36;plan_size=len(chain['malloc']['accesses'])
            plan_index=source_count-start;external_count=2;projection_count=1
            allocated=int(tag not in ('allocation-malloc-before','allocation-malloc-seh-installed','allocation-native-before'))
            published=tag not in ('allocation-malloc-before','allocation-malloc-seh-installed','allocation-native-before','allocation-native-after')
            owned=allocated;mapped=int(published);guest=P.ALLOC if published else 0
            fullptr=actual['pointer'] if allocated else 0
            if allocated:
                w=list(actual['allocation_witness']);w[7:9]=[0,0];w[10:]=[0]*6
                initial_bytes=actual['initial'];backing=actual['initial']+bytes(4096-extent)
            malloc=int(tag not in ('allocation-malloc-before','allocation-malloc-seh-installed','allocation-native-before',
                'allocation-native-after','allocation-backing-published','allocation-api-return-before','allocation-api-returned','allocation-malloc-seh-restored'))
            if tag.startswith(('allocation-client-','allocation-free-','allocation-null-free-')) or tag=='allocation-batch-complete' or tag in TERMINAL:
                phase_number=3;plan_index=plan_size;client=int(tag!='allocation-client-before');pattern=client
                if client:pattern_bytes=chain['pattern'];backing=pattern_bytes+bytes(4096-extent)
            if tag.startswith(('allocation-free-','allocation-null-free-')) or tag=='allocation-batch-complete' or tag in TERMINAL:
                phase_number=4;external_count=4;projection_count=3;start=36+len(chain['malloc']['accesses']);plan_size=25
                plan_index=source_count-start
                free_called=int(tag not in ('allocation-free-before','allocation-free-seh-installed','allocation-free-native-before'))
                free_success=free_called;owned=int(not free_called);mapped=owned
                if free_called:w=list(actual['allocation_witness'])
                freed=int(tag not in ('allocation-free-before','allocation-free-seh-installed','allocation-free-native-before',
                    'allocation-free-native-after','allocation-free-api-returned','allocation-free-seh-restored'))
            if tag.startswith('allocation-null-free-') or tag=='allocation-batch-complete' or tag in TERMINAL:
                phase_number=5;external_count=6;projection_count=5;start=36+len(chain['malloc']['accesses'])+25;plan_size=18
                plan_index=source_count-start;null=int(tag not in ('allocation-null-free-before','allocation-null-free-seh-installed','allocation-null-free-seh-restored'))
                batch=int(tag=='allocation-batch-complete' or tag in TERMINAL)
    FS=struct.unpack_from('<I',expected['state.bin'],P.source.FSBASE)[0]
    FS0=struct.unpack('<I',expected['tib-0.bin'])[0]
    if known:
        registry=(1,actual['owner'],1,guest,fullptr,actual['request'],extent,4096 if mapped else 0,
                  allocated,owned,free_called,free_success,mapped,pattern,client,malloc,freed,0,0,0,
                  actual['handle'] if tag.startswith('allocation-') or tag in TERMINAL else 0,
                  fullptr,P.MALLOC_MARKER,P.FREE_MARKER)
        # This new allocator registry is a constructor snapshot throughout
        # the original heap phases. Its first explicit private refresh occurs
        # at allocation-caller-before; the separate heap W/R already records
        # live ownership earlier. No guest-machine seed comes from this cache.
        progress=(1,caller,malloc,client,freed,null,batch,actual['request'],extent,phase_number,
                  plan_index,plan_size,start,owned,mapped,FS0)
    else:registry=[0]*24;progress=[0]*16
    result.update({'allocation-registry.bin':struct.pack('<24Q',*registry),
        'allocation-witness.bin':struct.pack('<16Q',*w),'allocation-progress.bin':struct.pack('<16I',*progress),
        'allocation-external-accesses.bin':packed(chain['external_accesses'][:external_count],5,320),
        'allocation-external-projections.bin':packed(chain['external_projections'][:projection_count],8,256)})
    if known:
        result.update({'allocation-initial.bin':initial_bytes,'allocation-pattern.bin':pattern_bytes,'allocation-backing.bin':backing})
        measured=tag.startswith('allocation-') and tag not in ('allocation-caller-before','allocation-caller-after',
                    'allocation-malloc-before','allocation-malloc-seh-installed') or tag in TERMINAL
        allocated_proof=measured and tag!='allocation-native-before'
        freed_proof=tag in ('allocation-free-native-after','allocation-free-api-returned','allocation-free-seh-restored',
                    'allocation-free-returned','allocation-null-free-before','allocation-null-free-seh-installed',
                    'allocation-null-free-seh-restored','allocation-null-free-returned','allocation-batch-complete') or tag in TERMINAL
        for stem in ('alloc','free'):
            result['allocation-'+stem+'-export-before.bin']=actual['export_proofs'][stem] if measured else bytes(4624)
            result['allocation-'+stem+'-export-after.bin']=actual['export_proofs'][stem] if (allocated_proof if stem=='alloc' else freed_proof) else bytes(4624)
    return result,known,mapped
