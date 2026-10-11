"""Freeze concrete connected code and literal link inputs without input admission."""
from pathlib import Path
import hashlib,json,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-mfc1168-native'/name;assert not out.exists();out.mkdir();pins={};passed=False;objects={}
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or v==h,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def copy(src,dst):dst.write_bytes(pin(src).read_bytes());pin(dst)
 try:
  interface=read(R/'reports/m4-mfc1168-native/connected-interface-r1/report.json','2d509e61a1fa822c2116bed237d345968ed75261a67a0cb057cd3458d5ce857c');assert interface['passed']and not interface['connected_execution_admitted']
  c=read(interface['contracts'],interface['contracts_sha256']);lifts=read(R/'reports/m4-mfc1168-native/lifts-r2/report.json','55bb1c8fd59cf11f63ae199e93ea83220fa2cbc15d4d39e388946fc452f4664e')
  resource=read(R/'reports/m4-mfc1168-native/resource-preparation-r3/report.json','bc56a951d2655876866fc8a75564e002fd754adb7a429a6a27df9e71b8ed97b1')
  assert len(lifts['source_bodies'])==13 and len(c['instructions'])==142 and len(c['normal_operand_order'])==113
  for name in ('connected_entry.hpp','connected_component.hpp','connected_component.cpp'):copy(R/'tools/m4-mfc1168-native'/name,out/name)
  copy(interface['address_header'],out/'connected_address_contract.hpp')
  copy(R/'tools/m4-mfc1168-native/resource_witness.hpp',out/'resource_witness.hpp')
  rows=c['instructions'];bodies=list(lifts['source_bodies'].values());header=['#pragma once','#include "connected_entry.hpp"','#include <array>']
  header.extend('extern "C" void*'+b['symbol']+'_body(State*,unsigned,void*);'for b in bodies)
  header.append('namespace mw34::m4_mfc1168_connected::literal {')
  header.extend(['struct Instruction {unsigned pc;bool call,ret;};','inline constexpr std::array<Instruction,142>instructions{{'+','.join('{'+str(r['pc'])+','+str(r['mnemonic']=='call').lower()+','+str(r['mnemonic'].startswith('ret')).lower()+'}'for r in rows)+'}};','inline const Instruction*instruction(unsigned pc){for(const auto&r:instructions)if(r.pc==pc)return&r;return nullptr;}'])
  header.append('inline bool body(unsigned pc){switch(pc){'+''.join('case '+str(b['entry'])+':return true;'for b in bodies)+'default:return false;}}')
  header.append('inline void*dispatch(unsigned pc,State*s,void*p){switch(pc){'+''.join('case '+str(b['entry'])+':return '+b['symbol']+'_body(s,pc,p);'for b in bodies)+'default:throw std::runtime_error("Unproved literal target");}}')
  header.extend(['struct SourceSpan{unsigned pc,size;std::array<std::byte,16>bytes;};','inline constexpr std::array<SourceSpan,142>source_spans{{'+','.join('{'+str(r['pc'])+','+str(r['width'])+',{'+','.join('std::byte{'+str(v)+'}'for v in bytes.fromhex(r['bytes_hex']))+'}}'for r in rows)+'}};'])
  # API sites/arity/returns are literal. Named target representatives are supplied
  # by separate chronological owning projections, never original AFTER registers.
  header.append('struct Api{unsigned site,argc,ret,call_site;};')
  apis=[]
  for a in read(R/'reports/m4-mfc1168-probe/native-contracts-r1/contracts.json','f7db9805f43e1eb7ef84ad8adb5ddb0f788b76844dbaadb736329787a410eb64')['normal_APIs']:
   apis.append([a['source_PC'],a['argc'],a['return_PC'],0x78003dee if a['API']=='GetACP'else a['source_PC']])
  header.append('inline constexpr std::array<Api,4>APIs{{'+','.join('{'+','.join(map(str,a))+'}'for a in apis)+'}};');header.append('}')
  (out/'connected_literals.hpp').write_text('\n'.join(header)+'\n');pin(out/'connected_literals.hpp')
  # Existing direct/undefined bridge names are physical lift dependencies only.
  bridges=pin(R/'reports/m4-mfc1168-native/resource-preparation-r3/generated_bridges.inc').read_text()
  bridges=bridges.replace('require(current,"Active explicit undefined arithmetic representative");current->authority();','auto&c=owner(Component::Impl::current);c.authority();')
  (out/'connected_bridges.inc').write_text(bridges);pin(out/'connected_bridges.inc')
  (out/'interface_link.cpp').write_text('#include "connected_component.hpp"\nextern "C" __declspec(dllexport) mw34::m4_runtime::NativeEntry mfc_connected_linked_entry=&mw34::m4_mfc1168_connected::entry;\n')
  pin(out/'interface_link.cpp')
  cmake='''cmake_minimum_required(VERSION 3.24)
project(MFC1168ConnectedComponent LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_library(mfc1168-component SHARED connected_component.cpp interface_link.cpp "${MW34_ROOT}/tools/m4-runtime/runtime.cpp" "${MW34_ROOT}/tools/m4-startup/image_loader.cpp" "${MW34_ROOT}/runtime/memory/guest_memory.cpp" ${MW34_OBJECTS})
target_include_directories(mfc1168-component PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}" "${MW34_ROOT}/tools/m4-runtime" "${MW34_ROOT}/tools/m4-startup" "${MW34_ROOT}/runtime" "${MW34_REMILL}")
target_link_libraries(mfc1168-component PRIVATE bcrypt)
'''
  (out/'CMakeLists.txt').write_text(cmake);pin(out/'CMakeLists.txt')
  for level in ('O0','O2'):
   objects[level]=[]
   for b in bodies:obj=b['objects'][level];objects[level].append(str(pin(obj['path'],obj['sha256'])))
  for source in ('tools/m4-runtime/runtime.cpp','tools/m4-runtime/runtime.hpp','tools/m4-startup/image_loader.cpp','runtime/memory/guest_memory.cpp','tools/m4-mfc1168-native/prepare_connected_component.py'):pin(R/source)
  pin(sys.executable)
  note='''Concrete current-Runtime component and loader-input code, not a connected admission. Component links thirteen normal literal COFFs using current State/CPU/FX, no isolated input pack. Five typed role backings, source-owned EH frames, four API calls, actual owned TLS/CS40, full borrowed capacities and raw import projections have executable checks. The seven source-owned import projections retain the parent's physical IAT cells. Loader materialization validates an owned GuestMemory copy before its single commit and touches only declared new mappings, six pointer cells and three CRT cells; the source domain still requires a separate chronological gate. The Admission type has a private constructor and no factory in these files, so this revision supplies no accepted input or executable worker. Fresh genuine13-root prefix is now available and will drive the separate factory/merge/source proof. No whole State/FX setter, main, registration callback, or initializer credit.\n'''
  (out/'component.md').write_text(note);pin(out/'component.md')
  for p,h in pins.items():assert sha(p)==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Concrete connected Runtime/resource/literal component frozen for O0/O2 link only; chronological input authority and writer absent',interface=str(R/'reports/m4-mfc1168-native/connected-interface-r1/report.json'),interface_sha256='2d509e61a1fa822c2116bed237d345968ed75261a67a0cb057cd3458d5ce857c',objects=objects,remill_include=resource['remill_include'],source_bodies=list(lifts['source_bodies']) if 'lifts'in locals()else[],literal_body_count=13,normal_instructions=142,normal_operands=113,named_source_API_calls=4,owned_native_API_services=9,chronological_input_factory_available=False,connected_execution_admitted=False,worker_prepared=False,source_roots_executed=0,initializer_credit=0,files=pins)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
