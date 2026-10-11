"""Isolate byte-identical current Windows VERSION/CRT providers; build only."""
from pathlib import Path
import hashlib,json,shutil,sys
R=Path(__file__).resolve().parents[2]
T=Path(__file__).resolve().parent
OLD=R/'reports/m4-version-source/original-preparation-r4'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def once(s,a,b):need(s.count(a)==1,'Exact isolated loader seam '+a);return s.replace(a,b,1)
def main(name):
 out=R/'reports/m4-version-source'/name;need(not out.exists(),'Fresh original5 provider isolation preparation');pins={}
 def pin(p,h=None):
  p=Path(p).resolve();need(p.suffix.lower()not in('.mwb','.zip'),'Preparation does not read archives');v=sha(p);need(h is None or v==h,'Exact physical provider preparation input '+str(p));pins[str(p)]=v;return p
 old=json.loads(pin(OLD/'report.json','7718e1cadfb8619b504ee5246ea9ade5d2e60b4ea89e11537db29ec04cf70529').read_bytes());need(old['passed'],'Frozen original4 lineage')
 for p,h in old['files'].items():pin(p,h)
 failed=R/'reports/m4-version-source/original-execution-r1/report.json'
 if failed.exists():pin(failed)
 sys.path.insert(0,str(R/'tools/analysis'));from pe import PEImage
 syv=pin(Path('C:/Windows/SysWOW64/version.dll'));syc=pin(Path('C:/Windows/SysWOW64/msvcrt.dll'));legacy=pin(R/'local/mw3-staged/Shared_DLLs/MSVCRT.DLL','2d5670881a6d13a100e37da297f6eeb876f68b63073a28eb5d650625c60f9bf7')
 v=PEImage(syv.read_bytes());c=PEImage(syc.read_bytes());o=PEImage(legacy.read_bytes());imports=[x for x in v.imports()if x['library'].lower()=='msvcrt.dll'];need(len(imports)==1,'One physical VERSION CRT import descriptor');symbols=imports[0]['symbols'];need(len(symbols)==8 and all('name'in x for x in symbols),'Whole eight named VERSION CRT imports')
 oldnames={n for e in o.exports()for n in e['names']};sysnames={n for e in c.exports()for n in e['names']};missing=[x['name']for x in symbols if x['name']not in oldnames];need(missing==['_except_handler4_common']and all(x['name']in sysnames for x in symbols),'Exact incompatible legacy CRT export and complete system CRT exports')
 out.mkdir(parents=True);provider=out/'system-version32';provider.mkdir();shutil.copyfile(syv,provider/'version.dll');shutil.copyfile(syc,provider/'msvcrt.dll');pin(provider/'version.dll',sha(syv));pin(provider/'msvcrt.dll',sha(syc))
 manifest=provider/'provider.manifest';manifest.write_text('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">\n <assemblyIdentity type="win32" name="MW34.Version32.IsolatedProvider" version="1.0.0.0" processorArchitecture="x86"/>\n <file name="version.dll"/>\n <file name="msvcrt.dll"/>\n</assembly>\n');pin(manifest)
 copied=[]
 for p in OLD.iterdir():
  if p.suffix.lower()in('.cpp','.hpp','.asm')or p.name in('pages.bin','CMakeLists.txt','fs-hook-bindings.json'):
   q=out/p.name;shutil.copyfile(p,q);copied.append(dict(parent=str(p),child=str(q),unchanged=True,sha256=sha(q)))
 literal=lambda p:'L'+json.dumps(str(p.resolve()).replace('\\','/'))
 bindings=','.join('{'+str(x['iat_rva'])+',"'+x['name']+'"}'for x in symbols)
 header='''#pragma once
// Current Windows DLLs are unmodified copies. The context redirects only their
// two filenames; it is inactive before any original source instruction runs.
static HMODULE version_isolated_crt{};
static std::array<std::uint64_t,8*5>version_provider_IAT{};
static std::array<std::uint64_t,10>version_provider_setup{};
static std::array<std::vector<unsigned char>,2>version_context_sections{};
static std::wstring version_isolated_VERSION_path,version_isolated_CRT_path;
static void version_load_isolated_provider(){
 const std::filesystem::path manifest_path(@MANIFEST@),VERSION_path(@VERSION@),CRT_path(@CRT@);
 require(sha256(read(manifest_path.string().c_str(),65536))=="@MANIFESTSHA@","Exact private VERSION activation manifest");
 require(sha256(read(VERSION_path.string().c_str(),32*1024*1024))=="@VERSIONSHA@"&&sha256(read(CRT_path.string().c_str(),32*1024*1024))=="@CRTSHA@","Whole byte-identical Windows32 VERSION and CRT input files");
 auto*old=GetModuleHandleW(L"msvcrt.dll");require(reinterpret_cast<unsigned>(old)==0x78000000&&!GetProcAddress(old,"_except_handler4_common"),"Actual legacy CRT basename and missing modern dependency before isolation");
 ACTCTXW description{};description.cbSize=sizeof(description);description.lpSource=manifest_path.c_str();const auto context=CreateActCtxW(&description);const auto create_error=GetLastError();
 if(context==INVALID_HANDLE_VALUE)throw std::runtime_error("CreateActCtx VERSION provider error "+std::to_string(create_error));
 struct Context {HANDLE h;ULONG_PTR cookie{};bool active{};~Context(){if(active)DeactivateActCtx(0,cookie);ReleaseActCtx(h);}}scope{context};
 if(!ActivateActCtx(context,&scope.cookie))throw std::runtime_error("ActivateActCtx VERSION provider error "+std::to_string(GetLastError()));scope.active=true;
 const std::array<const wchar_t*,2>names{L"version.dll",L"msvcrt.dll"};
 for(unsigned i=0;i<2;++i){ACTCTX_SECTION_KEYED_DATA key{};key.cbSize=sizeof(key);require(FindActCtxSectionStringW(0,nullptr,ACTIVATION_CONTEXT_SECTION_DLL_REDIRECTION,names[i],&key)&&key.lpData&&key.ulLength&&key.ulLength<=4096,"Actual isolated activation DLL redirection record");auto*b=static_cast<const unsigned char*>(key.lpData);version_context_sections[i].assign(b,b+key.ulLength);}
 version_isolated_crt=LoadLibraryExW(CRT_path.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);const auto CRT_error=GetLastError();
 if(!version_isolated_crt)throw std::runtime_error("Actual isolated system32 CRT load error "+std::to_string(CRT_error));
 version_module=LoadLibraryExW(VERSION_path.c_str(),nullptr,LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR|LOAD_LIBRARY_SEARCH_SYSTEM32);const auto VERSION_error=GetLastError();
 if(!version_module)throw std::runtime_error("Actual isolated system32 VERSION load error "+std::to_string(VERSION_error));
 version_isolated_CRT_path=version_module_path(version_isolated_crt);version_isolated_VERSION_path=version_module_path(version_module);
 require(!_wcsicmp(version_isolated_CRT_path.c_str(),CRT_path.c_str())&&!_wcsicmp(version_isolated_VERSION_path.c_str(),VERSION_path.c_str())&&version_isolated_crt!=old,"Actual loaded private system32 DLL paths and distinct legacy CRT owner");
 require(sha256(read(std::filesystem::path(version_isolated_CRT_path).string().c_str(),32*1024*1024))=="@CRTSHA@"&&sha256(read(std::filesystem::path(version_isolated_VERSION_path).string().c_str(),32*1024*1024))=="@VERSIONSHA@","Actual loaded providers retain whole Windows physical identity");
 struct Binding {unsigned RVA;const char*name;};const std::array<Binding,8>bindings{{@BINDINGS@}};
 for(unsigned i=0;i<bindings.size();++i){const auto&b=bindings[i];const auto named=GetProcAddress(version_isolated_crt,b.name);const auto actual=*reinterpret_cast<unsigned*>(reinterpret_cast<unsigned>(version_module)+b.RVA);require(named&&actual==reinterpret_cast<unsigned>(named),"Every genuine loaded VERSION CRT import resolves to the isolated actual system export");version_provider_IAT[5*i]=b.RVA;version_provider_IAT[5*i+1]=actual;version_provider_IAT[5*i+2]=reinterpret_cast<unsigned>(named);version_provider_IAT[5*i+3]=reinterpret_cast<unsigned>(version_isolated_crt);version_provider_IAT[5*i+4]=reinterpret_cast<unsigned>(old);}
 require(DeactivateActCtx(0,scope.cookie),"Private VERSION provider activation closed before source execution");scope.active=false;
 require(reinterpret_cast<unsigned>(GetModuleHandleW(L"msvcrt.dll"))==0x78000000&&*reinterpret_cast<unsigned*>(0x5f49814c)==0x780012b3&&*reinterpret_cast<unsigned*>(0x5f498148)==0x78001390,"Original legacy CRT basename and genuine MFC imports preserved after provider isolation");
 version_provider_setup={1,reinterpret_cast<unsigned>(version_module),reinterpret_cast<unsigned>(version_isolated_crt),reinterpret_cast<unsigned>(old),create_error,CRT_error,VERSION_error,8,2,1};
}
static void version_emit_isolated_provider(mw34::capture_direct::Writer&out){
 out.append("version-provider/setup.bin",version_provider_setup.data(),sizeof(version_provider_setup));out.append("version-provider/CRT-IAT.bin",version_provider_IAT.data(),sizeof(version_provider_IAT));
 out.append("version-provider/VERSION-path.bin",version_isolated_VERSION_path.data(),version_isolated_VERSION_path.size()*2);out.append("version-provider/CRT-path.bin",version_isolated_CRT_path.data(),version_isolated_CRT_path.size()*2);
 for(unsigned i=0;i<2;++i)out.append("version-provider/context-"+std::to_string(i)+".bin",version_context_sections[i].data(),version_context_sections[i].size());
}
'''
 for a,b in {'@MANIFEST@':literal(manifest),'@VERSION@':literal(provider/'version.dll'),'@CRT@':literal(provider/'msvcrt.dll'),'@MANIFESTSHA@':sha(manifest),'@VERSIONSHA@':sha(syv),'@CRTSHA@':sha(syc),'@BINDINGS@':bindings}.items():header=header.replace(a,b)
 (out/'version_provider_isolation.hpp').write_text(header)
 ref=(out/'reference.cpp').read_text();before=ref;ref=once(ref,'#include "version_observer.hpp"','#include "version_observer.hpp"\n#include "version_provider_isolation.hpp"');ref=once(ref,'version_module=LoadLibraryExW(L"version.dll",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);require(version_module,"Actual system original32 VERSION provider");','version_load_isolated_provider();');ref=once(ref,'mw34::capture_direct::Writer out(argv[4],std::move(version_transport_options));','mw34::capture_direct::Writer out(argv[4],std::move(version_transport_options));version_emit_isolated_provider(out);');(out/'reference.cpp').write_text(ref)
 for x in copied:
  if Path(x['child']).name=='reference.cpp':x.update(unchanged=False,parent_sha256=sha(OLD/'reference.cpp'),sha256=sha(out/'reference.cpp'),exact_changes=['one new isolation-header include','one setup loader call replacement','one provider proof emission'])
 c=json.loads((OLD/'contracts.json').read_bytes());c.update(byte_identical_system32_provider_isolation=True,private_activation_context_closed_before_source=True,legacy_CRT_MFC_import_guards_retained=True,all_VERSION_CRT_imports_actual_named_exports=True,provider_DLLs_unmodified=True);(out/'contracts.json').write_text(json.dumps(c,indent=2)+'\n')
 diagnosis=dict(original4_failed_before_source=True,physical_VERSION32=str(syv),physical_system_CRT32=str(syc),physical_legacy_CRT=str(legacy),VERSION_CRT_imports=symbols,unavailable_legacy_imports=missing,system_CRT_has_all_imports=True,VERSION_exports=[e for e in v.exports()if any(n in e['names']for n in ('GetFileVersionInfoSizeA','GetFileVersionInfoA','VerQueryValueA'))],loading_VERSION_first_would_change_existing_legacy_CRT_loader_lineage=True,solution='Unmodified current system DLL copies in a private two-file activation context; actual Windows loader/IAT proof; context closed before source execution',source_guards_removed=False,providers_executed=False)
 (out/'provider-dependency-proof.json').write_text(json.dumps(diagnosis,indent=2)+'\n');pin(__file__);pin(R/'tools/analysis/pe.py')
 for p in out.iterdir():
  if p.is_file():pin(p)
 report={k:old[k]for k in ('source_spans','sparse_pack_pages','pack_sha256','original_sequences','original_roots','original_phases','record_bytes','ordinary_pages','extra_source_code_pages','source_return_observer_spans','explicit_writer_reports_root','required_process_cwd','conditional_branch_relocation','actual_API_hardware_stdcall_consumption_guard','whole_actual_GPR_flags_FX_ENV_projection_guard','immediate_post_API_LastError_guard','actual_typed_version_provider')}
 report.update(passed=True,scope='Original5 preserves original4 whole source/ABI guards and isolates byte-identical real32 system VERSION CRT dependencies; prepare/build only',parent_preparation_sha256=sha(OLD/'report.json'),source_relations=copied,isolated_system_provider_dir=str(provider),provider_DLLs_unmodified=True,actual_legacy_MFC_CRT_lineage_retained=True,isolated_context_closed_before_source=True,all_system_CRT_IAT_bindings=8,source_after_seed=False,original_executed=False,native_executed=False,archive_reader_opened=False,initializer_credit=0,files=pins)
 q=out/'report.json';q.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=True,path=str(q),sha256=sha(q),provider_directory=str(provider),executed=False)))
if __name__=='__main__':main(sys.argv[1])
