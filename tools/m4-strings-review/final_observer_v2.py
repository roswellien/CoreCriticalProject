"""Read-only, exact provider observations of one persistent source machine.

API scalar and finite owned-byte witnesses are inputs. Full captured machine
checkpoints and owner dumps are comparison observations, never machine seeds.
"""
from pathlib import Path
import collections,copy,hashlib,importlib.util,json,struct,sys
import provider_bridge as B
import provider_capture as C
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-crt-locale-batch-review'))
COUNTS=collections.Counter();ROWS=[];CURRENT=None
def need(v,s):
 if not v:raise ValueError(s)
def equal(a,b,s):
 need(len(a)==len(b) and a==b,s+' '+str([(i,x,y)for i,(x,y)in enumerate(zip(a,b))if x!=y][:12]))
def load(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def provider_research(m):
 # Each selected-table Runtime dispatcher stores its own return word while
 # the provider owner is paused. Those explicit caller-frame records belong
 # to the full-game source comparison, outside the provider owner ledger.
 return [r for r in m.external_accesses if r!=(0x410a80,0x20001800,0x410a80,4,1)]
def configure(G,numeric,archive,seq,level,pin):
 global CURRENT
 stem=f'sequence-{seq}/cleaned/';index={};pages=collections.defaultdict(dict)
 for logical in archive.entries:
  if logical.startswith(stem+'registry-checkpoint-'):
   if logical.endswith('-name.bin'):index[archive.data(logical).decode()]=logical[:-9]
   elif '-page-'in logical:
    prefix,address=logical.rsplit('-page-',1);pages[prefix][int(address[:-4])]=logical
 CURRENT=Observer(archive,seq,level,pin,index,pages,numeric)
 install_responses()
 parent=getattr(G,'provider_final_base_machine',G.Machine);G.provider_final_base_machine=parent
 class Observed(parent):
  def __init__(self,*args,**kwargs):
   super().__init__(*args,**kwargs);previous=self.hook
   def hook(machine,event,data):
    if previous:previous(machine,event,data)
    CURRENT.string_event(machine,event,data)
    if event=='write-after'and data['domain']=='source'and data['address']==machine.word(B.I.BASE['fs']):CURRENT.check(machine,'locale-source-seh-'+str(len(machine.accesses))+'-after')
   self.hook=hook
  def snapshot(self,name):
   if name=='registry-producer-before':
    need(self.cursor==0x5ac3ec and self.word(2472)==0x5ac3e2,'Literal sentinel exact missing-body stop frontier')
    self.word(2472,self.cursor);COUNTS['declared_sentinel_stop_PC_projections']+=1
   super().snapshot(name)
   CURRENT.snapshot(self,name)
 G.Machine=Observed
 return CURRENT
def install_responses():
 if getattr(B.R,'strings_review_derived',False):return
 parent=B.R.ActualResponses
 class StringResponses(parent):
  def __call__(self,m,target):
   duplicate=any(f[0]==0x78010a6d for f in m.call_stack);count=len(self.allocations);super().__call__(m,target)
   if len(self.allocations)>count:self.allocations[-1]['kind']=3 if duplicate else 1
 B.R.ActualResponses=StringResponses;B.R.strings_review_derived=True
class Observer:
 def __init__(self,a,seq,level,pin,index,pages,numeric):
  self.a=a;self.seq=seq;self.level=level;self.pin=pin;self.index=index;self.pages=pages;self.numeric=numeric;self.seen=set();self.provider_start=None;self.regindex=0;self.runtime_cpu=None;self.root=0;self.strings=[];self.input_specs=json.loads(pin(ROOT/'reports/m4-strings-review/interface-r2/instruction-contracts.json').read_bytes())['inputs']
 def string_event(self,m,event,data):
  COPY={0x78002fde,0x7800366b,0x7800368c,0x78003693,0x780036a5,0x780036ad,0x780036b6}
  if event=='control'and data['op']=='call'and data['target']==0x78010a6d:
   frame=m.reg('esp');source=int.from_bytes(m.bytes(frame+4,4),'little');spec=next(r for r in self.input_specs if r['root']==self.root)
   need(spec['actual_strdup_called']and source==spec['source']and data['site']==spec['CALL_pc'],'Exact independently bound literal source string invocation')
   raw=bytes.fromhex(spec['bytes_hex']);need(m.bytes(source,len(raw))==raw,'Original input bytes at genuine BEFORE call')
   words=[1,len(self.strings),self.root,0x78010a6d,source,frame,int.from_bytes(m.bytes(frame,4),'little'),len(raw),0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,len(m.accesses),0,0,0,0,0,0,0]
   self.strings.append(dict(words=words,input=raw,reads=[],writes=[]))
  if not self.strings or self.strings[-1]['words'][17]:return
  record=self.strings[-1];w=record['words']
  if event=='control'and data['op']=='call':
   target=data['target'];frame=m.reg('esp')
   if target==0x78002f32:w[20]=frame
   if target==0x780012b3:w[21]=frame;w[9]=int.from_bytes(m.bytes(frame+4,4),'little');need(w[9]==w[7],'Literal strlen+1 actual malloc request')
   if target==0x78002fab:w[22]=frame;w[14]=int.from_bytes(m.bytes(frame+4,4),'little');need(w[14]==w[10],'Genuine actual owned destination for source strcpy')
  if event in ('read-after','write-after')and data['domain']=='source':
   row=(m.word(2472),data['address'],data['value'],data['bytes'],int(event=='write-after'))
   if not row[4]and w[4]<=row[1]<w[4]+w[7]+4:record['reads'].append(row)
   if row[4]and row[0]in COPY:
    need(row[1]==w[10]+w[16]and w[16]+row[3]<=w[7],'Exact sequential requested strcpy write, PUSH excluded');w[16]+=row[3];w[26]=row[0];w[27]=row[1];record['writes'].append(row)
  if event=='returned'and data['caller']:
   entry=data['caller'][0];result=m.reg('eax')
   if entry==0x78002f32:w[8]=result;need(result+1==w[7],'Exact literal strlen NUL-inclusive extent')
   if entry==0x780012b3:
    owned=m.responses.allocations[-1];need(owned['kind']==3 and owned['guest']==result and owned['requested']==w[7],'Exact original malloc actual HeapAlloc owner');w[10]=result;w[11]=owned['native'];w[12]=owned['generation'];w[13]=owned['extent']
   if entry==0x78002fab:w[15]=result;need(result==w[10]and w[16]==w[7]and m.bytes(result,w[7])==record['input'],'Exact complete strcpy NUL copy')
   if entry==0x78010a6d:w[17]=1;w[23]=result;w[25]=len(m.accesses);need(result==w[10]and w[15]==result,'Literal duplicate actual return association')
 def string_dump(self,m,responses,stage):
  stem=f'sequence-{self.seq}/{stage}/';actual=list(struct.iter_unpack('<32Q',self.a.data(stem+'strings-witnesses.bin')))
  need(len(actual)==len(self.strings)==16,'Exactly16 actual source calls, null descriptor root has no fabricated call')
  for n,(row,record)in enumerate(zip(actual,self.strings)):
   w=list(record['words']);owned=next(a for a in responses.allocations if a['generation']==w[12]);w[18]=int(not owned['live']);w[19]=0;w[28]=w[29]=int(owned['live'])
   need(row==tuple(w),stage+' exact32Q string ownership/source/frame/copy witness '+str((n,row,tuple(w))))
   equal(record['input'],self.a.data(stem+f'string-{n}-input.bin'),stage+' independently BEFORE-bound immutable source bytes')
   need(record['reads']and max(r[1]+r[3]for r in record['reads'])==(w[4]+w[7]+3)&~3,'Literal aligned string accesses retain terminal DWORD bytes beyond NUL')
   need(sum(r[3]for r in record['writes'])==w[7],'No copied bytes beyond first NUL')
   COUNTS['whole_string_witnesses']+=1;COUNTS['string_literal_copy_writes']+=len(record['writes']);COUNTS['string_literal_source_reads']+=len(record['reads'])
 def check(self,m,name):
  if name not in self.index:return
  need(name not in self.seen,'Each provider checkpoint observed exactly once '+name);p=self.index[name]
  observed_state=bytearray(m.state)
  equal(bytes(observed_state),self.a.data(p+'-state.bin'),f'{self.level} seq{self.seq} {name} full State')
  equal(B.cpu(observed_state),self.a.data(p+'-cpu.bin'),name+' source projected CPU')
  equal(m.fx,self.a.data(p+'-fx.bin'),name+' carried Runtime FX')
  if self.runtime_cpu is not None:
   equal(self.runtime_cpu,self.a.data(p+'-runtime-cpu.bin'),name+' declared paused Runtime CPU');COUNTS['whole_Runtime_CPU_checkpoints']+=1
  for addr,logical in self.pages[p].items():equal(m.bytes(addr,len(self.a.data(logical))),self.a.data(logical),name+' entire owned page '+hex(addr));COUNTS['whole_checkpoint_pages']+=1
  COUNTS['whole_State_checkpoints']+=1;COUNTS['whole_CPU_checkpoints']+=1;COUNTS['whole_FX_checkpoints']+=1;self.seen.add(name)
 def snapshot(self,m,name):
  self.check(m,name)
  # The native binding carries its source prefix ledger into the locale
  # observer. The independent model already retains those same literal rows.
  if name=='allocation-caller-after':self.provider_start=0
 def begin_root(self,m):self.root=m.cursor;self.runtime_cpu=B.cpu(m.state);self.check(m,f'registry-root-{self.regindex}-before')
 def end_root(self,m):self.check(m,f'registry-root-{self.regindex}-after');self.regindex+=1
 def ledger(self,m,responses,stage):
  stem=f'sequence-{self.seq}/{stage}/';actual=list(struct.iter_unpack('<IIQII',self.a.data(stem+'locale-source-accesses.bin')))
  need(self.provider_start is not None,'Independent source boundary establishes provider ledger start')
  expected=m.accesses[self.provider_start:]
  equal(json.dumps(expected).encode(),json.dumps(actual).encode(),stage+' exact ordered source memory ledger')
  actual=list(struct.iter_unpack('<IIQII',self.a.data(stem+'locale-api-transports.bin')))
  need(actual==m.transports,stage+' exact finite API output transport chronology')
  actual=list(struct.iter_unpack('<IIQII',self.a.data(stem+'locale-research-accesses.bin')))
  need(actual==provider_research(m),stage+' distinct explicit research stores '+str((actual,provider_research(m))))
  COUNTS['source_access_records']+=len(expected);COUNTS['API_transport_records']+=len(m.transports);COUNTS['research_access_records']+=len(provider_research(m))
 def owners(self,m,responses,stage,expected_callbacks):
  stem=f'sequence-{self.seq}/{stage}/';summary=self.a.words(stem+'registry-summary.bin',32,'Q');locale=self.a.words(stem+'locale-summary.bin',32)
  allocations=list(struct.iter_unpack('<16Q',self.a.data(stem+'locale-allocations.bin')));sections=list(struct.iter_unpack('<16Q',self.a.data(stem+'locale-critical-sections.bin')))
  need(len(allocations)==len(responses.allocations)==17,'Exactly one actual producer plus16 genuine duplicate owners through lifecycle')
  for observed,owned in zip(allocations,responses.allocations):
   live=int(owned['live']);expected=(1,owned['guest'],owned['requested'],owned['extent'],owned['mapped'],owned['generation'],owned.get('kind',1),owned['native'],owned['native']if live else 0,live,1-live,0,summary[15]if live else self.handle,0,0,0)
   need(observed==expected,stage+' full private allocation owner association '+str((observed,expected)))
   p=stem+'locale-allocation-'+str(owned['generation']);equal(owned['initial'],self.a.data(p+'-initial.bin'),stage+' actual acquired native bytes')
   if live:
    equal(m.bytes(owned['guest'],owned['mapped']),self.a.data(p+'-expected.bin'),stage+' full committed native/alias mirror')
    equal(m.bytes(owned['guest'],owned['mapped']),self.a.data(p+'-owned-page.bin'),stage+' whole private mapped backing')
    if owned.get('kind',1)==1:
     vector=responses.completed_registry(m,expected_callbacks);need(summary[6:10]==(vector['begin'],vector['next'],vector['capacity'],len(expected_callbacks)),stage+' exact registry vector owner/extent');COUNTS['owned_callback_entries']+=len(expected_callbacks)
   else:equal(self.last_owned[owned['generation']],self.a.data(p+'-expected.bin'),'Final released owner retains its historical committed mirror');need(p+'-owned-page.bin'not in self.a.entries,'Actual released mapping has no live owned-page output')
  need(len(sections)==len(responses.sections)==4,'Exact four independently source-initialized native CS owners')
  for observed,(guest,owned)in zip(sections,responses.sections.items()):
   deleted=int(owned['deletes']>0);expected=(1,guest,owned['generation'],owned['enters'],owned['leaves'],owned['depth'],1,owned['deletes'],int(owned['initialized']),deleted,owned['native'],40,0,0,0,0)
   need(observed==expected,stage+' full private CS lifecycle association')
  expected_counts=(sum(x['live']for x in responses.allocations),sum(x['initialized']and not x['deletes']for x in responses.sections.values()),responses.index,len(m.accesses)-self.provider_start,len(responses.growth))
  need(summary[10:15]==expected_counts,stage+' full owner/resource/source counts '+str((summary[10:15],expected_counts,self.provider_start)))
  need(summary[19:22]==(m.word(2472),m.reg('esp'),len(provider_research(m))),stage+' actual final source PC/SP/research chronology')
  need(locale[14:19]==(summary[10],summary[11],summary[13],len(m.transports),responses.index),'Same provider/registry actual summary counts')
  if stage=='cleaned':need(summary[4]==1 and summary[15]==0 and locale[23]==1 and locale[30]==0,'Actually closed native heap and all resources')
  else:need(summary[4]==0 and summary[15]==self.handle and locale[30]==1,'Same privately owned live heap')
  COUNTS['whole_owner_lifecycle_dumps']+=1
 def identities(self,stem,facts):
  E=load('provider_final_physical',self.pin(ROOT/'tools/m4-crt-locale-batch-review/check_v2.py'));E.FORWARDS.update(HeapSize='RtlSizeHeap',HeapReAlloc='RtlReAllocateHeap')
  for n,fact in enumerate(facts):
   p=stem+f'locale-api-{n}';before=E.identity(self.a,p+'-identity-before',self.pin);after=E.identity(self.a,p+'-identity-after',self.pin);need(before==after,'Same actual full-width API identity')
   raw=self.a.data(p+'-export-before.bin');equal(raw,self.a.data(p+'-export-after.bin'),'Actual API export proof unchanged');E.export_proof(raw,before,fact['name'],self.pin);COUNTS['actual_typed_API_identity_proofs']+=1
  for service,name in (('create','HeapCreate'),('query','GetVersionExA')):
   p=stem+'heap-'+service+'-api-';before=E.identity(self.a,p+'before',self.pin);after=E.identity(self.a,p+'after',self.pin);need(before==after,'Same actual bootstrap/lifecycle API identity');rva,forward=E.export(Path(before[2]),name);need(not forward and before[1]+rva==before[0],'Actual physical direct bootstrap/lifecycle API export');COUNTS['actual_heap_API_identity_proofs']+=1
  p=stem+'heap-destroy-api-';before=E.identity(self.a,p+'before',self.pin);rva,forward=E.export(Path(before[2]),'HeapDestroy');need(not forward and before[1]+rva==before[0],'Actual physical direct pre-call HeapDestroy export')
  after=E.identity(self.a,p+'after',self.pin);need(before==after,'Actual same full-width postdestroy export identity observed');COUNTS['actual_pre_HeapDestroy_identity_proofs']+=1;COUNTS['actual_post_HeapDestroy_identity_proofs']+=1
 def prefix(self,m):
  runtime=self.runtime_cpu;self.runtime_cpu=None
  for name,phase in m.bootstrap_prefix['phases'].items():
   if name in self.index and name not in self.seen:
    predicted=B.P.Machine(phase['state'],phase['fx'],phase['cpu'],phase['memory'],program={},callbacks={});self.check(predicted,name)
  self.runtime_cpu=runtime
 def finish(self,m,responses,roots,G):
  stem=f'sequence-{self.seq}/';selected_count=responses.index;self.handle=self.a.words(stem+'selected/registry-summary.bin',32,'Q')[15]
  self.prefix(m);self.owners(m,responses,'selected',roots);self.ledger(m,responses,'selected');self.string_dump(m,responses,'selected')
  observed_replays=self.a.words(stem+'growth-replay-count.bin',1)[0]
  vector=responses.completed_registry(m,roots);initial_growths=len(responses.growth);expected=list(roots);first=expected[0];capacity_steps=(vector['capacity']-(vector['next']-vector['begin']))//4+1
  n=0
  while len(responses.growth)==initial_growths:
   need(n<512,'Source-derived successful next growth reached within declared harness limit')
   self.runtime_cpu=B.cpu(m.state);self.check(m,f'registry-replay-{43+n}-before');m.invoke_external(0x410210,0xffffffa0,responses);expected.append(first);responses.completed_registry(m,expected);self.check(m,f'registry-replay-{43+n}-after');COUNTS['genuine_growth_replays']+=1;n+=1
  need(n==observed_replays==capacity_steps,'Independently measured msize capacity and carried next derive actual bounded replay count')
  need(len(responses.growth)==initial_growths+1,'Exactly one additional genuine actual source HeapReAlloc after selected sequence')
  self.owners(m,responses,'grown',expected);self.ledger(m,responses,'grown');self.string_dump(m,responses,'grown')
  self.last_owned={owned['generation']:m.bytes(owned['guest'],owned['mapped'])for owned in responses.allocations}
  self.runtime_cpu=B.cpu(m.state)
  for owned in [a for a in responses.allocations if a.get('kind',1)==3]+[a for a in responses.allocations if a.get('kind',1)==1]:
   oldsp=m.reg('esp');oldpc=m.word(2472);m.write(oldsp-4,owned['guest'],domain='research',pc=oldpc);m.reg('esp',oldsp-4);m.invoke_external(0x78001390,0xffffff70 if owned.get('kind',1)==3 else 0xffffff80,responses);m.reg('esp',oldsp)
   need(not owned['live'],'Genuine original source free retired its exact string/producer mapping')
  m.cpu=B.cpu(m.state)
  for guest,section in reversed(list(responses.sections.items())):
   fact=responses.facts[responses.index];w=fact['words'];need(fact['name']=='DeleteCriticalSection' and w[31]==1 and w[:2]==(1,responses.index) and w[2:8]==(0,0x7802e040,0x3446a,0,0,0) and w[8]==1 and w[9]==w[11] and w[14:17]==(1,1,section['native'])and not fact['inputs']and not fact['outputs'],'Actual research cleanup deletes exact reverse source-owned native CS')
   need(section['initialized']and section['depth']==0 and section['deletes']==0,'Balanced source lock before real delete');section['deletes']=1;responses.index+=1
  responses.complete();self.owners(m,responses,'cleaned',expected);self.ledger(m,responses,'cleaned');self.string_dump(m,responses,'cleaned');self.identities(stem+'cleaned/',responses.facts)
  h=self.a.words(stem+'cleaned/heap-create-registry.bin',18,'Q');need(h[4]==self.handle and h[7]==0 and h[9:11]==(1,1) and h[12]==1 and h[13]==0 and h[15]==1 and h[16]==self.handle,'Actual same full heap HANDLE destroyed exactly once')
  COUNTS['complete71_provider_sequences']+=1;COUNTS['selected_registration_closures']+=43;COUNTS['real_producer_allocations']+=1;COUNTS['successful_actual_growth']+=len(responses.growth);COUNTS['actual_source_frees']+=17;COUNTS['actual_duplicate_allocations']+=16;COUNTS['actual_CS_deletes']+=4;COUNTS['actual_heap_destroys']+=1
  remaining=sorted(set(self.index)-self.seen);need(remaining==['registry-bootstrap-before'],'Every captured provider AFTER checkpoint independently predicted '+str(remaining));COUNTS['true_bootstrap_BEFORE_inputs']+=1
  ROWS.append(dict(level=self.level,sequence=self.seq,selected_API_count=selected_count,grown_API_count=selected_count,cleaned_API_count=responses.index,compared_checkpoints=len(self.seen),selected_roots_growth=True,all_resources_released=True,actual_post_HeapDestroy_identity=True))
def begin(m):CURRENT.begin_root(m)
def end(m):CURRENT.end_root(m)
def finish(m,responses,roots,G):CURRENT.finish(m,responses,roots,G)
