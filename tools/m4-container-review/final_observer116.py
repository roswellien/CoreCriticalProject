"""Independent persistent MFC source/frame/owner/cleanup observations.

The parent interpreter starts once from genuine bootstrap BEFORE. Every new
frame, import and store witness is computed from literal original instructions.
Actual typed API scalars and acquired byte vectors remain bounded leaf inputs.
"""
from pathlib import Path
import importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-onexit-review'))
import provider_bridge as B
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
S=load('container116_provider_observation',ROOT/'tools/m4-container-review/string_observer116.py')
COUNTS=S.COUNTS;ROWS=S.ROWS
from exact_equal import equal
need=S.need;S.equal=equal
from event_model import ContainerEvents
class Observer(S.Observer):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  self.mfc=[];self.mfc_imports=[];self.mfc_stores=[];self.free_active=None
  self.specs=json.loads(self.pin(ROOT/'reports/m4-mfc-source/allocation-contracts-r4/allocation-inputs.json').read_bytes())
  self.fs_specs=json.loads(self.pin(ROOT/'reports/m4-fs-source/allocation-interface-r1/allocation-inputs.json','a3fb27e6f16c12bbc7499c912415b2c294d74e97c7600dbaeb3be4770ab492ff').read_bytes())
  self.specs+=self.fs_specs
  interface=ROOT/'reports/m4-container-source/allocation-interface-r1'
  self.new_allocation_specs=json.loads(self.pin(interface/'allocation-inputs.json').read_bytes());self.specs+=self.new_allocation_specs
  borrowed=json.loads(self.pin(interface/'borrowed-constructor-inputs.json').read_bytes());zero_frees=json.loads(self.pin(interface/'nullfree-inputs.json').read_bytes());vectors=json.loads(self.pin(interface/'vector-endpoints.json').read_bytes());stores=[]
  for row in vectors:
   for pc,address,kind in((row['publication_PC'],row['publication'],1),(row['end_PC'],row['end_address'],2),(row['capacity_PC'],row['capacity_address'],3)):
    stores.append(dict(root=row['root'],pc=pc,address=address,kind=kind,CALL_pc=row['CALL_pc']))
   for i,item in enumerate(row['additional_empty_pointer_fields']):stores.append(dict(root=row['root'],pc=item['PC'],address=item['address'],kind=4+i,CALL_pc=row['CALL_pc']))
  self.container_tail_projections=0;self.container=ContainerEvents(self,borrowed,zero_frees,stores)
  accesses=json.loads(self.pin(ROOT/'reports/m4-fs-source/allocation-interface-r1/shared-owner-accesses.json').read_bytes())
  self.fs_allowed={(r['root'],r['pc'],r['bytes'],r['owner_root'],r['owner_CALL_pc'],r['owner_offset'],r['write'])for r in accesses}
 def string_event(self,m,event,data):
  super().string_event(m,event,data);self.mfc_event(m,event,data)
 def mfc_event(self,m,event,data):
  if self.container.event(m,event,data):return
  if event=='control'and data['op']=='jmp'and data['site']==0x5abd26:
   need(data['target']==0x5f401ea0 and m.call_stack and m.call_stack[-1][0]==0x5abd26,'Genuine original ordinal823 thunk tail and current saved CALL frame')
   frame=m.call_stack[-1]
   # Only source frame naming changes at the already executed original JMP.
   # Site, physical stack, return, saved registers and whole machine stay literal.
   m.call_stack[-1]=(0x5f401ea0,)+frame[1:];COUNTS['declared_MFC_tail_frame_entry_projections']+=1
   sourceframe=m.reg('esp');site=frame[3];request=int.from_bytes(m.bytes(sourceframe+4,4),'little')
   spec=next(r for r in self.specs if r['root']==self.root and r['CALL_pc']==site)
   need(spec['requested_size']==request and frame[1]==sourceframe,'Literal original root/site/request and cdecl entry frame')
   words=[1,len(self.mfc),self.root,0x5f401ea0,site,sourceframe,int.from_bytes(m.bytes(sourceframe,4),'little'),request,0,0,0,0,0,0,0,0,0,0,0,0,0,0,m.reg('ecx'),0,0,0,0,0,0,0,0,0]
   self.mfc.append(dict(words=words,spec=spec))
  if event=='read-after'and data['domain']=='source':
   pc=data['pc'];address=data['address'];value=data['value'];size=data['bytes']
   if size==4 and (pc,address)==(0x5abd26,0x5bb4bc):
    need(value==0x80000337,'Retained raw ordinal823 source import');self.mfc_imports.append((1,len(self.mfc),self.root,pc,address,value,0x5f401ea0,0))
   elif size==4 and (pc,address)==(0x5f401ea1,0x5f49814c):
    w=self.mfc[-1]['words'];need(not w[21]and value==0x78001498,'Retained raw named malloc input');w[8:11]=[value,0x780012b3,pc];self.mfc_imports.append((1,w[1],w[2],pc,address,value,0x780012b3,1))
   elif size==4 and (pc,address)==(0x5f401ead,0x5f498970):
    w=self.mfc[-1]['words'];need(not w[21]and value==0xffffffff,'True literal and post-loader handler');w[14:16]=[pc,value];self.mfc_imports.append((1,w[1],w[2],pc,address,value,value,3))
   elif size==4 and (pc,address)==(0x5f401786,0x5f498148):
    need(self.free_active is not None and value==0x7800138a,'Retained raw named free input');w=self.free_active['words'];w[28:30]=[value,0x78001390];self.mfc_imports.append((1,w[1],w[2],pc,address,value,0x78001390,2))
  if event=='control'and data['op']=='call'and data['site']==0x5f401eb5:
   w=self.mfc[-1]['words'];frame=m.reg('esp');request=int.from_bytes(m.bytes(frame+4,4),'little')
   need(data['target']==m.reg('ebx')==w[9]==0x780012b3 and frame==w[5]-24 and int.from_bytes(m.bytes(frame,4),'little')==0x5f401eb7 and request==w[7],'Original CALL EBX exact source target/argument/return frame')
   w[11:14]=[data['site'],frame,request]
  if event=='write-after'and data['domain']=='source':
   pc=data['pc'];address=data['address'];size=data['bytes'];value=data['value'];record=None;kind=0
   for candidate in self.mfc:
    w=candidate['words']
    if w[16]and w[16]<=address and address+size<=w[16]+w[7]:record=candidate;kind=1;break
    if candidate['spec']not in self.fs_specs and w[2]==self.root and w[21]and size==4 and value==w[16]and address==candidate['spec']['publication']:record=candidate;kind=2;break
   if record:
    w=record['words']
    if w[2]!=self.root:
     need((self.root,pc,size,w[2],w[4],address-w[16],True)in self.fs_allowed,'Exact literal cross-root source owner/PC/requested offset')
     COUNTS['exact_FS_prior_owner_source_stores']+=1
    self.mfc_stores.append((1,w[1],w[2],pc,address,size,value,kind));w[24]+=size if kind==1 else 0;w[23]+=int(kind==2)
   if size==4:
    for spec in self.fs_specs:
     if spec['root']!=self.root or spec['publication_PC']!=pc:continue
     candidate=next((r for r in self.mfc if r['words'][2]==spec['root']and r['words'][4]==spec['CALL_pc']),None)
     if not candidate or candidate['words'][16]!=value:continue
     w=candidate['words'];expected=spec['publication'];parent=spec['publication_owner']
     if parent:
      earlier=next(r for r in self.mfc if r['words'][2]==parent['root']and r['words'][4]==parent['CALL_pc']);expected=earlier['words'][16]+parent['offset']
     need(address==expected and w[23]==0,'Source-established dynamic/static FS publication and exact earlier owner')
     w[23]+=1;COUNTS['exact_FS_primary_publications']+=1
  if event=='returned'and data['caller']:
   entry=data['caller'][0];result=m.reg('eax');frame=data['frame']
   if entry==0x780012b3 and self.mfc and not self.mfc[-1]['words'][21]:
    w=self.mfc[-1]['words'];need(frame==w[12]and result,'Genuine successful original malloc return')
    owner=m.responses.allocations[-1];need(owner['kind']==4 and owner['guest']==result and owner['requested']==w[7],'Actual typed HeapAlloc carries the literal MFC request')
    w[16:21]=[result,owner['native'],owner['generation'],owner['extent'],result]
   elif entry==0x5f401ea0:
    w=self.mfc[-1]['words'];need(frame==w[5]and result==w[20]==w[16]and result,'Original positive allocator returned its private malloc result');w[21]=1
   elif entry==0x5f401782:
    need(self.free_active is not None,'One genuine original825 cleanup frame');w=self.free_active['words'];owner=next(a for a in m.responses.allocations if a['generation']==w[18]);need(frame==w[26]and not owner['live'],'Original825 RET follows actual source free/unmap');w[30]=1;self.free_active=None
  if event=='control'and data['op']=='call'and data['site']==0x5f401786:
   need(self.free_active is not None,'Genuine sourcefree dispatch owns original825 frame');w=self.free_active['words'];frame=m.reg('esp');need(data['target']==0x78001390 and frame==w[26]-8 and int.from_bytes(m.bytes(frame+4,4),'little')==w[16]and int.from_bytes(m.bytes(frame,4),'little')==0x5f40178c,'Original825 exact CRTfree cdecl CALL frame');w[27]=frame
 def mfc_dump(self,m,responses,stage):
  stem=f'sequence-{self.seq}/{stage}/';actual=list(struct.iter_unpack('<32Q',self.a.data(stem+'mfc-allocation-witnesses.bin')))
  need(len(actual)==len(self.mfc)==50,'Exact50 genuine source allocation calls across43 MFC initializer roots')
  for observed,record in zip(actual,self.mfc):
   w=list(record['words']);owner=next(a for a in responses.allocations if a['generation']==w[18]);w[30]=int(not owner['live']);w[31]=0
   need(observed==tuple(w),stage+' entire literal32Q MFC source/owner/publication/free witness '+str((observed,w)))
   need(w[23]==1,'One literal publication field for each private source object')
   expected=[s for s in self.mfc_stores if s[1]==w[1]and s[7]==1]
   need(sum(s[5]for s in expected)==w[24]and all(w[16]<=s[4]and s[4]+s[5]<=w[16]+w[7]for s in expected),'Exact requested-byte initialization; rounded padding preserved')
   COUNTS['whole_MFC_witnesses']+=1
  need(list(struct.iter_unpack('<8Q',self.a.data(stem+'mfc-import-ledger.bin')))==self.mfc_imports,stage+' exact raw-first original MFC import/handler ledger')
  need(list(struct.iter_unpack('<8Q',self.a.data(stem+'mfc-store-ledger.bin')))==self.mfc_stores,stage+' exact literal owner/publication committed store ledger')
  need(self.a.words(stem+'mfc-store-probe.bin',8,'Q')==(0,)*8,'No pending ordinary source MFC store after returned phase')
  COUNTS['MFC_import_records']+=len(self.mfc_imports);COUNTS['MFC_literal_store_records']+=len(self.mfc_stores)
  for key,value in self.container.dump(m,stage).items():COUNTS[key]+=value
 def owners(self,m,responses,stage,expected_callbacks):
  stem=f'sequence-{self.seq}/{stage}/';summary=self.a.words(stem+'registry-summary.bin',32,'Q');locale=self.a.words(stem+'locale-summary.bin',32)
  allocations=list(struct.iter_unpack('<16Q',self.a.data(stem+'locale-allocations.bin')));sections=list(struct.iter_unpack('<16Q',self.a.data(stem+'locale-critical-sections.bin')))
  need(len(allocations)==len(responses.allocations)==70,'One real producer,19 strings and50 actual MFC private owners')
  need(sum(a.get('kind',1)==4 for a in responses.allocations)==50 and sum(a.get('kind',1)==3 for a in responses.allocations)==19,'Owner kind derives from actual literal allocation caller')
  for observed,owner in zip(allocations,responses.allocations):
   live=int(owner['live']);expected=(1,owner['guest'],owner['requested'],owner['extent'],owner['mapped'],owner['generation'],owner.get('kind',1),owner['native'],owner['native']if live else 0,live,1-live,0,summary[15]if live else self.handle,0,0,0)
   need(observed==expected,stage+' whole private owner generation/lifecycle '+str((observed,expected)))
   p=stem+'locale-allocation-'+str(owner['generation']);equal(owner['initial'],self.a.data(p+'-initial.bin'),stage+' complete actually acquired native byte vector')
   if live:
    full=m.bytes(owner['guest'],owner['mapped']);equal(full,self.a.data(p+'-expected.bin'),stage+' entire committed expected owner mirror');equal(full,self.a.data(p+'-owned-page.bin'),stage+' entire actual live guest owner page')
    if owner.get('kind',1)==1:
     vector=responses.completed_registry(m,expected_callbacks);need(summary[6:10]==(vector['begin'],vector['next'],vector['capacity'],len(expected_callbacks)),stage+' exact private ordered registry vector');COUNTS['owned_callback_entries']+=len(expected_callbacks)
   else:
    equal(self.last_owned[owner['generation']],self.a.data(p+'-expected.bin'),'Source-freed owner retains exact historical committed byte mirror');need(p+'-owned-page.bin'not in self.a.entries,'Source-free revokes actual guest mapping')
  need(len(sections)==len(responses.sections)==4,'Four actual source-initialized critical sections')
  for observed,(guest,owner)in zip(sections,responses.sections.items()):
   deleted=int(owner['deletes']>0);need(observed==(1,guest,owner['generation'],owner['enters'],owner['leaves'],owner['depth'],1,owner['deletes'],int(owner['initialized']),deleted,owner['native'],40,0,0,0,0),stage+' complete actual CS lifecycle')
  expected_counts=(sum(a['live']for a in responses.allocations),sum(a['initialized']and not a['deletes']for a in responses.sections.values()),responses.index,len(m.accesses)-self.provider_start,len(responses.growth))
  need(summary[10:15]==expected_counts,stage+' independently computed whole owner/API/source/growth counts '+str((summary[10:15],expected_counts)))
  need(summary[19:22]==(m.word(2472),m.reg('esp'),len(S.provider_research(m))),stage+' exact source PC/SP/research chronology')
  need(locale[14:19]==(summary[10],summary[11],summary[13],len(m.transports),responses.index),'Same locale/registry owner/transport counters')
  if stage=='cleaned':need(summary[4]==1 and summary[15]==0 and locale[23]==1 and locale[30]==0,'Actually released same native heap and all resources')
  else:need(summary[4]==0 and summary[15]==self.handle and locale[30]==1,'Privately owned same live actual heap')
  COUNTS['whole_owner_lifecycle_dumps']+=1
 def finish(self,m,responses,roots,G):
  stem=f'sequence-{self.seq}/';selected_count=responses.index;self.handle=self.a.words(stem+'selected/registry-summary.bin',32,'Q')[15]
  self.prefix(m);self.owners(m,responses,'selected',roots);self.ledger(m,responses,'selected');self.string_dump(m,responses,'selected');self.mfc_dump(m,responses,'selected')
  observed_replays=self.a.words(stem+'growth-replay-count.bin',1)[0];vector=responses.completed_registry(m,roots);initial_growths=len(responses.growth);expected=list(roots)
  old_roots=json.loads(self.pin(ROOT/'reports/m4-onexit-batch-recovery/recovery-r3/registration-roots.json').read_bytes());replayed=next(r['registration']['callback']for r in old_roots if r['entry']==0x410210)
  initial_used=vector['next']-vector['begin'];capacity_steps=None;first_query_capacity=None;n=0
  while len(responses.growth)==initial_growths:
   need(n<512,'Original source next-growth replay finite bound');self.runtime_cpu=B.cpu(m.state);self.check(m,f'registry-replay-{88+n}-before');first_API=responses.index;m.invoke_external(0x410210,0xffffffa0,responses);expected.append(replayed);responses.completed_registry(m,expected);self.check(m,f'registry-replay-{88+n}-after');COUNTS['genuine_growth_replays']+=1;n+=1
   if first_query_capacity is None:
    queries=[f for f in responses.facts[first_API:responses.index]if f['name']=='HeapSize'];need(len(queries)==1,'One genuine first replay source msize query')
    first_query_capacity=queries[0]['words'][17];need(first_query_capacity>=initial_used and first_query_capacity%4==0,'Actual source measured SIZE_T capacity covers the exact selected callback bytes')
    capacity_steps=(first_query_capacity-initial_used)//4+1;COUNTS['actual_first_replay_msize_capacity_derivations']+=1
  need(n==observed_replays==capacity_steps and len(responses.growth)==initial_growths+1,'Measured genuine msize capacity independently derives one additional actual growth and replay count')
  grown_count=responses.index;self.owners(m,responses,'grown',expected);self.ledger(m,responses,'grown');self.string_dump(m,responses,'grown');self.mfc_dump(m,responses,'grown')
  self.last_owned={a['generation']:m.bytes(a['guest'],a['mapped'])for a in responses.allocations};self.runtime_cpu=B.cpu(m.state)
  ordered=[a for kind in(4,3,1)for a in responses.allocations if a.get('kind',1)==kind]
  for owner in ordered:
   kind=owner.get('kind',1);oldsp=m.reg('esp');oldpc=m.word(2472);m.write(oldsp-4,owner['guest'],domain='research',pc=oldpc);m.reg('esp',oldsp-4)
   if kind==4:
    record=next(r for r in self.mfc if r['words'][18]==owner['generation']);w=record['words'];need(not self.free_active and not w[25]and owner['live'],'Genuine still-live whole MFC object before original825');self.free_active=record;w[25]=0x5f401782;w[26]=m.reg('esp')-4;m.invoke_external(0x5f401782,0xffffff50,responses)
   else:m.invoke_external(0x78001390,0xffffff70 if kind==3 else 0xffffff80,responses)
   m.reg('esp',oldsp);need(not owner['live'],'Actual original source free retires its exact private generation/mapping')
  m.cpu=B.cpu(m.state)
  for guest,section in reversed(list(responses.sections.items())):
   fact=responses.facts[responses.index];w=fact['words'];need(fact['name']=='DeleteCriticalSection'and w[31]==1 and w[:2]==(1,responses.index)and w[2:8]==(0,0x7802e040,0x3446a,0,0,0)and w[8]==1 and w[9]==w[11]and w[14:17]==(1,1,section['native'])and not fact['inputs']and not fact['outputs'],'Actual cleanup typed delete identifies exact reverse source-owned CS');need(section['initialized']and section['depth']==0 and section['deletes']==0,'Balanced source CS before actual deletion');section['deletes']=1;responses.index+=1
  responses.complete();self.owners(m,responses,'cleaned',expected);self.ledger(m,responses,'cleaned');self.string_dump(m,responses,'cleaned');self.mfc_dump(m,responses,'cleaned');self.identities(stem+'cleaned/',responses.facts)
  heap=self.a.words(stem+'cleaned/heap-create-registry.bin',18,'Q');need(heap[4]==self.handle and heap[7]==0 and heap[9:11]==(1,1)and heap[12]==1 and heap[13]==0 and heap[15]==1 and heap[16]==self.handle,'Exactly one actual same full-width heap HANDLE destroy')
  COUNTS['complete116_provider_sequences']+=1;COUNTS['selected_registration_closures']+=88;COUNTS['real_producer_allocations']+=1;COUNTS['actual_MFC_allocations']+=50;COUNTS['actual_duplicate_allocations']+=19;COUNTS['actual_source_frees']+=70;COUNTS['actual_MFC_source_frees']+=50;COUNTS['successful_actual_growth']+=len(responses.growth);COUNTS['actual_CS_deletes']+=4;COUNTS['actual_heap_destroys']+=1
  remaining=sorted(set(self.index)-self.seen);need(remaining==['registry-bootstrap-before'],'Every provider checkpoint independently predicted '+str(remaining));COUNTS['true_bootstrap_BEFORE_inputs']+=1
  COUNTS['declared_container_thunk_frame_entry_projections']+=self.container_tail_projections
  COUNTS['actual_normal_null_frees']+=5;COUNTS['actual_borrowed_constructors']+=3;COUNTS['source_unchanged_acquired_vector_extents']+=5
  ROWS.append(dict(level=self.level,sequence=self.seq,selected_API_count=selected_count,grown_API_count=grown_count,cleaned_API_count=responses.index,compared_checkpoints=len(self.seen),actual_MFC_allocations=50,all_resources_released=True,actual_post_HeapDestroy_identity=True))
def configure(G,numeric,archive,seq,level,pin):
 # Add owner classification only after the literal source allocation happened.
 S.install_responses();parent=B.R.ActualResponses
 if not getattr(B.R,'mfc_review_derived',False):
  class MfcResponses(parent):
   def __call__(self,m,target):
    mfc=any(f[0]==0x5f401ea0 for f in m.call_stack);count=len(self.allocations);super().__call__(m,target)
    if len(self.allocations)>count and mfc:self.allocations[-1]['kind']=4
  B.R.ActualResponses=MfcResponses;B.R.mfc_review_derived=True
 S.Observer=Observer;return S.configure(G,numeric,archive,seq,level,pin)
def begin(m):S.begin(m)
def end(m):S.end(m)
def finish(m,responses,roots,G):S.finish(m,responses,roots,G)
