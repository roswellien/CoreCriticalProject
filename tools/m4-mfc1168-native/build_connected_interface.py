"""Compile-only typed-address/NativeEntry interface; no worker or capture."""
from pathlib import Path
import hashlib,json,re,subprocess,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(preparation,digest,name):
 out=R/'reports/m4-mfc1168-native'/name;assert not out.exists();out.mkdir();pins={};commands=[];outputs={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');value=sha(p);assert h is None or value==h,(p,h,value);assert str(p)not in pins or pins[str(p)]==value;pins[str(p)]=value;return p
 def run(cmd,stem):
  commands.append([str(x)for x in cmd]);r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,errors='replace',creationflags=subprocess.CREATE_NO_WINDOW);(out/(stem+'.log')).write_text(r.stdout)
  assert r.returncode==0,(stem,r.returncode,r.stdout[-3500:]);return r.stdout
 try:
  receipt=json.loads(pin(preparation,digest).read_bytes());assert receipt['passed']and not receipt['connected_execution_admitted'];prep=Path(preparation).parent
  for p,h in receipt['files'].items():pin(p,h)
  llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';compiler=pin(llvm/'clang-cl.exe');nm=pin(llvm/'llvm-nm.exe');dis=pin(llvm/'llvm-objdump.exe')
  includes=[prep,R/'tools/m4-runtime',R/'runtime',R/'local/tools/remill-v6.0.1/remill-6.0.1/include']
  for level,opt in [('O0','/Od'),('O2','/O2')]:
   obj=out/('connected-interface-'+level+'.obj');log=run([str(compiler),'/nologo','/std:c++20','/EHsc','/W4','/WX',opt,'/showIncludes','/c',*[str('/I'+str(p))for p in includes],str(prep/'interface_compile.cpp'),'/Fo'+str(obj)],level+'-compile')
   paths=re.findall(r'(?im)^Note: including file:\s*(.+?)\s*$',log);assert paths,'Compiler dependency observations';dependencies=[]
   for path in paths:dependencies.append(str(pin(path)))
   symbols=run([str(nm),'--defined-only',str(obj)],level+'-symbols');assembly=run([str(dis),'-d',str(obj)],level+'-assembly')
   assert 'mfc_connected_compiled_entry'in symbols and 'entry@'in symbols and assembly.strip(),'Actual emitted callback address and body';pin(obj)
   outputs[level]=dict(object=str(obj),sha256=sha(obj),compiler_dependencies=sorted(set(dependencies)),compiler_dependency_occurrences=len(paths),actual_native_entry_emitted=True)
  for p in (Path(__file__),R/'tools/m4-mfc1168-native/build_connected_interface.ps1',Path(sys.executable)):pin(p)
  for p,h in pins.items():assert sha(p)==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Actual O0/O2 compile-only finite connected address and NativeEntry interfaces; no chronological input/context/worker admission',preparation=str(preparation),preparation_sha256=digest,objects=outputs,commands=commands,files=pins,worker_built=False,source_roots_executed=0,connected_execution_admitted=False,initializer_credit=0,capture_archive_reader_opened=False)
  (out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'build.json'),objects=outputs)))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
