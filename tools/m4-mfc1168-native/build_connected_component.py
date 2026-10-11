"""Actual O0/O2 DLL link of the new component; never load/execute that DLL."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(preparation,digest,name):
 out=R/'reports/m4-mfc1168-native'/name;assert not out.exists();out.mkdir();pins={};commands=[];libraries={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def run(args,label):
  args=list(map(str,args));pin(args[0]);r=subprocess.run(args,cwd=R,capture_output=True,timeout=240,creationflags=0x08000000);(out/label).write_bytes(r.stdout+r.stderr);commands.append(dict(arguments=args,exit_code=r.returncode,log=label));print(json.dumps(dict(log=label,exit_code=r.returncode)),flush=True);assert r.returncode==0,(label,(r.stdout+r.stderr)[-3500:]);return (r.stdout+r.stderr).decode(errors='replace')
 try:
  p=json.loads(pin(preparation,digest).read_bytes());assert p['passed']and not p['chronological_input_factory_available'];prep=Path(preparation).parent
  for q,h in p['files'].items():pin(q,h)
  pin(__file__);pin(R/'tools/m4-mfc1168-native/build_connected_component.ps1');pin(sys.executable);os.environ['TEMP']=os.environ['TMP']=str(out)
  llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';cmake=Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe');ninja=Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe');pin(llvm/'clang-cl.exe');pin(ninja)
  for level in ('O0','O2'):
   tree=out/('build-'+level);flags=('/Od'if level=='O0'else'/O2')+' /DNDEBUG /showIncludes /W4 /WX -Wno-error=deprecated-literal-operator -Wno-invalid- offsetof'.replace('- offsetof','-offsetof')
   run([cmake,'-G','Ninja','-S',prep,'-B',tree,f'-DCMAKE_MAKE_PROGRAM={ninja}',f'-DCMAKE_CXX_COMPILER={llvm}/clang-cl.exe','-DCMAKE_BUILD_TYPE=Release',f'-DCMAKE_CXX_FLAGS_RELEASE={flags}',f'-DMW34_ROOT={R}',f'-DMW34_REMILL={p["remill_include"]}',f'-DMW34_OBJECTS={";".join(p["objects"][level])}'],level+'-configure.log')
   log=run([cmake,'--build',tree,'--parallel','4'],level+'-build.log')
   deps=[]
   for path in re.findall(r'(?im)^Note: including file:\s*(.+?)\s*$',log):deps.append(str(pin(path)))
   # Ninja MSVC include parsing strips dependency lines from its normal stdout;
   # read the retained actual .ninja_deps tool output as a second complete source.
   deps_log=run([ninja,'-C',tree,'-t','deps'],level+'-ninja-deps.log')
   for path in re.findall(r'(?m)^\s{4}(.+?)\s*$',deps_log):
    q=Path(path);q=q if q.is_absolute()else tree/q
    if q.is_file():deps.append(str(pin(q)))
   assert deps,'Actual compiler dependencies observed'
   dll=pin(tree/'mfc1168-component.dll');lib=pin(tree/'mfc1168-component.lib')
   asm=run([llvm/'llvm-objdump.exe','-d',dll],level+'-linked-assembly.log');exports=run([llvm/'llvm-readobj.exe','--coff-exports',dll],level+'-exports.log')
   assert 'mfc_connected_linked_entry'in exports and asm.strip(),'Actual DLL export and linked instruction bytes'
   libraries[level]=dict(path=str(dll),sha256=sha(dll),import_library=str(lib),import_library_sha256=sha(lib),literal_objects=p['objects'][level],compiler_dependencies=sorted(set(deps)),native_component_linked=True,loaded=False)
  for q,h in pins.items():assert sha(q)==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual O0/O2 connected component DLL links with13 literal bodies; DLL not loaded, no worker/input admission/source execution',preparation=str(preparation),preparation_sha256=digest,libraries=libraries,commands=commands,files=pins,loaded=False,worker_built=False,connected_execution_admitted=False,source_roots_executed=0,initializer_credit=0)
  (out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'build.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
