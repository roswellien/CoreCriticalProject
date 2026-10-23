"""Independent ordinary source/whole-link prefix review. Never invokes a worker."""
from pathlib import Path
import ast,argparse,collections,hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-138-preresource-root-review'/name;assert not out.exists();out.mkdir();files={};links=[];counts=collections.Counter();passed=False;checks={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.mwi','.zip')and p.name!='transport.json';v=sha(p);assert h is None or h==v,(p,h,v);assert files.setdefault(str(p),v)==v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def blob(p,h=None):return pin(p,h).read_bytes()
 def module(p,name):
  s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 try:
  control_folder=R/'reports/m4-138-preresource-controls/preparation-r3';pr=read(control_folder/'report.json','8a322602c066931f5dd3ced2b9319f6907b0b01413828e2d72dd482c5ce09b2c')
  build=read(R/'reports/m4-138-preresource-controls/build-r4/build.json','9a65633f858e7c06c5ca09a8191a41051321cf2848c1a25b4318bd4c61c08a9f');assert build['passed']and build['preparation_sha256']==sha(control_folder/'report.json')and not build['worker_executed']
  ready=read(R/'reports/m4-138-preresource-controls/readiness-r2/report.json','c8a358beda8a2fdd02aeda33e21aea07cf32f8d9f55b45ae2cbeb6698772df04');assert ready['passed']and ready['no_worker_run']and ready['no_reader_run']
  for report in(pr,build,ready):
   for p,h in report['files'].items():pin(p,h)
  parentbuild=read(pr['parent_build'],pr['parent_build_sha256']);prep=read(pr['parent_preparation'],pr['parent_preparation_sha256']);folder=Path(pr['parent_preparation']).parent
  source=pin(control_folder/'native_main.cpp').read_text();inverse=source
  for d in reversed(pr['parent_main_changes']):assert inverse.count(d['after'])==1;inverse=inverse.replace(d['after'],d['before'])
  assert inverse==pin(folder/'native_main.cpp').read_text()
  controls=pin(control_folder/'controls_main.cpp').read_text();legacy=pin(R/'reports/m4-mfc1168-native/connected-controls-preparation-r6/connected_controls.inc').read_text();start=controls.index(legacy.splitlines()[0]);inverse=controls[start:]
  for d in reversed(pr['legacy_controls_changes']):assert inverse.count(d['after'])==1;inverse=inverse.replace(d['after'],d['before'])
  assert inverse==legacy;assert len(pr['parent_main_changes'])==5 and len(pr['legacy_controls_changes'])==12;checks['complete_source_inverse']=True
  assert 'snapshot(r,c->s_,true);mfc_control_entry(r,c->s_);c->mfc_component_='in source
  for token in('r.cpu().eip==mc::root&&r.cpu().esp==mw34::m4_mixed::frame','std::array<std::byte,64>frame{}','r.memory().read({r.cpu().esp},frame)','put("entry-frame64.bin",frame.data(),frame.size())'):assert token in controls
  checks['exact_real64byte_MFC_entry_frame']=True
  assert 'if(phase>=14)throw'in controls and 'if(phase!=13)return;'in controls and pr['cases']['prefix_completed']==13 and pr['cases']['failed_phase']==13
  assert 'if(p->retry)'in source and 'FaultReason::poisoned'in source and 'retry.completed' in controls
  for token in('State.bin','CPU.bin','FX.bin','memory-index.bin','c.registry().dump','c.control_widget_snapshot','c.control_checkpoint'):assert token in controls
  checks['bounded14prefix_no_reseed']=True;checks['complete_private_and_public_retry_inventory']=True
  for token in('if(widget_component_)widget_component_->context_fault()','if(failed_)widget_component_->context_fault()','widget_component_->cleanup_fonts(hardware)'):assert token in source
  for token in('context.control_cleanup();context.control_checkpoint("cleaned");context.cleanup_widgets()','context.registry().finish()','cleaned/Registry/','!context.registry().live_handle()'):assert token in controls
  checks['current_MFC_and_widget_fault_cleanup']=True
  blockdir=R/'reports/m4-138-preresource-root-review/preparation-r1';blockreceipt=read(blockdir/'report.json','87cc3b370ed52b3fb814ed156bb60b08c4178d5e863c3351403fd5ea465a2056');deltas=read(blockdir/'deltas.json');blocks={}
  for name in('native-inputs.py','native-TLS.py','native-boundary.py','native-linked.py'):
   text=pin(blockdir/name,blockreceipt['files'][str(blockdir/name)]).read_text();inverse=text
   for d in reversed([d for d in deltas if d['file']==name]):assert inverse.count(d['new'])==d['count'];inverse=inverse.replace(d['new'],d['old'])
   assert inverse==pin(R/'reports/m4-138-criteria-frontier/schema-checker-preparation-r7'/name).read_text();ast.parse(text);blocks[name]=text
  C=module(R/'tools/m4-tree-review/amd64_coff.py','prefix_coff');M=module(R/'tools/m4-tree-review/review_mfc1168_native_prelaunch_v4.py','prefix_image');N=module(R/'tools/m4-tree-review/review_hypot_c1_controls_prelaunch_v2.py','prefix_directories')
  lift=read(R/'reports/m4-mfc1168-native/lifts-r2/report.json');env=dict(R=R,pin=pin,read=read,blob=blob,module=module,prep=prep,build=build,folder=folder,C=C,M=M,N=N,lift=lift,re=re,struct=struct,Path=Path,counts=counts,links=links)
  for name in('native-inputs.py','native-TLS.py','native-boundary.py'):exec(compile(blocks[name],str(blockdir/name),'exec'),env)
  for level,w in build['workers'].items():
   relations=w['linked_input_relations'];assert len(relations)==444 and sum(v['reused_whole_bytes']for v in relations)==443
   changed=[v for v in relations if not v['reused_whole_bytes']];assert len(changed)==1 and Path(changed[0]['current']).resolve()==Path(w['object']).resolve()and Path(changed[0]['parent']).name=='native_main.cpp.obj'
   for v in relations:
    pin(v['parent'],v['parent_sha256']);pin(v['current'],v['parent_sha256']if v['reused_whole_bytes']else w['object_sha256'])
    if v['reused_whole_bytes']:assert Path(v['parent']).resolve()==Path(v['current']).resolve()
   bf=Path(w['path']).parent;tokens=re.findall(r'"([^"]+)"|(\S+)',pin(bf/'link.rsp').read_text());linked={str(Path(a or b).resolve()).casefold()for a,b in tokens if (a or b).lower().endswith(('.obj','.lib'))};declared={str(Path(v['current']).resolve()).casefold()for v in relations};absolute={str(Path(a or b).resolve()).casefold()for a,b in tokens if Path(a or b).is_absolute()and(a or b).lower().endswith(('.obj','.lib'))};assert declared<=absolute
   widget_library=R/f'reports/m4-fps-native/connected-component-build-r4/{level}/mw34_widget_native.lib';assert absolute-declared=={str(widget_library.resolve()).casefold()} and len(absolute)==445
   pin(widget_library,build['files'][str(widget_library)]);assert build['files'][str(widget_library)]==parentbuild['files'][str(widget_library)];counts['whole_additional_widget_libraries_reused']+=1
   sdk={a or b for a,b in tokens if not Path(a or b).is_absolute()and(a or b).lower().endswith('.lib')};assert sdk=={'bcrypt.lib','kernel32.lib','user32.lib','gdi32.lib','winspool.lib','shell32.lib','ole32.lib','oleaut32.lib','uuid.lib','comdlg32.lib','advapi32.lib'}
   parentgraph=pin(Path(parentbuild['workers'][level]['path']).parent/'build.ninja').read_text();assert all(name in parentgraph for name in sdk)
   counts['declared_SDK_library_names_inherited']+=len(sdk);linked=absolute
   component=[Path(v['current'])for v in relations if Path(v['current']).name=='connected_component.cpp.obj'];assert len(component)==1
   image=M.AMD64Image(blob(w['path'],w['sha256']));mainobj=pin(w['object'],w['object_sha256']);env.update(level=level,w=w,bf=bf,image=image,linked=linked,component_object_path=component[0],main_object_path=mainobj)
   exec(compile(blocks['native-linked.py'],str(blockdir/'native-linked.py'),'exec'),env)
   sy,se=C.parse(mainobj.read_bytes());current_matches=env['linked_candidates'];TLS=env['TLS_relations'];current_targets={}
   for prefix in('main','?mfc_mutate@@','?mfc_retry_snapshot@@','?mfc_control_entry@@','?cleanup_widgets@Context@','?control_cleanup@Context@','?control_widget_snapshot@Context@'):
    names=[v['name']for v in sy.values()if v['section']>0 and v['type']==32 and (v['name']==prefix if prefix=='main'else v['name'].startswith(prefix))]
    if not names:assert level=='O2'and prefix in('?mfc_control_entry@@','?control_cleanup@Context@','?control_widget_snapshot@Context@');counts['narrow_O2_methods_inlined_into_proven_current_callers']+=1;continue
    assert len(names)==1;raw,rel=C.function(sy,se,names[0]);matches=current_matches(image,raw,rel);assert len(matches)==1,(level,names[0],len(matches));TLS(image,raw,matches[0][1],rel,se);current_targets[names[0]]=matches[0][0];links.append(dict(level=level,symbol=names[0],whole_bytes=len(raw),address=matches[0][0],relocations=len(rel),scope='actual prefix control/caller/cleanup'))
   # Bind static source input/header ownership to actual successful compile,
   # not uncompiled original positive main/growth or runtime TLS claims.
   dependencies={Path(p).resolve()for p in w['compiler_dependencies']};assert control_folder/'native_main.cpp'in dependencies
   commands=[c for c in build['commands']if str(mainobj)in ''.join(c['arguments'])and '-c'in c['arguments']];assert len(commands)==1 and commands[0]['exit_code']==0 and commands[0]['arguments'][-1]==str(control_folder/'controls_main.cpp');pin(commands[0]['arguments'][0]);counts['actual_current_control_compile_commands']+=1
   for p in dependencies:pin(p)
   assert str(control_folder/'native_main.cpp')in pin(R/f'reports/m4-138-preresource-controls/build-r4/{level}-compile.log').read_text()
   counts['whole_linked_control_inputs']+=444;counts['whole_parent_inputs_reused']+=443
  assert counts['whole_current_typed_bridge_functions']==14 and counts['whole_hardware_caller_boundaries']==2
  checks['whole_linked_current_context_and_provider_inputs']=True;checks['typed_COFF_CALL_TLS_ownership']=True;checks['whole85byte_boundary_target_and_unwind']=True
  pin(R/'tools/m4-138-preresource-controls/run_v1.py');pin(R/'tools/m4-138-preresource-controls/run_v2.py');pin(__file__)
  for p,h in tuple(files.items()):assert sha(p)==h
  passed=True
 except Exception:(out/'failure.txt').write_text(traceback.format_exc())
 (out/'links.json').write_text(json.dumps(links,indent=2)+'\n');pin(out/'links.json')
 (out/'report.json').write_text(json.dumps(dict(passed=passed,independent_review=True,scope_identity='current138_preresource_legacy12',ordinary_outputs_only=True,modes=list(range(1,13)),levels=['O0','O2'],prelaunch_checks=checks,counts=dict(counts),source_physical_review_only=True,current12_refusals_proven=False,TLS64_runtime_proven=False,zero_API_resources_proven=False,worker_executed=False,canonical_reader_opened=False,initializer_credit=0,files=files),indent=2)+'\n');print(json.dumps(dict(passed=passed,report=str(out/'report.json'),sha256=sha(out/'report.json'),counts=dict(counts))))
 if not passed:raise SystemExit(1)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('name');main(p.parse_args().name)
