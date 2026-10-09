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
 parent=getattr(G,'provider_final_base_machine',G.Machine);G.provider_final_base_machine=parent
 class Observed(parent):
  def __init__(self,*args,**kwargs):
   super().__init__(*args,**kwargs);previous=self.hook
   def hook(machine,event,data):
    if previous:previous(machine,event,data)
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
class Observer:
 def __init__(self,a,seq,level,pin,index,pages,numeric):
  self.a=a;self.seq=seq;self.level=level;self.pin=pin;self.index=index;self.pages=pages;self.numeric=numeric;self.seen=set();self.provider_start=None;self.regindex=0;self.runtime_cpu=None
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
 def begin_root(self,m):self.runtime_cpu=B.cpu(m.state);self.check(m,f'registry-root-{self.regindex}-before')
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
  need(len(allocations)==len(responses.allocations)==1,'Exactly one actual producer owner through lifecycle')
  for observed,owned in zip(allocations,responses.allocations):
   live=int(owned['live']);expected=(1,owned['guest'],owned['requested'],owned['extent'],owned['mapped'],owned['generation'],1,owned['native'],owned['native']if live else 0,live,1-live,0,summary[15]if live else self.handle,0,0,0)
   need(observed==expected,stage+' full private allocation owner association '+str((observed,expected)))
   p=stem+'locale-allocation-'+str(owned['generation']);equal(owned['initial'],self.a.data(p+'-initial.bin'),stage+' actual acquired native bytes')
   if live:
    equal(m.bytes(owned['guest'],owned['mapped']),self.a.data(p+'-expected.bin'),stage+' full committed native/alias mirror')
    equal(m.bytes(owned['guest'],owned['mapped']),self.a.data(p+'-owned-page.bin'),stage+' whole private mapped backing')
    vector=responses.completed_registry(m,expected_callbacks);need(summary[6:10]==(vector['begin'],vector['next'],vector['capacity'],len(expected_callbacks)),stage+' exact registry vector owner/extent');COUNTS['owned_callback_entries']+=len(expected_callbacks)
   else:equal(self.last_owned,self.a.data(p+'-expected.bin'),'Final released owner retains its historical committed mirror');need(p+'-owned-page.bin'not in self.a.entries,'Actual released mapping has no live owned-page output')
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
  need(self.a.data(p+'after.bin')==bytes(88),'Existing worker explicitly has no postdestroy identity observation');COUNTS['actual_pre_HeapDestroy_identity_proofs']+=1;COUNTS['post_HeapDestroy_identity_unobserved']+=1
 def prefix(self,m):
  runtime=self.runtime_cpu;self.runtime_cpu=None
  for name,phase in m.bootstrap_prefix['phases'].items():
   if name in self.index and name not in self.seen:
    predicted=B.P.Machine(phase['state'],phase['fx'],phase['cpu'],phase['memory'],program={},callbacks={});self.check(predicted,name)
  self.runtime_cpu=runtime
 def finish(self,m,responses,roots,G):
  stem=f'sequence-{self.seq}/';selected_count=responses.index;self.handle=self.a.words(stem+'selected/registry-summary.bin',32,'Q')[15]
  self.prefix(m);self.owners(m,responses,'selected',roots);self.ledger(m,responses,'selected')
  observed_replays=self.a.words(stem+'growth-replay-count.bin',1)[0]
  vector=responses.completed_registry(m,roots);capacity_steps=(vector['capacity']-(vector['next']-vector['begin']))//4+1
  first=list(roots)[0];entry=0x410210;expected=list(roots)
  n=0
  while not responses.growth:
   need(n<512,'Source-derived successful growth reached within declared harness limit')
   self.runtime_cpu=B.cpu(m.state)
   self.check(m,f'registry-replay-{26+n}-before');m.invoke_external(entry,0xffffffa0,responses);expected.append(first);responses.completed_registry(m,expected);self.check(m,f'registry-replay-{26+n}-after');COUNTS['genuine_growth_replays']+=1
   n+=1
  need(n==observed_replays==capacity_steps==7,'Independent actual msize and carried begin/next derive exact replay count')
  need(len(responses.growth)==1,'Exactly one genuine successful actual HeapReAlloc growth');self.owners(m,responses,'grown',expected);self.ledger(m,responses,'grown')
  owned=responses.allocations[0];self.last_owned=m.bytes(owned['guest'],owned['mapped']);oldsp=m.reg('esp');oldpc=m.word(2472);self.runtime_cpu=B.cpu(m.state);m.write(oldsp-4,owned['guest'],domain='research',pc=oldpc);m.reg('esp',oldsp-4);m.invoke_external(0x78001390,0xffffff80,responses);m.reg('esp',oldsp);m.cpu=B.cpu(m.state)
  need(not owned['live'],'Genuine original source free retired its exact producer mapping')
  for guest,section in reversed(list(responses.sections.items())):
   fact=responses.facts[responses.index];w=fact['words'];need(fact['name']=='DeleteCriticalSection' and w[31]==1 and w[:2]==(1,responses.index) and w[2:8]==(0,0x7802e040,0x3446a,0,0,0) and w[8]==1 and w[9]==w[11] and w[14:17]==(1,1,section['native'])and not fact['inputs']and not fact['outputs'],'Actual research cleanup deletes exact reverse source-owned native CS')
   need(section['initialized']and section['depth']==0 and section['deletes']==0,'Balanced source lock before real delete');section['deletes']=1;responses.index+=1
  responses.complete();self.owners(m,responses,'cleaned',expected);self.ledger(m,responses,'cleaned');self.identities(stem+'cleaned/',responses.facts)
  h=self.a.words(stem+'cleaned/heap-create-registry.bin',18,'Q');need(h[4]==self.handle and h[7]==0 and h[9:11]==(1,1) and h[12]==1 and h[13]==0 and h[15]==1 and h[16]==self.handle,'Actual same full heap HANDLE destroyed exactly once')
  COUNTS['complete54_provider_sequences']+=1;COUNTS['selected_registration_closures']+=26;COUNTS['real_producer_allocations']+=1;COUNTS['successful_actual_growth']+=1;COUNTS['actual_source_frees']+=1;COUNTS['actual_CS_deletes']+=4;COUNTS['actual_heap_destroys']+=1
  remaining=sorted(set(self.index)-self.seen);need(remaining==['registry-bootstrap-before'],'Every captured provider AFTER checkpoint independently predicted '+str(remaining));COUNTS['true_bootstrap_BEFORE_inputs']+=1
  ROWS.append(dict(level=self.level,sequence=self.seq,selected_API_count=selected_count,grown_API_count=106,cleaned_API_count=responses.index,compared_checkpoints=len(self.seen),seven_replays=True,all_resources_released=True,post_HeapDestroy_identity_unobserved=True))
def begin(m):CURRENT.begin_root(m)
def end(m):CURRENT.end_root(m)
def finish(m,responses,roots,G):CURRENT.finish(m,responses,roots,G)
