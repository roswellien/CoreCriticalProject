"""Freeze an isolated tree Context over accepted124 source and new literal COFFs."""
from pathlib import Path
import hashlib, importlib.util, json, re, shutil, struct, sys
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]

def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()

def need(v,s):
 if not v:raise ValueError(s)

def main(native_path,digest,name):
 out=R/'reports/m4-tree-review'/name;need(not out.exists(),'Fresh isolated fixture preparation');out.mkdir(parents=True)
 pins={}
 def pin(p,h=None):
  p=Path(p).resolve();a=sha(p);need(h is None or a==h,'Exact fixture input '+str(p));pins[str(p)]=a;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 parent=R/'reports/m4-joint-startup124/preparation-r5';prior=read(parent/'report.json','7a2e383ab47bdb668e56181cdc3eec1c75ebf03437e5f9b9ac675861370a85c7')
 accepted=read(R/'reports/m4-joint-startup124-root/acceptance-r1/report.json','6bd35e55bca15e1a0537044bf59a1c3ced5e9ef8b30a8a169b71c78824811462')
 need(accepted['passed'],'Accepted124 base')
 npath=Path(native_path).resolve();native=read(npath,digest);nprep=npath.parent
 need(native['passed'] and not native['native_executed'],'Unexecuted explicit current native source preparation')
 for p,h in native['files'].items():
  if Path(p).resolve().parent==nprep:pin(p,h)
 lifts=read(native['source_lifts'],native['source_lifts_sha256'])
 need(lifts['passed'] and lifts['State_bytes']==3504 and lifts['FX_bytes']==512 and lifts['CPU_bytes']==40,'Exact new source COFF ABI')
 derived=out/'connected'
 derived.mkdir()
 for directory in ('derived','ancestors','O0','O2'):
  shutil.copytree(parent/directory,derived/directory)
 for p in parent.iterdir():
  if p.is_file() and p.suffix in ('.cpp','.hpp','.inc'):
   shutil.copy2(p,derived/p.name)
 shutil.copy2(parent/'CMakeLists.txt',derived/'CMakeLists.txt')
 for p,h in prior['generated_sources'].items():pin(p,h)
 contract=derived/'registration_contract.hpp';s=contract.read_text();needle='std::array<unsigned,96> registration_roots{';need(s.count(needle)==1,'Exact prior96 registration declarations')
 s=s.replace(needle,'std::array<unsigned,97> registration_roots{').replace('0x500660,0x5968f0};','0x500660,0x5968f0,0x4b7f70};')
 need(s.count('0x4b7f70')==1,'One new root declaration');contract.write_text(s,encoding='utf-8')
 # Keep packed Common/Native layout untouched. Only isolate the selected table
 # inventory and the final measured dispatcher accounting for this fixture.
 proto=derived/'joint_protocol.hpp';s=proto.read_text()
 s,n=re.subn(r'constexpr std::array<std::uint32_t,124> entries\{[^\n]+\};',
             'constexpr std::array<std::uint32_t,1> entries{0x4b7f70};',s)
 need(n==1,'Exact selected-table filter');proto.write_text(s,encoding='utf-8')
 main_cpp=derived/'native_main.cpp';s=main_cpp.read_text()
 old='phase==124&&r_.calls().size()==127&&r_.translation_count()==125'
 need(s.count(old)==1,'Exact connected dispatcher extent assertion')
 s=s.replace(old,'phase==1&&r_.calls().size()==1&&r_.translation_count()==126')
 main_cpp.write_text(s,encoding='utf-8')
 spec=importlib.util.spec_from_file_location('tree_fixture_pe',pin(R/'tools/analysis/pe.py'));mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 image=mod.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
 extent=0x4B7F9E-0x4B7F70;code=image.read(image.rva_range(0x4B7F70-image.image_base,extent)[0],extent);code_sha=hashlib.sha256(code).hexdigest()
 root=next(r for r in lifts['dispatch_manifest']if r['entry']==0x4B7F70)
 objects={}
 for level in ('O0','O2'):
  appended=[]
  for row in lifts['dispatch_manifest']:
   obj=row['objects'][level];pin(obj['path'],obj['sha256']);appended.append(obj['path'])
  objects[level]=prior['objects'][level]+appended
  need(len(objects[level])==371 and len(set(objects[level]))==371,'363 inherited and8 distinct new literal objects')
  for obj in prior['objects'][level]:pin(obj)
  p=derived/level/'registration_bindings.inc'
  s=p.read_text();need('0x4b7f70'not in s,'New root absent from accepted bindings')
  s+=f'\nr_.register_translation({{{{0x4b7f70}},{{m4_runtime::Abi::Cdecl,0,true}},&registration_entry,"Isolated literal tree root",{{m4_runtime::Domain::admitted_game,m4::admitted_image_hash,{extent},"{code_sha}","{root["objects"][level]["sha256"]}","{sha(native["source_lifts"])}"}}}});\n'
  p.write_text(s,encoding='utf-8')
 pages=sorted(set(map(int,native['source_pages']))|set(native['game_pages'])|{0x5c8000,0x5c9000,0x5cb000,0x5cc000,0x5e0000,0x5e1000,0x5e8000,0x604000,0x605000,0x60b000,0x20001000,0x5bb000,0x780c1000,0x78115000,0x5e6000,0x608000,0x482000,0x20000000})
 # The root harness counts43 ordinary pages and one separately carried lower
 # stack page; report both instead of dropping the authentic lower stack.
 need(len(pages)==65,'Complete43 ordinary21 source plus lower')
 (out/'current_pages.hpp').write_text('#pragma once\nnamespace mw34_tree_fixture {inline constexpr std::array<unsigned,'+str(len(pages))+'>current_pages{'+','.join(hex(x)for x in pages)+'};}\n')
 fixture=pin(R/'tools/m4-tree-review/control_fixture.inc');pin(R/'tools/m4-tree-review/prepare_fixture.py');pin(R/'tools/m4-tree-review/prepare_controls.py');pin(R/'tools/m4-tree-review/control_hooks.hpp');hooks=pin(R/'tools/m4-tree-review/control_hooks_v2.hpp');shutil.copy2(hooks,out/'control_hooks.hpp')
 (out/'fixture.cpp').write_text('#define main frozen_connected124_worker_main\n#include "'+(derived/'native_main.cpp').as_posix()+'"\n#undef main\n'+fixture.read_text(),encoding='utf-8')
 capture=pin(R/'tools/m4-crt-allocation/capture.s');s=capture.read_text();anchor='  movdqu 256(%r9), %xmm6';need(s.count(anchor)==1,'Exact caller capture source')
 (out/'capture.s').write_text(s.replace(anchor,'  fxrstor64 (%r9)\n  fldenv 512(%r9)\n'+anchor),encoding='utf-8')
 cm=(derived/'CMakeLists.txt').read_text();anchor='"${MW34_PREP}/native_main.cpp"';need(cm.count(anchor)==1,'Exact frozen worker source anchor')
 cm=cm.replace(anchor,'"'+(out/'fixture.cpp').as_posix()+'"');anchor='${MW34_OBJECTS} "${MW34_WRITER}"';need(cm.count(anchor)==1,'Exact frozen literal link anchor')
 cm=cm.replace(anchor,'${MW34_OBJECTS} "'+(out/'capture.obj').as_posix()+'" "${MW34_WRITER}"')
 (out/'CMakeLists.txt').write_text(cm,encoding='utf-8')
 pin(__file__)
 files={str(p.resolve()):sha(p)for p in out.rglob('*')if p.is_file()}
 report=dict(passed=True,scope='Isolated actual Runtime-selected tree causal controls preparation;18 scenarios36 attempts; no125 credit',parent_preparation_sha256=sha(parent/'report.json'),native_preparation=str(npath),native_preparation_sha256=digest,native_library=native['native_library'],native_include=native['native_include'],connected_include=str(derived),objects=objects,literal_objects_per_level=371,root=0x4B7F70,root_source_extent=extent,root_source_sha256=code_sha,registration_bindings=97,actual_Runtime_selected_call=True,selected_calls=1,registered_translations=126,CPU_after=[76,116],FX_before=[116,628],ordinary_pages=43,extra_source_pages=21,separately_carried_lower_stack=1,total_current_pages=65,current_pages=pages,source_bodies_modified=False,API_response_injection=False,native_executed=False,initializer_credit=0,control_scenarios=18,control_attempts=36,sources=pins,files=files)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(passed=True,sha256=sha(out/'report.json'),native_preparation_sha256=digest)))

if __name__=='__main__':main(Path(sys.argv[1]),sys.argv[2],sys.argv[3])
