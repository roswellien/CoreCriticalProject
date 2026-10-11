"""Bounded linked-input map for an independent138 machine/source review."""
from pathlib import Path
import hashlib,json,re,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(name):
 out=R/'reports/m4-joint-startup138'/name;assert not out.exists();out.mkdir();files={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or v==h;assert str(p)not in files or files[str(p)]==v;files[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 bp=pin(R/'reports/m4-joint-startup138/build-r3/build.json','b4cbd387ba718b52a900c5ff527749829f1936706c1b49c9e3a79a9765042ab6');build=read(bp);prep=read(build['preparation'],build['preparation_sha256']);assert build['passed']and prep['passed']
 wp=pin(R/'reports/m4-fps-native/connected-component-preparation-r1/report.json','17bce5443a2253a4af59c258ef54ea0f457deb0bf0b576d737c580d20a9472ae');widget=read(wp);wb=read(R/'reports/m4-fps-native/connected-component-build-r1/build.json','602f8a769f74c3883c4bcfe08fbc384c844125f0130c6f2cc184fb41f1670c99')
 for p,h in build['files'].items():pin(p,h)
 rootdir=Path(build['preparation']).parent;phase_map=read(rootdir/'widget-phase-map.json');page_map=read(rootdir/'source-page-union.json');services=read(R/'reports/m4-fps-native/service-preparation-r2/report.json','d3afbd1f20d9a286a0ae8565554845f897c4d7a051d60110bb64912fa15d77c2')
 levels={}
 for level,w in build['workers'].items():
  tree=Path(w['path']).parent;objects=[str(pin(p))for p in tree.rglob('*.obj')];widget_objects=[dict(path=str(pin(x['path'],x['sha256'])),sha256=x['sha256'])for x in wb['levels'][level]['objects']];literal=[str(pin(x))for x in prep['objects'][level]];assert len(literal)==410 and len(widget_objects)==60
  levels[level]=dict(worker=w['path'],worker_sha256=w['sha256'],actual_CMake_objects=objects,parent_literal_objects=literal,widget_library=wb['levels'][level]['library'],widget_library_sha256=wb['levels'][level]['library_sha256'],widget_objects=widget_objects,actual_compiler_headers=w['compiler_dependencies'],forced_registry_header=str(rootdir/level/'registry_build_bindings.hpp'),widget_binding_header=str(rootdir/level/'widget_build_bindings.hpp'))
 changes=read(rootdir/'integration-contracts.json');pin(__file__);pin(sys.executable)
 report=dict(passed=True,scope='Static current138 input/symbol map only; independent whole-linked machine attribution and fresh source/domain/runtime proofs pending',preparation_path=build['preparation'],preparation_sha256=build['preparation_sha256'],build_path=str(bp),build_sha256=sha(bp),component_preparation=str(wp),component_preparation_sha256=sha(wp),component_build_sha256='602f8a769f74c3883c4bcfe08fbc384c844125f0130c6f2cc184fb41f1670c99',primary_source=str(rootdir/'native_main.cpp'),helper_source=str(rootdir/'widget_services.hpp'),component_source=str(wp.parent/'component.cpp'),primary_source_symbols=['main','mw34::m4_mixed::Context::Context','mw34::m4_mixed::Context::widget_entry','mw34::m4_mixed::Context::setup_widgets','mw34::m4_mixed::Context::invoke_selected_body','mw34::m4_mixed::Context::cleanup_widgets','AcceptedWidgetServices::authority','AcceptedWidgetServices::cleanup_authority','AcceptedWidgetServices::invoke','map_current_formatter_sources','widget_whole_checkpoint'],component_source_symbols=['mw34::m4_widget_native::Component::Impl::invoke','mw34::m4_widget_native::Component::Impl::cleanup','mw34::m4_widget_native::Component::context_fault','mw34::m4_widget_native::entry','mw34_widget_native_api','mw34_widget_hardware_call'],named_Runtime_binding_callback='mw34::m4_mixed::Context::widget_entry',root_phase_map=phase_map,source_page_map=page_map,integration=changes,levels=levels,source_service=services['native_library'],manual_cleanup_scope='Actual same-thread owned native fonts; separate Context fault mark; before still-live source registry teardown; shutdown callbacks remain unexecuted',source_service_scope='Exact borrowed committed CALL5AC11E→78004A36/frame/Callback domain in same live Session; no host_onexit',nonREL32_relocation_review_pending=True,initializer_credit=0,writer_executed=False,capture_archive_reader_opened=False,files=files)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
