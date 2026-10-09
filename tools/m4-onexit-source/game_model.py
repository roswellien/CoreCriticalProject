"""Original BEFORE game instructions and exact bounded zero-vector x87 path.

This extends the independent provider interpreter. It never reads candidate
AFTER state/pages, uses a C++ float/long-double approximation, or runs an API.
Only the 4C58C0 default-zero constructor FP domain is admitted here.
"""
from pathlib import Path
import importlib.util, json, struct, sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-onexit-review'))
import provider_model as P
I=P.I
SF=((0,2755),(1,2753),(2,2751),(3,2749),(4,2747),(5,2745),(6,2757),(8,2737),(9,2739),(10,2741),(14,2743))
def u16(b,o):return struct.unpack_from('<H',b,o)[0]
def put16(b,o,v):struct.pack_into('<H',b,o,v&65535)

def source_program():
 p=ROOT/'reports/m4-onexit-source/interface-r1/instruction-contracts.json'
 q=ROOT/'reports/m4-onexit-source/game-callbacks-r2/callbacks.json'
 import hashlib
 I.need(hashlib.sha256(p.read_bytes()).hexdigest()=='3f0d96b381dc4e89dc7cb63c7f252414ba1392deae140718daba6e17c3d438d3','Frozen game source operand contract')
 I.need(hashlib.sha256(q.read_bytes()).hexdigest()=='df3f761e5672e290a01d8ef729f6bef3489d9d9a5520c532ee685e0d689d4076','Actual source undefined callback attribution')
 rows={r['pc']:r for r in json.loads(p.read_bytes())['instructions']}
 callbacks={int(k):tuple(v)for k,v in json.loads(q.read_bytes())['State_offsets_by_original_PC'].items()}
 return rows,callbacks

class Machine(P.Machine):
 """Literal integer/stack effects plus exact signed zero raw80 arithmetic."""
 def __init__(self,*args,**kwargs):
  super().__init__(*args,**kwargs);self.fp_depth=0;self.FP_PCs=[];self.import_projections=[]
 def projected_cpu(self):
  flags=0x202|sum(self.state[o]<<bit for bit,o in ((0,2065),(2,2067),(4,2069),(6,2071),(7,2073),(10,2075),(11,2077)))
  return tuple(self.word(I.REG[x])for x in ('eax','ecx','edx','ebx','esp','ebp','esi','edi'))+(flags,self.word(2472))
 def fp_status(self):
  return (u16(self.state,2770)&0xb880)|sum(self.state[o]<<bit for bit,o in SF)
 def fp_set(self,bit,value):
  offset=dict(SF)[bit];self.state[offset]=int(bool(value))
 def fp_slots(self):return [bytes(self.state[2486+16*n:2496+16*n])for n in range(8)]
 def fp_slot(self,n,raw=None):
  I.need(0<=n<8,'Bounded logical raw80 slot')
  if raw is None:return bytes(self.state[2486+16*n:2496+16*n])
  I.need(len(raw)==10,'Exact raw80 value');self.state[2486+16*n:2496+16*n]=raw
 def fp_top(self,delta):
  old=u16(self.state,2770);put16(self.state,2770,(old&~0x3800)|((((old>>11)+delta)&7)<<11))
 def fp_push(self,raw):
  I.need(self.fp_depth<8,'Source zero-vector no x87 stack overflow')
  slots=self.fp_slots();self.fp_top(-1)
  for n,value in enumerate([raw]+slots[:7]):self.fp_slot(n,value)
  self.fp_depth+=1
 def fp_pop(self):
  I.need(self.fp_depth>0,'Source zero-vector no x87 stack underflow')
  slots=self.fp_slots();self.fp_top(1)
  for n,value in enumerate(slots[1:]+[slots[0]]):self.fp_slot(n,value)
  self.fp_depth-=1
 def zero80(self,negative=False):return bytes(9)+bytes([0x80 if negative else 0])
 def zero_sign(self,raw):
  I.need(raw in (self.zero80(),self.zero80(True)),'Only literal exact-zero FP domain admitted')
  return raw[-1]>>7
 def fp_value(self,operand):
  if operand['kind']=='x87_register':
   I.need(operand['index']<self.fp_depth,'Only current live source x87 operand');return self.fp_slot(operand['index'])
  I.need(operand['kind']=='memory'and operand['bits']==32,'Bounded default-vector DWORD FP input')
  bits=self.read(self.address(operand),4);I.need(bits in (0,0x80000000),'Literal default-vector zero FP input')
  return self.zero80(bits>>31)
 def fp_meta(self,row,memory_operand=None):
  raw=bytes.fromhex(row['bytes_hex']);put16(self.state,2774,((raw[0]&7)<<8)|raw[1]);self.word(2776,row['pc']);put16(self.state,2780,0x23)
  if memory_operand is not None:self.word(2784,self.address(memory_operand));put16(self.state,2788,0x2b)
 def read(self,address,size=4,domain='source',pc=None):
  value=super().read(address,size,domain,pc)
  if domain=='source' and size==4 and address in (0x5bb52c,0x5bb530):
   expected,target,site=(0x1decb0,0x78004a36,0x5ac11e)if address==0x5bb52c else(0x1deca2,0x78002fe5,0x5ac580)
   I.need(value==expected and self.word(2472)==site,'Declared exact owning game import projection')
   self.import_projections.append((5,site,address,value,target,0,0,0));return target
  return value
 def step(self):
  pc=self.cursor;row=self.program.get(pc);I.need(row is not None,'Recovered game/provider exact source PC')
  op=row['mnemonic']
  if not op.startswith('f'):return super().step()
  I.need(0x4c5960<=pc<0x4c5a29 or 0x4020d0<=pc<0x402132,'Only declared new zero-vector x87 bodies')
  self.steps+=1;I.need(self.steps<=1000000,'Bounded whole source interpreter');self.word(2472,pc);self.PCs.append(pc);self.FP_PCs.append(pc);self.emit('instruction-before',row=row)
  args=row['decoded_operands'];self.cursor=pc+row['width'];memop=next((a for a in args if a['kind']=='memory'),None)
  if op!='fnstsw':self.fp_meta(row,memop);self.fp_set(9,0)
  if op=='fld':self.fp_push(self.fp_value(args[0]))
  elif op=='fld1':raise ValueError('Nonzero normalization branch outside default-zero constructor domain')
  elif op=='fxch':
   n=args[0]['index'];I.need(n<self.fp_depth,'Live source FXCH');a,b=self.fp_slot(0),self.fp_slot(n);self.fp_slot(0,b);self.fp_slot(n,a)
  elif op in ('fst','fstp'):
   raw=self.fp_slot(0);sign=self.zero_sign(raw)
   if args[0]['kind']=='memory':self.write(self.address(args[0]),sign<<31,4)
   else:self.fp_slot(args[0]['index'],raw)
   if op=='fstp':self.fp_pop()
  elif op=='fsub':
   a,b=self.zero_sign(self.fp_slot(0)),self.zero_sign(self.fp_value(args[0]));rounddown=(u16(self.state,2768)>>10)&3==1
   sign=a if a==(b^1) else int(rounddown);self.fp_slot(0,self.zero80(sign))
  elif op=='fmul':
   if len(args)==2:left,right=args
   else:left,right=dict(kind='x87_register',index=0,bits=80),args[0]
   sign=self.zero_sign(self.fp_value(left))^self.zero_sign(self.fp_value(right));self.fp_slot(left['index'],self.zero80(sign))
  elif op=='faddp':
   left,right=args;sa,sb=self.zero_sign(self.fp_value(left)),self.zero_sign(self.fp_value(right));rounddown=(u16(self.state,2768)>>10)&3==1
   self.fp_slot(left['index'],self.zero80(sa if sa==sb else int(rounddown)));self.fp_pop()
  elif op=='fsqrt':self.fp_slot(0,self.zero80(self.zero_sign(self.fp_slot(0))))
  elif op=='fcomp':
   self.zero_sign(self.fp_slot(0));self.zero_sign(self.fp_value(args[0]));self.fp_set(8,0);self.fp_set(10,0);self.fp_set(14,1);self.fp_pop()
  elif op=='fnstsw':self.destination(args[0],self.fp_status())
  elif op=='fchs':self.fp_slot(0,self.zero80(not self.zero_sign(self.fp_slot(0))))
  else:raise ValueError('Unadmitted zero-vector source FP instruction '+op)
  for offset in self.callbacks.get(pc,()):
   self.state[offset]=0;self.undefined.append((pc,offset,0));self.emit('undefined',pc=pc,offset=offset,value=0)
  self.emit('instruction-after',row=row)

def begin_root(machine,entry,frame=0x20001800,marker=0x410a80):
 """One declared scheduler PC/SP projection and genuine external CALL frame."""
 I.need(machine.reg('esp')==frame+4,'Persistent source caller return SP')
 machine.write(frame,marker,domain='research',pc=marker);machine.reg('esp',frame);machine.word(2472,entry);machine.cursor=entry
 machine.call_stack.append((entry,frame,marker,0,machine.reg('ebp'),machine.reg('ebx'),machine.reg('esi'),machine.reg('edi'),0))

def complete_root(machine,marker=0x410a80,api=None):
 machine.run(stop=lambda m:m.cursor==marker,api=api)
 I.need(machine.reg('esp')==0x20001804 and not machine.call_stack and machine.fp_depth==0,'Genuine whole root RETURN and empty source x87 domain')
 return machine.result()
