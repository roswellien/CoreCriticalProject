"""Source-event chronology for all74 native MFC records; no capture inputs."""
import struct

def word(m,a):return int.from_bytes(m.bytes(a,4),'little')

class Chronology:
 def __init__(self,need):
  self.need=need;self.records=[];self.imports=[];self.stores=[]
 def append(self,r):
  self.need(all(r is not x for x in self.records),'One actual source MFC entry occurrence')
  r['words'][1]=len(self.records);self.records.append(r)
 def inherited(self,o,m,event,data,parent):
  before=(len(o.mfc),len(o.mfc_imports),len(o.mfc_stores))
  result=parent(m,event,data)
  self.need(len(o.mfc)-before[0] in(0,1),'At most one inherited source MFC entry per event')
  for r in o.mfc[before[0]:]:self.append(r)
  for index in range(before[1],len(o.mfc_imports)):
   row=o.mfc_imports[index]
   if row[7]==0:
    self.need(event=='read-after' and data['domain']=='source' and (data['pc'],data['address'],data['bytes'])==(0x5abd26,0x5bb4bc,4),'Ordinal import preceding actual allocator entry')
    row=(row[0],len(self.records))+row[2:];o.mfc_imports[index]=row
   self.imports.append(row)
  self.stores.extend(o.mfc_stores[before[2]:])
  return result
 def constructor(self,o,m,event,d):
  n=self.need;c=o.constructor_active_call
  if o.constructor_free is not None:
   r=o.constructor_free;w=r['words']
   if event=='read-after' and d['domain']=='source' and (d['pc'],d['address'])==(0x5f401786,0x5f498148):
    n(d['bytes']==4 and d['value']==0x7800138a,'Whole source constructor825 named free input');w[28:30]=[d['value'],0x78001390];self.imports.append((1,w[1],0,d['pc'],d['address'],d['value'],0x78001390,2))
   if event=='control' and d['op']=='call' and d['site']==0x5f401786:
    n(d['target']==w[29]==0x78001390 and m.reg('esp')==w[26]-8 and word(m,m.reg('esp'))==0x5f40178c and word(m,m.reg('esp')+4)==w[16],'Whole source constructor825 CRT CALL');w[27]=m.reg('esp')
   return
  if not(o.root in(0x4103f0,0x410440,0x459b40) and getattr(m,'constructor_active',False)):return
  if event=='read-after' and d['domain']=='source' and (d['pc'],d['address'],d['bytes'])==(0x5abd26,0x5bb4bc,4):
   n(c is not None and c['request']>0 and d['value']==0x80000337,'Actual positive constructor ordinal823 source read');self.imports.append((1,len(self.records),0,d['pc'],d['address'],d['value'],0x5f401ea0,0))
  if event=='control' and d['op']=='jmp' and d['site']==0x5abd26:
   n(c is not None and c['request']>0 and d['target']==0x5f401ea0 and m.reg('esp')==c['frame'],'Actual positive constructor823 entry')
   w=[1,0,0,0x5f401ea0,c['site'],c['frame'],word(m,c['frame']),c['request']]+[0]*24;w[22]=m.reg('ecx')
   r=dict(words=w,root=c['root'],site=c['site']);self.append(r);c['source_record']=r
  if c is None or not c.get('source_record'):return
  w=c['source_record']['words']
  if event=='read-after' and d['domain']=='source' and d['bytes']==4:
   if (d['pc'],d['address'])==(0x5f401ea1,0x5f49814c):
    n(not w[21] and d['value']==0x78001498,'Source constructor malloc named input');w[8:11]=[d['value'],0x780012b3,d['pc']];self.imports.append((1,w[1],0,d['pc'],d['address'],d['value'],0x780012b3,1))
   elif (d['pc'],d['address'])==(0x5f401ead,0x5f498970):
    n(not w[21] and d['value']==0xffffffff,'Source constructor handler input');w[14:16]=[d['pc'],d['value']];self.imports.append((1,w[1],0,d['pc'],d['address'],d['value'],d['value'],3))
  if event=='control' and d['op']=='call' and d['site']==0x5f401eb5:
   f=m.reg('esp');n(d['target']==m.reg('ebx')==w[9]==0x780012b3 and f==w[5]-24 and word(m,f)==0x5f401eb7 and word(m,f+4)==w[7],'Whole source constructor cdecl malloc frame');w[11:14]=[d['site'],f,word(m,f+4)]
  if event=='returned' and d['caller']:
   if d['caller'][0]==0x780012b3:
    owner=m.responses.allocations[-1];n(d['frame']==w[12] and m.reg('eax')==owner['guest'] and owner['kind']==4 and owner['requested']==w[7] and owner['live'],'Actual constructor source malloc owner result');w[16:21]=[owner['guest'],owner['native'],owner['generation'],owner['extent'],m.reg('eax')]
   elif d['caller'][0]==0x5f401ea0:
    n(d['frame']==w[5] and m.reg('eax')==w[20]==w[16] and w[16]!=0,'Actual constructor complete823 RET');w[21]=1
 def dump(self,o,m,responses,stage,counts):
  n=self.need;stem=f'sequence-{o.seq}/{stage}/'
  n(len(o.mfc)==68 and len(o.constructor_mfc)==6 and len(self.records)==74,'Exact separate68+6 genuine source MFC occurrences')
  n(all(r['words'][1]==i for i,r in enumerate(self.records)) and {id(r)for r in self.records}=={id(r)for r in o.mfc+o.constructor_mfc},'Whole chronological74 source record union')
  expected=[]
  for r in self.records:
   w=list(r['words']);owner=next(a for a in responses.allocations if a['generation']==w[18]);w[30]=int(not owner['live']);w[31]=0;expected.append(tuple(w))
   own=[s for s in self.stores if s[1]==w[1]]
   if any(r is c for c in o.constructor_mfc):n(w[2]==0 and w[23]==w[24]==0 and not own,'Constructor game operands stay in separate component journal; no fabricated provider store/publication')
   else:n(w[23]==1 and sum(s[5]for s in own if s[7]==1)==w[24] and all(w[16]<=s[4]and s[4]+s[5]<=w[16]+w[7]for s in own if s[7]==1),'Retained exact requested-byte initialization and one publication')
  n(list(struct.iter_unpack('<32Q',o.a.data(stem+'mfc-allocation-witnesses.bin')))==expected,stage+' entire74 chronological32Q MFC source/owner/free witnesses')
  n(list(struct.iter_unpack('<8Q',o.a.data(stem+'mfc-import-ledger.bin')))==self.imports,stage+' entire chronological raw-first MFC import ledger')
  n(list(struct.iter_unpack('<8Q',o.a.data(stem+'mfc-store-ledger.bin')))==self.stores,stage+' entire committed MFC store ledger')
  n(o.a.words(stem+'mfc-store-probe.bin',8,'Q')==(0,)*8,'No pending ordinary source MFC store')
  counts['whole_MFC_witnesses']+=74;counts['MFC_import_records']+=len(self.imports);counts['MFC_literal_store_records']+=len(self.stores)
  for key,value in o.container.dump(m,stage).items():counts[key]+=value
  for key,value in o.vtable.dump(m,stage).items():counts[key]+=value
