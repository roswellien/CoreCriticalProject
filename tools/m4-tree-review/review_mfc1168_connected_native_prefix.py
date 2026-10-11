"""Independent bounded review of the current Context's new fourteen-root smoke."""
from pathlib import Path
from collections import Counter
import hashlib,importlib.util,json,re,struct,subprocess,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
B=R/'reports/m4-mfc1168-native'
BSHA='1f8fac0b491ee99e39a966bf2c03e5059e7f541d2d5ed862c9310b8be1b304ba'
PSHA='278be74db3998e7396ba46696a59f5e6fbd9acc43f71e0ca1eaedd272822ce4f'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir();pins={};counts=Counter();links=[];passed=False
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def blob(p,h=None):return pin(p,h).read_bytes()
 def module(p,name):
  s=importlib.util.spec_from_file_location(name,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def receipt(p,h=None):
  j=read(p,h);assert j['passed']
  for k in('files','artifacts','generated_sources'):
   for p,h in j.get(k,{}).items():
    if Path(p).suffix.lower()not in('.mwb','.zip'):pin(p,h)
  return j
 try:
  build=receipt(B/'connected-fixture-build-r1/build.json',BSHA)
  prep=receipt(build['preparation'],PSHA);folder=Path(build['preparation']).parent
  assert build['preparation_sha256']==PSHA and prep['source_roots']==14 and prep['source_sequences']==1
  assert prep['initializer_credit']==0 and not prep['AFTER_machine_seed'] and not prep['per_phase_reseed']
  parent=read(prep['parent_preparation'],'060094c0019760a1095d60ee39a73ea7193a060a332bc67db9aae628c128857c')
  accepted=read(R/'reports/m4-joint-startup130-root/acceptance-r1/report.json','12215395619ea72ee1a587763112bc3a2ed9aad15c9c99a5697f69c9658429aa')
  assert accepted['passed'] and accepted['connected_roots']==130
  assert prep['selected_order']==parent['selected_order'][:13]+[dict(entry=0x5ae3e4,slot=0x5e0040)]
  original=read(prep['chronological_original'],prep['chronological_original_sha256']);source=read(prep['chronological_source'],prep['chronological_source_sha256'])
  assert original['passed'] and source['passed'] and original['reader_closed']
  source_review=receipt(R/'reports/m4-tree-review/mfc1168-chronological-source-r2/report.json','cad4c935d169fccf4adbdff725daf3aa6bee617970cb96c90a42cbcf1c3c9f58')
  retained=read(Path(prep['chronological_original']).parent/'retained-actual-inputs.json')
  domain=read(Path(prep['chronological_original']).parent/'actual-borrowed-domains.json')['BEFORE']
  inputs=read(folder/'connected-inputs.json')
  assert inputs==prep['inputs'] and not inputs['source_AFTER_input'] and not inputs['native_CPU_or_FX_seed']
  assert not inputs['whole_registry_or_IAT_replace'] and inputs['source_initial_field14']==1
  header=pin(folder/'connected_inputs.hpp').read_text()
  def before(key):
   assert '/BEFORE/'in key or key.endswith('/TEB-before.bin');row=retained[key];b=blob(row['path'],row['sha256']);assert len(b)==row['bytes'];return b
  def cppbytes(raw):return bytes(map(int,re.findall(r'std::byte\{(\d+)\}',raw)))
  mappings=[]
  for match in re.finditer(r'i.new_mappings.push_back\(\{(\d+),(\d+),(.*?)\}\);',header):
   mappings.append((int(match[1]),int(match[2]),cppbytes(match[3])))
  assert len(mappings)==8
  borrowed=[cppbytes(re.search(r'i.borrowed_before\['+str(k)+r'\]=(.*?);',header)[1]) for k in range(5)]
  for k,(role,extent)in enumerate(zip(('manager-array','thread','thread-array','thread-object','global-object'),(256,16,12,280,4240))):
   o=inputs['role_owners'][k];assert o['role']==role and o['extent']==extent and o['new']==0x33001000+k*0x1000 and o['old']==domain['blocks'][role]['metadata'][0]
   raw=before('MFC1168/BEFORE/domain/'+role+'/bytes.bin');assert mappings[k]==(o['new'],3,raw)
   projected=bytearray(raw)
   for c in inputs['pointer_cells']:
    if o['new']<=c['address'] and c['address']+4<=o['new']+extent:
     at=c['address']-o['new'];assert struct.unpack_from('<I',raw,at)[0]==c['before'];struct.pack_into('<I',projected,at,c['projected'])
   assert borrowed[k]==projected;counts['whole_genuine_borrowed_BEFORE_relations']+=1
  cs=before('MFC1168/BEFORE/CRT-codepage-lock/bytes.bin');teb=before('phase/0/13/TEB-before.bin');manager=before('MFC1168/BEFORE/MFC/'+str(0x5f4cb000)+'.bin')
  assert mappings[5:]==[(0x5f4cb000,3,manager),(0x33007000,3,cs),(0x7ffdee1c,3,teb[0xe1c:0xe20])]
  assert cppbytes(re.search(r'i.CS_before=(.*?);',header)[1])==cs
  assert len(cs)==24 and struct.unpack_from('<3I',cs,4)==(0xffffffff,0,0)
  assert len(teb)==8192 and struct.unpack_from('<I',teb,0x18)[0]==inputs['original_TEB']
  for c in inputs['pointer_cells']:
   owners=[v for v in mappings if v[0]<=c['address'] and c['address']+4<=v[0]+len(v[2])];assert len(owners)==1
   assert struct.unpack_from('<I',owners[0][2],c['address']-owners[0][0])[0]==c['before'];counts['exact_consumed_pointer_projections']+=1
  PE=module(R/'tools/analysis/pe.py','mfc_prefix_pe')
  images={name:PE.PEImage(blob(path))for name,path in [('game',R/'MW3/Mech3.exe'),('MFC',R/'local/mw3-staged/Shared_DLLs/MFC42.DLL'),('CRT',R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL')]}
  def physical(name,address):
   image=images[name];off,_=image.rva_range(address-image.image_base,4);return struct.unpack_from('<I',image.data,off)[0]
  crt=before('MFC1168/BEFORE/CRT/'+str(0x78037000)+'.bin')
  assert [(c['address'],c['before'],c['projected']) for c in inputs['CRT_cells']]==[(0x7803708c,0,0x33007000),(0x780379c0,0,1252),(0x78037ae8,0,1)]
  for c in inputs['CRT_cells']:
   assert physical('CRT',c['address'])==c['before'] and struct.unpack_from('<I',crt,c['address']-0x78037000)[0]==c['original_before'];counts['finite_three_CRT_cell_source_relations']+=1
  contracts=read(R/'reports/m4-mfc1168-native/connected-interface-r1/connected-contracts.json')
  for i,row in zip(inputs['imports'],contracts['imports']):
   assert (i['pc'],i['cell'],i['raw'])==(row['source_pc'],row['cell'],physical(row['module'],row['cell']));counts['owning_raw_IAT_relations']+=1
  main=pin(folder/'native_main.cpp').read_text();component=pin(folder/'connected_component.cpp').read_text();entry=pin(folder/'connected_entry.hpp').read_text()
  for s in ('phase==14&&r_.calls().size()==14&&r_.translation_count()==132','overlay_cpu(c->s_,r.cpu())','registry_->bootstrap()','const std::array<std::array<unsigned,3>,1>cases{{{0,0x7f,0}}}','mfc_component_->finish();mfc_component_->checkpoint("cleaned")','record.common.after.pc==broker&&record.common.after.gpr[4]==frame+4'):
   assert s in main,s
  for s in ('auto candidate=r.memory()','candidate.load<unsigned>({cell.address})==cell.before','for(const auto&v:i.imports)require(candidate.load<unsigned>({v.cell})==v.raw','r.memory()=std::move(candidate)','GetCurrentThreadId()==host_thread&&TLS_live&&CS_live','matches(access_cursor,s.gpr.rip.dword,address,width,writing,input.addresses)','value=v.projected','if(index==0){auto p=mf_TlsGetValue(host_TLS)','mf_EnterCriticalSection(&CS)','mf_LeaveCriticalSection(&CS)','raw==1252','mf_TlsFree(host_TLS)','mf_DeleteCriticalSection(&CS)'):
   assert s in component,s
  assert 'project(s,r.cpu())'in entry and 'Integer MFC source retains entire carried Runtime FX512'in entry
  C=module(R/'tools/m4-tree-review/amd64_coff.py','mfc_prefix_coff');M=module(R/'tools/m4-tree-review/review_mfc1168_native_prelaunch_v4.py','mfc_prefix_amd64')
  lift=read(R/'reports/m4-mfc1168-native/lifts-r2/report.json')
  ninja=pin('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe')
  for level,w in build['workers'].items():
   bf=Path(w['path']).parent;image=M.AMD64Image(blob(w['path'],w['sha256']));graph=pin(bf/'build.ninja').read_text()
   assert len(prep['objects'][level])==410 and set(parent['objects'][level])<set(prep['objects'][level])
   line=next(s for s in graph.splitlines()if s.startswith('build '+Path(w['path']).name+': CXX_EXECUTABLE_LINKER'))
   linked={str((bf/Path(s.replace('$:',':'))).resolve()).casefold() for s in line.split(' ',3)[3].split(' |')[0].split(' ')if s.endswith(('.obj','.lib'))}
   assert {str(Path(p).resolve()).casefold() for p in prep['objects'][level]}<=linked
   for j in lift['source_bodies'].values():
    obj=j['objects'][level];symbols,sections=C.parse(blob(obj['path'],obj['sha256']));raw,relocs=C.function(symbols,sections,j['symbol']+'_body');matches=C.linked_candidates(image,raw,relocs);assert len(matches)==1,j['symbol']
    links.append(dict(level=level,symbol=j['symbol']+'_body',address=matches[0][0],whole_bytes=len(raw),relocation_DWORDs=len(relocs)));counts['whole_linked_literal_functions']+=1
   for filename,prefixes in [('connected_component.cpp.obj',('?materialize_loader_inputs@','?read@Impl@','?dispatch@Impl@','?API@Impl@')),('native_main.cpp.obj',('?mfc_entry@Context@','?invoke_selected_body@Context@'))]:
    obj=pin(bf/'CMakeFiles/mw34_mfc1168_connected.dir'/filename);symbols,sections=C.parse(obj.read_bytes())
    for prefix in prefixes:
     candidates=[s['name'] for s in symbols.values()if s['name'].startswith(prefix) and s['section']>0 and s['type']==32]
     if not candidates:
      # O2 may inline a bridge into its caller. The explicit MFC entry and
      # transactional loader remain actual required functions at both levels.
      assert level=='O2' and prefix in ('?read@Impl@','?dispatch@Impl@','?API@Impl@','?invoke_selected_body@Context@');counts['declared_O2_inlined_methods']+=1;continue
     assert len(candidates)==1
     raw,relocs=C.function(symbols,sections,candidates[0]);matches=C.linked_candidates(image,raw,relocs);assert len(matches)==1,candidates[0]
     links.append(dict(level=level,symbol=candidates[0],address=matches[0][0],whole_bytes=len(raw),relocation_DWORDs=len(relocs)));counts['whole_linked_changed_adapter_functions']+=1
   db=pin(bf/'.ninja_deps');result=subprocess.run([str(ninja),'-C',str(bf),'-t','deps'],capture_output=True,timeout=30,creationflags=0x08000000);assert result.returncode==0
   consumed=[Path(s.strip()) for s in result.stdout.decode().splitlines()if s.startswith('    ') and Path(s.strip()).is_file()]
   assert any(p.resolve()==(folder/'connected_component.cpp').resolve()for p in consumed) and any(p.resolve()==(folder/'native_main.cpp').resolve()for p in consumed)
   for p in consumed:pin(p)
   counts['current_compiler_dependency_paths']+=len(consumed)
  pin(R/'tools/m4-mfc1168-native/run_connected_fixture.py');pin(__file__);pin(sys.executable)
  q=out/'whole-link-observations.json';q.write_text(json.dumps(links,indent=2)+'\n');pin(q)
  for p,h in pins.items():assert sha(p)==h,p
  passed=True
 except BaseException:
  (out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Independent first positive connected14 prefix prelaunch only; source/provider/full endpoint/refusal/131 acceptance remain separate',build_sha256=BSHA,preparation_sha256=PSHA,
              counts=dict(counts),files=pins,archive_reader_opened=False,worker_launched=False,source_AFTER_seed=False,initializer_credit=0,
              whole_new_manager_CRT_TIB_endpoint_observations=False,requires=['Actual positive source/State/resource comparison','Whole added-domain endpoints','Connected refusals','Full persistent131 final acceptance'])
  q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(q),counts=dict(counts),files=len(pins))))
if __name__=='__main__':main(sys.argv[1])
