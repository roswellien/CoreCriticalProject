"""Prepare exact selector/probe objects and carried owned-heap experiment."""
import ctypes as c
import hashlib, importlib.util, json, pathlib, re, shutil, subprocess, sys, traceback
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).absolute().parents[2]
HERE=pathlib.Path(__file__).absolute().parent
BASE=ROOT/'reports/m4-crt-heap-mode'
OLD=ROOT/'reports/m4-crt-heap-create/preparation-r2'
REC=ROOT/'reports/m4-crt-heap-mode-recovery/recovery-r1'
ACCEPT_SHA='e40df22e7b6263f75d9215cdaeadeb6a30030a4b07008c58442d8512d10c4326'

def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def replace(s,a,b):
 assert s.count(a)==1,(a[:100],s.count(a))
 return s.replace(a,b)

def main(name,recovery_sha):
 out=BASE/name
 assert re.fullmatch('preparation-r[1-9][0-9]*',name) and out.parent==BASE and not out.exists()
 out.mkdir(parents=True)
 commands=[]
 try:
  accepted=ROOT/'reports/m4-crt-heap-create-root/root-acceptance-r1/report.json'
  assert sha(accepted)==ACCEPT_SHA and read(accepted)['passed']
  assert sha(REC/'report.json')==recovery_sha and read(REC/'report.json')['passed']
  for manifest in (OLD/'pins.json',REC/'pins.json'):
   for p,h in read(manifest)['files'].items():assert sha(p)==h,p
  for p in OLD.iterdir():
   if p.suffix in ('.cpp','.hpp','.inc'):
    shutil.copyfile(p,out/p.name);shutil.copyfile(p,out/(p.name+'.ancestor'))
  for name in ('heap_mode.hpp','heap_mode_binding.inc'):shutil.copyfile(HERE/name,out/name)
  llvm=ROOT/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin'
  lifter=ROOT/'local/tools/remill-x87-control-repair/remill-lift-control-21.exe'
  sem=ROOT/'local/tools/remill-x87-control-repair/semantics/x86.bc'
  def run(program,args,label):
   argv=[str(program),*map(str,args)]
   cp=subprocess.run(argv,capture_output=True,timeout=120,creationflags=0x08000000)
   (out/(label+'.stdout')).write_bytes(cp.stdout);(out/(label+'.stderr')).write_bytes(cp.stderr)
   commands.append(dict(program=str(program),arguments=argv,exit_code=cp.returncode))
   assert cp.returncode==0,(label,cp.stderr[-1000:])
  lower_source=(ROOT/'tools/m4-crt-mainargs-recovery/recover.py').read_text()
  body=lower_source[lower_source.index('def lower('):lower_source.index("if __name__ == '__main__':")]
  body=body.replace('mw34_mainargs_','mw34_heap_mode_').replace("and '__remill_missing_block' not in text",'')
  sys.path.insert(0,str(ROOT/'tools/lifting'))
  from host_adapter import LLVM,HOST_LAYOUT,FUNCTION_INDEX,checked_state_offsets
  namespace=dict(c=c,re=re,sha=sha,LLVM=LLVM,HOST_LAYOUT=HOST_LAYOUT,FUNCTION_INDEX=FUNCTION_INDEX,
   checked_state_offsets=checked_state_offsets,need=lambda ok,why:None if ok else (_ for _ in ()).throw(ValueError(why)),
   BRIDGES={'__remill_read_memory_32','__remill_write_memory_32','__remill_write_memory_8','__remill_read_memory_8','__remill_function_call','__remill_function_return','__remill_jump','__remill_missing_block'})
  exec(compile(body,str(ROOT/'tools/m4-crt-mainargs-recovery/recover.py'),'exec'),namespace)
  upstream=(ROOT/'local/tools/remill-v6.0.1/remill-6.0.1/tests/X86/Run.cpp').read_text()
  native={}
  for component,label,entry,digest in (
   ('selector','selector-prefix',0x78003a0c,'40dd412d93fff04b1e6bb4fd70fd4ecca4cf95cc9d4c152906a537f0ebbc2135'),
   ('probe','stack-probe',0x780058b5,'6c3968aa37f1e1ba00793f924b85c69c73dedc74491d3770c477e82b6107dd77')):
   code=(REC/(label+'.bin')).read_bytes();assert sha(REC/(label+'.bin'))==digest
   (out/(component+'-source.bin')).write_bytes(code)
   run(lifter,['--arch=x86','--os=windows','--address='+str(entry),'--entry_address='+str(entry),
    '--bytes='+code.hex(),'--semantics_dir='+str(sem.parent),'--ir_out='+str(out/(component+'-guest.ll'))],component+'-lift')
   calls=[dict(kind='direct',target=int(a,16)) for a in re.findall(r'^declare ptr @sub_([0-9a-f]+)',(out/(component+'-guest.ll')).read_text(),re.M)]
   native[component]=namespace['lower'](out,component,dict(entry=entry,outgoing_calls=calls),llvm/'LLVM-C.dll',upstream,run,llvm)
  p=out/'composition.cpp';s=p.read_text()
  s=replace(s,'#include "heap_create.hpp"','#include "heap_create.hpp"\n#include "heap_mode.hpp"')
  s=replace(s,'namespace hc=mw34::m4_crt_heap_create;','namespace hc=mw34::m4_crt_heap_create;\nnamespace hm=mw34::m4_crt_heap_mode;')
  s=replace(s,'#include "heap_create_binding.inc"','#include "heap_create_binding.inc"\n#include "heap_mode_binding.inc"')
  s=replace(s,'address==0x78003000)?','address==0x78003000||address==0x78005000)?')
  routes={'__remill_read_memory_32':'return hm::current(p,a)->read32(a);',
   '__remill_write_memory_32':'hm::current(p,a)->write32(a,v);return p;',
   '__remill_function_call':'return hm::current(p,a)->called(s,a,p);',
   '__remill_function_return':'return hm::current(p,a)->returned(s,a,p);',
   'mw34_heap_init_provider_undefined_8':'return hm::current(hm::owner,0)->undefined();'}
  for line in s.splitlines():
   if not(line.startswith('extern "C"') and 'noexcept(false)' in line and '{' in line):continue
   opening='noexcept(false) {' if 'noexcept(false) {' in line else 'noexcept(false){'
   key=next((k for k in routes if k+'(' in line),None)
   action=routes[key] if key else ('return hm::current(p,a)->called(s,a,p);' if line.startswith('extern "C" void*sub_') else 'hm::current(hm::owner,0)->unsupported(0,"Other bridge cannot use active heap mode authority");')
   s=replace(s,line,line.replace(opening,opening+'if(hm::has_authority()){'+action+'}',1))
  extra=''
  for bridge in sorted(set(v for n in native.values() for v in n['bridges'])):
   if re.search(r'\b'+re.escape(bridge)+r'\(',s):continue
   if bridge.endswith('_undefined_8'):
    extra+='extern "C" unsigned char '+bridge+'()noexcept(false){return hm::current(hm::owner,0)->undefined();}\n'
   elif bridge.startswith('sub_') or bridge=='__remill_missing_block':
    extra+='extern "C" void*'+bridge+'(State*s,unsigned a,void*p)noexcept(false){return hm::current(p,a)->called(s,a,p);}\n'
   else:raise ValueError('New unreviewed bridge '+bridge)
  s=replace(s,'#include "main_v2.inc"',extra+'#include "main_v2.inc"');p.write_text(s)
  p=out/'mainargs_binding.inc';s=p.read_text()
  s=replace(s,'hc::Binding heap_create;','hc::Binding heap_create;hm::Binding heap_mode;')
  s=replace(s,'heap_create(context,provider,mode){}','heap_create(context,provider,mode),heap_mode(context,provider,mode){}')
  s=replace(s,'mainargs_binding->heap_create.start(c);','mainargs_binding->heap_mode.start(c);mainargs_binding->heap_create.start(c);');p.write_text(s)
  p=out/'observations.hpp';s=p.read_text()
  s=replace(s,'std::array<unsigned,18>composition_pages','std::array<unsigned,20>composition_pages')
  s=replace(s,'0x78003000,0x78035000};','0x78003000,0x78035000,0x78005000,0x20000000};')
  s=replace(s,'if(auto*known=hc::capture_for(r))','if(auto*known=hm::capture_for(r))')
  s=replace(s,'fresh_output(phase/"state.bin",r.remill_state());','for(auto [address,size,name]:std::array<std::tuple<unsigned,unsigned,const char*>,2>{{{hm::mode,37,"heap-mode-selector.bin"},{hm::probe,49,"heap-stack-probe.bin"}}}){std::vector<std::byte>b(size);r.memory().read({address},b);fresh_output(phase/name,b);}\n fresh_output(phase/"state.bin",r.remill_state());');p.write_text(s)
  p=out/'main_v2.inc';s=p.read_text().replace('MW34_CRT_HEAP_CREATE_NO_MAIN','MW34_CRT_HEAP_MODE_NO_MAIN')
  s=replace(s,'scenario+97','scenario+109')
  s=replace(s,'namespace mw34::m4_crt_heap_create {void checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}}','namespace mw34::m4_crt_heap_create {void checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}}\nnamespace mw34::m4_crt_heap_mode {void checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}}')
  s=replace(s,'  fd::Registry fdiv(r);','  {auto page=provider_raw_page(provider,0x78005000);r.memory().map({0x78005000},4096,Permissions::read|Permissions::write);r.memory().write({0x78005000},page);r.memory().protect({0x78005000},Permissions::read|Permissions::execute);}\n  r.memory().map({0x20000000},4096,Permissions::read|Permissions::write);\n  fd::Registry fdiv(r);')
  s=replace(s,'auto&heap_create=mainargs.heap_create;','auto&heap_create=mainargs.heap_create;auto&heap_mode=mainargs.heap_mode;')
  s=replace(s,'hc::admitted_binding=&heap_create;boundary','hc::admitted_binding=&heap_create;hm::binding=&heap_mode;hm::admitted_binding=&heap_mode;boundary')
  a=s.index('  std::ofstream heap_create_reason(');b=s.index('  const auto state_copy=context.state();',a)
  s=s[:a]+(HERE/'worker_gate.inc').read_text()+s[b:]
  s=replace(s,'snapshot(r,row,"retry-after");hc::binding=nullptr;','snapshot(r,row,"retry-after");hm::binding=nullptr;hm::admitted_binding=nullptr;hc::binding=nullptr;');p.write_text(s)
  files={str(p.absolute()):sha(p) for p in out.iterdir() if p.is_file()}
  for p in (HERE/'prepare.py',HERE/'worker_gate.inc',HERE/'heap_mode.hpp',HERE/'heap_mode_binding.inc',accepted,OLD/'pins.json',REC/'report.json',REC/'pins.json',ROOT/'tools/m4-crt-mainargs-recovery/recover.py',ROOT/'tools/lifting/host_adapter.py',lifter,sem,llvm/'LLVM-C.dll',llvm/'clang.exe',llvm/'llvm-nm.exe',pathlib.Path(sys.executable)):
   files[str(p.absolute())]=sha(p)
  report=dict(passed=True,scope='Source/build preparation only: genuine selector/probe on carried private owned heap to first unresolved OS query',
   source_bodies=native,source_identity_bytes=2026,reused_compiled_source_bytes=84,new_compiled_source_bytes=86,new_guest_objects=4,reused_guest_objects=26,
   success_executed_source_bytes=132,source_accesses=24,source_PCs=39,separate_API_return_reads=1,borrowed_pages=20,prior_pages_preserved=18,
   additional_raw_RX_page=0x78005000,additional_owned_lower_stack_page=0x20000000,lower_stack_domain='Declared fresh initial owned research input, ordinary zero; not original-captured bytes or native guard-stack growth',
   Policy_and_TIB_unchanged=True,State_bytes=3504,FX_bytes=512,State_reseed_after_writer=False,Runtime_CPU_preserved=True,Runtime_call_record_added=False,
   scheduler_store_count=0,scheduler_State_projection='EIP only',undefined_AF=dict(sites=[0x780039bf,0x780039d6,0x780058db,0x780058c5],admitted_generated_representative=0,universal_AF_claim=False),
   original_attach_executed=False,HeapCreate_called=False,OS_query_called=False,heap_mode_selected=False,initializer_RET_executed=False,heap_initialized=False,
   locale_body_executed=False,parser_body_executed=False,original_executed=False,native_component_executed=False,whole_M4_complete=False,commands=commands,
   recovery_sha256=recovery_sha,baseline_acceptance_sha256=ACCEPT_SHA)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files[str(out/'report.json')]=sha(out/'report.json')
  (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
  print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))
 except Exception:
  (out/'failure.txt').write_text(traceback.format_exc());raise

if __name__=='__main__':main(*sys.argv[1:])
