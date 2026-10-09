"""Independent original-source contract for the bounded mainargs prefix.

Only PE bytes/metadata and already frozen source IR are consulted. No candidate,
execution AFTER, model or author validator supplies the original contract.
"""
import hashlib, importlib.util, json, re, struct, subprocess, sys, traceback
from pathlib import Path
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'reports/m4-crt-mainargs'
LLVM=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
PINS,COMMANDS={},[]
FROZEN={
 'MW3/Mech3.exe':'95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf',
 'local/mw3-staged/Shared_DLLs/MSVCRT.DLL':'2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7',
 'tools/analysis/pe.py':'bdad31b70e97fe6df3817dd42b9e7654561760ce3ef5203dadbfd9c3dd2b2638',
 'tools/m4-runtime/runtime.cpp':'48865157011deaa151dccbb598da3f5a8ed16ea1944d048549f97f66f32308f7',
 'tools/m4-runtime/runtime.hpp':'41ed0a20e4f87cba3838127d943126ff88b453c39212c2ecdfe028242b4f3536',
 'reports/m4-crt-entry-initterm/root-acceptance-r2/report.json':'0685db17817db850ae18d146de4c70844c4d94a0a5d41703bff57702b46c46fc',
}
def need(ok,why):
 if not ok:raise ValueError(why)
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p,want=None):
 p=Path(p).resolve();h=sha(p);need(want is None or h==want,'Physical source identity '+str(p));need(str(p)not in PINS or PINS[str(p)]==h,'Conflicting identity');PINS[str(p)]=h;return p
def run(out,argv,label):
 argv=list(map(str,argv));r=subprocess.run(argv,capture_output=True,cwd=ROOT);p=out/(label+'.txt');p.write_bytes(r.stdout+r.stderr);pin(p);pin(argv[0]);COMMANDS.append(dict(arguments=argv,exit_code=r.returncode,log=str(p),sha256=sha(p)));need(r.returncode==0,'Independent source decode '+label);return r.stdout.decode(errors='replace')
def target(pc,raw):
 if raw[0]in(0xe8,0xe9):return pc+len(raw)+struct.unpack_from('<i',raw,1)[0]
 if raw[0]==0xeb or 0x70<=raw[0]<=0x7f:return pc+len(raw)+struct.unpack_from('<b',raw,1)[0]
 if raw[:1]==b'\x0f'and len(raw)==6 and 0x80<=raw[1]<=0x8f:return pc+len(raw)+struct.unpack_from('<i',raw,2)[0]
 return None
def graph(code,start,end):
 pending=[start];seen=set();edges=[];calls=[];returns=[]
 while pending:
  pc=pending.pop()
  if pc in seen:continue
  need(pc in code and start<=pc<end,'Whole local CFG branch instruction '+hex(pc));seen.add(pc);i=code[pc];raw=bytes.fromhex(i['hex']);n=pc+len(raw);t=target(pc,raw);m=i['mnemonic']
  if m=='ret':returns.append(pc);continue
  if m=='call':
   if t is not None:calls.append(dict(site=pc,target=t,return_PC=n,kind='direct'))
   else:
    need(raw[:2]==b'\xff\x15'and len(raw)==6,'Bounded IAT CALL encoding');calls.append(dict(site=pc,IAT=struct.unpack_from('<I',raw,2)[0],return_PC=n,kind='import'))
   edges.append([pc,n,'return-continuation']);pending.append(n)
  elif m=='jmp':need(t is not None,'Direct local JMP');edges.append([pc,t,'jump']);pending.append(t)
  elif m.startswith('j'):
   need(t is not None,'Direct local conditional');edges.extend([[pc,t,'taken'],[pc,n,'fallthrough']]);pending.extend([t,n])
  else:edges.append([pc,n,'next']);pending.append(n)
 need(seen==set(pc for pc in code if start<=pc<end),'Complete function source contains no unaccounted local instruction')
 return dict(entry=start,end_exclusive=end,instructions=len(seen),edges=edges,calls=calls,returns=returns,complete_local_CFG=True)
def ordered(text,fragments,label):
 pos=-1
 for s in fragments:
  nxt=text.find(s,pos+1);need(nxt>pos,label+' fragment '+s);pos=nxt
 return dict(label=label,ordered_fragments=fragments)
def main(name):
 out=BASE/name;need(out.parent==BASE and name.startswith('independent-contract-')and not out.exists(),'New independent report only');out.mkdir(parents=True)
 try:
  for p,h in FROZEN.items():pin(ROOT/p,h)
  spec=importlib.util.spec_from_file_location('mainargs_independent_pe',ROOT/'tools/analysis/pe.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  gp=ROOT/'MW3/Mech3.exe';dp=ROOT/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL';game=mod.PEImage(gp.read_bytes());dll=mod.PEImage(dp.read_bytes())
  def source(pe,va,n):return pe.read(pe.rva_range(va-pe.image_base,n)[0],n)
  def owner(pe,va,name,library,raw):
   xs=[dict(library=x['library'],**s)for x in pe.imports()for s in x['symbols']if pe.image_base+s['iat_rva']==va];need(len(xs)==1 and xs[0]['library']==library and xs[0].get('name')==name,'Unique original named owner '+name);need(pe.rva_u32(va-pe.image_base)==raw,'Original raw IAT '+name);return dict(slot=va,raw_IAT=raw,**xs[0])
  game_owner=owner(game,0x5bb514,'__getmainargs','MSVCRT.dll',0x1ded02);os_owner=owner(dll,0x7802e018,'GetModuleFileNameA','KERNEL32.dll',0x343b0)
  ex=[e for e in dll.exports()if '__getmainargs'in e['names']];need(len(ex)==1 and ex[0]['rva']==0xba5e and ex[0]['ordinal']==89 and 'forwarder'not in ex[0],'Exact direct provider export')
  ranges=[('game-continuation',gp,game,0x5ac445,0x5ac483),('mainargs',dp,dll,0x7800ba5e,0x7800baa0),('normal-builder',dp,dll,0x7800bbbc,0x7800bc48),('normal-parser',dp,dll,0x7800bc48,0x7800bdfc),('wildcard-builder',dp,dll,0x7800b3b4,0x7800b451)]
  code={};spans=[];graphs={}
  for label,path,pe,start,end in ranges:
   b=source(pe,start,end-start);bp=out/(label+'.bin');bp.write_bytes(b);pin(bp);spans.append(dict(label=label,start=start,end_exclusive=end,size=end-start,sha256=sha(bp)))
   decoded=run(out,[LLVM/'llvm-objdump.exe','-d','--x86-asm-syntax=intel',f'--start-address={start}',f'--stop-address={end}',path],label+'-decode')
   local={}
   for line in decoded.splitlines():
    m=re.match(r'^\s*([0-9a-f]+):\s+((?:[0-9a-f]{2}\s+)+)\s*([a-z][a-z0-9]*)\s*(.*?)\s*$',line)
    if not m:continue
    pc=int(m[1],16);raw=bytes.fromhex(m[2]);need(start<=pc<end and source(pe,pc,len(raw))==raw and pc not in code,'Exact unique original PC');i=dict(hex=raw.hex(),size=len(raw),mnemonic=m[3],operands=re.sub(r'\s*<[^>]*>','',m[4]).strip());local[pc]=i;code[pc]=i
   pcs=sorted(local);need(pcs and pcs[0]==start and pcs[-1]+local[pcs[-1]]['size']==end and all(a+local[a]['size']==b for a,b in zip(pcs,pcs[1:])),'Complete contiguous literal span '+label)
   if label!='game-continuation':graphs[label]=graph(local,start,end)
  expected={0x5ac448:('mov','edx, dword ptr [0x736598]'),0x5ac44e:('mov','dword ptr [ebp - 0x6c], edx'),0x5ac451:('lea','eax, [ebp - 0x6c]'),0x5ac455:('mov','ecx, dword ptr [0x736594]'),0x5ac45c:('lea','edx, [ebp - 0x64]'),0x5ac460:('lea','eax, [ebp - 0x70]'),0x5ac464:('lea','ecx, [ebp - 0x60]'),0x5ac468:('call','dword ptr [0x5bb514]'),0x5ac46e:('add','esp, 0x14'),0x5ac47b:('call','0x5ac598'),0x7800ba5e:('push','ebp'),0x7800ba5f:('mov','ebp, esp'),0x7800ba61:('mov','eax, dword ptr [ebp + 0x18]'),0x7800ba64:('cmp','dword ptr [ebp + 0x14], 0x0'),0x7800ba68:('mov','eax, dword ptr [eax]'),0x7800ba6a:('mov','dword ptr [0x78037150], eax'),0x7800ba6f:('je','0x7800ba99'),0x7800ba99:('call','0x7800bbbc'),0x7800bbbc:('push','ebp'),0x7800bbbd:('mov','ebp, esp'),0x7800bbbf:('push','ecx'),0x7800bbc0:('push','ecx'),0x7800bbc1:('push','esi'),0x7800bbc2:('push','edi'),0x7800bbc3:('mov','esi, 0x7803b3f0'),0x7800bbc8:('push','0x104'),0x7800bbcd:('push','esi'),0x7800bbce:('push','0x0'),0x7800bbd0:('call','dword ptr [0x7802e018]')}
  for pc,(m,o)in expected.items():need(code[pc]['mnemonic']==m and code[pc]['operands']==o,'Original source operand '+hex(pc))
  need(graphs['mainargs']['calls']==[dict(site=0x7800ba71,target=0x7800b3b4,return_PC=0x7800ba76,kind='direct'),dict(site=0x7800ba99,target=0x7800bbbc,return_PC=0x7800ba9e,kind='direct')]or sorted(graphs['mainargs']['calls'],key=lambda x:x['site'])==[dict(site=0x7800ba71,target=0x7800b3b4,return_PC=0x7800ba76,kind='direct'),dict(site=0x7800ba99,target=0x7800bbbc,return_PC=0x7800ba9e,kind='direct')],'Only original two mainargs direct dependencies')
  need(graphs['normal-parser']['calls']==[],'Normal parser has no calls; integer string-only body')
  bss=[]
  for va in(0x736594,0x736598):
   sections=[s for s in game.sections if s['virtual_address']<=va-game.image_base and va-game.image_base+4<=s['virtual_address']+s['virtual_size']];need(len(sections)==1 and sections[0]['writable']and va-game.image_base>=sections[0]['virtual_address']+sections[0]['raw_size'],'Virtual zero-filled game BSS DWORD');bss.append(dict(address=va,value=0,source='Original PE virtual-zero data tail'))
  pages=[]
  for va,need_perm in[(0x7800b000,'RX'),(0x7802e000,'R'),(0x78037000,'RW'),(0x7803b000,'RW')]:
   s=[s for s in dll.sections if s['virtual_address']<=va-dll.image_base and va-dll.image_base+4096<=s['virtual_address']+max(s['virtual_size'],s['raw_size'])];need(len(s)==1 and s[0]['readable']and (s[0]['executable']if need_perm=='RX'else s[0]['writable']if need_perm=='RW'else not s[0]['writable']),'Provider page original permissions');pages.append(dict(base=va,source_permissions=need_perm,existing_owner=True,remap_or_reseed=False,sha256=hashlib.sha256(source(dll,va,4096)).hexdigest()))
  need(source(dll,0x78037150,4)==b'\0'*4,'Source newmode zero identity; source store still required')
  prep=ROOT/'reports/m4-crt-mainargs/recovery-r3';ir=[]
  ma=pin(prep/'mainargs-host.ll').read_text();na=pin(prep/'normal_argv-host.ll').read_text();pin(prep/'mainargs-guest.ll');pin(prep/'normal_argv-guest.ll');pin(prep/'report.json');pin(prep/'pins.json')
  need(not re.search(r'\b(?:nounwind|willreturn)\b',ma+na),'Checked provider unwind not prohibited')
  ir.append(ordered(ma,['%12 = call noundef ptr @__remill_write_memory_32','store i32 %8, ptr %6'], 'Mainargs PUSH store before State ESP'))
  ir.append(ordered(ma,['%101 = call noundef ptr @__remill_write_memory_32','store i32 %97, ptr %95','store i32 %92, ptr %102','%105 = call ptr @sub_7800bbbc'], 'Source BA99 CALL store then ESP/PC then native direct route'))
  ir.append(ordered(na,['%114 = call noundef i32 @__remill_read_memory_32','%118 = call noundef ptr @__remill_write_memory_32','store i32 %113, ptr %111','store i32 %114, ptr %119','%122 = call ptr @__remill_function_call'], 'Source BBD0 IAT read then return store then ESP/PC then import bridge'))
  accesses=[(0x7800ba5e,0x2000185c,'entry EBP',1),(0x7800ba61,0x20001874,0x20001890,0),(0x7800ba64,0x20001870,0,0),(0x7800ba68,0x20001890,0,0),(0x7800ba6a,0x78037150,0,1),(0x7800ba99,0x20001858,0x7800ba9e,1),(0x7800bbbc,0x20001854,0x2000185c,1),(0x7800bbbf,0x20001850,0x2000189c,1),(0x7800bbc0,0x2000184c,0x2000189c,1),(0x7800bbc1,0x20001848,'entry ESI',1),(0x7800bbc2,0x20001844,'entry EDI',1),(0x7800bbc8,0x20001840,260,1),(0x7800bbcd,0x2000183c,0x7803b3f0,1),(0x7800bbce,0x20001838,0,1),(0x7800bbd0,0x7802e018,0x343b0,0),(0x7800bbd0,0x20001834,0x7800bbd6,1)]
  instruction_path=[0x7800ba5e,0x7800ba5f,0x7800ba61,0x7800ba64,0x7800ba68,0x7800ba6a,0x7800ba6f,0x7800ba99,0x7800bbbc,0x7800bbbd,0x7800bbbf,0x7800bbc0,0x7800bbc1,0x7800bbc2,0x7800bbc3,0x7800bbc8,0x7800bbcd,0x7800bbce,0x7800bbd0]
  source_contract=dict(incoming_game_EBP=0x200018fc,incoming_provider_ESP=0x20001860,game_return_word=0x5ac46e,five_arguments=[dict(index=1,stack=0x20001864,value=0x2000189c,meaning='argc output DWORD pointer'),dict(index=2,stack=0x20001868,value=0x2000188c,meaning='argv output guest-pointer cell'),dict(index=3,stack=0x2000186c,value=0x20001898,meaning='environment output guest-pointer cell'),dict(index=4,stack=0x20001870,value=0,meaning='wildcard value, not pointer'),dict(index=5,stack=0x20001874,value=0x20001890,meaning='startupinfo pointer; first DWORD copied from736598')],cdecl_bytes=20,provider_internal_CALL=dict(site=0x7800ba99,target=0x7800bbbc,return_PC=0x7800ba9e,frame=0x20001858,args_bytes=0,route='Typed same-Context native provider call; no public Runtime translation or generic ledger/frame'),actual_instruction_path=instruction_path,actual_memory_accesses=[dict(pc=pc,address=a,value=v,width=4,write=w)for pc,a,v,w in accesses],required_stop=dict(source_site=0x7800bbd0,provider_IAT=0x7802e018,raw_target=0x343b0,real_return_PC=0x7800bbd6,frame=0x20001834,args=[0,0x7803b3f0,260],buffer_size=260,buffer_end_exclusive=0x7803b4f4,no_OS_service_success=True),terminal_State=dict(EAX=0,ECX=0x2000189c,EDX=0x20001898,EBX='carried entry EBX',ESP=0x20001834,EBP=0x20001854,ESI=0x7803b3f0,EDI='carried entry EDI',PC=0x343b0,arithmetic_flags=dict(CF=0,PF=1,AF=0,ZF=1,SF=0,OF=0),rflags_other='unchanged source flags representation',FP='Full State x87/legacy ENV/raw80 and separate FX carried unchanged; no prefix FP instruction'),Runtime_CPU_on_failure=dict(EIP=0x5bb514,ESP=0x20001860,EAX=0x2000188c,ECX=0x2000189c,EDX=0x20001898,EBP=0x200018fc,remaining='Last game CALL projection; source provider updates are not projected after fault'),unwind_contract=dict(public_fault='Fault(unresolved_import,{7800BBD0},{7802E018},detail) after checked raw IAT and real CALL frame',Runtime_r9_unchanged=True,generic_runtime_frames='Only real game mainargs service frame; nested provider route does not create one',owners='Exact current serial mainargs token; old entry/control/matherr/initterm tokens rejected while provider active',cleanup='Owner/active/boundary depth cleared before checkpoint observer that may throw; encompassing Runtime catches public Fault and poisons terminally',no_return_credit=True,ledger_mainargs_completed=False),partial_fault_order=dict(PUSH='Source PC set, checked memory store before ESP publication',CMP='Operand read before ALU/flag publication',MOV_read='Checked read then destination register publication',CALL_direct='Checked return word write before ESP/target PC/native route',CALL_IAT='Checked raw IAT read before checked return write before ESP/target PC/import route',rejected_import='Real CALL completed in State, import success/return not executed'),unchanged_outputs=['argc189C','argv188C','env1898','filenamebuffer7803B3F0..7803B4F4'],next_success_prerequisites=['Measured GetModuleFileNameA owned buffer/error/truncation contract','Actual commandline producer composed before dereference7800BBE3','Parser classification-table initialization/locale ownership','Actual malloc/newmode ownership/failure behavior','Environment producer/vector/string ownership'],later_game_call=dict(site=0x5ac47b,target=0x5ac598,return_PC=0x5ac480,interval=[0x5e0000,0x5e0244],unadmitted=True))
  cp=out/'source-contract.json';cp.write_text(json.dumps(dict(instructions=code,graphs=graphs,contract=source_contract),indent=2)+'\n');pin(cp);pin(Path(__file__))
  report=dict(passed=True,scope='Independent static original-source and preserved source-IR contract for actual native mainargs-to-first-provider-import stop',game_import=game_owner,provider_export=ex[0],provider_import=os_owner,source_spans=spans,whole_local_CFGs=graphs,actual_prefix_instructions=19,actual_prefix_memory_accesses=16,total_borrowed_checkpoint_pages=16,new_pages=0,provider_page_ownership=pages,source_BSS=bss,IR_order=ir,source_contract=source_contract,commands=COMMANDS,limitations=['No candidate, native body, original provider or ordinary game executed by this review','Literal file zero is source identity, not runtime initialized argc/argv/environment','Successful OS filename output, parser/allocation/environment and provider returns remain unadmitted','Original arbitrary async observers/hostile concurrency/mappings are outside trusted serial source domain','No original mainargs BEFORE hardware capture; parent must derive whole composition from original FDIV BEFORE corpus'],files=PINS,whole_M4_complete=False)
 except Exception as e:report=dict(passed=False,error=str(e),traceback=traceback.format_exc(),commands=COMMANDS,files=PINS)
 rp=out/'report.json';rp.write_text(json.dumps(report,indent=2)+'\n');pin(rp);(out/'pins.json').write_text(json.dumps(dict(files=PINS),indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],report=str(rp),report_sha256=sha(rp),bindings=len(PINS),error=report.get('error'))));return 0 if report['passed']else 1
if __name__=='__main__':raise SystemExit(main(sys.argv[1]))
