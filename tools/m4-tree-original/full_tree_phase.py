"""Actual full-schedule tree observations; source effects remain a separate gate."""
import collections,hashlib,json,struct
def words(data,offset=0,count=1):return struct.unpack_from('<'+'I'*count,data,offset)
def observe(records,data,seq,phase,owners,geometry,snapshot_rows,counts,page,tid,targets,read,root):
    def need(v,m):
        if not v:raise ValueError(m)
    before=page(data,0x60b000);after=page(data,0x60b000,True)
    need(words(before,0x314,2)==(0,0),'Authentic complete-schedule tree shared header/counter BEFORE zero')
    head,counter=words(after,0x314,2);sentinel=words(after,0x2fc)[0]
    need(head and sentinel and head!=sentinel and counter==1 and words(after,0x304)[0]==5,'Actual measured tree header/sentinel/count/size endpoint')
    api=records.data(f'phase/{seq}/{phase}/api-ledger.bin');api_count=words(records.data(f'phase/{seq}/{phase}/api-count.bin'))[0]
    need(len(api)==api_count*104,'Complete actual allocation/API ledger')
    occurrences=collections.Counter();new=[]
    # Bounds come from compiled observer storage; all per-site invocations are
    # discovered from actual retained allocation metadata, never manufactured.
    for index in range(len(owners),64):
        name=f'phase/{seq}/{phase}/lockit-allocation/{index}/meta.bin'
        if name not in records.entries:break
        meta=words(records.data(name),0,9)
        need(meta[:3]==(1,index,0x4b7f70) and meta[3] in (0x4ba306,0x4ba33c,0x4bab32) and meta[4]==24 and 24<=meta[8]<=512,'Actual repeated original source allocation identity and complete capacity')
        ledger=words(api,meta[6]*104,26)
        need(meta[6]<api_count and ledger[24]==0 and ledger[10]==meta[7] and ledger[4]+104==meta[5] and ledger[25]==0x78001385 and ledger[22]==32,'Actual MFC24/CRT rounded32 request and live returned API backing')
        initial=records.data(f'phase/{seq}/{phase}/api-initial/{meta[6]}/bytes.bin');owned=records.data(f'phase/{seq}/{phase}/lockit-allocation/{index}/bytes.bin')
        need(words(records.data(f'phase/{seq}/{phase}/api-initial/{meta[6]}/size.bin'))[0]==len(initial)==len(owned)==meta[8] and owned[24:]==initial[24:],'Whole actual initial/final capacity and untouched eight-byte tail')
        occurrence=occurrences[meta[3]];occurrences[meta[3]]+=1
        if meta[3]==0x4ba306:need(meta[7]==head,'Actual conditional header owner publication')
        elif meta[3]==0x4ba33c:need(meta[7]==sentinel,'Actual sentinel owner publication')
        row=dict(sequence=seq,phase=phase,root=0x4b7f70,index=index,generation=index+1,CALL_pc=meta[3],site_invocation=occurrence,requested=24,actual_API_rounded_request=32,pointer=meta[7],capacity=meta[8],source_frame=meta[5],API_index=meta[6],initial_hex=initial.hex(),actual_final_hex=owned.hex())
        geometry.append(row);owners.append((meta,owned));new.append(row)
        counts['owners']+=1;counts['actual_initial_allocations']+=1
    need(len(new)==7 and dict(occurrences)=={0x4ba306:1,0x4ba33c:1,0x4bab32:5},'Actual full sequence allocation multiplicities agree with independently measured prefix domain')
    pointers={r['pointer'] for r in new};need(len(pointers)==7,'Seven distinct actual live owner identities')
    # Validate the actual pointer graph as an observation, without making this
    # structural check stand in for literal source byteflow equivalence.
    for r in new:
        node=bytes.fromhex(r['actual_final_hex']);left,parent,right=words(node,0,3)
        need(all(value==0 or value in pointers for value in (left,parent,right)),'Every actual complete tree link names a live measured owner')
    raw=records.data(f'phase/{seq}/{phase}/lockit-snapshots.bin');count=words(records.data(f'phase/{seq}/{phase}/lockit-count.bin'))[0]
    need(len(raw)==count*12988 and count==78,'Actual full tree Lockit observation extent in measured domain')
    expected_pc={0:0x7810a290,1:targets[0x78146198],2:0x7810a311,3:0x7810a350,4:targets[0x78146184],5:0x7810a364}
    depth=0;maximum=0;open_pairs=[];calls=[];last_kind=None;pending=None
    for k in range(count):
        block=raw[k*12988:(k+1)*12988];w=words(block,0,16);cpu=words(block,64,10);frame=words(block,644,8);cs=words(block,676,6);kind=w[3]
        need(w[:3]==(1,k,0x4b7f70) and w[6:9]==(tid,2,0x60b2f8) and w[13:15]==(0x7810a290,0x7810a350) and kind in expected_pc and cpu[9]==expected_pc[kind],'Actual true loaded provider boundary/current domain and owning game imports')
        if kind in (0,3):
            need(last_kind in (None,2,5),'Actual complete provider call triplets')
            pending=dict(entry=k,kind=kind,CPU=list(cpu),frame=list(frame),FX=block[104:616],ENV=block[616:644],scratch=cpu[1])
            if kind==0:open_pairs.append(pending)
            else:need(open_pairs and open_pairs[-1]['scratch']==cpu[1],'Actual source scratch LIFO destructor owns the live constructor scratch')
        elif kind in (1,4):
            need(pending and last_kind==(0 if kind==1 else 3) and pending['kind']==(0 if kind==1 else 3),'Actual named API belongs to current provider entry')
            need(cpu[4]==pending['CPU'][4]-(16 if kind==1 else 8) and frame[:2]==(0x7810a311 if kind==1 else 0x7810a364,0x78145640),'Actual source API return word, complete CALL frame and CS argument')
            counts['actual_API_frames']+=1
        else:
            need(pending and last_kind==(1 if kind==2 else 4),'Actual provider API-return follows authentic named API')
            need(cpu[4]==pending['CPU'][4]-(8 if kind==2 else 0) and block[104:616]==pending['FX'] and block[616:644]==pending['ENV'],'Actual bounded pre-epilogue/preRET frame and whole hardware FX/ENV preservation')
            if kind==2:depth+=1
            else:depth-=1;open_pairs.pop()
            pending=None
        need(0<=depth<=2 and cs==(0xffffffff,0xfffffffe if depth else 0xffffffff,depth,tid if depth else 0,0,0x020007d0),'Complete actual CS24 held/unheld recursion and source current thread')
        need(block[4796+0x640:4796+0x658]==block[676:700],'Whole actual provider data page joins complete CS24')
        maximum=max(maximum,depth);calls.append(dict(index=k,kind=kind,PC=cpu[9],CPU=list(cpu),frame=list(frame),CS=list(cs),depth=depth,FX_sha256=hashlib.sha256(block[104:616]).hexdigest(),ENV_hex=block[616:644].hex(),actual_postRET_observed=False));counts['Lockit_snapshots']+=1;last_kind=kind
    need(depth==0 and not open_pairs and pending is None,'Every genuine nested Lockit pair returned with balanced ownership')
    snapshot_rows.append(dict(sequence=seq,phase=phase,root=0x4b7f70,snapshots=calls,maximum_depth=maximum))
    static=read(root/'reports/m4-tree-source/recovery-r1/FS-frame-contracts.json');sites={r[f]:(r,kind) for r in static for kind,f in enumerate(('read','install','restore'))}
    fsraw=records.data(f'phase/{seq}/{phase}/fs-events.bin');fs_count=words(records.data(f'phase/{seq}/{phase}/fs-event-count.bin'))[0]
    need(len(fsraw)==fs_count*1216,'Actual full tree FS event extent');active={};invocations=[];ordinals=collections.Counter()
    for k in range(fs_count):
        block=fsraw[k*1216:(k+1)*1216];w=words(block,0,8)
        need(w[2] in sites,'Every actual tree FS operation has an exact physical static source site');contract,kind=sites[w[2]];before_cpu=words(block,32,10);after_cpu=words(block,72,10)
        need(w[:2]==(1,0x4b7f70) and w[3]==kind and block[136:648]==block[648:1160] and block[1160:1188]==block[1188:1216],'Actual FS source operation preserves whole hardware FX/ENV')
        entry=contract['entry']
        if kind==0:
            need(entry not in active and before_cpu[4]==after_cpu[4],'New actual normal source FS invocation')
            active[entry]=dict(entry=entry,invocation=ordinals[entry],read_event=k,entry_ESP=before_cpu[4]+8,previous=w[4]);ordinals[entry]+=1
        elif kind==1:
            need(entry in active and w[7]==1,'Actual source frame installed after genuine FS read');inv=active[entry];record=words(block,112,3)
            need(record[:2]==(inv['previous'],contract['handler']) and w[6]==inv['entry_ESP']-12==before_cpu[4]==w[5] and block[112:124]==block[124:136],'Actual complete12B frame/previous/handler and true FS publication')
            inv.update(install_event=k,record_address=w[6],installed_record_hex=block[112:124].hex())
        else:
            need(entry in active and 'install_event' in active[entry] and w[7]==1,'Actual source restored installed invocation');inv=active.pop(entry);record=words(block,112,3)
            need(w[4]==w[6]==inv['record_address'] and w[5]==inv['previous'] and record[:2]==(inv['previous'],contract['handler']) and block[112:124]==block[124:136],'Actual full12B record and genuine previous head restoration')
            inv.update(restore_event=k,restored_record_hex=block[112:124].hex());invocations.append(inv)
        counts['new_FS_records']+=1
    need(not active and len(invocations)==7 and fs_count==21,'Actual seven complete normal tree source FS invocations')
    geometry.append(dict(sequence=seq,phase=phase,root=0x4b7f70,FS_invocations=invocations,observed_tree_page_after_sha256=hashlib.sha256(after).hexdigest()))
    counts['tree_phases']=counts.get('tree_phases',0)+1;counts['tree_allocation_invocations']=counts.get('tree_allocation_invocations',0)+len(new)
