"""Exact original observer guest PUSHFD shadow; literal source memory remains pure."""
from pathlib import Path
import importlib.util,hashlib,json,struct,sys
sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('constructor_v6_shadow_parent',Path(__file__).with_name('game_model_v6.py'));P=importlib.util.module_from_spec(s);s.loader.exec_module(P)
I=P.I;G=P.G;ROOTS=P.ROOTS;BITS=P.BITS;ActualAPIs=P.ActualAPIs;from_original_before=P.from_original_before;source_program=P.source_program
class Machine(P.Machine):
 def __init__(self,*args,original_observer_stack=False,**kwargs):
  super().__init__(*args,**kwargs);self.original_observer_stack=original_observer_stack;self.observer_shadow=None;self.observer_stores=[];self.observer_read_checks=0;self.observer_points={}
  if original_observer_stack:
   path=Path(__file__).resolve().parents[2]/'reports/m4-138-validation-review/constructor-observer-stack-spec-r2/spec.json';raw=path.read_bytes();I.need(hashlib.sha256(raw).hexdigest()=='8b45b01c56bc2e06e5702233bdefc589f1363bc3be79ec092ebed0cac37de0ce','Exact complete compiled original observer PUSHFD spec');spec=json.loads(raw);I.need(spec['passed'],'Physical observer PUSHFD source/link proof');self.observer_points={v['source_PC']:v for v in spec['points']};self.observer_shadow=bytearray(self.bytes(0x20001000,4096))
 def read(self,address,size=4,domain='source',pc=None):
  if self.observer_shadow is not None and domain=='source'and 0x20001000<=address and address+size<=0x20002000:
   I.need(self.bytes(address,size)==self.observer_shadow[address-0x20001000:address-0x20001000+size],'Exact earlier observer store is overwritten before every live source operand read');self.observer_read_checks+=1
  return super().read(address,size,domain,pc)
 def write(self,address,value,size=4,domain='source',pc=None):
  result=super().write(address,value,size,domain,pc)
  if self.observer_shadow is not None and 0x20001000<=address and address+size<=0x20002000:self.observer_shadow[address-0x20001000:address-0x20001000+size]=self.bytes(address,size)
  return result
 def step(self):
  if self.original_observer_stack and self.constructor_active and self.cursor in self.observer_points:
   spec=self.observer_points[self.cursor];cpu=list(self.projected_cpu());address=cpu[4]-4;I.need(0x20001000<=address and address+4<=0x20002000,'Exact physical observer guest PUSHFD bounded stack address');old=bytes(self.observer_shadow[address-0x20001000:address-0x20001000+4]);self.observer_shadow[address-0x20001000:address-0x20001000+4]=struct.pack('<I',cpu[8]);self.observer_stores.append(dict(root=self.constructor_root,source_PC=self.cursor,source_instruction_index=len(self.PCs),CPU=cpu,FX512_hex=bytes(self.fx).hex(),source_undefined_flags=dict(self.arch_undefined),observer_PUSHFD_PC=spec['observer_PUSHFD_PC'],observer=spec['observer'],kind=spec['kind'],address=address,old_shadow_hex=old.hex(),source_EFLAGS=cpu[8],write_bytes=4,write_hex=struct.pack('<I',cpu[8]).hex(),source_value_used=True,observed_endpoint_seed=False))
  return super().step()
 def result(self):
  result=super().result();result.update(original_observer_stores=self.observer_stores,original_observer_live_stack_read_checks=self.observer_read_checks,source_instrumented_upper_stack_hex=bytes(self.observer_shadow).hex()if self.observer_shadow is not None else None,observer_source_memory_changed=False);return result
