"""Review the exact negative Context delta and reattribute its whole linked code."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_joint138_prelaunch_v10.py')
scope={'__file__':str(p),'__name__':'materialize_controls_physical_core'}
exec(compile(p.read_text(),str(p),'exec'),scope)
t=scope['t']
start=t.index("  folder=R/'reports/m4-joint-startup138/preparation-r4'")
end=t.index("  C=load(R/'tools/m4-tree-review/amd64_coff.py'",start)
intro=r'''  folder=R/'reports/m4-joint-startup138/controls-preparation-r4'
  p=read(folder/'report.json',PH);b=read(R/'reports/m4-joint-startup138/controls-build-r2/build.json',BH)
  a=read(R/'reports/m4-joint-startup138/controls-admission-map-r2/report.json','11e658eabca320ae58b27df96a32a28148344adc8263cfb8972c5f5c14eaa5d9')
  positive=read(R/'reports/m4-tree-review/joint138-prelaunch-r10/report.json','cede59b7c9b77ab98b78da72374938775b3c78ec3e9a737f618bd688873e3325')
  checker=read(R/'reports/m4-widget-growth-review/context-checker-source-review-r2/report.json','e92f5b0d1e3725aff88bd7f1677157d3abd88aed21ae99554f8e2e461fa47028')
  parent=read(R/'reports/m4-joint-startup131/preparation-r1/report.json','2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25')
  assert b['preparation_sha256']==PH and a['build_sha256']==BH and a['preparation_sha256']==PH
  assert p['control_modes']==8 and p['control_target']==0x5a3ff0 and p['control_phase']==p['completed_prefix_roots']==135
  assert p['owned_font_prefix_root']==0x5a3c30 and p['owned_font_prefix_phase']==134
  assert p['source_owned_font_create_calls']==15 and p['source_GDI_calls_before_fault']==149
  assert p['borrowed_service_preparation_sha256']=='cb0e8aaffe9ed7320113b1c1b18d2d3615e38d84eb16a51fcec3bdc4018385f9'
  assert p['widget_component_preparation_sha256']=='c9618af8d3c4f947bf56defe2b928dfac9cb08b87fa287f90b78f05b641a9b21'
  assert p['widget_component_build_sha256']=='d7e4d35fe95f7524d2c9a059e115de674d74752fc557d31400e70d319f1fa119'
  cur=pin(folder/'native_main.cpp').read_text();old=pin(R/'reports/m4-joint-startup138/preparation-r4/native_main.cpp').read_text()
  route='if(c->control_route_override)W::Component::entry_40e250(r);else b.callback(r);'
  assert cur.count(route)==1
  reduced=cur.replace(route,'b.callback(r);')
  additions=[line for line in reduced.splitlines(True)if line.startswith((' unsigned control_route_override{};',' void control_snapshot('))]
  assert len(additions)==2
  snapshot=next(line for line in additions if line.startswith(' void control_snapshot('))
  for token in ['widget_component_&&registry_->live_handle()','widget_component_->checkpoint(stem);widget_whole_checkpoint(r_,stem);','const auto f=first_;','r_.poisoned()','for(const auto&c:r_.calls())','widget_dump(std::string(stem)+"/routes.bin",routes.data(),routes.size()*sizeof(routes[0]));']:
   assert token in snapshot,token
  assert all(token not in snapshot for token in ['store<','protect(','seed(','r_.cpu()='])
  for line in additions:reduced=once(reduced,line,'')
  assert reduced==old,'Whole positive138 retained outside one explicit wrong-route fault seam and observational accessors'
  counts['whole_positive_Context_inversion']=1
  controls=pin(folder/'controls_main.cpp').read_text()
  for token in ['#define main mw34_context_controls_unused_positive_main','#include "native_main.cpp"','if(phase!=135)return','c.completed==135','const std::array<unsigned,9>cause{1,mode,phase,0x5a3ff0','mode>=1&&mode<=8','cause.injected&&!task.completed&&task.error.empty()','context.runtime().poisoned()','context.completed==135&&records.size()==135','first==context.failure_reason()','p->context->cleanup_widgets();p->context->registry().finish();','cleanup.completed&&cleanup.error.empty()&&!context.registry().live_handle()','records.reserve(136)']:
   assert token in controls,token
  for mode in range(1,9):assert controls.count('if(mode=='+str(mode)+')')==1
  for token in ['address=0x5bb52c','address=0x5a3ff0','address=0x736130','address=region=0x20001000','address=region=r.fs_base().value','c.control_route_override=1','s.addr.ds_base.dword=after','s.aflag.df=1']:
   assert token in controls,token
  assert controls.count('context_controls_hardware_call(&')==3
  assert 'execute('not in controls and 'seed('not in controls
  # Sources with all seven borrowed service registrations and GDI identity
  # observations remain the exact previously reviewed physical component.
  assert pin(a['component_source']).read_bytes()==pin(R/'reports/m4-fps-native/connected-component-preparation-r4/component.cpp').read_bytes()
  helper=pin(folder/'widget_services.hpp').read_bytes()
  assert helper==pin(R/'reports/m4-joint-startup138/preparation-r4/widget_services.hpp').read_bytes()
  selected=p['selected_order'];newroots=[x['root']for x in a['root_phase_map']]
  assert len(selected)==138 and len(newroots)==7 and [x for x in selected if x['entry']not in newroots]==parent['selected_order']
  S=load(R/'tools/analysis/pe.py','controls138_source_pe');game=S.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  for x in selected:assert struct.unpack('<I',game.read_va(x['slot'],4))[0]==x['entry'];counts['physical_sorted_initializer_slots']+=1
'''
t=t[:start]+intro+t[end:]
def change(a,b):
 global t
 assert a in t,a
 t=t.replace(a,b)
change("PH='a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a'","PH='f413ea66cb259ecebf8bf76024113a0410fe5883304fa10af9a442b291c1b07e'")
change("BH='7ca7a8a0a1f16513c5579890a2d71aab7a882016459b072669e9ab4f9922db47'","BH='e064098f58982c7c6115e43f0ebf14a39eb1ae68f4162225c48c10c70b2f1bf6'")
change('build-r5/connected_hardware_boundary.obj','controls-build-r2/connected_hardware_boundary.obj')
change("q.name=='native_main.cpp.obj'","q.name=='controls_main.cpp.obj'")
change("'mfc_connected_hardware_call'","'mfc_connected_hardware_call','context_controls_hardware_call'")
change("'mw34_widget_invoke_guarded')","'mw34_widget_invoke_guarded','context_controls_guarded')")
change("n=='main'or '@Context@","n in ('main','mw34_context_controls_unused_positive_main')or '@context_control@@'in n and not n.startswith('??$')or '@Context@")
change('build mw34_joint_startup138.exe:','build mw34_widget_context_controls.exe:')
change(': CXX_EXECUTABLE_LINKER__mw34_joint_startup138_Release ',': CXX_EXECUTABLE_LINKER__mw34_widget_context_controls_Release ')
change("  pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v9.py');","  pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v10.py');pin(R/'tools/m4-tree-review/review_joint138_prelaunch_v9.py');")
change('Independent sorted138 single Context source delta and complete current selected function/target/TLS/static-library/compiler-input physical admission; only bounded native observation authorized','Independent exact controls4 Context inversion, eight concrete fault recipes and complete current selected function/target/TLS/ASM/library/compiler-input physical admission; only bounded negative observations authorized')
exec(compile(t,str(Path(__file__)),'exec'),globals())
