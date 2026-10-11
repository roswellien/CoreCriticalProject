"""Compose genuine BEFORE role inputs with the current130 persistent Context.

One bounded first-CW/TOP fourteen-root candidate. No worker execution here.
"""
from pathlib import Path
import hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def one(t,a,b):assert t.count(a)==1,(a,t.count(a));return t.replace(a,b)
def main(name):
 out=R/'reports/m4-mfc1168-native'/name;assert not out.exists();out.mkdir();pins={};generated={};passed=False;objects={};inputs={};selected=[]
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip'),p;v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def raw(p,h=None):return pin(p,h).read_bytes()
 def write(p,data):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data if isinstance(data,bytes)else data.encode());generated[str(p.resolve())]=sha(p);pin(p)
 try:
  original_dir=R/'reports/m4-mfc1168-connected-original/validation-r1';original=read(original_dir/'report.json','0c768ff2d22a06d44e16175b511920422dceb94deb1482a98ee9c327e362d777');assert original['passed']
  source_dir=R/'reports/m4-mfc1168-connected-original/source-r3';source=read(source_dir/'report.json','3afcb5f1669726f43fa4c86a23eb1af8349dae1710e63ca7e87271a4fa1907d0');assert source['passed']
  derived=read(source_dir/'source-derivations.json');assert derived['actual_prefix_carried_BEFORE']and not derived['source_AFTER_seed']and len(derived['source_PCs'])==142
  retained=read(original_dir/'retained-actual-inputs.json');domain=read(original_dir/'actual-borrowed-domains.json')['BEFORE'];roots=read(original_dir/'actual-root-endpoints.json');assert len(roots)==14 and roots[-1]['root']==0x5ae3e4
  def before(key):assert '/BEFORE/'in key or key.endswith('/TEB-before.bin');row=retained[key];value=raw(row['path'],row['sha256']);assert len(value)==row['bytes'];return value
  parent_dir=R/'reports/m4-joint-startup130/preparation-r2';parent=read(parent_dir/'report.json','060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c');assert parent['passed']and len(parent['selected_order'])==130
  accepted=read(R/'reports/m4-joint-startup130-root/acceptance-r1/report.json','12215395619ea72ee1a587763112bc3a2ed9aad15c9c99a5697f69c9658429aa');assert accepted['passed']
  component_dir=R/'reports/m4-mfc1168-native/connected-component-preparation-r2';component=read(component_dir/'report.json','91e5cf450a5765798e3fbb729e34bb404971e9288d86482ad1a11cf2d995f562');build=read(R/'reports/m4-mfc1168-native/connected-component-build-r2/build.json','302e59ac9c5819919305caa4b4aa66125ebabdd827fb83f1ae66c6bcb700bfe2');assert component['passed']and build['passed']
  for p,h in component['files'].items():pin(p,h)
  # Copy only source files from the accepted composition. Historical archive
  # identities stay in its immutable receipt and are not opened for this fixture.
  for p in parent_dir.rglob('*'):
   if p.is_file()and p.suffix in('.cpp','.hpp','.inc'):write(out/p.relative_to(parent_dir),raw(p).decode().replace(parent_dir.as_posix(),out.as_posix()))
  for p in component_dir.iterdir():
   if p.suffix in('.cpp','.hpp','.inc')and p.name!='interface_link.cpp':write(out/p.name,raw(p))
  selected=parent['selected_order'][:13]+[dict(entry=0x5ae3e4,slot=0x5e0040)]
  assert [(x['entry'],x['slot'])for x in selected]==[(x['root'],x['slot'])for x in roots]
  roles=['manager-array','thread','thread-array','thread-object','global-object'];aliases=[0x33001000+k*0x1000 for k in range(5)];extents=[256,16,12,280,4240]
  owners=[];old=[]
  for role,alias,extent in zip(roles,aliases,extents):
   metadata=domain['blocks'][role]['metadata'];assert metadata[6:]==[extent,1];b=before('MFC1168/BEFORE/domain/'+role+'/bytes.bin');assert len(b)==extent
   owners.append(dict(role=role,old=metadata[0],new=alias,extent=extent,raw_before=b,projected_before=bytearray(b)));old.append(metadata[0])
  manager=before('MFC1168/BEFORE/MFC/'+str(0x5f4cb000)+'.bin');teb=before('phase/0/13/TEB-before.bin');original_teb=domain['metadata'][0];assert len(teb)==8192
  mappings=[dict(address=o['new'],permissions=3,bytes=o['raw_before'],role=o['role'])for o in owners]
  cs=before('MFC1168/BEFORE/CRT-codepage-lock/bytes.bin');assert len(cs)==24 and struct.unpack_from('<III',cs,4)==(0xffffffff,0,0)
  mappings.extend([dict(address=0x5f4cb000,permissions=3,bytes=manager,role='authentic manager page'),dict(address=0x33007000,permissions=3,bytes=cs,role='borrowed guestCS24'),dict(address=0x7ffde000+0xe1c,permissions=3,bytes=teb[0xe1c:0xe20],role='minimal typed TLS mirror')])
  pointer_cells=[dict(address=0x5f4cb018,before=old[0],projected=aliases[0]),dict(address=0x5f4cb01c,before=old[1],projected=aliases[1]),dict(address=0x5f4cb040,before=old[4],projected=aliases[4]),dict(address=0x7ffde000+0xe1c,before=old[1],projected=aliases[1]),dict(address=aliases[1]+12,before=old[2],projected=aliases[2]),dict(address=aliases[2]+4,before=old[3],projected=aliases[3])]
  for cell in pointer_cells:
   matches=[m for m in mappings if m['address']<=cell['address']and cell['address']+4<=m['address']+len(m['bytes'])];assert len(matches)==1;m=matches[0];assert struct.unpack_from('<I',m['bytes'],cell['address']-m['address'])[0]==cell['before']
   for owner in owners:
    if owner['new']<=cell['address']and cell['address']+4<=owner['new']+owner['extent']:struct.pack_into('<I',owner['projected_before'],cell['address']-owner['new'],cell['projected'])
  spec=importlib.util.spec_from_file_location('mfc_connected_physical',pin(R/'tools/analysis/pe.py'));PE=importlib.util.module_from_spec(spec);spec.loader.exec_module(PE)
  images={k:PE.PEImage(raw(p,h))for k,p,h in [('game',R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf'),('MFC',R/'local/mw3-staged/Shared_DLLs/MFC42.DLL','5f66a4d221e24c767aadd3f43a981df53d42f3d73bdf05b518120632099e2fc8'),('CRT',R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')]}
  def scalar(module,a):im=images[module];offset,_=im.rva_range(a-im.image_base,4);return struct.unpack_from('<I',im.data,offset)[0]
  crt=before('MFC1168/BEFORE/CRT/'+str(0x78037000)+'.bin');CRT_cells=[dict(address=a,before=scalar('CRT',a),projected=v,original_before=struct.unpack_from('<I',crt,a-0x78037000)[0])for a,v in [(0x7803708c,0x33007000),(0x780379c0,1252),(0x78037ae8,1)]]
  assert [c['original_before']for c in CRT_cells]==[domain['lock25_metadata'][1],1252,1]and [c['before']for c in CRT_cells]==[0,0,0]
  interface=read(R/'reports/m4-mfc1168-native/connected-interface-r1/connected-contracts.json');APIs=read(original_dir/'actual-named-API-boundaries.json');imports=[]
  for k,row in enumerate(interface['imports']):
   projected=row['original_isolated_loaded_target']if k<3 else APIs[(k-3)*2]['CPU'][9]
   assert scalar(row['module'],row['cell'])==row['file_raw'];imports.append(dict(pc=row['source_pc'],cell=row['cell'],raw=row['file_raw'],projected=projected))
  inputs=dict(root=0x5ae3e4,slot=0x5e0040,selected_order=selected,original_prefix_receipt_sha256=sha(original_dir/'report.json'),source_domain_receipt_sha256=sha(source_dir/'report.json'),guest_thread=domain['metadata'][1],guest_CS=0x33007000,original_TEB=original_teb,source_FS_before=derived['source_FS_BEFORE'],native_guest_FS=0x7ffde000,role_owners=[{k:v for k,v in o.items()if k not in('raw_before','projected_before')}for o in owners],pointer_cells=pointer_cells,CRT_cells=CRT_cells,imports=imports,whole_registry_or_IAT_replace=False,source_AFTER_input=False,native_CPU_or_FX_seed=False,source_initial_field14=owners[4]['raw_before'][20])
  assert inputs['source_initial_field14']==1
  write(out/'connected-inputs.json',json.dumps(inputs,indent=2)+'\n')
  def bytes_cpp(b):return '{'+','.join('std::byte{'+str(v)+'}'for v in b)+'}'
  lines=['#pragma once','#include "connected_component.hpp"','#include "admission.hpp"','namespace mw34::m4_mfc1168_connected {','inline Inputs make_fixture_inputs(){Inputs i;', 'i.addresses.bases={0,0x20001800,0x7ffde000,'+','.join(hex(a)for a in aliases)+'};',f'i.guest_thread={inputs["guest_thread"]};i.guest_CS=0x33007000;',f'i.original_prefix_receipt_sha256="{inputs["original_prefix_receipt_sha256"]}";i.source_domain_receipt_sha256="{inputs["source_domain_receipt_sha256"]}";']
  for k,o in enumerate(owners):lines.append(f'i.borrowed_before[{k}]='+bytes_cpp(o['projected_before'])+';')
  lines.append('i.CS_before='+bytes_cpp(cs)+';')
  for m in mappings:lines.append('i.new_mappings.push_back({'+str(m['address'])+','+str(m['permissions'])+','+bytes_cpp(m['bytes'])+'});')
  lines.append('i.pointer_cells={{'+','.join('{'+','.join(str(c[k])for k in ('address','before','projected'))+'}'for c in pointer_cells)+'}};')
  lines.append('i.CRT_cells={{'+','.join('{'+','.join(str(c[k])for k in ('address','before','projected'))+'}'for c in CRT_cells)+'}};')
  lines.append('i.imports={{'+','.join('{'+','.join(str(c[k])for k in ('pc','cell','raw','projected'))+'}'for c in imports)+'}};return i;}')
  # This is a candidate-only input authority, binding the sealed BEFORE vectors.
  # It grants no writer/run authorization. The independent prelaunch does that.
  lines.extend(['class InputAuthority {public: static std::unique_ptr<ChronologicalAdmission>admit(Runtime&r,const Inputs&i){auto e=make_fixture_inputs();require(i.addresses.bases==e.addresses.bases&&i.guest_thread==e.guest_thread&&i.guest_CS==e.guest_CS&&i.borrowed_before==e.borrowed_before&&i.CS_before==e.CS_before&&i.original_prefix_receipt_sha256==e.original_prefix_receipt_sha256&&i.source_domain_receipt_sha256==e.source_domain_receipt_sha256,"Whole sealed genuine BEFORE role input authority");require(i.new_mappings.size()==e.new_mappings.size(),"Exact new mapping count");for(unsigned k=0;k<i.new_mappings.size();++k)require(i.new_mappings[k].address==e.new_mappings[k].address&&i.new_mappings[k].permissions==e.new_mappings[k].permissions&&i.new_mappings[k].before==e.new_mappings[k].before,"Whole explicit loader BEFORE mapping");for(unsigned k=0;k<6;++k)require(i.pointer_cells[k].address==e.pointer_cells[k].address&&i.pointer_cells[k].before==e.pointer_cells[k].before&&i.pointer_cells[k].projected==e.pointer_cells[k].projected,"Exact six typed pointer cells");for(unsigned k=0;k<3;++k)require(i.CRT_cells[k].address==e.CRT_cells[k].address&&i.CRT_cells[k].before==e.CRT_cells[k].before&&i.CRT_cells[k].projected==e.CRT_cells[k].projected,"Exact three source loaded CRT cells");for(unsigned k=0;k<7;++k)require(i.imports[k].pc==e.imports[k].pc&&i.imports[k].cell==e.imports[k].cell&&i.imports[k].raw==e.imports[k].raw&&i.imports[k].projected==e.imports[k].projected,"Exact seven owning projections");return std::unique_ptr<ChronologicalAdmission>(new ChronologicalAdmission(r,i,i.source_domain_receipt_sha256));}};','}'])
  write(out/'connected_inputs.hpp','\n'.join(lines)+'\n')
  protocol=(out/'joint_protocol.hpp').read_text();protocol,n=re.subn(r'constexpr std::array<std::uint32_t,130> entries\{[^\n]+\};','constexpr std::array<std::uint32_t,14> entries{'+','.join(hex(x['entry'])for x in selected)+'};',protocol);assert n==1;write(out/'joint_protocol.hpp',protocol)
  text=(out/'native_main.cpp').read_text();text=one(text,'#include "registration_contract.hpp"','#include "registration_contract.hpp"\n#include "connected_inputs.hpp"\nnamespace mc=mw34::m4_mfc1168_connected;\nstruct MFCOutput{std::string name;std::vector<std::byte>bytes;};\nstatic std::vector<MFCOutput>mfc_output;\nstatic void mfc_sink(std::string_view name,std::span<const std::byte>b,void*){mfc_output.push_back({std::string(name),{b.begin(),b.end()}});}')
  text=one(text,'m4_runtime::Runtime r_;State&s_;','m4_runtime::Runtime r_;State&s_;mc::Inputs mfc_inputs_=mc::make_fixture_inputs();std::unique_ptr<mc::ChronologicalAdmission>mfc_admission_;std::unique_ptr<mc::Component>mfc_component_;')
  text=one(text,' unsigned completed{};',' static void mfc_entry(m4_runtime::Runtime&r){auto*c=active_context;require(c&&&r==&c->r_&&observation,"Current connected MFC Context/observation");overlay_cpu(c->s_,r.cpu());snapshot(r,c->s_,true);c->mfc_component_=std::make_unique<mc::Component>(r,c->mfc_inputs_,*c->mfc_admission_,&mfc_sink,nullptr);mc::Borrow borrow(*c->mfc_component_);mc::entry(r);sync_fx(r,c->s_);snapshot(r,c->s_,false);observation->state_seeded=r.remill_seeded();}\n unsigned completed{};')
  text=one(text,' r_.freeze_registry();',' mfc_admission_=mc::InputAuthority::admit(r_,mfc_inputs_);mc::materialize_loader_inputs(r_,mfc_inputs_,*mfc_admission_);\n r_.register_translation({{mc::root},{m4_runtime::Abi::Cdecl,0,true},&mfc_entry,"Chronological MFC1168 cached initializer",{m4_runtime::Domain::admitted_game,m4::admitted_image_hash,15,mfc_root_sha,mfc_object_sha,mfc_component_gate}});\n r_.freeze_registry();')
  text=one(text,'observation=nullptr;\n    if(item.target.value==ni::root)', 'observation=nullptr;if(item.target.value==mc::root){mfc_component_->finish();mfc_component_->checkpoint("cleaned");}\n    if(item.target.value==ni::root)')
  text=one(text,'phase==130&&r_.calls().size()==133&&r_.translation_count()==131','phase==14&&r_.calls().size()==14&&r_.translation_count()==132')
  text=text.replace('records.reserve(130)','records.reserve(14)').replace('records.size()==130','records.size()==14').replace('total==780','total==14').replace('seq==6','seq==1').replace('1,6,130,780,17,sizeof(Native)','1,1,14,14,17,sizeof(Native)').replace('1,6,sizeof(SequenceRecord),17','1,1,sizeof(SequenceRecord),17')
  text=one(text,'const std::array<std::array<unsigned,3>,6>cases{{{0,0x7f,0},{0,0x37f,7},{0,0xf7f,0},{1,0x47f,7},{1,0xa7f,0},{1,0xe7f,7}}};','const std::array<std::array<unsigned,3>,1>cases{{{0,0x7f,0}}};')
  text=one(text,'for(auto input:cases){const auto repeat=', 'for(auto input:cases){mfc_output.clear();const auto repeat=')
  text=one(text,'  direct.prefix=prefix+"selected/";', '  for(const auto&row:mfc_output)writer.append(prefix+"MFC/"+row.name,row.bytes.data(),row.bytes.size());\n  direct.prefix=prefix+"selected/";')
  # The bounded prefix has no registering selected root: retain actual producer
  # cleanup, but do not introduce an unrelated growth/root replay after phase14.
  start=text.index('  // Genuine source root replay is a separate growth experiment, outside selected-table credit.')
  end=text.index('DirectPhaseWriter::current=nullptr;total+=records.size();++seq;',start)
  text=text[:start]+'  context.registry().finish();direct.prefix=prefix+"registry-cleaned/";context.registry().dump(&DirectPhaseWriter::sink,&direct);need(!context.registry().live_handle(),"Current registry owner cleanup");'+text[end:]
  text=text.replace('Six persistent130-root sequences and genuine source growth/cleanup complete; fullM4 incomplete','One genuine-domain persistent14-root native prefix and owned cleanup complete; fullM4 incomplete').replace('780native phases in6persistent130-root sequences','14native phases in1persistent connected MFC prefix')
  write(out/'native_main.cpp',text)
  lift=read(R/'reports/m4-mfc1168-native/lifts-r2/report.json');root_body=lift['source_bodies']['f_5ae3e4'];root_sha='97b845ebbb837a375af2962ba2bc65cba1c966f37b380aa46b380c9ed8fd5fa2'
  for level in ('O0','O2'):
   objects[level]=list(parent['objects'][level])+component['objects'][level];assert len(objects[level])==410
   for p in objects[level]:pin(p)
   bindings=f'namespace mw34::m4_mixed{{constexpr auto mfc_root_sha="{root_sha}";constexpr auto mfc_object_sha="{root_body["objects"][level]["sha256"]}";constexpr auto mfc_component_gate="{sha(component_dir/"report.json")}";}}\n'
   write(out/level/'mfc_build_bindings.hpp',bindings)
  write(out/'native_main.cpp',one((out/'native_main.cpp').read_text(),'#include "connected_inputs.hpp"','#include "connected_inputs.hpp"\n#include "mfc_build_bindings.hpp"'))
  cmake=raw(parent_dir/'CMakeLists.txt').decode();cmake=one(cmake,'"${MW34_PREP}/native_main.cpp" ${MW34_FP_CPP}','"${MW34_PREP}/native_main.cpp" "${MW34_PREP}/connected_component.cpp" ${MW34_FP_CPP}');cmake=cmake.replace('mw34_joint_startup130','mw34_mfc1168_connected');write(out/'CMakeLists.txt',cmake)
  for p in (Path(__file__),Path(sys.executable),R/'tools/m4-mfc1168-native/build_connected_fixture.py',R/'tools/m4-mfc1168-native/build_connected_fixture.ps1'):pin(p)
  for p,h in pins.items():assert sha(p)==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Linked candidate current130 Context with first13 accepted roots then nonregistering MFC1168; genuine chronological BEFORE-only five-role graph, typed raw-IAT projections, three loaded CRT cells; writer pending independent prelaunch',parent_preparation=str(parent_dir/'report.json') if 'parent_dir'in locals()else None,selected_order=selected,source_roots=14,source_sequences=1,current_registration_callbacks=101,Runtime_translations=132,literal_objects_per_level=410,objects=objects,native_library=parent['native_library']if'parent'in locals()else None,native_include=parent['native_include']if'parent'in locals()else None,component_preparation=str(component_dir/'report.json')if'component_dir'in locals()else None,chronological_original=str(original_dir/'report.json')if'original_dir'in locals()else None,chronological_original_sha256='0c768ff2d22a06d44e16175b511920422dceb94deb1482a98ee9c327e362d777',chronological_source=str(source_dir/'report.json')if'source_dir'in locals()else None,chronological_source_sha256='3afcb5f1669726f43fa4c86a23eb1af8349dae1710e63ca7e87271a4fa1907d0',inputs=inputs,generated_sources=generated,files=pins,capture_archive_reader_opened=False,worker_executed=False,execution_admitted=False,AFTER_machine_seed=False,per_phase_reseed=False,initializer_credit=0,remaining_gate='Build/prelaunch, current14 execution/source/full caller/API resources and CRT merge/registry closure; then persistent131/paired acceptance')
  (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'report.json'))))
if __name__=='__main__':main(sys.argv[1])
