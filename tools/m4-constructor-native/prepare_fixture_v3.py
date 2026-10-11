"""Prepare one persistent measured 37-root fixture; never launch or read archives."""
from pathlib import Path
import hashlib,json,re,shutil,sys
R=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def main(name):
 out=R/'reports/m4-constructor-native'/name;need(not out.exists(),'Fresh constructor fixture');out.mkdir(parents=True);files={};changes=[]
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'No archive reader');v=sha(p);need(h is None or h==v,'Physical current fixture dependency '+str(p));files[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 joint=R/'reports/m4-joint-startup131/preparation-r1/report.json';j=read(joint,'2985c7af9372ca342ccea8a294d7dd829aba4dffe81eb8ab1ad4a01095ffac25')
 recipe=read(R/'reports/m4-widget-native/fixture-preparation-r16/report.json','58c6d615dfc5c23acf56bd3f62b8635f5647831e623c956154b78986af0e5401')
 comp=R/'reports/m4-constructor-native/preparation-r7/report.json';c=read(comp,'d291ae395b5ee16243f160daba61d360a08142188c84291f4c7458bc86693384')
 build=read(R/'reports/m4-constructor-native/build-r5/build.json','10441be38276c3f199119665eaf2d236726e87597a0bcd3eac77630cf5fbf271')
 service=R/'reports/m4-constructor-native/service-preparation-r4/report.json';sv=read(service,'ccd92f92048563db7fe9de82d694179d5f43bec42b9e4ad32ff733934cbd74e5')
 sb=read(R/'reports/m4-constructor-native/service-build-r4/build.json','3ea775399bf76f6dc32f23f2f2610a73718a03e06c840536a6c1fa4703fd4e3a')
 original=read(R/'reports/m4-constructor-original/chronological-preparation-r10/report.json','22cc8626a26963643e2a56d600c282f128f6db46920353f4e7ac58f81580cefe')
 validation=read(R/'reports/m4-constructor-original/chronological-validation-r3/report.json','00f22911cff2ebde706df7eac235d1621127cb6bd670fd9d680c8478f19b0b95')
 need(all(v['passed']for v in(j,recipe,c,build,sv,sb,validation)),'All compile/original prerequisites passed')
 order=read(R/'reports/m4-constructor-original/chronological-preparation-r10/selected-order.json',original['files'][str((R/'reports/m4-constructor-original/chronological-preparation-r10/selected-order.json').resolve())]);entries=[v['entry']for v in order];need(len(entries)==37 and entries[13:16]==[0x4103f0,0x410440,0x5ae3e4]and entries[36]==0x459b40,'Measured constructor chronology and later third root')
 for p in joint.parent.iterdir():
  if p.is_file()and p.suffix in('.hpp','.inc','.s','.cpp'):
   pin(p,j['files'][str(p.resolve())]);shutil.copyfile(p,out/p.name)
 h=out/'joint_protocol.hpp';s=h.read_text();a=re.search(r'constexpr std::array<std::uint32_t,131> entries\{[^}]+\};',s);need(a is not None,'One fixed selected table');h.write_text(s[:a.start()]+'constexpr std::array<std::uint32_t,37> entries{'+','.join(hex(v)for v in entries)+'};'+s[a.end():])
 (out/'selected-order.json').write_text(json.dumps(order,indent=2)+'\n')
 p=pin(service.parent/'session.hpp',sv['files'][str((service.parent/'session.hpp').resolve())]);shutil.copyfile(p,out/'constructor_session.hpp')
 p=pin(comp.parent/'component.hpp',c['files'][str((comp.parent/'component.hpp').resolve())]);s=p.read_text();need(s.count('#include "session.hpp"')==1,'Constructor header service declaration seam');(out/'constructor_component.hpp').write_text(s.replace('#include "session.hpp"','#include "constructor_session.hpp"',1))
 p=out/'fixture.cpp';s=(out/'native_main.cpp').read_text()
 def change(a,b):
  nonlocal s
  need(s.count(a)==1,'Exact measured fixture source hunk '+a[:90]);s=s.replace(a,b,1);changes.append(dict(before=a,after=b))
 change('#include "onexit_session.hpp"','#include "constructor_session.hpp"\n#include "constructor_component.hpp"\nnamespace cc=mw34::m4_constructor_native;')
 change('static std::vector<MFCOutput>mfc_output;','static std::vector<MFCOutput>mfc_output,constructor_output;\nstatic void constructor_sink(std::string_view name,std::span<const std::byte>b,void*){constructor_output.push_back({std::string(name),{b.begin(),b.end()}});}')
 change('std::unique_ptr<mc::Component>mfc_component_;','std::unique_ptr<mc::Component>mfc_component_;std::unique_ptr<cc::Component>constructor_component_;')
 change(' unsigned completed{};',' static void constructor_entry(m4_runtime::Runtime&r){auto*c=active_context;require(c&&&r==&c->r_&&observation,"Actual borrowed constructor Context source CALL");overlay_cpu(c->s_,r.cpu());snapshot(r,c->s_,true);if(!c->constructor_component_)c->constructor_component_=std::make_unique<cc::Component>(r,*c->registry_,CONSTRUCTOR_COMPONENT_GATE,&constructor_sink,nullptr);cc::HostBoundary hardware;c->constructor_component_->borrow_entry(r.cpu().eip,hardware);constructor_sink("root-"+std::to_string(observation->common.entry)+"/caller-hardware.bin",hardware.bytes,nullptr);sync_fx(r,c->s_);snapshot(r,c->s_,false);observation->state_seeded=r.remill_seeded();}\n unsigned completed{};')
 change(' r_.freeze_registry();',' #include "constructor_bindings.inc"\n r_.freeze_registry();')
 change('phase==131&&r_.calls().size()==134&&r_.translation_count()==132','phase==37&&r_.calls().size()==37&&r_.translation_count()==135')
 change('const unsigned header[]{1,6,131,786,17,sizeof(Native)}','const unsigned header[]{1,6,37,222,17,sizeof(Native)}')
 change('mfc_output.clear();','mfc_output.clear();constructor_output.clear();')
 change('records.reserve(131)','records.reserve(37)')
 change('need(records.size()==131,','need(records.size()==37,')
 change('need(seq==6&&total==786,','need(seq==6&&total==222,')
 change('for(const auto&row:mfc_output)writer.append(prefix+"MFC/"+row.name,row.bytes.data(),row.bytes.size());','for(const auto&row:mfc_output)writer.append(prefix+"MFC/"+row.name,row.bytes.data(),row.bytes.size());\n  for(const auto&row:constructor_output)writer.append(prefix+"Constructors/"+row.name,row.bytes.data(),row.bytes.size());')
 # No selected-source growth replay: cleanup the actually carried native owners.
 change('const auto initial_growth=context.registry().growth_witnesses().size();while(context.registry().growth_witnesses().size()==initial_growth){need(replays<512,"Actual registry growth bounded replay limit");context.registry().replay(registration_roots.front());++replays;}','// Bounded37 cleanup only; no replay, no growth or full144 chronology claim.')
 change('static void image(mw34::m4_mixed::Context&c,unsigned phase,bool after){','static void image(mw34::m4_mixed::Context&c,unsigned phase,bool after){') if False else None
 s=s.replace('786native phases in6persistent131-root sequences','222native phases in6persistent37-root sequences').replace('Six persistent131-root sequences and source growth/owned cleanup complete','Six measured37-root sequences and actual owned cleanup complete')
 # Separately observe the genuine PE global prerequisite page; no BEFORE reseed.
 a='auto summary=c.registry().summary();w->writer->append(p+"-registry.bin",summary.data(),sizeof(summary));'
 change(a,'{std::array<std::byte,4096>b{};c.runtime().memory().read({0x5f2000},b);w->writer->append(p+"-constructor-global5F2000.bin",b.data(),b.size());}'+a)
 p.write_text(s);(out/'source-delta.json').write_text(json.dumps(changes,indent=2)+'\n')
 sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
 game=pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf');pe=PEImage(game.read_bytes());roots=[0x4103f0,0x410440,0x459b40];bindings=[];levels={}
 for root in roots:
  data=pe.data[pe.rva_range(root-pe.image_base,29)[0]:pe.rva_range(root-pe.image_base,29)[0]+29];bindings.append(dict(entry=root,bytes=29,source_sha256=hashlib.sha256(data).hexdigest(),source_hex=data.hex()))
 for level in('O0','O2'):
  dst=out/level;dst.mkdir();rows=[]
  for parent_header in (joint.parent/level).iterdir():
   if parent_header.is_file():pin(parent_header,j['files'][str(parent_header.resolve())]);shutil.copyfile(parent_header,dst/parent_header.name)
  for x in bindings:
   obj=Path(R/f'reports/m4-constructor-native/build-r5/{level}/f_{x["entry"]:x}.obj');pin(obj,build['files'][str(obj.resolve())]);rows.append('r_.register_translation({{%d},{m4_runtime::Abi::Cdecl,0,true},&constructor_entry,"Measured constructor root",{m4_runtime::Domain::admitted_game,m4::admitted_image_hash,29,"%s","%s","%s"}});'%(x['entry'],x['source_sha256'],sha(obj),sha(comp)))
  (dst/'constructor_bindings.inc').write_text('\n'.join(rows)+'\n');(dst/'constructor_gate.hpp').write_text('#define CONSTRUCTOR_COMPONENT_GATE "%s"\n'%sha(comp))
  objects=[]
  for v in j['objects'][level]:
   q=Path(v['path']if isinstance(v,dict)else v);pin(q,j['files'][str(q.resolve())]);objects.append(str(q))
  core=recipe['levels'][level]['objects'][-30:];need(len(core)==30,'Exact current core inventory')
  for v in core:q=pin(v,recipe['files'][str(Path(v).resolve())]);objects.append(str(q))
  need(len(objects)==440 and len(set(objects))==440,'410 physical literals plus30 current core objects')
  for q,hv in [(build['levels'][level]['library'],build['levels'][level]['library_sha256']),(sb['levels'][level]['library'],sb['levels'][level]['library_sha256'])]:pin(q,hv)
  forced=pin(recipe['levels'][level]['forced_registry_header'],recipe['files'][str(Path(recipe['levels'][level]['forced_registry_header']).resolve())])
  levels[level]=dict(objects=objects,component_library=build['levels'][level]['library'],component_library_sha256=build['levels'][level]['library_sha256'],service_library=sb['levels'][level]['library'],service_library_sha256=sb['levels'][level]['library_sha256'],forced_registry_header=str(forced))
 (out/'root-bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
 for p in out.rglob('*'):
  if p.is_file():pin(p)
 pin(__file__);pin(R/'tools/analysis/pe.py')
 d=dict(passed=True,scope='Unexecuted genuine37 chronology native fixture, own PE/loader BEFORE and same Session; equality observations are not machine seeds',levels=levels,parent_include=str(Path(j['parent_preparation']).parent),component_include=str(comp.parent),native_include=str(service.parent),native_library=str(service.parent/'registry_library.cpp'),selected_order=order,source_roots=37,source_sequences=6,selected_phases=222,Runtime_translations=135,Runtime_calls_per_sequence=37,current_callbacks=25,fixed_native_bytes=159716,ordinary_pages=46,constructor_global_page=0x5f2000,original_validation_sha256=sha(R/'reports/m4-constructor-original/chronological-validation-r3/report.json'),component_preparation_sha256=sha(comp),component_build_sha256=sha(R/'reports/m4-constructor-native/build-r5/build.json'),service_preparation_sha256=sha(service),service_build_sha256=sha(R/'reports/m4-constructor-native/service-build-r4/build.json'),source_AFTER_seed=False,per_phase_reseed=False,native_executed=False,initializer_credit=0,whole_literal_source_comparison_pending=True,files=files)
 p=out/'report.json';p.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=True,sha256=sha(p),source_roots=37)))
if __name__=='__main__':main(sys.argv[1])
