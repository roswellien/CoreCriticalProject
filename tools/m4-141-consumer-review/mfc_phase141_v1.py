"""Fresh full131 original normal observations; no literal/native or guessed-result claim."""
import struct
def w(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def observe(records,data,seq,phase,out,pin,counts,artifacts):
 def need(x,m):
  if not x:raise ValueError(m)
 need(phase==15 and w(data,16)==(0x5ae3e4,),'Exact current chronological MFC phase')
 stem=f'phase/{seq}/{phase}';base=stem+'/MFC1168/'
 def retain(key):
  raw=records.data(key);p=out/'actual-MFC-inputs'/key;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);pin(p);return raw
 # The small exports seal complete actual loaded images, capacities and API
 # observations, while the single current capture reader is already open.
 keys=sorted(k for k in records.entries if k.startswith(base))
 need(keys,'Fresh current MFC exports')
 values={key:retain(key)for key in keys}
 raw_path=out/'actual-MFC-inputs'/(stem+'.bin');raw_path.parent.mkdir(parents=True,exist_ok=True);raw_path.write_bytes(data);pin(raw_path)
 for address in(0x5cd000,0x5e3000,0x5e9000):
  for side in('before','after'):retain(stem+f'/extra-{side}/{address}.bin')
 targets=w(values[base+'named-API/targets.bin'],0,4)
 for side in('before','after'):
  address=w(retain(stem+f'/TEB-{side}-base.bin'))[0];teb=retain(stem+f'/TEB-{side}.bin')
  need(address%4096==0 and len(teb)==8192 and w(teb,0x18)==(address,),'Coherent full true root TIB and self')
  counts['MFC_true_root_TIB8192_endpoints']+=1
 domains={}
 for side in('BEFORE','AFTER'):
  domain=values[base+side+'/domain/domain.bin'];need(len(domain)==40,'Exact current MFC domain geometry')
  meta=w(domain,0,10);blocks={}
  need(meta[0]==w(records.data(stem+'/TEB-before-base.bin'))[0]and meta[1]>0,'Current domain thread/TEB identity')
  for kind,lo,hi in [('MFC',0x5f400000,0x5f4ed000),('CRT',0x78000000,0x78040000)]:
   ledger=values[base+side+'/'+kind+'/metadata.bin'];need(len(ledger)%16==0,'Whole loaded page ledger')
   seen=set()
   for i in range(len(ledger)//16):
    address,protection,type_,owner=w(ledger,i*16,4);need(address not in seen and lo<=address<hi and address%4096==0 and type_==0x1000000 and owner==lo,'Actual canonical loader page identity');seen.add(address)
    need(len(values[base+side+'/'+kind+'/'+str(address)+'.bin'])==4096,'Every complete current loader page');counts['MFC_whole_loaded_'+kind+'_page_endpoints']+=1
   need((0x5f4cb000 if kind=='MFC'else 0x78037000)in seen,'Actual whole manager/codepage page retained')
  for role in('manager','manager-array','thread','thread-array','thread-object','thread-object-plus4','global-object'):
   key=base+side+'/domain/'+role+'/meta.bin'
   if key not in values:continue
   row=w(values[key],0,8);info=dict(metadata=list(row),whole_capacity_observed=bool(row[6]and row[7]))
   if row[6]and row[7]:
    raw=values[key.replace('/meta.bin','/bytes.bin')];need(len(raw)==row[6]<=65536,'Actual whole borrowed backing');info['bytes_hex']=raw.hex();counts['MFC_whole_borrowed_backing_endpoints']+=1
   elif row[5]!=0x1000000:need(len(values[key.replace('/meta.bin','/unresolved-page.bin')])==4096,'Explicit unresolved domain remains page-only')
   blocks[role]=info
  lock=w(values[base+side+'/CRT-codepage-lock/meta.bin'],0,4);need(lock[0]==0x7803708c and lock[2]==24 and lock[3]==bool(lock[1]),'Actual codepage lock25 pointer')
  if lock[1]:need(len(values[base+side+'/CRT-codepage-lock/bytes.bin'])==24,'Whole actual unheld CS24');counts['MFC_codepage_CS24_endpoints']+=1
  domains[side]=dict(metadata=list(meta),blocks=blocks,lock25_metadata=list(lock))
 n=w(values[base+'boundaries/count.bin'])[0];blob=values[base+'boundaries/records.bin'];pcs=[0x5f401083,0x5ae3ad,0x5ae3b7,0x5ae3ba,0x5ae3c0,0x78003ddb,0x5ae3ca]
 need(n==7 and len(blob)==n*664,'All seven normal source/provider boundaries')
 boundaries=[]
 for i,pc in enumerate(pcs):
  b=blob[i*664:(i+1)*664];cpu=w(b,0,10);frame=b[580:644];meta=w(b,644,5)
  need(cpu[9]==pc and meta[1]==domains['BEFORE']['metadata'][1],'Actual reached MFC boundary order and source thread')
  if i==0:need(w(frame)==(0x5ae3ad,),'True actual MFC CALL saved return')
  if i==5:need(w(frame,0,2)==(0x5ae3ca,0xfffffffd),'True cdecl setmbcp−3 argument')
  row=dict(sequence=seq,phase=phase,index=i,CPU=list(cpu),FX512_hex=b[40:552].hex(),ENV28_hex=b[552:580].hex(),frame64_hex=frame.hex(),metadata=list(meta),FS_scope='C++ observer samples actual compiler host EH frame; true source TIB retained separately')
  if i in(1,2,3,4):
   raw=values[base+'boundaries/'+str(i)+'-whole-provider.bin'];need(len(raw)==meta[4]>=0x1044 and meta[3]==cpu[0],'Actual complete returned provider object before source field write');row['whole_provider_hex']=raw.hex();row['whole_provider_before_write_hex']=raw.hex()
  boundaries.append(row);counts['MFC_full_normal_boundaries']+=1
 n=w(values[base+'named-API/count.bin'])[0];blob=values[base+'named-API/records.bin'];need(n==8 and len(blob)==n*668,'Four complete genuine named API entry/return pairs')
 apis=[]
 for i in range(n):
  b=blob[i*668:(i+1)*668];cpu=w(b,0,10);frame=b[580:644];kind,side,argc,thread,error,head=w(b,644,6)
  need(kind<4 and side==i%2 and argc==(0 if kind==2 else 1)and thread==domains['BEFORE']['metadata'][1],'Actual named API frame domain')
  row=dict(sequence=seq,phase=phase,index=i,API=['TlsGetValue','EnterCriticalSection','GetACP','LeaveCriticalSection'][kind],kind=kind,side=side,argc=argc,thread=thread,last_error=error,FShead=head,CPU=list(cpu),FX512_hex=b[40:552].hex(),ENV28_hex=b[552:580].hex(),frame64_hex=frame.hex())
  if not side:need(cpu[9]==targets[kind],'Actual owning named API target');row['saved_source_return']=w(frame)[0]
  else:
   a=apis[-1];need(a['kind']==kind and a['side']==0 and cpu[9]==a['saved_source_return']and cpu[4]==a['CPU'][4]+4*(argc+1),'Same actual API callee cleanup/source continuation');need(all(cpu[j]==a['CPU'][j]for j in(3,5,6,7)),'Actual API callee-saved GPRs');counts['MFC_full_named_API_pairs']+=1
  apis.append(row)
 need([v['kind']for v in apis[::2]]==[0,1,2,3],'Genuine normal cached/TLS/codepage named API chronology')
 before=w(data,36,10);after=w(data,76,10);need(before[4]==0x20001800 and after[4]==0x20001804 and after[9]==0x410a80,'Actual initializer return and full caller framing; root EAX retained observed and derived later from literal root tail')
 artifacts.append(dict(sequence=seq,phase=phase,root=0x5ae3e4,CPU_before=list(before),CPU_after=list(after),raw_phase_record=str(raw_path),raw_phase_record_sha256=__import__('hashlib').sha256(data).hexdigest(),FX_before_hex=data[116:628].hex(),FX_after_hex=data[628:1140].hex(),ENV_before_hex=data[2164:2192].hex(),ENV_after_hex=data[2192:2220].hex(),domains=domains,boundaries=boundaries,APIs=apis,source_BEFORE_input_seeded=False,source_literal_model_pending=True))
 counts['MFC_original_phases']+=1

def constructor(records,out,pin,counts,artifacts):
 def need(x,m):
  if not x:raise ValueError(m)
 keys=sorted(k for k in records.entries if k.startswith('constructor-prerequisites/'))
 need(keys,'Actual constructor prerequisite exports from this worker')
 values={}
 for key in keys:
  raw=records.data(key);p=out/'actual-constructor-inputs'/key;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);pin(p);values[key]=raw
 for seq in range(6):
  before=None
  for side in('BEFORE-MFC','AFTER-MFC'):
   base=f'constructor-prerequisites/phase/{seq}/15/{side}/';meta=w(values[base+'meta.bin'],0,9);page=values[base+'5F2000.bin']
   need(meta[:2]==(1,0x603fdc)and meta[3]==0x603fe0 and meta[5]==0x5f2a48 and len(page)==4096 and w(page,0xa48)==(meta[6],),'Whole genuine current constructor data page and named scalar identity')
   occraw=values[base+'occurrences.bin'];need(len(occraw)%48==0,'Complete actual allocation occurrence ledger');occ=[w(occraw,i*48,12)for i in range(len(occraw)//48)]
   byserial={v[1]:v for v in occ};need(len(byserial)==len(occ)and all(v[0]==1 and v[1]and v[4]in(0,3)and v[8]and v[9]in(0,1)for v in occ),'Measured occurrence IDs/revisions, not OS generations')
   nodes=[];n=w(values[base+'nodes-count.bin'])[0];need(n<=256 and bool(n)==bool(meta[2]),'Bounded genuine list extent')
   for i in range(n):
    r=w(values[base+f'node-{i}/meta.bin'],0,10);raw=values[base+f'node-{i}/bytes.bin'];need(r[:2]==(1,i)and len(raw)==r[3]>=12 and r[4]in byserial,'Whole actual list owner capacity and occurrence join');o=byserial[r[4]]
    need(o[9]==1 and o[7]==r[2]and o[8]==r[3]and o[2:4]==r[5:7]and w(raw,0,3)==r[7:10],'Full actual owner/publication/link metadata joins')
    nodes.append(dict(meta=list(r),whole_bytes_hex=raw.hex()));counts['constructor_whole_current_list_owner_endpoints']+=1
   if n:
    need(nodes[0]['meta'][2]==meta[2]and all(v['meta'][7]==nodes[(i+1)%n]['meta'][2]and v['meta'][8]==nodes[(i-1)%n]['meta'][2]for i,v in enumerate(nodes)),'Complete forward/backward current shared-list graph')
   row=dict(sequence=seq,side=side,metadata=list(meta),occurrences=[list(v)for v in occ],nodes=nodes,whole_5F2000_hex=page.hex(),constructor_roots_executed=True,source_inputs=False,allocation_identity_scope='Actual observed API invocation occurrence and reallocation revision; not OS heap generation')
   if before is not None:need(row['metadata']==before['metadata']and row['occurrences']==before['occurrences']and row['nodes']==before['nodes']and row['whole_5F2000_hex']==before['whole_5F2000_hex'],'Actual MFC service leaves constructor prerequisite graph/data unchanged')
   before=row;artifacts.append(row);counts['constructor_prerequisite_graph_endpoints']+=1
  # Attribute each HeapAlloc initial input to the actual same current prefix
  # ledger call/result. The bootstrap immediate bytes have no second duplicate;
  # they remain authenticated by the actual linked inherited observer.
  for key,raw in values.items():
   prefix='constructor-prerequisites/'
   if not key.endswith('/occurrence.bin'):continue
   v=w(raw,0,12);stem=key[len(prefix):].rsplit('/allocation-',1)[0]
   if not(stem==f'bootstrap/{seq}'or stem.startswith(f'phase/{seq}/')):continue
   ledger=records.data(stem+('/producer-api-ledger.bin'if stem.startswith('bootstrap/')else'/api-ledger.bin'))
   need(len(ledger)%104==0 and v[3]<len(ledger)//104,'Real current prefix API occurrence index')
   a=w(ledger,v[3]*104,26);initial=values[key.replace('/occurrence.bin','/initial.bin')]
   need(v[0]==1 and v[4]==a[24]==0 and v[5]==a[20]and v[6]==a[22]and v[7]==a[10]and v[8]==v[11]==len(initial)<=1024 and v[9]==1 and v[10]==0,'Actual HeapAlloc target/result/request and complete immediately captured capacity')
   if stem.startswith('phase/'):
    need(initial==records.data(stem+f'/api-initial/{v[3]}/bytes.bin')and w(records.data(stem+f'/api-initial/{v[3]}/size.bin'))==(len(initial),),'Complete same measured initial bytes before guest writes')
   counts['constructor_actual_prefix_initial_allocations']+=1
