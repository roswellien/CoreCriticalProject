"""Compile/link the exact fourteen-root current Context; do not run it."""
from pathlib import Path
import hashlib,json,os,re,subprocess,sys,traceback
sys.dont_write_bytecode=True
R=Path(__file__).resolve().parents[2]
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(preparation,digest,name):
 out=R/'reports/m4-mfc1168-native'/name;assert not out.exists();out.mkdir();pins={};commands=[];workers={};passed=False
 def pin(p,h=None):
  p=Path(p).resolve();assert p.suffix.lower()not in('.mwb','.zip');v=sha(p);assert h is None or h==v,(p,h,v);assert str(p)not in pins or pins[str(p)]==v;pins[str(p)]=v;return p
 def run(args,label):
  args=list(map(str,args));pin(args[0]);r=subprocess.run(args,cwd=R,capture_output=True,timeout=300,creationflags=0x08000000);(out/label).write_bytes(r.stdout+r.stderr);commands.append(dict(arguments=args,exit_code=r.returncode,log=label));print(json.dumps(dict(log=label,exit_code=r.returncode)),flush=True);assert r.returncode==0,(label,(r.stdout+r.stderr)[-3000:]);return (r.stdout+r.stderr).decode(errors='replace')
 try:
  p=json.loads(pin(preparation,digest).read_bytes());assert p['passed']and not p['execution_admitted'];prep=Path(preparation).parent
  for q,h in p['files'].items():pin(q,h)
  llvm=R/'local/tools/llvm-21.1.8/clang+llvm-21.1.8-x86_64-pc-windows-msvc/bin';cmake=Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe');ninja=Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe');pin(llvm/'clang-cl.exe');pin(ninja)
  writer=pin(R/'reports/m4-capture-direct/build-r5/capture_direct.lib');pin(R/'reports/m4-capture-direct/build-r4/preserve.obj');pin(__file__);pin(R/'tools/m4-mfc1168-native/build_connected_fixture.ps1');pin(sys.executable);os.environ['TEMP']=os.environ['TMP']=str(out)
  for level in ('O0','O2'):
   tree=out/('build-'+level);flags=('/Od'if level=='O0'else'/O2')+' /DNDEBUG /showIncludes -Wno-error=deprecated-literal-operator -Wno-invalid- offsetof'.replace('- offsetof','-offsetof')
   run([cmake,'-G','Ninja','-S',prep,'-B',tree,f'-DCMAKE_MAKE_PROGRAM={ninja}',f'-DCMAKE_CXX_COMPILER={llvm}/clang-cl.exe','-DCMAKE_BUILD_TYPE=Release',f'-DCMAKE_CXX_FLAGS_RELEASE={flags}',f'-DMW34_ROOT={R}',f'-DMW34_PREP={prep}',f'-DMW34_LEVEL={level}',f'-DMW34_OBJECTS={";".join(p["objects"][level])}',f'-DMW34_WRITER={writer}',f'-DMW34_REGISTRY={p["native_library"]}',f'-DMW34_REGISTRY_INCLUDE={p["native_include"]}'],level+'-configure.log')
   log=run([cmake,'--build',tree,'--parallel','4'],level+'-build.log');deps=[]
   dep=run([ninja,'-C',tree,'-t','deps'],level+'-ninja-deps.log')
   for path in re.findall(r'(?m)^\s{4}(.+?)\s*$',dep):
    q=Path(path);q=q if q.is_absolute()else tree/q
    if q.is_file():deps.append(str(pin(q)))
   assert deps,'Actual compiler dependency records'
   worker=pin(tree/'mw34_mfc1168_connected.exe');workers[level]=dict(path=str(worker),sha256=sha(worker),literal_objects=p['objects'][level],compiler_dependencies=sorted(set(deps)))
  for q,h in pins.items():assert sha(q)==h
  passed=True
 except BaseException:(out/'failure.txt').write_text(traceback.format_exc());raise
 finally:
  report=dict(passed=passed,scope='Current130 derived connected14 prefix Context compiled O0/O2 with410 literal objects; no worker execution',preparation=str(preparation),preparation_sha256=digest,workers=workers,commands=commands,files=pins,worker_executed=False,execution_admitted=False,initializer_credit=0)
  (out/'build.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=passed,sha256=sha(out/'build.json'))))
if __name__=='__main__':main(Path(sys.argv[1]).resolve(),sys.argv[2],sys.argv[3])
