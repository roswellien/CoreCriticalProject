"""Pure cached1168 source phase for a persistent interpreter.

State, CPU, FX and memory are the caller's independently carried BEFORE.
Only declared typed source services are applied; opaque native CS bytes and
captured AFTER fields are never supplied to this derivation.
"""
from pathlib import Path
import importlib.util,struct,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def need(v,s):
 if not v:raise ValueError(s)
def module(p,name):
 spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
I=module(R/'tools/m4-crt-locale-batch-model-review/interpreter_v2.py','persistent_mfc_literal_integer')
F=module(R/'tools/m4-formatting-source/flag_domain.py','persistent_mfc_flag_domain')
class Literal(I.Machine):
 def cpu_now(self):
  flags=self.initial_flags
  for name,bit in F.BITS.items():flags=(flags&~(1<<bit))|(int(bool(self.flag(name)))<<bit)
  return tuple(self.reg(k)for k in ('eax','ecx','edx','ebx','esp','ebp','esi','edi'))+(flags,self.cursor)
 def read(self,address,size=4,domain='source',pc=None):
  source_PC=self.word(2472)if pc is None else pc;value=super().read(address,size,domain,pc)
  for v in self.inputs['imports']:
   if source_PC==v['pc']and address==v['cell']:
    need((size,value)==(4,v['raw'])and domain=='source','Literal current owning raw IAT preimage');self.projections.append(dict(access_index=len(self.accesses)-1,PC=source_PC,cell=address,raw=value,projected=v['projected']));self.accesses[-1]=(source_PC,address,v['projected'],size,0);return v['projected']
  return value
 def step(self):
  if self.cursor==0x780014b4:
   need(self.call_stack and self.call_stack[-1][0]==0x5f40107d and self.call_stack[-1][2]==0x5f4010b5,'Source-defined special imported EH return');self.call_stack.pop();outer=self.call_stack;self.call_stack=[]
   try:return super().step()
   finally:self.call_stack=outer
  return super().step()
def derive(state,fx,cpu,memory,inputs,contracts,return_PC=0x410a80):
 """Return machine and all source-derived phase relations; no native capture."""
 need(len(state)==3504 and len(fx)==512 and len(cpu)==40,'Complete independently carried caller machine');entry=struct.unpack('<10I',cpu);need(entry[4]==0x20001800 and entry[9]==0x5ae3e4,'Exact source root/current caller frame');program={r['pc']:r for r in contracts['instructions']};need(len(program)==142,'Exact finite normal source union');m=Literal(state,fx,cpu,memory,program=program,callbacks={});m.inputs=inputs;m.initial_flags=entry[8];m.call_stack.append((0x5ae3e4,entry[4],return_PC,0,m.reg('ebp'),m.reg('ebx'),m.reg('esi'),m.reg('edi'),0));API_relations=[];index=0;domain={};flags=[]
 while m.cursor!=return_PC:
  need(m.cursor in program,'Unproved lazy/callback source path denied');r=program[m.cursor];need(m.bytes(r['pc'],r['width'])==bytes.fromhex(r['bytes_hex']),'Whole physical literal source span');domain=F.advance(m,r,domain);m.step();flags.append(dict(PC=r['pc'],undefined_flags=dict(domain)))
  if m.cursor not in program and m.cursor!=return_PC:
   need(index<4,'Finite typed API count');spec=contracts['normal_APIs'][index];imp=inputs['imports'][index+3];need(m.cursor==imp['projected']and m.call_stack and m.call_stack[-1][2]==spec['return_PC'],'Exact source-defined typed API target/current CALL');before=m.cpu_now();frame=m.reg('esp');frame64=m.bytes(frame,64);need(struct.unpack_from('<I',frame64)[0]==spec['return_PC'],'Actual source-derived typed API return frame');expected_arg=inputs['role_owners'][1]['new']if index==0 else inputs['guest_CS'];need(not spec['argc']or struct.unpack_from('<I',frame64,4)[0]==(3 if index==0 else expected_arg),'Finite source TLSindex3/CS24 argument')
   result=expected_arg if index==0 else 1252 if index==2 else 0;outputs=[]
   if index in (1,3):depth=1 if index==1 else 0;values=(0xfffffffe if depth else 0xffffffff,depth,inputs['guest_thread']if depth else 0);outputs=[(inputs['guest_CS']+4+4*k,struct.pack('<I',v))for k,v in enumerate(values)]
   m.api_return(spec['source_PC'],spec['argc'],result,outputs);API_relations.append(dict(index=index,spec=spec,target=imp['projected'],CPU_before=before,CPU_after=m.cpu_now(),frame64_hex=frame64.hex(),typed_result=result,CS_depth_before=(0,0,1,1)[index],CS_depth_after=(0,1,1,0)[index],guest_semantic_writes=[(a,b.hex())for a,b in outputs]));index+=1;domain={}
 need(index==4 and not m.call_stack and len(m.PCs)==142 and len(m.accesses)==113,'Complete literal/API/ordinary and EH frame closure')
 source=dict(root=0x5ae3e4,source_PCs=m.PCs,source_accesses=m.accesses,source_import_projections=m.projections,source_API_relations=API_relations,source_FS_writes=[v for v in m.accesses if v[1]==0x7ffde000 and v[4]],source_State_hex=bytes(m.state).hex(),source_CPU=m.cpu_now(),source_FX_hex=m.fx.hex(),source_borrowed_backings=[dict(**o,initial_hex=bytes(memory[o['new']]).hex(),source_final_hex=m.bytes(o['new'],o['extent']).hex())for o in inputs['role_owners']],flag_lifetimes=flags,source_AFTER_seed=False,opaque_hostCS40_copied_to_guest=False)
 return m,source
