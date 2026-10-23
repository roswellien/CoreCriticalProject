"""Independent literal BEFORE-derived container witness construction.

The integer machine executes physical original instructions. This observer
derives evidence fields from genuine carried frames/accesses/owners; captured
witnesses never seed this machine. Native labels only define serialization.
"""
import struct

def need(v,s):
 if not v:raise ValueError(s)
def word(m,a):return int.from_bytes(m.bytes(a,4),'little')
def fs0(m):return word(m,0x7ffde000)
def live(m):return sum(a['live']for a in m.responses.allocations)

class ContainerEvents:
 def __init__(self,observer,borrowed,zero_frees,vector_stores):
  self.o=observer;self.borrowed_specs=borrowed;self.zero_specs=zero_frees+[dict(root=0,CALL_pc=0x58af9a,argument=0)];self.store_specs=vector_stores;self.constructor_null_roots=[]
  self.nulls=[];self.borrowed=[];self.imports=[];self.stores=[];self.probe=[0]*16;self.null_active=None;self.borrowed_active=None
 def imports_row(self,root,pc,address,raw,target,kind):
  self.imports.append((1,len(self.imports),root,pc,address,raw,target,kind))
 def event(self,m,event,data):
  root=self.o.root;responses=m.responses;consumed=False
  c=getattr(self.o,'constructor_active_call',None)
  constructor_null=root in(0x4103f0,0x410440) and getattr(m,'constructor_active',False) and c is not None and c['thunk']==0x5abd1a
  if constructor_null:
   need(c['root']==root and c['site']==0x58af9a and c['request']==0 and c['ret']==0x58af9f,'Source-owned finite constructorNULL825 domain')
   root=0 # Native Binding registry_root is zero during this physically borrowed provider body; logical root retained separately.

  if event=='control'and data['op']=='jmp'and data['site']in(0x5abd1a,0x5abdb0):
   nil=data['site']==0x5abdb0;target=0x5f4020b4 if nil else 0x5f401782;frame=m.call_stack[-1]
   need(data['target']==target and frame[0]==data['site'],'Original owning game thunk/target and true saved CALL frame')
   m.call_stack[-1]=(target,)+frame[1:] # Explicit naming only; actual machine and remaining source frame fields unchanged.
   self.o.container_tail_projections+=1;site=frame[3];sp=m.reg('esp');ret=word(m,sp)
   if nil:
    spec=next(r for r in self.borrowed_specs if r['root']==root and r['CALL_pc']==site)
    need(self.borrowed_active is None and spec['object']==m.reg('ecx')and sp==frame[1],'Literal540 root/site/ECX/source frame')
    w=[1,len(self.borrowed),root,target,site,sp,ret,m.reg('ecx'),0x8000021c,0x5abdb0,0,0,0,0x5f4ccb54,0,0,0,0,0,0,0,0,0,len(m.accesses),0,fs0(m),0,responses.index,0,live(m),0,0]
    self.borrowed.append(w);self.borrowed_active=w
   else:
    spec=next(r for r in self.zero_specs if r['root']==root and r['CALL_pc']==site)
    need(self.null_active is None and word(m,sp+4)==0 and spec['argument']==0 and sp==frame[1],'Literal825 source normal zero argument and true frame')
    w=[1,len(self.nulls),root,site,target,sp,ret,0,0x80000339,0x5abd1a,responses.generation,0,0,0,0,0,0,0,0,fs0(m),0,0,0,responses.index,0,live(m),0,len(m.accesses),0,0,0,0]
    self.nulls.append(w);self.null_active=w
    if constructor_null:self.constructor_null_roots.append(self.o.root)
  if event=='read-after'and data['domain']=='source':
   pc,address,raw,size=data['pc'],data['address'],data['value'],data['bytes']
   if size==4 and(pc,address)in((0x5abd1a,0x5bb4c8),(0x5abdb0,0x5bb454)):
    nil=pc==0x5abdb0;need(raw==(0x8000021c if nil else 0x80000339),'Retained exact raw owning game import')
    self.imports_row(root,pc,address,raw,0x5f4020b4 if nil else 0x5f401782,540 if nil else 825)
   elif self.null_active is not None and(pc,address)==(0x5f401786,0x5f498148):
    need(size==4 and raw==0x7800138a,'Raw original named free import before exact declared relocation');w=self.null_active;w[14:17]=[raw,pc,0x78001390];self.imports_row(root,pc,address,raw,0x78001390,0);consumed=True
   elif(pc,address)==(0x5f4020bc,0x5f4ccb54):
    w=self.borrowed_active;need(w is not None and size==4 and raw==0x5f4cecec and w[12]==address and m.reg('eax')==address,'Exact authenticated borrowed DWORD read after accessor RET')
    w[14:16]=[pc,raw]
  if event=='control'and data['op']=='call':
   pc=data['site'];sp=m.reg('esp')
   if self.null_active is not None and pc==0x5f401786:
    w=self.null_active;need(data['target']==w[16]==0x78001390 and sp==w[5]-8 and word(m,sp)==0x5f40178c and word(m,sp+4)==0,'Genuine original825 CALL frame to literal free(NULL)')
    w[11:14]=[data['target'],sp,word(m,sp)];w[20]=fs0(m);consumed=True
   if self.borrowed_active is not None and pc==0x5f4020b7:
    w=self.borrowed_active;need(data['target']==0x5f4020c4 and sp==w[5]-8 and word(m,sp)==0x5f4020bc,'Literal540 accessor source CALL frame');w[10:12]=[sp,word(m,sp)]
  if event=='write-before'and data['domain']=='source':
   pc,address,size,value=data['pc'],data['address'],data['bytes'],data['value']
   if pc==0x5f4020be:
    w=self.borrowed_active;need(w is not None and size==4 and address==w[7]and value==w[15]and w[14]==0x5f4020bc and not w[19],'Only source ECX object receives unchanged borrowed DWORD');w[16:19]=[address,pc,value]
   spec=next((r for r in self.store_specs if r['root']==root and r['pc']==pc),None)
   if spec:
    r=next(r for r in self.o.mfc if r['words'][2]==root and r['words'][4]==spec['CALL_pc']);w=r['words'];owner=next(a for a in responses.allocations if a['generation']==w[18]);want=w[16]+(w[7]if spec['kind']==3 else 0)
    need(size==4 and address==spec['address']and owner['live']and owner.get('kind')==4 and value==want and w[21],'Exact source vector begin/end/capacity joins its genuine still-live whole owner')
    self.probe=[1,len(self.stores),root,pc,address,size,value,spec['kind'],w[1],w[16],w[18],w[7],w[17],w[19],len(m.accesses),0]
  if event=='write-after'and data['domain']=='source':
   pc,address,size,value=data['pc'],data['address'],data['bytes'],data['value']
   if pc==0x5f4020be:
    w=self.borrowed_active;need(w is not None and(w[16],w[17],w[18])==(address,pc,value)and size==4,'Committed source borrowed store');w[19]=1
   if self.probe[3:7]==[pc,address,size,value]:self.probe[15]=len(m.accesses);self.stores.append(tuple(self.probe));self.probe=[0]*16
  if event=='returned'and data['caller']:
   entry=data['caller'][0];frame=data['frame'];result=m.reg('eax')
   if self.null_active is not None and entry in(0x78001390,0x5f401782):
    w=self.null_active;need(responses.index==w[23]and live(m)==w[25]and responses.generation==w[10]and fs0(m)==w[19],'Literal normal free(NULL) has no native API/owner/generation effect and restores same outer chain')
    if entry==0x78001390:
     need(frame==w[12]and w[11],'Exact literal CRTfree(NULL) RET frame');w[17]=1;w[21]=fs0(m);w[29]=result
    else:
     need(frame==w[5]and w[17],'Genuine825 null RET after literal CRTfree');w[18]=1;w[22]=fs0(m);w[24]=responses.index;w[26]=live(m);w[28]=len(m.accesses);w[30]=result;w[31]=responses.generation;self.null_active=None
    consumed=True
   if self.borrowed_active is not None and entry in(0x5f4020c4,0x5f4020b4):
    w=self.borrowed_active
    if entry==0x5f4020c4:
     need(frame==w[10]and result==0x5f4ccb54,'Borrowed accessor returns only owned module DWORD address');w[12]=result
    else:
     need(frame==w[5]and w[19]and result==w[7]and responses.index==w[27]and live(m)==w[29]and fs0(m)==w[25],'Complete literal540 restores frame/chain and returns object without an owner/API')
     w[20]=data['site'];w[21]=result;w[22]=1;w[24]=len(m.accesses);w[26]=fs0(m);w[28]=responses.index;w[30]=live(m);self.borrowed_active=None
  return consumed
 def dump(self,m,stage):
  o=self.o;stem=f'sequence-{o.seq}/{stage}/';a=o.a
  for name,values,width in(('container-nullfree-witnesses.bin',self.nulls,32),('container-borrowed-witnesses.bin',self.borrowed,32),('container-import-ledger.bin',self.imports,8),('container-vector-stores.bin',self.stores,16)):
   actual=list(struct.iter_unpack('<'+str(width)+'Q',a.data(stem+name)));need(actual==[tuple(v)for v in values],stage+' entire independently source-derived '+name)
  need(len(self.nulls)==7 and sum(w[2]!=0 for w in self.nulls)==5 and sum(w[2]==0 for w in self.nulls)==2 and self.constructor_null_roots==[0x4103f0,0x410440] and len(self.borrowed)==3 and len(self.stores)==len(self.store_specs)==17,'Exact five inherited normal plus two source-owned constructor null frees/three borrowed constructors/seventeen literal vector field stores')
  need(self.probe==list(a.words(stem+'container-vector-probe.bin',16,'Q'))==[0]*16,'No pending normal vector source store')
  need(a.words(stem+'container-active.bin',2)==(0,0)and self.null_active is self.borrowed_active is None,'Returned exact source container frames')
  need(a.words(stem+'container-null-active.bin',1)==a.words(stem+'container-borrowed-active.bin',1)==(0,),'Actual scalar active fields equal aggregate returned-source observation')
  footprint=[r for r in m.accesses if r[1]<0x5f4cd000 and r[1]+r[3]>0x5f4cc000]
  need(footprint==[(0x5f4020bc,0x5f4ccb54,0x5f4cecec,4,0)]*3,'Complete selected literal module data-page footprint is exactly three borrowed DWORD reads and zero writes')
  need(0x5f4ce000 not in m.memory,'Borrowed pointee page receives no map or dereference admission')
  for spec in self.o.new_allocation_specs:
   record=next(r for r in self.o.mfc if(r['words'][2],r['words'][4])==(spec['root'],spec['CALL_pc']));w=record['words'];owner=next(r for r in m.responses.allocations if r['generation']==w[18])
   need(w[24]==0 and not any(r[4]and r[1]<w[16]+w[7]and r[1]+r[3]>w[16]for r in m.accesses),'Literal empty-vector initialization writes zero acquired buffer bytes')
   full=m.bytes(owner['guest'],owner['extent'])if owner['live']else self.o.last_owned[owner['generation']][:owner['extent']]
   need(full==owner['initial'],'Entire true acquired vector backing and untouched padding remain source-unchanged')
  return dict(nullfree_witnesses=len(self.nulls),borrowed_witnesses=len(self.borrowed),container_import_rows=len(self.imports),container_vector_stores=len(self.stores),complete_borrowed_data_footprint=len(footprint))
