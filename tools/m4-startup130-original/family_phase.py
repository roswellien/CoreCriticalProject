"""Fresh whole original formatter/mixed/COS observations, separate from literal/native credit."""
import hashlib,struct
def words(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def observe(records,data,seq,phase,entry,page,formats,mixed,artifacts,counts,tid,targets,roots):
 def need(v,m):
  if not v:raise ValueError(m)
 stem=f'phase/{seq}/{phase}';is_format=entry in roots
 # Assets are source input pages, retained whole for every actual endpoint.
 for a in(0x5cd000,0x5e3000,0x5e9000):
  before=records.data(stem+f'/extra-before/{a}.bin');after=records.data(stem+f'/extra-after/{a}.bin');need(len(before)==4096 and before==after,'Complete immutable additional source page carried through this actual phase');counts['extra_whole_page_endpoint_relations']+=2
 eventraw=records.data(stem+'/formatting/events.bin');eventn=words(records.data(stem+'/formatting/count.bin'))[0];need(len(eventraw)==eventn*2244 and eventn==(6 if is_format else 0),'Exactly current-root six genuine cdecl boundaries, other roots transparent')
 sides=[]
 if is_format:
  r=roots[entry]
  for i in range(6):
   b=eventraw[i*2244:(i+1)*2244];h=words(b,0,16);cpu=words(b,64,10);f=words(b,644,8);need(h[:4]==(1,i,entry,i)and h[6]==tid and cpu[9]==h[4]and h[7]==(0x780264a9,0x780012b3,0x78022b9a)[i//2],'Genuine named loaded provider and source root cdecl observation')
   strings=[]
   for j in range(4):
    q=676+j*136;p,n=words(b,q,2);v=b[q+8:q+8+n];need(n<=128 and(not p or n and v[-1]==0),'Full actual source input string');strings.append(dict(pointer=p,bytes_hex=v.hex()))
   row=dict(sequence=seq,phase=phase,root=entry,index=i,kind=i,header=list(h),CPU=list(cpu),frame32_hex=b[644:676].hex(),FX512_hex=b[104:616].hex(),ENV28_hex=b[616:644].hex(),strings=strings,owned_hex=b[1220:1220+h[15]].hex(),original_source_cleanup_after_RET_captured=False)
   artifacts['cdecl'].append(row);sides.append((h,cpu,f,b));counts['format_cdecl_boundaries']+=1
  for k,(pc,ret,nargs)in enumerate([(0x4dea15,0x4dea1b,2),(0x4deab1,0x4deab7,1),(0x4dead1,0x4dead7,4)]):
   h,c,f,b=sides[2*k];q,d,g,a=sides[2*k+1];need(h[8]==q[8]==pc and f[0]==ret and d[9]==ret and c[4]+4==d[4]and f[1:nargs+1]==g[:nargs]and all(c[j]==d[j]for j in(3,5,6,7)),'Actual complete cdecl return/frame/callee-saved relation');counts['format_cdecl_frames']+=1
  h,c,f,b=sides[0];q,d,g,a=sides[1];need(f[1:3]==(r['filename'],0x2e)and d[0]==0 and b[104:644]==a[104:644],'Actual default suffix-search NULL and complete FP/ENV conservation')
  mh,mc,mf,mb=sides[2];rh,rc,rf,rb=sides[3];sh,sc,sf,sb=sides[4];th,tc,tf,tb=sides[5]
  filename=bytes.fromhex(artifacts['cdecl'][-6]['strings'][0]['bytes_hex']);need(filename==r['filename_bytes']and mf[1]==len(filename)+3 and sf[1:4]==(rc[0],0x5e37f0,r['filename']),'Actual filename-derived request and sprintf arguments')
  need(bytes.fromhex(artifacts['cdecl'][-2]['strings'][0]['bytes_hex'])==b'%s%s\0'and bytes.fromhex(artifacts['cdecl'][-2]['strings'][1]['bytes_hex'])==filename and bytes.fromhex(artifacts['cdecl'][-2]['strings'][2]['bytes_hex'])==b'.zrd\0','Actual full finite %s%s/filename/suffix input domain')
 n=words(records.data(stem+'/formatting/owner-count.bin'))[0];need(n==len(formats)+(1 if is_format else 0),'Actual persistent format owner occurrences grow only at selected normal call')
 for i in range(n):
  base=stem+f'/formatting/owner/{i}';meta=words(records.data(base+'/meta.bin'),0,16);initial=records.data(base+'/initial.bin');final=records.data(base+'/bytes.bin');need(meta[:2]==(1,i)and len(initial)==len(final)==meta[6]and meta[4]<=meta[6]<=1024,'Complete genuine owned allocation capacity')
  if i in formats:need((meta,initial,final)==formats[i],'Full formatting owner metadata/initial/final byteflow persists through every later root');counts['format_owner_phase_relations']+=1;continue
  need(is_format and meta[2:4]==(entry,0x4deab1)and meta[4]==mf[1]and meta[5]==rc[0]and meta[7]==rh[14],'New actual source malloc occurrence')
  ledger=records.data(stem+'/api-ledger.bin');api=words(ledger,meta[7]*104,26);need(api[24]==0 and api[10]==meta[5]and api[20]==meta[8]and api[22]==meta[9]and meta[4]<=meta[9]<=meta[6],'Actual HeapAlloc request/result/heap attribution')
  need(initial==records.data(stem+f'/api-initial/{meta[7]}/bytes.bin')and words(records.data(stem+f'/api-initial/{meta[7]}/size.bin'))==(meta[6],),'Complete actual API-return initial input')
  output=r['filename_bytes'][:-1]+b'.zrd\0';need(final==output+initial[len(output):]and tc[0]==len(output)-1 and rb[1220:1220+meta[6]]==initial and tb[1220:1220+meta[6]]==final,'Actual finite formatter result and full untouched backing tail')
  need(words(page(data,r['object']&~4095,True),(r['object']&4095)+4)==(meta[5],),'Actual literal formatting owner publication');formats[i]=(meta,initial,final);artifacts['format_owners'].append(dict(sequence=seq,phase=phase,index=i,root=entry,meta=list(meta),initial_hex=initial.hex(),final_hex=final.hex()));counts['format_owners']+=1
 if is_format:
  meta=records.data(stem+'/CRT-image/metadata.bin');need(len(meta)%12==0,'Complete loaded CRT region metadata');pages=words(meta,0,len(meta)//4);need([pages[i]for i in range(0,len(pages),3)]==list(range(0x78000000,0x78040000,4096)),'Actual64 current readable original CRT image pages')
  for i in range(0,len(pages),3):
   a=pages[i];before=records.data(stem+f'/CRT-image/before/{a}.bin');after=records.data(stem+f'/CRT-image/after/{a}.bin');need(len(before)==len(after)==4096 and pages[i+2]==0x1000000,'Whole current CRT page and MEM_IMAGE identity');counts['format_current_CRT_page_endpoints']+=2
   artifacts['CRT_pages'].append(dict(sequence=seq,phase=phase,root=entry,page=a,protection=pages[i+1],type=pages[i+2],BEFORE_sha256=hashlib.sha256(before).hexdigest(),AFTER_sha256=hashlib.sha256(after).hexdigest(),whole_bytes_retained=True))
 n=words(records.data(stem+'/mixed/owner-count.bin'))[0];need(n==len(mixed)+(3 if entry==0x4e1ca0 else 0),'Actual mixed owners grow only in selected normal root')
 current=[]
 for i in range(n):
  base=stem+f'/mixed/owner/{i}';meta=words(records.data(base+'/meta.bin'),0,17);initial=records.data(base+'/initial.bin');final=records.data(base+'/bytes.bin');need(meta[:3]==(1,i,0x4e1ca0)and len(initial)==len(final)==meta[8]and meta[4]<=meta[8]<=1024,'Full actual mixed source owner metadata/backing')
  if i in mixed:need((meta,initial,final)==mixed[i],'Complete mixed live owner identity/initial/final persists across later roots');counts['mixed_owner_phase_relations']+=1;continue
  need(entry==0x4e1ca0 and meta[9:11]==(meta[3]+5,meta[4]),'Actual game allocation CALL+5 return and source request frame')
  api=words(records.data(stem+'/api-ledger.bin'),meta[6]*104,26);need(api[24]==0 and api[10]==meta[7]and api[4]+104==meta[5]and meta[4]<=api[22]<=meta[8]and api[25]==0x78001385,'Actual sourceMFC/CRT/HeapAlloc frame/result')
  need(initial==records.data(stem+f'/api-initial/{meta[6]}/bytes.bin'),'Actual initial backing captured before guest stores');current.append((meta,initial,final));mixed[i]=(meta,initial,final);counts['mixed_owners']+=1
 if entry==0x4e1ca0:
  need([(m[3],m[4])for m,a,b in current]==[(0x49cc8d,12),(0x4e5325,24),(0x4e535b,24)],'Actual reached source12/24/24 allocations')
  inner,header,sentinel=current;stores=[[(0x49cc95,0,inner[0][7]),(0x49cc97,4,inner[0][7])],[(0x4e532a,4,0),(0x4e532d,20,1),(0x4e5339,0,0),(0x4e5343,8,0)],[(0x4e5360,4,header[0][7]),(0x4e5363,20,0),(0x4e5372,0,sentinel[0][7]),(0x4e5381,8,sentinel[0][7])]]
  for(m,a,b),writes,(pc,field)in zip(current,stores,[(0x49cc9a,0x60b750),(0x4e5334,0x60b7d4),(0x4e5366,0x60b764)]):
   predicted=bytearray(a)
   for wp,off,v in writes:struct.pack_into('<I',predicted,off,v)
   need(predicted==b and words(page(data,field&~4095,True),field&4095)==(m[7],),'Complete actual MFC byteflow from initial plus literal ten stores and three publications');artifacts['mixed_owners'].append(dict(sequence=seq,phase=phase,root=entry,meta=list(m),initial_hex=a.hex(),final_hex=b.hex(),stores=[dict(PC=wp,offset=off,width=4,value=v)for wp,off,v in writes],publication_PC=pc,publication_address=field));counts['mixed_owned_stores']+=len(writes);counts['mixed_publications']+=1
  need(words(page(data,0x60b000),0x7d0,2)==(0,0)and words(page(data,0x60b000,True),0x7d0,2)==(1,header[0][7]),'Genuine mixed BEFORENULL shared header/counter and literal AFTER publication')
  raw=records.data(stem+'/fs-events.bin');game=[raw[i:i+1216]for i in range(0,len(raw),1216)if words(raw,i+8)[0]<0x78000000];need(len(game)==6,'Two complete actual mixed game FS frames');prior=None;active=[];outer=None
  for i,(b,(pc,kind))in enumerate(zip(game,[(0x4e5297,0),(0x4e529e,1),(0x4e2197,0),(0x4e219e,1),(0x4e22cd,2),(0x4e539d,2)])):
   h=words(b,0,8);c=words(b,32,10);d=words(b,72,10);rb=b[112:124];ra=b[124:136];need(h[:4]==(1,entry,pc,kind)and c[9]==d[9]==pc and rb==ra and all(c[j]==d[j]for j in range(9)if not(kind==0 and j==0))and b[136:648]==b[648:1160]and b[1160:1188]==b[1188:1216],'Whole actual FS CPU/FX/ENV/12B instruction relation')
   if prior is not None:need(h[4]==prior,'Complete actual nested sourceFS chain')
   if kind==0:need(h[4]==h[5]==d[0],'Actual FS predecessor read');outer=h[4]if outer is None else outer
   elif kind==1:need(h[5]==c[4]==h[6]and h[7]==1 and words(rb,0,3)==(h[4],0x5b956c if pc==0x4e529e else 0x5b90fb,0xffffffff),'Actual installed source12B scope');active.append(h[6])
   else:need(active and h[4]==active.pop()and h[5]==c[1]and h[6]==h[4]and h[7]==1 and words(rb)[0]==h[5],'Actual LIFO frame restore')
   prior=h[5];artifacts['mixed_FS'].append(dict(sequence=seq,phase=phase,index=i,header=list(h),CPU_before=list(c),CPU_after=list(d),record12_hex=rb.hex(),FX_before_hex=b[136:648].hex(),FX_after_hex=b[648:1160].hex(),ENV_before_hex=b[1160:1188].hex(),ENV_after_hex=b[1188:1216].hex()));counts['mixed_FS_records']+=1
  need(not active and prior==outer,'Actual mixed hostFS restored')
  raw=records.data(stem+'/lockit-snapshots.bin');cps=[]
  for i in range(6):
   b=raw[i*12988:(i+1)*12988];h=words(b,0,16);c=words(b,64,10);f=words(b,644,8);cs=words(b,676,6);depth=0 if i in(0,1,5)else 1
   need(h[:4]==(1,i,entry,i)and h[6:9]==(tid,2,0x60b668)and h[13:15]==(0x7810a290,0x7810a350)and h[10:12]==((0,0)if i<3 else(header[0][7],1)),'Authentic current loadedCP/object/initialheader/allocatedheader identity')
   need(c[9]=={0:0x7810a290,1:targets[0x78146198],2:0x7810a311,3:0x7810a350,4:targets[0x78146184],5:0x7810a364}[i]and cs==(0xffffffff,0xfffffffe if depth else 0xffffffff,depth,tid if depth else 0,0,0x020007d0),'Actual API/source preepilogue/preRET and completeCS24 ownership')
   need(b[700+4096+0x640:700+4096+0x658]==b[676:700],'Actual whole loadedprovider CS-page joins');cps.append((h,c,f,b));artifacts['mixed_CP'].append(dict(sequence=seq,phase=phase,index=i,header=list(h),CPU=list(c),frame32_hex=b[644:676].hex(),CS24_hex=b[676:700].hex(),FX512_hex=b[104:616].hex(),ENV28_hex=b[616:644].hex(),pages_sha256=[hashlib.sha256(b[700+j*4096:700+(j+1)*4096]).hexdigest()for j in range(3)]));counts['mixed_Lockit_snapshots']+=1
  h,c,f,b=cps[0];_,a,g,_=cps[1];_,r,g2,_=cps[2];_,d,f2,_=cps[3];_,l,g3,_=cps[4];_,z,g4,_=cps[5]
  need(c[1]==d[1]==c[4]+48==d[4]+48 and f[0]==0x4e5315 and f2[0]==0x4e538f and a[4]==c[4]-16 and g[:2]==(0x7810a311,0x78145640)and r[4]==c[4]-8 and l[4]==d[4]-8 and g3[:2]==(0x7810a364,0x78145640)and z[4]==d[4],'Actual literal+44caller/+48entered scratch and bounded API-return geometry');counts['mixed_API_frames']+=2
 if entry==0x4b64f0:
  before=page(data,0x5e8000);after=page(data,0x5e8000,True);observed=bytearray(before)
  for a,v in[(0x5e886c,0x7f7fffff),(0x5e8870,0x40400000),(0x5e8874,0x40c00000),(0x5e8878,0x3f800000),(0x5e887c,0),(0x5e888c,0x42480000),(0x5e8890,0)]:need(words(after,a&4095)==(v,),'Seven literal original scalar stores');struct.pack_into('<I',observed,a&4095,v)
  inputs=[];results=[]
  for a,dst in[(0x5c93d0,0x5e8880),(0x5c93d8,0x5e8884),(0x5c93e0,0x5e8888)]:inputs.append(dict(address=a,source_input_hex=page(data,0x5c9000)[a&4095:(a&4095)+8].hex()));results.append(dict(address=dst,actual_F32_hex=after[dst&4095:(dst&4095)+4].hex()));observed[dst&4095:(dst&4095)+4]=after[dst&4095:(dst&4095)+4]
  need(after==observed,'Whole cosine output page changed only at ten physically decoded source store cells; trigonometric values retained as observations')
  c=words(data,36,10);d=words(data,76,10);need(d[0]==0 and all(c[j]==d[j]for j in(1,2,3,5,6,7))and d[4]==c[4]+4,'Original FCOS leaf literal GPR and RET geometry')
  fx1=data[116:628];fx2=data[628:1140];need(fx1[24:32]==fx2[24:32]and fx1[160:]==fx2[160:],'Actual complete nonx87 state remains conserved; latentST/status retained separately')
  artifacts['cosine'].append(dict(sequence=seq,phase=phase,CPU_before=list(c),CPU_after=list(d),FX_before_hex=fx1.hex(),FX_after_hex=fx2.hex(),ENV_before_hex=data[2164:2192].hex(),ENV_after_hex=data[2192:2220].hex(),inputs=inputs,results=results,host_cos_expected_used=False,AFTER_as_source_seed=False));counts['cosine_phases']+=1;counts['cosine_observed_results']+=3
def cleanup(records,seq,formats,mixed,counts):
 def need(v,m):
  if not v:raise ValueError(m)
 need(words(records.data(f'cleanup/{seq}/formatting-owner-count.bin'))==(len(formats),)and len(formats)==4,'Four genuine whole formatting owner cleanup occurrences')
 for i,(m,a,b)in formats.items():
  stem=f'cleanup/{seq}/formatting/{i}';need(words(records.data(stem+'/meta.bin'),0,16)==m and records.data(stem+'/before.bin')==b and words(records.data(stem+'/returned.bin'))==(1,),'Actual source free returns after whole final formatting backing capture');counts['format_source_free_returns']+=1
 need(words(records.data(f'cleanup/{seq}/mixed-owner-count.bin'))==(len(mixed),)and len(mixed)==3,'Three genuine whole MFC mixed cleanup occurrences')
 for i,(m,a,b)in mixed.items():
  stem=f'cleanup/{seq}/mixed/{i}';need(words(records.data(stem+'/meta.bin'),0,17)==m and records.data(stem+'/before.bin')==b and words(records.data(stem+'/returned.bin'))==(1,),'Actual MFC825 return after whole final backing capture');counts['mixed_MFC825_free_returns']+=1
