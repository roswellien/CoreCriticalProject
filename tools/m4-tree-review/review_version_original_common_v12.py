"""Physical one-root x86 VERSION observer admission; never run/read a capture."""
from pathlib import Path
from collections import Counter
import hashlib,importlib.util,json,re,struct,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
PH='fafc198f6a20184cf3cc3bec67710e8f22eb7408789568eacefb73c90163d48f'
BH='14e3040ee8aa42f014a07d042bf3bab06d3565006b9ce5a2dfb39cf952893b52'
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(name):
 out=R/'reports/m4-tree-review'/name;assert not out.exists();out.mkdir();pins={};counts=Counter();links=[];passed=False;worker_sha=None
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip','.iso');v=sha(p);assert h is None or v==h,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def read(p,h=None):return json.loads(pin(p,h).read_bytes())
 def text(p):return pin(p).read_text(encoding='utf-8-sig')
 def module(p,n):
  s=importlib.util.spec_from_file_location(n,pin(p));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
 def sparse(p,h):
  raw=pin(p,h).read_bytes();n=struct.unpack_from('<I',raw,8)[0];assert raw[:8]==b'MW4J124P'and len(raw)==12+4104*n
  rows={struct.unpack_from('<I',raw,12+4104*i)[0]:(struct.unpack_from('<I',raw,16+4104*i)[0],raw[20+4104*i:4116+4104*i])for i in range(n)};assert len(rows)==n;return rows
 try:
  folder=R/'reports/m4-version-source/original-preparation-r8';bf=R/'reports/m4-version-source/original-build-r8'
  prep=read(folder/'report.json',PH);build=read(bf/'build.json',BH);assert prep['passed']and build['passed']and build['preparation_sha256']==PH
  for d in(prep,build):
   for p,h in d['files'].items():pin(p,h)
  assert(prep['original_sequences'],prep['original_roots'],prep['original_phases'],prep['sparse_pack_pages'],prep['record_bytes'])==(1,1,1,121,356992)
  assert not prep['original_executed']and not prep['archive_reader_opened']and prep['initializer_credit']==0
  assert prep['required_process_cwd']==str((R/'MW3').resolve())and prep['explicit_writer_reports_root']==str((R/'reports').resolve())
  oldfolder=R/'reports/m4-cosine-original/prefix-preparation-r2';old=read(oldfolder/'report.json','aac031ac5949fa6fb1698c63130aa2652f352e521e140c02034fcb5df9f492df')
  correction=read(R/'reports/m4-version-source/original6-relation-correction-r1/report.json','298b8ba1c253a3bd82e514757112dc25199ebfe6d8962d69806421d1a09cbac7');assert correction['passed']
  Common=module(R/'tools/m4-version-source/review_common_source_bridge.py','whole_common_source_bridge');common=Common.review(pin,read,counts)
  changed=[]
  for row in common['original_parent']['source_relations']:
   if Path(row['child']).name=='contracts.json':
    before=read(row['parent'],'fae34c1c41a7a4832488300a93bba234fea192fa53721077fb276d6cd8b3ec36')
    after=read(row['child'],'6e5ed33530b2dad06f0424ba86ea7b8193a3121460a900f8f11dbefb75bd5a4f')
    extra={'actual_loaded_and_expected_provider_whole_file_IDs':True,'independent_same_physical_provider_file_equivalence':True,'raw_loaded_provider_paths_retained':True}
    assert set(after)-set(before)==set(extra) and after==dict(before,**extra)
    counts['explicit_corrected_contracts_whole_file_relation']+=1
    continue
   before=pin(row['parent'],row.get('parent_sha256',row['sha256'])).read_bytes();after=pin(row['child'],row['sha256']).read_bytes()
   if row['unchanged']:assert before==after;counts['whole_retained_original_inputs']+=1
   else:assert Path(row['child']).name=='version_provider_isolation.hpp';changed.append(row)
  assert len(changed)==1 and counts['whole_retained_original_inputs']==16 and counts['explicit_corrected_contracts_whole_file_relation']==1
  former=read(R/'reports/m4-version-source/original-preparation-r4/report.json','7718e1cadfb8619b504ee5246ea9ade5d2e60b4ea89e11537db29ec04cf70529')
  assert prep['source_spans']==former['source_spans'] and prep['pack_sha256']==former['pack_sha256'] and prep['source_return_observer_spans']==former['source_return_observer_spans']
  for n in ['reference_x86.asm','preserve_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm','fs_observer_x86.asm','version_observer_x86.asm','version_observer.hpp','pages.bin','protocol.hpp']:
   assert pin(folder/n).read_bytes()==pin(R/'reports/m4-version-source/original-preparation-r4'/n).read_bytes();counts['whole_unchanged_original4_inputs']+=1
  before=text(R/'reports/m4-version-source/original-preparation-r4/reference.cpp');after=common['original_parent_CPP']
  include='#include "version_provider_isolation.hpp"\n';loader='version_load_isolated_provider();';emit='version_emit_isolated_provider(out);'
  assert after.count(include)==after.count(loader)==after.count(emit)==1
  reduced=after.replace(include,'').replace(loader,'version_module=LoadLibraryExW(L"version.dll",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);require(version_module,"Actual system original32 VERSION provider");').replace(emit,'')
  assert reduced==before,'Whole original4 CPP preserved outside isolated loader and observational setup export'
  counts['whole_original4_reference_inversion']=1
  header=text(folder/'version_provider_isolation.hpp')
  for token in ['CreateActCtxW(&description)','ActivateActCtx(context,&scope.cookie)','ACTIVATION_CONTEXT_SECTION_DLL_REDIRECTION','key.ulLength<=4096','LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32','version_isolated_crt!=old','version_provider_file_IDs[0]==version_provider_file_IDs[1]','version_provider_file_IDs[2]==version_provider_file_IDs[3]','std::filesystem::equivalent','GetFileInformationByHandle(f.h,&i)','i.dwVolumeSerialNumber,i.nFileIndexHigh,i.nFileIndexLow,i.nFileSizeHigh,i.nFileSizeLow,i.ftLastWriteTime.dwHighDateTime,i.ftLastWriteTime.dwLowDateTime','named&&actual==reinterpret_cast<unsigned>(named)','DeactivateActCtx(0,scope.cookie)','scope.active=false','0x5f49814c)==0x780012b3','0x5f498148)==0x78001390','version-provider/file-IDs.bin','version-provider/CRT-IAT.bin']:
   assert token in header,token
  assert header.index('DeactivateActCtx(0,scope.cookie),')<header.index('version_provider_setup={')
  assert prep['actual_provider_file_identity_bytes']==224 and prep['provider_DLLs_unmodified'] and prep['actual_legacy_MFC_CRT_lineage_retained'] and prep['isolated_context_closed_before_source']

  P=module(R/'tools/analysis/pe.py','version32_pe');C=module(R/'tools/m4-tree-review/review_hypot_trace_prelaunch_v7.py','version32_coff')
  import xml.etree.ElementTree as ET
  provider_dir=Path(prep['isolated_system_provider_dir'])
  manifest=pin(provider_dir/'provider.manifest','ccc8b14faadb131b7e428fc531c22d354db3803973d6aa83283450e8aa275260')
  root=ET.fromstring(manifest.read_bytes());ns='{urn:schemas-microsoft-com:asm.v1}'
  assert root.tag==ns+'assembly' and sorted([x.attrib for x in root.findall(ns+'file')],key=lambda x:x['name'])==sorted([{'name':'version.dll'},{'name':'msvcrt.dll'}],key=lambda x:x['name'])
  identity=root.find(ns+'assemblyIdentity');assert identity is not None and identity.attrib=={'type':'win32','name':'MW34.Version32.IsolatedProvider','version':'1.0.0.0','processorArchitecture':'x86'}
  providers={}
  for n,h in [('version.dll','4f66b88731e84be8e1545eefc589a79e701cca426ce916e4ac9322e60ea9680b'),('msvcrt.dll','23a918921c545140d189ce6dc68590bacdeb0ab2f3e3a9a2d722c5aff45ce64f')]:
   original=pin(Path('C:/Windows/SysWOW64')/n,h).read_bytes();copied=pin(provider_dir/n,h).read_bytes();assert copied==original
   providers[n]=P.PEImage(copied);assert providers[n].machine==0x14c;counts['whole_unmodified_system32_provider_files']+=1
  imports=[x for x in providers['version.dll'].imports()if x['library'].casefold()=='msvcrt.dll'];assert len(imports)==1
  pairs=[(x['iat_rva'],x['name'])for x in imports[0]['symbols']]
  expected=[(20796,'_vsnprintf'),(20800,'_vsnwprintf'),(20804,'_XcptFilter'),(20808,'_amsg_exit'),(20812,'free'),(20816,'malloc'),(20820,'_initterm'),(20824,'_except_handler4_common')]
  assert pairs==expected
  exports=providers['msvcrt.dll'].exports()
  for rva,n in pairs:
   assert '{'+str(rva)+',"'+n+'"}'in header
   match=[x for x in exports if n in x['names']];assert len(match)==1 and 'forwarder'not in match[0];counts['physical_system_VERSION_CRT_import_export_bindings']+=1
  legacy=P.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7').read_bytes())
  assert not any('_except_handler4_common'in x['names']for x in legacy.exports());counts['physical_legacy_missing_modern_export']=1
  game=P.PEImage(pin(R/'MW3/Mech3.exe','95bc2c114c9b2e5c5ada8e40ca78cc79470f862e45313ffad0d1e8e6d4d916bf').read_bytes())
  cp=P.PEImage(pin(R/'local/mw3-staged/Shared_DLLs/MSVCP50.DLL','91cd76f9fa3b25008decb12c005c194bdf66c8d6526a954de7051bec9aae462a').read_bytes())
  def physical(image,pc,n):start,_=image.rva_range(pc-image.image_base,n);return image.data[start:start+n]
  pack=sparse(folder/'pages.bin',prep['pack_sha256']);oldpack=sparse(oldfolder/'pages.bin',old['pack_sha256']);assert len(pack)==121 and len(oldpack)==119
  native=read(R/'reports/m4-version-source/preparation-r2/report.json','137c214307a28b0e120b600ee53f14fcfacac0a72a7ef64b437178f3b3b17c75')
  source=read(R/'reports/m4-version-source/preparation-r2/source-rows.json');assert len(source)==109
  expected={row['pc']+i:b for row in source for i,b in enumerate(bytes.fromhex(row['bytes']))}
  for pc,value in expected.items():assert pack[pc&~4095][1][pc&4095]==value
  for pc,(rights,data)in pack.items():
   assert pc%4096==0 and rights in(0,1,2)and len(data)==4096
   if pc in oldpack:
    assert rights==oldpack[pc][0]
    for n,(before,after)in enumerate(zip(oldpack[pc][1],data)):
     if before!=after:assert rights==1 and before==0xcc and expected.get(pc+n)==after;counts['exact_new_source_overlay_bytes']+=1
   else:
    assert pc in(0x4af000,0x4ea000)and rights==1
    for n,value in enumerate(data):assert value==expected.get(pc+n,0xcc)
   counts['whole_sparse_pack_pages']+=1
  for row in prep['source_spans']:
   image=cp if row['origin']else game;data=physical(image,row['pc'],row['size']);assert image.data[row['image_offset']:row['image_offset']+row['size']]==data
   if not row['origin']:
    for n,value in enumerate(data):assert pack[(row['pc']+n)&~4095][1][(row['pc']+n)&4095]==value
   counts['whole_physical_source_spans']+=1
  assert struct.unpack('<I',physical(game,0x5e0140,4))[0]==0x4af240 and physical(game,0x5e867c,10)==b'mech3.exe\0'and physical(game,0x5e8664,2)==b'\\\0'
  seams=[(0x4af113,bytes.fromhex('85c08907747e'),0x4af197,0x4af119),(0x4af131,bytes.fromhex('85c0750f8bcf'),0x4af144,0x4af137),(0x4af16c,bytes.fromhex('85c074278b4c2414'),0x4af197,0x4af174)]
  for pc,raw,target,fall in seams:assert physical(game,pc,len(raw))==raw;counts['whole_conditional_return_spans']+=1
  asm=text(folder/'version_observer_x86.asm')
  regs=('eax','ecx','edx','ebx','esp','ebp','esi','edi')
  for i,label in enumerate(('size','info','query')):
   prefix='version_'+label;argc=2 if i==0 else 4;ret=seams[i][0]
   for side in('entry','return'):
    block=asm[asm.index(prefix+'_'+side+' PROC'):asm.index(prefix+'_'+side+' ENDP')]
    for j,reg in enumerate(regs):assert ' mov DWORD PTR version_cpu[%d],%s'%(4*j,reg)in block
    for j,reg in enumerate(regs):
     if reg!='esp':assert ' mov %s,DWORD PTR version_cpu[%d]'%(reg,4*j)in block
    for token in ('mov esp,mixed_host_esp','pushfd','pop DWORD PTR version_cpu[32]','fxsave version_fx','fnstenv version_env','fldenv version_env','call version_observe','fxrstor version_fx','push DWORD PTR version_cpu[32]','popfd','mov esp,DWORD PTR version_cpu[16]'):assert token in block,token
    if side=='entry':
     actual=' call DWORD PTR version_targets[%d]'%(i*4);assert block.count(actual)==1
     for arg in range(argc,0,-1):assert ' push DWORD PTR [eax+%d]'%(4*arg)in block
     for token in ('mov eax,DWORD PTR fs:[34h]','mov DWORD PTR fs:[34h],eax','mov version_API_before_error,eax','mov version_API_after_error,eax','fxsave version_hardware[48]','fnstenv version_hardware[560]','fldenv version_hardware[560]','fxsave version_hardware[640]','fnstenv version_hardware[1152]','fldenv version_hardware[1152]','lea eax,[eax+%d]'%(4*(argc+1)),'jmp DWORD PTR version_return_PCs[%d]'%(4*i)):assert token in block,token
     assert block.index('mov DWORD PTR fs:[34h],eax')<block.index(actual)<block.index('mov version_API_after_error,eax')<block.rindex('call version_observe')
    counts['complete_source_and_API_wrapper_bodies']+=1
  assert 'test eax,eax\n mov DWORD PTR [edi],eax\n jnz version_size_fallthrough\n jmp DWORD PTR version_branch_targets[0]'in asm
  assert 'test eax,eax\n jz version_info_fallthrough\n jmp DWORD PTR version_branch_targets[4]'in asm and 'version_info_fallthrough:\n mov ecx,edi\n jmp DWORD PTR version_return_continues[4]'in asm
  assert 'test eax,eax\n jz version_query_failure\n mov ecx,DWORD PTR [esp+14h]\n jmp DWORD PTR version_return_continues[8]'in asm and 'version_query_failure:\n jmp DWORD PTR version_branch_targets[8]'in asm
  observer=text(folder/'version_observer.hpp');original_header=text(R/'tools/m4-version-source/original_observer_v3.hpp')
  seam=' unsigned short version_DS{}';assert original_header.count(seam)==1
  original_header=original_header.replace(seam,' unsigned version_return_PCs[3]{0x4af113,0x4af131,0x4af16c},version_frame{};\n'+seam)
  assert observer==original_header
  for token in ('sizeof(Version32HardwareSide)==592&&sizeof(Version32Hardware)==1184','ha.cpu.esp==hb.cpu.esp+4*(version_argc[API]+1)','ha.cpu.ebx==hb.cpu.ebx','ha.cpu.ebp==hb.cpu.ebp','ha.cpu.esi==hb.cpu.esi','ha.cpu.edi==hb.cpu.edi','version_cpu.flags==ha.cpu.flags','!std::memcmp(version_fx,ha.fx,512)','!std::memcmp(version_env,ha.env,28)','error==version_API_after_error','version_incoming_error==version_API_before_error','capacity==(*allocation_owner)[5]','output-pointer<version_dword(0x60b198)','length<=version_dword(0x60b198)-(output-pointer)','version_same(entry.identity,v.identity)&&version_same(entry.file,v.file)','v.sha==image_sha','GetProcAddress(version_module,version_names[index])','region.Type==MEM_IMAGE','std::memcpy(v.entry.data(),reinterpret_cast<void*>(target),64)'):assert token in observer,token
  cpp=text(folder/'reference.cpp')
  for token in ('version_transport_options.reports_root=std::filesystem::path("'+str((R/'reports').resolve()).replace('\\','/')+'")','Writer out(argv[4],std::move(version_transport_options))','version_load_isolated_provider();','version_count=version_error=version_allocation_count=0','Whole actual original VERSION return seam raw bytes','Whole original VERSION return bytes restored','version_emit(out,','require(!version_error','Actual original source onexit4AF270 publication','manual-version-MFC825.bin','Entire declared VERSION observer patch bytes'):assert token in cpp,token
  protocol=text(folder/'protocol.hpp');assert protocol==text(oldfolder/'protocol.hpp').replace('sequences=6, roots=1','sequences=1, roots=1')
  spec=text(folder/'spec.hpp')
  for field,value in [('entries',0x4af240),('table_slots',0x5e0140)]:assert 'std::array<std::uint32_t,1> '+field+'{'+hex(value)+'}'in spec
  worker_sha=build['worker_sha256'];worker=P.PEImage(pin(build['worker'],worker_sha).read_bytes());assert(worker.machine,worker.image_base)==(0x14c,0x18000000)
  symbols_by_object={}
  for obj in build['objects']:
   q=pin(obj['path'],obj['sha256']);sy,se=C.coff(q.read_bytes());symbols_by_object[q.name]=(sy,se)
   if q.name in('reference.obj','capture_direct_v3.obj'):continue
   exe=[i for i,section in se.items()if section['flags']&0x20000000 and section['bytes']];assert len(exe)==1
   fake={0:dict(name=q.stem+' whole assembly section',value=0,section=exe[0],type=32,storage=2)}
   proof=C.linked_function(worker,fake,se,fake[0]['name']);links.append(proof);counts['whole_linked_assembly_sections']+=1;counts['whole_linked_assembly_bytes']+=proof['bytes']
  sy,se=symbols_by_object['reference.obj'];names=[v['name']for v in sy.values()if v['section']>0 and v['type']==32 and(v['name']in('_main','_registry_observe_allocation','_version_observe','_version_note_allocation','_nullfree_observe','_fs_observe_before','_fs_observe_after','_vtable_observe','_lockit_observe')or (v['name'].startswith('?version_')or '@m4_version_common@mw34@@'in v['name'])and not v['name'].startswith('?version_dword@@'))]
  assert {'_main','_registry_observe_allocation','_version_observe','_version_note_allocation','_nullfree_observe','_fs_observe_before','_fs_observe_after','_vtable_observe','_lockit_observe'}<=set(names)
  for section in se.values():
   if section['flags']&0x20000000:assert not any(r['symbol']['name'].startswith('?version_dword@@')for r in section['relocations'])
  counts['inlined_DWORD_accessor_no_executable_references']=1
  inlined=[n for n in names if n.startswith('?version_same@@')]
  assert len(inlined)==2
  for n in inlined:
   refs=[(section,r)for section in se.values()for r in section['relocations']if r['symbol']['name']==n]
   assert refs and all(not section['flags']&0x20000000 and r['type']in(7,10)for section,r in refs)
  names=[n for n in names if n not in inlined];counts['inlined_identity_comparisons_no_executable_references']=len(inlined)
  for n in names:links.append(C.linked_function(worker,sy,se,n));counts['whole_linked_version_CPP_functions']+=1
  targets={}
  for proof in links:
   for row in proof['relocations']:
    if 'actual_symbol_address'not in row or row['symbol_section']!=0:continue
    name=row['symbol'];value=row['actual_symbol_address'];assert name not in targets or targets[name]==value,(name,targets.get(name),value);targets[name]=value;counts['actual_linked_symbol_joins']+=1
  for proof in links:
   if proof['symbol']in targets:assert targets[proof['symbol']]==proof['address']
  for n,values in [('_version_return_PCs',(0x4af113,0x4af131,0x4af16c)),('_version_return_continues',(0x4af119,0x4af137,0x4af174)),('_version_branch_targets',(0x4af197,0x4af144,0x4af197))]:assert physical(worker,targets[n],12)==struct.pack('<3I',*values)
  for c in build['commands']:assert c['exit_code']==0;pin(c['argv'][0]);pin(c['stdout']);pin(c['stderr'])
  link=[c for c in build['commands']if Path(c['argv'][0]).name.lower()=='link.exe'];assert len(link)==1
  args=link[0]['argv'];assert len(args)==2 and args[1].startswith('@')
  response=pin(args[1][1:]);lines=response.read_text().splitlines();assert lines and all(line.startswith('"')and line.endswith('"')for line in lines)
  expanded=[line[1:-1]for line in lines];assert '/machine:x86'in expanded and '/base:0x18000000'in expanded and '/dynamicbase:no'in expanded
  assert all(any(str(Path(o['path']).resolve()).casefold()==str(Path(a).resolve()).casefold()for a in expanded if a.lower().endswith('.obj'))for o in build['objects'])
  mapping=text(bf/'original-worker.map');actual_map={}
  for line in mapping.splitlines():
   match=re.match(r'\s+[0-9a-fA-F]{4}:[0-9a-fA-F]{8}\s+(\S+)\s+([0-9a-fA-F]{8})\s+',line)
   if match:actual_map[match[1]]=int(match[2],16)
  for proof in links:
   if proof['symbol']in names:assert actual_map[proof['symbol']]==proof['address'];counts['actual_linker_MAP_function_joins']+=1
  for c in build['commands']:
   if Path(c['argv'][0]).name.lower()=='cl.exe':assert all(arg in c['argv']for arg in('/O2','/W4','/WX','/MD','/showIncludes'))

  for p in build['actual_compiler_headers']:pin(p);counts['actual_compiler_header_paths']+=1
  assert str((folder/'version_observer.hpp').resolve())in build['actual_compiler_headers']
  for p in build['actual_linker_libraries']:pin(p['path'],p['sha256']);counts['actual_linker_library_inputs']+=1
  controller=read(R/'reports/m4-version-source/common-controllers-preparation-r1/report.json','03dc6dd94532209fb7885d29d65278dff34bb91d8835b1c29ca0543ecefac232')
  for p,h in controller['files'].items():pin(p,h)
  pin(R/'tools/m4-version-source/run_original_common_v1.py','696bc67c1a611d896dad1b9d67380abb69d9f64eba9927926cfcaf1744757c75');pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v10.py');pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v9.py');pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v8.py');pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v7.py');pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v6.py');pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v5.py');pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v4.py');pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v3.py');pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v2.py');pin(R/'tools/m4-tree-review/review_version_original_prelaunch.py');pin(__file__);pin(sys.executable)
  for p,h in pins.items():assert sha(p)==h,p
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  q=out/'physical-links.json';q.write_text(json.dumps(links,indent=2)+'\n');pin(q)
  d=dict(passed=passed,prelaunch_justified=passed,common_caller_recipe_sha256='ca7f036b3693ef71bbbe5ce7a0af4ae3cb98755550d1bd1dcd8da955ab311281',preparation_sha256=PH,build_sha256=BH,worker_sha256=worker_sha,counts=dict(counts),files=pins,worker_launched=False,archive_reader_opened=False,initializer_credit=0,scope='One genuine version root with whole conditional source branch relocation, actual32 API hardware/LastError/owner/file observations; source equivalence and carried startup remain separate')
  q=out/'report.json';q.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(dict(passed=passed,path=str(q),sha256=sha(q),counts=dict(counts),files=len(pins))))
if __name__=='__main__':main(sys.argv[1])
