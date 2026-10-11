"""Complete provider130 lifetimes, adding four genuine formatter owned buffers."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
_source=Path(__file__).resolve().parents[1]/'m4-tree-source/final_observer125_v2.py'
_text=_source.read_text()
def _one(a,b):
 global _text
 assert _text.count(a)==1,(a,_text.count(a));_text=_text.replace(a,b)
_one('len(actual)==len(self.mfc)==65','len(actual)==len(self.mfc)==68')
_one('len(allocations)==len(responses.allocations)==85','len(allocations)==len(responses.allocations)==92')
_one("sum(a.get('kind',1)==4 for a in responses.allocations)==65","sum(a.get('kind',1)==4 for a in responses.allocations)==68")
_one("live,1-live,0,summary[15]", "live,(1-live)*int(not owner.get('formatter',False)),(1-live)*int(owner.get('formatter',False)),summary[15]")
_one("if owner.get('kind',1)==1:","if owner.get('kind',1)==1 and not owner.get('formatter',False):")
_text=_text.replace("len(roots)==97", "len(roots)==101").replace('registry-replay-{97+n}', 'registry-replay-{101+n}')
_one("ordered=[a for kind in(4,3,1)for a in responses.allocations if a.get('kind',1)==kind]","ordered=[a for kind in(4,3,1)for a in responses.allocations if a.get('kind',1)==kind and not a.get('formatter',False)]")
_one("responses.complete();self.owners(m,responses,'cleaned',expected)",'''for owner in reversed(responses.allocations):
   if not owner.get('formatter',False):continue
   fact=responses.facts[responses.index];w=tuple(fact['words']);need(fact['name']=='HeapFree'and w[:8]==(1,responses.index,0,0x7802e090,0x345ba,0,0,0)and w[8]==1 and w[9]==w[11]and w[14:17]==(1,1,owner['native'])and w[31]==1 and not fact['inputs']and not fact['outputs'],'Actual reverse-order formatter cleanup frees same acquired pointer')
   need(owner['live']and owner['extent']==16 and len(m.memory[owner['guest']])==owner['mapped'],'Actual source formatter owner remains live until same native cleanup');owner['live']=False;m.memory.pop(owner['guest']);responses.index+=1;COUNTS['actual_formatter_cleanup_frees']+=1
  responses.complete();self.owners(m,responses,'cleaned',expected)''')
_text=_text.replace("COUNTS['complete125_provider_sequences']", "COUNTS['complete130_provider_sequences']").replace("COUNTS['selected_registration_closures']+=97", "COUNTS['selected_registration_closures']+=101").replace("COUNTS['actual_MFC_allocations']+=65", "COUNTS['actual_MFC_allocations']+=68").replace("COUNTS['actual_source_frees']+=85", "COUNTS['actual_source_frees']+=88").replace("COUNTS['actual_MFC_source_frees']+=65", "COUNTS['actual_MFC_source_frees']+=68").replace('actual_MFC_allocations=65','actual_MFC_allocations=68').replace("COUNTS['complete_Lockit_semantic_API_relations']+=34", "COUNTS['complete_Lockit_semantic_API_relations']+=36")
exec(compile(_text,str(_source),'exec'),globals())
BaseObserver=Observer
FORMAT_ROOTS=(0x4df610,0x4e0710,0x4e0810,0x4e1ca0)
FORMAT_IMPORTS={0x4dea15:(0x780264a9,2),0x4deab1:(0x780012b3,1),0x4dead1:(0x78022b9a,4)}
class Observer(BaseObserver):
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs)
  family=json.loads(self.pin(ROOT/'reports/m4-formatting-native/preparation-r18/family-contracts.json').read_bytes());self.family=family
  for a in family['mixed_interface']['MFC_allocation_contracts']:
   spec=dict(root=0x4e1ca0,CALL_pc=a['allocation_CALL_pc'],requested_size=a['requested'],publication=a['publication_address'],publication_PC=a['publication_pc'],publication_owner=None)
   self.specs.append(spec);self.fs_specs.append(spec)
  self.formatting_calls=[];self.formatting_owned=[];self.formatting_publications=[];self.formatting_dispatches=[];self.formatting_phase_results=[]
  self.formatting_base=0;self.formatting_owner=None;self.formatting_cursor=0;self.formatting_di=0;self.formatting_completed=0
 def begin_root(self,m):
  super().begin_root(m)
  if self.root in FORMAT_ROOTS:self.formatting_base=0;self.formatting_owner=None;self.formatting_cursor=0;self.formatting_di=0
 def string_event(self,m,event,data):
  super().string_event(m,event,data)
  if self.root not in FORMAT_ROOTS:return
  if event=='control'and data['op']=='call':
   target,site=data['target'],data['site'];frame=m.reg('esp')
   if target==0x4de9c0:need(not self.formatting_base,'One literal shared formatter constructor');self.formatting_base=frame
   if site in FORMAT_IMPORTS:
    declared,argc=FORMAT_IMPORTS[site];need(target==declared and self.formatting_base,'Exact literal cdecl import target and constructor frame')
    args=[int.from_bytes(m.bytes(frame+4+4*k,4),'little')for k in range(argc)];owner=self.formatting_owner
    row=[1,self.root,site,target,frame,self.formatting_base,argc]+args+[0]*(4-argc)+[0,owner['guest']if owner else 0,owner['generation']if owner else 0,0,0];need(len(row)==16,'Whole16Q formatter cdecl row');self.formatting_calls.append(row)
  if event=='returned'and data['caller']and data['caller'][0]in(0x780264a9,0x780012b3,0x78022b9a):
   entry=data['caller'][0];frame=data['frame'];matches=[r for r in self.formatting_calls if r[1]==self.root and r[3]==entry and r[4]==frame and not r[14]]
   if matches:
    need(len(matches)==1,'One literal same-frame formatter return');row=matches[0]
    if entry==0x780012b3:
     owner=next(a for a in m.responses.allocations if a['guest']==m.reg('eax')and a['live']);need(owner.get('formatter',False)and owner['extent']==16,'Source-owned formatter malloc result');self.formatting_owner=owner
    owner=self.formatting_owner;row[12:]=[owner['guest']if owner else 0,owner['generation']if owner else 0,1,m.reg('eax')]
    need(m.reg('esp')==frame+4,'Exact formatter cdecl RET stack cleanup')
  if event in('read-after','write-after')and data['domain']=='source':
   pc,address,width,value=data['pc'],data['address'],data['bytes'],data['value'];writing=event=='write-after'
   if pc in(0x7801042a,0x78022bd5):
    owner=self.formatting_owner;need(owner and owner['guest']<=address and address+width<=owner['guest']+owner['requested'],'Literal formatter operand stays in actual current request')
    self.formatting_owned.append((1,self.root,self.formatting_cursor,pc,address,width,int(writing),value,owner['guest'],owner['generation'],address-owner['guest'],len(m.accesses)));self.formatting_cursor+=1
   if pc==0x4deabc and writing:
    owner=self.formatting_owner;need(owner and value==owner['guest'],'Literal formatter publication binds current owner')
    self.formatting_publications.append((1,self.root,pc,address,value,owner['generation'],owner['requested'],owner['extent'],len(m.accesses),0,0,0))
   if pc==0x7800fcef and not writing:
    index=m.reg('eax');need(index==[1,7,1,7][self.formatting_di]and width==4 and address==0x780103fa+4*index and value==(0x7800fd04 if index==1 else 0x7800fe69),'Literal finite normal formatter table branch')
    self.formatting_dispatches.append((1,self.root,self.formatting_di,pc,index,address,value,len(m.accesses)));self.formatting_di+=1
 def end_root(self,m):
  super().end_root(m)
  if self.root not in FORMAT_ROOTS:return
  owner=self.formatting_owner;need(owner and self.formatting_di==4 and self.formatting_cursor==owner['requested']+1,'Complete literal formatter output/NUL RMW operand extent');self.formatting_completed+=1
 def formatting_dump(self,m,stage):
  stem=f'sequence-{self.seq}/{stage}/'
  for name,width,expected in(('formatting-calls',16,self.formatting_calls),('formatting-owned',12,self.formatting_owned),('formatting-publications',12,self.formatting_publications),('formatting-dispatches',8,self.formatting_dispatches)):
   actual=list(struct.iter_unpack('<'+str(width)+'Q',self.a.data(stem+name+'.bin')));need(actual==[tuple(r)for r in expected],stage+' complete formatter private history from literal source '+name);COUNTS['whole_'+name+'_rows']+=len(actual)
  owner=self.formatting_owner;need(self.formatting_completed==4 and owner,'Four source formatter lifetimes')
  need(self.a.words(stem+'formatting-status.bin',10)==(1,0,4,self.formatting_base,owner['guest'],owner['generation'],self.formatting_cursor,4,1,0),'Whole final formatter private scalar lifetime status')
 def owners(self,m,responses,stage,expected_callbacks):
  super().owners(m,responses,stage,expected_callbacks);self.formatting_dump(m,stage)

def configure(G,numeric,archive,seq,level,pin):
 pin(_source);pin(Path(__file__))
 S.install_responses();parent=B.R.ActualResponses
 if not getattr(B.R,'formatting_review_derived',False):
  class FormattingResponses(parent):
   def __call__(self,m,target):
    frames=[f for f in m.call_stack if f[0]==0x780012b3];fmt=bool(frames and int.from_bytes(m.bytes(frames[-1][1],4),'little')==0x4deab7);count=len(self.allocations);super().__call__(m,target)
    if len(self.allocations)>count and fmt:self.allocations[-1]['formatter']=True;self.allocations[-1]['kind']=1
  B.R.ActualResponses=FormattingResponses;B.R.formatting_review_derived=True
 parent=B.R.ActualResponses
 if not getattr(B.R,'mfc_review_derived',False):
  class MfcResponses(parent):
   def __call__(self,m,target):
    mfc=any(f[0]==0x5f401ea0 for f in m.call_stack);count=len(self.allocations);super().__call__(m,target)
    if len(self.allocations)>count and mfc:self.allocations[-1]['kind']=4
  B.R.ActualResponses=MfcResponses;B.R.mfc_review_derived=True
 S.Observer=Observer;return S.configure(G,numeric,archive,seq,level,pin)
