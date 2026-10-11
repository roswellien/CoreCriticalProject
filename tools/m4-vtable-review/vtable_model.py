"""Independent literal-before finite indirect-call/store witness derivation."""
import json,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def need(v,s):
 if not v:raise ValueError(s)
def word(m,a):return int.from_bytes(m.bytes(a,4),'little')
def fs0(m):return word(m,0x7ffde000)
def live(m):return sum(o['live']for o in m.responses.allocations)
class VtableEvents:
 def __init__(self,observer):
  self.o=observer;p=ROOT/'reports/m4-next-source/recovery-r1'
  self.specs=json.loads(observer.pin(p/'indirect-call-inputs.json','a329e3988a4d77137e1270d9606c2c65f8b6aee95d1f04fb5928eb9a28a90d9a').read_bytes())
  contract=json.loads(observer.pin(p/'instruction-contracts.json').read_bytes())
  self.store_PCs={r['pc']for r in contract['instructions']if r['mnemonic']in('mov','or')and r['explicit_memory_writes']}
  self.roots={r['root']for r in self.specs};self.calls=[];self.stores=[];self.read=[0]*8;self.vptr=[0]*8;self.probe=[0]*16;self.active=0
 def event(self,m,event,d):
  root=self.o.root
  if root not in self.roots:return
  if event.startswith('read-')and d['domain']=='source':
   pc,address,size=d['pc'],d['address'],d['bytes'];spec=next((r for r in self.specs if(r['root'],r['CALL_pc'])==(root,pc)),None)
   instance=pc==0x59ff64
   if instance:spec=next(r for r in self.specs if(r['root'],r['CALL_pc'])==(root,0x59ff6e))
   if not spec:return
   expected=spec['source_vtable']if instance else spec['target'];wanted=spec['source_object']if instance else spec['slot']
   need(size==4 and address==wanted and m.reg('ecx')==spec['entry_ECX'],'Literal instance/cell address and live source ECX')
   if not instance and pc==0x59ff6e:
    need(self.vptr[1]==root and self.vptr[3]==spec['source_object']and self.vptr[4]==m.reg('edx')==spec['source_vtable'],'Virtual dispatch follows actual literal instance vptr and delivered EDX')
   if event=='read-before':self.read=[1,root,pc,address,size,expected,len(m.accesses),int(instance)]
   elif event=='read-after':
    value=d['value'];need(value==expected,'Actual source raw cell retains fixed physical target/vptr')
    if instance:
     found=next(((i,r)for i,r in reversed(list(enumerate(m.accesses)))if r[4]and r[1]==address and r[3]==4),None)
     need(found is not None and found[1]==(spec['dominating_vtable_store_PC'],address,value,4,1),'Most recent literal source vptr publication owns this instance')
     self.vptr=[1,root,pc,address,value,len(m.accesses)-1,found[0],found[1][0]]
    else:
     need(not self.active,'One finite literal indirect call at a time')
     virtual=pc==0x59ff6e;published=0;publication_index=0
     if spec.get('source_vtable'):
      found=next(((i,r)for i,r in reversed(list(enumerate(m.accesses)))if r[4]and r[1]==spec['source_object']and r[3]==4),None)
      need(found is not None and found[1]==(spec['dominating_vtable_store_PC'],spec['source_object'],spec['source_vtable'],4,1)and word(m,spec['source_object'])==spec['source_vtable'],'Actual dominating publication establishes fixed-cell class header independently of future vptr read')
      publication_index=found[0];published=found[1][2]
     self.calls.append([1,len(self.calls),root,pc,address,value,value,pc,len(m.accesses)-1,m.reg('ecx'),published,spec.get('source_vtable',0),publication_index,self.vptr[5]if virtual else 0,0,0,0,spec['RET_cleanup'],0,0,0,0,len(m.accesses)-1,0,fs0(m),0,m.responses.index,0,live(m),0,0,0]);self.active=len(self.calls)
  if event=='control'and d['op']=='call':
   spec=next((r for r in self.specs if(r['root'],r['CALL_pc'])==(root,d['site'])),None)
   if spec:
    need(self.active,'Literal genuine CALL follows actual owning source cell read');w=self.calls[self.active-1];sp=m.reg('esp');arg=word(m,sp+4)if spec['argument']is not None else 0
    need(d['target']==w[6]==spec['target']and m.reg('ecx')==spec['entry_ECX']and word(m,sp)==spec['return_pc']and(spec['argument']is None or arg==spec['argument']==0),'Actual CALL frame/return/zero argument/source target')
    w[14:17]=[sp,word(m,sp),arg];self.o.check(m,f'vtable-call-{w[1]}-entered')
  if event=='returned'and d['caller']and self.active:
   w=self.calls[self.active-1]
   if d['caller'][0]==w[6]:
    need(d['frame']==w[14]and m.reg('esp')==w[14]+4+w[17]and m.word(2472)==w[15]and m.responses.index==w[26]and live(m)==w[28]and fs0(m)==w[24],'Literal RET cleanup/frame/full owner/API/FS conservation')
    w[18:22]=[m.reg('esp'),m.reg('eax'),d['site'],1];w[23]=len(m.accesses);w[25]=fs0(m);w[27]=m.responses.index;w[29]=live(m);self.o.check(m,f'vtable-call-{w[1]}-returned');self.active=0
  if event.startswith('write-')and d['domain']=='source'and d['pc']in self.store_PCs and d['address']<0x20000000:
   pc,address,size,value=d['pc'],d['address'],d['bytes'],d['value']
   if event=='write-before':self.probe=[1,len(self.stores),root,pc,address,size,value,len(m.accesses),0,fs0(m),self.active,0,0,0,0,0]
   elif event=='write-after':
    need(self.probe[3:7]==[pc,address,size,value],'Source object write commits its actual prepared operand');self.probe[8]=len(m.accesses);self.stores.append(tuple(self.probe));self.probe=[0]*16
 def dump(self,m,stage):
  a=self.o.a;stem=f'sequence-{self.o.seq}/{stage}/'
  for name,values,width in(('vtable-call-witnesses.bin',self.calls,32),('vtable-source-stores.bin',self.stores,16)):
   actual=list(struct.iter_unpack('<'+str(width)+'Q',a.data(stem+name)))
   need(actual==[tuple(w)for w in values],stage+' complete independent literal '+name)
  for name,w in(('vtable-read-probe.bin',self.read),('vtable-instance-vptr.bin',self.vptr),('vtable-store-probe.bin',self.probe)):
   need(a.words(stem+name,len(w),'Q')==tuple(w),stage+' entire genuine source probe '+name)
  need(a.words(stem+'vtable-active.bin',1)==(self.active,)==(0,),'All exact source indirect calls genuinely returned')
  need(len(self.calls)==6 and all(w[21]for w in self.calls),'Six finite CALLs with no discarded return')
  need(not any(r[0]in range(0x59ff88,0x59ffa1)for r in m.accesses),'Nonzero59FF80 pointee-copy branch is not in admitted source footprint')
  return dict(independent_vtable_calls=len(self.calls),independent_vtable_object_stores=len(self.stores),complete_vtable_dump_sets=1)
