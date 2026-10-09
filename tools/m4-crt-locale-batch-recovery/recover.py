"""Exact static source closure and operand contracts for the whole locale unit."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import time
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2]
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import normalized,unique_object,verify_manifest
from paths import publish_bytes,workspace_path
PROVIDER_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
BASELINE_SHA='8b5e67e5ab25bd5bae54f5d16e943b4313d7ef329868d43c3603407b99e0b010'
ALLOC_SHA='5ea56445e5367a421a28251f5e097b72f0d8370cf232a2fb4734b6698f14c2c6'
SPANS=(('static-locks',0x78003bf4,0x78003c1d),
 ('default-stub',0x78003dd2,0x78003ddb),('setmbcp',0x78003ddb,0x78003e84),
 ('resolver',0x78003e84,0x78003eb1),('classification',0x78003eb1,0x78003fba),
 ('locale-map',0x78003fba,0x7800415d),('bounded-length',0x7800415d,0x78004187),
 ('string-type',0x78002e20,0x78002f32),('lock',0x78001055,0x780010b0),
 ('lock-cold',0x7800bba4,0x7800bbbc),('unlock',0x7800129e,0x780012b3),
 ('setmbcp-cold',0x7800e4e4,0x7800e615),('lcid',0x7800e615,0x7800e648),
 ('reset',0x7800e648,0x7800e671),('classification-cold',0x7800e671,0x7800e6fc),
 ('string-type-cold',0x7800f2f7,0x7800f339),('string-type-failure',0x7800f349,0x7800f350),
 ('locale-map-cold',0x7800f350,0x7800f39d),('locale-map-sort-or-failure',0x7800f3b5,0x7800f3e8),
 ('locale-map-zero-output',0x7800f3ff,0x7800f406),('bounded-length-cold',0x7800f406,0x7800f40b),
 ('memset',0x78001000,0x78001055),('memset-cold',0x78010cc6,0x78010cd9),
 ('stack-probe',0x780058b5,0x780058e6),('builder',0x7800bbbc,0x7800bc48),
 ('parser',0x7800bc48,0x7800bdfc))
API_ARGUMENTS={'InitializeCriticalSection':1,'EnterCriticalSection':1,'LeaveCriticalSection':1,
 'GetACP':0,'GetOEMCP':0,'GetCPInfo':2,'MultiByteToWideChar':6,'WideCharToMultiByte':8,
 'GetStringTypeA':5,'GetStringTypeW':4,'LCMapStringA':6,'LCMapStringW':6,'GetModuleFileNameA':3}
REG_WIDTH={**{v:32 for v in ('eax','ecx','edx','ebx','esp','ebp','esi','edi')},
 **{v:16 for v in ('ax','cx','dx','bx','sp','bp','si','di')},
 **{v:8 for v in ('al','ah','cl','ch','dl','dh','bl','bh')}}

def need(ok,why):
 if not ok:raise ValueError(why)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_bytes(),object_pairs_hook=unique_object)

def operand(text):
 text=text.strip()
 if text in REG_WIDTH:return dict(kind='register',register=text,bits=REG_WIDTH[text])
 memory=re.fullmatch(r'(?:(byte|word|dword|qword) ptr )?(?:(fs|es|ds|ss):)?\[(.+)\]',text)
 if memory:
  width,segment,expression=memory.groups();terms=[];displacement=0
  for sign,part in re.findall(r'([+-]?)([^+-]+)',expression.replace(' ','')):
   multiplier=-1 if sign=='-' else 1
   if part in REG_WIDTH:need(REG_WIDTH[part]==32,'32-bit effective address register');terms.append(dict(register=part,scale=multiplier))
   elif '*' in part:
    pieces=part.split('*');need(len(pieces)==2,'One source scale term')
    register=next((v for v in pieces if v in REG_WIDTH),None);scale=next((v for v in pieces if v.isdigit()),None)
    need(register is not None and REG_WIDTH[register]==32 and scale in ('1','2','4','8'),'Actual x86 indexed operand');terms.append(dict(register=register,scale=int(scale)*multiplier))
   else:displacement+=multiplier*int(part,0)
  return dict(kind='memory',bits={None:0,'byte':8,'word':16,'dword':32,'qword':64}[width],
              segment=segment or 'default',terms=terms,displacement=displacement&0xffffffff)
 return dict(kind='immediate',value=int(text,0)&0xffffffff,signed_text=text)

def instruction_contract(row):
 op=row['mnemonic'];args=[operand(v) for v in row['operands'].split(',')] if row['operands'] else []
 reads=[];writes=[]
 for i,value in enumerate(args):
  if value['kind']!='memory' or op=='lea':continue
  if op=='mov':(writes if i==0 else reads).append(i)
  elif op=='pop':writes.append(i)
  elif op in ('cmp','test','push','call','jmp','movzx','movsx'):reads.append(i)
  else:reads.append(i);writes.append(i) if i==0 else None
 implicit=[]
 if op=='push':implicit=[dict(kind='stack-write',bits=32,address='SSBASE+ESP-4',ordering='write before ESP publication')]
 if op=='pop':implicit=[dict(kind='stack-read',bits=32,address='SSBASE+incomingESP',ordering='ESP+4 published before checked read')]
 if op=='call':implicit=[dict(kind='stack-write',bits=32,address='SSBASE+ESP-4',value=row['pc']+row['width'],ordering='return store before ESP/EIP and callback')]
 if op=='ret':implicit=[dict(kind='stack-read',bits=32,address='SSBASE+ESP',ordering='read before EIP/ESP publication')]
 if op=='leave':implicit=[dict(kind='stack-read',bits=32,address='SSBASE+EBP',ordering='ESP=EBP then ESP+4 before checked saved-EBP read')]
 if op.startswith('stos'):implicit=[dict(kind='string-write',bits={'stosb':8,'stosw':16,'stosd':32}[op],address='ESBASE+EDI',value='low EAX',direction='actual DF',repeat=row.get('repeat'))]
 if op=='movsd':implicit=[dict(kind='string-read',bits=32,address='DSBASE+ESI'),dict(kind='string-write',bits=32,address='ESBASE+EDI',value='source DWORD',direction='actual DF')]
 flags={'add':'six arithmetic flags','sub':'six arithmetic flags','cmp':'six arithmetic flags','neg':'six arithmetic flags',
  'inc':'arithmetic except CF retained','dec':'arithmetic except CF retained','sbb':'six arithmetic flags including incoming CF',
  'xor':'CF/OF=0, PF/ZF/SF result, AF research representative','and':'CF/OF=0, PF/ZF/SF result, AF research representative',
  'or':'CF/OF=0, PF/ZF/SF result, AF research representative','test':'CF/OF=0, PF/ZF/SF result, AF research representative',
  'shl':'source count-qualified shift flags/representatives','shr':'source count-qualified shift flags/representatives',
  'sar':'source count-qualified shift flags/representatives'}.get(op,'retained')
 return dict(**row,decoded_operands=args,explicit_memory_reads=reads,explicit_memory_writes=writes,implicit_memory=implicit,flags=flags)

def main(name):
 started=time.perf_counter_ns();out=workspace_path(ROOT/'reports/m4-crt-locale-batch-recovery'/name,reports=True)
 need(re.fullmatch('recovery-r[1-9][0-9]*',name) and not out.exists(),'Fresh current whole-unit static recovery')
 files={}
 def add(p,h=None):
  p=Path(p).absolute();v=sha(p);k=normalized(str(p));need(h is None or h==v,'Exact physical static input '+str(p));need(k not in files or files[k]==v,'Unique physical static binding');files[k]=v;return p
 loader=add(ROOT/'tools/m4-crt/recover_provider.py');spec=importlib.util.spec_from_file_location('locale_batch_PE',loader);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 provider=add(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',PROVIDER_SHA);pe=module.PE(provider,PROVIDER_SHA)
 accepted=add(ROOT/'reports/m4-crt-allocation-root/acceptance-r1/report.json',BASELINE_SHA)
 alloc=add(ROOT/'reports/m4-crt-allocation-recovery/recovery-r1/report.json',ALLOC_SHA)
 need(read(accepted)['passed'] is True and read(alloc)['passed'] is True,'Frozen complete functional allocation source baseline')
 tool=add(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe','a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a')
 for p in (Path(__file__),Path(__file__).with_name('README.md'),Path(sys.executable),ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/paths.py'):add(p)
 initial=verify_manifest(files);out.mkdir(parents=True);spans={};instructions={};commands=[]
 def section(a,n):
  hits=[s for s in pe.sections if s[0]<=a-pe.base and a-pe.base+n<=s[0]+s[2]];need(len(hits)==1,'Unique full file-backed source extent');r,v,n,p,f=hits[0]
  return dict(rva=r,virtual_bytes=v,raw_bytes=n,raw_offset=p,permissions=f&0xe0000000,readable=bool(f&0x40000000),writable=bool(f&0x80000000),executable=bool(f&0x20000000))
 for label,start,end in SPANS:
  argv=[str(tool),'-d','--x86-asm-syntax=intel','--start-address='+hex(start),'--stop-address='+hex(end),str(provider)]
  cp=subprocess.run(argv,capture_output=True,timeout=30,creationflags=0x08000000);need(cp.returncode==0,'Actual fresh static disassembly')
  rows=[]
  for line in cp.stdout.decode().splitlines():
   m=re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)',line)
   if not m:continue
   pc=int(m[1],16);raw=bytes.fromhex(m[2]);need(start<=pc<end and pc+len(raw)<=end and pe.read(pc-pe.base,len(raw))==raw,'Exact literal instruction bytes')
   op=m[3];args=m[4].split(' <')[0].replace('\t',' ').strip();repeat=None
   if op in ('rep','repe','repz','repne','repnz'):repeat=op;op,args=args.split(None,1)
   row=dict(pc=pc,width=len(raw),bytes_hex=raw.hex(),mnemonic=op,operands=args)
   if repeat:row['repeat']=repeat
   rows.append(instruction_contract(row));instructions[pc]=rows[-1]
  raw=pe.read(start-pe.base,end-start);need(b''.join(bytes.fromhex(v['bytes_hex']) for v in rows)==raw,'Complete contiguous exact source body '+label)
  for suffix,data in (('.bin',raw),('-decode.stdout',cp.stdout),('-decode.stderr',cp.stderr)):
   p=out/(label+suffix);publish_bytes(p,data);add(p)
  spans[label]=dict(start=start,end_exclusive=end,bytes=end-start,sha256=sha(out/(label+'.bin')),section=section(start,end-start),instructions=rows)
  commands.append(dict(argv=argv,exit_code=cp.returncode,original_executed=False))
 imports=[];sites=[]
 for v in pe.imports():
  if v.get('name') not in API_ARGUMENTS:continue
  raw=struct.unpack('<I',pe.read(v['iat']-pe.base,4))[0];argc=API_ARGUMENTS[v['name']]
  imports.append(dict(**v,raw_IAT=raw,hint=struct.unpack('<H',pe.read(raw,2))[0],argument_DWORDs=argc,stdcall_frame_consumed_bytes=4+4*argc,
    guest_ABI_scope='Finite measured API response; no original internals or volatile-register equivalence',void=v['name'].endswith('CriticalSection')))
  for row in instructions.values():
   if row['mnemonic'] in ('call','jmp') and row['operands']=='dword ptr ['+hex(v['iat'])+']':
    sites.append(dict(pc=row['pc'],kind=row['mnemonic'],API=v['name'],IAT=v['iat'],raw_IAT=raw,return_word=row['pc']+row['width'] if row['mnemonic']=='call' else 'actual existing resolver caller return'))
 for pc in (0x78003c01,0x78003c09,0x78003c11,0x78003c19):
  sites.append(dict(pc=pc,kind='call',API='InitializeCriticalSection',IAT=0x7802e03c,raw_IAT=0x3444e,return_word=pc+2,register='esi'))
 data={}
 for label,address,n in (('lock-table',0x78037028,0xe8-0x28),('static-lock-storage',0x780370e8,96),
  ('codepage-descriptors',0x780378d0,240),('classification-tables',0x780379c0,0x840),
  ('descriptor-masks',0x780394f0,4),('string-scope-table',0x7802e350,12),('locale-scope-table',0x7802e3d0,24),
  ('NLS-wide-probe-input',0x7802e290,4),('NLS-ANSI-probe-input',0x7802f314,2)):
  raw=pe.read(address-pe.base,n);p=out/(label+'.bin');publish_bytes(p,raw);add(p)
  data[label]=dict(address=address,bytes=n,sha256=sha(p),section=section(address,n),file_identity_only=True)
 branches=[];allowed={0x780012b3:'accepted malloc',0x78001390:'accepted free',0x7800badb:'unresolved fatal _amsg_exit',0x7800ef03:'SEH handler identity only'}
 for row in instructions.values():
  if row['mnemonic'] not in ('call','jmp') and not row['mnemonic'].startswith('j'):continue
  if not row['operands'].startswith('0x'):continue
  target=int(row['operands'],16)
  branches.append(dict(pc=row['pc'],kind=row['mnemonic'],target=target,within_recovered_closure=target in instructions,
                       external_contract=allowed.get(target) if target not in instructions else None))
 need(all(v['within_recovered_closure'] or v['target'] in allowed for v in branches),'Every static normal branch/CALL dependency is explicit')
 contracts=out/'memory-specs.json';publish_bytes(contracts,(json.dumps(dict(schema='mw34-locale-batch-original-memory-specs-v1',instructions=list(instructions.values())),indent=2)+'\n').encode());add(contracts)
 p=out/'API-contracts.json';publish_bytes(p,(json.dumps(dict(imports=imports,sites=sorted(sites,key=lambda v:v['pc'])),indent=2)+'\n').encode());add(p)
 report=dict(schema='mw34-m4-locale-batch-static-recovery-v1',passed=True,scope='Complete selected locale/default/classification/NLS/parser source closure; no provider/native/API execution',
  provider_sha256=PROVIDER_SHA,baseline_acceptance_sha256=BASELINE_SHA,accepted_allocation_source_sha256=ALLOC_SHA,
  spans=spans,source_spans=len(spans),source_identity_bytes=sum(v['bytes'] for v in spans.values()),source_instruction_count=len(instructions),
  memory_specs_path=str(contracts),memory_specs_sha256=sha(contracts),imports=imports,API_sites=sorted(sites,key=lambda v:v['pc']),branches=branches,data=data,
  function_entries={label:a for label,a,b in SPANS},new_file_code_pages=sorted({a&~4095 for a in instructions}),
  static_lock_order=[dict(slot=s,pointer=struct.unpack('<I',pe.read(s-pe.base,4))[0],source_bytes=24) for s in (0x7803706c,0x7803705c,0x7803704c,0x7803702c)],
  normal_SEH=[dict(entry=0x78002e20,publish=0x78002e36,restore=0x78002efe,RET=0x78002f09,scope=0x7802e350),dict(entry=0x78003fba,publish=0x78003fd0,restore=0x78004151,RET=0x7800415c,scope=0x7802e3d0)],
  parser=dict(entry=0x7800bc48,RET=0x7800bdfb,first_call=0x7800bbf7,first_return=0x7800bbfc,second_call=0x7800bc2d,second_return=0x7800bc32,
              allocator_call=0x7800bc06,argv_store=0x7800bc39,argc_store=0x7800bc40,builder_RET=0x7800bc47),
  original_executed=False,native_component_executed=False,actual_API_executed=False,original_attach_proved=False,full_CRT_complete=False,whole_M4_complete=False,
  fatal_NULL_allocator_branch_executed=False,SEH_dispatch_proved=False,original_lower_stack_or_guard_growth_proved=False,
  source_commands=commands,files=files,initial_physical_closure=initial,physical_closure=verify_manifest(files),seconds=(time.perf_counter_ns()-started)/1e9)
 p=out/'report.json';publish_bytes(p,(json.dumps(report,sort_keys=True,indent=2)+'\n').encode());add(p)
 publish_bytes(out/'pins.json',(json.dumps(dict(schema='mw34-m4-locale-batch-recovery-pins-v1',files=files),sort_keys=True,indent=2)+'\n').encode())
 print(json.dumps(dict(passed=True,source_spans=len(spans),bytes=report['source_identity_bytes'],instructions=len(instructions),report_sha256=sha(p),pins_sha256=sha(out/'pins.json'))))

if __name__=='__main__':main(sys.argv[1])
