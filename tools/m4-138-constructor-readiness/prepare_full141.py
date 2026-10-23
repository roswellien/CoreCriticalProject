"""Exact additive full141 Context; prepare only, never read captures or launch."""
from pathlib import Path
import hashlib,json,re,shutil,sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-startup141-runway'/name;assert not out.exists();pins={};deltas=[];relations=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or v==h,str(p);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 parent=R/'reports/m4-joint-startup138/preparation-r4';p=read(parent/'report.json','a392e9d80e88a3779cc37247b681eeea5e3012aa90304564290d5283f7f73a2a')
 fixture=R/'reports/m4-constructor-native/fixture-preparation-r6';f=read(fixture/'report.json','f0dfc1427c9cca0c1b920be6fc030c6b9bb7e53ef631946abcbf4ddf215001a0')
 service=R/'reports/m4-startup141-runway/service-preparation-r1';s=read(service/'report.json','6edf61e7b56bb178a6b1dbbb5a0b647af4099272cb59a80f3e277267c435aade')
 sb=read(R/'reports/m4-startup141-runway/service-build-r1/build.json','f822b1d1ec46933486f7abe1d008c45f6d87d7ee7fdd947511aa0b3462a880f5')
 c=read(Path(f['component_include'])/'report.json',f['component_preparation_sha256'])
 cb=read(R/'reports/m4-constructor-native/build-r5/build.json',f['component_build_sha256'])
 assert all(x['passed']for x in(p,f,s,sb,c,cb))and sb['preparation_sha256']==sha(service/'report.json')
 orderpath=R/'reports/m4-startup141-runway/readiness-r1/selected-order141.json';order=read(orderpath)
 assert len(order)==141 and [v for v in order if v['entry']not in(0x4103f0,0x410440,0x459b40)]==p['selected_order']
 assert [order[i]['entry']for i in(13,14,39)]==[0x4103f0,0x410440,0x459b40]
 # Preserve every existing preparation source byte, then enumerate exact deltas.
 out.mkdir(parents=True)
 for src in parent.rglob('*'):
  if src.is_file()and src.name!='report.json':
   pin(src,p['files'][str(src.resolve())]);dst=out/src.relative_to(parent);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
 def replace(file,before,after):
  q=out/file;text=q.read_text();assert text.count(before)==1,(file,before[:80]);q.write_text(text.replace(before,after,1));deltas.append(dict(file=file,before=before,after=after,occurrences=1))
 proto=(out/'joint_protocol.hpp').read_text();table=re.search(r'constexpr std::array<std::uint32_t,138> entries\{[^}]+\};',proto).group(0)
 replace('joint_protocol.hpp',table,'constexpr std::array<std::uint32_t,141> entries{'+','.join(hex(v['entry'])for v in order)+'};')
 # One canonical union Session declaration; no duplicate local class definitions.
 oldheader=(out/'onexit_session.hpp').read_text();wrapper='#pragma once\n#include "'+str((service/'session.hpp').resolve()).replace('\\','/')+'"\n'
 replace('onexit_session.hpp',oldheader,wrapper);pin(service/'session.hpp',s['files'][str((service/'session.hpp').resolve())])
 h=pin(fixture/'constructor_component.hpp',f['files'][str((fixture/'constructor_component.hpp').resolve())]);header=h.read_text();assert header.count('#include "constructor_session.hpp"')==1
 (out/'constructor_component.hpp').write_text(header.replace('#include "constructor_session.hpp"','#include "onexit_session.hpp"',1))
 replace('native_main.cpp','#include "onexit_session.hpp"','#include "onexit_session.hpp"\n#include "constructor_component.hpp"\n#include "constructor_gate.hpp"\nnamespace cc=mw34::m4_constructor_native;')
 replace('native_main.cpp','static std::vector<MFCOutput>mfc_output;','static std::vector<MFCOutput>mfc_output,constructor_output;\nstatic void constructor_sink(std::string_view name,std::span<const std::byte>b,void*){constructor_output.push_back({std::string(name),{b.begin(),b.end()}});}')
 replace('native_main.cpp','std::unique_ptr<mc::Component>mfc_component_;','std::unique_ptr<mc::Component>mfc_component_;std::unique_ptr<cc::Component>constructor_component_;')
 fixture_code=pin(fixture/'fixture.cpp',f['files'][str((fixture/'fixture.cpp').resolve())]).read_text();constructor=next(line for line in fixture_code.splitlines(True)if line.startswith(' static void constructor_entry('))
 replace('native_main.cpp',' unsigned completed{};',constructor+' unsigned completed{};')
 replace('native_main.cpp',' r_.freeze_registry();',' #include "constructor_bindings.inc"\n r_.freeze_registry();')
 for before,after in [('phase==138&&r_.calls().size()==141&&r_.translation_count()==139','phase==141&&r_.calls().size()==144&&r_.translation_count()==142'),('const unsigned header[]{1,6,138,828,17,sizeof(Native)}','const unsigned header[]{1,6,141,846,17,sizeof(Native)}'),('mfc_output.clear();','mfc_output.clear();constructor_output.clear();'),('records.reserve(138)','records.reserve(141)'),('records.size()==138','records.size()==141'),('seq==6&&total==828','seq==6&&total==846')]:replace('native_main.cpp',before,after)
 replace('native_main.cpp','for(const auto&row:mfc_output)writer.append(prefix+"MFC/"+row.name,row.bytes.data(),row.bytes.size());','for(const auto&row:mfc_output)writer.append(prefix+"MFC/"+row.name,row.bytes.data(),row.bytes.size());\n  for(const auto&row:constructor_output)writer.append(prefix+"Constructors/"+row.name,row.bytes.data(),row.bytes.size());')
 anchor='auto summary=c.registry().summary();w->writer->append(p+"-registry.bin",summary.data(),sizeof(summary));'
 replace('native_main.cpp',anchor,'{std::array<std::byte,4096>b{};c.runtime().memory().read({0x5f2000},b);w->writer->append(p+"-constructor-global5F2000.bin",b.data(),b.size());}'+anchor)
 # Numeric display strings are also exact finite substitutions, not code gates.
 for before,after in [('828native phases in6persistent138-root sequences','846native phases in6persistent141-root sequences'),('Six persistent138-root sequences and source growth/owned cleanup complete','Six persistent141-root sequences and source growth/owned cleanup complete')]:
  if before in(out/'native_main.cpp').read_text():replace('native_main.cpp',before,after)
 cm=(out/'CMakeLists.txt').read_text();assert cm.count('mw34_joint_startup138')>=1
 replace('CMakeLists.txt',cm,cm.replace('mw34_joint_startup138','mw34_joint_startup141').replace('"${MW34_WIDGET_LIBRARY}" bcrypt','"${MW34_WIDGET_LIBRARY}" "${MW34_CONSTRUCTOR_LIBRARY}" bcrypt'))
 libraries={}
 for level in('O0','O2'):
  for n in ['constructor_gate.hpp','constructor_bindings.inc']:
   src=pin(fixture/level/n,f['files'][str((fixture/level/n).resolve())]);shutil.copyfile(src,out/level/n)
  lib=f['levels'][level]['component_library'];pin(lib,f['levels'][level]['component_library_sha256']);libraries[level]=lib
  assert cb['levels'][level]['library']==lib and cb['levels'][level]['library_sha256']==f['levels'][level]['component_library_sha256']
  # All inherited410 COFFs remain exactly same, and existing58widget body library
  # stays the same. Additionalconstructor33IRs live in a separately proven lib.
  for obj in p['objects'][level]:pin(obj,p['files'][obj])
  pin(p['widget_libraries'][level],p['files'][p['widget_libraries'][level]])
 for ir in c['IRs']:pin(ir,c['files'][ir])
 pin(Path(f['component_include'])/'component.cpp',c['files'][str((Path(f['component_include'])/'component.cpp').resolve())])
 # Exact reverse deltas prove all old chronology/state/FP/widget/GDI/cleanup/
 # growth bodies and output code survive unchanged outside declared additions.
 for rel in {d['file']for d in deltas}:
  restored=(out/rel).read_text()
  for d in reversed([x for x in deltas if x['file']==rel]):assert restored.count(d['after'])==1;restored=restored.replace(d['after'],d['before'],1)
  assert restored==(parent/rel).read_text(),rel
 for src in parent.rglob('*'):
  if src.is_file()and src.name!='report.json':
   dst=out/src.relative_to(parent);relations.append(dict(parent=str(src),child=str(dst),sha256_parent=sha(src),sha256_child=sha(dst),whole_bytes_equal=sha(src)==sha(dst)))
 assert {Path(x['child']).relative_to(out).as_posix()for x in relations if not x['whole_bytes_equal']}=={d['file']for d in deltas}
 (out/'selected-order.json').write_text(json.dumps(order,indent=2)+'\n');(out/'full141-source-deltas.json').write_text(json.dumps(deltas,indent=2)+'\n');(out/'source-relations.json').write_text(json.dumps(relations,indent=2)+'\n')
 p.update(scope='Unexecuted exact additive141 singleContext with138old roots preserved,3constructor Component callbacks and one canonical unionSession; independent source/full-link/current domains pending',selected_order=order,source_roots=141,source_sequences=6,selected_phases=846,Runtime_translations=142,Runtime_calls_per_sequence=144,current_registration_callbacks=111,
  parent_preparation=str(parent/'report.json'),parent_preparation_sha256=sha(parent/'report.json'),native_library=str(service/'registry_library.cpp'),native_include=str(service),borrowed_service_preparation=str(service/'report.json'),borrowed_service_preparation_sha256=sha(service/'report.json'),
  constructor_component_preparation=str(Path(f['component_include'])/'report.json'),constructor_component_preparation_sha256=f['component_preparation_sha256'],constructor_libraries=libraries,constructor_IRs=len(c['IRs']),one_canonical_union_Session_header=str(service/'session.hpp'),
  full_parent_source_inverse=True,all138_old_root_IR_COFFER_inputs_unchanged=True,new_constructor_order_phases=[13,14,39],whole_native141_source_original_controls_pending=True,current141_acceptance=False,
  worker_executed=False,native_executed=False,execution_admitted=False,initializer_credit=0)
 for q in out.rglob('*'):
  if q.is_file():pin(q)
 pin(__file__);pin(sys.executable);p['files']=pins
 q=out/'report.json';q.write_text(json.dumps(p,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),deltas=len(deltas),constructor_IRs=len(c['IRs']))))
if __name__=='__main__':main(sys.argv[1])
