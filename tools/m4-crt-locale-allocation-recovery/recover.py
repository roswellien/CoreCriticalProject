"""Bounded original malloc/SEH/heap prerequisite recovery; static source only."""
import hashlib,importlib.util,json,re,struct,subprocess,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).absolute().parents[2];BASE=ROOT/'reports/m4-crt-locale-allocation-recovery'
sys.path.insert(0,str(ROOT/'tools/m4-pipeline'))
from manifests import normalized,unique_object,verify_manifest
from paths import workspace_path,publish_bytes
PROVIDER_SHA='2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7'
SOURCE_SHA='500e515b769e674d63503bf8572212221c7af8ae9519b712d4ee712c512c37c3'
SPANS=(('malloc-wrapper',0x780012b3,0x780012c5),('size-wrapper',0x780012c5,0x780012e3),('heap-worker-hot',0x780012e3,0x78001390),('malloc-cold',0x7800cc3f,0x7800ccbd),('heap-initializer',0x780039bf,0x78003a0c),('attach-heap-scheduling',0x78001823,0x7800184c),('handler-entry',0x7800ef03,0x7800ef33))
PREFIX=[0x780012b3,0x780012b9,0x780012bd,0x780012c5,0x780012ca,0x780012d0,0x780012d4,0x780012e3,0x780012e4,0x780012e6,0x780012e8,0x780012ed,0x780012f2]
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 started=time.perf_counter_ns();out=workspace_path(BASE/name,reports=True);need(re.fullmatch('recovery-r[1-9][0-9]*',name)and out.parent==BASE and not out.exists(),'Fresh immediate recovery directory')
 source=ROOT/'tools/m4-crt/recover_provider.py';spec=importlib.util.spec_from_file_location('allocation_pe',source);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 provider=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';pe=mod.PE(provider,PROVIDER_SHA);need(pe.exports()['malloc']['address']==0x780012b3,'Exact named malloc export');tool=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin/llvm-objdump.exe';prior=ROOT/'reports/m4-crt-locale-default-recovery/recovery-r2/report.json';need(sha(prior)==SOURCE_SHA,'Frozen genuine locale source recovery')
 files={}
 def add(p):
  p=Path(p).absolute();k=normalized(str(p));h=sha(p);need(k not in files or files[k]==h,'Current unique binding');files[k]=h;return p
 for p in (Path(__file__),Path(__file__).with_name('README.md'),source,provider,tool,prior,Path(sys.executable),ROOT/'tools/m4-pipeline/manifests.py',ROOT/'tools/m4-pipeline/paths.py'):add(p)
 initial=verify_manifest(files);out.mkdir(parents=True);spans={};instructions={};commands=[]
 def section(a,n):
  s=[v for v in pe.sections if v[0]<=a-pe.base and a-pe.base+n<=v[0]+v[2]];need(len(s)==1,'One complete file-backed section');rva,vs,rs,rp,flags=s[0];return dict(rva=rva,virtual_bytes=vs,raw_bytes=rs,raw_offset=rp,permissions=flags&0xe0000000)
 for label,start,end in SPANS:
  argv=[str(tool),'-d','--x86-asm-syntax=intel','--start-address='+hex(start),'--stop-address='+hex(end),str(provider)];cp=subprocess.run(argv,capture_output=True,timeout=60);need(cp.returncode==0,'Fresh source disassembly');rows=[]
  for line in cp.stdout.decode().splitlines():
   m=re.match(r'\s*([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)',line)
   if m:
    pc=int(m[1],16);code=bytes.fromhex(m[2]);need(start<=pc<end and pc+len(code)<=end and pe.read(pc-pe.base,len(code))==code,'Every bounded decoded byte is exact original');row=dict(pc=pc,bytes_hex=code.hex(),mnemonic=m[3],operands=m[4].split(' <')[0].replace('\t',' ').strip());rows.append(row);need(pc not in instructions or instructions[pc]==row,'No conflicting decode');instructions[pc]=row
  raw=pe.read(start-pe.base,end-start);need(b''.join(bytes.fromhex(r['bytes_hex'])for r in rows)==raw,'Complete contiguous original span '+label)
  for suffix,data in (('.bin',raw),('-decode.stdout',cp.stdout),('-decode.stderr',cp.stderr)):p=out/(label+suffix);publish_bytes(p,data);add(p)
  spans[label]=dict(start=start,end_exclusive=end,bytes=end-start,sha256=sha(out/(label+'.bin')),section=section(start,end-start),instructions=rows);commands.append(dict(argv=argv,exit_code=0,provider_executed=False))
 data={}
 for label,a,n in (('heap-state-file-identity',0x78035000,8),('newmode-file-identity',0x78037150,4),('smallblock-threshold-file-identity',0x78037148,4),('lock9-file-identity',0x7803704c,4),('scope-table-file-identity',0x7802e248,24)):
  b=pe.read(a-pe.base,n);p=out/(label+'.bin');publish_bytes(p,b);add(p);data[label]=dict(address=a,bytes=n,sha256=sha(p),section=section(a,n),DWORDs=list(struct.unpack('<'+'I'*(n//4),b)),initialized=False)
 need(data['heap-state-file-identity']['DWORDs']==[0,0]and data['newmode-file-identity']['DWORDs']==[0],'Zero raw heap/newmode identity only')
 owners=[]
 for slot in (0x7802e094,0x7802e0a8,0x7802e038):
  row=[v for v in pe.imports()if v['iat']==slot];need(len(row)==1,'Unique actual provider API import');owners.append(dict(**row[0],raw_IAT=struct.unpack('<I',pe.read(slot-pe.base,4))[0],section=section(slot,4)))
 accesses=[(0x780012b3,'78037150',False,'0'),(0x780012b3,'M-4',True,'0'),(0x780012b9,'M+4',False,'24'),(0x780012b9,'M-8',True,'24'),(0x780012bd,'M-12',True,'780012C2'),(0x780012c5,'M-8',False,'24'),(0x780012d0,'M-8',False,'24'),(0x780012d0,'M-16',True,'24'),(0x780012d4,'M-20',True,'780012D9'),(0x780012e3,'M-24',True,'entry.EBP'),(0x780012e6,'M-28',True,'FFFFFFFF'),(0x780012e8,'M-32',True,'7802E248'),(0x780012ed,'M-36',True,'7800EF03')]
 ledger=[dict(ordinal=i+1,pc=pc,address_expression=a,write=w,value_expression=v,bytes=4)for i,(pc,a,w,v)in enumerate(accesses)]
 # Direct file-operand references identify initialization writers without
 # claiming exhaustive alias recovery or execution of any startup branch.
 inspect=ROOT/'reports/m4-crt-locale-allocation-recovery/inspect-r1/provider-decode.stdout';need(inspect.exists(),'Fresh static inspection output');add(inspect);xrefs=[]
 for line in inspect.read_text().splitlines():
  m=re.match(r'([0-9a-f]+):\s*((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*)',line)
  if m and re.search(r'\[0x7803500[04]\]',m[4]):
   pc=int(m[1],16);code=bytes.fromhex(m[2]);need(pe.read(pc-pe.base,len(code))==code,'Exact direct heap global xref');xrefs.append(dict(pc=pc,bytes_hex=code.hex(),mnemonic=m[3],operands=m[4].split(' <')[0].strip()))
 report=dict(passed=True,scope='Static exact malloc24 continuation to first required provider SEH operation and heap initialization prerequisites; no execution',provider_sha256=PROVIDER_SHA,previous_source_sha256=SOURCE_SHA,spans=spans,data=data,API_owners=owners,commands=commands,
  next_gate=dict(entry=0x780012b3,actual_CALL_site=0x7800107b,actual_return=0x78001080,entry_ESP='M=20001810',argument='[M+4]=24',newmode_domain='Current carried original-file value0; read by actual source, no new-mode initializer claim',visited_source_PCs=PREFIX,completed_source_instructions=12,source_PC_count_including_stop=13,completed_accesses=13,accesses=ledger,first_refused_pc=0x780012f2,first_refused_operation='MOV EAX,FS:[0]; before source read, stack publication or SEH installation',refused_access_ordinal=14,FS_address_expression='carried owned State.fs_base+0',target_body_entered='Source heap worker12E3 prologue only',stop_State=dict(ESP='M-36=200017EC',EBP='M-24=200017F8',EAX='entry.EAX=25',ESI='entry.ESI=7803708C',EBX='entry.EBX',EDI='entry.EDI',ECX='entry.ECX',EDX='entry.EDX',flags=dict(CF=1,PF=0,AF=0,ZF=0,SF=0,OF=0,defining_PC=0x780012c5,other_flags='incoming flags retained'))),
  CALL_frames=[dict(site=0x780012bd,target=0x780012c5,return_word=0x780012c2,ESP='M-12',arguments=['24','newmode0']),dict(site=0x780012d4,target=0x780012e3,return_word=0x780012d9,ESP='M-20',arguments=['24'])],
  subsequent_SEH=dict(read_PC=0x780012f2,push_previous_PC=0x780012f8,publish_PC=0x780012f9,scope_table=0x7802e248,handler=0x7800ef03,source_registration_frame='M-40',source_scope_word='M-32',try_level_word='M-28',source_handler_word='M-36',previous_chain='M-40',existing_game_exception_frame='Borrowed existing source-written CRT entry chain; not reset',SEH_dispatch_proved=False,registration_executed=False),
  heap_paths=dict(selector_global=0x78035004,selector_file_value=0,selector_initialized=False,first_selector_read_PC=0x78001306,mode3=dict(branch_PC=0x7800130e,target=0x7800cc62,threshold=0x7803b764,lock_id=9,allocator=0x7800d361),mode2=dict(branch_PC=0x78001317,fallthrough=0x7800131d,threshold=0x78037148,threshold_file_value=480,lock_id=9,lock_CALL=0x7800133b,allocator=0x780010b0),other_modes=dict(branch_PC=0x78001317,target=0x7800cc97,nonzero24_rounding=32,HeapAlloc_CALL=0x7800137f,HeapAlloc_IAT=0x7802e094,heap_handle_global=0x78035000,heap_handle_file_value=0,allocation_flags=0),raw_zero_selector_grants_initialized_allocator=False),
  authentic_heap_initializer=dict(entry=0x780039bf,original_attach_CALL=0x7800183e,original_attach_argument=1,first_actual_API_CALL=0x780039d0,API_IAT=0x7802e0a8,API_name='HeapCreate',flags='SETE of incoming initializer argument==0; originalattacharg1→flags0',initial_bytes=4096,maximum_bytes=0,handle_store_PC=0x780039d8,handle_global=0x78035000,selector_helper_CALL=0x780039e3,selector_helper_target=0x78003a0c,selector_store_PC=0x780039eb,selector_global=0x78035004,source_success_return=1,original_attach_executed=False,API_outcome_or_guest_handle_proved=False),
  allocation_RETURN=dict(source_HeapAlloc_result='EAX after actual API outcome only',normal_restore_chain_PC=0x7800136a,restore_previous_from='[EBP-10h]',provider_RET=0x78001375,size_wrapper_RET=0x780012e2,malloc_wrapper_cleanup=[0x780012c2,0x780012c3],malloc_RET=0x780012c4,lock_resume=0x78001080,lock_result_to_EDI=0x78001080,zero_alloc_branch=0x78001085,zero_target=0x7800bba4,successful_alloc_result_admitted=False),
  future_mapping_requirements=dict(heap_global_page=0x78035000,heap_global_source_permissions='RW',current17page_set_does_not_include_heap_global_page=True,file_page_copy_is_not_heap_initialization=True),initialization_xrefs=xrefs,alias_inventory_exhaustive=False,initial_check=initial,original_executed=False,native_executed=False,provider_loaded=False,fake_allocation=False,locale_initialized=False,whole_M4_complete=False)
 report['final_dependency_check']=verify_manifest(files);report['elapsed_seconds']=(time.perf_counter_ns()-started)/1e9;report['files']=files;p=out/'report.json';publish_bytes(p,(json.dumps(report,indent=2)+'\n').encode());add(p);publish_bytes(out/'pins.json',(json.dumps(dict(files=files),indent=2)+'\n').encode());print(json.dumps(dict(passed=True,report_sha256=sha(p),pins_sha256=sha(out/'pins.json'),source_spans=len(spans),next_required_PC=hex(0x780012f2))))
if __name__=='__main__':main(sys.argv[1])
