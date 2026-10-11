"""Freeze a bounded admitted-image native fixture from genuine BEFORE only.

The borrowed layout and causal operand identities are finite source contracts.
No original AFTER backing, register, page or response is supplied to native code.
"""
from pathlib import Path
import hashlib,json,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
B=R/'reports/m4-mfc1168-native'
V=R/'reports/m4-mfc1168-probe/validation-r6'
C=R/'reports/m4-mfc1168-probe/native-contracts-r1'
L=B/'lifts-r2'
E=R/'reports/m4-mfc1168-probe/execution-r6/trace'
PINS={}
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def pin(p,h=None):
 p=Path(p).resolve();a=sha(p);need(h is None or a==h,'Pinned physical input '+str(p));need(str(p)not in PINS or PINS[str(p)]==a,'Stable input');PINS[str(p)]=a;return p
def raw(p):return pin(p).read_bytes()
def read(p,h=None):return json.loads(pin(p,h).read_bytes())
def u(p,n=1):return struct.unpack('<'+'I'*n,raw(p))
def main(name):
 out=B/name;need(not out.exists(),'Fresh fixture preparation');out.mkdir(parents=True);passed=False
 try:
  v=read(V/'report.json','81006b3089f41d0df95aae70428d400108d44c5026cc428682faab2407bd99f2');need(v['passed'],'Passed literal original proof')
  c=read(C/'report.json','ec43e53280a0b15d6f29da7ac51e9f04d20d6b25514275cfb618448348eadade');need(c['passed'],'Passed finite native contract preparation')
  contracts=read(C/'contracts.json');lift=read(L/'report.json','55bb1c8fd59cf11f63ae199e93ea83220fa2cbc15d4d39e388946fc452f4664e');need(lift['passed']and len(lift['source_bodies'])==13,'Thirteen frozen literal bodies')
  for q,h in lift['entry_objects'].items():pin(q,h)
  # These authored causal rows derive from the independently executed source;
  # only PC/address/width/direction are compiled, never their observed values.
  source=read(V/'source-derivations.json');accesses=[(a,b,d,e)for a,b,_,d,e in source['accesses']];need(len(accesses)==113,'Exact normal operand sequence')
  blocks=[]
  def block(address,bytes_,permissions,role):
   need(bytes_ and 0<=address<2**32 and address+len(bytes_)<=2**32,'Bounded guest block')
   need(all(address>=b['address']+b['size']or address+len(bytes_)<=b['address']for b in blocks),'Nonoverlapping exact guest backings')
   blocks.append(dict(address=address,size=len(bytes_),permissions=permissions,role=role,bytes=bytes_))
  def perms(p):
   p&=255;need(p in(2,4,8,0x20,0x40,0x80),'Observed readable physical page protection');return {2:1,4:3,8:3,0x20:5,0x40:7,0x80:7}[p]
  for module in('MFC','CRT'):
   meta=raw(E/f'BEFORE/{module}/metadata.bin');need(len(meta)%16==0,'Whole module metadata')
   for address,protect,type_,allocationbase in struct.iter_unpack('<4I',meta):
    x=raw(E/f'BEFORE/{module}/{address}.bin');need(len(x)==4096,'Whole genuine source provider BEFORE page');block(address,x,perms(protect),module+'-loaded-before')
  need(len(blocks)==272,'272 genuine loaded provider pages')
  for q in sorted((E/'BEFORE/game-physical').glob('*.bin')):block(int(q.stem),raw(q),1 if int(q.stem)==0x736000 else 5,'Game-loaded-before')
  teb=u(E/'root-TEB-before-base.bin')[0];block(teb,raw(E/'root-TEB-before-pages.bin'),3,'Coherent genuine root TEB8192')
  block(0x20000000,raw(E/'stack-before.bin'),3,'Whole genuine source stack65536')
  for backing in contracts['borrowed_backings']:
   p=E/f'BEFORE/domain/{backing["role"]}/bytes.bin';x=raw(p);need(sha(p)==backing['initial_sha256']and len(x)==backing['extent'],'Whole authentic borrowed backing');block(backing['guest'],x,3,'Borrowed '+backing['role'])
  lm=u(E/'BEFORE/CRT-codepage-lock/meta.bin',4);need(lm[0]==0x7803708c and lm[2:]==(24,1),'Genuine initialized guest codepage lock25');block(lm[1],raw(E/'BEFORE/CRT-codepage-lock/bytes.bin'),3,'Borrowed initialized opaque guest CS24')
  cpu=u(E/'CPU-before.bin',10);fx=raw(E/'FX-before.bin');need(len(fx)==512 and cpu[4]==0x20008000,'Measured caller State/FX input')
  domain=u(E/'BEFORE/domain/domain.bin',10);need(domain[0]==teb and domain[5]==3 and domain[7]==next(x['guest']for x in contracts['borrowed_backings']if x['role']=='thread'),'Actual source current-thread/TLS lineage')
  pack=bytearray(b'M4MFCNAT'+struct.pack('<I',len(blocks)))
  for b in blocks:pack+=struct.pack('<3I',b['address'],b['size'],b['permissions'])+b['bytes']
  (out/'before-pack.bin').write_bytes(pack)
  layout=[{k:v for k,v in b.items()if k!='bytes'}|dict(initial_sha256=hashlib.sha256(b['bytes']).hexdigest())for b in blocks];(out/'before-layout.json').write_text(json.dumps(layout,indent=2)+'\n')
  (out/'fixture.cpp').write_bytes(raw(R/'tools/m4-mfc1168-native/fixture.cpp'))
  bridges=set(x for b in lift['source_bodies'].values()for x in b['bridges']);extra=[]
  for name_ in sorted(bridges):
   if '_direct_' in name_:extra.append(f'extern "C" void*{name_}(State*s,unsigned a,void*p){{return mw34_mfc1168_call(s,a,p);}}')
   elif name_.endswith('_undefined_8'):extra.append(f'extern "C" unsigned char {name_}(){{require(current,"Active explicit undefined arithmetic representative");current->authority();return 0;}}')
  (out/'generated_bridges.inc').write_text('\n'.join(extra)+'\n')
  rootbytes=raw(L/'f_5ae3e4-source.bin');need(len(rootbytes)==15,'Physical registered root complete span')
  prefix=['#pragma once','#include "runtime.hpp"','#include <remill/Arch/X86/Runtime/State.h>','#include <array>','#include <cstddef>']
  for body in lift['source_bodies'].values():prefix.append(f'extern "C" void*{body["symbol"]}_body(State*,unsigned,void*);')
  prefix+=['namespace mw34_mfc_fixture {',f'inline constexpr unsigned thread_pointer={domain[7]}U,global_pointer={domain[4]}U,TEB={teb}U,CS_pointer={lm[1]}U,guest_thread={contracts["thread_contract"]["current_process_thread"]}U,initial_flags={cpu[8]}U;',
   'struct AccessSpec {unsigned pc,address,width,writing;};',f'inline constexpr std::array<AccessSpec,{len(accesses)}>access_order{{{{'+','.join('{'+','.join(str(x)+'U'for x in row)+'}'for row in accesses)+'}};',
   'struct ApiSpec {unsigned site,raw,argc,ret,call_site;};', 'inline constexpr std::array<ApiSpec,4>APIs{{'+','.join('{'+','.join(str(x)+'U'for x in (r['source_PC'],r['source_target'],r['argc'],r['return_PC'],0x78003dee if i==2 else r['source_PC']))+'}'for i,r in enumerate(contracts['normal_APIs']))+'}};',
   'struct Instruction {unsigned pc;bool call,ret;};',f'inline constexpr std::array<Instruction,{len(contracts["instructions"])}>instructions{{{{'+','.join('{'+str(r['pc'])+'U,'+str(r['mnemonic']=='call').lower()+','+str(r['mnemonic'] in('ret','retn')).lower()+'}'for r in contracts['instructions'])+'}};',
   'inline const Instruction*instruction(unsigned pc){for(const auto&i:instructions)if(i.pc==pc)return &i;return nullptr;}',
   'inline bool body(unsigned pc){switch(pc){'+''.join('case '+str(b['entry'])+'U:'for b in lift['source_bodies'].values())+'return true;default:return false;}}',
   'inline void*dispatch(unsigned pc,State*s,void*p){switch(pc){'+''.join('case '+str(b['entry'])+'U:return '+b['symbol']+'_body(s,pc,p);'for b in lift['source_bodies'].values())+'default:throw std::runtime_error("Unproved literal target");}}',
   'inline constexpr mw34::m4_runtime::Cpu32 initial_cpu{'+','.join(str(x)+'U'for x in cpu)+'};',
   'inline constexpr std::array<std::byte,512>initial_FX{'+','.join('std::byte{'+str(x)+'}'for x in fx)+'};',
   'inline constexpr const char*root_sha="'+hashlib.sha256(rootbytes).hexdigest()+'";',
   'inline constexpr const char*lift_report_sha="'+sha(L/'report.json')+'";']
  objects={}
  for level in('O0','O2'):
   objects[level]=[b['objects'][level]['path']for b in lift['source_bodies'].values()]
   header=prefix+['inline constexpr const char*native_object_sha="'+lift['source_bodies']['f_5ae3e4']['objects'][level]['sha256']+'";','}']
   (out/f'fixture_spec_{level}.hpp').write_text('\n'.join(header)+'\n')
  remill=R/'local/tools/remill-v6.0.1/remill-6.0.1/include'
  cmake='''cmake_minimum_required(VERSION 3.24)
project(MFC1168Native LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
configure_file("${CMAKE_CURRENT_SOURCE_DIR}/fixture_spec_${MW34_LEVEL}.hpp" "${CMAKE_CURRENT_BINARY_DIR}/fixture_spec.hpp" COPYONLY)
add_executable(mfc1168-native fixture.cpp "${MW34_ROOT}/tools/m4-runtime/runtime.cpp" "${MW34_ROOT}/tools/m4-startup/image_loader.cpp" "${MW34_ROOT}/runtime/memory/guest_memory.cpp" ${MW34_OBJECTS})
target_include_directories(mfc1168-native PRIVATE "${CMAKE_CURRENT_BINARY_DIR}" "${MW34_ROOT}/tools/m4-runtime" "${MW34_ROOT}/tools/m4-startup" "${MW34_ROOT}/runtime" "${MW34_REMILL}")
target_link_libraries(mfc1168-native PRIVATE bcrypt)
'''
  (out/'CMakeLists.txt').write_text(cmake)
  for q in(R/'tools/m4-runtime/runtime.hpp',R/'tools/m4-runtime/runtime.cpp',R/'tools/m4-startup/image_loader.hpp',R/'tools/m4-startup/image_loader.cpp',R/'runtime/memory/guest_memory.hpp',R/'runtime/memory/guest_memory.cpp',R/'runtime/core/guest_address.hpp'):pin(q)
  for q in remill.rglob('*.h'):pin(q)
  for q in(out/'before-pack.bin',out/'before-layout.json',out/'fixture.cpp',out/'generated_bridges.inc',out/'fixture_spec_O0.hpp',out/'fixture_spec_O2.hpp',out/'CMakeLists.txt',Path(__file__),Path(sys.executable)):pin(q)
  for q,h in PINS.items():need(sha(q)==h,'Stable frozen fixture input')
  passed=True
 finally:
  report=dict(passed=passed,scope='One registered admitted-image cached MFC1168 root; BEFORE-only input and13 literal bodies, compile/execute still pending',
   original_validation=str(V/'report.json'),original_validation_sha256=sha(V/'report.json'),native_contracts=str(C/'report.json'),native_contracts_sha256=sha(C/'report.json'),lifts=str(L/'report.json'),lifts_sha256=sha(L/'report.json'),
   objects=objects if'objects'in locals()else{},remill_include=str(remill)if'remill'in locals()else None,layout=layout if'layout'in locals()else[],input_pack=str(out/'before-pack.bin'),files=PINS,
   assertions=dict(original_AFTER_data_seed=False,original_API_response_seed=False,borrowed_native_resource_separate=True,unobserved_branches_denied=True,source_undefined_flags='explicit zero representative'),
   counts=dict(literal_entries=13,literal_instructions=142,causal_operands=113,borrowed_backings=5,borrowed_CS24=1,named_APIs=4,current_native_CS40=1,current_host_TLS_associations=1),native_executed=False,initializer_credit=0)
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,report_sha256=sha(out/'report.json'))))
if __name__=='__main__':
 try:main(sys.argv[1])
 except BaseException:traceback.print_exc();raise
