"""Add typed MFC/FS/Lockit scope to the immutable genuine cdecl-prefix validator."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def one(s,a,b):
 assert s.count(a)==1,a[:70];return s.replace(a,b,1)
s=(ROOT/'tools/m4-formatting-original/validate_v2.py').read_text()
s=s.replace("BASE=ROOT/'reports/m4-formatting-original'","BASE=ROOT/'reports/m4-mixed-format-original'")
s=one(s,"build['phases']==build['roots']==3","build['phases']==build['roots']==1")
s=one(s,"'Three-root fresh worker'","'One-root fresh mixed worker'")
s=one(s,"roots=read(ROOT/'reports/m4-formatting-frontier/recovery-r1/roots.json');pages=prep['observed_pages'];", "roots=read(ROOT/'reports/m4-mixed-format-original/recovery-r1/roots.json');\n  for r in roots:r.update(vtable=0x5cd5a8,statically_derived_default_request=r['formatting_default_request'],statically_derived_default_output=r['formatting_default_output'])\n  mixed_rows=[];fs_rows=[];lockit_rows=[];page_rows=[];pages=prep['observed_pages'];")
s=one(s,"'Actual complete object fields'","'Actual literal base object header fields; complete264B retained without inferred later-byte expectations'")
s=one(s,"registry=words(bundle.data('cleanup/0/registry.bin'),0,3)","registry=words(bundle.data('cleanup/0/registry.bin'),0,1)")
marker="  registry=words(bundle.data('cleanup/0/registry.bin'),0,1)"
extension=r'''  # Initial allocator backings are genuine API-return inputs, all writes below are literal source stores.
  root=roots[0];data=bundle.data('phase/0/0.bin');n=words(bundle.data('phase/0/0/mixed/owner-count.bin'))[0];need(n==3,'Measured normal path has three MFC occurrences')
  actual_alloc=[]
  for i in range(n):
   stem=f'phase/0/0/mixed/owner/{i}';meta=words(bundle.data(stem+'/meta.bin'),0,17);initial=bundle.data(stem+'/initial.bin');final=bundle.data(stem+'/bytes.bin');need(meta[:3]==(1,i,0x4e1ca0)and len(initial)==len(final)==meta[8]and meta[8]>=meta[4]and meta[9]==meta[3]+5 and meta[10]==meta[4],'Genuine measured source MFC CALL frame/request/capacity')
   api=ledger[meta[6]];need(api[24]==0 and api[10]==meta[7]and api[4]+104==meta[5]and api[22]<=meta[8]and meta[4]<=api[22],'Actual HeapAlloc result and exact MFC source frame')
   need(initial==bundle.data(f'phase/0/0/api-initial/{meta[6]}/bytes.bin') and words(bundle.data(f'phase/0/0/api-initial/{meta[6]}/size.bin'))==(meta[8],),'Whole actual allocated initial backing before literal writes')
   actual_alloc.append((meta,initial,final));counts['actual_MFC_allocator_occurrences']+=1
  inner,header,sentinel=actual_alloc;need([(m[3],m[4])for m,a,b in actual_alloc]==[(0x49cc8d,12),(0x4e5325,24),(0x4e535b,24)],'Actual reached12B/24B/24B allocation source sites')
  allstores=[[(0x49cc95,0,inner[0][7]),(0x49cc97,4,inner[0][7])],[(0x4e532a,4,0),(0x4e532d,20,1),(0x4e5339,0,0),(0x4e5343,8,0)],[(0x4e5360,4,header[0][7]),(0x4e5363,20,0),(0x4e5372,0,sentinel[0][7]),(0x4e5381,8,sentinel[0][7])]]
  publication=[(0x49cc9a,0x60b750),(0x4e5334,0x60b7d4),(0x4e5366,0x60b764)]
  for (meta,initial,final),stores,(pubpc,field)in zip(actual_alloc,allstores,publication):
   expected=bytearray(initial)
   for pc,offset,value in stores:struct.pack_into('<I',expected,offset,value)
   need(final==expected,'Complete genuine backing predicted only from initial+literal source writes; untouched tails preserved')
   need(words(image('after',field,4))==(meta[7],),'Actual literal source owner publication')
   row=dict(index=meta[1],root=meta[2],CALL_pc=meta[3],source_request=meta[4],source_frame=meta[5],API_index=meta[6],pointer=meta[7],capacity=meta[8],actual_source_frame32_hex=struct.pack('<8I',*meta[9:]).hex(),meta=list(meta),initial_hex=initial.hex(),final_hex=final.hex(),literal_source_stores=[dict(PC=pc,offset=off,width=4,value=value)for pc,off,value in stores],publication_PC=pubpc,publication_field=field,OS_heap_generation_claimed=False);mixed_rows.append(row);counts['full_MFC_owned_byteflows']+=1;counts['MFC_literal_owned_stores']+=len(stores);counts['MFC_source_publications']+=1
   stem=f'cleanup/mixed/{meta[1]}';need(words(bundle.data(stem+'/meta.bin'),0,17)==meta and bundle.data(stem+'/before.bin')==final and words(bundle.data(stem+'/returned.bin'))==(1,),'Actual MFC825 full backing and free return');counts['actual_MFC825_free_returns']+=1
  need(words(image('before',0x60b7d4,4))==(0,)and words(image('before',0x60b7d0,4))==(0,)and words(image('after',0x60b7d0,4))==(1,),'Genuine untouched zero header/counter and literal counter increment')
  raw=bundle.data('phase/0/0/fs-events.bin');need(words(bundle.data('phase/0/0/fs-event-count.bin'))==(6,)and len(raw)==6*1216,'Two actual complete nested FS frames')
  sequence=[(0x4e5297,0),(0x4e529e,1),(0x4e2197,0),(0x4e219e,1),(0x4e22cd,2),(0x4e539d,2)];prior=None;active=[];outer_host=None
  for i,(pc,kind)in enumerate(sequence):
   b=raw[i*1216:(i+1)*1216];h=words(b,0,8);c=words(b,32,10);d=words(b,72,10);rb=b[112:124];ra=b[124:136];need(h[:4]==(1,0x4e1ca0,pc,kind)and c[9]==d[9]==pc and rb==ra,'Actual full FS boundary/opcode and twelve-byte frame conservation');need(all(c[j]==d[j]for j in range(9)if not(kind==0 and j==0))and b[136:648]==b[648:1160]and b[1160:1188]==b[1188:1216],'Actual FS full register/FP/ENV conservation')
   if prior is not None:need(h[4]==prior,'Actual FS source chain continuity')
   if kind==0:need(h[4]==h[5]==d[0],'Actual MOV EAX,FS head');outer_host=h[4]if outer_host is None else outer_host
   elif kind==1:
    need(h[5]==c[4]==h[6]and h[7]==1,'Actual FS installation owns twelve-byte guest frame');r=words(rb,0,3);need(r==(h[4],0x5b956c if pc==0x4e529e else 0x5b90fb,0xffffffff),'Actual predecessor/handler/scope at install');active.append(h[6])
   else:
    need(active and h[4]==active.pop() and h[5]==c[1]and h[6]==h[4]and h[7]==1 and words(rb)[0]==h[5],'Actual LIFO restore through exact saved predecessor/complete frame')
   fs_rows.append(dict(index=i,PC=pc,kind=kind,header=list(h),CPU_before=list(c),CPU_after=list(d),record_before_hex=rb.hex(),record_after_hex=ra.hex(),FX_before_hex=b[136:648].hex(),FX_after_hex=b[648:1160].hex(),ENV_before_hex=b[1160:1188].hex(),ENV_after_hex=b[1188:1216].hex()));prior=h[5];counts['actual_complete_FS_events']+=1
  need(not active and prior==outer_host,'Actual original FS chain restored')
  raw=bundle.data('phase/0/0/lockit-snapshots.bin');need(words(bundle.data('phase/0/0/lockit-count.bin'))==(6,)and len(raw)==6*12988,'Actual single balanced six-boundary Lockit pair');cps=[]
  for i in range(6):
   b=raw[i*12988:(i+1)*12988];h=words(b,0,16);c=words(b,64,10);frame=words(b,644,8);cs=words(b,676,6);need(h[:4]==(1,i,0x4e1ca0,i)and h[7]==2 and h[8]==0x60b668 and h[13:15]==(0x7810a290,0x7810a350),'Authentic postDllMain state2/named source imports and pair scope')
   if i in(0,1,2):need(h[10:12]==(0,0),'Actual header NULL/counter zero before entered allocation path')
   else:need(h[10:12]==(header[0][7],1),'Actual published header/counter carried under held lock')
   cps.append((h,c,frame,cs,b));lockit_rows.append(dict(index=i,kind=i,header=list(h),CPU=list(c),frame32_hex=b[644:676].hex(),CS24_hex=b[676:700].hex(),FX512_hex=b[104:616].hex(),ENV28_hex=b[616:644].hex(),pages_sha256=[hashlib.sha256(b[700+j*4096:700+(j+1)*4096]).hexdigest()for j in range(3)],genuine_pre_epilogue=True if i==2 else False,derived_source_postRET=False));counts['actual_Lockit_boundaries']+=1
  h,c,f,cs,b=cps[0];scratch=c[1];need(f[0]==0x4e5315 and c[9]==0x7810a290,'Actual constructor CALL entry')
  ah,ac,af,acs,ab=cps[1];need(ac[4]==c[4]-16 and af[0:2]==(0x7810a311,0x78145640)and ac[9]==ah[9]and ah[9]!=0,'Actual entered Win32 API CPU/frame at source CALL')
  dh,dc,df,dcs,db=cps[3];need(dc[1]==scratch and df[0]==0x4e538f and dc[9]==0x7810a350,'Actual destructor same literal scratch and CALL entry')
  lh,lc,lf,lcs,lb=cps[4];need(lc[4]==dc[4]-8 and lf[0:2]==(0x7810a364,0x78145640)and lc[9]==lh[9]and lh[9]!=0,'Actual leave Win32 API CPU/frame at source CALL')
  unheld=cps[0][3];held=cps[2][3];need(unheld==cps[1][3]==cps[5][3] and held==cps[3][3]==cps[4][3],'Complete actual CS24 ownership stages balanced');need(unheld[1:4]==(0xffffffff,0,0)and held[1:4]==(0xfffffffe,1,cps[0][0][6])and unheld[0]==held[0]and unheld[4:]==held[4:],'Measured exact current thread held/unheld CS24 fields, opaque words conserved')
  need(cps[2][1][4]==c[4]-8 and cps[2][1][9]==0x7810a311 and cps[5][1][4]==dc[4]and cps[5][1][9]==0x7810a364,'Scope bounded original ctor pre-epilogue and dtor actual preRET; no captured source postRET seeded')
  for page in pages:page_rows.append(dict(page=page,BEFORE_sha256=hashlib.sha256(image('before',page,4096)).hexdigest(),AFTER_sha256=hashlib.sha256(image('after',page,4096)).hexdigest(),whole_bytes_captured=True,literal_source_comparison_pending=True))
  counts['complete_root_page_endpoints']=2*len(pages);counts['actual_MFC_owner_count']=n
'''
s=one(s,marker,extension+marker)
s=one(s,"('actual-root-relations.json',root_rows)","('actual-root-relations.json',root_rows),('actual-mixed-owned-relations.json',mixed_rows),('actual-FS-events.json',fs_rows),('actual-Lockit-boundaries.json',lockit_rows),('whole-page-endpoints.json',page_rows)")
s=s.replace('Genuine original formatting3 actual cdecl calls/returns, complete source inputs, allocator initial/capacity/backing/publication and source CRT cleanup; reached literal _output semantics remain pending, no generic formatter or native execution claim','Genuine mixed original prefix cdecl formatting, initial-to-literal-write whole MFC backings/publications, complete nested FS frames and balanced Lockit API boundaries; original ctor pre-epilogue is explicitly bounded, no native or cold-path credit')
out=ROOT/'tools/m4-mixed-format-original/validate.py';assert not out.exists();out.write_text(s)
