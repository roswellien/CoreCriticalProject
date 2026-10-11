"""Bind loaded whole-page inputs and actual compiler dependencies/symbols."""
from pathlib import Path
import json,re,subprocess,time
from review import ROOT,PREP,NPREP,LLVM,common,emit,machine,sha
def main(buildpath,digest,name):
 started=time.perf_counter();out,pins,pin,p,n,old=common(name);pin(__file__)
 b=json.loads(pin(buildpath,digest).read_bytes());assert b['passed']
 source=pin(NPREP/'registry_library.cpp');contract=pin(NPREP/'lockit_contract.inc');operations=pin(NPREP/'lockit_operations.inc');session=pin(NPREP/'session_impl.inc');tree_contract=pin(NPREP/'tree_contract.inc');tree_operations=pin(NPREP/'tree_operations.inc')
 assert '#include "lockit_contract.inc"'in source.read_text() and '#include "tree_contract.inc"'in source.read_text()
 assert '#include "lockit_operations.inc"'in pin(NPREP/'locale_batch_operations.inc').read_text() and '#include "tree_operations.inc"'in pin(NPREP/'locale_batch_operations.inc').read_text()
 text=contract.read_text();pages=[]
 for name,key,hkey in [('lockit_loaded_page','loaded_input_page','loaded_input_page_sha256'),('lockit_loaded_iat_page','loaded_IAT_page','loaded_IAT_page_sha256')]:
  content=re.search(r'const std::array<std::byte,4096>'+name+r'\{([^}]*(?:\}[^;]*)?)\};',text)
  # Each literal is one byte; the whole initializer is frozen physical source.
  content=text.split('const std::array<std::byte,4096>'+name+'{',1)[1].split('};',1)[0]
  raw=bytes(int(x)for x in re.findall(r'std::byte\{(\d+)\}',content));actual=pin(n[key],n[hkey]).read_bytes();assert len(raw)==4096 and raw==actual
  pages.append(dict(name=name,path=n[key],bytes=4096,sha256=n[hkey]))
 imports=re.findall(r'v.push_back\(\{(0x[0-9a-f]+),(0x[0-9a-f]+),(\d+),1,"(EnterCriticalSection|LeaveCriticalSection)",0\}\)',text)
 assert imports==[('0x7810a30b','0x78146198','1997620192','EnterCriticalSection'),('0x7810a35e','0x78146184','1997616224','LeaveCriticalSection')]
 code=operations.read_text();assert 'runtime.memory().load<unsigned>({0x78145658})!=2'in code and '::InitializeCriticalSection(&section->native)'in code
 assert 'auto bytes=lockit_source_cs_'in code and 'put(4,'in code and 'put(8,'in code and 'put(12,'in code
 assert not re.search(r'(?:store|write)[^;]*0x78145658',code)
 assert 'p.address==0x78145000?lb::lockit_loaded_page:p.address==0x78146000?lb::lockit_loaded_iat_page'in session.read_text()
 nm=pin(LLVM/'llvm-nm.exe');ninja=pin('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe')
 levels=[]
 for level in ['O0','O2']:
  exe=pin(b['workers'][level]['path'],b['workers'][level]['sha256']);folder=exe.parent;graph=pin(folder/'build.ninja').read_text()
  line=next(l for l in graph.splitlines()if ': CXX_COMPILER_'in l and str(source).replace(':','$:')in l)
  objname=line[6:].split(': CXX_COMPILER_',1)[0];obj=pin(folder/objname);assert machine(obj)==0x8664
  deps=subprocess.run([str(ninja),'-t','deps',objname],cwd=folder,capture_output=True,timeout=20);assert deps.returncode==0
  (out/f'{level}-compiler-dependencies.txt').write_bytes(deps.stdout+deps.stderr);pin(out/f'{level}-compiler-dependencies.txt')
  normalized=deps.stdout.decode(errors='replace').replace('\\','/').casefold()
  expected=[source,contract,operations,session,tree_contract,tree_operations,NPREP/'locale_batch_operations.inc',PREP/level/'registry_build_bindings.hpp']
  for dependency in expected:assert str(dependency).replace('\\','/').casefold()in normalized,('Compiler did not consume',dependency);pin(dependency)
  names=subprocess.run([str(nm),'--defined-only','--demangle',str(obj)],capture_output=True,timeout=20);assert names.returncode==0
  decoded=names.stdout.decode(errors='replace');wanted=['Binding::lockit_bootstrap','Binding::lockit_guard','Binding::lockit_read','Binding::lockit_called','Binding::lockit_returned','Binding::lockit_section_after','Binding::dump_lockit','Binding::tree_enter','Binding::tree_role','Binding::tree_owner_before','Binding::tree_owner_after','Binding::tree_publish','Binding::tree_lockit_read','Binding::tree_lockit_called','Binding::tree_lockit_returned','Binding::tree_returned']
  found=[]
  for needle in wanted:
   matches=[line for line in decoded.splitlines()if needle+'('in line];assert matches,(level,needle);found.extend(matches)
  (out/f'{level}-resource-defined-symbols.txt').write_text('\n'.join(found)+'\n');pin(out/f'{level}-resource-defined-symbols.txt')
  levels.append(dict(level=level,actual_compiled_object=str(obj),compiled_object_sha256=sha(obj),compiler_consumed_source_dependencies=list(map(str,expected)),actual_defined_resource_methods=16))
 emit(out,dict(passed=True,scope='Current compiled tree and Lockit resource dependencies, defined AMD64 methods, authentic whole-page input and named API source bindings; no semantic execution or MSVCP DllMain recompile credit',build_sha256=digest,loaded_pages=pages,named_API_contracts=imports,guest_CS_bytes=24,native_resource_bytes=40,guest_semantic_DWORD_offsets=[4,8,12],opaque_loaded_DWORD_offsets=[0,16,20],seeded_state2=False,levels=levels,elapsed_seconds=time.perf_counter()-started),pins)
if __name__=='__main__':main(*__import__('sys').argv[1:])
