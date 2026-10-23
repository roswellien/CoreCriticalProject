"""Finite literal sort from authentic file BEFORE; no executable DLL load.

The ambient CALL machine is explicitly synthetic, not a captured DllMain
machine. The accepted integer interpreter and source-decoded operands predict
all table/string/frame effects. This proves this finite table algorithm only.
"""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,struct,sys,time,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def need(v,s):
 if not v:raise ValueError(s)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(n,p):
 spec=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
CONSUMERS={'je':('ZF',),'jne':('ZF',),'jb':('CF',),'jae':('CF',),'jbe':('CF','ZF'),'ja':('CF','ZF'),'jl':('SF','OF'),'jge':('SF','OF'),'jle':('ZF','SF','OF'),'jg':('ZF','SF','OF'),'setl':('SF','OF'),'sbb':('CF',)}
class SourceEval:
 def __init__(self,out,pin):
  self.out=out;self.pin=pin;self.I=load('message_accepted_integer',pin(R/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py'));self.D=load('message_source_decode',pin(R/'tools/m4-crt-locale-batch-recovery/recover_v2.py'));self.F=load('message_source_flags',pin(R/'tools/m4-formatting-source/flag_domain.py'))
  sys.path.insert(0,str(R/'tools/m4-onexit-review'));self.P=load('message_accepted_SAR',pin(R/'tools/m4-onexit-review/provider_model.py'))
  self.PE=load('message_source_PE',pin(R/'tools/analysis/pe.py'));self.image=self.PE.PEImage(pin(R/'MW3/Mech3Msg.dll','8899fabb7e57383a9a483cb048636bcc027334b48941aa49835cdcc1c4715b8c').read_bytes());self.before={};self.regions=[]
  pe=self.image
  for s in pe.sections:
   va=pe.image_base+s['virtual_address'];n=max(s['virtual_size'],s['raw_size']);buf=bytearray(n);buf[:s['raw_size']]=pe.read(s['raw_offset'],s['raw_size']);self.before[va]=bytes(buf);self.regions.append(dict(base=va,end=va+n,readable=s['readable'],writable=s['writable'],name=s['name']))
  g=json.loads(pin(R/'reports/m4-loader-message-review/physical-r4/current-physical-CFG.json').read_bytes());pcs=set(g['closures']['sort']['physical_PCs']);need(len(pcs)==952 and g['closures']['sort']['dynamic_CFG_closed'],'Closed952 literal source instructions');rows={r['pc']:r for r in g['rows']};self.program={}
  for pc in sorted(pcs):
   row=rows[pc];raw=bytes.fromhex(row['bytes']);off=pe.rva_range(pc-pe.image_base,len(raw))[0];need(pe.read(off,len(raw))==raw,'Exact physical instruction bytes');d=dict(pc=pc,mnemonic=row['mnemonic'],operands=re.sub(r'\s+<[^>]+>','',row['operands']),width=row['size'],bytes_hex=row['bytes']);self.program[pc]=self.D.instruction_contract(d)
  self.opcounts=collections.Counter(d['mnemonic']for d in self.program.values());allowed={'mov','lea','push','pop','cmp','add','sub','sbb','inc','dec','test','and','or','xor','sar','setl','call','jmp','ret',*CONSUMERS};need(set(self.opcounts)<=allowed,'Only fully reviewed literal integer instruction subset')
  self.domain={};self.definitions={k:None for k in self.I.FLAGS};self.flag_joins=[];self.current_cpu=None;self.counts=collections.Counter();self.permissions=[]
 def cpu(self,m):
  flags=0x202|sum(m.flag(k)<<n for k,n in self.F.BITS.items());return tuple(m.reg(k)for k in('eax','ecx','edx','ebx','esp','ebp','esi','edi'))+(flags,m.word(2472))
 def hook(self,m,event,data):
  if event=='instruction-before':
   row=data['row'];pc=row['pc'];self.current_cpu=self.cpu(m)
   for flag in CONSUMERS.get(row['mnemonic'],()):
    need(flag not in self.domain and self.definitions[flag]is not None,'Every consumed flag independently source-defined, no ambient or undefined flag oracle');self.flag_joins.append((pc,self.definitions[flag],self.F.BITS[flag]));self.counts['source_defined_flag_consumers']+=1
   new=self.F.advance(m,row,self.domain);op=row['mnemonic'];defined=set()
   if op in('add','sub','sbb','cmp'):defined=set(self.F.ARITH)
   elif op in('inc','dec'):defined=set(self.F.ARITH)-{'CF'}
   elif op in('and','or','xor','test'):defined={'CF','PF','ZF','SF','OF'}
   elif op=='sar'and self.F.count(m,row['decoded_operands'][1]):defined={'PF','ZF','SF','CF'}|({'OF'}if self.F.count(m,row['decoded_operands'][1])==1 else set())
   for flag in defined:self.definitions[flag]=pc
   self.domain=new
  elif event=='instruction-after':
   row=data['row'];self.trace.write(struct.pack('<I20I',row['pc'],*self.current_cpu,*self.cpu(m)));self.counts['literal_instruction_steps']+=1
  elif event in('read-before','write-before'):
   address,size,pc=data['address'],data['bytes'],data['pc'];owners=[r for r in self.regions if r['base']<=address and address+size<=r['end']];need(len(owners)==1,'Single owned source access region');owner=owners[0];need(owner['readable'],'Physical source-readable access');write=event=='write-before'
   if write:need(owner['writable']and(owner['name']=='declared-call-stack'or 0x10003010<=address and address+size<=0x10006158),'Literal source store confined to physical table or genuine stack')
   self.counts[('writes_'if write else'reads_')+owner['name']]+=1
 def evaluate(self):
  S=self
  class Machine(self.P.Machine):
   def step(self):
    row=self.program[self.cursor]
    if row['mnemonic']!='setl':return super().step()
    self.steps+=1;S.I.need(self.steps<=1000000,'Finite source evaluation budget');self.word(2472,self.cursor);self.PCs.append(self.cursor);self.emit('instruction-before',row=row);self.cursor+=row['width'];self.destination(row['decoded_operands'][0],bool(self.flag('SF'))!=bool(self.flag('OF')));self.emit('instruction-after',row=row)
  stack=0x20000000;size=0x20000;sp=stack+size-0x100;marker=0xf17ef17e;initial=bytearray(3504);fx=bytes(512);cpu=bytes(40);memory=dict(self.before);memory[stack]=bytes(size);self.regions.append(dict(base=stack,end=stack+size,readable=True,writable=True,name='declared-call-stack'));m=Machine(initial,fx,cpu,memory,self.program,{},self.hook)
  registers=dict(eax=0x11112222,ecx=0x33334444,edx=0x55556666,ebx=0x77778888,esp=sp+4,ebp=0x9999aaaa,esi=0xbbbbcccc,edi=0xddddeeee)
  for k,v in registers.items():m.reg(k,v)
  m.flag('DF',0);initial_state=bytes(m.state);initial_cpu=struct.pack('<10I',*self.cpu(m));self.emit('declared-before-State.bin',initial_state);self.emit('declared-before-CPU.bin',initial_cpu);self.emit('declared-before-FX.bin',fx)
  self.emit('source-program.json',json.dumps(dict(rows=list(self.program.values()),opcounts=dict(self.opcounts)),indent=2).encode())
  endpoints=[];tracepath=self.out/'source-PC-CPU-before-after.bin';self.trace=tracepath.open('wb')
  try:
   for ordinal in range(2):
    m.reg('esp',sp);m.store_bytes(sp,struct.pack('<I',marker));m.word(2472,0x10001000);m.cursor=0x10001000;m.call_stack.append((0x10001000,sp,marker,0,m.reg('ebp'),m.reg('ebx'),m.reg('esi'),m.reg('edi'),0));beforesteps=m.steps;beforecalls=len(m.calls);m.run(lambda x:x.cursor==marker)
    need(not m.call_stack and m.reg('esp')==sp+4,'Genuine complete declared CALL/RET stack balance')
    for reg in('ebx','ebp','esi','edi'):need(m.reg(reg)==registers[reg],'Literal callee-preserved register '+reg)
    raw=m.bytes(0x10003010,1577*8);expected=self.pin(R/'reports/m4-loader-message-review/physical-r4/current-sorted-table-design.bin').read_bytes();need(raw==expected,'All1577 authentic name-pointer/id pairs predict exact candidate design endpoint')
    for va,b in self.before.items():
     actual=bytes(m.memory[va]);lo=max(va,0x10003010);hi=min(va+len(b),0x10006158)
     if lo<hi:need(actual[:lo-va]==b[:lo-va]and actual[hi-va:]==b[hi-va:],'Every image byte outside table retained')
     else:need(actual==b,'Entire physical non-table image retained')
    self.emit('source-sorted-table-'+str(ordinal)+'.bin',raw);self.emit('source-State-'+str(ordinal)+'.bin',bytes(m.state));self.emit('source-CPU-'+str(ordinal)+'.bin',struct.pack('<10I',*self.cpu(m)));endpoints.append(dict(ordinal=ordinal,persistent_machine_reused=ordinal>0,steps=m.steps-beforesteps,recursive_calls=len(m.calls)-beforecalls,table_sha256=hashlib.sha256(raw).hexdigest(),all_image_bytes_outside_table_retained=True,callee_preserved_registers=True,genuine_stack_balanced=True))
  finally:self.trace.close()
  self.pin(tracepath);self.emit('source-operands.bin',b''.join(struct.pack('<5I',*row)for row in m.accesses));self.emit('source-defined-flag-joins.bin',b''.join(struct.pack('<3I',*row)for row in self.flag_joins));self.emit('source-call-returns.json',json.dumps(dict(calls=m.calls,returns=m.returns),indent=2).encode());self.emit('source-final-stack.bin',bytes(m.memory[stack]));need(m.fx==fx and not m.API_reads and not m.transports and not m.external_accesses,'No API or captured-result/AFTER transport')
  return dict(endpoints=endpoints,counts=dict(self.counts),static_literal_instructions=len(self.program),actually_reached_distinct_source_PCs=len(set(m.PCs)),source_operands=len(m.accesses),trace_schema='<I20I: sourcePC, BEFORE projected CPU40, AFTER projected CPU40',operand_schema='<5I: sourcePC,address,value,width,write',flag_join_schema='<3I: consumerPC,definingPC,EFLAGSbit',ambient_CALL_machine_synthetic=True,authentic_initial_image_file_owned=True,source_defined_all_consumed_flags=True,initial_FX_unchanged=True,API_executed=False,source_table_endpoint_equal=True)
 def emit(self,name,raw):
  p=self.out/name;p.write_bytes(raw);self.pin(p)
def main():
 out=R/'reports/m4-loader-message-review/literal-sorter-evaluation-r1';need(not out.exists(),'Fresh finite source evaluation');out.mkdir(parents=True);pins={};passed=False;result={};t=time.monotonic()
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);need(h is None or v==h,'Exact physical evaluation input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable physical evaluation input');pins[str(p)]=v;return p
 try:
  for p in [R/'reports/m4-loader-message-review/physical-r4/report.json',R/'reports/m4-loader-message-review/native-preparation-r1/report.json',R/'reports/m4-loader-message-review/literal-sorter-lifts-r1/report.json']:pin(p)
  result=SourceEval(out,pin).evaluate();passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  pin(__file__);pin(sys.executable)
  q=out/'report.json';q.write_text(json.dumps(dict(passed=passed,scope='Finite physical literal sorter/table source prediction on authentic current file BEFORE and declared synthetic CALL machine, twice persistent; no loader/DllMain/captured caller equivalence',**result,seconds=time.monotonic()-t,native_executed=False,DLL_loaded=False,archive_reader_opened=False,real_loader_runtime_CPU_or_host_State_claim=False,whole_CRT_entry_or_lifecycle_equivalence=False,whole_native_provider_source_equivalence=False,initializer_credit=0,files=pins),indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q),counts=result.get('counts',{}))))
if __name__=='__main__':main()
