"""One persistent131+seven Context in the physical startup-table order.

Compilation recipe only. Current six-case evidence, original chronology,
provider/GDI identity, connected source/refusal and paired acceptance are open.
"""
from pathlib import Path
import hashlib,json,re,shutil,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def one(t,a,b):need(t.count(a)==1,'One exact Context hunk: '+a[:80]);return t.replace(a,b)
def main(name):
 out=R/'reports/m4-joint-startup138'/name;need(not out.exists(),'Fresh joint138 preparation');out.mkdir(parents=True);pins={};generated={};copies=[];passed=False;parent={};selected=[];extra=[];widget_build={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive payload');v=sha(p);need(h is None or h==v,'Exact ordinary input '+str(p));need(str(p)not in pins or pins[str(p)]==v,'Stable input');pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def write(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b if isinstance(b,bytes)else b.encode());generated[str(p.resolve())]=sha(p)
 try:
  pp=pin(R/'reports/m4-joint-startup131/preparation-r1/report.json','2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25');parent=read(pp);need(parent['passed']and parent['source_roots']==131,'Current131 carried Context')
  wp=pin(R/'reports/m4-fps-native/connected-component-preparation-r1/report.json','17bce5443a2253a4af59c258ef54ea0f457deb0bf0b576d737c580d20a9472ae');widget=read(wp);need(widget['passed']and widget['literal_bodies']==58,'Sorted current58 component')
  wb=pin(R/'reports/m4-fps-native/connected-component-build-r1/build.json','602f8a769f74c3883c4bcfe08fbc384c844125f0130c6f2cc184fb41f1670c99');widget_build=read(wb);need(widget_build['passed']and widget_build['preparation_sha256']==sha(wp),'Actual sorted library build')
  sp=pin(R/'reports/m4-fps-native/service-preparation-r2/report.json','d3afbd1f20d9a286a0ae8565554845f897c4d7a051d60110bb64912fa15d77c2');service=read(sp);need(service['passed'],'Actual accepted finite borrowed source service')
  fp=pin(R/'reports/m4-fps-native/fixture-preparation-r2/report.json','bf63967a42e1f35c869ea5e1e0473122d9913f1d03bd68d104c1a63e2aaa04f0');fixture=read(fp);need(fixture['passed'],'Whole own CRT page admission recipe')
  for d in (parent,widget,widget_build,service,fixture):
   for p,h in d['files'].items():pin(p,h)
  for p in pp.parent.rglob('*'):
   if p.is_file()and p.name!='report.json':
    q=out/p.relative_to(pp.parent);raw=pin(p).read_bytes();current=raw.replace(pp.parent.as_posix().encode(),out.as_posix().encode());write(q,current);copies.append(dict(source=str(p.resolve()),target=str(q.resolve()),before_sha256=sha(p),initial_current_sha256=sha(q),path_rebased=raw!=current))
  contract=read(wp.parent/'contracts.json');new_roots=contract['roots'];need([r['root']for r in new_roots]==widget['roots'],'Sorted exact root association')
  selected=sorted(parent['selected_order']+[dict(entry=r['root'],slot=r['slot'])for r in new_roots],key=lambda x:x['slot']);need(len(selected)==138 and len({r['entry']for r in selected})==138,'Exact disjoint138 table rows');need([r for r in selected if r['entry']not in widget['roots']]==parent['selected_order'],'All131 prior rows unchanged')
  phase_map=[]
  for i,row in enumerate(new_roots):
   n=next(j for j,x in enumerate(selected)if x['entry']==row['root']);phase_map.append(dict(root=row['root'],slot=row['slot'],phase=n,component_index=i,source_slice=contract['connected_root_slice_associations'][i]))
  # Keep fixed17 record geometry. Additional pages are typed external records.
  protocol=(out/'joint_protocol.hpp').read_text();fixed=[int(v,16)for v in re.search(r' pages\{([^}]+)',protocol)[1].split(',')]
  reg=(out/'registration_contract.hpp').read_text();old_extra=[int(v,16)for v in re.search(r'registration_pages\{([^}]+)',reg)[1].split(',')]
  original=read(R/'reports/m4-fps-original/preparation-r1/report.json','7c2aea9d60270b768b1c9ecdd63ed7f2898decfa72f5536c43151e7b7e1278a1')
  source_pages=set(original['observed_pages']+original['external_pages'])|set(old_extra)|set(fixed)|{0x7800f000,0x78010000,0x78023000,0x7802e000,0x78037000};extra=sorted(source_pages-set(fixed));need(len(fixed)==17 and len(extra)==52 and len(source_pages)==69,'Whole source inventory union69')
  reg,n=re.subn(r'constexpr std::array<unsigned,29> registration_pages\{[^}]+\};','constexpr std::array<unsigned,52> registration_pages{'+','.join(hex(x)for x in extra)+'};',reg);need(n==1,'Exact added whole source observation pages')
  old_regs=[int(v,16)for v in re.search(r'registration_roots\{([^}]+)',reg)[1].split(',')];new_regs=old_regs+widget['roots'];need(len(new_regs)==108 and len(set(new_regs))==108,'101 plus seven actual callbacks');reg,n=re.subn(r'constexpr std::array<unsigned,101> registration_roots\{[^}]+\};','constexpr std::array<unsigned,108> registration_roots{'+','.join(hex(x)for x in new_regs)+'};',reg);need(n==1,'Exact108 observer callback classification');write(out/'registration_contract.hpp',reg)
  protocol,n=re.subn(r'constexpr std::array<std::uint32_t,131> entries\{[^}]+\};','constexpr std::array<std::uint32_t,138> entries{'+','.join(hex(x['entry'])for x in selected)+'};',protocol);need(n==1,'Physical table-sorted138 selection');write(out/'joint_protocol.hpp',protocol)
  # Runtime evidence is the physical contiguous root span, not gathered CFG rows.
  shutil.copyfile(pin(fp.parent/'widget_bindings.hpp'),out/'widget_bindings.hpp');shutil.copyfile(pin(fp.parent/'Runtime-physical-source-spans.json'),out/'widget-source-spans.json');shutil.copyfile(pin(fp.parent/'provider_pages.hpp'),out/'provider_pages.hpp');shutil.copyfile(pin(fp.parent/'provider-page-contracts.json'),out/'provider-page-contracts.json')
  span_rows=read(out/'widget-source-spans.json');need(len(span_rows)==7 and {x['root']for x in span_rows}==set(widget['roots']),'Seven authentic physical spans')
  # Reuse the successful physical provider mapping implementation verbatim.
  fixture_text=pin(R/'tools/m4-fps-native/fixture_v2.cpp','be1dd1e4745e5b82ebc305c0b17d5eebfffd467aaba13aff90a3ccd315f1e990').read_text();start=fixture_text.index('void map_current_formatter_sources(');end=fixture_text.index('\n} // namespace',start);mapping=fixture_text[start:end]
  mapping=mapping.replace('void map_current_formatter_sources(m4_runtime::Runtime&r,std::span<const std::byte>crt,Writer&w)','void map_current_formatter_sources(m4_runtime::Runtime&r,std::span<const std::byte>crt)');mapping=mapping.replace('need(', 'widget_require(').replace('w.bytes(', 'widget_dump(')
  helper='''#pragma once
#include "component.hpp"
#include "widget_bindings.hpp"
#include "provider_pages.hpp"
namespace W=mw34::m4_widget_native;
struct WidgetOutput{std::string name;std::vector<std::byte>bytes;};
static std::vector<WidgetOutput>widget_output;
static void widget_sink(std::string_view name,std::span<const std::byte>b,void*){widget_output.push_back({std::string(name),{b.begin(),b.end()}});}
static void widget_dump(std::string_view name,const void*p,std::size_t n){widget_sink(name,std::span(static_cast<const std::byte*>(p),n),nullptr);}
static void widget_require(bool b,const char*m){if(!b)throw std::runtime_error(m);}
struct AcceptedWidgetServices final:W::Services {
 mw34::m4_runtime::Runtime&r;mw34::m4_onexit::Session&session;
 AcceptedWidgetServices(mw34::m4_runtime::Runtime&runtime,mw34::m4_onexit::Session&s):r(runtime),session(s){}
 mw34::m4_runtime::Runtime&runtime()noexcept override{return r;}
 void authority()override{const auto v=session.summary();widget_require(&session.runtime()==&r&&v[1]&&!v[3]&&!v[4]&&session.live_handle(),"Actual live persistent accepted registry service context");}
 void cleanup_authority()override{const auto v=session.summary();widget_require(&session.runtime()==&r&&v[1]&&!v[4]&&session.live_handle(),"Actual same Context live registry before manual owned-font cleanup; source work denied after fault");}
 unsigned resolve_import(const W::Import&i)override{authority();widget_require(i.pc==0x5ac11e&&i.slot==0x5bb52c&&i.raw==0x1decb0&&i.projected==0x78004a36,"Exact actual source onexit projection");return i.projected;}
 void invoke(State&s,const W::SourceCall&call)override{authority();widget_require(call.site==0x5ac11e&&call.target==0x78004a36&&call.return_pc==0x5ac124&&!call.tail,"One admitted actual source onexit service");session.borrow_widget_onexit(s,call.root,call.frame,call.return_pc);authority();}
};
''' + mapping + '''
static void widget_whole_checkpoint(mw34::m4_runtime::Runtime&r,std::string_view stem){
 const auto prefix=std::string(stem)+"/";
 widget_dump(prefix+"State.bin",r.remill_state().data(),3504);widget_dump(prefix+"CPU.bin",&r.cpu(),40);widget_dump(prefix+"FX.bin",r.fx().data(),512);
 for(const auto&region:r.image_metadata().mapped_regions){std::vector<std::byte>b(static_cast<std::size_t>(region.size));r.memory().read(region.start,b);widget_dump(prefix+"game-region-"+std::to_string(region.start.value)+".bin",b.data(),b.size());}
 std::array<std::byte,4096>stack{};r.memory().read({0x20001000},stack);widget_dump(prefix+"stack.bin",stack.data(),stack.size());const std::array<unsigned,5>tib{r.fs_base().value,r.fs_load32(0),r.fs_load32(4),r.fs_load32(8),r.fs_load32(0x18)};widget_dump(prefix+"TIB.bin",tib.data(),sizeof(tib));
 for(const auto&p:fps_provider_pages){std::array<std::byte,4096>b{};r.memory().read({p.address},b);widget_dump(prefix+"provider-source-page-"+std::to_string(p.address)+".bin",b.data(),b.size());}
}
'''
  # Helper is outside mw34; exact names qualify inherited memory primitives.
  helper=helper.replace('m4_runtime::','mw34::m4_runtime::').replace('mw34::mw34::','mw34::').replace('m4::sha256','mw34::m4::sha256').replace('MemoryFaultReason::','mw34::MemoryFaultReason::').replace('const MemoryFault&','const mw34::MemoryFault&').replace('Permissions::','mw34::Permissions::').replace('static_cast<Permissions>','static_cast<mw34::Permissions>');write(out/'widget_services.hpp',helper)
  t=(out/'native_main.cpp').read_text();t=one(t,'#include "registration_contract.hpp"','#include "registration_contract.hpp"\n#include "widget_services.hpp"')
  t=one(t,'std::unique_ptr<m4_onexit::Session>registry_;','std::unique_ptr<m4_onexit::Session>registry_;std::span<const std::byte>widget_crt_;std::unique_ptr<AcceptedWidgetServices>widget_services_;std::unique_ptr<W::Component>widget_component_;bool widget_cleaned_{};')
  t=one(t,'admitted_cw_(static_cast<std::uint16_t>(cw)){','widget_crt_(crt),admitted_cw_(static_cast<std::uint16_t>(cw)){')
  callback=''' static void widget_entry(m4_runtime::Runtime&r){auto*c=active_context;require(c&&&r==&c->r_&&observation&&c->widget_component_,"Actual same carried Widget Context/Runtime");overlay_cpu(c->s_,r.cpu());snapshot(r,c->s_,true);widget_whole_checkpoint(r,"root-"+std::to_string(r.cpu().eip)+"/carried-before");bool routed{};for(const auto&b:widget_bindings)if(b.root==r.cpu().eip){b.callback(r);routed=true;break;}require(routed,"Exact one prepared widget binding");sync_fx(r,c->s_);snapshot(r,c->s_,false);widget_whole_checkpoint(r,"root-"+std::to_string(observation->common.entry)+"/carried-after");observation->state_seeded=r.remill_seeded();}
 void setup_widgets(){require(!widget_component_,"One persistent widget owner per Context");map_current_formatter_sources(r_,widget_crt_);widget_services_=std::make_unique<AcceptedWidgetServices>(r_,*registry_);W::Inputs input;input.before_domain_gate_sha256=widget_component_gate;const std::array<unsigned,7>pcs{0x5a013c,0x5a063f,0x5a074b,0x517287,0x5ac11e,0x5ac580,0x5a2f68},slots{0x5bb070,0x5bb074,0x5bb068,0x5bb064,0x5bb52c,0x5bb530,0x5bb53c},targets{0x71f00010,0x71f00020,0x71f00030,0,0x78004a36,0,0x780230dd};for(unsigned k=0;k<7;++k){const auto raw=r_.memory().load<unsigned>({slots[k]});input.imports[k]={pcs[k],slots[k],raw,targets[k]?targets[k]:raw};}widget_component_=std::make_unique<W::Component>(r_,*widget_services_,input,&widget_sink,nullptr);}
'''
  t=one(t,' unsigned completed{};',callback+' unsigned completed{};')
  t=one(t,' r_.freeze_registry();',' for(const auto&b:widget_bindings)r_.register_translation({{b.root},{m4_runtime::Abi::Cdecl,0,true},&widget_entry,"Carried widget/FPS initializer",{m4_runtime::Domain::admitted_game,m4::admitted_image_hash,b.source_size,b.source_sha256,widget_library_sha,widget_component_gate}});\n r_.freeze_registry();')
  t=one(t,'registry_->bootstrap();if(before_projection)','registry_->bootstrap();setup_widgets();if(before_projection)')
  t=one(t,'phase==131&&r_.calls().size()==134&&r_.translation_count()==132','phase==138&&r_.calls().size()==141&&r_.translation_count()==139')
  t=one(t,'observation=nullptr;failed_=true;if(!first_.kind)','observation=nullptr;failed_=true;if(widget_component_)widget_component_->context_fault();if(!first_.kind)')
  t=one(t,' void snapshot_numeric(Native&record){',' void cleanup_widgets(){require(widget_component_&&!widget_cleaned_,"One actual widget cleanup before registry teardown");if(failed_)widget_component_->context_fault();W::HostBoundary hardware{};widget_component_->cleanup_fonts(hardware);widget_dump("font-cleanup-caller-hardware.bin",&hardware,sizeof(hardware));widget_whole_checkpoint(r_,"font-cleaned-current");widget_cleaned_=true;}\n void snapshot_numeric(Native&record){')
  t=t.replace('records.reserve(131)','records.reserve(138)').replace('records.size()==131','records.size()==138').replace('seq==6&&total==786','seq==6&&total==828').replace('1,6,131,786,17,sizeof(Native)','1,6,138,828,17,sizeof(Native)').replace('mfc_output.clear();','mfc_output.clear();widget_output.clear();')
  oldfailure='if(!ok){const std::string reason=context.failure_reason()[0]?context.failure_reason():sf.reason?sf.reason:"Connected130 invocation refused";writer.append("FAILURE.txt",reason.data(),reason.size());writer.finish();throw std::runtime_error(reason);}'
  newfailure='if(!ok){const std::string reason=context.failure_reason()[0]?context.failure_reason():sf.reason?sf.reason:"Connected138 invocation refused";writer.append("FAILURE.txt",reason.data(),reason.size());try{context.cleanup_widgets();context.registry().finish();}catch(const std::exception&e){writer.append("CLEANUP-FAILURE.txt",e.what(),std::strlen(e.what()));}for(const auto&row:widget_output)writer.append(prefix+"Widget/"+row.name,row.bytes.data(),row.bytes.size());direct.prefix=prefix+"failed-cleaned/";context.registry().dump(&DirectPhaseWriter::sink,&direct);writer.finish();throw std::runtime_error(reason);}'
  t=one(t,oldfailure,newfailure)
  t=one(t,'  // Genuine source root replay is a separate growth experiment, outside selected-table credit.','  context.cleanup_widgets();for(const auto&row:widget_output)writer.append(prefix+"Widget/"+row.name,row.bytes.data(),row.bytes.size());\n  // Genuine source root replay is a separate growth experiment, outside selected-table credit.')
  t=t.replace('Six persistent131-root sequences','Six persistent138-root sequences').replace('786native phases in6persistent131-root sequences','828native phases in6persistent138-root sequences');write(out/'native_main.cpp',t)
  cmake=(out/'CMakeLists.txt').read_text().replace('mw34_joint_startup131','mw34_joint_startup138');cmake=one(cmake,'target_link_libraries(mw34_joint_startup138 PRIVATE bcrypt user32)','target_include_directories(mw34_joint_startup138 PRIVATE "${MW34_WIDGET_INCLUDE}")\ntarget_link_libraries(mw34_joint_startup138 PRIVATE "${MW34_WIDGET_LIBRARY}" bcrypt user32)');write(out/'CMakeLists.txt',cmake)
  for level in ('O0','O2'):
   lib=pin(widget_build['levels'][level]['library'],widget_build['levels'][level]['library_sha256']);h='#pragma once\ninline constexpr const char*widget_component_gate="'+sha(wp)+'";\ninline constexpr const char*widget_library_sha="'+sha(lib)+'";\n';write(out/level/'widget_build_bindings.hpp',h)
  t=(out/'native_main.cpp').read_text();t=one(t,'#include "widget_services.hpp"','#include "widget_services.hpp"\n#include "widget_build_bindings.hpp"');write(out/'native_main.cpp',t)
  write(out/'selected-order.json',json.dumps(selected,indent=2)+'\n');write(out/'widget-phase-map.json',json.dumps(phase_map,indent=2)+'\n');write(out/'source-page-union.json',json.dumps(dict(fixed=fixed,extra=extra,union=sorted(source_pages)),indent=2)+'\n')
  integration=dict(selected_roots=138,sequences=6,phases_per_level=828,Runtime_translations=139,Runtime_calls_per_selected_sequence=141,registration_callbacks=108,parent_literal_objects=410,widget_literal_objects=58,total_literal_objects=468,one_persistent_Runtime=True,one_persistent_State=True,one_registry_Session=True,component_initialized_after_actual_registry_bootstrap=True,current_actual_CW_TOP_carried=True,external_authored_caller_projection_only_once=True,per_root_reseed=False,full_game_memory_shared_without_reconstruction=True,stack_shared_without_reconstruction=True,component_fault_mark_precedes_manual_font_cleanup=True,manual_font_cleanup_precedes_registry_growth_and_cleanup=True,Native_bytes=159716,Sequence_bytes=147400,fixed_source_pages=17,external_source_pages=52,whole_source_page_union=69,widget_phase_map=phase_map,initializer_credit=0,required_fresh=['Genuine original138 table order and six CW/TOP domains','Whole source/provider/typed GDI identity and resource lifetimes','Whole connected caller hardware and exact changed Context refusal/retries','Fresh paired138 and accepted physical union'])
  write(out/'integration-contracts.json',json.dumps(integration,indent=2)+'\n')
  for p in out.rglob('*'):
   if p.is_file():pin(p)
  pin(__file__);pin(sys.executable);passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(parent);report.update(passed=passed,scope='Unexecuted single carried138 Context: current131 plus seven table-sorted widgets/FPS, one registry/Runtime/State, explicit component Context-fault/owned-font cleanup boundary, whole69 source-page observation inventory',selected_order=selected,source_roots=138,source_sequences=6,current_registration_callbacks=108,Runtime_translations=139,Runtime_calls_per_selected_sequence=141,literal_objects_per_level=468,widget_component_include=str(R/'reports/m4-fps-native/connected-component-preparation-r1'),widget_libraries={k:v['library']for k,v in widget_build.get('levels',{}).items()},native_library=str(R/'reports/m4-fps-native/service-preparation-r2/registry_library.cpp'),native_include=str(R/'reports/m4-fps-native/service-preparation-r2'),parent_current131_preparation_sha256='2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25',prior_copy_relations=copies,generated_sources=generated,files=pins,capture_archive_reader_opened=False,worker_executed=False,execution_admitted=False,initializer_credit=0,current131_acceptance=False,current138_acceptance=False,pending_fresh_original138=True,pending_current_Context_refusals=True)
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q))))
if __name__=='__main__':main(sys.argv[1])
