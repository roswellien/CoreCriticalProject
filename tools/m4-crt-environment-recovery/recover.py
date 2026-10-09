"""Exact original environment functional-unit recovery; no source execution."""
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
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-environment-recovery'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import normalized,unique_object,verify_manifest
from paths import publish_bytes,workspace_path

PROVIDER_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
DECODER_SHA='a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a'
ALLOC_ACCEPT_SHA='8b5e67e5ab25bd5bae54f5d16e943b4313d7ef329868d43c3603407b99e0b010'
LOCALE_SOURCE_SHA='2d1c4a3f41505358df0ba8aaf4ed31c4b90a08d18b8bdf5cf1ed3eed2d996170'
SPANS=(('environment-acquire',0x78003cf1,0x78003d9a),
 ('environment-acquire-cold',0x7800f0e5,0x7800f180),
 ('environment-vector',0x78004187,0x78004227),
 ('strlen',0x78002f32,0x78002fab),('strcpy-hot',0x78002fab,0x78002fe5),
 ('strcpy-cold',0x78003664,0x780036be),
 ('memcpy-forward-hot',0x7800160e,0x780016f5),
 ('memcpy-forward-cold',0x78010f05,0x78010f71),
 ('mainargs-outputs-and-return',0x7800ba76,0x7800ba99),
 ('mainargs-builder-return',0x7800ba9e,0x7800baa0),
 ('acquired-block-caller-publication',0x78001882,0x7800188c),
 ('environment-vector-caller',0x780018a6,0x780018ab),
 ('environment-fatal-cold',0x7800bdfc,0x7800be16))
APIS=((0x7802e0f0,'GetEnvironmentStringsW',0),(0x7802e0ec,'GetEnvironmentStrings',0),
 (0x7802e0e4,'FreeEnvironmentStringsW',1),(0x7802e0e0,'FreeEnvironmentStringsA',1),
 (0x7802e0e8,'WideCharToMultiByte',8))
REGISTER_CALLS={0x78003d10:(0x7802e0f0,'ebp'),0x7800f14d:(0x7802e0f0,'ebp'),
 0x78003d5a:(0x7802e0e8,'edi'),0x78003d7c:(0x7802e0e8,'edi')}

def need(ok,why):
 if not ok:raise ValueError(why)
def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def load(path):return json.loads(Path(path).read_bytes(),object_pairs_hook=unique_object)

def main(name):
 started=time.perf_counter();out=workspace_path(BASE/name,reports=True)
 need(re.fullmatch('recovery-r[1-9][0-9]*',name) and out.parent==BASE and not out.exists(),'Fresh owned static receipt')
 files={}
 def pin(path,expected=None):
  p=Path(path).resolve();h=sha(p);key=normalized(str(p));need(expected is None or h==expected,'Pinned exact physical source '+str(p));need(key not in files or files[key]==h,'Unique physical identity');files[key]=h;return p
 def module(path,name):
  spec=importlib.util.spec_from_file_location(name,pin(path));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
 parser=module(ROOT/'tools/m4-crt/recover_provider.py','environment_PE')
 semantics=module(ROOT/'tools/m4-crt-locale-batch-recovery/recover_v2.py','environment_static_operands')
 provider=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',PROVIDER_SHA);pe=parser.PE(provider,PROVIDER_SHA)
 decoder=pin(ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe',DECODER_SHA)
 previous=pin(ROOT/'reports/m4-crt-allocation-root/acceptance-r1/report.json',ALLOC_ACCEPT_SHA)
 locale=pin(ROOT/'reports/m4-crt-locale-batch-recovery/recovery-r2/report.json',LOCALE_SOURCE_SHA)
 need(load(previous)['passed'] and load(locale)['passed'],'Accepted allocator and frozen source recovery prerequisites')
 cached=pin(ROOT/'reports/m4-crt-mainargs/recovery-r3/provider-decode.stdout')
 for p in (Path(__file__),Path(__file__).with_name('README.md'),Path(sys.executable),ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/paths.py'):pin(p)
 initial=verify_manifest(files);out.mkdir(parents=True);spans={};instructions={};commands=[]
 def publish(label,data):
  p=out/label;publish_bytes(p,data);pin(p);return p
 def jsonfile(label,value):return publish(label,(json.dumps(value,sort_keys=True,indent=2)+'\n').encode())
 def section(address,n):
  candidates=[s for s in pe.sections if s[0]<=address-pe.base and address-pe.base+n<=s[0]+s[2]];need(len(candidates)==1,'Unique complete file-backed extent');rva,virtual,raw,offset,flags=candidates[0]
  return dict(rva=rva,virtual_bytes=virtual,raw_bytes=raw,raw_offset=offset,characteristics=flags,readable=bool(flags&0x40000000),writable=bool(flags&0x80000000),executable=bool(flags&0x20000000))
 for label,start,end in SPANS:
  argv=[str(decoder),'-d','--x86-asm-syntax=intel','--start-address='+hex(start),'--stop-address='+hex(end),str(provider)]
  cp=subprocess.run(argv,capture_output=True,timeout=30,creationflags=0x08000000);need(cp.returncode==0,'Successful pinned static decoder')
  rows=[]
  for line in cp.stdout.decode().splitlines():
   m=re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)',line)
   if not m:continue
   pc=int(m[1],16);raw=bytes.fromhex(m[2]);need(start<=pc<end and pc+len(raw)<=end and pe.read(pc-pe.base,len(raw))==raw,'Literal original instruction bytes')
   op=m[3];args=m[4].split(' <')[0].replace('\t',' ').strip();repeat=None
   if op in ('rep','repe','repz','repne','repnz'):repeat=op;op,args=args.split(None,1)
   row=dict(pc=pc,width=len(raw),bytes_hex=raw.hex(),mnemonic=op,operands=args)
   if repeat:row['repeat']=repeat
   row=semantics.instruction_contract(row)
   if op=='leave':row['implicit_memory']=[dict(kind='stack-read',bits=32,address='SSBASE+incomingEBP',ordering='Architectural saved EBP read; compiled ordering requires future exact IR audit')]
   need(pc not in instructions or instructions[pc]==row,'Exact overlapping instruction identity');instructions[pc]=row;rows.append(row)
  raw=pe.read(start-pe.base,end-start);need(b''.join(bytes.fromhex(r['bytes_hex']) for r in rows)==raw,'Complete exact selected source span '+label)
  p=publish(label+'.bin',raw);publish(label+'-decode.stdout',cp.stdout);publish(label+'-decode.stderr',cp.stderr)
  spans[label]=dict(start=start,end_exclusive=end,bytes=end-start,sha256=sha(p),section=section(start,end-start),instructions=rows)
  commands.append(dict(argv=argv,exit_code=0,source_executed=False))
 imports=[];api_sites=[]
 for slot,name,argc in APIS:
  hit=[x for x in pe.imports() if x['iat']==slot];need(len(hit)==1 and hit[0]['library']=='KERNEL32.dll' and hit[0]['name']==name,'Exact original import name including unsuffixed ANSI')
  raw=struct.unpack('<I',pe.read(slot-pe.base,4))[0];need(pe.text(raw+2)==name,'Raw original hint/name identity');item=dict(**hit[0],raw_IAT=raw,hint=struct.unpack('<H',pe.read(raw,2))[0],argc=argc,finite_stdcall_return_bytes=4*(argc+1),section=section(slot,4));imports.append(item)
  for row in instructions.values():
   if row['mnemonic']=='call' and row['operands']=='dword ptr ['+hex(slot)+']':api_sites.append(dict(pc=row['pc'],IAT=slot,name=name,raw_IAT=raw,register=None,return_pc=row['pc']+row['width']))
  for pc,(regslot,reg) in REGISTER_CALLS.items():
   if regslot==slot:
    need(instructions[pc]['mnemonic']=='call' and instructions[pc]['operands']==reg,'Exact original indirect-register call');api_sites.append(dict(pc=pc,IAT=slot,name=name,raw_IAT=raw,register=reg,return_pc=pc+instructions[pc]['width'],requires_source_register_dataflow=True))
 tables=[]
 for label,address,count,indices in (('memcpy-forward-alignment-table',0x780016f4,4,[1,2,3]),('memcpy-forward-DWORD-table',0x78001704,8,list(range(8))),('memcpy-forward-tail-table',0x78001728,4,list(range(4)))):
  raw=pe.read(address-pe.base,4*count);p=publish(label+'.bin',raw);values=struct.unpack('<'+'I'*count,raw);targets=[values[i] for i in indices];need(all(t in instructions for t in targets),'Every bounded forward jump-table target is recovered')
  tables.append(dict(label=label,address=address,bytes=len(raw),sha256=sha(p),values=values,admitted_indices=indices,targets=targets,section=section(address,len(raw))))
 external={0x780012b3:'accepted authentic mode1 malloc',0x78001390:'accepted authentic free',0x7800badb:'unresolved fatal _amsg_exit',0x78010f71:'memcpy overlap/backward domain not admitted; source destination/source ownership must prove disjoint'}
 branches=[];rets=[];indirect_jumps=[]
 for row in instructions.values():
  op=row['mnemonic'];args=row['operands']
  if op=='ret':rets.append(dict(pc=row['pc'],stack_effect='Actual source return read then ESP+4',scope='Static source identity only'))
  if op=='jmp' and not args.startswith('0x'):indirect_jumps.append(dict(pc=row['pc'],operand=args,domain='Exact forward memcpy jump tables with source-derived bounded index'))
  if op not in ('call','jmp') and not op.startswith('j'):continue
  if not args.startswith('0x'):continue
  target=int(args,16);branches.append(dict(pc=row['pc'],kind=op,target=target,recovered=target in instructions,external_contract=external.get(target)))
 need(all(x['recovered'] or x['target'] in external for x in branches),'Every direct source dependency explicitly recovered or bounded unresolved')
 data={}
 for label,address,n in (('environment-cache',0x780378c8,4),('acquired-ANSI-block-global',0x78037178,4),('environ-vector-global',0x78037c04,4),('argc-global',0x78038ef4,4),('argv-global',0x7803b3d8,4)):
  raw=pe.read(address-pe.base,n);p=publish(label+'.bin',raw);data[label]=dict(address=address,bytes=n,sha256=sha(p),section=section(address,n),file_identity_only=True)
 pages={}
 for address in sorted({pc&~4095 for pc in instructions}|{a['IAT']&~4095 for a in api_sites}|{v['address']&~4095 for v in data.values()}):
  raw=pe.read(address-pe.base,4096);p=publish('source-page-'+format(address,'08x')+'.bin',raw);pages[format(address,'08x')]=dict(address=address,bytes=4096,sha256=sha(p),section=section(address,4096),original_file_input_only=True)
 contract=dict(schema='mw34-environment-original-source-contract-v1',instructions=[instructions[p] for p in sorted(instructions)],branches=branches,returns=rets,imports=imports,API_sites=sorted(api_sites,key=lambda x:x['pc']),indirect_jumps=indirect_jumps,jump_tables=tables)
 c=jsonfile('source-contract.json',contract)
 report=dict(schema='mw34-m4-environment-static-recovery-v1',passed=True,scope='Complete selected environment acquisition/vector/mainargs functional-unit source plus exact forward-disjoint ANSI memcpy domain; no execution/lift/API credit',provider_sha256=PROVIDER_SHA,allocator_acceptance_sha256=ALLOC_ACCEPT_SHA,locale_source_sha256=LOCALE_SOURCE_SHA,source_contract_path=str(c),source_contract_sha256=sha(c),spans=spans,source_spans=len(spans),source_identity_bytes=sum(x['bytes'] for x in spans.values()),source_instruction_count=len(instructions),imports=imports,API_sites=sorted(api_sites,key=lambda x:x['pc']),branches=branches,returns=rets,jump_tables=tables,data=data,pages=pages,commands=commands,
  source_flow=dict(acquire_entry=0x78003cf1,acquire_RET=0x78003d99,acquire_call=0x78001882,acquire_return=0x78001887,acquired_global=0x78037178,vector_entry=0x78004187,vector_RET=0x78004226,vector_global_store=0x780041bd,vector_global=0x78037c04,old_block_free_call=0x78004214,old_block_global_clear=0x78004219,vector_sentinel_store=0x78004220,mainargs_live_boundary=0x7800ba9e,mainargs_jump=0x7800ba9e,mainargs_outputs_entry=0x7800ba76,environ_read=0x7800ba8f,environ_output_store=0x7800ba95,mainargs_RET=0x7800ba98),
  required_runtime_contracts=['Carry current live heap/lazy lock/builder ownership; never resume cleaned final captures','Declare external environment helper CALL scheduling/frames separately; do not execute or claim preceding original attach','Native W/A blocks retain full pointer and matched API release lifetime; guest alias is not a truncated pointer','Actual complete double-NUL block and conversion outputs are measured, bounded and immutable historical API witnesses','Source helper owns malloc vector/strings, excludes leading equals entries, publishes global/sentinel, frees acquired malloc block','Frame/normal State/FX/CPU/source pages/FS effects derive from original BEFORE plus finite API witnesses and explicit seam inputs','Unrecovered fatal _amsg_exit and memcpy overlap path remain explicit refusals'],
  original_executed=False,native_component_executed=False,actual_API_executed=False,source_lifted=False,compiled_objects_created=False,full_CRT_complete=False,original_attach_proved=False,game_launch_proved=False,whole_M4_complete=False,files=files,initial_physical_closure=initial,physical_closure=verify_manifest(files),seconds=time.perf_counter()-started)
 p=jsonfile('report.json',report);jsonfile('pins.json',dict(schema='mw34-m4-environment-recovery-pins-v1',files=files))
 print(json.dumps(dict(passed=True,spans=len(spans),source_bytes=report['source_identity_bytes'],instructions=len(instructions),report_sha256=sha(p),pins_sha256=sha(out/'pins.json'))))

if __name__=='__main__':main(sys.argv[1])
