"""Independent bounded original x86 source interpreter.

Inputs are an explicit BEFORE machine, literal decoded source, declared owned
memory, and finite actual API responses. Captured AFTER state is never an input.
This module does not import candidate guards or execute native code or APIs.
"""
import copy
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).absolute().parents[2]
REG={'eax':2216,'ecx':2248,'edx':2264,'ebx':2232,'esp':2312,'ebp':2328,'esi':2280,'edi':2296}
BASE={'ss':2120,'es':2136,'cs':2152,'fs':2168,'ds':2184,'gs':2200}
FLAGS={'CF':2065,'PF':2067,'AF':2069,'ZF':2071,'SF':2073,'DF':2075,'OF':2077}
def need(value,why):
 if not value:raise ValueError(why)
def source_program():
 p=ROOT/'reports/m4-crt-locale-batch-recovery/interface-r1/instruction-contracts.json'
 need(hashlib.sha256(p.read_bytes()).hexdigest()=='194e2ca814869c500fd2948d9cc801d3ad7a8aef2367166379a5d0ad87e5a624','Sealed original source interface')
 rows={r['pc']:r for r in json.loads(p.read_bytes())['instructions']}
 p=ROOT/'reports/m4-crt-locale-batch-recovery/callbacks-union-r1/callbacks.json'
 need(hashlib.sha256(p.read_bytes()).hexdigest()=='ce770b98b2dc1f25fa759b2ffa287d3870f367852a5ac406e86bf50e21774c1a','Sealed actual callback source inventory')
 callbacks={}
 raw=json.loads(p.read_bytes())
 for domain in ('new_bodies','baseline_bodies'):
  for body in raw[domain].values():
   for site in body['callback_sites']:
    value=tuple(site['State_offsets']);need(site['pc'] not in callbacks or callbacks[site['pc']]==value,'One actual callback sequence per sourcePC');callbacks[site['pc']]=value
 return rows,callbacks
def alias(name):
 if name in REG:return name,32,0
 if name in ('ax','cx','dx','bx','sp','bp','si','di'):return 'e'+name,16,0
 if name in ('al','cl','dl','bl'):return 'e'+name[0]+'x',8,0
 if name in ('ah','ch','dh','bh'):return 'e'+name[0]+'x',8,8
 raise ValueError('Unadmitted original register '+name)

class Machine:
 def __init__(self,state,fx,cpu,memory,program=None,callbacks=None,hook=None):
  need(len(state)==3504 and len(fx)==512 and len(cpu)==40,'Complete explicitly bounded BEFORE machine')
  self.state=bytearray(state);self.fx=bytes(fx);self.cpu=bytes(cpu)
  self.memory={p:bytearray(b) for p,b in memory.items() if isinstance(p,int)}
  if program is None:program,callbacks=source_program()
  self.program=program;self.callbacks=callbacks;self.cursor=self.word(2472);self.hook=hook
  self.PCs=[];self.accesses=[];self.API_reads=[];self.transports=[];self.external_accesses=[];self.projections=[]
  self.calls=[];self.returns=[];self.undefined=[];self.call_stack=[];self.phases={};self.steps=0
 def word(self,offset,value=None):
  if value is None:return struct.unpack_from('<I',self.state,offset)[0]
  struct.pack_into('<I',self.state,offset,value&0xffffffff)
 def reg(self,name,value=None):
  parent,bits,shift=alias(name);mask=(1<<bits)-1
  if value is None:return (self.word(REG[parent])>>shift)&mask
  self.word(REG[parent],(self.word(REG[parent])&~(mask<<shift))|((value&mask)<<shift))
 def flag(self,name,value=None):
  if value is None:return self.state[FLAGS[name]]
  self.state[FLAGS[name]]=int(bool(value))
 def address(self,operand,lea=False):
  value=(operand['displacement']+sum(self.reg(t['register'])*t['scale'] for t in operand['terms']))&0xffffffff
  if not lea:
   segment=operand['segment']
   if segment=='default':segment='ss' if any(t['register'] in ('ebp','esp') for t in operand['terms']) else 'ds'
   need(segment in BASE,'Recovered original address segment')
   value=(value+self.word(BASE[segment]))&0xffffffff
  return value
 def locations(self,address,size):
  owners=[(p,b) for p,b in self.memory.items() if p<=address and address+size<=p+len(b)]
  need(owners,'Declared owned source access '+hex(address)+' bytes '+str(size))
  # Semantic aliases from earlier models are checked against complete pages.
  owners.sort(key=lambda x:len(x[1]),reverse=True);v=bytes(owners[0][1][address-owners[0][0]:address-owners[0][0]+size])
  need(all(bytes(b[address-p:address-p+size])==v for p,b in owners),'Consistent independently carried aliases')
  return owners
 def bytes(self,address,size):
  owners=self.locations(address,size);p,b=owners[0];return bytes(b[address-p:address-p+size])
 def store_bytes(self,address,raw):
  self.locations(address,len(raw))
  for p,b in self.memory.items():
   lo=max(address,p);hi=min(address+len(raw),p+len(b))
   if lo<hi:b[lo-p:hi-p]=raw[lo-address:hi-address]
 def emit(self,event,**data):
  if self.hook:self.hook(self,event,data)
 def read(self,address,size=4,domain='source',pc=None):
  pc=self.word(2472) if pc is None else pc;value=int.from_bytes(self.bytes(address,size),'little')
  self.emit('read-before',pc=pc,address=address,value=value,bytes=size,domain=domain)
  row=(pc,address,value,size,0)
  (self.accesses if domain=='source' else self.API_reads).append(row)
  self.emit('read-after',pc=pc,address=address,value=value,bytes=size,domain=domain);return value
 def write(self,address,value,size=4,domain='source',pc=None):
  pc=self.word(2472) if pc is None else pc;value&=(1<<(8*size))-1
  self.emit('write-before',pc=pc,address=address,value=value,bytes=size,domain=domain)
  self.store_bytes(address,value.to_bytes(size,'little'))
  row=(pc,address,value,size,1)
  (self.accesses if domain=='source' else self.external_accesses if domain=='research' else self.transports).append(row)
  self.emit('write-after',pc=pc,address=address,value=value,bytes=size,domain=domain)
 def operand(self,op):
  if op['kind']=='register':return self.reg(op['register'])
  if op['kind']=='immediate':return op['value']
  need(op['kind']=='memory' and op['bits'] in (8,16,32,64),'Original memory operand width')
  return self.read(self.address(op),op['bits']//8)
 def destination(self,op,value):
  if op['kind']=='register':self.reg(op['register'],value)
  else:need(op['kind']=='memory','Original writable operand');self.write(self.address(op),value,op['bits']//8)
 def push(self,value):
  sp=(self.reg('esp')-4)&0xffffffff;self.write((sp+self.word(BASE['ss']))&0xffffffff,value);self.reg('esp',sp)
 def pop(self,name):
  sp=self.reg('esp');self.reg('esp',sp+4);self.reg(name,self.read((sp+self.word(BASE['ss']))&0xffffffff))
 def arith(self,a,b,bits,sub=False,carry=0,preserve_cf=False):
  mask=(1<<bits)-1;a&=mask;b&=mask
  full=a-b-carry if sub else a+b+carry;r=full&mask;sign=1<<(bits-1)
  old=self.flag('CF')
  self.flag('CF',a<b+carry if sub else full>mask)
  self.flag('PF',(r&255).bit_count()%2==0);self.flag('AF',(a^b^r)&16)
  self.flag('ZF',r==0);self.flag('SF',r&sign)
  self.flag('OF',((a^b)&(a^r)&sign) if sub else (~(a^b)&(a^r)&sign))
  if preserve_cf:self.flag('CF',old)
  return r
 def logic(self,result,bits):
  result&=(1<<bits)-1
  for k,v in dict(CF=0,PF=(result&255).bit_count()%2==0,AF=0,ZF=result==0,SF=result>>(bits-1),OF=0).items():self.flag(k,v)
  return result
 def condition(self,op):
  cf,zf,sf,of,pf=(bool(self.flag(k)) for k in ('CF','ZF','SF','OF','PF'))
  choices={'je':zf,'jne':not zf,'jb':cf,'jae':not cf,'jbe':cf or zf,'ja':not cf and not zf,'jl':sf!=of,'jge':sf==of,'jle':zf or sf!=of,'jg':not zf and sf==of,'jp':pf,'jnp':not pf}
  need(op in choices,'Exact admitted branch condition');return choices[op]
 def snapshot(self,name):
  need(name not in self.phases,'Unique source-derived checkpoint '+name)
  self.phases[name]=dict(state=bytes(self.state),fx=self.fx,cpu=self.cpu,memory=copy.deepcopy(self.memory),source_accesses=len(self.accesses),API_reads=len(self.API_reads),transports=len(self.transports),undefined=len(self.undefined),external_accesses=len(self.external_accesses),projections=len(self.projections),call_stack=copy.deepcopy(self.call_stack))
 def project(self,kind,target,sp=None,extra=(0,0,0)):
  oldpc,oldsp=self.word(2472),self.reg('esp');sp=oldsp if sp is None else sp
  self.projections.append((kind,oldpc,oldsp,target,sp,*extra));self.word(2472,target);self.reg('esp',sp);self.cursor=target
 def invoke_external(self,target,marker,api=None):
  oldpc,sp=self.word(2472),self.reg('esp');self.write(sp-4,marker,domain='research',pc=oldpc)
  self.project(1,target,sp-4,(marker,0,0));self.call_stack.append((target,sp-4,marker,0,self.reg('ebp'),self.reg('ebx'),self.reg('esi'),self.reg('edi'),0))
  self.run(stop=lambda m:m.cursor==marker,api=api)
  need(self.reg('esp')==sp,'Genuine external helper source RET frame')
  self.project(2,oldpc,sp,(0,0,0))
 def api_return(self,site,argc,result,outputs=()):
  """Only measured finite response effects; source registers/flags carried."""
  frame=self.reg('esp')
  for address,raw in outputs:
   for i in range(0,len(raw),4):self.write(address+i,int.from_bytes(raw[i:i+4],'little'),min(4,len(raw)-i),domain='transport',pc=site)
  ret=self.read((frame+self.word(BASE['ss']))&0xffffffff,domain='api',pc=site)
  if self.call_stack:
   f=self.call_stack.pop();need(f[1]==frame and f[2]==ret,'Finite API return consumes genuine current source caller frame')
  self.reg('eax',result);self.reg('esp',frame+4*(argc+1));self.word(2472,ret);self.cursor=ret
  self.emit('api-returned',site=site,frame=frame,target=ret)
 def step(self):
  pc=self.cursor;need(pc in self.program,'Unrecovered original source frontier '+hex(pc));row=self.program[pc]
  self.steps+=1;need(self.steps<=1000000,'Finite bounded source loop budget')
  self.word(2472,pc);self.PCs.append(pc);self.emit('instruction-before',row=row)
  op=row['mnemonic'];args=row['decoded_operands'];fall=(pc+row['width'])&0xffffffff;self.cursor=fall
  if op=='mov':self.destination(args[0],self.operand(args[1]))
  elif op=='movzx':self.destination(args[0],self.operand(args[1]))
  elif op=='lea':self.destination(args[0],self.address(args[1],lea=True))
  elif op=='push':self.push(self.operand(args[0]))
  elif op=='pop':self.pop(args[0]['register'])
  elif op=='leave':
   # The authenticated literal lowering checks the EBP-based read first,
   # then publishes both destination registers. This matters at a failed read.
   sp=self.reg('ebp');value=self.read((sp+self.word(BASE['ss']))&0xffffffff)
   self.reg('esp',sp+4);self.reg('ebp',value)
  elif op in ('call','jmp'):
   target=self.operand(args[0])
   if op=='call':
    self.push(fall);self.calls.append((pc,target,fall));self.call_stack.append((target,self.reg('esp'),fall,pc,self.reg('ebp'),self.reg('ebx'),self.reg('esi'),self.reg('edi'),(self.reg('eax')|0x80000000) if target==0x780058b5 else 0))
   self.word(2472,target);self.cursor=target;self.emit('control',op=op,site=pc,target=target)
  elif op=='ret':
   sp=self.reg('esp');target=self.read((sp+self.word(BASE['ss']))&0xffffffff)
   cleanup=args[0]['value'] if args else 0;self.word(2472,target);self.reg('esp',sp+4+cleanup);self.cursor=target
   self.returns.append((pc,target,sp))
   if self.call_stack:
    f=self.call_stack.pop();need(target==f[2],'Actual source RET current caller identity')
    if f[0]!=0x780058b5:need(sp==f[1],'Original source RET actual frame')
   else:f=None
   self.emit('returned',site=pc,target=target,frame=sp,caller=f)
  elif op.startswith('j'):
   if self.condition(op):self.cursor=args[0]['value']
   self.word(2472,self.cursor)
  elif op=='sete':self.destination(args[0],self.flag('ZF'))
  elif op in ('stosb','stosd','movsd'):
   size=1 if op=='stosb' else 4;count=self.reg('ecx') if row.get('repeat') else 1
   need(count<=262144,'Bounded original REP extent')
   for _ in range(count):
    if op=='movsd':value=self.read((self.reg('esi')+self.word(BASE['ds']))&0xffffffff,size)
    else:value=self.reg('eax')&((1<<(8*size))-1)
    self.write((self.reg('edi')+self.word(BASE['es']))&0xffffffff,value,size)
    delta=-size if self.flag('DF') else size
    self.reg('edi',self.reg('edi')+delta)
    if op=='movsd':self.reg('esi',self.reg('esi')+delta)
    if row.get('repeat'):self.reg('ecx',self.reg('ecx')-1)
  elif op in ('cmp','add','sub','sbb','inc','dec','neg','test','and','or','xor','shl','shr'):
   a=self.operand(args[0]);bits=args[0]['bits'];b=self.operand(args[1]) if len(args)>1 else 1
   if op in ('cmp','sub','sbb'):r=self.arith(a,b,bits,sub=True,carry=self.flag('CF') if op=='sbb' else 0)
   elif op=='add':r=self.arith(a,b,bits)
   elif op in ('inc','dec'):r=self.arith(a,1,bits,sub=op=='dec',preserve_cf=True)
   elif op=='neg':r=self.arith(0,a,bits,sub=True)
   elif op in ('test','and','or','xor'):
    r=self.logic((a&b) if op in ('test','and') else (a|b) if op=='or' else (a^b),bits)
   else:
    count=b&31;mask=(1<<bits)-1;a&=mask;r=a
    if count:
     r=((a<<count) if op=='shl' else (a>>count))&mask
     self.flag('CF',(a>>(bits-count))&1 if op=='shl' and count<=bits else (a>>(count-1))&1 if op=='shr' and count<=bits else 0)
     self.flag('PF',(r&255).bit_count()%2==0);self.flag('AF',0);self.flag('ZF',r==0);self.flag('SF',r>>(bits-1))
     self.flag('OF',((r>>(bits-1))^self.flag('CF')) if op=='shl' and count==1 else (a>>(bits-1)) if op=='shr' and count==1 else 0)
   if op not in ('cmp','test'):self.destination(args[0],r)
  else:raise ValueError('Original source operation not admitted '+op)
  # The current literal lowering chooses0 for each declared undefined callback.
  for offset in self.callbacks.get(pc,()):
   self.state[offset]=0;self.undefined.append((pc,offset,0));self.emit('undefined',pc=pc,offset=offset,value=0)
  self.emit('instruction-after',row=row)
 def run(self,stop,api=None):
  while not stop(self):
   if self.cursor not in self.program:
    need(api is not None,'Unresolved API or declared terminal');api(self,self.cursor)
   else:self.step()
  return self
 def result(self):
  return dict(state=bytes(self.state),fx=self.fx,cpu=self.cpu,memory=self.memory,PCs=self.PCs,accesses=self.accesses,
   API_reads=self.API_reads,transports=self.transports,external_accesses=self.external_accesses,projections=self.projections,calls=self.calls,returns=self.returns,undefined=self.undefined,phases=self.phases,
   AFTER_machine_seed=False,native_executed=False,API_executed=False,original_lower_stack_growth_proved=False)
