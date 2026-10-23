"""Exact temporary full literal journal with separately owned provider view.

Full accesses remain installed during every instruction/CRT/FS guard. Only the
observer callback receives the provider view. Both ordered ledgers are retained;
no source memory, CPU, flags, FX or API state is changed by this association.
"""
import hashlib,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[2]
CONTRACT=R/'reports/m4-startup141-runway/service-preparation-r2/constructor-FS-contracts.json'
def need(v,s):
 if not v:raise ValueError(s)
def word(m,a):return int.from_bytes(m.bytes(a,4),'little')
def fs_specs():
 d=json.loads(CONTRACT.read_bytes());return {f[k]:(kind,f['entry'],f['handler'])for f in d['frames']for k,kind in(('read',0),('install',1),('restore',2))}
class Association:
 def __init__(self,m,o,root):
  self.m=m;self.o=o;self.root=root;self.full=m.accesses;self.start=len(self.full);self.provider=list(self.full);self.provider_start=len(self.provider);self.component=[];self.shared=[];self.mode='component';self.borrow=None;self.hook=m.hook;self.fs=[];self.specs=fs_specs()
 def before_event(self,event,d):
  m=self.m
  if event in('read-before','write-before')and d['domain']=='source'and d['address']==m.word(2168)and d['pc']in self.specs:
   kind,group,handler=self.specs[d['pc']];need(d['bytes']==4 and (event=='write-before')==(kind!=0),'Exact declared game FS operand')
   previous=word(m,d['address']);frame=m.reg('esp')if kind==1 else previous
   self.fs.append(dict(root=self.root,PC=d['pc'],kind=kind,group_entry=group,handler=handler,before_head=previous,after_head=d['value']if kind else previous,entry_ESP=m.reg('esp')+8 if kind==0 else None,ESP=m.reg('esp'),record_address=frame,record_hex=m.bytes(frame,12).hex()if frame!=0xffffffff else None))
  if event in('read-after','write-after')and d['domain']=='source':
   row=(d['pc'],d['address'],d['value'],d['bytes'],int(event=='write-after'));need(self.full and tuple(self.full[-1])==row,'Exact committed full literal operand retained')
   if self.mode=='component':
    self.component.append(row)
    if row[4]and row[1]==m.word(2168):self.provider.append(row);self.shared.append(row)
   else:self.provider.append(row)
  if event=='control'and d['op']=='call'and d['target']in(0x5abd26,0x5abd1a,0x78004a36):
   need(self.mode=='component'and self.borrow is None,'One serial literal borrowed constructor call');frame=m.reg('esp');site=d['site'];ret=word(m,frame)
   shared=[(site,frame,ret,4,1)]
   if d['target']==0x78004a36:
    need(site==0x5ac11e and ret==0x5ac124,'Exact source onexit CALL');shared.insert(0,(site,0x5bb52c,0x1decb0,4,0));need(self.component[-2:]==shared,'Both shared raw-IAT and committed onexit CALL operands')
   else:need(self.component[-1:]==shared and ret==site+5,'Exactly one shared constructor MFC CALL write')
   self.provider.extend(shared);self.shared.extend(shared);self.mode='provider';self.borrow=(d['target'],frame)
 def after_event(self,event,d):
  if event=='returned'and d['caller']and self.borrow is not None:
   target={0x5abd26:0x5f401ea0,0x5abd1a:0x5f401782}.get(self.borrow[0],self.borrow[0])
   if d['caller'][0]==target:
    need(self.mode=='provider'and d['frame']==self.borrow[1]and self.m.reg('esp')==self.borrow[1]+4,'Whole literal borrowed return restores component journal ownership');self.mode='component';self.borrow=None
 def observer_hook(self,m,event,d):
  need(m.accesses is self.full,'Every source guard executes against complete temporary chronology')
  self.before_event(event,d);m.accesses=self.provider
  try:
   if self.hook:self.hook(m,event,d)
  finally:m.accesses=self.full
  self.after_event(event,d)
 def finish(self):
  need(self.mode=='component'and self.borrow is None and self.m.accesses is self.full,'Every borrowed source scope returned without replacing full literal journal')
  full=self.full[self.start:];provider=self.provider[self.provider_start:]
  need(len(full)==len(self.component)+len(provider)-len(self.shared),'Exhaustive full component/provider/shared operand cardinality')
  self.m.accesses=self.provider;self.m.hook=self.hook
  return dict(component_source_accesses=[list(r)for r in self.component],provider_source_accesses=[list(r)for r in provider],shared_source_accesses=[list(r)for r in self.shared],whole_literal_source_accesses=[list(r)for r in full],game_FS_observations=self.fs,full_literal_journal_preserved_during_instruction_guards=True,AFTER_seed=False)
