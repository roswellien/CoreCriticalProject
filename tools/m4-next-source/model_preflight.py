"""Declared BEFORE-only four-root model preflight, no execution credit.

This checks reached physical source control and trace mechanics on explicit
source-only inputs. The real original/native captures remain mandatory.
"""
from pathlib import Path
import hashlib,importlib.util,json,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
G=load('fixed120_preflight_model','tools/m4-next-source/game_model.py')
V=load('fixed120_preflight_trace','tools/m4-next-source/indirect_trace.py')
PE=load('fixed120_preflight_PE','tools/analysis/pe.py')
pe=PE.PEImage((ROOT/'MW3/Mech3.exe').read_bytes())
contract=json.loads((ROOT/'reports/m4-next-source/recovery-r1/instruction-contracts.json').read_bytes())
def mapped_page(address):
 result=bytearray(4096);rva=address-pe.image_base
 for section in pe.sections:
  lo=max(rva,section['virtual_address']);hi=min(rva+4096,section['virtual_address']+section['raw_size'])
  if hi>lo:off=section['raw_offset']+lo-section['virtual_address'];result[lo-rva:hi-rva]=pe.data[off:off+hi-lo]
 return result
class Machine(G.Machine):
 def step(self):V.before_step(self);result=super().step();V.after_step(self);return result
program,callbacks=G.source_program();rows=[]
for item in contract['roots']:
 memory={page:mapped_page(page) for page in contract['source_data_pages']};memory[0x20001000]=bytearray(4096);memory[0x7ffde000]=bytearray(struct.pack('<I',0xffffffff))
 state=bytearray(3504)
 for reg,value in zip(('eax','ecx','edx','ebx','esp','ebp','esi','edi'),(0x13579bdf,0x2468ace0,0x81726354,0x10293847,0x20001800,0x92837465,0x56473829,0xaabbccdd)):
  struct.pack_into('<I',state,G.I.REG[reg],value)
 struct.pack_into('<I',state,2472,item['entry']);struct.pack_into('<I',state,2168,0x7ffde000)
 model=Machine(state,bytes(512),bytes(40),memory,program=program,callbacks=callbacks);model.write(0x20001800,0x410a80,domain='research',pc=0x410a80)
 model.call_stack.append((item['entry'],0x20001800,0x410a80,0,model.reg('ebp'),model.reg('ebx'),model.reg('esi'),model.reg('edi'),0))
 V.configure(model,lambda m:(bytes(512),bytes(28)),dict(root=item['entry'],declared_source_only_input=True))
 model.run(stop=lambda m:m.cursor==0x78004a36,api=lambda m,t:(_ for _ in()).throw(ValueError('No API in pure source prefix')))
 expected=[r for r in V.INPUTS.values()if r['root']==item['entry']]
 assert len(model.indirect_derivations)==len(expected)and not model.indirect_pending
 rows+=model.indirect_derivations
out=ROOT/'reports/m4-next-source/model-preflight-r1';assert not out.exists();out.mkdir()
(out/'source-only-derivations.json').write_text(json.dumps(rows,indent=2)+'\n')
files={str((ROOT/path).resolve()):hashlib.sha256((ROOT/path).read_bytes()).hexdigest()for path in('tools/m4-next-source/game_model.py','tools/m4-next-source/indirect_trace.py','tools/m4-next-source/model_preflight.py','reports/m4-next-source/recovery-r1/instruction-contracts.json','MW3/Mech3.exe')}
r=dict(passed=True,scope='Declared source-only BEFORE input preflight of four literal normal prefixes and observation-only tracing; no original/native execution or admission',roots=4,derived_source_calls=len(rows),AFTER_machine_seed=False,initializer_credit=False,files=files)
(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(dict(passed=True,calls=len(rows),sha256=hashlib.sha256((out/'report.json').read_bytes()).hexdigest())))
