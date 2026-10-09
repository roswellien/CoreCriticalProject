"""Callable original-BEFORE provider/bootstrap model for the shared game lane.

The accepted literal heap prefix supplies only predicted source effects. Finite
HeapCreate/GetVersionExA and typed allocation/CS API witnesses supply declared
API responses. No captured AFTER State, CPU, FX, stack or page is an input.
"""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys,types
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-onexit-review'))
import provider_model as P
import provider_responses_v2 as R
I=P.I
PREFIX_PINS={'consumer.py':'2d6f357baabea5e2fa750fb7d111bb81ab313e4fe39d05c8c613f23aef2606e8',
             'before.py':'819ec625f266e99c1ce6c7bd2209e030a00a29dd283b060c3c61b5d8aea97ea6',
             'prefix.py':'9f1eafac2333c97cc5192b0681e57d3968269617a13a1b25c7e649eb5dee716e'}
INTERFACE_SHA='9ab58b814dcc797f54b8929d7e2f8e9f9c022149b0daa40c2fe370884f6ab02d'
CALLBACK_SHA='3c0a5fab10ec834c8e027ed88a8443b7d63d559c151d40ade6a045a71ce1565d'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def source_checkpoint(state,fx,cpu,memory):
 """Observe only this model's computed machine, without unrelated old fields."""
 import copy
 return dict(state=bytes(state),fx=bytes(fx),cpu=bytes(cpu),memory=copy.deepcopy(memory))
def observation_only_prefix(prefix):
 """Keep sealed source computation; substitute its checkpoint serializer only.

 Earlier serializers require many unrelated CRT seam payloads. Their source
 prediction does not read those serialization fields. Function code is reused
 verbatim, with only stage and nested observation-only predict references bound.
 """
 memo={}
 def function(fn):
  if id(fn)in memo:return memo[id(fn)]
  g=dict(fn.__globals__);g['stage']=source_checkpoint
  result=types.FunctionType(fn.__code__,g,fn.__name__,fn.__defaults__,fn.__closure__);memo[id(fn)]=result
  if isinstance(g.get('first_prefix'),types.FunctionType):g['first_prefix']=function(g['first_prefix'])
  prior=g.get('prior')
  if isinstance(prior,types.ModuleType)and isinstance(getattr(prior,'predict',None),types.FunctionType):
   g['prior']=types.SimpleNamespace(**dict(vars(prior),predict=function(prior.predict)))
  return result
 return function(prefix.predict)
def material(output,pin):
 """Prepare original-only static heap rows once, with fresh named decode files."""
 core=ROOT/'tools/m4-crt-heap-return-root'
 for name,digest in PREFIX_PINS.items():pin(core/name,digest)
 previous={name:sys.modules.get(name)for name in('consumer','before')}
 try:
  consumer=load('onexit_bootstrap_consumer',core/'consumer.py');sys.modules['consumer']=consumer
  before=load('onexit_bootstrap_before',core/'before.py');sys.modules['before']=before
  prefix=load('onexit_bootstrap_prefix',core/'prefix.py')
 finally:
  for name,m in previous.items():
   if m is None:sys.modules.pop(name,None)
   else:sys.modules[name]=m
 heap_program,heap_pages,commands=prefix.source_material(Path(output))
 interface=pin(ROOT/'reports/m4-onexit-review/interface-r1/instruction-contracts.json',INTERFACE_SHA)
 callbacks=pin(ROOT/'reports/m4-onexit-review/callbacks-r1/callbacks.json',CALLBACK_SHA)
 rows,_=P.source_program(interface)
 cb={int(k):tuple(v)for k,v in json.loads(callbacks.read_bytes())['State_offsets_by_original_PC'].items()}
 for module in list(sys.modules.values()):
  path=getattr(module,'__file__',None)
  if path:
   q=Path(path).resolve()
   if q.is_relative_to(ROOT/'tools') and q.is_file():pin(q)
 pin(ROOT/'tools/m4-runtime/runtime.cpp')
 return dict(prefix=prefix,predict=observation_only_prefix(prefix),heap_program=heap_program,heap_pages=heap_pages,commands=commands,program=rows,callbacks=cb)
def bounded_tib(memory,state):
 """Admit the four explicit Runtime constructor mappings, leaving holes absent."""
 fs=struct.unpack_from('<I',state,I.BASE['fs'])[0]
 I.need(fs==0x7ffde000,'Exact declared Runtime constructor FS-base domain')
 result={p:bytearray(b)for p,b in memory.items()}
 for address,value in ((fs,0xffffffff),(fs+4,0x20002000),(fs+8,0x20001000),(fs+0x18,fs)):
  raw=struct.pack('<I',value)
  if address in result:I.need(result[address]==raw,'Explicit TIB BEFORE admission preserves any supplied original bytes')
  else:result[address]=bytearray(raw)
 return result
def cpu(state):
 flags=0x202|sum(state[I.FLAGS[k]]<<bit for k,bit in (('CF',0),('PF',2),('AF',4),('ZF',6),('SF',7),('DF',10),('OF',11)))
 return struct.pack('<10I',*(struct.unpack_from('<I',state,I.REG[r])[0]for r in('eax','ecx','edx','ebx','esp','ebp','esi','edi')),flags,struct.unpack_from('<I',state,2472)[0])
def bootstrap(before,facts,heap,material,machine_type,game_program,game_callbacks,restore_pc,restore_sp,hook=None):
 """Return one predicted persistent machine and API owner at bootstrap return.

 before has state/fx/cpu/memory at registry-bootstrap-before (5BB514). restore_pc/SP are
 declared scheduler inputs from the independently established calling context.
 heap has create16Q,registry18Q,query20Q,input148B,output148B actual API facts.
 """
 w,h,q=tuple(heap['create']),tuple(heap['registry']),tuple(heap['query'])
 I.need(len(w)==16 and len(h)==18 and len(q)==20,'Exact inherited finite bootstrap witness widths')
 I.need(w[0:6]==(1,0,1,0,4096,0) and w[6] and w[7]==0x48450001 and w[11]==w[6],
        'Actual successful source HeapCreate flags0/initial4096/max0 and owned opaque token')
 I.need(h[0]==1 and h[4]==w[6] and h[5] and h[8]==1,'Exactly one actual private bootstrap heap acquisition')
 I.need(w[12:16]==(0x20001848,0x780039d6,0x20001858,0x780039d6),
        'Actual source-derived genuine HeapCreate stdcall frame and return')
 I.need(q[0:3]==(1,1,1) and q[3] and q[4:8]==(148,0x200017b8,0x20000618,0x78003a31)
        and q[8]==q[10] and q[11:18]==(37,1,1,1,1,1,0),'Complete actual finite mode1 version-query response and genuine stdcall')
 response=dict(input=bytes(heap['input']),output=bytes(heap['output']),result=q[3])
 I.need(len(response['input'])==len(response['output'])==148 and struct.unpack_from('<I',response['output'],4)[0]==q[18]
        and struct.unpack_from('<I',response['output'],16)[0]==q[19],'Actual immutable complete query output bytes')
 state=bytes(before['state']);fx=bytes(before['fx']);runtime_cpu=bytes(before['cpu'])
 I.need(struct.unpack_from('<I',state,2472)[0]==0x5bb514 and struct.unpack_from('<I',state,I.REG['esp'])[0]==0x20001860
        and runtime_cpu==cpu(state),'Declared bootstrap PC/SP projection matches source-computed CPU')
 memory=bounded_tib(before['memory'],state)
 entry=types.SimpleNamespace(state=state,fx=fx,runtime_cpu=runtime_cpu,mem=memory)
 predicted=material['predict'](entry,material['heap_program'],w[7],response)
 I.need(predicted['initializer_RET'] and predicted['heap_mode_value']==1,'Literal original source publishes mode1 and returns')
 program=dict(material['program']);callbacks=dict(material['callbacks'])
 for pc,row in game_program.items():I.need(pc not in program or program[pc]==row,'Disjoint or identical original game/provider rows');program[pc]=row
 for pc,offsets in game_callbacks.items():I.need(pc not in callbacks or callbacks[pc]==offsets,'Identical source callback offsets');callbacks[pc]=offsets
 m=machine_type(predicted['state'],fx,predicted['cpu'],predicted['memory'],program=program,callbacks=callbacks,hook=hook)
 m.PCs=list(predicted['PCs']);m.accesses=list(predicted['accesses'])
 m.API_reads=[predicted['API_return_access'],predicted['query_return_access']]
 m.undefined=[(pc,I.FLAGS['AF'],value)for pc,value in predicted['undefined']]
 # The accepted inherited prefix keeps query output transport separate from
 # the locale transport ledger; both remain independently observable.
 m.bootstrap_query_transports=list(predicted['query_output_accesses'])
 responses=R.ActualResponses(facts);m.responses=responses
 m.snapshot('allocation-caller-before');m.run(lambda x:x.cursor==0x7800184c);m.snapshot('allocation-caller-after')
 m.snapshot('locale-batch-before');m.invoke_external(0x78003bf4,0xffffffc0,responses);m.snapshot('locale-static-locks-returned')
 I.need(len(responses.sections)==4 and responses.index==4,'Genuine four static lock initializations')
 m.project(3,0x5ac3d8,0x20001860);m.run(lambda x:x.cursor==0x5ac3ec);m.snapshot('registry-producer-before')
 m.invoke_external(0x78004482,0xffffff90,responses);m.snapshot('registry-producer-after')
 empty=responses.completed_registry(m,())
 I.need(responses.index==5 and empty['begin']==empty['next'] and m.bytes(empty['begin'],4)==bytes(4),
        'Genuine producer malloc128 publishes an owned empty vector')
 m.reg('esp',restore_sp);m.word(2472,restore_pc);m.cursor=restore_pc;m.cpu=cpu(m.state);m.snapshot('registry-bootstrap-returned')
 m.bootstrap_prefix=predicted
 return m,responses
