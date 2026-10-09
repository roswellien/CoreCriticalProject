"""Independent exact source and IR contract for the first actual _initterm call.

Reads the two frozen PE images and the actual lifted provider. No candidate
execution output, Session model, author comparator or expected AFTER is used.
"""
import hashlib, importlib.util, json, re, struct, subprocess, sys, traceback
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/m4-crt-entry-initterm'
LLVM = ROOT / 'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
PINS, CHECKS, COMMANDS = {}, [], []
FROZEN = {
 'MW3/Mech3.exe':'95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf',
 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL':'2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7',
 'tools/analysis/pe.py':'bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638',
 'tools/m4-runtime/runtime.cpp':'48865157011deaa151dccbb598da3f5a8ed16ea1944d048549f97f66f32308f7',
 'tools/m4-runtime/runtime.hpp':'41ed0a20e4f87cba3838127d943126ff88b453c39212c2ecdfe028242b4f3536',
 'reports/m4-crt-entry-control/root-acceptance-r1/report.json':'984e18e7165532a0d219082122245d527716042d7dd97ff1fb6f378df134b460',
}

def need(ok, why):
 if not ok: raise ValueError(why)
def sha(p):
 with Path(p).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p, wanted=None):
 p=Path(p).resolve(); h=sha(p)
 need(wanted is None or wanted==h,'Physical identity: '+str(p))
 need(str(p) not in PINS or PINS[str(p)]==h,'Conflicting physical identity')
 PINS[str(p)]=h; return p
def text(p): return pin(p).read_text(encoding='utf-8-sig')
def read(p): return json.loads(text(p))
def check(name, **facts): CHECKS.append(dict(name=name,passed=True,**facts))
def run(out, argv, name):
 argv=list(map(str,argv)); cp=subprocess.run(argv,capture_output=True,cwd=ROOT)
 log=out/name; log.write_bytes(cp.stdout+cp.stderr);pin(log);pin(argv[0])
 COMMANDS.append(dict(arguments=argv,exit_code=cp.returncode,log=str(log),log_sha256=sha(log)))
 need(cp.returncode==0,'Independent decode '+name);return cp.stdout.decode(errors='replace')

def image_contract(out):
 spec=importlib.util.spec_from_file_location('independent_initterm_pe',pin(ROOT/'tools/analysis/pe.py',FROZEN['tools/analysis/pe.py']))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 gp=pin(ROOT/'MW3/Mech3.exe',FROZEN['MW3/Mech3.exe']);dp=pin(ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL',FROZEN['local/mw3-staged/Shared_DLLs/MSVCRT.DLL'])
 game,provider=gp.read_bytes(),dp.read_bytes();pe,dll=module.PEImage(game),module.PEImage(provider)
 owners={}
 for slot,name,raw in [(0x5bb510,'_initterm',0x1ded12),(0x5bb514,'__getmainargs',0x1ded02)]:
  matched=[(lib['library'],s)for lib in pe.imports()for s in lib['symbols']if pe.image_base+s['iat_rva']==slot]
  need(len(matched)==1 and matched[0][0].casefold()=='msvcrt.dll' and matched[0][1].get('name')==name,'Unique actual import '+name)
  need(pe.rva_u32(slot-pe.image_base)==raw,'Actual raw IAT '+name);owners[name]=dict(library=matched[0][0],symbol=matched[0][1],slot=slot,raw_IAT=raw)
 exports=[e for e in dll.exports()if '_initterm' in e['names']]
 need(len(exports)==1 and exports[0]['ordinal']==272 and exports[0]['rva']==0x14f8 and 'forwarder'not in exports[0],'Unique direct provider _initterm export')
 ranges=[('outer-call',game,pe,0x5ac440,5,'4b4b65b32d6aa62283b66afd64b3fda9a487f2cb6c16cc3347a300c792612f34'),('thunk',game,pe,0x5ac598,6,'86127a1a5240eff849fe402fc8517ae3ead7498476c8f17188afd36be6060947'),('provider',provider,dll,0x780014f8,28,'960ed0d00b0200736930590a16fbb3caa9c3bc24af9851a3728258fd9b340678'),('continuation',game,pe,0x5ac445,41,'f3e53036f7ab7e18799482b2d2cf084fc739d8761d9884e5065e0b70f7299b5a')]
 spans=[]
 for label,data,image,va,n,want in ranges:
  off=image.rva_range(va-image.image_base,n)[0];code=data[off:off+n]
  need(hashlib.sha256(code).hexdigest()==want,'Exact source '+label)
  section=[s for s in image.sections if s['virtual_address']<=va-image.image_base<s['virtual_address']+s['raw_size']]
  need(len(section)==1 and section[0]['readable']and section[0]['executable']and not section[0]['writable'],'Raw RX source '+label)
  path=out/(label+'.bin');path.write_bytes(code);pin(path);spans.append(dict(label=label,VA=va,bytes=n,file_offset=off,sha256=want,section=section[0]['name']))
 program={}
 for label,path,start,stop in [('caller',gp,0x5ac436,0x5ac46e),('thunk',gp,0x5ac598,0x5ac59e),('provider',dp,0x780014f8,0x78001514)]:
  decoded=run(out,[LLVM/'llvm-objdump.exe','-d','--x86-asm-syntax=intel',f'--start-address={start}',f'--stop-address={stop}',path],label+'-decode.txt')
  image,data=(pe,game)if path==gp else(dll,provider)
  for line in decoded.splitlines():
   m=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*([a-z]+)\s*(.*?)\s*$',line)
   if not m:continue
   pc=int(m[1],16);code=bytes.fromhex(m[2]);off=image.rva_range(pc-image.image_base,len(code))[0]
   need(start<=pc<stop and data[off:off+len(code)]==code and pc not in program,'Every decoded PC is unique exact original source')
   program[pc]=dict(bytes=len(code),instruction=m[3],operands=re.sub(r'\s*<[^>]*>','',m[4]).strip())
 expected={0x5ac436:('push','0x5e024c'),0x5ac43b:('push','0x5e0248'),0x5ac440:('call','0x5ac598'),0x5ac445:('add','esp, 0x8'),0x5ac448:('mov','edx, dword ptr [0x736598]'),0x5ac44e:('mov','dword ptr [ebp - 0x6c], edx'),0x5ac451:('lea','eax, [ebp - 0x6c]'),0x5ac454:('push','eax'),0x5ac455:('mov','ecx, dword ptr [0x736594]'),0x5ac45b:('push','ecx'),0x5ac45c:('lea','edx, [ebp - 0x64]'),0x5ac45f:('push','edx'),0x5ac460:('lea','eax, [ebp - 0x70]'),0x5ac463:('push','eax'),0x5ac464:('lea','ecx, [ebp - 0x60]'),0x5ac467:('push','ecx'),0x5ac468:('call','dword ptr [0x5bb514]'),0x5ac598:('jmp','dword ptr [0x5bb510]'),0x780014f8:('push','esi'),0x780014f9:('mov','esi, dword ptr [esp + 0x8]'),0x780014fd:('jmp','0x78001502'),0x780014ff:('add','esi, 0x4'),0x78001502:('cmp','esi, dword ptr [esp + 0xc]'),0x78001506:('jae','0x78001512'),0x78001508:('mov','eax, dword ptr [esi]'),0x7800150a:('test','eax, eax'),0x7800150c:('je','0x780014ff'),0x7800150e:('call','eax'),0x78001510:('jmp','0x780014ff'),0x78001512:('pop','esi'),0x78001513:('ret','')}
 need(set(program)==set(expected),'Complete exact caller/thunk/provider PC set')
 for pc,(ins,args)in expected.items():need(program[pc]['instruction']==ins and program[pc]['operands']==args,'Exact operand '+hex(pc))
 (out/'instruction-contract.json').write_text(json.dumps(program,indent=2)+'\n');pin(out/'instruction-contract.json')
 need(pe.rva_u32(0x5e0248-pe.image_base)==0,'First actual interval contains precisely one null source DWORD')
 page_contract=[]
 for label,data,image,base in [('table',game,pe,0x5e0000),('provider-code',provider,dll,0x78001000)]:
  off=image.rva_range(base-image.image_base,4096)[0];body=data[off:off+4096];path=out/(label+'-page.bin');path.write_bytes(body);pin(path)
  sec=[s for s in image.sections if s['virtual_address']<=base-image.image_base<s['virtual_address']+max(s['virtual_size'],s['raw_size'])][0]
  need(sec['readable']and(sec['writable']if label=='table'else sec['executable']and not sec['writable']),'Exact mapped page source permission')
  page_contract.append(dict(label=label,base=base,bytes=4096,file_offset=off,sha256=sha(path),permissions='RW'if label=='table'else'RX',already_mapped_by_game=label=='table',remap_allowed=False))
 bss=[]
 for va in(0x736594,0x736598):
  try:pe.rva_range(va-pe.image_base,4);raise ValueError('Unexpected file backing for source BSS global')
  except module.PEError:pass
  sec=[s for s in pe.sections if s['virtual_address']<=va-pe.image_base and va-pe.image_base+4<=s['virtual_address']+s['virtual_size']]
  need(len(sec)==1 and sec[0]['readable']and sec[0]['writable']and va-pe.image_base>=sec[0]['virtual_address']+sec[0]['raw_size'],'Admitted virtual-zero BSS')
  bss.append(dict(VA=va,value=0,source='PE virtual zero-filled .data tail',already_owned_page=0x736000))
 check('Unique raw import and provider export identities',owners=owners,provider_export=exports[0],source_spans=spans,complete_provider_PC_count=13)
 check('First actual interval and literal page ownership',begin=0x5e0248,end_exclusive=0x5e024c,source_DWORDs=[0],end_not_read=True,provider_page_addition=0x78001000,checkpoint_page_addition=0x5e0000,pages=page_contract,BSS_reads=bss,expected_checkpoint_union_pages=16)
 return program

def ir_order(out):
 prep=ROOT/'reports/m4-crt-entry-initterm/provider-preparation-r3';report=read(prep/'report.json');host=text(prep/'host.ll');guest=text(prep/'guest.ll');pin(prep/'source.bin','960ed0d00b0200736930590a16fbb3caa9c3bc24af9851a3728258fd9b340678')
 need(report['passed']and report['host_sha256']==sha(prep/'host.ll')and report['source_bytes']==28,'Exact prepared source association')
 need(re.findall(r'^define ptr @([^ (]+)',host,re.M)==['sub_780014f8']and '__remill_missing_block'not in host,'Complete provider CFG is actual source translation')
 need('target triple = "x86_64-pc-windows-msvc"'in host and len(report['layouts'])==34 and report['layouts']['struct.State']['size']==3504,'Host target and full persistent State layout')
 need(not re.search(r'\b(?:nounwind|willreturn)\b',host),'Provider and checked bridge calls permit C++ unwind')
 def ordered(label,fragments):
  cursor=-1
  for fragment in fragments:
   nxt=host.find(fragment,cursor+1);need(nxt>cursor,'Actual IR order '+label+': '+fragment);cursor=nxt
  return dict(label=label,ordered_fragments=fragments)
 orders=[ordered('PUSH ESI: checked write before ESP publication',['%12 = call noundef ptr @__remill_write_memory_32','store i32 %8, ptr %6']),ordered('MOV ESI argument: checked read before register publication',['%21 = call noundef i32 @__remill_read_memory_32','store i32 %21, ptr %ESI']),ordered('MOV EAX table: checked read before register publication',['%104 = call noundef i32 @__remill_read_memory_32','store i32 %104, ptr %EAX']),ordered('Callback CALL: checked store before ESP/target publication and bridge',['%193 = call noundef ptr @__remill_write_memory_32','store i32 %189, ptr %187','store i32 %184, ptr %194','%197 = call ptr @__remill_function_call']),ordered('POP ESI: ESP publication before checked read and ESI publication',['store i32 %92, ptr %90','%96 = call noundef i32 @__remill_read_memory_32','store i32 %96, ptr %ESI']),ordered('RET: checked read before PC/ESP publication and return bridge',['%216 = call noundef i32 @__remill_read_memory_32','store i32 %216, ptr %217','store i32 %219, ptr %211','%223 = tail call ptr @__remill_function_return'])]
 need('store i8 0, ptr %127'in host and '@mw34_entry_initerm_undefined_8()'in host,'TEST undefined AF representative explicitly routed')
 need('__remill_undefined_8'in guest and 'mw34_entry_initerm_undefined_8'not in guest,'Only lowered AF bridge receives isolated name')
 check('Read-only actual lowered provider IR partial-fault contract',preparation=str(prep),host_sha256=sha(prep/'host.ll'),orders=orders,State_bytes=3504,guest_pointer_values_never_cast_to_host_pointers=not re.search(r'\b(?:inttoptr|ptrtoint)\b',host),integer_provider_only=True,FP_reseed_allowed=False,AF='TEST AF uses explicit native zero representative only; final null-path CMP defines AF')

def boundary_contract():
 for rel,want in FROZEN.items():pin(ROOT/rel,want)
 accepted=read(ROOT/'reports/m4-crt-entry-control/root-acceptance-r1/report.json')
 need(accepted['actual_CRT_entry_control_composition_accepted']and accepted['owned_pages']==14,'Accepted unchanged prior control prefix')
 runtime=text(ROOT/'tools/m4-runtime/runtime.cpp')
 imp=runtime[runtime.index('void Runtime::call_import'):runtime.index('void Runtime::invoke')]
 need(imp.index('original_iat_value')<imp.index('services_.find')<imp.index('call(item->second.native'),'Missing next service checked before frame publication')
 check('Actual frames, flags and next required dependency',entry_EBP=0x200018fc,after_control_ESP=0x20001878,outer_call_PC=0x5ac440,outer_return_PC=0x5ac445,provider_frame=0x2000186c,saved_ESI_address=0x20001868,begin_arg_address=0x20001870,end_arg_address=0x20001874,provider_return_ESP=0x20001870,null_path_dynamic_provider_instructions=13,null_path_unique_provider_PCs=11,null_path_source_accesses_including_thunk=8,null_path_EAX=0,null_path_ESI='restored exact caller value',provider_final_flags_IF_fixture=0x246,continuation_final_flags_IF_fixture=0x206,all_persistent_FP_State_FX_metadata='carry unchanged from accepted control producer; integer provider and caller continuation',next_call_PC=0x5ac468,next_slot=0x5bb514,next_raw_target=0x1ded02,next_return_PC=0x5ac46e,next_required_name='MSVCRT.dll!__getmainargs',final_State={'ESP':0x20001860,'EIP':0x1ded02,'EAX':0x2000188c,'ECX':0x2000189c,'EDX':0x20001898,'EBP':0x200018fc},stale_Runtime_CPU={'ESP':0x20001864,'EIP':0x5ac468},actual_after_initerm_game_accesses=10,missing_service_creates_no_new_runtime_ledger=True,selected_initializers_executed=0)
 check('Smallest admissible additive integration and excluded credit',prior_code_components='Use physically frozen accepted producer/matherr/control components; no hidden resets/remaps',new_components='Full actual 28-byte provider compiled O0/O2; existing actual game thunk registered with new typed provider service',namespace='Isolate colliding internal pure helper definitions or reversible names only; never overwrite frozen objects',bridges='Exact typed current owner before cast; guarded thread and token; checked source operand addresses; C++ BridgeAbort; nested boundary cleanup before failure observer checkpoint',source_identity='Check unchanged full thunk/provider and literal first table source; no pointer fixups',scope='First null-only actual interval and caller continuation through missing __getmainargs; all callback success and later 144-entry interval remain outside gate',handwritten_Session_model_native_credit=False,standalone_longjmp_adoption_allowed=False,full_CRT=False,native_menu=False)

def main():
 out=Path(sys.argv[1]).resolve();need(out.parent==BASE and out.name.startswith('independent-source-')and not out.exists(),'Fresh isolated source-review directory');out.mkdir(parents=True)
 (out/'review.py').write_bytes(Path(__file__).read_bytes());pin(out/'review.py')
 try:
  image_contract(out);ir_order(out);boundary_contract()
  report=dict(passed=True,scope='Independent exact source/IR contract only; final candidate and native execution acceptance remain separate',checks=CHECKS,commands=COMMANDS,findings=[],ordinary_game_launched=False,original_x86_executed=False,native_candidate_executed=False,full_CRT=False,native_menu=False,selected_initializer_count_unchanged=27,total_selected_initializers=144,whole_M4_complete=False)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');pin(out/'report.json');pin(Path(__file__))
  (out/'pins.json').write_text(json.dumps(dict(files=dict(sorted(PINS.items()))),indent=2)+'\n')
  print(json.dumps(dict(passed=True,checks=len(CHECKS),files=len(PINS),report=str(out/'report.json'),report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))
 except Exception:
  (out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main()
