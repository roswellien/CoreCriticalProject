"""Fresh exact source recovery of witnessed version return/selector branches."""
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
BASE=ROOT/'reports/m4-crt-heap-version-recovery'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import normalized,unique_object,verify_manifest
from paths import publish_bytes,workspace_path
PROVIDER_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
TOOL_SHA='a3be577fb4ce2267477af45614d011c4b12a1e968aee4c8651ea22a3dc55091a'
ACCEPT_SHA='fccb8400f1c4a5b8ee3824684d763d1a6391d9322ad28c0a5b173ef8bf483154'
SOURCE_SHA='135ad3a9d2b24635d3f2547aa6904fef968daab02ae230302d1e3812914cd74c'
SPANS=(
 ('heap-fragment',0x7800183c,0x78001843),('heap-provider',0x780039bf,0x78003a0c),
 ('selector-prefix',0x78003a0c,0x78003a31),('stack-probe',0x780058b5,0x780058e6),
 ('selector-conditions',0x78003a31,0x78003a4b),
 ('selector-environment-frontier',0x78003a4b,0x78003a62),
 ('selector-mode1-cold',0x7800ccc5,0x7800cccd),('selector-epilogue',0x78003a7d,0x78003a80),
 ('heap-after-selector-static',0x780039e8,0x78003a0c),
 ('attach-after-heap-static',0x78001843,0x7800184c),
 ('selector-fallback-static',0x78003a62,0x78003aad),
 ('selector-cold-environment-static',0x7800cccd,0x7800cdc0))
CONDITIONS=(0x78003a31,0x78003a33,0x78003a35,0x78003a3c,0x78003a3e,0x78003a45)
MODE1=CONDITIONS+(0x7800ccc5,0x7800ccc7,0x7800ccc8,0x78003a7d,0x78003a7e,0x78003a7f)
ENV=(0x78003a4b,0x78003a51,0x78003a56,0x78003a57,0x78003a5c)


def need(value,why):
 if not value:raise ValueError(why)


def sha(path):
 with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def read(path):return json.loads(Path(path).read_bytes(),object_pairs_hook=unique_object)


def main(name):
 started=time.perf_counter_ns()
 need(re.fullmatch(r'recovery-r[1-9][0-9]*',name),'Fresh simple receipt name')
 out=workspace_path(BASE/name,reports=True)
 need(out.parent==BASE and not out.exists(),'Fresh immediate-child output')
 loader=ROOT/'tools/m4-crt/recover_provider.py'
 spec=importlib.util.spec_from_file_location('version_original_PE',loader)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';pe=module.PE(provider,PROVIDER_SHA)
 tool=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe'
 accepted=ROOT/'reports/m4-crt-heap-mode-root/root-acceptance-r1/report.json'
 previous=ROOT/'reports/m4-crt-heap-mode-recovery/recovery-r1/report.json'
 need(sha(tool)==TOOL_SHA,'Exact pinned disassembler')
 need(sha(accepted)==ACCEPT_SHA and read(accepted)['passed'],'Accepted real prior selector/probe query CALL')
 need(sha(previous)==SOURCE_SHA and read(previous)['passed'],'Exact prior static identity')
 prior=read(previous);files={}
 def add(path,digest=None):
  path=Path(path).absolute();key=normalized(str(path));value=sha(path) if digest is None else digest
  need(sha(path)==value and (key not in files or files[key]==value),'Exact unique physical pin')
  files[key]=value
 for path in (Path(__file__),Path(__file__).with_name('README.md'),Path(sys.executable),loader,provider,tool,
              accepted,previous,ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/paths.py'):add(path)
 initial=verify_manifest(files);out.mkdir(parents=True)
 spans,instructions,commands={},{},[]
 def section(address,count):
  matches=[s for s in pe.sections if s[0]<=address-pe.base and address-pe.base+count<=s[0]+s[2]]
  need(len(matches)==1,'Complete single file-backed section')
  rva,virtual,raw,offset,flags=matches[0]
  return dict(rva=rva,virtual_bytes=virtual,raw_bytes=raw,raw_offset=offset,permissions=flags&0xe0000000,
              readable=bool(flags&0x40000000),writable=bool(flags&0x80000000),executable=bool(flags&0x20000000))
 for label,start,end in SPANS:
  argv=[str(tool),'-d','--x86-asm-syntax=intel','--start-address='+hex(start),'--stop-address='+hex(end),str(provider)]
  decoded=subprocess.run(argv,capture_output=True,timeout=60);need(decoded.returncode==0,'Fresh exact source decode')
  rows=[]
  for line in decoded.stdout.decode('utf-8').splitlines():
   match=re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)',line)
   if not match:continue
   pc,raw=int(match[1],16),bytes.fromhex(match[2])
   need(start<=pc<end and pc+len(raw)<=end and pe.read(pc-pe.base,len(raw))==raw,'Exact bounded original instruction bytes')
   row=dict(pc=pc,bytes_hex=raw.hex(),width=len(raw),mnemonic=match[3],operands=match[4].split(' <')[0].replace('\t',' ').strip())
   need(pc not in instructions or instructions[pc]==row,'Consistent overlapping spans');instructions[pc]=row;rows.append(row)
  raw=pe.read(start-pe.base,end-start)
  need(b''.join(bytes.fromhex(r['bytes_hex']) for r in rows)==raw,'Complete contiguous source span')
  for suffix,value in (('.bin',raw),('-decode.stdout',decoded.stdout),('-decode.stderr',decoded.stderr)):
   path=out/(label+suffix);publish_bytes(path,value);add(path)
  spans[label]=dict(start=start,end_exclusive=end,bytes=end-start,sha256=sha(out/(label+'.bin')),section=section(start,end-start),instructions=rows)
  commands.append(dict(argv=argv,exit_code=0,original_body_executed=False))
 for label in ('heap-fragment','heap-provider','selector-prefix','stack-probe'):
  need(spans[label]['sha256']==prior['spans'][label]['sha256'],'All carried original source bodies remain byte-identical')
 new_labels=('selector-conditions','selector-environment-frontier','selector-mode1-cold','selector-epilogue')
 need(sum(spans[k]['bytes'] for k in new_labels)==60,'Four new disjoint guarded spans total60bytes')
 need(sum(instructions[pc]['width'] for pc in MODE1)==37,'Qualifying source path executes37newbytes')
 for pc,raw in ((0x78003a31,'85c0'),(0x78003a35,'83bd78ffffff02'),(0x78003a3e,'83bd6cffffff05'),
                (0x7800ccc5,'6a01'),(0x7800ccc7,'58'),(0x7800ccc8,'e9b06dffff'),
                (0x78003a7d,'5b'),(0x78003a7e,'c9'),(0x78003a7f,'c3'),(0x78003a5c,'ff159ce00278')):
  need(instructions[pc]['bytes_hex']==raw,'Exact source decision/return/import bytes')
 # Reconstruct import ownership from the original descriptors and INT entries.
 directory,size=struct.unpack_from('<2I',pe.bytes,pe.opt+104);descriptors=[]
 for i in range(size//20):
  raw=pe.read(directory+i*20,20);values=struct.unpack('<5I',raw)
  if not any(values):break
  original,timestamp,forwarder,name,iat=values
  descriptors.append(dict(address=pe.base+directory+i*20,raw_hex=raw.hex(),original_first_thunk_RVA=original,
      timestamp=timestamp,forwarder_chain=forwarder,library_name_RVA=name,library=pe.text(name),first_thunk_RVA=iat))
 owners=[]
 for slot in (0x7802e0a0,0x7802e09c,0x7802e098,0x7802e018,0x7802e0a8,0x7802e0a4):
  matches=[i for i in pe.imports() if i['iat']==slot];need(len(matches)==1,'Unique original import');item=matches[0];found=[]
  for desc in descriptors:
   delta=slot-pe.base-desc['first_thunk_RVA']
   if desc['library']!=item['library'] or delta<0 or delta%4:continue
   lookup=(desc['original_first_thunk_RVA'] or desc['first_thunk_RVA'])+delta
   try:
    name=struct.unpack('<I',pe.read(lookup,4))[0]
    if name&0x80000000 or pe.text(name+2)!=item.get('name'):continue
   except (ValueError,UnicodeError):continue
   found.append((desc,lookup,name))
  need(len(found)==1,'Unique descriptor/INT/hint-name provenance');desc,lookup,name=found[0]
  owners.append(dict(**item,raw_IAT=struct.unpack('<I',pe.read(slot-pe.base,4))[0],IAT_hex=pe.read(slot-pe.base,4).hex(),
      IAT_section=section(slot,4),descriptor=desc,lookup_address=pe.base+lookup,lookup_hex=pe.read(lookup,4).hex(),
      hint_name_address=pe.base+name,hint_name_hex=pe.read(name,2+len(item['name'])+1).hex(),
      hint=struct.unpack('<H',pe.read(name,2))[0],API_executed=False,runtime_import_resolution_observed=False))
 query=next(i for i in owners if i['iat']==0x7802e0a0);env=next(i for i in owners if i['iat']==0x7802e09c)
 need((query['name'],query['raw_IAT'],query['hint'])==('GetVersionExA',0x34600,373),'Exact query import identity')
 need((env['name'],env['raw_IAT'])==('GetEnvironmentVariableA',0x345e6),'Exact next unresolved alternate import')
 publish_bytes(out/'import-metadata.json',(json.dumps(owners,indent=2)+'\n').encode());add(out/'import-metadata.json')
 data={}
 for label,address,count in (('selector-cold-page',0x7800c000,4096),('environment-name',0x7802e3b8,len('__MSVCRT_HEAP_SELECT')+1)):
  raw=pe.read(address-pe.base,count);publish_bytes(out/(label+'.bin'),raw);add(out/(label+'.bin'))
  data[label]=dict(address=address,bytes=count,sha256=sha(out/(label+'.bin')),section=section(address,count))
 need(pe.read(0x2e3b8,len('__MSVCRT_HEAP_SELECT')+1)==b'__MSVCRT_HEAP_SELECT\0','Exact alternate environment source name')
 need(data['selector-cold-page']['section']['executable'] and not data['selector-cold-page']['section']['writable'],'New source page is RX')
 success_access=(
  (0x78003a35,0x200017c8,'P: actual measured platform DWORD, qualifying2',False),
  (0x78003a3e,0x200017bc,'V: actual measured unsigned major DWORD, qualifying>=5',False),
  (0x7800ccc5,0x2000061c,1,True),(0x7800ccc7,0x2000061c,1,False),
  (0x78003a7d,0x20000620,'EBX0: authentic selector-entry saved EBX',False),
  (0x78003a7e,0x20001850,'EBP0: authentic selector-entry saved EBP',False),
  (0x78003a7f,0x20001854,0x780039e8,False))
 ledger=[dict(ordinal=i+25,pc=pc,address=address,value=value,width=4,write=write) for i,(pc,address,value,write) in enumerate(success_access)]
 env_access=[dict(pc=pc,address=a,value=v,width=4,write=w) for pc,a,v,w in (
  (0x78003a51,0x2000061c,0x1090,True),(0x78003a56,0x20000618,0x20000624,True),
  (0x78003a57,0x20000614,0x7802e3b8,True),(0x78003a5c,0x7802e09c,0x345e6,False),
  (0x78003a5c,0x20000610,0x78003a62,True))]
 refs=[
  dict(title='Microsoft GetVersionExA',url='https://learn.microsoft.com/en-us/windows/win32/api/sysinfoapi/nf-sysinfoapi-getversionexa',
       verified_UTC_date='2026-10-09',facts=['One in/out OSVERSIONINFOA pointer; nonzero BOOL success, zero failure',
       'Caller sets size member; output is manifest and compatibility sensitive; GetLastError on failure']),
  dict(title='Microsoft OSVERSIONINFOA',url='https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-osversioninfoa',
       verified_UTC_date='2026-10-09',facts=['Five DWORDs and128CHAR give148bytes; platform2 is Win32NT']),
  dict(title='Microsoft x86 stdcall',url='https://learn.microsoft.com/en-us/cpp/cpp/stdcall?view=msvc-170',
       verified_UTC_date='2026-10-09',facts=['Callee cleans four-byte Win32 pointer argument; native x64 ABI separate'])]
 publish_bytes(out/'primary-API-contracts.json',(json.dumps(refs,indent=2)+'\n').encode());add(out/'primary-API-contracts.json')
 report=dict(schema='mw34-m4-heap-version-static-recovery-v1',passed=True,
  scope='Fresh original version-return, conditional selector RET and alternate unresolved environment-CALL contracts; static only',
  provider_sha256=PROVIDER_SHA,accepted_heap_mode_sha256=ACCEPT_SHA,prior_static_source_sha256=SOURCE_SHA,
  spans=spans,commands=commands,API_owners=owners,data=data,primary_API_references=refs,
  carried_source_PCs=prior['all_source_PCs'],carried_source_access_ledger=prior['all_source_access_ledger'],
  conditional_mode1_source_PCs=list(MODE1),conditional_mode1_all_source_PCs=prior['all_source_PCs']+list(MODE1),
  new_guarded_source_span_names=list(new_labels),new_guarded_source_instruction_rows=[row for label in new_labels for row in spans[label]['instructions']],
  conditional_mode1_added_source_access_ledger=ledger,
  counts=dict(prior_source_instructions=39,qualifying_added_instructions=12,qualifying_total_instructions=51,
      prior_source_accesses=24,qualifying_added_accesses=7,qualifying_total_source_accesses=31,
      qualifying_added_writes=1,qualifying_added_reads=6,qualifying_total_source_CALLs=5,
      qualifying_source_RETs=2,qualifying_added_executed_bytes=37,qualifying_total_executed_bytes=169,
      new_guarded_source_bytes=60,total_heap_guarded_source_bytes=230,total_source_identity_bytes=2086,
      distinct_API_return_reads=2,prior_mappings=20,total_mappings=21),
  query_entry_contract=dict(EIP=0x34600,ESP=0x20000618,EAX=0x200017b8,EBP=0x20001850,
      actual_source_query_CALL=0x78003a2b,source_IAT=0x7802e0a0,actual_return_word=0x78003a31,
      argument_address=0x2000061c,argument_pointer=0x200017b8,structure_bytes=148,size_DWORD=148,
      structure_end_exclusive=0x2000184c,only_size_DWORD_source_initialized=True),
  finite_query_API_contract=dict(named_API='KERNEL32.dll!GetVersionExA',input_bytes=148,output_bytes=148,
      scratch_before='Copy exact checked guest BEFORE148 bytes, not a synthetic zero structure',
      scratch_after='Complete measured real host output retained even when raw BOOL is0',
      raw_BOOL='Exact actual 32-bit BOOL bits; branch only tests zero/nonzero',
      measured_native_API_identity_required=True,manifest_context_identity_required=True,
      output_transport='Explicit checked guest148byte write from separately validated typed actual host output witness',
      no_host_source_store_shortcut=True,no_guest_output_from_After_State_seed=True,
      no_universal_original_version_or_API_internal_equivalence=True,
      checked_return_read=dict(context_pc=0x78003a2b,address=0x20000618,value=0x78003a31,width=4,write=False),
      separate_return_read_not_source_access=True,stdcall_return_plus_argument_bytes=8,
      ESP_after=0x20000620,EIP_after=0x78003a31,EAX_after='Raw actual BOOL bits',
      declared_State_effects=['EAX.low32','ESP.low32','EIP.low32'],FX_CPU_other_State_carried=True,
      API_admission_reads_and_output_transport_accesses_separately_labeled=True,API_executed_by_this_recovery=False),
  conditional_mode1_contract=dict(required_actual_outcome='BOOL!=0 and platform DWORD==2 and unsigned major DWORD>=5',
      selector_computed_return=1,selector_RET_pc=0x78003a7f,EIP=0x780039e8,ESP=0x20001858,EAX=1,
      EBP='Restored EBP0',EBX='Restored EBX0',ECX='Source-carried restored ECX0',
      source_cold_stack_PUSHandPOP_address=0x2000061c,source_saved_EBX_address=0x20000620,
      LEAVE_moves_ESP_to_EBP_before_checked_pop=True,LEAVE_saved_EBP_address=0x20001850,
      selector_RET_return_address=0x20001854,selector_RET_word=0x780039e8,
      cold_stack_write_source_only=True,heap_mode_global_publication=False,heap_mode_global_address=0x78035004,
      initializer_RET_executed=False,initializer_success_produced=False,original_attach_proved=False,
      stop_before_heap_CMP39E8_and_MOV39EB=True,no_full_initialized_allocator_claim=True),
  alternative_contracts=[dict(name=name,required_actual_outcome=condition,
      added_source_PCs=list(prefix+ENV),total_source_PCs=39+len(prefix)+5,
      total_source_accesses=24+reads+5,total_source_CALLs=6,source_RETs=1,
      new_executed_bytes=sum(instructions[pc]['width'] for pc in prefix+ENV),
      source_version_reads=[dict(pc=pc,address=a,width=4) for pc,a in ((0x78003a35,0x200017c8),(0x78003a3e,0x200017bc)) if pc in prefix],
      env_added_source_access_ledger=env_access,EIP=0x345e6,ESP=0x20000610,EAX=0x20000624,EBP=0x20001850,
      next_named_API='KERNEL32.dll!GetEnvironmentVariableA',source_CALL=0x78003a5c,source_IAT=0x7802e09c,
      source_return_word=0x78003a62,arguments=[0x7802e3b8,0x20000624,0x1090],
      argument_addresses=[0x20000614,0x20000618,0x2000061c],source_environment_name='__MSVCRT_HEAP_SELECT',
      API_executed=False,selector_RET_executed=False,heap_mode_published=False)
      for name,condition,prefix,reads in (
       ('actual_query_failure','BOOL==0; actual output still separately retained',CONDITIONS[:2],0),
       ('actual_non_NT_platform','BOOL!=0 and platform!=2',CONDITIONS[:4],1),
       ('actual_older_NT','BOOL!=0 and platform==2 and unsigned major<5',CONDITIONS,2))],
  flag_contract=dict(new_TEST_pc=0x78003a31,TEST=dict(CF=0,OF=0,SF='BOOL bit31',ZF='BOOL==0',
      PF='Even low-byte BOOL parity',AF='Undefined at exact source TEST3A31; declared representative only'),
      platform_CMP_pc=0x78003a35,platform_CMP_expression='Actual platformDWORD -2',
      major_CMP_pc=0x78003a3e,major_CMP_expression='Actual unsigned majorDWORD -5',
      CMP_defines_all_six_arithmetic_flags=True,qualifying_terminal_flags='Exact CMPmajor-5; no fixed major assumed',
      actual_query_failure_terminal_flags='TESTactualBOOL0: CF0 PF1 ZF1 SF0 OF0; qualified undefinedAF',
      non_NT_terminal_flags='Exact CMPplatform-2',older_NT_terminal_flags='Exact CMPmajor-5',
      PUSH_POP_JMP_LEAVE_RET_preserve_final_CMP_flags=True,other_carried_flags_preserved=True,
      universal_undefined_AF_or_original_API_volatile_equivalence=False),
  mapping_contract=dict(prior_mappings=20,new_raw_RX_page=0x7800c000,total_mappings=21,
      new_page_sha256=data['selector-cold-page']['sha256'],all_prior_pages_TIB_and_Policy_preserved=True,
      old_owned_lower_stack_is_declared_input_not_original_capture=True,original_guard_stack_growth_proved=False,
      generic_Runtime_CPU_and_call_records_preserved=True,host_scheduler_guest_source_stores=0,
      query_output_write_is_declared_API_effect_not_original_source_store=True),
  anticipated_checkpoint_contract=dict(new_API_phases=['version-api-before','version-api-output','version-api-returned'],
      source_progress_phases=['selector-conditions','selector-mode1-before','selector-epilogue-before','selector-returned'],
      alternate_terminal='environment-query-before',final_schema_requires_author_root_agreement=True),
  failures_and_future_dependencies=[
      'Validate named query authority, actual source CALL frame, pointer/size and whole148byte read/write permissions before host API effects',
      'Host scratch starts from exact guest bytes; capture rawBOOL/errors/fulloutput even on0; no fabricated success or API failure',
      'Explicit APIoutput transport and checked return read order/partial faults must be captured and separately modeled',
      'Source query TEST/CMP flags depend measured actualBOOL/platform/major; directed synthetic branches must be labeled fixture controls',
      'Denied platform/major reads or cold/epilogue stack accesses preserve exact source partial effects and prohibit synthesizedRET',
      'LEAVE genuinely movesESP toEBP before popping savedEBP; selectorRET genuinely reads1854 and returns39E8',
      'Source heap mode MOV39EB and initializerRET3A0B remain unexecuted at recommended success cut',
      'Alternate environmentCALL is unresolved; its output, parserhelpers and modulefallback are later gates',
      'Original attach fragment after1843 requires earlier GetVersion-derivedESI/EBX state and is not admitted by selectorRET',
      'Real heap handle ownership remains private; cleanup must use fullhandle with actual successful witness on ordinary and fault paths'],
  limitations=['This static receipt executes no native/API body and witnesses no actual version outcome',
      'Current host query outputs are manifest-sensitive evidence, not original Win32 API internals or original-game observation',
      'Conditional selector return1 is source computation; heap mode global and heap initializer completion remain unproduced',
      'No original lower stack capture, guard growth, original attach, full causal replay or wholeM4 completion'],
  native_executed=False,original_executed=False,game_executed=False,API_executed=False,
  selector_RET_executed=False,initializer_RET_executed=False,heap_mode_global_published=False,
  heap_initialized=False,original_attach_proved=False,full_causal_model_claim=False,whole_M4_complete=False,
  historical_receipts_recursively_expanded=False,initial_dependency_check=initial,
  final_dependency_check=verify_manifest(files),elapsed_seconds=(time.perf_counter_ns()-started)/1e9,files=dict(sorted(files.items())))
 path=out/'report.json';publish_bytes(path,(json.dumps(report,indent=2)+'\n').encode());add(path)
 publish_bytes(out/'pins.json',(json.dumps(dict(files=dict(sorted(files.items()))),indent=2)+'\n').encode())
 print(json.dumps(dict(passed=True,schema=report['schema'],report_sha256=sha(path),pins_sha256=sha(out/'pins.json'),
     source_PCs=51,source_accesses=31,new_guarded_bytes=60,mappings=21,selector_stop_EIP=hex(0x780039e8),API_executed=False)))


if __name__=='__main__':main(sys.argv[1])
