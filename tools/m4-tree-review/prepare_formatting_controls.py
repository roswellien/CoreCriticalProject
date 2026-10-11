"""Additive actual Runtime-selected formatter3 control fixture, frozen native15."""
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
 positive=read(R/'reports/m4-formatting-native/fixture-execution-r4/report.json','55ecbdc1a115f73ab046ea92f6e33f5af0020d92a530dbe2a3e145af7d37bba0');assert positive['passed']
 build=read(R/'reports/m4-formatting-native/fixture-build-r7/build.json','f4669c5b495974a1d09c1aca4b35aa8cbeb14a1d9300bd65e612f76a690c3307')
 p=read(R/'reports/m4-formatting-native/fixture-preparation-r6/report.json','573103fc7ead65d28607c8dbe97637d0911572f628205f5812fd91e91089d31a');parent=Path(build['preparation']).parent
 assert p['native_preparation_sha256']==build['native_preparation_sha256']=='bbe18a53a6c8c400f3274e470a28ded84d7c7c45c4fc860cf5e598ed4d5730aa'
 for q,h in(p['sources']|p['files']).items():pin(q,h)
 native=read(p['native_preparation'],p['native_preparation_sha256']);assert native['passed']
 for q,h in native['files'].items():
  if Path(q).parent==Path(p['native_preparation']).parent:pin(q,h)
 for file in ('current_pages.hpp','capture.s'):shutil.copy2(parent/file,out/file)
 template=pin(R/'tools/m4-tree-review/control_fixture.inc');s=template.read_text()
 def one(a,b):
  nonlocal s;assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 one('constexpr unsigned tree_root=0x4b7f70;','constexpr unsigned tree_root=0x4df610;')
 one('need(active_tree_task&&phase==0,"One actual tree before phase");dump(c,*active_tree_task->w,active_tree_task->prefix+"actual-before-root/",active_tree_task->aliases);','need(active_tree_task&&phase<3,"Three actual formatter before phases");dump(c,*active_tree_task->w,active_tree_task->prefix+"actual-before-root-"+std::to_string(phase)+"/",active_tree_task->aliases);')
 one('need(active_tree_task&&phase==1,"One actual tree after phase");dump(c,*active_tree_task->w,active_tree_task->prefix+"actual-after-root/",active_tree_task->aliases);','need(active_tree_task&&phase>=1&&phase<=3,"Three actual formatter after phases");dump(c,*active_tree_task->w,active_tree_task->prefix+"actual-after-root-"+std::to_string(phase-1)+"/",active_tree_task->aliases);')
 one('result&&t.completed==1&&sample.tags[10]==7&&sample.tags[11]==7','result&&t.completed==3&&sample.tags[10]==0&&sample.tags[11]==0')
 one('const unsigned header[]{1,18,36,sizeof(Sample),tree_root,3504,40,512,65}','const unsigned header[]{1,14,28,sizeof(Sample),tree_root,3504,40,512,'+str(len(p['current_pages']))+'}')
 one('n<18','n<14');s=s.replace('Tree scenario ','Formatter scenario ').replace('actual tree causal','actual formatter causal').replace('Bounded actual Runtime tree controls passed; full125 acceptance is separate','Bounded actual Runtime formatter controls passed; full130 acceptance is separate')
 (out/'fixture.cpp').write_text('#define main frozen_connected125_worker_main\n#include "'+(Path(p['connected_include'])/'native_main.cpp').as_posix()+'"\n#undef main\n'+s)
 hooks=pin(R/'tools/m4-tree-review/formatting_control_hooks.hpp');shutil.copy2(hooks,out/'control_hooks.hpp')
 cm=(parent/'CMakeLists.txt').read_text().replace((parent/'fixture.cpp').as_posix(),(out/'fixture.cpp').as_posix()).replace((parent/'capture.obj').as_posix(),(out/'capture.obj').as_posix());(out/'CMakeLists.txt').write_text(cm)
 pin(__file__);files={str(q.resolve()):sha(q)for q in out.iterdir()if q.is_file()}
 p.update(scope='Actual Runtime-selected formatter3 causal controls; fourteen scenarios/twenty-eight attempts per level',passed=True,control_scenarios=14,control_attempts=28,actual_Runtime_selected_call=True,positive_execution_sha256='55ecbdc1a115f73ab046ea92f6e33f5af0020d92a530dbe2a3e145af7d37bba0',native_executed=False,initializer_credit=0,sources=pins,files=files)
 (out/'report.json').write_text(json.dumps(p,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
