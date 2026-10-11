"""Fresh small original probe validation. Observed string/owner effects; no generic formatter proof."""
from pathlib import Path
import collections,hashlib,importlib.util,json,struct,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'reports/m4-mixed-format-original';PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def pin(p,h=None):
 p=Path(p).resolve();v=sha(p);need(h is None or h==v,'Physical identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==v,'Stable physical source');PINS[str(p)]=v;return p
def read(p,h=None):return json.loads(pin(p,h).read_text(encoding='utf-8-sig'))
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def main(path,digest,name):
 out=BASE/name;need(not out.exists(),'Fresh additive validation');out.mkdir(parents=True);passed=False;bundle=None;counts=collections.Counter();events=[];owners=[];root_rows=[]
 try:
  execution=read(path,digest);need(execution['passed'],'Actual bounded original execution');build=read(execution['build_path'],execution['build_sha256']);need(build['passed']and build['sequences']==1 and build['phases']==build['roots']==1,'One-root fresh mixed worker');pin(build['worker'],build['worker_sha256'])
  prep=read(Path(build['preparation'])/'report.json',build['preparation_sha256']);need(prep['format_event_bytes']==2244 and not prep['source_output_seed'] and not prep['predicted_counts_supplied_to_execution'],'Exact capture schema and no predicted observation input')
  for p,h in prep['files'].items():pin(p,h)
  roots=read(ROOT/'reports/m4-mixed-format-original/recovery-r1/roots.json');
  for r in roots:r.update(vtable=0x5cd5a8,statically_derived_default_request=r['formatting_default_request'],statically_derived_default_output=r['formatting_default_output'])
  mixed_rows=[];fs_rows=[];lockit_rows=[];page_rows=[];pages=prep['observed_pages'];need(len(pages)==43,'Unchanged ordinary43 pages')
  spec=importlib.util.spec_from_file_location('format_original_direct',pin(ROOT/'tools/m4-crt-allocation-root/run_v2.py'));direct=importlib.util.module_from_spec(spec);spec.loader.exec_module(direct);bundle=direct.DirectSet(Path(execution['original_capture']),pin)
  targets=words(bundle.data('formatting/import-targets.bin'),0,3);need(targets==(0x780264a9,0x780012b3,0x78022b9a),'Actual named staged CRT identities')
  initial_by_index={};previous_owners={};phase_pages=[]
  for phase,r in enumerate(roots):
   data=bundle.data(f'phase/0/{phase}.bin');need(len(data)==356992 and words(data,0,9)==(0,0,phase,r['slot'],r['entry'],0x7f,0,0,1),'Actual successful root and full hardware host restoration')
   def image(side,address,size):
    need((address&4095)+size<=4096,'Whole-page field');o=(2276 if side=='before' else 178404)+pages.index(address&~4095)*4096+(address&4095);return data[o:o+size]
   need(image('before',r['object'],r['object_extent'])==bytes(r['object_extent']),'Genuine untouched object BEFORE')
   root_before=words(data,36,10);root_after=words(data,76,10);need(root_before[4]==root_after[4]-4 and root_after[9]==0x410a80,'Actual top-level source RET')
   need(data[116:628]==data[628:1140] and data[2164:2192]==data[2192:2220],'Actual root architectural FP/ENV conservation')
   for page in prep['extra_whole_source_pages']:
    a=bundle.data(f'phase/0/{phase}/extra-before/{page}.bin');b=bundle.data(f'phase/0/{phase}/extra-after/{page}.bin');raw=pin(ROOT/f'reports/m4-formatting-frontier/recovery-r1/game-{page:08x}-raw-page.bin').read_bytes();need(len(a)==len(b)==4096 and a==b==raw,'Complete actual source asset page identity');counts['extra_whole_page_endpoint_relations']+=2
   ledger=list(struct.iter_unpack('<26I',bundle.data(f'phase/0/{phase}/api-ledger.bin')));need(words(bundle.data(f'phase/0/{phase}/api-count.bin'))[0]==len(ledger),'Actual full API ledger');counts['actual_Win32_API_records']+=len(ledger)
   stem=f'phase/0/{phase}/formatting';raw=bundle.data(stem+'/events.bin');n=words(bundle.data(stem+'/count.bin'))[0];need(n and len(raw)==n*2244,'Bounded actual full cdecl boundary array');sides=[]
   for i in range(n):
    row=raw[i*2244:(i+1)*2244];head=words(row,0,16);cpu=words(row,64,10);frame=words(row,644,8);kind=head[3];need(head[:3]==(1,i,r['entry']) and kind<6 and head[7]==targets[kind//2] and cpu[9]==head[4],'Actual root/API boundary labels and named targets')
    strings=[]
    for j in range(4):
     o=676+j*136;p,l=words(row,o,2);need(l<=128,'Actual bounded string extent');v=row[o+8:o+8+l];need(not p or l and v[-1]==0,'Actual whole NUL-terminated input string');strings.append(dict(pointer=p,length=l,bytes_hex=v.hex()))
    evt=dict(phase=phase,index=i,root=r['entry'],kind=kind,actual_source_pc=head[4],actual_provider=head[7],CALL_pc=head[8],header=list(head),cpu=list(cpu),frame32_hex=row[644:676].hex(),strings=strings,FX512_hex=row[104:616].hex(),ENV28_hex=row[616:644].hex(),owned_hex=row[1220:1220+head[15]].hex(),actual_provider_return_to_game_observed=bool(kind&1),original_post_source_cleanup_observed=False)
    events.append(evt);sides.append((head,cpu,row,frame));counts['actual_cdecl_boundaries']+=1
   need([h[3]for h,c,b,f in sides]==[0,1,2,3,4,5],'Actual observed cdecl CALL/return order')
   for type_,(callpc,retpc,nargs)in enumerate([(0x4dea15,0x4dea1b,2),(0x4deab1,0x4deab7,1),(0x4dead1,0x4dead7,4)]):
    h,c,b,f=sides[type_*2];q,d,a,g=sides[type_*2+1];need(c[4]+4==d[4] and f[0]==retpc and q[4]==d[9]==retpc,'Actual cdecl frame and genuine return-to-caller ESP/PC');need(all(c[j]==d[j]for j in (3,5,6,7)),'Actual cdecl callee-saved CPU');need(f[1:nargs+1]==g[:nargs],'Actual caller-owned arguments carried over RET');counts['actual_cdecl_frame_and_return_pairs']+=1
   h,c,b,f=sides[0];q,d,a,g=sides[1];need(f[1:3]==(r['filename'],0x2e) and not d[0],'Actual default strrchr NULL result');need(b[104:644]==a[104:644] and not(c[8]&0x400)and not(d[8]&0x400),'Actual complete strrchr FP/ENV and source DF0')
   mh,mc,mb,mf=sides[2];rh,rc,rb,rf=sides[3];sh,sc,sb,sf=sides[4];th,tc,tb,tf=sides[5]
   need(mf[1]==r['statically_derived_default_request'] and sf[1]==rc[0] and sf[2]==0x5e37f0 and sf[3]==r['filename'],'Actual malloc request and sprintf destination/format/filename args')
   actual_owner_count=words(bundle.data(stem+'/owner-count.bin'))[0];need(actual_owner_count>len(previous_owners) and actual_owner_count<=16,'Actual owner occurrence count grew')
   for index in range(actual_owner_count):
    base=stem+f'/owner/{index}';meta=words(bundle.data(base+'/meta.bin'),0,16);initial=bundle.data(base+'/initial.bin');final=bundle.data(base+'/bytes.bin');need(meta[:2]==(1,index) and len(initial)==len(final)==meta[6]>=meta[4],'Actual whole capacity owner observation')
    if index in previous_owners:need(meta==previous_owners[index]['meta'] and initial==previous_owners[index]['initial'] and final==previous_owners[index]['final'],'Persistent actual full owner bytes');counts['whole_carried_owner_relations']+=1;continue
    need(meta[2]==r['entry'] and meta[3]==0x4deab1 and meta[4]==mf[1] and meta[5]==rc[0] and meta[7]==rh[14],'Unique actual malloc occurrence/source frame/HeapAlloc attribution');api=ledger[meta[7]];need(api[24]==0 and api[10]==meta[5] and api[20]==meta[8] and api[22]==meta[9] and meta[4]<=meta[9]<=meta[6],'Actual HeapAlloc result/heap/request/capacity relation')
    need(initial==bundle.data(f'phase/0/{phase}/api-initial/{meta[7]}/bytes.bin') and len(initial)==words(bundle.data(f'phase/0/{phase}/api-initial/{meta[7]}/size.bin'))[0],'Whole original allocator initial backing')
    output=r['statically_derived_default_output'].encode()+b'\0';need(final[:len(output)]==output and final[len(output):]==initial[len(output):],'Actual formatted output and untouched complete capacity tail');need(tc[0]==len(output)-1 and tb[1220:1220+meta[6]]==final and rb[1220:1220+meta[6]]==initial,'Actual sprintf return count/final bytes and actual malloc-return initial bytes');need(words(image('after',r['owned_pointer_field'],4))[0]==meta[5],'Actual game owner publication')
    owned=dict(index=index,root=r['entry'],meta=list(meta),pointer=meta[5],request=meta[4],actual_HeapAlloc_request=meta[9],capacity=meta[6],API_index=meta[7],initial_hex=initial.hex(),final_hex=final.hex(),output_hex=output.hex());owners.append(owned);previous_owners[index]=dict(meta=meta,initial=initial,final=final);counts['actual_allocator_occurrences']+=1;counts['full_owned_initial_final_relations']+=1;counts['source_owner_publications']+=1
   obj=words(image('after',r['object'],r['object_extent']),0,r['object_extent']//4);need(obj[0]==r['vtable'] and obj[1]==rc[0] and obj[2:9]==(0,0,0,128,100,0,1)and(r['object_extent']==36 or obj[9]==0),'Actual literal base object header fields; complete264B retained without inferred later-byte expectations');root_rows.append(dict(phase=phase,entry=r['entry'],BEFORE_CPU=list(root_before),AFTER_CPU=list(root_after),object_address=r['object'],object_DWORDs=list(obj),request=mf[1],sprintf_result=tc[0],source_strlen_plus4_verified=True));counts['actual_root_phases']+=1
   for name in ('lockit-count.bin','fs-count.bin'):
    # These APIs may expose FS inside registry/free; per-kind boundaries retained separately.
    if f'phase/0/{phase}/{name}'in bundle.entries:counts['actual_'+name.split('-')[0]+'_observations']+=words(bundle.data(f'phase/0/{phase}/{name}'))[0]
  # Initial allocator backings are genuine API-return inputs, all writes below are literal source stores.
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
  registry=words(bundle.data('cleanup/0/registry.bin'),0,1);need(registry==tuple(r['registration']['callback']for r in roots),'Actual callback registrations in source order');counts['actual_callbacks_registered']=len(registry)
  owner_count=words(bundle.data('cleanup/formatting-owner-count.bin'))[0];need(owner_count==len(owners),'Actual full cleanup owner extent')
  for o in owners:
   base=f'cleanup/formatting/{o["index"]}';need(words(bundle.data(base+'/meta.bin'),0,16)==tuple(o['meta']) and bundle.data(base+'/before.bin').hex()==o['final_hex'] and words(bundle.data(base+'/returned.bin'))==(1,),'Actual source CRT free returned after complete final backing capture');counts['actual_source_free_returns']+=1
  need(bundle.data('COMPLETE.txt')==b'complete','Actual worker completion');passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  if bundle:bundle.close()
  for fn,value in [('actual-cdecl-boundaries.json',events),('actual-owners.json',owners),('actual-root-relations.json',root_rows),('actual-mixed-owned-relations.json',mixed_rows),('actual-FS-events.json',fs_rows),('actual-Lockit-boundaries.json',lockit_rows),('whole-page-endpoints.json',page_rows)]:p=out/fn;p.write_text(json.dumps(value,indent=2)+'\n');pin(p)
  pin(__file__);report=dict(passed=passed,scope='Genuine mixed original prefix cdecl formatting, initial-to-literal-write whole MFC backings/publications, complete nested FS frames and balanced Lockit API boundaries; original ctor pre-epilogue is explicitly bounded, no native or cold-path credit',execution_path=str(path),execution_sha256=digest,build_sha256=execution.get('build_sha256'),preparation_sha256=build.get('preparation_sha256'),counts=dict(counts),reader_closed=True,original_source_instruction_trace_pending=True,native_executed=False,initializer_credit=False,source_output_seed=False,files=PINS);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'),counts=dict(counts))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
