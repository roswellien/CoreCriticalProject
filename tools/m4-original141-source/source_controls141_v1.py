"""Bounded causal controls only; invoke after independent physical admission.

The existing genuine original18 own input is only a control fixture. It does
not authenticate an original141 execution endpoint or connected chronology.
"""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,struct,sys,types
R=Path(__file__).resolve().parents[2]
def controls(pin):
 tests=[]
 def load(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def reject(name,f):
  try:f()
  except (ValueError,AssertionError):tests.append(dict(name=name,rejected=True));return
  raise AssertionError('Unrefused control '+name)
 D=load(R/'tools/m4-original141-source/derive_source141_v1.py','control_current_constructor')
 fixture=json.loads(pin(R/'reports/m4-138-validation-review/constructor-original18-source-r4/original-0-4260848/input.json').read_bytes())
 prep=pin(R/'reports/m4-constructor-native/source-comparison-preparation-r1/report.json');program,callbacks=D.M.source_program(prep)
 def machine():return D.M.Machine(D.M.from_original_before(fixture),bytes.fromhex(fixture['BEFORE_FX_hex']),bytes.fromhex(fixture['BEFORE_CPU_hex']),{int(k):bytes.fromhex(v)for k,v in fixture['BEFORE_memory'].items()},program=program,callbacks=callbacks,owner_roles=copy.deepcopy(fixture['owners']),source_imports={},original_observer_stack=True)
 m=machine();at=0x200017fc;old=m.bytes(at,4);wrong=bytes([old[0]^1])+old[1:];m.observer_shadow[at-0x20001000:at-0x20001000+4]=wrong
 reject('Source read rejects exact earlier observer clobber',lambda:m.read(at,4))
 reject('API memory rejects exact earlier observer clobber',lambda:m.observer_live_bytes(at,4))
 reject('One-byte overlapping API memory rejects observer clobber',lambda:m.observer_live_bytes(at-3,4))
 m.write(at,int.from_bytes(old,'little'));m.read(at,4);m.observer_live_bytes(at,4);tests.append(dict(name='Only actual later literal write restores source transparency',passed=True))
 m=machine();sp=m.reg('esp');m.observer_shadow[sp-0x20001000]^=1;response=D.M.ActualAPIs([dict(argc=3,args=[0,0,16],initial_allocations=[],input_buffers=[])]);reject('Real saved API return is checked before any volatile response',lambda:response(m,0))
 m=machine();sp=m.reg('esp');m.observer_shadow[sp+7-0x20001000]^=1;response=D.M.ActualAPIs([dict(argc=3,args=[0,0,16],initial_allocations=[],input_buffers=[])]);reject('Real API argument byte is checked before any volatile response',lambda:response(m,0))
 # Source-computed shadow STORE block is the unchanged whole V8 algorithm.
 model=pin(R/'tools/m4-original141-source/observer_shadow141_v1.py');tree=ast.parse(model.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef));step=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='step');block=ast.unparse(step.body[0]);spec=json.loads(pin(R/'reports/m4-original141/PUSHFD-preparation-r2/spec.json','da8a35a834970303ef3ded3465c0cb82d548761dfcded82e40b282563cf7b215').read_bytes());assert len(spec['points'])==11
 def need(v,s):
  if not v:raise ValueError(s)
 class Fake:
  def __init__(self,p,flags):
   self.original_observer_stack=True;self.constructor_active=True;self.cursor=p['source_PC'];self.observer_points={self.cursor:p};self.observer_shadow=bytearray(4096);self.observer_stores=[];self.constructor_root=0x4103f0;self.PCs=[1]*19;self.fx=bytearray(512);self.arch_undefined={'AF':0x1234};self.flags=flags
  def projected_cpu(self):return [0,1,2,3,0x20001f00,5,6,7,self.flags,self.cursor]
 for p in spec['points']:
  for flag in(0x202,0x8d5):
   m=Fake(p,flag);exec(compile(block,'literal current constructor PUSHFD','exec'),dict(self=m,I=types.SimpleNamespace(need=need),struct=struct));e=m.observer_stores[0];assert e['address']==0x20001efc and e['write_hex']==struct.pack('<I',flag).hex()and e['source_undefined_flags']=={'AF':0x1234}and e['source_EFLAGS']==flag and not e['observed_endpoint_seed'];assert e['observer_PUSHFD_PC']==p['observer_PUSHFD_PC']and e['source_PC']==p['source_PC']and e['kind']==p['kind'];tests.append(dict(name=p['observer']+' source-computed flag'+hex(flag),passed=True))
 B=load(R/'tools/m4-startup138-paired/registry_backing_policy.py','control_whole_registry')
 for label,meta,raw,callback,birth in [('wrong-own-mode',[1,1,4,2],bytes(4),2,None),('missing-growth-input',[1,5,4,1],bytes(4),2,None),('growth-without-full-buffer',[1,1,4,1],bytes(4),2,{}),('wrong-full-prefix',[1,5,4,1],b'abcd',2,dict(old_begin=1,requested=20,source_CALL_pc=0x78011c27,return_word=0x78011c2d,pointer=8,initial=bytes(20)))]:reject(label,lambda meta=meta,raw=raw,callback=callback,birth=birth:B.derive(meta,raw,callback,birth))
 return dict(passed=True,tests=tests,control_fixture_original141_input=False,current_shadow_points=11,source_memory_or_AFTERMACHINE_seed=False,current_original141_execution_claim=False,canonical_reader_opened=False,worker_launched=False,initializer_credit=0)
if __name__=='__main__':raise SystemExit('ROOT admitted pin closure required; no standalone source controls')
