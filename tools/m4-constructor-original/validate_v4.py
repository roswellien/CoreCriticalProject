"""Genuine constructor chronology observations; literal/native proof is separate.

This joins current source phase pages, API occurrences, normal MFC/getter
frames and complete list/owner byte records. No predicted count/capacity or
candidate AFTER state is used to supply an observation.
"""
from pathlib import Path
from collections import Counter
import hashlib,importlib.util,json,struct,sys,traceback

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-constructor-original'
CASES=((0,0x7f,0),(0,0x37f,7),(0,0xf7f,0),(1,0x47f,7),(1,0xa7f,0),(1,0xe7f,7))
NBYTES=189108
NEW={0x4103f0,0x410440,0x459b40}

def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def words(raw,offset=0,count=1):return struct.unpack_from('<'+str(count)+'I',raw,offset)

def main(build,build_sha,execution,preflight,preflight_sha,name):
    out=BASE/name
    if out.exists():raise ValueError('Fresh bounded validation required')
    out.mkdir(parents=True);files={};counts=Counter();passed=False;reader=None;export=None
    rows=[];occurrences=[];graph_rows=[];normal_rows=[];cleanup_rows=[];null_rows=[]
    def need(value,message):
        if not value:raise ValueError(message)
    def pin(path,digest=None):
        path=Path(path).resolve();actual=sha(path)
        need(digest is None or digest==actual,'Exact current physical input '+str(path))
        need(str(path)not in files or files[str(path)]==actual,'Stable current dependency')
        files[str(path)]=actual;return path
    def read(path,digest=None):return json.loads(pin(path,digest).read_text(encoding='utf-8-sig'))
    def load(path,name):
        spec=importlib.util.spec_from_file_location(name,pin(ROOT/path));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
    try:
        b=read(build,build_sha);need(b['passed']and(b['roots'],b['phases'],b['record_bytes'])==(37,222,356992),'Actual current bounded x86 build')
        for path,digest in read(Path(build).parent/'pins.json')['files'].items():pin(path,digest)
        prep=Path(b['preparation']);p=read(prep/'report.json',b['preparation_sha256']);contracts=read(prep/'contracts.json');order=read(prep/'selected-order.json')
        need(p['passed']and len(order)==37 and [order[i]['entry']for i in(13,14,15,36)]==[0x4103f0,0x410440,0x5ae3e4,0x459b40],'Exact selected chronology, third root at later slot')
        q=read(preflight,preflight_sha);need(q['passed']and q['files'].get(str(Path(build).resolve()))==build_sha and q['files'].get(str(Path(b['worker']).resolve()))==b['worker_sha256'],'Independent whole current linked worker attribution')
        for path,digest in q['files'].items():pin(path,digest)
        e=read(Path(execution)/'report.json');need(e['passed']and e['build_sha256']==build_sha and e['preflight_sha256']==preflight_sha,'Actual writer bound exact prelaunch')
        need(read(Path(execution)/'run/stage.json')['passed'],'Completed single genuine stage')
        D=load('tools/m4-crt-allocation-root/run_v2.py','constructor_direct_reader')
        E=load('tools/m4-joint-startup131/paired_exports.py','constructor_raw_export')
        reader=D.DirectSet(Path(execution)/'original/transport.json',pin)
        need(reader.data('COMPLETE.txt')==b'complete','Complete current original capture')
        header=reader.data('header.bin');need(header[:8]==b'MW4C037O'and words(header,8,6)==(1,6,37,222,43,356992),'Exact captured selected chronology ABI')
        pages=p['observed_pages'];need(len(pages)==43,'Whole fixed source page inventory');allpages=contracts['source_pages46'];need(len(allpages)==46 and len(set(allpages))==46,'Complete normal46 source pages')
        patches={row['return_PC']:row for row in read(prep/'constructor-hook-bindings.json')}
        chain=read(BASE/'entry-chain-r1/report.json',contracts['source_MFC_entry_chain_sha256']);need(chain['passed'],'Exact physical named export and finite affine source frame')
        provider_entries=words(reader.data('constructor/provider-entries.bin'),0,7)
        need(provider_entries==(1,chain['MFC_exports']['823']['target'],chain['MFC_exports']['825']['target'],chain['MFC_exports']['823']['target'],chain['MFC_exports']['825']['target'],chain['CRT_named_exports']['malloc']['target'],chain['CRT_named_exports']['free']['target']),'Actual loaded owning named MFC/CRT targets and whole observation')
        ctor_interface=read(ROOT/'reports/m4-constructor-source/preparation-r1/contracts.json')
        callback_byroot={row['entry']:row['callback']for row in ctor_interface['roots']}
        current131_callbacks={}
        callback_paths=[('m4-onexit-batch-recovery/recovery-r3/registration-roots.json',None),('m4-strings-source/recovery-r7/string-roots.json',None),('m4-mfc-source/recovery-r4/mfc-roots.json',None),('m4-fs-source/recovery-r3/fs-roots.json',None),('m4-container-source/recovery-r3/container-roots.json',None),('m4-next-source/recovery-r1/instruction-contracts.json','roots'),('m4-lockit-source/recovery-r1/Lockit-roots.json',None)]
        for relative,key in callback_paths:
            value=read(ROOT/'reports'/relative);value=value[key]if key else value
            for row in value:current131_callbacks[row['entry']]=row['registration']['callback']
        callback_byroot.update(current131_callbacks)
        need([callback_byroot[row['entry']]for row in order if row['entry']in callback_byroot]==contracts['callback_values'],'Physical callbacks in exact selected order')
        def phase_page(raw,address,side):
            start=(2276 if side=='BEFORE'else 178404)+pages.index(address)*4096
            return raw[start:start+4096]
        def normal(raw):
            need(len(raw)==NBYTES,'Whole packed normal snapshot')
            meta=words(raw,0,12);cpu=words(raw,48,10)
            return dict(metadata=list(meta),CPU=list(cpu),FX512_hex=raw[88:600].hex(),ENV28_hex=raw[600:628].hex(),frame64_hex=raw[628:692].hex(),pages_raw=raw[692:])
        def occ(raw):
            need(len(raw)==48,'Whole actual occurrence record');v=words(raw,0,12)
            need(v[0]==1 and v[1]>0 and v[4]in(0,3)and v[8]>0 and v[9]in(0,1),'Actual allocator invocation/revision identity')
            return v
        def graph(stem,member=False,phase_data=None,side=None):
            prefix='constructor-prerequisites/'+stem+'/';meta=words(reader.data(prefix+'meta.bin'),0,5 if member else 9)
            n=words(reader.data(prefix+'nodes-count.bin'))[0]
            need(meta[0]==1 and(meta[1],meta[3])==((0x605ae4,0x605ae8)if member else(0x603fdc,0x603fe0))and n<=256 and bool(n)==bool(meta[2]),'Bounded observed list header and count')
            if phase_data is not None:
                page=phase_page(phase_data,meta[1]&~4095,side)
                need(words(page,meta[1]&4095,2)==(meta[2],meta[4]),'Actual phase page and whole list header/counter join')
            nodes=[]
            for i in range(n):
                node=words(reader.data(prefix+f'node-{i}/meta.bin'),0,10);backing=reader.data(prefix+f'node-{i}/bytes.bin')
                need(node[:2]==(1,i)and node[2]and len(backing)==node[3]>=12 and words(backing,0,3)==node[7:10],'Complete observed node capacity/link/payload tuple')
                need(node[4]in live_byserial,'List node joins measured allocator occurrence');v=live_byserial[node[4]]
                need(v[9]and(v[7],v[8],v[2],v[3])==(node[2],node[3],node[5],node[6]),'Current live ownership role and source API identity')
                nodes.append(dict(metadata=list(node),whole_backing_hex=backing.hex()));counts['whole_list_node_endpoints']+=1
            if n:need(nodes[0]['metadata'][2]==meta[2]and all(v['metadata'][7]==nodes[(i+1)%n]['metadata'][2]and v['metadata'][8]==nodes[(i-1)%n]['metadata'][2]for i,v in enumerate(nodes)),'Complete current cyclic forward/backward source graph')
            item=dict(stem=stem,metadata=list(meta),nodes=nodes,observed_only=True)
            if not member:
                source=reader.data(prefix+'5F2000.bin');need(len(source)==4096 and words(source,0xa48)==(meta[6],),'Whole actual identifier page')
                item['whole_5F2000_hex']=source.hex();counts['whole_identifier_page_endpoints']+=1
            graph_rows.append(item);counts['list_graph_endpoints']+=1
        def whole_owners(stem):
            prefix='constructor-prerequisites/'+stem+'/'
            keys=sorted(k for k in reader.entries if k.startswith(prefix)and k.endswith('/meta.bin'))
            found=set();owners=[]
            for key in keys:
                v=occ(reader.data(key));need(v[1]not in found and v[1]in live_byserial and v==live_byserial[v[1]]and v[9],'Actual whole live backing joins carried occurrence identity')
                backing=reader.data(key.replace('/meta.bin','/bytes.bin'));need(len(backing)==v[8],'Whole measured live capacity without tail exclusion')
                found.add(v[1]);owners.append(dict(metadata=list(v),whole_backing_hex=backing.hex()));counts['whole_live_owner_endpoints']+=1
            need(found=={serial for serial,v in live_byserial.items()if v[9]},'Exhaustive complete current live backing inventory')
            graph_rows.append(dict(stem=stem,whole_live_owners=owners,observed_only=True))
        for sequence,(repeat,cw,top)in enumerate(CASES):
            carried=[];live_byserial={};pending_new={};source_new_serials=set()
            boot_stem=f'bootstrap/{sequence}'
            boot_ledger=reader.data(boot_stem+'/producer-api-ledger.bin')
            boot_count=words(reader.data(boot_stem+'/producer-api-count.bin'))[0]
            need(len(boot_ledger)==boot_count*104 and boot_count<=256,'Actual complete producer ledger')
            boot_occ=reader.data('constructor-prerequisites/'+boot_stem+'/occurrences.bin')
            need(len(boot_occ)%48==0,'Complete actual bootstrap owner occurrences')
            for i in range(0,len(boot_occ),48):
                v=occ(boot_occ[i:i+48]);need(v[1]not in live_byserial and v[2]==0xffffffff and v[3]<boot_count and v[4]==0,'Genuine pre-prefix allocator occurrence identity')
                api=words(boot_ledger,v[3]*104,26);initial=reader.data('constructor-prerequisites/'+boot_stem+f'/allocation-{v[1]}/initial.bin')
                need(v[4]==api[24]and v[5]==api[20]and v[6]==api[22]and v[7]==api[10]and v[8]==v[11]==len(initial)<=1024,'Bootstrap request/result and actual immediate whole capacity')
                live_byserial[v[1]]=v
                occurrences.append(dict(sequence=sequence,phase=0xffffffff,root=None,metadata=list(v),API26=list(api),whole_initial_hex=initial.hex()));counts['actual_whole_initial_HeapAlloc_backings']+=1
            # Each phase's exported complete occurrence vector is authoritative
            # only as an observation, and is rejoined to its own raw API ledger.
            for phase,item in enumerate(order):
                root=item['entry'];stem=f'phase/{sequence}/{phase}';raw=reader.data(stem+'.bin')
                need(len(raw)==356992 and words(raw,0,9)==(sequence,repeat,phase,item['slot'],root,cw,top,0,1),'Actual successful selected phase and hardware restoration tag')
                before=words(raw,36,10);after=words(raw,76,10)
                need(before[4]==0x20001800 and after[4]==0x20001804 and after[9]==0x410a80,'True initializer caller frame and return observation')
                hb,ha=raw[1140:1652],raw[1652:2164]
                need(hb[:5]==ha[:5]and hb[24:28]==ha[24:28]and raw[2220:2248]==raw[2248:2276]and all(hb[32+i*16:42+i*16]==ha[32+i*16:42+i*16]for i in range(8))and hb[160:288]==ha[160:288],'Architectural whole caller FP/control restoration')
                if root in callback_byroot:carried.append(callback_byroot[root])
                begin,nxt,capacity,mode=words(raw,356464,4)
                need(begin and nxt-begin==len(carried)*4<=capacity<=512 and mode==1 and words(raw,356480,len(carried))==tuple(carried),'Actual complete registration chronology and vector contents')
                counts['actual_callback_phase_relations']+=1
                for cell in(0x5bb4bc,0x5bb4c8):
                    a=words(phase_page(raw,0x5bb000,'BEFORE'),cell&4095)[0];z=words(phase_page(raw,0x5bb000,'AFTER'),cell&4095)[0]
                    need(a==z and a,'Full owning MFC import restored at source endpoints');counts['named_MFC_IAT_endpoint_pairs']+=1
                ledger=reader.data(stem+'/api-ledger.bin');api_count=words(reader.data(stem+'/api-count.bin'))[0]
                need(len(ledger)==api_count*104 and api_count<=256,'Whole bounded actual provider ledger')
                occ_key='constructor-prerequisites/'+stem+'/occurrences.bin';all_occ=reader.data(occ_key);need(len(all_occ)%48==0,'Complete carried owner occurrences')
                current={v[1]:v for v in(occ(all_occ[i:i+48])for i in range(0,len(all_occ),48))}
                need(len(current)==len(all_occ)//48,'Unique source allocation occurrence IDs')
                previous=live_byserial
                need(set(previous)<=set(current),'No missing carried allocation occurrence')
                new_by_api={v[3]:v for serial,v in current.items()if serial not in previous}
                need(len(new_by_api)==len(current)-len(previous),'Every new occurrence has one distinct actual API invocation')
                replay={serial:list(v)for serial,v in previous.items()};matched_new=set()
                for api_index in range(api_count):
                    api=words(ledger,api_index*104,26);kind=api[24];result=api[10]
                    if kind==0 and result:
                        need(api_index in new_by_api,'Every successful HeapAlloc produces a measured occurrence')
                        v=new_by_api[api_index]
                        need(v[2]==phase and v[4]==0 and(v[5],v[6],v[7],v[10])==(api[20],api[22],result,0),'Actual new allocation metadata/request/result')
                        need(not any(x[9]and(x[5],x[7])==(v[5],v[7])for x in replay.values()),'No already-live heap/address allocation alias')
                        replay[v[1]]=list(v);replay[v[1]][9]=1;matched_new.add(v[1])
                    elif kind in(1,3)and result:
                        candidates=[serial for serial,v in replay.items()if v[9]and(v[5],v[7])==(api[20],api[22])]
                        need(len(candidates)==1,'Successful free/reallocation joins one current live heap/address occurrence')
                        predecessor=candidates[0];replay[predecessor][9]=0
                        if kind==3:
                            need(api_index in new_by_api,'Successful reallocation has a measured successor revision');v=new_by_api[api_index]
                            need(v[2]==phase and v[4]==3 and(v[5],v[6],v[7],v[10],v[11])==(api[20],api[23],result,predecessor,0),'Exact real reallocation request/result/predecessor')
                            need(not any(x[9]and(x[5],x[7])==(v[5],v[7])for x in replay.values()),'Fresh live reallocation successor heap/address')
                            replay[v[1]]=list(v);replay[v[1]][9]=1;matched_new.add(v[1])
                        counts['actual_API_joined_ownership_retirements']+=1
                need(matched_new==set(current)-set(previous)and set(replay)==set(current)and all(tuple(v)==current[serial]for serial,v in replay.items()),'Complete allocation/free/reallocation chronology and final occurrence metadata')
                live_byserial=current
                for serial,v in current.items():
                    if serial in previous:need(v[:9]==previous[serial][:9]and v[10:]==previous[serial][10:]and(not v[9]or previous[serial][9]),'Persistent allocation identity; only actual free changes lifetime');continue
                    need(v[2]==phase and v[3]<api_count,'New occurrence joins this actual phase API invocation')
                    api=words(ledger,v[3]*104,26)
                    need(v[4]==api[24]and v[5]==api[20]and v[7]==api[10]and api[25]>0,'Exact actual allocator kind/result, saved source return and heap identity')
                    if v[4]==0:
                        initial=reader.data('constructor-prerequisites/'+stem+f'/allocation-{serial}/initial.bin')
                        need(v[6]==api[22]and v[8]==v[11]==len(initial)<=1024 and initial==reader.data(stem+f'/api-initial/{v[3]}/bytes.bin'),'Whole immediately observed HeapAlloc input before source writes')
                        occurrences.append(dict(sequence=sequence,phase=phase,root=root,metadata=list(v),API26=list(api),whole_initial_hex=initial.hex()));counts['actual_whole_initial_HeapAlloc_backings']+=1
                        if root in NEW:pending_new[(v[7],v[3])]=v;source_new_serials.add(serial)
                    else:need(v[6]==api[23]and v[10]in current,'Actual reallocation predecessor/request, initial reallocation bytes remain unobserved')
                if root in NEW:
                    # BEFORE graphs join the previously carried owners, not
                    # the fresh allocations observed later in this phase.
                    after_current=live_byserial;live_byserial=previous
                    graph(stem+'/BEFORE-constructor',phase_data=raw,side='BEFORE');graph(stem+'/BEFORE-member',True,raw,'BEFORE')
                    whole_owners(stem+'/BEFORE-owners')
                    live_byserial=after_current
                    graph(stem+'/AFTER-constructor',phase_data=raw,side='AFTER');graph(stem+'/AFTER-member',True,raw,'AFTER')
                    whole_owners(stem+'/AFTER-owners')
                    n=words(reader.data('constructor-prerequisites/'+stem+'/normal/normal-count.bin'))[0]
                    normal_blob=reader.data('constructor-prerequisites/'+stem+'/normal/normal-records.bin');need(0<n<=256 and len(normal_blob)==n*NBYTES,'Actual bounded new-root normal observations')
                    backing_blob=reader.data('constructor-prerequisites/'+stem+'/normal/getter-backings.bin');need(len(backing_blob)==n*40,'Complete normal-indexed getter backing companion')
                    null_count=words(reader.data(stem+'/nullfree-count.bin'))[0];null_blob=reader.data(stem+'/nullfree-snapshots.bin')
                    need(null_count<=10 and not null_count%2 and len(null_blob)==null_count*628,'Complete actual bounded NULL-free frame/CPU/FX/ENV observations')
                    if root in(0x4103f0,0x410440):need(null_count>0,'Actual literal normal old-NULL buffer release observed')
                    else:need(null_count==0,'No undeclared new-root NULL-free site')
                    null_active=None
                    for ni in range(null_count):
                        nr=null_blob[ni*628:(ni+1)*628];nm=words(nr,0,8);ncpu=words(nr,32,10);nframe=words(nr,612,4)
                        need(nm[:3]==(1,ni,root)and nm[3]==ni%2 and nm[4]==ncpu[9]and nm[5]==ncpu[4]and 0x20001000<=ncpu[4]<=0x20001ff0 and nframe==(0x5f40178c,0,0x58af9f,0),'Actual normal-zero MFC825/free cdecl frame joins physical58AF9A CALL')
                        need(nm[4]==(0x78001390 if ni%2==0 else 0x78001424),'Actual free entry and source post-epilogue preRET PCs')
                        item=dict(sequence=sequence,phase=phase,root=root,index=ni,metadata=list(nm),CPU=list(ncpu),FX512_hex=nr[72:584].hex(),ENV28_hex=nr[584:612].hex(),frame16_hex=nr[612:628].hex(),whole_raw_sha256=hashlib.sha256(nr).hexdigest(),source_CALL_PC=0x58af9a,source_return_PC=0x58af9f,postRET_observed=False)
                        if ni%2==0:null_active=item
                        else:
                            need(null_active is not None and nm[5:8]==tuple(null_active['metadata'][5:8])and item['frame16_hex']==null_active['frame16_hex']and item['FX512_hex']==null_active['FX512_hex']and item['ENV28_hex']==null_active['ENV28_hex']and all(ncpu[j]==null_active['CPU'][j]for j in(3,4,5,6,7)),'Balanced real NULL free call; complete frame/FS/APIcount/nonvolatile/FP conservation')
                            item['paired_entry_index']=null_active['index'];null_active=None;counts['actual_new_NULL_free_pairs']+=1
                        null_rows.append(item);counts['actual_new_NULL_free_boundaries']+=1
                    need(null_active is None,'No unmatched NULL free observer boundary')
                    active=None;getter=None;allocation_pairs=0;getter_pairs=0
                    for i in range(n):
                        raw_normal=normal_blob[i*NBYTES:(i+1)*NBYTES];row=normal(raw_normal);meta=row['metadata'];cpu=row['CPU'];frame=bytes.fromhex(row['frame64_hex']);kind=meta[3]
                        need(meta[:3]==[1,i,root]and meta[4]==cpu[9]and meta[5]==cpu[4]and meta[6]==contracts['source_MFC_entry_target']and meta[11]==cpu[1]and 0x20001000<=cpu[4]<=0x20001fc0,'Actual source machine/frame metadata')
                        need(words(row['pages_raw'],allpages.index(0x603000)*4096+0xfdc,2)==(meta[7],meta[8]),'Whole normal source page and shared list state')
                        backing=words(backing_blob,i*40,10)
                        if kind in(10,11):
                            need((cpu[1]&~4095)in allpages and(cpu[1]&4095)+8<=4096,'Full source-owned receiver page and field extent')
                            receiver_page=row['pages_raw'][allpages.index(cpu[1]&~4095)*4096:allpages.index(cpu[1]&~4095)*4096+4096];vptr=words(receiver_page,cpu[1]&4095)[0]
                            need((vptr&~4095)in allpages and(vptr&4095)+0x1c<=4096,'Full declared readonly vptr/slot backing')
                            vpage=row['pages_raw'][allpages.index(vptr&~4095)*4096:allpages.index(vptr&~4095)*4096+4096];target_PC=words(vpage,(vptr&4095)+0x18)[0]
                            need(backing==(1,i,cpu[1],cpu[1]&~4095,vptr,vptr&~4095,vptr+0x18,target_PC,4,2)and cpu[2]==vptr and target_PC==0x40a850,'Measured actual receiver/vptr permissions, held EDX and exact named slot target')
                            row['whole_receiver_page_sha256']=hashlib.sha256(receiver_page).hexdigest();row['whole_vptr_page_sha256']=hashlib.sha256(vpage).hexdigest();row['observed_backing_permissions']=list(backing)
                            counts['whole_source_receiver_readonly_dispatch_joins']+=1
                        else:need(backing==(0,)*10,'No stale getter companion at an unrelated normal boundary')
                        if kind==0:
                            need(active is None and getter is None and cpu[9]==meta[6]and words(frame)[0]in patches,'True actual callee823 entry source frame');active=row
                        elif 1<=kind<=8:
                            need(active is not None and getter is None,'Balanced actual allocation entry/return order')
                            a=active['CPU'];return_pc=words(bytes.fromhex(active['frame64_hex']))[0]
                            need(cpu[9]==return_pc and patches[return_pc]['kind']==kind and cpu[4]==a[4]+4 and all(cpu[j]==a[j]for j in(3,5,6,7)),'Same genuine cdecl allocation CALL and returned source frame')
                            requested=words(bytes.fromhex(active['frame64_hex']),4)[0];candidates=[v for v in pending_new.values()if v[2]==phase and v[7]==cpu[0]and active['metadata'][10]<=v[3]<meta[10]]
                            need(len(candidates)==1,'Returned MFC pointer joins one actual new HeapAlloc occurrence');v=candidates[0];api=words(ledger,v[3]*104,26)
                            need(v[6]==requested and api[4]-chain['MFC823_entry_to_HeapAlloc_before_delta']==a[4]and api[25]==chain['HeapAlloc_source_saved_return']and meta[10]>v[3],'Exact physical MFC/malloc/HeapAlloc frame chain and requested bytes')
                            row['matched_allocation_occurrence']=list(v);row['paired_entry_index']=active['metadata'][1];allocation_pairs+=1;active=None;counts['actual_cdecl_MFC_pairs']+=1
                        elif kind==10:
                            need(active is None and getter is None and cpu[9]==0x40a850 and words(frame)[0]==0x58b186,'Actual reached virtual getter entry');getter=dict(row)
                        elif kind==11:
                            need(active is None and getter is not None and cpu[9]==0x40a853 and words(frame)[0]==0x58b186,'Actual getter source preRET')
                            g=getter['CPU'];need((g[1]&~4095)in allpages and(g[1]&4095)+8<=4096,'Actual getter object field belongs to one complete declared source page; no owner AFTER seed')
                            expected=list(g);expected[0]=words(getter['pages_raw'],allpages.index(g[1]&~4095)*4096+(g[1]&4095)+4)[0];expected[9]=0x40a853
                            need(cpu==expected and row['FX512_hex']==getter['FX512_hex']and row['ENV28_hex']==getter['ENV28_hex']and row['frame64_hex']==getter['frame64_hex'],'Literal three-byte MOV getter effect and full integer-only source boundaries')
                            row['paired_entry_index']=getter['metadata'][1];getter_pairs+=1;getter=None;counts['actual_getter_entry_preRET_pairs']+=1
                        else:raise ValueError('Unrecognized real constructor observer kind')
                        row.pop('pages_raw');row.update(sequence=sequence,phase=phase,root=root,index=i,whole_raw_sha256=hashlib.sha256(raw_normal).hexdigest(),normal_blob_logical_key='constructor-prerequisites/'+stem+'/normal/normal-records.bin',normal_blob_offset=i*NBYTES,postRET_observed=False)
                        normal_rows.append(row);counts['whole_normal_CPU_FX_ENV_frame_boundaries']+=1
                    need(active is None and getter is None and allocation_pairs>0,'Complete observed positive normal constructor path; no unreturned pair')
                    counts['actual_new_constructor_phases']+=1
                    rows.append(dict(sequence=sequence,phase=phase,root=root,CPU_before=list(before),CPU_after=list(after),FX_before_hex=raw[116:628].hex(),FX_after_hex=raw[628:1140].hex(),ENV_before_hex=raw[2164:2192].hex(),ENV_after_hex=raw[2192:2220].hex(),observed_allocation_pairs=allocation_pairs,observed_getter_pairs=getter_pairs,source_derived_model_pending=True))
                counts['whole_phase_records']+=1;counts['whole_source_page_endpoints']+=92
            expected_registry=struct.pack('<'+str(len(carried))+'I',*carried)
            need(len(carried)==len(contracts['callback_values'])and reader.data(f'cleanup/{sequence}/registry.bin')==expected_registry,'Complete actual selected callback vector before cleanup')
            cleanup_prefix=f'constructor-prerequisites/cleanup/{sequence}/constructor-owner-'
            observed_cleaned=set()
            for key in sorted(k for k in reader.entries if k.startswith(cleanup_prefix)and k.endswith('/meta.bin')):
                v=occ(reader.data(key));need(v[1]not in observed_cleaned and v[1]in source_new_serials and v[1]in live_byserial and v==live_byserial[v[1]]and v[2]<len(order)and order[v[2]]['entry']in NEW and v[9],'Exactly one cleanup joins the whole final live new-owner occurrence')
                backing=reader.data(key.replace('/meta.bin','/before.bin'));need(len(backing)==v[8]and reader.data(key.replace('/meta.bin','/returned.bin'))==struct.pack('<I',1),'Whole actual MFC825 cleanup observation')
                observed_cleaned.add(v[1]);cleanup_rows.append(dict(sequence=sequence,metadata=list(v),whole_before_hex=backing.hex(),returned=True,scope='Research cleanup; registered callback shutdown remains unexecuted'));counts['whole_actual_new_owner_cleanup_returns']+=1
            need(observed_cleaned=={serial for serial in source_new_serials if live_byserial[serial][9]},'Every live measured new constructor owner freed exactly once by research cleanup')
        need(counts['whole_phase_records']==222 and counts['actual_new_constructor_phases']==18,'Complete genuine six-domain selected chronology')
        # Export all whole raw equality targets once, within this same reader.
        # Consumers use their own BEFORE as inputs and literal-derived outputs;
        # this export supplies no expected values to guest execution.
        export=E.Export(out/'raw-export','original',reader.path,pin);export.copy(reader);export_row=export.finish();export=None
        for filename,value in [('constructor-observations.json',rows),('constructor-normal-boundaries.json',normal_rows),('actual-initial-allocation-inputs.json',occurrences),('actual-list-graphs.json',graph_rows),('actual-new-owner-cleanup.json',cleanup_rows),('actual-new-NULL-free-boundaries.json',null_rows)]:
            path=out/filename;path.write_text(json.dumps(value,indent=2)+'\n');pin(path)
        pin(__file__);pin(Path(__file__).with_name('validate.py'));pin(Path(__file__).with_name('derive_validator_v2.py'));pin(Path(__file__).with_name('validate_v2.py'));pin(Path(__file__).with_name('derive_validator_v3.py'));pin(Path(__file__).with_name('validate_v3.py'));pin(Path(__file__).with_name('derive_validator_v4.py'));pin(sys.executable);passed=True
    except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        if export is not None:export.close();export=None
        if reader is not None:reader.close();reader.entries.clear();reader.bundles.clear();reader=None
        report=dict(passed=passed,scope='Actual37-root selected chronology through three constructors; genuine complete source pages, allocator occurrence capacities/initial inputs, list graphs, source cdecl MFC frames, getter entry/preRET and research cleanup. Literal native proof and full144 chronology remain separate.',build_path=str(Path(build).resolve()),build_sha256=build_sha,preflight_path=str(Path(preflight).resolve()),preflight_sha256=preflight_sha,execution_path=str(Path(execution).resolve()),execution_sha256=sha(Path(execution)/'report.json'),preparation_path=str(prep)if'prep'in locals()else None,preparation_sha256=b['preparation_sha256']if'b'in locals()else None,counts=dict(counts),paired_exports=[export_row]if'export_row'in locals()else[],reader_closed=True,reader_scope='One fresh bounded constructor original transport; all raw/index aliases closed',original_executed=True,native_executed=False,whole_literal_source_proof=False,initializer_credit=0,full144_chronology_claim=False,unexecuted_widget_slots=[0x5e0048,0x5e004c,0x5e0050],allocator_identity_scope='Actual observed API invocation/reallocation revision, not OS heap generation',observed_count_prediction_seed=False,source_AFTER_seed=False,original_getter_postRET_observed=False,files=files)
        path=out/'report.json';path.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,reader_closed=True,sha256=sha(path),counts=dict(counts))))

if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],Path(sys.argv[3]).resolve(),Path(sys.argv[4]).resolve(),sys.argv[5],sys.argv[6])
