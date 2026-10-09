"""Prepare a fresh authority around unchanged literal x64 source objects."""
import hashlib,json,pathlib,re,shutil,sys,traceback
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2]
HERE=pathlib.Path(__file__).resolve().parent
BASE=ROOT/'reports/m4-crt-heap-return'
OLD=ROOT/'reports/m4-crt-heap-version/preparation-r2'
OLD_BUILD=ROOT/'reports/m4-crt-heap-version/build-r3/build.json'
REC=ROOT/'reports/m4-crt-heap-return-recovery/recovery-r1'
ACCEPT_SHA='cedd67126afce1ec3392e8e0f8fec71f54823e58bc353055aee723203eef18d1'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def replace(s,a,b):
 assert s.count(a)==1,(a[:100],s.count(a))
 return s.replace(a,b)
def main(name,recovery_sha):
 out=BASE/name
 assert re.fullmatch('preparation-r[1-9][0-9]*',name) and not out.exists()
 out.mkdir(parents=True)
 try:
  accepted=ROOT/'reports/m4-crt-heap-version-root/root-acceptance-r1/report.json'
  assert sha(accepted)==ACCEPT_SHA and read(accepted)['passed']
  assert sha(REC/'report.json')==recovery_sha and read(REC/'report.json')['passed']
  for manifest in (OLD/'pins.json',REC/'pins.json'):
   for p,h in read(manifest)['files'].items():assert sha(p)==h,p
  for p in OLD.iterdir():
   if p.suffix in ('.cpp','.hpp','.inc'):
    shutil.copyfile(p,out/p.name);shutil.copyfile(p,out/(p.name+'.ancestor'))
  for name in ('heap_return.hpp','heap_return_binding.inc'):shutil.copyfile(HERE/name,out/name)
  p=out/'composition.cpp';s=p.read_text()
  s=replace(s,'#include "heap_version.hpp"','#include "heap_version.hpp"\n#include "heap_return.hpp"')
  s=replace(s,'namespace hv=mw34::m4_crt_heap_version;','namespace hv=mw34::m4_crt_heap_version;\nnamespace hr=mw34::m4_crt_heap_return;')
  s=replace(s,'#include "heap_version_binding.inc"','#include "heap_version_binding.inc"\n#include "heap_return_binding.inc"')
  for line in s.splitlines():
   if not(line.startswith('extern "C"') and 'noexcept(false)' in line and '{' in line):continue
   marker='if(hv::has_authority())'
   if marker in line:
    opening='noexcept(false) {' if 'noexcept(false) {' in line else 'noexcept(false){'
    action=line[line.index(marker)+len(marker):]
    close=action.index('}')
    action=action[:close+1].replace('hv::','hr::')
    s=replace(s,line,line.replace(opening,opening+'if(hr::has_authority())'+action,1))
   elif 'return hv::current' in line:s=replace(s,line,line.replace('return hv::current','return hr::current'))
  p.write_text(s)
  p=out/'mainargs_binding.inc';s=p.read_text()
  s=replace(s,'hv::Binding heap_version;','hv::Binding heap_version;hr::Binding heap_return;')
  s=replace(s,'heap_version(context,provider,mode){}','heap_version(context,provider,mode),heap_return(context,provider,mode){}')
  s=replace(s,'mainargs_binding->heap_version.start(c);','mainargs_binding->heap_return.start(c);mainargs_binding->heap_version.start(c);');p.write_text(s)
  p=out/'observations.hpp';s=p.read_text().replace('hv::capture_for(r)','hr::capture_for(r)')
  s=replace(s,' fresh_output(phase/"state.bin",r.remill_state());',' {std::array<unsigned,8>progress{};if(auto*known=hr::capture_for(r))progress=known->progress();raw_output(phase/"heap-return-progress.bin",progress);}\n fresh_output(phase/"state.bin",r.remill_state());');p.write_text(s)
  p=out/'main_v2.inc';s=p.read_text().replace('MW34_CRT_HEAP_VERSION_NO_MAIN','MW34_CRT_HEAP_RETURN_NO_MAIN')
  s=replace(s,'scenario+121','scenario+133')
  s=replace(s,'namespace mw34::m4_crt_heap_version {void checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}}','namespace mw34::m4_crt_heap_version {void checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}}\nnamespace mw34::m4_crt_heap_return {void checkpoint(Runtime&r,const char*name){snapshot(r,checkpoint_directory,name);}}')
  s=replace(s,'auto&heap_version=mainargs.heap_version;','auto&heap_version=mainargs.heap_version;auto&heap_return=mainargs.heap_return;')
  s=replace(s,'hv::admitted_binding=&heap_version;boundary','hv::admitted_binding=&heap_version;hr::binding=&heap_return;hr::admitted_binding=&heap_return;boundary')
  a=s.index('  require(!heap_version.active');b=s.index('  const auto state_copy=context.state();',a)
  s=s[:a]+(HERE/'worker_gate.inc').read_text()+s[b:]
  s=replace(s,'snapshot(r,row,"retry-after");hv::binding=nullptr;','snapshot(r,row,"retry-after");hr::binding=nullptr;hr::admitted_binding=nullptr;hv::binding=nullptr;');p.write_text(s)
  old_build=read(OLD_BUILD);objects=old_build['entry_objects'];libraries=old_build['libraries']
  assert len(objects)==38 and len(libraries)==2
  for p,h in {**objects,**libraries}.items():assert sha(p)==h,p
  files={str(p.absolute()):sha(p) for p in out.iterdir() if p.is_file()}
  for p in (HERE/'prepare.py',HERE/'worker_gate.inc',HERE/'heap_return.hpp',HERE/'heap_return_binding.inc',accepted,OLD/'pins.json',REC/'report.json',REC/'pins.json',OLD_BUILD,pathlib.Path(sys.executable)):
   files[str(p.absolute())]=sha(p)
  files.update(objects);files.update(libraries)
  report=dict(passed=True,scope='Source/build only: naturally resume original translated initializer after genuine selector RET, source mode1 publication and initializer RET; stop before fragment caller',
   source_identity_bytes=2086,reused_compiled_source_bytes=230,new_compiled_source_bytes=0,new_guest_objects=0,reused_guest_objects=38,reused_FDIV_libraries=2,reused_object_hashes=objects,reused_library_hashes=libraries,
   qualifying_executed_source_bytes=192,added_executed_source_bytes=23,source_accesses=35,source_PCs=59,source_CALLs=5,source_RETs=3,separate_API_return_reads=2,declared_API_output_DWORD_stores=37,borrowed_pages=21,prior_pages_preserved=21,new_pages=0,
   Policy_and_TIB_unchanged=True,State_bytes=3504,FX_bytes=512,CPU_bytes=40,State_reseed_after_writer=False,Runtime_CPU_preserved=True,Runtime_call_record_added=False,
   selector_unwind='Same typed token through the existing translated native CALL chain; binding depth3 to2 only; no State projection or provider reentry',
   source_POP_order='Generated ESP advances before checked POP read; read-before-EAX-publication',source_RET_order='Checked read before generated EIP/ESP publication',
   source_mode_global_write='Literal source MOV39EB only; no host publication',scheduler_store_count=0,scheduler_State_projection='Initial EIP only, unchanged accepted seam',
   undefined_AF=dict(sites=[0x780039bf,0x780039d6,0x780058db,0x780058c5,0x78003a31],admitted_generated_representative=0,universal_AF_claim=False),
   original_attach_executed=False,HeapCreate_called=False,OS_query_called=False,selector_return1_produced=False,heap_mode_global_published=False,initializer_RET_executed=False,heap_initialized=False,fragment_caller_continued=False,
   locale_body_executed=False,parser_body_executed=False,original_executed=False,native_component_executed=False,whole_M4_complete=False,commands=[],recovery_sha256=recovery_sha,baseline_acceptance_sha256=ACCEPT_SHA)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files[str(out/'report.json')]=sha(out/'report.json')
  (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
  print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))
 except Exception:
  (out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(*sys.argv[1:])
