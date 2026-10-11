"""Actual chronological widget/FPS/GDI observations; no source execution seed."""
import hashlib,struct
ROOTS=(0x40e250,0x40ef50,0x40f000,0x479590,0x5a3c30,0x5a3ff0,0x5a66f0)
PHASES=(15,16,17,47,134,135,136)
GDI_BYTES=287444;FPS_BYTES=550180
def w(b,o=0,n=1):return struct.unpack_from('<'+'I'*n,b,o)
def need(v,m):
 if not v:raise ValueError(m)
def descriptor(raw,i,counts):
 need(len(raw)==40 and w(raw)[0]==i,'Actual selector record occurrence')
 selectors=w(raw,4,3);rows=[]
 for j in range(3):
  b=raw[16+j*8:24+j*8];lo,base_low,base_mid,access,flags,base_hi=struct.unpack('<HHBBBB',b);base=base_low|(base_mid<<16)|(base_hi<<24);limit=lo|((flags&15)<<16);effective=(limit<<12)|4095 if flags&128 else limit
  need(selectors[j]!=0 and base==0 and effective==0xffffffff and access&128 and access&16 and not(access&8)and access&2 and flags&64,'Actual flat readable/writable32 data descriptor with full effective source access coverage')
  rows.append(dict(selector=selectors[j],raw_hex=b.hex(),base=base,effective_limit=effective));counts['widget_actual_flat_segment_relations']+=1
 return rows
def pair_position(index,side):
 need(side==index%2,'Every actual GDI boundary alternates entry then return; no missing or trailing entry')
def pair_extent(sides,returns):
 need(sides==2*returns,'Every actual GDI entry has exactly one return')
class Observer:
 def __init__(self,records,contract,whole,fixed,bindings,counts,targets,fps_target,transition):
  self.transition=transition;self.records=records;self.contract=contract;self.whole=whole;self.fixed=fixed;self.extras=[a for a in self.whole if a not in self.fixed];self.bindings=bindings;self.counts=counts;self.targets=targets;self.fps_target=fps_target
  need(len(self.whole)==69 and len(self.fixed)==43 and len(self.extras)==26 and len(set(self.whole))==69,'Complete current observed source69 geometry')
  self.events=[];self.fs=[];self.fps=[];self.phases=[];self.registry=[];self.page_relations=[];self.lifetimes=[];self.allocations=[];self.begin_sequence(0)
 def begin_sequence(self,sequence):
  self.sequence=sequence;self.created=[];self.live={};self.stock={};self.previous=None;self.previous_CRT=None
 def pages(self,raw,stem,side):
  off=2276 if side=='before' else 178404;pages={a:raw[off+i*4096:off+(i+1)*4096]for i,a in enumerate(self.fixed)}
  for a in self.extras:pages[a]=self.records.data(stem+f'extra-{side}/{a}.bin')
  need(set(pages)==set(self.whole)and all(len(x)==4096 for x in pages.values()),'Every complete current source69 page at actual root endpoint');self.counts['widget_whole_source_page_endpoints']+=69;return pages
 def phase(self,raw,sequence,phase,entry):
  stem=f'phase/{sequence}/{phase}/';before=self.pages(raw,stem,'before');after=self.pages(raw,stem,'after');new=entry in ROOTS
  for address in self.whole:
   a,z=before[address],after[address]
   if self.previous is not None and address!=0x20001000:
    if phase in(13,14):self.transition.relation(self.previous[address],a,address,phase,sequence)
    else:need(self.previous[address]==a,'Actual whole chronological nonstack source page carry '+hex(address))
    self.counts['widget_whole_nonstack_carried_page_relations']+=1
   self.page_relations.append(dict(sequence=sequence,phase=phase,root=entry,page=address,BEFORE_sha256=hashlib.sha256(a).hexdigest(),AFTER_sha256=hashlib.sha256(z).hexdigest()))
  self.previous=after
  registry=w(self.records.data(stem+'registry-before-meta.bin'),0,4);backing=self.records.data(stem+'registry-before-backing.bin');need(registry[0]and registry[0]<=registry[1]and registry[1]-registry[0]<=registry[2]<=512 and len(backing)==registry[2],'Entire actual registry BEFORE capacity/backing')
  crt={}
  for side in('before','after'):
   pages={a:self.records.data(stem+f'CRT-{side}/{a}.bin')for a in range(0x78000000,0x78040000,4096)};need(all(len(b)==4096 for b in pages.values()),'Every full actual CRT provider endpoint page');crt[side]=pages;self.counts['widget_whole_CRT_phase_page_endpoints']+=64
   for a in set(self.whole)&set(pages):need(pages[a]==(before if side=='before'else after)[a],'Overlapping complete source/CRT endpoint bytes agree')
  if phase in(13,14):
   need(self.previous_CRT is not None,'Actual immediately prior complete CRT endpoint')
   for address in crt['before']:
    self.transition.relation(self.previous_CRT[address],crt['before'][address],address,phase,sequence);self.counts['widget_exact_MFC_CRT_transition_page_relations']+=1
  self.previous_CRT=crt['after']
  need(w(crt['before'][0x78037000],0x888)[0]==registry[1]and w(crt['before'][0x78037000],0x88c)[0]==registry[0]and w(crt['before'][0x78035000],4)[0]==registry[3],'Current loaded CRT fields authenticate actual registry BEFORE')
  self.registry.append(dict(sequence=sequence,phase=phase,root=entry,BEFORE_metadata=list(registry),BEFORE_backing_hex=backing.hex()))
  if new:
   n=w(self.records.data(stem+'api-count.bin'))[0];ledger=self.records.data(stem+'api-ledger.bin');need(n<=256 and len(ledger)==n*104,'Entire bounded current selected-root provider API ledger')
   for i in range(n):
    api=ledger[i*104:(i+1)*104];v=w(api,0,26)
    if v[24]==0 and v[10]:
     size=w(self.records.data(stem+f'api-initial/{i}/size.bin'))[0];initial=self.records.data(stem+f'api-initial/{i}/bytes.bin');final=self.records.data(stem+f'api-final/{i}/bytes.bin');need(v[22]<=size<=1024 and len(initial)==len(final)==size,'Actual HeapAlloc requested extent and full measured capacity/initial/final backing; role intentionally unclassified')
     self.allocations.append(dict(sequence=sequence,phase=phase,root=entry,API_index=i,API_entry_CPU=list(v[:10]),API_return_CPU=list(v[10:20]),arguments=list(v[20:24]),kind=v[24],saved_return=v[25],pointer=v[10],measured_HeapSize_capacity=size,initial_hex=initial.hex(),final_hex=final.hex(),source_owner_role='unclassified',source_byteflow_proven=False));self.counts['widget_actual_initial_heap_allocations']+=1
  count=w(self.records.data(stem+'widget-count.bin'))[0];blob=self.records.data(stem+'widget-snapshots.bin');segments=self.records.data(stem+'widget-segments.bin');need(count<=384 and count%2==0 and len(blob)==count*GDI_BYTES and len(segments)==count*40 and(new or count==0),'Actual bounded selected-root GDI observation extent')
  def actual(snap,address,n):
   page=address&~4095;need(page in self.whole and(address&4095)+n<=4096,'Observed complete GDI/FPS source extent');start=4820+self.whole.index(page)*4096+(address&4095);return snap[start:start+n]
  paired=[];returns_before=self.counts['widget_actual_stdcall_RETURN_relations']
  for i in range(count):
   snap=blob[i*GDI_BYTES:(i+1)*GDI_BYTES];h=w(snap,0,16);cpu=w(snap,64,10);frame=snap[644:708];api=h[3]//2;side=h[3]%2;pair_position(i,side);need(api<3 and h[:3]==(1,i,entry)and h[4]==cpu[9]and h[7]==self.targets[api]and h[8]==cpu[4]and h[11]==cpu[6]and h[12]==(1,1,14)[api],'Complete genuine GDI header/CPU/named target');need(0x20001000<=cpu[4]and cpu[4]+64<=0x20002000 and frame==actual(snap,cpu[4],64)and not(cpu[8]&0x400),'Actual live stack64 and forward source domain')
   if h[14]:need(snap[708:724]==actual(snap,h[5],16),'Whole raw GDI FS frame view')
   seg=descriptor(segments[i*40:(i+1)*40],i,self.counts);row=dict(sequence=sequence,phase=phase,root=entry,index=i,API=('GetStockObject','DeleteObject','CreateFontA')[api],side=side,header=list(h),CPU=list(cpu),FX512_hex=snap[104:616].hex(),ENV28_hex=snap[616:644].hex(),frame64_hex=frame.hex(),FS_view16_hex=snap[708:724].hex(),segments=seg,raw_sha256=hashlib.sha256(snap).hexdigest(),page_sha256=[hashlib.sha256(snap[4820+j*4096:4820+(j+1)*4096]).hexdigest()for j in range(69)],source_replay_observed=False)
   if not side:
    need(cpu[9]==self.targets[api]and w(frame)[0]==(0x5a0142,0x5a0645,0x5a0751)[api],'Actual game CALL return frame');args=w(frame,4,(1,1,14)[api]);row['arguments']=list(args)
    if api==0:need(args==(10,),'Actual OEM_FIXED_FONT request')
    elif api==1:
     need(actual(snap,cpu[6]+0x258,4)==frame[4:8],'Actual DeleteObject source instance field');row['resource_origin']='owned-created'if(cpu[6],args[0])in self.live else'borrowed-stock'if self.stock.get(cpu[6])==args[0]else'unclassified';need(row['resource_origin']!='unclassified','Current resource origin derived from earlier same-instance observed acquisition')
    else:need(args==(0xfffffff6,6,0,0,500,0,0,0,0,4,0,1,2,0x5e15dc)and actual(snap,0x5e15dc,6)==b'Arial\0','All14 actual font args and whole face bytes')
   else:
    need(paired and paired[-1]['side']==0 and paired[-1]['API']==row['API'],'Actual adjacent GDI pair');a=paired[-1];need(cpu[9]==(0x5a0142,0x5a0645,0x5a0751)[api]and cpu[4]==a['CPU'][4]+4*((1,1,14)[api]+1)and h[5]==a['header'][5]and all(cpu[j]==a['CPU'][j]for j in(3,5,6,7)),'True stdcallRET/nonvolatile/hidden FS relation')
    if api==0:self.stock[cpu[6]]=cpu[0]
    elif api==2:
     need(cpu[0]!=0 and all(handle!=cpu[0]for _,handle in self.live),'Genuine finite successful font owner and no unretired alias');owner=dict(sequence=sequence,occurrence=len(self.created),phase=phase,root=entry,instance=cpu[6],handle=cpu[0],created_event=i,live=True,deleted_event=None);self.created.append(owner);self.live[(cpu[6],cpu[0])]=owner
    elif cpu[0]and a['resource_origin']=='owned-created':owner=self.live.pop((cpu[6],a['arguments'][0]));owner['live']=False;owner['deleted_event']=i
    row['BOOL_or_handle_result']=cpu[0];self.counts['widget_actual_'+row['API']+'_calls']+=1;self.counts['widget_actual_stdcall_RETURN_relations']+=1
   self.events.append(row);paired.append(row);self.counts['widget_complete_GDI_boundary_sides']+=1;self.counts['widget_whole_GDI_source_page_endpoints']+=69
  pair_extent(count,self.counts['widget_actual_stdcall_RETURN_relations']-returns_before)
  fc=w(self.records.data(stem+'fps-count.bin'))[0];fb=self.records.data(stem+'fps-snapshots.bin');fs=self.records.data(stem+'fps-segments.bin');need(fc<=8 and fc%2==0 and len(fb)==fc*FPS_BYTES and len(fs)==fc*40 and(entry==0x40f000 or fc==0),'Exact finite genuine FPS observation extent');fp=[]
  for i in range(fc):
   snap=fb[i*FPS_BYTES:(i+1)*FPS_BYTES];h=w(snap,0,16);cpu=w(snap,64,10);frame=snap[644:708];side=i%2;need(h[:5]==(1,i,entry,side,cpu[9])and h[7]==self.fps_target and h[8]==cpu[4]and h[11]==cpu[6]and h[12]==3 and not(cpu[8]&0x400),'Actual FPS full header/CPU/DF');seg=descriptor(fs[i*40:(i+1)*40],i,self.counts);dest,fmt,va=h[13:16];need(dest==cpu[6]+0x34 and fmt==0x5e1590 and 0x20001000<=va and va+64<=0x20002000,'True source FPS destination/format/va_list domain')
   need(actual(snap,fmt,16)==snap[549652:549668]and snap[549652:549656]==b'fps\0'and actual(snap,dest,512)==snap[549668:550180]and actual(snap,va,64)==snap[549588:549652],'Full FPS inputs/output view joins own source69 pages')
   if 0x20001000<=h[5]and h[5]+16<=0x20002000:need(actual(snap,h[5],16)==snap[708:724],'Actual current source FS16 view')
   else:need(snap[708:724]==bytes(16),'Unmapped FS view retained explicitly empty')
   if not side:need(cpu[9]==self.fps_target and w(frame,0,4)==(0x5a2f6e,dest,fmt,va),'Actual cdecl3 entry frame')
   else:
    a=fp[-1];need(cpu[9]==0x5a2f6e and cpu[4]==a['CPU'][4]+4 and h[5]==a['header'][5]and h[13:16]==tuple(a['header'][13:16])and all(cpu[j]==a['CPU'][j]for j in(3,5,6,7))and frame[:12]==bytes.fromhex(a['frame64_hex'])[4:16],'True FPS cdeclRET before caller cleanup')
    need(snap[104:644].hex()==a['FX512_hex']+a['ENV28_hex']and cpu[0]==3 and snap[549668:549672]==b'fps\0'and snap[549672:550180].hex()==a['destination512_hex'][8:]and snap[549588:549652].hex()==a['va64_hex'],'Genuine finite literal-string FPS effects and full FP/ENV/unused output conservation');self.counts['widget_actual_FPS_cdeclRET_relations']+=1
   row=dict(sequence=sequence,phase=phase,root=entry,index=i,side=side,header=list(h),CPU=list(cpu),FX512_hex=snap[104:616].hex(),ENV28_hex=snap[616:644].hex(),frame64_hex=frame.hex(),format16_hex=snap[549652:549668].hex(),va64_hex=snap[549588:549652].hex(),destination512_hex=snap[549668:550180].hex(),segments=seg,raw_sha256=hashlib.sha256(snap).hexdigest(),own_source_page_sha256=[hashlib.sha256(snap[4820+j*4096:4820+(j+1)*4096]).hexdigest()for j in range(69)],own_CRT_page_sha256=[hashlib.sha256(snap[GDI_BYTES+j*4096:GDI_BYTES+(j+1)*4096]).hexdigest()for j in range(64)],source_replay_observed=False);fp.append(row);self.fps.append(row);self.counts['widget_complete_FPS_boundary_sides']+=1
  if entry==0x40f000:need(fc>0,'Actual nonnull FPS path reached')
  resources=self.records.data(stem+'widget-resources.bin');need(len(resources)==len(self.created)*32,'Whole current carried font occurrence inventory')
  for j,owner in enumerate(self.created):
   h=w(resources,j*32,8);need(h[:6]==(1,j,owner['root'],owner['instance'],owner['handle'],owner['created_event'])and h[6:]==(int(owner['live']),0xffffffff if owner['live']else owner['deleted_event']),'Every source phase carries exact same resource occurrence and measured live/deleted state');self.counts['widget_resource_phase_relations']+=1
  fn=w(self.records.data(stem+'widget-fs-count.bin'))[0];fb=self.records.data(stem+'widget-fs-events.bin');need(fn<=2048 and len(fb)==fn*1224 and(new or fn==0),'Complete separate current widget FS ledger')
  for i in range(fn):
   f=fb[i*1224:(i+1)*1224];h=w(f,0,8);a=w(f,32,10);z=w(f,72,10);need(h[0]==1 and h[1]==entry and h[2]in self.bindings and h[3]==self.bindings[h[2]]['kind']and a[9]==z[9]==h[2],'Exact physical current FS binding');need(all(a[j]==z[j]for j in(1,2,3,4,5,6,7,8))and(a[0]==z[0]if h[3]else z[0]==h[4])and h[5]==(h[4]if h[3]==0 else a[4]if h[3]==1 else a[1]),'Only exact literal FS instruction CPU/head effect');need(f[112:128]==f[128:144]and f[144:656]==f[656:1168]and f[1168:1196]==f[1196:1224],'Whole FS16 frame/FX512/ENV28 conservation');self.fs.append(dict(sequence=sequence,phase=phase,root=entry,index=i,header=list(h),CPU_before=list(a),CPU_after=list(z),frame16_hex=f[112:128].hex(),FX_hex=f[144:656].hex(),ENV28_hex=f[1168:1196].hex(),source_raw=self.bindings[h[2]]['raw_bytes']));self.counts['widget_actual_FS_instruction_events']+=1
  if new:
   need(phase==PHASES[ROOTS.index(entry)],'Genuine sorted new initializer chronology');self.phases.append(dict(sequence=sequence,phase=phase,root=entry,CPU_BEFORE=list(w(raw,36,10)),CPU_AFTER=list(w(raw,76,10)),FX_BEFORE_hex=raw[116:628].hex(),FX_AFTER_hex=raw[628:1140].hex(),ENV_BEFORE_hex=raw[2164:2192].hex(),ENV_AFTER_hex=raw[2192:2220].hex(),GDI_sides=count,FPS_sides=fc,FS_events=fn));self.counts['widget_actual_root_phases']+=1
 def cleanup(self,sequence):
  raw=self.records.data(f'cleanup/{sequence}/resources.bin');need(len(raw)==len(self.created)*32,'Complete current font occurrence cleanup inventory')
  for i,owner in enumerate(self.created):
   h=w(raw,i*32,8);need(h[:6]==(1,i,owner['root'],owner['instance'],owner['handle'],owner['created_event']),'Actual same font occurrence identity')
   if owner['live']:
    c=self.records.data(f'cleanup/{sequence}/owned-font/{i}.bin');need(len(c)==1112 and w(c,0,4)==(1,i,owner['instance'],owner['handle'])and w(c,16)[0]!=0 and w(c,28)[0]==1 and h[6:]==(0,0xfffffffe),'Actual successful owned-only manual resource cleanup');owner.update(manual_cleanup_BOOL=w(c,16)[0],FX_BEFORE_hex=c[32:544].hex(),FX_AFTER_hex=c[544:1056].hex(),ENV_BEFORE_hex=c[1056:1084].hex(),ENV_AFTER_hex=c[1084:1112].hex());self.counts['widget_actual_owned_manual_DeleteObject_calls']+=1
   else:need(h[6:]==(0,owner['deleted_event']),'Actual source deletion retires exact occurrence')
   self.lifetimes.append(owner)
