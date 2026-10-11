"""Freeze a linked-worker recipe with accepted CRT services, no execution."""
from pathlib import Path
import hashlib,json,shutil,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def main():
 out=(R/sys.argv[1]).resolve();need(not out.exists(),'Fresh widget fixture preparation');out.mkdir(parents=True);files={}
 def bind(p,h=None):
  p=Path(p);p=p if p.is_absolute()else R/p;p=p.resolve();v=sha(p);need(h is None or h==v,'Exact physical input '+str(p));files[str(p)]=v;return p
 def load(p,h):return json.loads(bind(p,h).read_text())
 component=load('reports/m4-widget-native/preparation-r2/report.json','775828a192f57bf6e8fcf75fe629461402c7b8c367220f76ed9883c76c6f75b8');cb=load('reports/m4-widget-native/build-r4/build.json','ad9d4d5345d01429ff749bfabb9cce1e9cb6ff1d0b87716601083fa1a0c7d56c');services=load('reports/m4-widget-native/service-preparation-r2/report.json','d10b800a817dd3fc684f276d5df19154748b2b0735137d062d9bff05376a1fca')
 parent=load('reports/m4-joint-startup130/build-r2/build.json','1a51ee4bbba62c9505eb1ffae7dee2538cc68297708119a1fa3485769a1cde53');widget=load('reports/m4-widget-source/lifts-r1/report.json',component['files'][str((R/'reports/m4-widget-source/lifts-r1/report.json').resolve())]);remaining=load('reports/m4-remaining-service-source/lifts-r2/report.json','b408ef417766435e082a436a2af6fbbcd3827fd1e30e6503d7d16fc7b1fb3c8e')
 for report in (component,cb,services):
  for p,h in report['files'].items():bind(p,h)
 for p in ['tools/m4-widget-native/fixture.cpp','tools/m4-widget-native/derive_fixture_v2.py','tools/m4-widget-native/fixture_v2.cpp','tools/m4-widget-native/build_fixture.py','tools/m4-widget-native/build_fixture.ps1','tools/m4-widget-native/build_fixture_v2.py','tools/m4-widget-native/build_fixture_v2.ps1','tools/m4-widget-native/derive_fixture_v3.py','tools/m4-widget-native/build_fixture_v3.py','tools/m4-widget-native/build_fixture_v3.ps1','tools/m4-widget-native/derive_fixture_v4.py',Path(__file__).resolve()]:bind(p)
 shutil.copyfile(R/'tools/m4-widget-native/fixture_v2.cpp',out/'fixture.cpp');levels={}
 h=['#pragma once','#include "component.hpp"','struct WidgetBinding {unsigned root,source_size;const char*source_sha256;mw34::m4_runtime::NativeEntry callback;};','inline constexpr std::array<WidgetBinding,6>widget_bindings{{']
 for root in component['roots']:
  key=f'f_{root:x}';row=widget['source_bodies'].get(key,remaining['source_bodies'].get(key));need(row and row['entry']==root,'Exact six literal source root spans');h.append('{%d,%d,"%s",mw34::m4_widget_native::Component::entry_%x},'%(root,row['source_bytes'],row['source_sha256'],root))
 h+=['}};'];(out/'widget_bindings.hpp').write_text('\n'.join(h)+'\n')
 for level in ('O0','O2'):
  literal=[bind(p,parent['sources'][p])for p in parent['workers'][level]['objects']];need(len(literal)==397,'Exact current130 literal COFF inventory')
  core=[bind(p,h)for p,h in parent['artifacts'].items()if p.endswith('.obj')and('build-'+level+'\\CMakeFiles\\mw34_joint_startup130.dir\\')in p and Path(p).name not in ('native_main.cpp.obj','registry_library.cpp.obj')];need(len(core)==28,'Current core excludes only original worker and registry implementation')
  capture=bind('reports/m4-capture-direct/build-r4/capture_direct-'+level+'.obj',parent['sources'][str((R/('reports/m4-capture-direct/build-r4/capture_direct-'+level+'.obj')).resolve())]);preserve=bind('reports/m4-capture-direct/build-r4/preserve.obj',parent['sources'][str((R/'reports/m4-capture-direct/build-r4/preserve.obj').resolve())]);lib=bind(cb['levels'][level]['library'],cb['levels'][level]['library_sha256'])
  forced=bind('reports/m4-joint-startup130/preparation-r2/'+level+'/registry_build_bindings.hpp',parent['sources'][str((R/('reports/m4-joint-startup130/preparation-r2/'+level+'/registry_build_bindings.hpp')).resolve())])
  levels[level]={'objects':[str(p)for p in literal+core+[capture,preserve]],'component_library':str(lib),'component_library_sha256':sha(lib),'forced_registry_header':str(forced),'fixed_objects':427}
 for p in out.iterdir():bind(p)
 report={'passed':True,'scope':'First six registered literal widget Runtime routes with caller-owned accepted source onexit/heap/CS; compile recipe only, no full136/persistent initializer acceptance','component_preparation_sha256':sha(R/'reports/m4-widget-native/preparation-r2/report.json'),'component_build_sha256':sha(R/'reports/m4-widget-native/build-r4/build.json'),'service_preparation_sha256':sha(R/'reports/m4-widget-native/service-preparation-r2/report.json'),'native_library':services['native_library'],'native_include':services['native_include'],'component_include':str(R/'reports/m4-widget-native/preparation-r2'),'parent_include':str(R/'reports/m4-joint-startup130/preparation-r2'),'levels':levels,'files':files,'source_roots':component['roots'],'root_count':6,'literal_bodies':51,'whole_Game_BEFORE_from_own_admitted_PE':True,'authored_current_caller_CPU_initialization':True,'original_CPU_or_GDI_seeds':False,'per_root_State_or_page_seed':False,'AFTER_machine_seed':False,'native_executed':False,'initializer_credit':0}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'report':str(out/'report.json'),'sha256':sha(out/'report.json')}))
if __name__=='__main__':main()
