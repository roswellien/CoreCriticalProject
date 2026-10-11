"""Attribute original6's two-file real system provider isolation additively."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
p=Path(__file__).with_name('review_version_original_prelaunch_v8.py')
scope={'__file__':str(p),'__name__':'materialize_VERSION_isolation_review'}
exec(compile(p.read_text(),str(p),'exec'),scope)
t=scope['t']
for a,b in [
 ('7718e1cadfb8619b504ee5246ea9ade5d2e60b4ea89e11537db29ec04cf70529','37e51c84827c8556d7c3ba96d4834bd809e0a85ae767ed4b30b100e178b5fad6'),
 ('fd5caff7e35d7ab8e6a10e9d00f41c4ca7ddfcee7ee9261692f54e1fad68a292','cbe606c38282b970b3977305a030744f450923b928140d3f57b3502d7e36d4b7'),
 ('original-preparation-r4','original-preparation-r6'),('original-build-r4','original-build-r6'),
 ('original-controller-preparation-r1','original-controller-preparation-r3'),
 ('d1b1faf63ff581b3141fe9ddc0032a8abd315e47440406d16ec96341d3571246','d27b2f1b1391dbe56647d8c593ad1a83885ed887ec9f486e67ba727d3ed600bb'),
 ('run_original_v1.py','run_original_v3.py'),('90e05b415bf8925b8d9aa17ec9b55deb694c09b91e6bd6a261408dcf1b05369f','e6cafcbe42f728ba8e68913fd01f991061a3bb4335786fa7483c286b04e59e5d')]:
 assert a in t,a;t=t.replace(a,b)
a="  oldfolder=R/'reports/m4-cosine-original/prefix-preparation-r2';old=read(oldfolder/'report.json',prep['parent_preparation_sha256'])\n  for row in prep['source_relations']:assert pin(row['parent'],row['sha256']).read_bytes()==pin(row['child'],row['sha256']).read_bytes();counts['whole_retained_original_inputs']+=1"
assert t.count(a)==1
t=t.replace(a,r'''  oldfolder=R/'reports/m4-cosine-original/prefix-preparation-r2';old=read(oldfolder/'report.json','aac031ac5949fa6fb1698c63130aa2652f352e521e140c02034fcb5df9f492df')
  changed=[]
  for row in prep['source_relations']:
   before=pin(row['parent'],row.get('parent_sha256',row['sha256'])).read_bytes();after=pin(row['child'],row['sha256']).read_bytes()
   if row['unchanged']:assert before==after;counts['whole_retained_original_inputs']+=1
   else:assert Path(row['child']).name=='version_provider_isolation.hpp';changed.append(row)
  assert len(changed)==1 and counts['whole_retained_original_inputs']==17
  former=read(R/'reports/m4-version-source/original-preparation-r4/report.json','7718e1cadfb8619b504ee5246ea9ade5d2e60b4ea89e11537db29ec04cf70529')
  assert prep['source_spans']==former['source_spans'] and prep['pack_sha256']==former['pack_sha256'] and prep['source_return_observer_spans']==former['source_return_observer_spans']
  for n in ['reference_x86.asm','preserve_x86.asm','nullfree_observer_x86.asm','vtable_observer_x86.asm','lockit_observer_x86.asm','fs_observer_x86.asm','version_return_x86.asm','version_observer.hpp','pages.bin','protocol.hpp']:
   assert pin(folder/n).read_bytes()==pin(R/'reports/m4-version-source/original-preparation-r4'/n).read_bytes();counts['whole_unchanged_original4_inputs']+=1
  before=text(R/'reports/m4-version-source/original-preparation-r4/reference.cpp');after=text(folder/'reference.cpp')
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
''')
a="'LoadLibraryExW(L\"version.dll\",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32)'"
assert t.count(a)==1;t=t.replace(a,"'version_load_isolated_provider();'")
a="  game=P.PEImage("
at=t.index(a)
extra=r'''  import xml.etree.ElementTree as ET
  provider_dir=Path(prep['isolated_system_provider_dir'])
  manifest=pin(provider_dir/'provider.manifest','ccc8b14faadb131b7e428fc531c22d354db3803973d6aa83283450e8aa275260')
  root=ET.fromstring(manifest.read_bytes());ns='{urn:schemas-microsoft-com:asm.v1}'
  assert root.tag==ns+'assembly' and sorted(x.attrib for x in root.findall(ns+'file'))==sorted([{'name':'version.dll'},{'name':'msvcrt.dll'}],key=lambda x:x['name'])
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
'''
t=t[:at]+extra+t[at:]
a="pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v7.py');"
assert t.count(a)==1;t=t.replace(a,"pin(R/'tools/m4-tree-review/review_version_original_prelaunch_v8.py');"+a)
exec(compile(t,str(Path(__file__)),'exec'),globals())
