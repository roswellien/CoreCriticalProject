"""Whole source delta from independently predicted heap/caller BEFORE.

Actual API results and complete scratch output bytes are finite input witnesses.
They are authenticated against source arguments and independently derived buffer
contracts before copying. This module never reads a captured machine AFTER.
"""
import copy
import hashlib
import json
from pathlib import Path
import struct
import interpreter_v2 as I

ROOT=I.ROOT
class OwnedMachine(I.Machine):
 """APIs may span adjacent declared pages; aliases remain independently checked."""
 def bytes(self,address,size):
  I.need(size>=0,'Nonnegative owned byte extent')
  result=bytearray();cursor=address
  while cursor<address+size:
   owners=[(p,b) for p,b in self.memory.items() if p<=cursor<p+len(b)]
   I.need(owners,'Owned contiguous byte span '+hex(cursor))
   end=min(address+size,max(p+len(b) for p,b in owners));n=end-cursor
   # Choose a complete owner for this segment; check every smaller semantic alias.
   p,b=max(owners,key=lambda x:x[0]+len(x[1]));raw=bytes(b[cursor-p:cursor-p+n])
   for q,c in owners:
    finish=min(end,q+len(c));I.need(bytes(c[cursor-q:finish-q])==raw[:finish-cursor],'Consistent source-derived semantic alias')
   result.extend(raw);cursor=end
  return bytes(result)
 def store_bytes(self,address,raw):
  self.bytes(address,len(raw))
  for p,b in self.memory.items():
   lo=max(address,p);hi=min(address+len(raw),p+len(b))
   if lo<hi:b[lo-p:hi-p]=raw[lo-address:hi-address]
 def snapshot(self,name):
  super().snapshot(name)
  if hasattr(self,'responses'):
   r=self.responses
   self.phases[name]['allocations']=copy.deepcopy(r.allocations)
   self.phases[name]['sections']=copy.deepcopy(r.sections)
   self.phases[name]['api_count']=r.index+(r.active is not None)
def contracts():
 p=ROOT/'reports/m4-crt-locale-batch-recovery/recovery-r2/API-contracts.json'
 q=json.loads(p.read_bytes());imports={x['name']:x for x in q['imports']}
 source=json.loads((p.parent/'report.json').read_bytes())['API_sites'];result={}
 for site in source:
  item=imports[site['API']];result[site['pc']]=dict(name=site['API'],slot=site['IAT'],raw=site['raw_IAT'],argc=item['argument_DWORDs'],tail=site['kind']=='jmp',void=item['void'])
 result[0x7800137f]=dict(name='HeapAlloc',slot=0x7802e094,raw=0x345c6,argc=3,tail=False,void=False)
 result[0x78001430]=dict(name='HeapFree',slot=0x7802e090,raw=0x345ba,argc=3,tail=False,void=False)
 return result
def dwords(raw):I.need(len(raw)%4==0,'Complete typed DWORD array');return struct.unpack('<'+'I'*(len(raw)//4),raw)
def qwords(raw):I.need(len(raw)%8==0,'Complete typed uint64 array');return struct.unpack('<'+'Q'*(len(raw)//8),raw)

class ActualResponses:
 """Independent transport, argument and source-frame checker."""
 def __init__(self,facts):
  self.facts=facts;self.index=0;self.contracts=contracts();self.allocations=[];self.sections={};self.generation=0
  self.allocation_cursor=0x31000000;self.transport_ordinal=0;self.active=None
 def input_bytes(self,m,p,count,unit):
  count=count if count<0x80000000 else count-0x100000000
  I.need(count>=-1 and (p or count<=0),'Bounded authentic API source pointer/count')
  if not p:return b''
  if count==-1:
   count=0
   while count<131072//unit:
    value=m.bytes(p+count*unit,unit);count+=1
    if value==bytes(unit):break
   else:raise ValueError('NUL-inclusive actual API source extent')
  I.need(0<=count*unit<=131072,'Bounded authentic API input bytes');return m.bytes(p,count*unit)
 def buffers(self,m,name,a):
  """Return actual original pointer/extent/input or output-before in source order."""
  descriptors=[]
  def input(p,c,u=1):
   b=self.input_bytes(m,p,c,u);descriptors.append((p,len(b),1,b));return b
  def output(p,n):
   I.need(n<=131072 and (p or not n),'Actual bounded API writable scratch')
   if p and n:descriptors.append((p,n,2,m.bytes(p,n)))
  if name in ('GetACP','GetOEMCP'):pass
  elif name=='GetCPInfo':output(a[1],20)
  elif name=='GetModuleFileNameA':output(a[1],a[2])
  elif name=='MultiByteToWideChar':input(a[2],a[3]);output(a[4],a[5]*2)
  elif name=='WideCharToMultiByte':
   input(a[2],a[3],2);output(a[4],a[5])
   if a[6]:input(a[6],2)
   if a[7]:output(a[7],4)
  elif name in ('GetStringTypeW','GetStringTypeA'):
   wide=name.endswith('W');source=input(a[1 if wide else 2],a[2 if wide else 3],2 if wide else 1)
   output(a[3 if wide else 4],len(source) if wide else len(source)*2)
  elif name in ('LCMapStringW','LCMapStringA'):
   wide=name.endswith('W');input(a[2],a[3],2 if wide else 1);output(a[4],a[5]*(2 if wide else 1))
  elif name.find('CriticalSection')!=-1:descriptors.append((a[0],24,1,m.bytes(a[0],24)))
  elif name=='HeapFree':
   owned=next((x for x in self.allocations if x['guest']==a[2] and x['live']),None);I.need(owned is not None,'Source free same private live allocation')
   descriptors.append((a[2],owned['extent'],1,m.bytes(a[2],owned['extent'])))
  elif name!='HeapAlloc':raise ValueError('Unadmitted measured original API '+name)
  return descriptors
 def __call__(self,m,target):
  I.need(self.index<len(self.facts),'Complete finite actual source API witness')
  fact=self.facts[self.index];self.active=self.index;w=fact['words'];I.need(len(w)==32 and w[0]==1 and w[1]==self.index,'Typed actual API32Q index')
  site=m.PCs[-1];I.need(site in self.contracts,'Authentic recovered API site');c=self.contracts[site]
  frame=m.reg('esp');ret=int.from_bytes(m.bytes(frame,4),'little')
  a=tuple(int.from_bytes(m.bytes(frame+4+4*n,4),'little') for n in range(c['argc']))
  I.need(tuple(w[2:8])==(site,c['slot'],c['raw'],frame,ret,c['argc']) and target==c['raw'],'Source-derived actual API import/frame/arity')
  I.need(tuple(w[20:20+c['argc']])==a and w[19]==c['tail'],'Source-derived actual API complete arguments/tail contract')
  I.need(w[14]==w[15]==1,'Actual API and checked stdcall return completed')
  I.need(w[9]==w[11] and w[9]<=0xffffffff and w[10]<=0xffffffff,'Actual caller LastError restored, raw API error finite')
  buffers=self.buffers(m,c['name'],a)
  I.need(len(fact['inputs'])==len(buffers),'All immutable actual input/output-before payloads')
  for n,(pointer,size,kind,payload) in enumerate(buffers):
   I.need(fact['inputs'][n]==payload,'Independent complete pre-API scratch/source bytes '+c['name'])
   if c['name'] not in ('HeapFree',) and 'CriticalSection' not in c['name']:
    I.need(tuple(fact['buffers'][n])==(pointer,size,kind,n),'Independent actual API buffer ownership contract')
  tag='locale-api-'+str(self.index);name=c['name'];result=w[12]
  if name=='InitializeCriticalSection':
   I.need(a[0] not in self.sections,'Fresh exact guest CS initialization');self.generation+=1
   self.sections[a[0]]=dict(generation=self.generation,depth=0,native=w[16],enters=0,leaves=0,initialized=False,deletes=0)
  m.snapshot(tag+'-before');m.emit('api-before',index=self.index,fact=fact,contract=c)
  outputs=[]
  if name=='HeapAlloc':
   I.need(a[0]==0x48450001 and a[1]==0 and 0<a[2]<=1048576 and w[8]!=0,'Actual source same-private-heap bounded allocation')
   extent=a[2];mapped=(extent+4095)&~4095;guest=self.allocation_cursor
   I.need(result==guest and w[13]==extent and len(fact['outputs'])==1 and len(fact['outputs'][0])==extent,'Actual full native allocation bytes and opaque guest address')
   self.generation+=1;entry=dict(guest=guest,extent=extent,mapped=mapped,generation=self.generation,native=w[8],live=True,initial=fact['outputs'][0])
   self.allocations.append(entry);m.snapshot(tag+'-after')
   I.need(not any(p<=guest<p+len(b) or guest<=p<guest+mapped for p,b in m.memory.items()),'Disjoint declared research allocation backing')
   m.memory[guest]=bytearray(entry['initial']+bytes(mapped-extent));self.allocation_cursor+=mapped
  elif name=='HeapFree':
   I.need(w[8]!=0 and result==w[8],'Actual successful raw BOOL release witness')
   entry=next(x for x in self.allocations if x['guest']==a[2] and x['live']);I.need(w[16]==entry['native'],'Actual same-full-pointer source release')
   entry['live']=False;m.memory.pop(entry['guest']);m.snapshot(tag+'-after')
  elif 'CriticalSection' in name:
   guest=a[0];I.need(w[16]!=0 and w[17]==40 and not fact['outputs'],'Opaque native CS40 association; no guest-structure transport')
   I.need(guest in self.sections and self.sections[guest]['native']==w[16],'Exact same current native CS')
   entry=self.sections[guest]
   if name=='InitializeCriticalSection':entry['initialized']=True
   if name=='EnterCriticalSection':entry['depth']+=1;entry['enters']+=1
   if name=='LeaveCriticalSection':I.need(entry['depth']>0,'Source serial recursive CS ownership');entry['depth']-=1;entry['leaves']+=1
   I.need(w[18]==entry['depth'],'Actual source CS depth agrees with genuine calls')
   result=m.reg('eax');I.need(w[8]==w[12]==0,'Void actual API rawreturn has no fabricated guest result');m.snapshot(tag+'-after')
  else:
   I.need(w[8]<=0xffffffff and w[12]==w[8],'Finite actual DWORD API output')
   destinations=[(p,n) for p,n,k,_ in buffers if k==2]
   I.need(len(fact['outputs'])==len(destinations),'Complete finite actual scratch output payloads')
   for (p,n),raw in zip(destinations,fact['outputs']):I.need(len(raw)==n,'Whole actual API scratch output extent');outputs.append((p,raw))
   I.need(w[13]==sum(len(b) for _,b in outputs) and w[29]==len(buffers) and w[30]==len(outputs),'Exact complete actual API payload inventory')
   m.snapshot(tag+'-after')
   for p,raw in outputs:
    i=0
    while i<len(raw):
     size=min(4,len(raw)-i,4096-((p+i)&4095))
     m.write(p+i,int.from_bytes(raw[i:i+size],'little'),size,domain='transport',pc=site);i+=size
   m.snapshot(tag+'-output-after')
  m.api_return(site,c['argc'],result)
  if 'CriticalSection' not in name and name!='HeapFree':m.snapshot(tag+'-returned')
  self.index+=1;self.active=None
 def complete(self):I.need(self.index==len(self.facts),'Exact actual source API witness exhaustion')

def commandline(m,actual_bytes):
 """Two literal source instructions plus declared finite owned-copy/carry seam."""
 I.need(actual_bytes and actual_bytes[-1]==0 and len(actual_bytes)<=131072,'Finite actual NUL-inclusive GetCommandLineA witness')
 frame=m.reg('esp');I.need(frame==0x20001860 and m.word(2472)==0x5ac468,'Declared mainargs command-line scheduling seam')
 m.snapshot('commandline-producer-before');m.word(2472,0x7800188c);m.cursor=0x7800188c;m.snapshot('commandline-producer-projected')
 old=len(m.accesses);m.PCs.append(0x7800188c)
 I.need(m.read(0x7802e034)==0x3442e,'Original named command-line IAT')
 m.push(0x78001892);m.word(2472,0x3442e);m.snapshot('commandline-api-before');m.snapshot('commandline-api-after')
 I.need(0x33000000 not in m.memory,'Fresh disjoint command-line owned extent');m.memory[0x33000000]=bytearray(actual_bytes)
 m.snapshot('commandline-buffer-after');m.reg('eax',0x33000000);m.reg('esp',frame);m.word(2472,0x78001892);m.PCs.append(0x78001892)
 m.write(0x78037174,0x33000000);m.word(2472,0x78001897);m.cursor=0x78001897;m.snapshot('commandline-producer-after')
 m.word(2472,0x5ac468);m.cursor=0x5ac468;cpu=bytearray(m.cpu);struct.pack_into('<I',cpu,0,0x33000000);m.cpu=bytes(cpu);m.snapshot('commandline-carry-after')
 return m.accesses[old:]

def predict(initializer,facts,actual_commandline,extra_memory,hook=None):
 """initializer is computed by the frozen original BEFORE/source oracle."""
 I.need(initializer['initializer_RET'] and initializer['heap_mode_value']==1,'Actual qualifying source initializer return')
 memory=copy.deepcopy(initializer['memory'])
 for p,b in extra_memory.items():
  if p in memory:I.need(bytes(memory[p])==bytes(b),'Declared extra memory does not overwrite carried source state')
  else:memory[p]=bytearray(b)
 m=OwnedMachine(initializer['state'],initializer['fx'],initializer['cpu'],memory,hook=hook)
 m.accesses=list(initializer['accesses']);m.API_reads=[initializer['API_return_access'],initializer['query_return_access']]
 # The frozen prefix uses routes and API_return_accesses labels, handled by
 # the observer when attaching its separately authenticated historical ledgers.
 responses=ActualResponses(facts);m.responses=responses
 m.undefined=[(pc,I.FLAGS['AF'],value) for pc,value in initializer['undefined']]
 parser_returns=0
 original_hook=m.hook
 def observe(x,event,data):
  nonlocal parser_returns
  if original_hook:original_hook(x,event,data)
  if event=='write-after' and data['domain']=='source' and data['address']==x.word(I.BASE['fs']):x.snapshot('locale-source-seh-'+str(len(x.accesses))+'-after')
  if event=='control' and data['op']=='call' and data['target']==0x7800bc48:x.snapshot('locale-parser-'+('sizing' if parser_returns==0 else 'output')+'-before')
  if event=='returned' and data['caller'] and data['caller'][0]==0x7800bc48:
   parser_returns+=1;x.snapshot('locale-parser-'+('sizing' if parser_returns==1 else 'output')+'-returned')
  if event=='returned' and data['caller'] and data['caller'][0]==0x7800bbbc:x.snapshot('locale-builder-returned')
 m.hook=observe
 m.snapshot('allocation-caller-before');m.run(lambda x:x.cursor==0x7800184c);m.snapshot('allocation-caller-after')
 m.snapshot('locale-batch-before');m.invoke_external(0x78003bf4,0xffffffc0,responses);m.snapshot('locale-static-locks-returned')
 I.need(len(responses.sections)==4,'Four real API-supported static critical sections')
 m.invoke_external(0x78003dd2,0xffffffb0,responses);m.snapshot('locale-default-returned')
 I.need(m.reg('eax')==0 and len(responses.allocations)==1 and len(responses.sections)==5,'Completed default source locale and owned lazylock25')
 m.project(3,0x5ac468);m.snapshot('locale-commandline-suspended');commandline(m,actual_commandline)
 m.project(4,0x7800ba5e);m.call_stack.append((0x7800ba5e,m.reg('esp'),int.from_bytes(m.bytes(m.reg('esp'),4),'little'),0,m.reg('ebp'),m.reg('ebx'),m.reg('esi'),m.reg('edi'),0));m.snapshot('locale-mainargs-before')
 m.run(lambda x:'locale-builder-returned' in x.phases,responses);responses.complete()
 I.need(parser_returns==2 and m.cursor==0x7800ba9e,'Sizing/output parser RETs and genuine argv-builder RET')
 argc=int.from_bytes(m.bytes(0x78038ef4,4),'little');argv=int.from_bytes(m.bytes(0x7803b3d8,4),'little')
 I.need(argc>0 and int.from_bytes(m.bytes(argv+argc*4,4),'little')==0,'Source-published argc/argv/null sentinel')
 strings=[]
 for i in range(argc):
  p=int.from_bytes(m.bytes(argv+i*4,4),'little');buf=bytearray()
  while len(buf)<131072:
   b=m.bytes(p+len(buf),1)
   if b==b'\0':break
   buf.extend(b)
  else:raise ValueError('Source-produced bounded argv string')
  strings.append(bytes(buf))
 result=m.result();result.update(argc=argc,argv=argv,argv_strings=strings,responses=responses,static_helper_RET=True,default_locale_RET=True,parser_passes=2,builder_RET=True,mainargs_export_RET=False,full_CRT=False,whole_M4_complete=False)
 return result
