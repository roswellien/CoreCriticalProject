"""Causal scalar native allocation metadata; future summary is never an input."""
def need(v,m):
 if not v:raise ValueError(m)
def derive(facts,mfc,strings,resource,growth,cut,contracts):
 need(type(cut)is int and 0<=cut<=len(facts),'Exact complete pre-cut API ordinal')
 need(len(resource)==8 and resource[0:2]==[1,1]and resource[2]>0 and resource[3:6]==[0x78145640,24,40]and resource[6]>0 and resource[7]==0,'Whole actual initialized Lockit resource identity; generation only corroborates causal bootstrap boundary')
 generation=0;cursor=0x31000000;owners={};sections=set();events=[];lockit_native=0;lockit_depth=0
 growth_by_api={g[1]:g for g in growth};need(len(growth_by_api)==len(growth),'Unique actual growth API index')
 for index,w in enumerate(facts[:cut]):
  need(len(w)==32 and w[:2]==[1,index]and w[14:16]==[1,1],'Whole indexed completed normal pre-cut32Q API fact')
  if index<4:need(w[3]==0x7802e03c,'Physical bootstrap start executes exactly four source CS initializations first')
  if index==4:
   need(generation==4 and len(sections)==4,'Physical Session bootstrap establishes four normal source CS before real indexed Lockit lifecycle API')
   need(0<w[16]<(1<<64) and w[16]%8==0 and 0<=w[9]<=0xffffffff and 0<=w[10]<=0xffffffff and w[9]==w[11],'Actual opaque native Lockit subject and restored DWORD LastError')
   expected=[0]*32;expected[:5]=[1,index,0,0x78146190,0x866ce];expected[8]=1;expected[9:12]=w[9:12];expected[14:17]=[1,1,w[16]];expected[31]=1
   need(w==expected,'Only exact whole32Q Lockit InitializeCriticalSection lifecycle row has no source CALL frame and marker31')
   lockit_native=w[16];generation+=1;need(resource[2]==generation,'Actual resource generation corroborates causal fifth generation at real lifecycle API4')
   events.append(dict(API=index,event='distinct-Lockit-association',generation=generation,source_CALL_frame_observed=False,lifecycle_subject=w[16]));continue
  need(not w[31],'Every other pre-cut record is normal source API, no generic lifecycle/cleanup allowance')
  slot=w[3];need(w[2]in contracts and (w[3],w[4],w[7],w[19])==tuple(contracts[w[2]][1:5]),'Exact physical source API CALL/slot/raw/arity contract')
  if slot in(0x78146198,0x78146184):
   entering=slot==0x78146198;need((w[2],w[4],w[7],w[19],w[20])==(0x7810a30b if entering else 0x7810a35e,0x771143e0 if entering else 0x77113460,1,0,0x78145640),'Exact named Lockit source CALL/import/argument; no arbitrary no-generation API')
   need(w[16]==lockit_native and w[17]==40 and w[13]==24 and w[29:31]==[1,1]and w[8]==w[12]==0 and not any(w[21:29]),'Same actual native lifecycle resource and full24B typed input/output, exact VOID return')
   next_depth=lockit_depth+(1 if entering else -1);need(0<=next_depth<=8 and w[18]==next_depth,'Actual serial same-resource Lockit depth and balanced source/API order');lockit_depth=next_depth
   events.append(dict(API=index,event='Lockit-Enter'if entering else'Lockit-Leave',generation=generation,depth=lockit_depth));continue
  if slot==0x7802e03c:
   need(w[7]==1 and w[20]not in sections,'Source one fresh normal CS initialization');sections.add(w[20]);generation+=1;events.append(dict(API=index,event='CS-birth',generation=generation));continue
  if slot in(0x7802e094,0x7802e1dc,0x7802e0b4,0x7802e090):need(w[20]==0x48450001 and w[21]==0,'Exact physical source own heap token and flags0')
  if slot==0x7802e094:
   extent=w[22];mapped=(extent+4095)&~4095;need(w[7]==3 and w[21]==0 and 0<extent<=1048576 and w[8]and w[8]%16==0 and w[12]==cursor and cursor+mapped<=0x32000000 and w[13]==extent,'Actual HeapAlloc source rounded request and disjoint birth alias')
   generation+=1;guest=cursor;cursor+=mapped;ms=[m for m in mfc if m[16]==guest];ss=[s for s in strings if s[10]==guest];need(len(ms)<=1 and len(ss)<=1 and not(ms and ss),'One current typed source birth')
   if ms:
    m=ms[0];need(len(m)==32 and m[0]==1 and m[3]==0x5f401ea0 and m[7]==m[13]and m[17]==w[8]and m[18]==generation and m[19]==extent and m[20]==guest and m[21]==1,'Actual same MFC/malloc source request, return, native pointer and derived generation');request=m[7];kind=4
   elif ss:
    s=ss[0];need(len(s)==32 and s[0]==1 and s[3]==0x78010a6d and s[7]==s[9]==s[8]+1 and s[11]==w[8]and s[12]==generation and s[13]==extent and s[17]==1 and s[23]==guest,'Actual same strdup strlen-plus-one request and complete typed source return');request=s[9];kind=3
   else:
    need(guest==0x31000000 and extent==128,'Only physical bootstrap PUSH128/CALLmalloc may birth untyped registry owner');request=128;kind=1
   need(((request+15)&~15 or 16)==extent,'Literal mode1 malloc source request rounding')
   need(guest not in owners,'Fresh disjoint live source birth');owners[guest]=dict(guest=guest,requested=request,extent=extent,mapped_bytes=mapped,generation=generation,kind=kind,native=w[8],acquired=w[8],capacity=0,live=True,birth_API=index);events.append(dict(API=index,event='HeapAlloc-birth',guest=guest,generation=generation));continue
  if slot==0x7802e1dc:
   need(w[7]==3 and w[21]==0 and w[22]in owners,'Own live HeapSize source pointer');o=owners[w[22]];need(o['live']and w[16]==o['native']and w[8]==w[17]==w[12]and o['extent']<=w[12]<=o['mapped_bytes']and w[13]==w[12],'Measured live same-native capacity bounded by own mapped backing');o['capacity']=o['extent']=w[12];events.append(dict(API=index,event='HeapSize',guest=o['guest'],generation=o['generation']));continue
  if slot==0x7802e0b4:
   need(index in growth_by_api and w[7]==4 and w[22]in owners,'Actual source growth joins existing own allocation');g=growth_by_api[index];o=owners[w[22]];need(o['live']and o['kind']==1 and w[16]==o['native']and w[17]==o['capacity']==o['extent']and w[23]==((o['capacity']+16+15)&~15),'Exact causal registry msize-plus16/rounded request')
   need(len(g)==32 and g[:3]==[1,index,w[2]]and g[3:11]==[o['guest'],o['native'],o['generation'],o['requested'],o['extent'],o['capacity'],o['capacity']+16,w[23]],'Growth OLD metadata only corroborates already derived causal owner')
   need(w[8]and w[8]%16==0 and g[11]==w[8]and g[12]==w[10]and g[14]==w[8]and not any(g[24:])and g[19]==1 and g[20]==w[23]and g[21:24]==[0,1,0],'Actual positive complete registry growth outcome')
   oldguest=o['guest'];newguest=cursor if w[8]!=o['native']else oldguest;need(g[13]==w[12]==newguest and g[16]==w[13]==w[23]and g[17]==0 and bool(g[18])==(w[8]!=o['native']),'Exact actual source-derived move/alias/extent')
   generation+=1;need(g[15]==generation,'New growth generation independently incremented')
   request=o['capacity']+16;mapped=(w[23]+4095)&~4095
   if newguest!=oldguest:del owners[oldguest];cursor+=mapped
   else:mapped=o['mapped_bytes']
   o.update(guest=newguest,requested=request,extent=w[23],mapped_bytes=mapped,generation=generation,native=w[8],acquired=w[8],capacity=0);owners[newguest]=o;events.append(dict(API=index,event='HeapReAlloc',guest=newguest,generation=generation));continue
  if slot==0x7802e090:
   need(w[7]==3 and w[22]in owners,'Source HeapFree of an actual prior owner');o=owners[w[22]];need(o['live']and w[16]==o['native']and w[8]==w[12]and 0<=w[12]<=0xffffffff,'Whole same-native HeapFree association and exact actual BOOL return')
   if w[12]:o['live']=False
   events.append(dict(API=index,event='HeapFree',guest=o['guest'],generation=o['generation']));continue
  # Other APIs have no allocation/CS birth in the reviewed current Binding.
  need(slot not in(0x7802e094,0x7802e0b4,0x7802e03c),'No unhandled generation-changing API')
 need(lockit_depth==0,'Constructor metadata input/return cut lies outside every completed source Lockit scope')
 return dict(owners={k:v for k,v in owners.items()if v['live']},generation=generation,allocation_cursor=cursor,events=events,cut_API=cut,future_allocation_summary_used=False,future_growth_seed_used=False)
