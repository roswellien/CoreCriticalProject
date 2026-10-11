"""Additive actual Runtime-selected mixed initializer/four-root control fixture, frozen native15."""
from pathlib import Path
import hashlib,json,shutil,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir(parents=True);pins={}
 def pin(p,h=None):
  p=Path(p).resolve();a=sha(p);assert h is None or h==a,(p,h,a);pins[str(p)]=a;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 positive=read(R/'reports/m4-formatting-native/family-fixture-execution-r1/report.json','5ecd8260c6625a589c8e1c517b41c1c7f8deddfbbeb1b61825f6e337c1767297');assert positive['passed']
 build=read(R/'reports/m4-formatting-native/family-fixture-build-r2/build.json','c3c635d084ec22553148f634bdd44d494080a173840fc336fd45304ae4f06c3d')
 p=read(R/'reports/m4-formatting-native/family-fixture-preparation-r1/report.json','cac2b14da823312705f16008a4bba7151c14479364d6a43024fcabe3af5db9d0');parent=Path(build['preparation']).parent
 assert p['native_preparation_sha256']==build['native_preparation_sha256']=='68498a9eaaf924205e11bbf30fbaa355380afc528b892c6739f9a1d199731d06'
 for q,h in(p['sources']|p['files']).items():pin(q,h)
 native=read(p['native_preparation'],p['native_preparation_sha256']);assert native['passed']
 for q,h in native['files'].items():
  if Path(q).parent==Path(p['native_preparation']).parent:pin(q,h)
 for file in ('current_pages.hpp','capture.s'):shutil.copy2(parent/file,out/file)
 template=pin(R/'tools/m4-tree-review/control_fixture.inc');s=template.read_text()
 def one(a,b):
  nonlocal s;assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 one('constexpr unsigned tree_root=0x4b7f70;','constexpr unsigned tree_root=0x4e1ca0;')
 one('need(active_tree_task&&phase==0,"One actual tree before phase");dump(c,*active_tree_task->w,active_tree_task->prefix+"actual-before-root/",active_tree_task->aliases);','need(active_tree_task&&phase<4,"Four actual formatting/mixed before phases");dump(c,*active_tree_task->w,active_tree_task->prefix+"actual-before-root-"+std::to_string(phase)+"/",active_tree_task->aliases);')
 one('need(active_tree_task&&phase==1,"One actual tree after phase");dump(c,*active_tree_task->w,active_tree_task->prefix+"actual-after-root/",active_tree_task->aliases);','need(active_tree_task&&phase>=1&&phase<=4,"Four actual formatting/mixed after phases");dump(c,*active_tree_task->w,active_tree_task->prefix+"actual-after-root-"+std::to_string(phase-1)+"/",active_tree_task->aliases);')
 one('result&&t.completed==1&&sample.tags[10]==7&&sample.tags[11]==7','result&&t.completed==4&&sample.tags[10]==2&&sample.tags[11]==3')
 one('const unsigned header[]{1,18,36,sizeof(Sample),tree_root,3504,40,512,65}','const unsigned header[]{1,10,20,sizeof(Sample),tree_root,3504,40,512,'+str(len(p['current_pages']))+'}')
 one('n<18','n<10');s=s.replace('Tree scenario ','Formatter scenario ').replace('actual tree causal','actual formatter causal').replace('Bounded actual Runtime tree controls passed; full125 acceptance is separate','Bounded actual Runtime formatter controls passed; full130 acceptance is separate')
 one('extern "C" unsigned data_boundary_initialize(void*p)noexcept{','extern "C" unsigned data_boundary_initialize(void*p)noexcept{\n m4_spi_connected::ErrorBoundary outer_error;ni::NumericHostBoundary diagnostic_boundary(0x37f);')
 one('(void)invoke(t);mw34_tree_controls::restore_actual();','Hardware invocation_before{},invocation_after{};hardware(invocation_before);(void)invoke(t);hardware(invocation_after);t.w->append(t.prefix+"actual-invocation-hardware-before.bin",&invocation_before,sizeof(invocation_before));t.w->append(t.prefix+"actual-invocation-hardware-after.bin",&invocation_after,sizeof(invocation_after));need(hardware_equal(invocation_before,invocation_after),"Actual Context invocation preserves caller numerical environment before diagnostics");mw34_tree_controls::restore_actual();')
 one('}catch(...){t.cleanup=0;}','}catch(const std::exception&e){t.w->append(t.prefix+"actual-cleanup-exception.bin",e.what(),std::strlen(e.what()));t.cleanup=0;}catch(...){const char message[]="Nonstandard cleanup exception";t.w->append(t.prefix+"actual-cleanup-exception.bin",message,sizeof(message)-1);t.cleanup=0;}')
 (out/'fixture.cpp').write_text('#define main frozen_connected125_worker_main\n#include "'+(Path(p['connected_include'])/'native_main.cpp').as_posix()+'"\n#undef main\n'+s)
 hooks=pin(R/'tools/m4-tree-review/mixed_control_hooks_v2.hpp');shutil.copy2(hooks,out/'control_hooks.hpp')
 cm=(parent/'CMakeLists.txt').read_text().replace((parent/'fixture.cpp').as_posix(),(out/'fixture.cpp').as_posix()).replace((parent/'capture.obj').as_posix(),(out/'capture.obj').as_posix());(out/'CMakeLists.txt').write_text(cm)
 pin(__file__);files={str(q.resolve()):sha(q)for q in out.iterdir()if q.is_file()}
 p.update(scope='Actual Runtime-selected mixed initializer/four-root causal controls; ten scenarios/twenty attempts per level',passed=True,control_scenarios=10,control_attempts=20,actual_Runtime_selected_call=True,positive_execution_sha256='5ecd8260c6625a589c8e1c517b41c1c7f8deddfbbeb1b61825f6e337c1767297',native_executed=False,initializer_credit=0,sources=pins,files=files)
 (out/'report.json').write_text(json.dumps(p,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
