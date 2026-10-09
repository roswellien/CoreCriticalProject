"""Prepare full authentic mode-1 malloc/free bodies on the frozen heap-return baseline."""
import ctypes as c
import hashlib,json,pathlib,re,shutil,subprocess,sys,traceback
sys.dont_write_bytecode=True
ROOT=pathlib.Path(__file__).resolve().parents[2]
HERE=pathlib.Path(__file__).resolve().parent
BASE=ROOT/'reports/m4-crt-allocation'
OLD=ROOT/'reports/m4-crt-heap-return/preparation-r2'
OLD_BUILD=ROOT/'reports/m4-crt-heap-return/build-r2/build.json'
REC=ROOT/'reports/m4-crt-allocation-recovery/recovery-r1'
ACCEPT_SHA='7a71e5de996f841010817182875a7e068eba0dee9f7e0645efaca9bfde60aeaf'
COMPONENTS=(('caller','caller-cleanup'),('malloc','malloc-wrapper'),('size','malloc-size'),
 ('worker','malloc-worker-hot'),('round','malloc-round-mode1'),('null','malloc-null-cold'),
 ('free','free-hot'),('freecold','free-mode1-cold'))
OVERLAPPING=(('alloc_tail','malloc-worker-hot',0x78001377,16),
 ('worker_epilogue','malloc-worker-hot',0x78001367,15),
 ('free_tail','free-hot',0x78001428,16),('free_epilogue','free-hot',0x78001416,15),
 ('size_ret','malloc-size',0x780012e2,1))
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def replace(s,a,b):
 assert s.count(a)==1,(a[:100],s.count(a))
 return s.replace(a,b)
def main(name,recovery_sha):
 out=BASE/name
 assert re.fullmatch('preparation-r[1-9][0-9]*',name) and not out.exists()
 out.mkdir(parents=True);commands=[]
 try:
  accepted=ROOT/'reports/m4-crt-heap-return-root/root-acceptance-r1/report.json'
  assert sha(accepted)==ACCEPT_SHA and read(accepted)['passed']
  assert sha(REC/'report.json')==recovery_sha and read(REC/'report.json')['passed']
  recovery=read(REC/'report.json')
  for manifest in (OLD/'pins.json',REC/'pins.json'):
   for p,h in read(manifest)['files'].items():assert sha(p)==h,p
  for p in OLD.iterdir():
   if p.suffix in ('.cpp','.hpp','.inc'):
    shutil.copyfile(p,out/p.name);shutil.copyfile(p,out/(p.name+'.ancestor'))
  for name in ('allocation.hpp','allocation_binding.inc','allocation_operations.inc'):
   shutil.copyfile(HERE/name,out/name)
  lifts_path=BASE/'lifts-r1/report.json';lifts_pins=BASE/'lifts-r1/pins.json'
  assert sha(lifts_path)=='81efe961919c3d4b7c46683aab4158b27f2a043cdcf6f8a4481e2adc07c20963'
  assert sha(lifts_pins)=='bab54b5d018512bef65e1040b8264bf955acf6a967425cb01b1ab8c055ff0f67'
  for p,h in read(lifts_pins)['files'].items():assert sha(p)==h,p
  lifts=read(lifts_path);assert lifts['passed'] and not lifts['native_component_executed'] and lifts['new_guest_objects']==26
  native=lifts['source_bodies'];assert len(native)==13
  writer_path=ROOT/'reports/m4-capture-direct/build-r4/build.json'
  assert sha(writer_path)=='909955901c310e5fcf5eb0713e48a20bf896d13ea335e9d8093dec25ba232e96'
  writer=read(writer_path);assert writer['passed']
  for p,h in writer['sources'].items():assert sha(p)==h,p
  for p,h in writer['objects'].items():assert sha(p)==h,p
  p=out/'composition.cpp';s=p.read_text()
  s=replace(s,'#include "heap_return.hpp"','#include "heap_return.hpp"\n#include "allocation.hpp"')
  s=replace(s,'namespace hr=mw34::m4_crt_heap_return;','namespace hr=mw34::m4_crt_heap_return;\nnamespace al=mw34::m4_crt_allocation;')
  s=replace(s,'#include "heap_return_binding.inc"','#include "heap_return_binding.inc"\n#include "allocation_binding.inc"')
  for line in s.splitlines():
   if not(line.startswith('extern "C"') and 'noexcept(false)' in line and '{' in line):continue
   marker='if(hr::has_authority())'
   if marker in line:
    opening='noexcept(false) {' if 'noexcept(false) {' in line else 'noexcept(false){'
    action=line[line.index(marker)+len(marker):];close=action.index('}')
    action=action[:close+1].replace('hr::','al::')
    s=replace(s,line,line.replace(opening,opening+'if(al::has_authority())'+action,1))
   elif 'return hr::current' in line:s=replace(s,line,line.replace('hr::','al::'))
  extra=''
  for bridge in sorted(set(v for n in native.values() for v in n['bridges'])):
   if re.search(r'\b'+re.escape(bridge)+r'\(',s):continue
   if bridge.endswith('_undefined_8'):extra+='extern "C" unsigned char '+bridge+'()noexcept(false){return al::current(al::owner,0)->undefined();}\n'
   elif bridge.startswith('sub_'):extra+='extern "C" void*'+bridge+'(State*s,unsigned a,void*p)noexcept(false){return al::current(p,a)->called(s,a,p);}\n'
   else:raise ValueError('New unreviewed bridge '+bridge)
  s=replace(s,'#include "main_v2.inc"',extra+'#include "main_v2.inc"');p.write_text(s)
  p=out/'mainargs_binding.inc';s=p.read_text()
  s=replace(s,'hr::Binding heap_return;','hr::Binding heap_return;al::Binding allocation;')
  s=replace(s,'heap_return(context,provider,mode){}','heap_return(context,provider,mode),allocation(context,provider,mode){}')
  s=replace(s,'mainargs_binding->heap_return.start(c);','mainargs_binding->allocation.start(c);mainargs_binding->heap_return.start(c);');p.write_text(s)
  # Main/capture adapter is a fresh source authored for direct strict emission.
  for name in ('main_v2.inc','observations.hpp','capture_adapter.hpp','worker_gate.inc'):
   shutil.copyfile(HERE/name,out/name)
  old_build=read(OLD_BUILD);objects=old_build['entry_objects'];libraries=old_build['libraries']
  assert len(objects)==38 and len(libraries)==2
  for p,h in {**objects,**libraries}.items():assert sha(p)==h,p
  files={str(p.absolute()):sha(p)for p in out.iterdir()if p.is_file()}
  for p in (HERE/'prepare.py',HERE/'allocation.hpp',HERE/'allocation_binding.inc',HERE/'allocation_operations.inc',HERE/'main_v2.inc',HERE/'observations.hpp',HERE/'capture_adapter.hpp',HERE/'worker_gate.inc',accepted,OLD/'pins.json',REC/'report.json',REC/'pins.json',OLD_BUILD,lifts_path,lifts_pins,writer_path,pathlib.Path(sys.executable)):
   files[str(p.absolute())]=sha(p)
  files.update(read(lifts_pins)['files']);files.update(writer['sources']);files.update(writer['objects'])
  files.update(objects);files.update(libraries)
  report=dict(passed=True,scope='Source/build only functional mode1 malloc/free with real API ownership bridge and explicit external research callers; no execution',
   source_bodies=native,reused_guest_objects=38,reused_FDIV_libraries=2,reused_object_hashes=objects,reused_library_hashes=libraries,
   new_guest_objects=26,new_compiled_source_bytes=532,
   new_unique_source_identity_bytes=sum(recovery['spans'][label]['bytes']for _,label in COMPONENTS),
   overlapping_compiled_source_bytes=63,overlapping_entries=[dict(component=a,source_label=b,entry=e,bytes=n)for a,b,e,n in OVERLAPPING],
   State_bytes=3504,FX_bytes=512,CPU_bytes=40,State_reseed_after_writer=False,Runtime_CPU_preserved=True,
   direct_strict_capture_emission=True,flat_capture_tree=False,actual_API_results_injected=False,
   original_attach_executed=False,locale_body_executed=False,parser_body_executed=False,original_executed=False,
   native_component_executed=False,whole_M4_complete=False,commands=commands,literal_lifts_reused=True,lifts_path=str(lifts_path),lifts_sha256=sha(lifts_path),direct_writer_build=str(writer_path),direct_writer_build_sha256=sha(writer_path),recovery_sha256=recovery_sha,baseline_acceptance_sha256=ACCEPT_SHA)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');files[str(out/'report.json')]=sha(out/'report.json')
  (out/'pins.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
  print(json.dumps(dict(passed=True,report_sha256=sha(out/'report.json'),pins_sha256=sha(out/'pins.json'))))
 except Exception:
  (out/'failure.txt').write_text(traceback.format_exc());raise
if __name__=='__main__':main(*sys.argv[1:])
